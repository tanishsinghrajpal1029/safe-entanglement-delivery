# Match BSM tagger segments (scan steps) to Node A raw files (steps) via per-cycle loop counts
from common import *
import pickle
A=pickle.load(open(f'{CACHE}/nodeA_loops.pkl','rb'))
res={}
for ra,rb,b,_,_ in RUNS:
    z=np.load(f'{CACHE}/{b}_cycles.npz'); seg=z['seg']; n0=z['n0']; n3=z['n3']
    L=A[ra]['loops']; nseg=seg.max()+1
    # for each seg, compare to each file: number of exactly equal cycles (n0 vs loops) over the overlapping cycles
    best=[]
    for j in range(nseg):
        x=n0[seg==j]; xa=n3[seg==j]-1
        sc=[ (np.sum(l[:len(x)]==x) if len(l)>=len(x) and len(l)>0 else -1) for l in L]
        i=int(np.argmax(sc)); s=sorted(sc)[-2]
        best.append((j,i,sc[i],len(x),s, int(np.sum(L[i][:len(x)]==xa)) if len(L[i])>=len(x) else -1))
    best=np.array(best)
    off=best[:,1]-best[:,0]
    print(ra,b,'nseg',nseg,'file-seg offset values',np.unique(off,return_counts=True),
          'segs perfect(n0)',int(np.sum(best[:,2]==best[:,3])),'perfect(n3-1)',int(np.sum(best[:,5]==best[:,3])),
          'min best score',best[:,2].min(),'max 2nd-best',best[:,4].max(), 'imperfect segs',[(int(r[0]),int(r[2]),int(r[3])) for r in best if r[2]!=r[3]][:6])
    res[ra]=best
pickle.dump(res,open(f'{CACHE}/matchA.pkl','wb'))
