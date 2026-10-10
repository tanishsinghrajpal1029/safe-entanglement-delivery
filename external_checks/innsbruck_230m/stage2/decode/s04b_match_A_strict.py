# Strict matching: for offset k (file = seg + k), count segments where all overlapping cycles agree exactly (n0 == loops),
# restricted to segments that contain >=1 early-ended cycle (informative).
from common import *
import pickle
A=pickle.load(open(f'{CACHE}/nodeA_loops.pkl','rb'))
for ra,rb,b,_,_ in RUNS:
    z=np.load(f'{CACHE}/{b}_cycles.npz'); seg=z['seg']; n0=z['n0']
    L=A[ra]['loops']; nseg=seg.max()+1
    rows=[]
    for k in range(-40,41):
        inf=agree=0
        for j in range(nseg):
            i=j+k
            if i<0 or i>=len(L) or len(L[i])==0: continue
            x=n0[seg==j]; l=L[i][:len(x)]
            if len(l)<len(x): continue
            if np.any(x<20) or np.any(l<20):
                inf+=1; agree+= np.array_equal(x,l)
        rows.append((k,inf,agree))
    rows=np.array(rows); o=np.argsort(-rows[:,2])[:3]
    print(ra,'best offsets (k, informative segs, exact agree):',rows[o].tolist())
