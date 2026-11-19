"""Only row-local GIVEN values; original columns always remain first."""
import json
import re
import numpy as np
import pandas as pd
from external_v3 import values as external_values

def instrument(schema):
    names=set(schema['items'])
    if {'wave','s3_11_intent_return_12m_lbl'}<=names:return 'unhcr'
    if {'Country','Q03','Q13'}<=names:return 'unicef'
    if any(n.split('.')[-1]=='wageOfSimilarEmployees' for n in names):return 'world_bank'
    return 'generic'

def salary_ranks(values):
    # Parse the declared numeric intervals, never sort their text labels.
    bands=[]
    for value in values:
        token=str(value).strip().replace(',','')
        match=re.fullmatch(r'(\d+)(?:\s*-\s*(\d+)|(\+))?',token)
        if match:
            lo=int(match[1]);hi=int(match[2]) if match[2] else (float('inf') if match[3] else lo)
            if hi<lo:raise ValueError('Reversed salary interval')
            bands.append((lo,hi,str(value)))
    bands.sort(key=lambda b:(b[0],b[1]))
    if any(a[1]>=b[0] for a,b in zip(bands,bands[1:])):raise ValueError('Ambiguous overlapping salary intervals')
    return {label:i for i,(_,_,label) in enumerate(bands)}

def transform(frame,schema):
    given=[n for n,item in schema['items'].items() if item['class']=='GIVEN']
    x=frame[given].copy()
    for n in given:x[n]=x[n].fillna('__ACTUAL_MISSING__').astype(str)
    kind=instrument(schema);added=[]
    def pair(a,b):
        if a not in given or b not in given:return
        name='__fe__'+a+'__x__'+b
        x[name]=[json.dumps([u,v],ensure_ascii=True,separators=(',',':')) for u,v in zip(x[a],x[b])];added.append(name)
    def field(short):
        matches=[n for n in given if n.split('.')[-1]==short]
        return matches[0] if len(matches)==1 else None
    def add(name,values):
        key='__fe__'+name;x[key]=np.asarray(values).astype(str);added.append(key)
    def numerical(name,values):
        x[name]=np.asarray(values,dtype=np.float32);added.append(name)
    if kind=='unicef':
        for a,b in [('Country','Q03'),('Country','Q04'),('Country','Q05'),('Q04','Q05'),('Q13','Q03')]:pair(a,b)
        # Q01/Q02 are age/gender in the actual UNICEF schema; aliases only when GIVEN.
        sex=next((n for n in ['Q02','sex','gender','user.gender'] if n in given),None)
        age=next((n for n in ['Q01','age','user.age'] if n in given),None)
        if sex:pair('Q13',sex)
        if age:pair('Q13',age)
    elif kind=='world_bank':
        wage,pay=field('wageOfSimilarEmployees'),field('lowestAcceptablePay')
        if wage and pay:
            pair(wage,pay)
            wr=salary_ranks(schema['items'][wage]['values']);pr=salary_ranks(schema['items'][pay]['values'])
            # Ordinal distance only makes sense for matching declared salary bands.
            if set(wr)!=set(pr):raise ValueError('Salary schemas have different band supports')
            a=x[wage].map(wr);b=x[pay].map(pr);known=a.notna()&b.notna();d=b-a
            add('salary_relation',np.select([known&(d<0),known&(d==0),known&(d>0)],['minimum_lower','same','minimum_higher'],default='unknown'))
            add('salary_distance',np.select([known&(d<=-2),known&(d==-1),known&(d==0),known&(d==1),known&(d>=2)],['<=-2','-1','0','+1','>=+2'],default='unknown'))
            add('both_zero',np.select([~known,(x[wage]=='0')&(x[pay]=='0')],['unknown','true'],default='false'))
            add('salary_missing_pattern',np.select([a.isna()&b.isna(),a.isna(),b.isna()],['both_missing','similar_wage_missing','minimum_pay_missing'],default='neither_missing'))
        for a,b in [('hadJob','employmentStatus'),('educationLevel','employmentStatus'),('age','hadJob')]:
            aa,bb=field(a),field(b)
            if aa and bb:pair(aa,bb)
        add('not_answered_count',frame[given].eq('Not answered').sum(axis=1).to_numpy())
    for name,values in external_values(frame[given],kind):numerical(name,values)
    return x,added
