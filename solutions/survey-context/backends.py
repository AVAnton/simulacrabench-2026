"""Pinned SDM classification checkpoints; no training or alternative models."""
from pathlib import Path
import gc,hashlib,importlib,json,sys,time
import runtime_bootstrap
sys.path.insert(0,str(Path(__file__).resolve().parent/'vendor'))
import numpy as np
import numpy.rec,numpy.ma
import pandas as pd
import torch
import sdm
from huggingface_hub import hf_hub_download
from safetensors.torch import load_file
from sdm.models.tabfm.ckpt import remap_ckpt
from multiclass import hierarchical_predict,hierarchy_calls
from sdm.models.callback import Callback
from external_v3 import NUMERICAL_COLUMNS
CACHE_PLACEMENT="gpu"

class FullContextGuard(Callback):
    def __init__(self,rows):self.rows=rows;self.observed=[]
    def on_context_preprocessing_end(self,model,x,y,related_tables):
        if x.size(-2)!=self.rows or y.size(-2)!=self.rows:
            raise RuntimeError("SDM altered the full training context")
        self.observed.append(int(x.size(-2)))
        return x,y,related_tables

SEED=271828
torch.set_num_threads(8)
DEVICE='cuda:0' if torch.cuda.is_available() else 'cpu'
if DEVICE.startswith('cuda'):torch.cuda.init()
# Use the upstream eager RMSNorm fallback; runtime JIT performs filesystem I/O.
_rms=importlib.import_module('sdm._kernels.rmsnorm_cast')
TRITON_RMS=_rms._triton_rmsnorm_cast
_rms._triton_rmsnorm_cast=None
MANIFEST=json.loads((Path(__file__).parent/'checkpoint_manifest.json').read_text())
MODELS={};LOAD_RECORDS=[]

def checkpoint(spec):
    # models.txt prefetches repository main snapshots; verify immutable bytes.
    path=hf_hub_download(spec['repo'],spec['filename'],local_files_only=True)
    h=hashlib.sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda:stream.read(4*1024**2),b''):h.update(block)
    if h.hexdigest()!=spec['sha256']:raise RuntimeError('Prefetched checkpoint revision does not match '+spec['repo'])
    return path

for name,spec in MANIFEST.items():
    stamp=time.monotonic();path=checkpoint(spec)
    if name=='kumo':
        model=sdm.models.KumoTabular(task='classification',size='large',pretrained=False,device='meta')
        state=torch.load(path,map_location=DEVICE,weights_only=True)
    else:
        assert name=='tabfm'
        model=sdm.models.TabFM(task='classification',pretrained=False,device='meta')
        state=remap_ckpt(load_file(path,device=DEVICE),is_classifier=True)
    model.models['classification'].load_state_dict(state,assign=True)
    del state
    model.eval();model.requires_grad_(False);MODELS[name]=model
    LOAD_RECORDS.append(dict(backend=name,seconds=time.monotonic()-stamp,parameters=sum(p.numel() for p in model.parameters()),**spec))
gc.collect()

def table(df):
    return sdm.TableTensor.from_pandas(df,{n:'numerical' if n in NUMERICAL_COLUMNS else 'categorical' for n in df.columns},device=DEVICE)

def native(name,x,y,z,members,seed,mode='cache',chunk=512):
    model=MODELS[name];stamp=time.monotonic()
    model._offload_cache=CACHE_PLACEMENT=="cpu"
    guard=FullContextGuard(len(y));cache_bytes={"cuda":0,"cpu":0}
    all_x=pd.concat([x,z],ignore_index=True)
    for n in all_x.columns:
        if n not in NUMERICAL_COLUMNS:all_x[n]=all_x[n].astype('category')
    tx=table(all_x);ty=table(pd.DataFrame({'target':pd.Categorical(np.asarray(y,dtype=np.int64))}))
    generator=torch.Generator(device=DEVICE).manual_seed(seed)
    chunks=[];labels=None;fit_seconds=0.
    try:
        with torch.inference_mode(),torch.amp.autocast('cuda',dtype=torch.bfloat16 if name=='tabfm' else torch.float16,enabled=DEVICE.startswith('cuda')):
            fit_start=time.monotonic()
            if mode=='cache':
                model.fit(tx[:len(x)],ty,num_estimators=members,estimator_batch_size=1,generator=generator,callbacks=[guard])
                for tensor in model._cache._tensors():
                    cache_bytes[tensor.device.type]+=tensor.numel()*tensor.element_size()
                if DEVICE.startswith('cuda'):torch.cuda.synchronize()
                fit_seconds=time.monotonic()-fit_start
                for a in range(len(x),len(tx),chunk):
                    out=model.predict(tx[a:a+chunk]);chunks.append(out.numerical.float().cpu().numpy())
                    labels=np.asarray([int(n) for n in out.columns[sdm.Stype.numerical]])
            elif mode=='forward':
                out=model(x_context=tx[:len(x)],y_context=ty,x_query=tx[len(x):],num_estimators=members,estimator_batch_size=1,generator=generator,callbacks=[guard])
                chunks=[out.numerical.float().cpu().numpy()]
                labels=np.asarray([int(n) for n in out.columns[sdm.Stype.numerical]])
            else:raise ValueError(mode)
        seen=np.unique(y)
        if set(labels)!=set(seen):raise ValueError('Backend class mapping mismatch')
        p=np.concatenate(chunks).astype(np.float64)[:,[np.flatnonzero(labels==v)[0] for v in seen]]
        if not np.isfinite(p).all() or (p<0).any() or (p.sum(1)<=0).any():raise ValueError('Invalid backend probabilities')
        p/=p.sum(1,keepdims=True)
        assert len(guard.observed)==members, (guard.observed,members)
        return p,dict(preprocessed_context_rows=guard.observed,cache_bytes=cache_bytes,cache_placement=CACHE_PLACEMENT,seconds=time.monotonic()-stamp,fit_seconds=fit_seconds,context_rows=len(y),query_rows=len(z),classes=len(seen),mode=mode,query_chunk=chunk)
    finally:
        model.clear()

def predict_target(name,x,y,z,k,members,context,mode='cache',chunk=512):
    y=np.asarray(y,dtype=np.int64);seen=np.unique(y)
    if context is not None and context<len(y):raise ValueError("Full context is mandatory")
    if not len(seen):raise ValueError('No visible answers')
    if len(seen)==1:
        p=np.zeros((len(z),k));p[:,seen[0]]=1
        return p,[]
    def call(a,b,c,seed):return native(name,a,b,c,members,seed,mode,chunk)
    if name=='tabfm' and len(seen)>10:
        return hierarchical_predict(x,y,z,k,call,None,SEED)
    p0,row=call(x,y,z,SEED)
    p=np.zeros((len(z),k));p[:,seen]=p0
    row['ecoc_tasks_per_estimator']=max(int(np.ceil(len(seen)/9)),4*int(np.ceil(np.log10(len(seen))))) if name=='kumo' and len(seen)>10 else 1
    return p,[row]

def warm():
    x=pd.DataFrame({'a':[str(i%7) for i in range(80)],'b':[str(i%11) for i in range(80)],'constant':['x']*80})
    z=x.iloc[:3].copy();z.iloc[0,0]='unseen'
    for name in MODELS:
        predict_target(name,x,np.arange(80)%11,z,13,1,None)
    gc.collect()

warm()
