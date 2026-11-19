"""Writable scratch without disconnecting the provided build-time HF cache."""
import os
import sys
import tempfile
from pathlib import Path

_hf_home=Path(os.environ.get('HF_HOME',Path(os.environ.get('XDG_CACHE_HOME',Path.home()/'.cache'))/'huggingface'))
os.environ.setdefault('HF_HUB_CACHE',os.environ.get('HUGGINGFACE_HUB_CACHE',str(_hf_home/'hub')))
SCRATCH=tempfile.mkdtemp(prefix='simulacrabench-runtime-')
sys.dont_write_bytecode=True
for name,suffix in {'XDG_CACHE_HOME':'cache','MPLCONFIGDIR':'matplotlib','JOBLIB_TEMP_FOLDER':'joblib','TORCH_HOME':'torch','CUDA_CACHE_PATH':'cuda','TRITON_CACHE_DIR':'triton'}.items():
    os.environ[name]=os.path.join(SCRATCH,suffix)
os.environ['HF_HUB_OFFLINE']='1'
os.environ['HF_HUB_DISABLE_TELEMETRY']='1'
os.environ['CUDA_CACHE_DISABLE']='1'
for name in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='8'
