"""Cached holdout calibration with the official floor and optional gate temperature."""
import time
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.special import expit
from schema_utils import _options, _route

FLOOR=.001
MIN_ROWS=100
MIN_GATE_CLASS=50
MIN_GAIN=1e-6

def gate_indices(schema,names):
    sentinel=schema.get('gated_value','NA_GATED')
    return [_options(schema,n).index(sentinel) if sentinel in _options(schema,n) else None for n in names]

def _power(p,value):
    logs=np.log(np.maximum(p,1e-300))/value
    q=np.exp(logs-logs.max(axis=1,keepdims=True));q[p==0]=0
    sums=q.sum(axis=1,keepdims=True)
    return np.divide(q,sums,out=np.full_like(q,1/q.shape[1]),where=sums>0)

def apply(outputs,model,gates):
    result=[]
    for raw,gate in zip(outputs,gates):
        p=np.asarray(raw,dtype=np.float64);p=p/p.sum(axis=1,keepdims=True)
        if model['mode']=='none':q=p.copy()
        elif model['mode']=='single':q=_power(p,model['T_answer'])
        elif gate is None:q=_power(p,model['T_answer'])
        else:
            g=p[:,gate];logit=np.log(np.maximum(g,1e-300))-np.log(np.maximum(1-g,1e-300))
            adjusted=expit(logit/model['T_gate']);adjusted[g==0]=0;adjusted[g==1]=1
            content=np.arange(p.shape[1])!=gate
            q=np.empty_like(p);q[:,content]=_power(p[:,content],model['T_answer'])*(1-adjusted[:,None]);q[:,gate]=adjusted
        result.append(q)
    return result

def per_question_nll(outputs,y):
    return np.array([-np.log(FLOOR+(1-FLOOR*p.shape[1])*(p/p.sum(axis=1,keepdims=True))[np.arange(len(y)),y[:,t]]).mean() for t,p in enumerate(outputs)])

def comparison(outputs,y,schema,names,frame,fit_rows,cal_rows,complete,deadline=None):
    """All optimization uses these cached arrays; this module never calls a model."""
    gates=gate_indices(schema,names);y=np.asarray(y,dtype=np.int64)
    # Reliability is learned only from fit_rows. Holdout truths remain masked in frame.
    probes=[np.full_like(p,1/p.shape[1],dtype=np.float64) for p in outputs]
    _route(frame,schema,names,fit_rows,cal_rows,probes)
    masks=[p.max(axis=1)==1 for p in probes]
    positive=negative=0
    for t,gate in enumerate(gates):
        if gate is not None:
            usable=~masks[t];positive+=int(((y[:,t]==gate)&usable).sum());negative+=int(((y[:,t]!=gate)&usable).sum())
    eligible=complete and len(y)>=MIN_ROWS and min(positive,negative)>=MIN_GATE_CLASS
    evaluations=0;cache={};budget_expired=False
    class BudgetExpired(Exception):pass
    def evaluate(model,details=False,initial=False):
        nonlocal evaluations
        key=(model['mode'],model['T_answer'],model['T_gate'])
        if key in cache:return cache[key] if details else cache[key]['NLL']
        if not initial and deadline is not None and time.monotonic()>=deadline:raise BudgetExpired
        evaluations+=1
        out=apply(outputs,model,gates)
        for p,mask in zip(out,masks):
            p[mask]=0;p[mask,-1]=1
        values=per_question_nll(out,y)
        gated=np.array([g is not None for g in gates])
        cache[key]={'NLL':float(values.mean()),'gated_NLL':float(values[gated].mean()) if gated.any() else None,
                'ordinary_NLL':float(values[~gated].mean()) if (~gated).any() else None,
                'gated_questions':int(gated.sum()),'ordinary_questions':int((~gated).sum())}
        return cache[key] if details else cache[key]['NLL']
    none={'mode':'none','T_answer':1.,'T_gate':1.}
    baseline=evaluate(none,True,initial=True);scalar_seen={1.:baseline['NLL']}
    def scalar(value):
        value=float(value);score=evaluate({'mode':'single','T_answer':value,'T_gate':value});scalar_seen[value]=score;return score
    try:
        opt=minimize_scalar(scalar,bounds=(.5,2.),method='bounded',options={'xatol':.002,'maxiter':30})
        for value in (.5,2.,float(opt.x)):scalar(value)
    except BudgetExpired:budget_expired=True
    value,nll=min(scalar_seen.items(),key=lambda a:(a[1],abs(a[0]-1)))
    single={'mode':'single' if value!=1 else 'none','T_answer':value,'T_gate':value}
    dual_seen=[];success=False;message='skipped: incomplete validation or insufficient gate observations'
    def joint(params):
        model={'mode':'dual','T_answer':float(params[0]),'T_gate':float(params[1])}
        score=evaluate(model);dual_seen.append((score,model));return score
    if eligible and not budget_expired:
        try:
            joint_opt=minimize(joint,np.ones(2),method='L-BFGS-B',bounds=[(.5,2.),(.5,2.)],options={'maxiter':40,'ftol':1e-10,'gtol':1e-6})
            success=bool(joint_opt.success);message=str(joint_opt.message)
        except BudgetExpired:budget_expired=True;message='calibration deadline reached'
    dual=min(dual_seen,key=lambda a:a[0])[1] if dual_seen else {'mode':'dual','T_answer':1.,'T_gate':1.}
    dual_score=evaluate(dual,True) if dual_seen else dict(baseline)
    scores={'none':dict(none,**baseline),'single':dict(single,**evaluate(single,True)),
            'dual':dict(dual,**dual_score,optimized=success,eligible=eligible)}
    selected=dual if eligible and success and scores['dual']['NLL']<scores['single']['NLL']-MIN_GAIN else single
    reason=('improved_validation_NLL' if selected is dual else 'incomplete_validation' if not complete else
            'insufficient_gate_observations' if not eligible else 'calibration_deadline' if budget_expired else 'joint_optimizer_failed' if not success else 'no_confirmed_dual_gain')
    return dict(selected=selected,comparison=scores,selection_reason=reason,all_targets=bool(complete),targets=len(names),
                holdout_rows=len(y),gate_positive=positive,gate_negative=negative,minimum_rows=MIN_ROWS,minimum_gate_class=MIN_GATE_CLASS,
                minimum_dual_gain=MIN_GAIN,optimizer_initial=[1.,1.],optimizer_success=success,budget_expired=budget_expired,
                optimizer_message=message,objective_evaluations=evaluations,inference_during_optimization=0)
