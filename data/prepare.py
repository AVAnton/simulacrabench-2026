"""Build the six survey-context tables from verified local inputs.

No downloading, model inference, benchmark responses, or unpublished audit archive
is required. Read README.md and SOURCE_TERMS.md before opting in.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse, csv, hashlib, json, math, os, re, shutil, sys, tempfile, time, zipfile
import numpy as np
import pandas as pd
import openpyxl
import pyreadstat

COUNTRIES = ['Brazil','Egypt','Guatemala','Iraq','Kenya','Mali','Nepal','Nigeria','Pakistan','Zambia']
UNI_AGES = ['18 to 24 years old','25 - 34 years old','35 - 44 years old','45 and above']
WB_AGES = ['15-19','20-24','25-29','30-34','35-44','45+']
DEM = [('country','age','sex'),('country','age'),('country','sex'),('country',)]
AFRO_DIMS = [('country','religion'), *DEM]
WB_DIMS = [('age','sex'),('age',),('sex',),()]

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4*1024**2),b''): h.update(b)
    return h.hexdigest()

def dump(path, obj):
    Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def age_band(s, kind):
    bounds, labels = ([17,24,34,44,112],UNI_AGES) if kind=='uni' else ([14,19,24,29,34,44,64],WB_AGES)
    return pd.cut(s,bounds,labels=labels).astype(object)

def write_csv(path, rows):
    with Path(path).open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def build(sources, out, cache, runtime_manifest, published):
    cross = runtime_manifest['ged_region_crosswalk']
    @contextmanager
    def open_member(block, member):
        path = sources[block]
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as z, z.open(member) as src:
                yield src
        else:
            # Exact extracted member bytes are accepted during preflight.
            with path.open('rb') as src:
                yield src
    def extract(block, member):
        dest = cache / (block + '.dta')
        # Open the exact known member; never extract arbitrary paths from an archive.
        with open_member(block, member) as src, dest.open('wb') as dst:
            shutil.copyfileobj(src, dst)
        return dest
    tables={}; definitions=[]
    def aggregate(block,d,weight,metric,den,num,dims,numerator,denominator,family=None):
        valid=den & np.isfinite(d[weight]) & d[weight].gt(0)
        a=d.loc[valid].copy(); a['_w']=a[weight].astype('float64'); a['_w2']=a._w**2
        a['_num']=a._w*num.loc[valid].astype(float)
        rows=[]
        for keys in dims:
            known=a[list(keys)].notna().all(axis=1) if keys else pd.Series(True,index=a.index)
            groups=a.loc[known].groupby(list(keys),sort=True,dropna=True) if keys else [((),a)]
            for key,g in groups:
                if not len(g): continue
                if not isinstance(key,tuple):key=(key,)
                sw=float(g._w.sum()); sw2=float(g._w2.sum()); nw=float(g._num.sum())
                rows.append(dict(metric=metric,dimensions='|'.join(keys),key=json.dumps(list(key),ensure_ascii=False,separators=(',',':')),
                                 numerator_weight=nw,denominator_weight=sw,n=len(g),sum_w2=sw2,n_eff=sw*sw/sw2,value=nw/sw))
        assert rows and all(0<=r['value']<=1 and math.isfinite(r['n_eff']) for r in rows)
        tables.setdefault(block,[]).extend(rows)
        definitions.append(dict(name='__new3__'+metric,block=block,numerator=numerator,denominator=denominator,
                                weight=weight,unit='weighted proportion',family=family or metric,
                                threshold=100 if block in ('palms','pases') else 50,
                                fallback=[list(k) for k in dims],groups=len(rows)))
        return rows
    t=time.monotonic()
    if 'afro' in sources:
        cols=['COUNTRY','Q1','Q100','Q95','Q58A','Q58B','Q58C','Q37K','Q59','withinwt_hh']
        d,_=pyreadstat.read_sav(sources['afro'],usecols=cols,user_missing=True)
        d['country']=d.COUNTRY.map({16:'Kenya',21:'Mali',28:'Nigeria',39:'Zambia'})
        d=d.loc[d.country.notna()].copy()
        # Age is a grouping key: unparseable ages do not exclude national/religion/sex totals.
        d['age']=age_band(d.Q1.where(d.Q1.between(18,112)),'uni')
        d['sex']=d.Q100.map({1:'Male',2:'Female'}); d['religion']=d.Q95.map({int(k):v for k,v in runtime_manifest['afro_religion_map'].items()})
        reason=d.Q58A.eq(0)&d.Q58B.isin([1,2])&d.Q58C.isin([*range(1,27),95])
        for metric,den,num,numer,denom,family in [
            ('afro_willing',d.Q58A.eq(0)&d.Q58B.isin([1,2,3,4]),d.Q58B.isin([3,4]),'Q58B in {3,4}','Q58A=0; Q58B in {1,2,3,4}',None),
            ('afro_god_protection',reason,d.Q58C.eq(5),'Q58C=5','Q58A=0; Q58B in {1,2}; Q58C in {1..26,95}','afro_reasons'),
            ('afro_other_bad_side_effects',reason,d.Q58C.eq(13),'Q58C=13','Q58A=0; Q58B in {1,2}; Q58C in {1..26,95}','afro_reasons'),
            ('afro_religious_leader_trust_alot',d.Q37K.isin([0,1,2,3]),d.Q37K.eq(3),'Q37K=3','Q37K in {0,1,2,3}',None),
            ('afro_government_vaccine_trust',d.Q59.isin([1,2,3,4]),d.Q59.isin([3,4]),'Q59 in {3,4}','Q59 in {1,2,3,4}',None)]:
            aggregate('afro',d,'withinwt_hh',metric,den,num,AFRO_DIMS,numer,denom,family)
        print('Afro complete',flush=True)
    if 'wgm' in sources:
        wb=openpyxl.load_workbook(sources['wgm'],read_only=True,data_only=True)
        dd={r[0]:r[1:] for r in wb['Data dictionary'].iter_rows(values_only=True) if r[0]}
        codes={int(k):v.strip() for k,v in re.findall(r'(\d+)\s*=\s*([^,]+)',dd['WP5'][1])}
        it=wb['Full dataset'].iter_rows(values_only=True); headers=next(it)
        cols=['WP5','Age','Gender','wgt','D1','Q21','Q22','Q23','Q24','Q25','Q26','Q29','Q30']
        ix=[headers.index(c) for c in cols]
        d=pd.DataFrame.from_records((tuple(row[i] for i in ix) for row in it),columns=cols); wb.close()
        d=d.apply(pd.to_numeric,errors='coerce'); d['country']=d.WP5.map(codes)
        d=d.loc[d.country.isin(COUNTRIES)&d.Age.between(18,99)].copy()
        d['age']=age_band(d.Age,'uni'); d['sex']=d.Gender.map({1:'Male',2:'Female'})
        for metric,q in [('wgm_children_strongly_important','Q24'),('wgm_vaccines_strongly_safe','Q25'),('wgm_vaccines_strongly_effective','Q26')]:
            aggregate('wgm',d,'wgt',metric,d.Q23.eq(1)&d[q].isin(range(1,6)),d[q].eq(1),DEM,q+'=1','Q23=1; '+q+' in {1..5}')
        for metric,q in [('wgm_government_health_trust_alot','Q21'),('wgm_medical_health_trust_alot','Q22')]:
            aggregate('wgm',d,'wgt',metric,d[q].isin(range(1,5)),d[q].eq(1),DEM,q+'=1',q+' in {1..4}')
        aggregate('wgm',d,'wgt','wgm_science_religion_conflict',d.D1.eq(1)&d.Q29.isin([1,2]),d.Q29.eq(1),DEM[1:],'Q29=1','D1=1; Q29 in {1,2}')
        aggregate('wgm',d,'wgt','wgm_prefers_religion_in_conflict',d.D1.eq(1)&d.Q29.eq(1)&d.Q30.isin([1,2,97]),d.Q30.eq(2),DEM[1:],'Q30=2','D1=1; Q29=1; Q30 in {1,2,97}')
        print('WGM complete',flush=True)
    for block,member,selector,cols in [
        ('palms','palmsv4.dta',('wave',92),['wave','age','gender','empstat1','ceweight1','searchlengthqlfs']),
        ('pases','pases-1995-2024-v1.1-stata/pasesv1.1.dta',('year',2024),['year','age','gender','empstat1','searching','emp_wage','pweight'])]:
        if block not in sources:
            continue
        path=extract(block,member); selected=[]
        for chunk in pd.read_stata(path,columns=cols,convert_categoricals=False,chunksize=200000):
            selected.append(chunk.loc[chunk[selector[0]].eq(selector[1])])
        d=pd.concat(selected,ignore_index=True); raw=len(d); d=d.loc[d.age.between(15,64)].copy()
        d['sex']=d.gender.map({1:'Male',2:'Female'}); d['age']=age_band(d.age,'wb')
        if block=='palms':
            den=d.empstat1.eq(2)&d.searchlengthqlfs.isin(range(1,8))
            for metric,num,numer in [('palms_search_ge6m',d.searchlengthqlfs.isin([3,4,5,6,7]),'searchlengthqlfs in {3,4,5,6,7}'),('palms_search_ge1y',d.searchlengthqlfs.isin([5,6,7]),'searchlengthqlfs in {5,6,7}'),('palms_search_gt5y',d.searchlengthqlfs.eq(7),'searchlengthqlfs=7')]:
                rows=aggregate(block,d,'ceweight1',metric,den,num,WB_DIMS,numer,'wave=92; age 15..64; empstat1=2; searchlengthqlfs in {1..7}','palms_search')
                national=next(r for r in rows if r['dimensions']=='')
                assert national['n']==8086 and abs(national['n_eff']-6578.76)<0.02,national
                assert sum(r['dimensions']=='age|sex' and r['n_eff']>=100 for r in rows)==12
        else:
            ns={}
            for metric,den,num,numer,denom,expected_n in [
                ('pases_unemployment_share',d.empstat1.isin([1,2]),d.empstat1.eq(2),'empstat1=2','empstat1 in {1,2}',29050),
                ('pases_search_among_nonemployed',d.empstat1.isin([0,2])&d.searching.isin([1,2]),d.searching.eq(1),'searching=1','empstat1 in {0,2}; searching in {1,2}',26700),
                ('pases_paid_work_among_employed',d.empstat1.eq(1)&d.emp_wage.isin([1,2]),d.emp_wage.eq(1),'emp_wage=1','empstat1=1; emp_wage in {1,2}',18711)]:
                rows=aggregate(block,d,'pweight',metric,den,num,WB_DIMS,numer,'year=2024; age 15..64; '+denom)
                national=next(r for r in rows if r['dimensions']==''); assert national['n']==expected_n,national
                ns[metric]={k:national[k] for k in ('n','n_eff','denominator_weight','sum_w2')}
        print(block+' complete',flush=True)
    if 'hno' in sources:
        wb=openpyxl.load_workbook(sources['hno'],read_only=True,data_only=True)
        names=[n for n in wb.sheetnames if n.strip()=='sectr_+inter-sectr sub-district']; assert len(names)==1
        it=wb[names[0]].iter_rows(values_only=True)
        for row in it:
            if 'admin3Pcode' in row: headers=row; break
        d=pd.DataFrame.from_records(it,columns=headers); wb.close()
        d=d.loc[d.admin3Pcode.astype(str).str.fullmatch(r'SY\d{6}')].copy()
        assert len(d)==270 and d.admin3Pcode.is_unique and d.admin1Name_en.nunique()==14
        rows=[]
        for metric,col in [('hno_protection_mean','Protection_severity'),('hno_mine_action_mean','Protection_MA_Severity'),('hno_education_mean','Education_severity')]:
            for region,g in d.groupby('admin1Name_en'):
                v=pd.to_numeric(g[col],errors='coerce'); v=v.loc[v.isin(range(1,6))]; value=float(v.mean()) if len(v) else None
                rows.append(dict(metric=metric,region=region,n=len(v),all_subdistricts=len(g),value=value))
            definitions.append(dict(name='__new3__'+metric,block='hno',numerator='sum valid '+col,denominator='number of subdistricts with '+col+' in {1..5}',weight='equal subdistricts',unit='arithmetic mean ordinal severity code',groups=14))
        tables['hno']=rows
    if 'ged' in sources:
        counts=[dict.fromkeys(cross.values(),0),dict.fromkeys(cross.values(),0)]; seen=set(); ambiguous=0
        with open_member('ged', 'GEDEvent_v26_1.csv') as f:
            for d in pd.read_csv(f,usecols=['id','country','adm_1','date_start','date_end'],chunksize=100000):
                assert d.id.notna().all() and d.id.is_unique
                ids=set(d.id); assert not seen.intersection(ids),'duplicate GED id'; seen.update(ids)
                d=d.loc[d.country.eq('Syria')].copy(); d['region']=d.adm_1.map(cross)
                a=pd.to_datetime(d.date_start,errors='coerce'); b=pd.to_datetime(d.date_end,errors='coerce')
                valid=d.region.notna() & a.notna() & b.notna() & a.eq(b)
                for i,(lo,hi) in enumerate([('2024-01-01','2024-12-31'),('2025-01-01','2025-04-30')]):
                    for k,v in d.loc[valid&a.between(lo,hi)].region.value_counts().items():counts[i][k]+=int(v)
        assert [sum(c.values()) for c in counts]==[1064,209],counts
        rows=[]
        for metric,c in zip(['ged_2024_log_events','ged_janapr2025_log_events'],counts):
            for region,n in sorted(c.items()):rows.append(dict(metric=metric,region=region,n=n,value=math.log1p(n)))
            definitions.append(dict(name='__new3__'+metric,block='ged',numerator='count of unique event records with parsed date_start=date_end',denominator='none',weight='none',unit='log1p event record count',groups=14))
        tables['ged']=rows
    assert len(definitions) == sum(f['block'] in sources for f in runtime_manifest['features'])
    table_meta = {}
    for block, rows in tables.items():
        name = block + '.csv'
        write_csv(out / name, rows)
        table_meta[block] = {'file': name, 'sha256': sha(out / name), 'rows': len(rows)}
    for block, path in published.items():
        name = block + '.csv'
        shutil.copyfile(path, out / name)
        with (out / name).open(encoding='utf-8', newline='') as f:
            rows = list(csv.DictReader(f))
        table_meta[block] = {'file': name, 'sha256': sha(out / name), 'rows': len(rows)}
    if table_meta != runtime_manifest['tables']:
        mismatches = [k for k in table_meta if table_meta[k] != runtime_manifest['tables'].get(k)]
        raise RuntimeError('Aggregate identity mismatch: ' + ', '.join(mismatches) +
                           '. No output was installed. Use the pinned preparation environment; do not edit expected hashes.')
    # The public manifest preserves runtime semantics and omits historical source
    # paths and numerical source-audit controls. CSVs must still match exactly.
    dump(out / 'manifest.json', runtime_manifest)
    return table_meta


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs', type=Path, required=True, help='JSON mapping source keys to local files; omitted cleared blocks use bundled aggregates; relative paths resolve beside this JSON')
    p.add_argument('--output', type=Path, required=True, help='New or empty private output directory')
    args = p.parse_args()
    base = Path(__file__).resolve().parent
    metadata = json.loads((base / 'source_manifest.json').read_text(encoding='utf-8'))
    runtime_manifest = json.loads((base / 'feature_definitions.json').read_text(encoding='utf-8'))
    supplied = json.loads(args.inputs.read_text(encoding='utf-8-sig'))
    if not isinstance(supplied, dict) or set(supplied) - set(metadata['sources']):
        p.error('Input JSON keys must be drawn from: ' + ', '.join(metadata['sources']))
    sources = {}
    source_checks = {}
    for block, value in supplied.items():
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = args.inputs.resolve().parent / path
        path = path.resolve(strict=True)
        expected = metadata['sources'][block]
        actual_hash = sha(path)
        exact = path.stat().st_size == expected['bytes'] and actual_hash == expected['sha256']
        member_match = False
        if not exact and expected.get('member_identity'):
            member = expected['member_identity']
            if zipfile.is_zipfile(path):
                with zipfile.ZipFile(path) as z:
                    try:
                        info = z.getinfo(member['name'])
                        with z.open(info) as f:
                            h = hashlib.sha256()
                            for chunk in iter(lambda: f.read(4 * 1024**2), b''):
                                h.update(chunk)
                        member_match = info.file_size == member['bytes'] and h.hexdigest() == member['sha256']
                    except KeyError:
                        member_match = False
            else:
                member_match = path.stat().st_size == member['bytes'] and actual_hash == member['sha256']
        if not exact and not member_match:
            raise RuntimeError('Source identity mismatch: ' + block + '. Obtain the documented source or exact extracted member; no schema-only fallback is allowed.')
        source_checks[block] = {'supplied_sha256': actual_hash, 'identity': 'original-file' if exact else 'exact-archive-member'}
        sources[block] = path
    published = {}
    for block in set(metadata['sources']) - set(sources):
        expected = metadata['sources'][block]
        path = base / 'aggregates' / (block + '.csv')
        if not expected['included_in_repository'] or not path.is_file():
            p.error('Missing local input for non-distributed source: ' + block)
        if sha(path) != runtime_manifest['tables'][block]['sha256']:
            raise RuntimeError('Bundled aggregate hash mismatch: ' + block)
        published[block] = path
        source_checks[block] = {'identity': 'published-derived-table', 'sha256': sha(path)}
    out = args.output.resolve()
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        p.error('--output must be new or empty; existing data are never overwritten.')
    out.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    print(f'Verified {len(sources)} local sources and {len(published)} published tables; preparing private output.', flush=True)
    with tempfile.TemporaryDirectory(prefix='survey-context-', dir=out.parent) as temporary:
        stage = Path(temporary)
        payload = stage / 'payload'
        cache = stage / 'scratch'
        payload.mkdir()
        cache.mkdir()
        tables = build(sources, payload, cache, runtime_manifest, published)
        receipt = {'status': 'passed', 'comparison': 'byte-exact SHA256 for all six historical CSVs',
                   'tables': tables, 'source_checks': source_checks,
                   'python': sys.version, 'versions': {n: __import__(n).__version__ for n in ('numpy','pandas','openpyxl','pyreadstat')},
                   'seconds': time.monotonic() - started, 'redistribution_permission': False}
        dump(payload / 'preparation.json', receipt)
        # Stage beside the destination, then install the complete directory with
        # one same-filesystem rename. Recheck emptiness after the lengthy build.
        if out.exists():
            if not out.is_dir() or any(out.iterdir()):
                raise RuntimeError('Output changed during preparation; existing data were not overwritten.')
            out.rmdir()  # Only an empty directory can be removed here.
        os.replace(payload, out)
    print(json.dumps({'status': 'passed', 'tables': len(tables), 'comparison': 'byte-exact'}), flush=True)


if __name__ == '__main__':
    main()
