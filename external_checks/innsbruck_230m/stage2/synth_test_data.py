import numpy as np, pandas as pd, sys
rng=np.random.default_rng(int(sys.argv[1])); drift=float(sys.argv[2]); rate_drift=float(sys.argv[3])
runs=[]; ev=[]
bases=[(x,y) for x in "XYZ" for y in "XYZ"]
for i,(ba,bb) in enumerate(bases):
    run=f"r{i}"; dur=1200.0; runs.append((run,0.0,dur))
    n=rng.poisson(55); 
    # rate drift: thinning
    t=np.sort(rng.uniform(0,dur,int(n*1.6)))
    keep=rng.uniform(size=len(t)) < (1-rate_drift*t/dur)/1.6*1.6*0.62
    t=t[keep]
    for tt in t:
        h="psi+" if rng.uniform()<0.5 else "psi-"
        corr = 0.85 if ba==bb else 0.0
        corr = corr*(1 - drift*tt/dur)
        p_agree=(1+corr)/2 if h=="psi+" else (1-corr)/2
        a=rng.integers(2); b=a if rng.uniform()<p_agree else 1-a
        ev.append((run,tt,h,ba,bb,a,b))
pd.DataFrame(ev,columns="run t_s herald basisA basisB a b".split()).to_csv("events.csv",index=False)
pd.DataFrame(runs,columns="run t_start_s t_end_s".split()).to_csv("runs.csv",index=False)
