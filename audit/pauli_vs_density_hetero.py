import itertools, numpy as np, pandas as pd
exec(open("pauli_vs_density.py").read().split("rows=[]")[0])   # reuse helpers only
rng=np.random.default_rng(18)
def chain(ps, waits, T1s, T2s, t_after, T1end, T2end):
    """L links; link i between node i and i+1; waits[i] = storage of link i's two qubits before final swap.
    Swaps done sequentially left-to-right: (A,R1)+(R1',R2) -> (A,R2) ... Each stored qubit decays with its node's T1/T2."""
    L=len(ps); nodesT1=T1s; nodesT2=T2s
    # link i qubits sit at node i (left) and node i+1 (right)
    st=depol2(PHI,ps[0]); st=ad_deph(st,0,2,waits[0],T1s[0],T2s[0]); st=ad_deph(st,1,2,waits[0],T1s[1],T2s[1])
    branches=[(1.0,st,())]
    for i in range(1,L):
        nl=depol2(PHI,ps[i]); nl=ad_deph(nl,0,2,waits[i],T1s[i],T2s[i]); nl=ad_deph(nl,1,2,waits[i],T1s[i+1],T2s[i+1])
        new=[]
        for pr,s,oc in branches:
            for k,(q,ab) in enumerate(swap(np.kron(s,nl))):
                new.append((pr*q,ab,oc+(k,)))
        branches=new
    out=[]
    for pr,ab,oc in branches:
        ab=ad_deph(ab,0,2,t_after,T1end[0],T2end[0]); ab=ad_deph(ab,1,2,t_after,T1end[1],T2end[1])
        out.append((pr,F(ab),oc))
    # Pauli model: product of per-qubit factors
    lx=np.prod([1-p for p in ps]); lz=lx
    for i in range(L):
        for n in (i,i+1):
            lx*=np.exp(-waits[i]/T2s[n]); lz*=np.exp(-waits[i]/T1s[n])
    for n,T1e,T2e in ((0,T1end[0],T2end[0]),(1,T1end[1],T2end[1])):
        lx*=np.exp(-t_after/T2e); lz*=np.exp(-t_after/T1e)
    return out,(1+2*lx+lz)/4
rows=[]
for trial in range(4000):
    L=int(rng.integers(2,4))
    T1s=rng.uniform(0.3,3.0,L+1); T2s=np.minimum(2*T1s, T1s*rng.uniform(0.2,2.0,L+1))
    ps=rng.uniform(0,0.08,L); waits=rng.exponential(rng.choice([0.01,0.05,0.2]),L)
    t_after=rng.choice([0,0.02,0.1])
    out,Fp=chain(ps,waits,T1s,T2s,t_after,(T1s[0],T1s[-1]),(T2s[0],T2s[-1]))
    for pr,Ft,oc in out:
        rows.append((trial,L,pr,Ft,Fp,str(oc)))
d=pd.DataFrame(rows,columns="trial L prob F_true F_pauli outcome".split()); d["err"]=d.F_pauli-d.F_true
spread=d.groupby("trial").F_true.agg(lambda x: x.max()-x.min())
print("trials",d.trial.nunique(),"| max spread of true F across Bell outcomes within a trial:", round(spread.max(),6))
for lo in (0.95,0.9,0.85,0.8):
    s=d[(d.F_true>=lo)|(d.F_pauli>=lo)]
    print(f"F>={lo}: n={len(s)} max|err|={s.err.abs().max():.4f}  Pauli overestimates (err>1e-9) in {(s.err>1e-9).sum()} rows; max overestimate {max(s.err.max(),0):.5f}")
mis=d[(d.F_pauli>=0.9)&(d.F_true<0.9)]
print("rows where Pauli says >=0.9 but truth <0.9 (would be a BAD delivery):", len(mis))
print("rows where Pauli says <0.9 but truth >=0.9 (lost goodput):", len(d[(d.F_pauli<0.9)&(d.F_true>=0.9)]), "of", len(d))
g=d.assign(w=d.prob*d.F_true).groupby("trial").agg(Favg=("w","sum"),spread=("F_true",lambda x:x.max()-x.min()))
for lo,hi in ((0.95,1.01),(0.9,0.95),(0.85,0.9),(0.8,0.85),(0.6,0.8),(0,0.6)):
    s=g[(g.Favg>=lo)&(g.Favg<hi)]
    if len(s): print(f"avg F in [{lo},{hi}): trials={len(s)} max outcome spread={s.spread.max():.5f} median={s.spread.median():.6f}")
