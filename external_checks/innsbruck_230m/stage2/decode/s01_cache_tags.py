# Convert BSM time-tag text files to npy caches (time in ps as float64->int64, channel int8)
import pandas as pd, numpy as np, sys, os, glob
ROOT=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P=os.path.join(ROOT,'data/Data/Full_tomography/Photons')
out=os.path.join(os.path.dirname(os.path.abspath(__file__)),'cache')
for f in sorted(glob.glob(P+'/*.txt')):
    b=os.path.basename(f)[:-4]
    if os.path.exists(f'{out}/{b}_t.npy'): continue
    df=pd.read_csv(f,sep='\t',header=0,names=['t','c'],dtype={'t':np.float64,'c':np.float64})
    t=np.round(df.t.values).astype(np.int64); c=df.c.values.astype(np.int8)
    np.save(f'{out}/{b}_t.npy',t); np.save(f'{out}/{b}_c.npy',c)
    u,n=np.unique(c,return_counts=True)
    print(b,len(t),'monotone' if np.all(np.diff(t)>=0) else 'NONMONO',(t[-1]-t[0])/1e12,'s',dict(zip(u.tolist(),n.tolist())),flush=True)
