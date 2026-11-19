"""Fixed audited numeric context; only prepared aggregates, only row-local GIVEN keys."""
from pathlib import Path
from functools import lru_cache
import csv, hashlib, json, math
import numpy as np

UNICEF_COLUMNS=tuple('__new3__'+n for n in (
    'afro_willing','afro_god_protection','afro_other_bad_side_effects','afro_religious_leader_trust_alot','afro_government_vaccine_trust',
    'wgm_children_strongly_important','wgm_vaccines_strongly_safe','wgm_vaccines_strongly_effective','wgm_government_health_trust_alot','wgm_medical_health_trust_alot','wgm_science_religion_conflict','wgm_prefers_religion_in_conflict'))
WB_COLUMNS=tuple('__new3__'+n for n in ('palms_search_ge6m','palms_search_ge1y','palms_search_gt5y','pases_unemployment_share','pases_search_among_nonemployed','pases_paid_work_among_employed'))
UNHCR_COLUMNS=tuple('__new3__'+n for n in ('hno_protection_mean','hno_mine_action_mean','hno_education_mean','ged_2024_log_events','ged_janapr2025_log_events'))
COLUMNS={'unicef':UNICEF_COLUMNS,'world_bank':WB_COLUMNS,'unhcr':UNHCR_COLUMNS}
NUMERICAL_COLUMNS=frozenset(UNICEF_COLUMNS+WB_COLUMNS+UNHCR_COLUMNS)
NAMED_RELIGIONS=frozenset(('Buddhist','Christian','Hindu','Jewish','Muslim','Traditional religions',"Baha'i",'Sikh'))
UNI_AGES=frozenset(('18 to 24 years old','25 - 34 years old','35 - 44 years old','45 and above'))
WB_AGES=frozenset(('15-19','20-24','25-29','30-34','35-44','45+'))
BASE=Path(__file__).resolve().parent/'external_data_v3'
MANIFEST=json.loads((BASE/'manifest.json').read_text(encoding='utf-8'))
assert {r['name'] for r in MANIFEST['features']}==NUMERICAL_COLUMNS
SPECS={r['name']:r for r in MANIFEST['features']}
SURVEY={}; REGIONAL={}
for block,meta in MANIFEST['tables'].items():
    payload=(BASE/meta['file']).read_bytes()
    if hashlib.sha256(payload).hexdigest()!=meta['sha256']:raise RuntimeError('v3 aggregate hash mismatch: '+block)
    rows=list(csv.DictReader(payload.decode('utf-8').splitlines()))
    if len(rows)!=meta['rows'] or not rows:raise RuntimeError('v3 missing aggregate block: '+block)
    for r in rows:
        name='__new3__'+r['metric']; value=float(r['value'])
        if name not in NUMERICAL_COLUMNS or not math.isfinite(value):raise RuntimeError('Invalid v3 cell')
        if block in ('hno','ged'):
            if (block=='hno' and not 1<=value<=5) or (block=='ged' and value<0):raise RuntimeError('Invalid region value')
            cells=REGIONAL.setdefault(name,{})
            if r['region'] in cells:raise RuntimeError('Duplicate region cell')
            cells[r['region']]=value
        else:
            if not 0<=value<=1:raise RuntimeError('Invalid weighted share')
            dims=tuple(r['dimensions'].split('|')) if r['dimensions'] else ()
            key=tuple(json.loads(r['key'])); cells=SURVEY.setdefault(name,{}).setdefault(dims,{})
            if key in cells:raise RuntimeError('Duplicate survey cell')
            cells[key]=(value,float(r['n_eff']))
assert set(SURVEY)|set(REGIONAL)==NUMERICAL_COLUMNS

@lru_cache(maxsize=8192)
def select(name,country,age,sex,religion):
    spec=SPECS[name]; values={'country':country,'age':age,'sex':sex,'religion':religion}
    for dims in spec['fallback']:
        key=tuple(values[n] for n in dims)
        if any(v is None for v in key):continue
        cell=SURVEY[name].get(tuple(dims),{}).get(key)
        if cell is not None and cell[1]>=spec['threshold']:return cell[0]
    return np.nan

def values(given,kind):
    """Return arrays in registry order; caller passes GIVEN-only frame."""
    names=COLUMNS.get(kind,())
    if not names:return []
    def field(name):
        if name not in given:return [None]*len(given)
        return [v if isinstance(v,str) else None for v in given[name]]
    result=np.full((len(given),len(names)),np.nan,dtype=np.float32)
    if kind=='unicef':
        for i,(country,age,sex,religion) in enumerate(zip(field('Country'),field('Q01'),field('Q02'),field('Q05'))):
            age=age if age in UNI_AGES and country!='Egypt' else None
            sex=sex if sex in ('Male','Female') else None
            for j,name in enumerate(names):
                if j>=10 and religion not in NAMED_RELIGIONS:continue
                result[i,j]=select(name,country,age,sex,religion)
    elif kind=='world_bank':
        for i,(country,age,sex) in enumerate(zip(field('user.country'),field('user.age'),field('user.gender'))):
            if country!='South Africa':continue
            age=age if age in WB_AGES else None; sex=sex if sex in ('Male','Female') else None
            for j,name in enumerate(names):result[i,j]=select(name,country,age,sex,None)
    elif kind=='unhcr':
        for i,region in enumerate(field('s2_4a_origin_governorate_lbl')):
            for j,name in enumerate(names):result[i,j]=REGIONAL[name].get(region,np.nan)
    return [(name,result[:,j]) for j,name in enumerate(names)]
