"""H-cal falsification test (no NetSquid): does finite-shot calibration make threshold-qualified
delivery calibration-LIMITED in realistic regimes?
Calibration protocol = the Study-18 pilot's: local X/Y/Z parity of consumed pairs at holds {0, 0.4, 1.6}*T2,
known symmetric readout flip q. Parameters fitted by weighted least squares (≈MLE for binomial cells).
Prediction model near threshold = Pauli product model (ledger E3: error <=0.0013 at F>=0.9).
Outputs: parameter error vs pairs/link; margin needed for r_cond<=1%; acceptance loss; overhead fraction."""
import numpy as np, pandas as pd
from scipy.optimize import least_squares
rng=np.random.default_rng(1803)
q=0.03; HOLD_FR=np.array([0.0,0.4,1.6])
def expect(p,T1,T2,t):
    g=1-np.exp(-t/T1); c2=np.exp(-2*t/T2); r=(1-2*q)**2
    return r*(1-p)*c2, -r*(1-p)*c2, r*((1-p)*(1-g)**2+g**2)
def calibrate(p,T1,T2,n):
    holds=HOLD_FR*T2; m=max(n//9,1); obs=[]
    for t in holds:
        for E in expect(p,T1,T2,t):
            k=rng.binomial(m,(1+E)/2); obs.append((t,2*k/m-1))
    obs=np.array(obs)
    def res(th):
        pp,lT1,lT2=th; T1e,T2e=np.exp(lT1),np.exp(lT2)
        pred=np.concatenate([expect(pp,T1e,T2e,t) for t in holds])
        return (pred-obs[:,1])*np.sqrt(m)
    s=least_squares(res,[0.05,np.log(T1*1.3),np.log(T2*0.8)],bounds=([-0.5,np.log(T2*0.05),np.log(T2*0.05)],[0.5,np.log(T1*50),np.log(T2*20)]))
    pp,lT1,lT2=s.x; T2e=min(np.exp(lT2),2*np.exp(lT1))
    return pp,np.exp(lT1),T2e
# --- 1) parameter error vs calibration pairs per link
rows=[]
for n in (250,1000,2250,10000,50000):
    for rep in range(300):
        p=rng.uniform(0.01,0.05); T2=1.0; T1=rng.uniform(1.0,3.0)
        pe,T1e,T2e=calibrate(p,T1,T2,n)
        rows.append((n,pe-p,np.log(T1e/T1),np.log(T2e/T2)))
E=pd.DataFrame(rows,columns="n dp dlogT1 dlogT2".split())
print("1) calibration error vs pairs per link (median-free RMS):")
print(E.groupby("n").agg(rms_dp=("dp",lambda x: np.sqrt((x**2).mean())),rms_rel_T1=("dlogT1",lambda x: np.sqrt((x**2).mean())),rms_rel_T2=("dlogT2",lambda x: np.sqrt((x**2).mean()))).round(4).to_string())
# --- 2) delivery risk / acceptance vs n, path length L, margin m
def F_path(ps,T1s,T2s,waits,pbsm=0.005):
    lx=np.prod(1-np.clip(ps,0,1))*(1-pbsm)**(2*(len(ps)-1)); lz=lx
    lx=lx*np.exp(-2*np.sum(waits/T2s)); lz=lz*np.exp(-2*np.sum(waits/T1s))
    return (1+2*lx+lz)/4
Fth=0.9; out=[]
for n in (250,1000,2250,10000,50000):
    for L in (1,3,6,10):
        Ft=[];Fh=[]
        for net in range(150):                       # each 'net' = L links with fresh params + one calibration of each
            ps=rng.uniform(0.2,1.8,L)*0.06/L; T2s=np.ones(L); T1s=rng.uniform(1,3,L)
            est=[calibrate(ps[i],T1s[i],T2s[i],n) for i in range(L)]
            pe=np.array([e[0] for e in est]); T1e=np.array([e[1] for e in est]); T2e=np.array([e[2] for e in est])
            for req in range(60):
                waits=rng.exponential(0.02/L,L)    # storage per link (units of T2) -> F spread around threshold
                Ft.append(F_path(ps,T1s,T2s,waits)); Fh.append(F_path(pe,T1e,T2e,waits))
        Ft=np.array(Ft); Fh=np.array(Fh)
        for m in (0.0,0.005,0.01,0.02,0.04):
            d=Fh>=Fth+m; good_all=(Ft>=Fth)
            out.append((n,L,m,d.mean(),(d&(Ft<Fth)).sum()/max(d.sum(),1),(d&good_all).mean(),good_all.mean(),np.sqrt(np.mean((Fh-Ft)**2))))
R=pd.DataFrame(out,columns="n L margin deliver_frac r_cond qualified_frac oracle_qualified rms_Ferr".split())
pd.set_option("display.width",200)
print("\n2) risk and qualified fraction (oracle = perfect knowledge, m=0):")
best=[]
for (n,L),g in R.groupby(["n","L"]):
    ok=g[g.r_cond<=0.01]
    b=ok.iloc[0] if len(ok) else g.iloc[-1]
    best.append((n,L,b.margin if len(ok) else np.nan,b.r_cond,b.qualified_frac,b.oracle_qualified,b.qualified_frac/b.oracle_qualified,g.rms_Ferr.iloc[0]))
B=pd.DataFrame(best,columns="n L margin_needed r_cond qualified oracle_qualified fraction_of_oracle rms_Ferr".split())
print(B.round(4).to_string(index=False))
B.to_csv("calibration_overhead_table_v2.csv",index=False); E.to_csv("calibration_param_errors_v2.csv",index=False)
