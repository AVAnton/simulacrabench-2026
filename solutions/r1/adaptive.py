"""Respondent holdout, calibrated NLL selection and measured inference reserves."""
import gc,json,time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from scipy.optimize import minimize_scalar
from features import transform,instrument
from schema_utils import _options,_route
from multiclass import hierarchy_calls
from backends import predict_target,DEVICE,SEED,MODELS
from settings import CONFIG

LAST_AUDIT={}
RUN_GPU_PEAK={'allocated':0,'reserved':0}
PROFILE=json.loads((Path(__file__).parent/'runtime_profile.json').read_text())

def temperature(outputs,value):
    result=[]
    for p in outputs:
        q=p**(1/value);result.append(q/q.sum(1,keepdims=True))
    return result

def loss(outputs,y):
    return float(np.mean([-np.log(.001+(1-.001*p.shape[1])*(p/p.sum(1,keepdims=True))[np.arange(len(y)),y[:,t]]).mean() for t,p in enumerate(outputs)]))

def representatives(y,widths,count):
    stats=[]
    for t,k in enumerate(widths):
        counts=np.bincount(y[:,t],minlength=k);p=counts[counts>0]/len(y)
        stats.append([np.log1p(k),-float(np.sum(p*np.log(p)))/max(np.log(k),1.),len(p)/k,float(p.min()),float(np.mean(counts[counts>0]<=5))])
    values=np.array(stats);span=np.ptp(values,axis=0);v=(values-values.min(0))/np.where(span>0,span,1)
    selected=[int(np.argmax(v[:,0]))]
    while len(selected)<min(count,len(widths)):
        distance=((v[:,None,:]-v[selected][None,:,:])**2).sum(2).min(1);distance[selected]=-1
        selected.append(int(np.argmax(distance)))
    return selected,stats

def gpu_peaks():
    peaks={'allocated':int(torch.cuda.max_memory_allocated()),'reserved':int(torch.cuda.max_memory_reserved())} if DEVICE.startswith('cuda') else {'allocated':0,'reserved':0}
    for key,value in peaks.items():RUN_GPU_PEAK[key]=max(RUN_GPU_PEAK[key],value)
    return peaks

def fit_target(backend,x,y,z,k,cfg):
    start=time.monotonic();gpu_peaks()
    if DEVICE.startswith('cuda'):torch.cuda.reset_peak_memory_stats()
    try:
        p,calls=predict_target(backend,x,y,z,k,cfg['estimators'],cfg['context'],cfg['mode'],cfg['chunk'])
    finally:
        for model in MODELS.values():model.clear()
        peaks=gpu_peaks();gc.collect()
    seen=np.unique(y)
    return p,dict(status='constant' if len(seen)==1 else 'fitted',seconds=time.monotonic()-start,
        train_rows=len(y),query_rows=len(z),context_rows=len(y),estimators=cfg['estimators'],
        k=k,observed_classes=len(seen),missing_classes=k-len(seen),native_calls=calls,
        gpu_peak_allocated_bytes=peaks['allocated'],gpu_peak_reserved_bytes=peaks['reserved'])

def optional_fit(*args):
    start=time.monotonic()
    try:return fit_target(*args)
    except torch.cuda.OutOfMemoryError as error:
        message=str(error);seen=set()
        while error is not None and id(error) not in seen:
            seen.add(id(error));nested=error.__cause__ or error.__context__
            error.__traceback__=None;error.__cause__=None;error.__context__=None;error=nested
    for model in MODELS.values():model.clear()
    peaks=gpu_peaks();gc.collect();torch.cuda.empty_cache()
    return None,dict(status='cuda_oom',seconds=time.monotonic()-start,error=message,
        gpu_peak_allocated_bytes=peaks['allocated'],gpu_peak_reserved_bytes=peaks['reserved'])

def predict(frame,schema,deadline,search_budget=None):
    start=time.monotonic();LAST_AUDIT.clear();kind=instrument(schema)
    search_deadline=min(deadline,start+search_budget) if search_budget is not None else deadline
    backend='kumo'
    names=[n for n,v in schema['items'].items() if v['class']=='PREDICT']
    if not names:return []
    missing=frame[names].isna().to_numpy();train=np.flatnonzero(~missing.any(1));query=np.flatnonzero(missing.any(1))
    if not len(query):return []
    if not len(train):raise ValueError('Visible training rows are required')
    widths=[len(_options(schema,n)) for n in names]
    y=np.column_stack([pd.Categorical(frame[n].iloc[train],categories=_options(schema,n)).codes for n in names]).astype(np.int64)
    if (y<0).any():raise ValueError('Visible target outside schema support')
    x,added=transform(frame,schema)
    order=np.random.default_rng(SEED+17).permutation(len(train));cut=max(1,int(.8*len(train)));fit,cal=order[:cut],order[cut:]
    xt=x.iloc[train];z=x.iloc[query];xf=x.iloc[train[fit]];zf=x.iloc[train[cal]]
    validation_frame=frame.copy();validation_frame.loc[frame.index[train[cal]],names]=None
    rep,stats=representatives(y[fit],widths,CONFIG['representatives'].get(kind,4));all_targets=list(range(len(names)))
    seen=[np.unique(y[:,t]) for t in all_targets]
    trials=[];calibration=[];disabled=[];oom=[];records=[];switches=[];history=[]
    def settings(cfg):return {k:cfg[k] for k in ('context','estimators','mode','chunk')}
    def new(count):return dict(context=None,estimators=count,mode='cache',chunk=512,outputs={},records=[],temperature=1.,calibrated_NLL=None,validated=False,runtime_scale=1.,timing_actual=0.,timing_expected=0.)
    chosen=new(1);measured=PROFILE['datasets'].get(kind,PROFILE['datasets']['world_bank'])
    def cost(cfg,t,validation=False):
        if len(seen[t])<2:return .04
        available=measured['counts'];key=str(cfg['estimators'])
        if key not in available:key=min(available,key=lambda n:abs(int(n)-cfg['estimators']))
        source=available[key]['targets'].get(names[t])
        if source is None:source=max(available[key]['targets'].values(),key=lambda r:r['seconds'])
        rows=len(fit) if validation else len(train);q=len(cal) if validation else len(query)
        def scaled(row):
            fit_seconds=row.get('fit_seconds',sum(c['fit_seconds'] for c in row.get('native_calls',[])))
            query_seconds=max(0.,row['seconds']-fit_seconds)
            ratio=rows/row['context_rows']
            # Attention fit cost and cached query cost scale independently.
            fit_scale=max(.5,ratio**2)
            query_scale=max(.35,ratio)*np.ceil(q/cfg['chunk'])/max(1.,np.ceil(row['query_rows']/cfg['chunk']))
            return (fit_seconds*fit_scale+query_seconds*query_scale)*cfg['estimators']/row['estimators']+.025
        def calls(k):return hierarchy_calls(np.arange(k)) if backend=='tabfm' else (max(int(np.ceil(k/9)),4*int(np.ceil(np.log10(k)))) if k>10 else 1)
        class_scale=max(1.,calls(len(seen[t]))/max(1,calls(source['observed_classes'])))
        # Direct full-context measurements outrank extrapolations from smaller
        # validation folds. Validation timings inform validation only; final
        # predictions get their own cumulative observed speed correction.
        observed=[scaled(r) for r in cfg['records'] if r.get('target_index')==t] if validation else []
        return max([scaled(source)*class_scale,*observed])*cfg['runtime_scale']
    def forecast(cfg,indices,margin=1.12):return margin*sum(cost(cfg,t) for t in indices)+6.
    def calibrate(cfg,indices,stage):
        stamp=time.monotonic()
        def objective(value):
            out=temperature([cfg['outputs'][t] for t in indices],value)
            _route(validation_frame,schema,[names[t] for t in indices],train[fit],train[cal],out)
            return loss(out,y[cal][:,indices])
        opt=minimize_scalar(objective,bounds=(.5,2.),method='bounded',options={'xatol':.002,'maxiter':30})
        tests=[(.5,objective(.5)),(1.,objective(1.)),(2.,objective(2.)),(float(opt.x),float(opt.fun))]
        value,nll=min(tests,key=lambda v:(v[1],abs(v[0]-1.)))
        calibration.append(dict(settings(cfg),stage=stage,temperature=value,NLL=nll,seconds=time.monotonic()-stamp,target_indices=list(indices)))
        cfg.update(temperature=value,calibrated_NLL=nll)
    def validate(cfg):
        row=dict(settings(cfg),stage='estimators',target_indices=list(rep),status='discarded')
        reserve=max(forecast(chosen,all_targets),forecast(cfg,all_targets))
        if time.monotonic()+reserve+1.12*sum(cost(cfg,t,True) for t in rep)+5>=search_deadline:
            row['reason']='reserve_full_context_final_inference';trials.append(row);return False
        for t in rep:
            if time.monotonic()+reserve+1.05*cost(cfg,t,True)+3>=search_deadline:
                row['reason']='reserve_full_context_final_inference';trials.append(row);return False
            p,r=optional_fit(backend,xf,y[fit,t],zf,widths[t],cfg);r.update(target=names[t],target_index=t)
            if p is None:
                oom.append(dict(r,phase='validation'));row['reason']='cuda_oom';trials.append(row);return False
            cfg['outputs'][t]=p;cfg['records'].append(r)
        calibrate(cfg,rep,'candidate');cfg['validated']=True
        row.update(status='complete',calibrated_NLL=cfg['calibrated_NLL'],temperature=cfg['temperature'],fit_records=list(cfg['records']))
        trials.append(row);return True
    if len(cal) and len(train)>=100 and x.shape[1]:
        for count in CONFIG['candidates'].get(kind,[1]):
            cfg=new(count)
            if not validate(cfg):break
            history.append(cfg)
            if not chosen['validated'] or cfg['calibrated_NLL']<=chosen['calibrated_NLL']:
                chosen=cfg
    else:disabled.append(dict(stage='validation',reason='too_few_rows'))
    selection=settings(chosen);reused=len(chosen['outputs']);extension=[]
    # Full context and useful estimators take priority over extra calibration.
    if chosen['validated'] and CONFIG['extend_calibration']:
        missing_cal=[t for t in all_targets if t not in chosen['outputs']];keys=set(chosen['outputs'])
        if time.monotonic()+forecast(chosen,all_targets)+1.2*sum(cost(chosen,t,True) for t in missing_cal)+5>=deadline:
            disabled.append(dict(stage='all_target_calibration',reason='reserve_full_context_final_inference'));missing_cal=[]
        for t in missing_cal:
            if time.monotonic()+forecast(chosen,all_targets)+1.1*cost(chosen,t,True)+3>=deadline:break
            p,r=optional_fit(backend,xf,y[fit,t],zf,widths[t],chosen);r.update(target=names[t],target_index=t)
            if p is None:oom.append(dict(r,phase='calibration'));break
            chosen['outputs'][t]=p;chosen['records'].append(r);extension.append(r)
        if extension and len(chosen['outputs'])!=len(names):
            chosen['outputs']={t:p for t,p in chosen['outputs'].items() if t in keys}
            disabled.append(dict(stage='all_target_calibration',reason='incomplete_extension_discarded'))
        if len(chosen['outputs'])>reused:calibrate(chosen,sorted(chosen['outputs']),'dataset_temperature')
    output=[];used=[];final_start=time.monotonic()
    for t,k in enumerate(widths):
        # Optional search reserves 12%; final inference uses measured timings,
        # a 5% margin, six seconds of fixed slack, and the outer 20-second reserve.
        remaining=all_targets[t:];estimate=forecast(chosen,remaining,1.05)
        if time.monotonic()+estimate>=deadline:
            affordable=[c for c in history if time.monotonic()+forecast(c,remaining,1.05)<deadline]
            if affordable:
                previous=chosen;chosen=min(affordable,key=lambda c:(c['calibrated_NLL'],-c['estimators']))
                if chosen is not previous:switches.append(dict(before_target=t,reason='remaining_inference_deadline',old=settings(previous),new=settings(chosen)))
        if time.monotonic()+1.05*cost(chosen,t)>=deadline:
            raise TimeoutError('Full-context requested backend cannot finish every target within the measured budget')
        expected=cost(chosen,t);p,r=optional_fit(backend,xt,y[:,t],z,k,chosen)
        if p is None:
            oom.append(dict(r,phase='final',target=names[t]));cheaper=[c for c in history if c['estimators']<chosen['estimators']]
            if not cheaper:raise torch.cuda.OutOfMemoryError('Full-context one-estimator configuration is infeasible: '+r['error'])
            chosen=min(cheaper,key=lambda c:c['calibrated_NLL']);p,r=fit_target(backend,xt,y[:,t],z,k,chosen)
            switches.append(dict(before_target=t,reason='cuda_oom',new=settings(chosen)))
        r.update(target=names[t],target_index=t,forecast_before_fit_seconds=estimate,remaining_deadline_seconds=deadline-time.monotonic())
        if r['status']=='fitted':
            # Regularize early timings with sixteen measured target equivalents.
            # One cold or unusually slow fit must not scale every remaining head.
            raw_expected=expected/chosen['runtime_scale']
            chosen['timing_actual']+=r['seconds'];chosen['timing_expected']+=raw_expected
            if 'timing_prior' not in chosen:
                chosen['timing_prior']=16*sum(cost(chosen,j) for j in all_targets)/len(all_targets)/chosen['runtime_scale']
            prior=chosen['timing_prior']
            chosen['runtime_scale']=max(1.,(chosen['timing_actual']+prior)/(chosen['timing_expected']+prior))
        output.append(p);records.append(r);used.append(chosen)
    matching={t:cfg['outputs'][t] for t,cfg in enumerate(used) if t in cfg['outputs']};indices=sorted(matching);temp=chosen['temperature']
    if indices and any(c is not chosen for c in used):
        mixed=new(chosen['estimators']);mixed['outputs']=matching;calibrate(mixed,indices,'runtime_final_temperature');temp=mixed['temperature']
    for t,r in enumerate(records):
        if r['status']=='fitted':output[t]=temperature([output[t]],temp)[0]
    _route(frame,schema,names,train,query,output)
    rows,cols=np.nonzero(missing[query]);result=[output[t][r].tolist() for r,t in zip(rows,cols)];gpu_peaks()
    LAST_AUDIT.update(implementation='Kumo_Large_All_Full_Context_SDM',backend=backend,nb_used=False,prior_blend=False,quality_eligible=True,fallback=0,
        full_context=True,cache_placement='gpu',temperature=temp,temperature_semantics='external_power_preserving_default_internal_temperature',selection_configuration=selection,
        runtime_switches=switches,train_rows=len(train),query_rows=len(query),inner_train_rows=len(fit),inner_validation_rows=len(cal),targets=len(names),
        given_features=x.shape[1]-len(added),engineered_features=added,representative_targets=[names[t] for t in rep],representative_statistics=[stats[t] for t in rep],
        tuning_trials=trials,calibration=calibration,disabled_tuning=disabled,calibration_targets=len(indices),calibration_all_targets=len(indices)==len(names),
        validation_predictions_reused=reused,validation_fits_added=len(extension),validation_records=chosen['records'],calibration_extension_records=extension,oom_attempts=oom,
        target_records=records,fitted=sum(r['status']=='fitted' for r in records),constant=sum(r['status']=='constant' for r in records),
        overall_gpu_peak_allocated_bytes=RUN_GPU_PEAK['allocated'],overall_gpu_peak_reserved_bytes=RUN_GPU_PEAK['reserved'],
        final_seconds=time.monotonic()-final_start,seconds=time.monotonic()-start,device=DEVICE,allocated_budget=deadline-start,deadline_margin_seconds=deadline-time.monotonic())
    return result
