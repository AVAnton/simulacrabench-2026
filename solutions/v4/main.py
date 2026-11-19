"""Kumo Large for UNICEF, World Bank and UNHCR; full training context."""
import time
_WORKER_START=time.monotonic()
import runtime_bootstrap
import adaptive
from features import instrument
LAST_AUDIT={}
_completed=set()
_FINAL_RESERVES={name:row['reserve_seconds'] for name,row in adaptive.PROFILE['datasets'].items()}
_DATASET_BUDGETS=adaptive.PROFILE['dataset_budgets']

def predict(frame,schema):
    kind=instrument(schema)
    pending=sum(cost for name,cost in _FINAL_RESERVES.items() if name!=kind and name not in _completed)
    deadline=_WORKER_START+870.-pending
    result=adaptive.predict(frame,schema,deadline,_DATASET_BUDGETS.get(kind,60.))
    _completed.add(kind)
    LAST_AUDIT.clear();LAST_AUDIT.update(adaptive.LAST_AUDIT,instrument=kind,worker_elapsed_seconds=time.monotonic()-_WORKER_START,
        completed=sorted(_completed),shared_work_budget=870.,end_to_end_target=890.)
    return result
