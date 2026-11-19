"""Deterministic context selection and a TabFM-only conditional hierarchy."""
import numpy as np

def hierarchy(classes):
    classes=np.asarray(classes,dtype=np.int64)
    if len(classes)<=10:return [np.array([c]) for c in classes]
    return list(np.array_split(classes,10))

def hierarchy_calls(classes):
    if len(classes)<2:return 0
    return 1+sum(hierarchy_calls(g) for g in hierarchy(classes) if len(g)>1)

def hierarchical_predict(x,y,z,k,native,limit,seed):
    """Each leaf receives the product of all conditional probabilities to it."""
    out=np.zeros((len(z),k),dtype=np.float64);records=[]
    def visit(rows,classes,mass,depth):
        if len(classes)==1:
            out[:,classes[0]]=mass
            return
        groups=hierarchy(classes)
        lookup={int(c):i for i,g in enumerate(groups) for c in g}
        # Preserve rare original answers even at an internal node.
        chosen=rows
        if limit is not None and limit<len(rows):raise ValueError("Full branch context is mandatory")
        target=np.array([lookup[int(v)] for v in y[chosen]],dtype=np.int64)
        p,row=native(x.iloc[chosen],target,z,seed+depth)
        if p.shape!=(len(z),len(groups)):raise ValueError('Hierarchy output support mismatch')
        records.append(dict(row,depth=depth,original_classes=classes.tolist(),conditional_classes=len(groups)))
        for i,g in enumerate(groups):
            child_rows=rows[np.isin(y[rows],g)]
            visit(child_rows,g,mass*p[:,i],depth+1)
    visit(np.arange(len(y)),np.unique(y),np.ones(len(z)),0)
    return out,records
