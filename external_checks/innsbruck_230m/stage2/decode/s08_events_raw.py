# Herald list: in-window ([5.5,23] us after ch0) two-click coincidences on two distinct detectors, with pattern label.
from common import *
PAT={(2,6):'psi+',(4,5):'psi+',(2,5):'psi-',(4,6):'psi-',(2,4):'par',(5,6):'par'}
LO,HI=5.5,23.0
def heralds(lo=LO,hi=HI):
    df=pd.read_csv(f'{CACHE}/coinc_candidates.csv',dtype={'run':str})
    rows=[]
    for r in df.itertuples():
        ch=list(map(int,r.chs.split(','))); ts=list(map(float,r.ts.split(',')))
        sel=[(c,t) for c,t in zip(ch,ts) if lo<=t<=hi]
        dets=set(c for c,_ in sel)
        if len(sel)!=2 or len(dets)!=2: continue
        p=tuple(sorted(dets))
        rows.append(dict(run=r.run,seg=r.seg,cyc=r.cyc_in_seg,attempt=r.attempt,n_att=r.n_att,last_cycle=r.last_cycle,
                         t0_s=r.t0_s,pat=f'{p[0]}{p[1]}',kind=PAT[p],tau=abs(sel[0][1]-sel[1][1]),t1=min(sel[0][1],sel[1][1]),t2=max(sel[0][1],sel[1][1])))
    return pd.DataFrame(rows)
