"""Does link-fidelity DRIFT impose a precision floor on verified delivery?
Per link the Werner parameter lambda drifts down at rate g (1/s). A calibration window of length T uses a
fraction rho of the link's heralded pairs (rate R) for X/Y/Z parity estimation (readout q).
Static estimator: mean over window -> unbiased for window-midpoint value; used for the NEXT window, so at
use time it overestimates lambda by g*(T/2+u), u~U(0,T) (stale -> unsafe direction).
Drift-aware estimator: regresses on time inside the window and extrapolates (removes bias, inflates variance x ~4..7).
For each (preset, L, strategy, g, estimator) we grid-search rho, T and margin m (dev-style selection), requiring
pooled r_cond <= 1%, and report the best NET qualified rate = (1-rho)*qualified_kept / oracle_qualified."""
import numpy as np, pandas as pd, itertools
rng=np.random.default_rng(18302)
PRE={"ion_2020":dict(F0=0.940,R=182.,T2=1.0,q=0.001,e=0.005),
     "ion_proj":dict(F0=0.970,R=200.,T2=1.0,q=0.001,e=0.003),
     "aspir_cfg":dict(F0=0.9978,R=1e4,T2=0.08,q=0.01,e=0.0)}
CELLS=[("ion_2020",1,"raw"),("ion_2020",2,"purify1"),("ion_proj",2,"raw"),("ion_proj",3,"purify1"),
       ("aspir_cfg",10,"raw"),("aspir_cfg",20,"raw")]
lamF=lambda F:(4*F-1)/3; Flam=lambda l:(1+3*l)/4
def dej(F1,F2):
    b1,b2=(1-F1)/3,(1-F2)/3; N=(F1+b1)*(F2+b2)+(2*b1)*(2*b2); return (F1*F2+b1*b2)/N
def path_F(lams,P,L,strat,waits,w2,hold):
    base=np.prod(lams,axis=-1)*(1-P["e"])**(2*max(L-1,0))
    if strat=="raw": return Flam(base*np.exp(-2*waits/P["T2"]))
    f1=Flam(base*np.exp(-2*(waits+hold)/P["T2"])); f2=Flam(base*np.exp(-2*w2/P["T2"]))
    return dej(f1,f2)*(1-P["e"])+P["e"]/4
NREQ=6000; Fth=0.9; out=[]
for (pre,L,strat),g,est in itertools.product(CELLS,(1e-6,1e-5,1e-4),("static","drift_aware")):
    P=PRE[pre]; r=(1-2*P["q"])**2
    F0=np.clip(P["F0"]+rng.normal(0,(1-P["F0"])*0.2,(NREQ,L)),0.3,0.99999)
    lam_true=lamF(F0)
    t=rng.exponential(1/P["R"],(NREQ,L)); waits=(t.max(1,keepdims=True)-t).sum(1)
    t2=rng.exponential(1/P["R"],(NREQ,L)); w2=(t2.max(1,keepdims=True)-t2).sum(1); hold=t2.max(1)
    Ft=path_F(lam_true,P,L,strat,waits,w2,hold); oracle=(Ft>=Fth).mean()
    if oracle<0.02: continue
    best=(0,None)
    s1=np.sqrt(np.maximum(1-(r*lam_true)**2,1e-6))/r       # per-pair std of the lambda estimator
    for rho,T in itertools.product((0.01,0.03,0.1,0.3),(1,3,10,30,100,300,1000,3000)):
        n=rho*P["R"]*T
        if n<30: continue
        u=rng.uniform(0,T,(NREQ,L))
        if est=="static":
            bias=g*(T/2+u); sd=s1/np.sqrt(n)
        else:
            bias=np.zeros_like(u); sd=s1/np.sqrt(n)*np.sqrt(4+12*(u/T)+12*(u/T)**2)  # OLS extrapolation var factor (1+12*(dt)^2/T^2) approx, dt=T/2+u
        lam_hat=lam_true+bias+rng.normal(0,1,(NREQ,L))*sd      # estimate refers to the past (higher) value
        Fh=path_F(np.clip(lam_hat,0,1),P,L,strat,waits,w2,hold)
        for m in np.arange(0,0.0801,0.0025):
            d=Fh>=Fth+m; rc=(d&(Ft<Fth)).sum()/max(d.sum(),1)
            if rc<=0.01:
                net=(1-rho)*(d&(Ft>=Fth)).mean()/oracle
                if net>best[0]: best=(net,dict(rho=rho,T=T,n=round(n),m=round(m,4)))
                break
    out.append(dict(preset=pre,L=L,strategy=strat,drift_g=g,estimator=est,oracle_qualified=round(oracle,3),
                    best_net_frac_of_oracle=round(best[0],3),**(best[1] or {})))
D=pd.DataFrame(out); D.to_csv("drift_floor_table.csv",index=False)
pd.set_option("display.width",220); print(D.to_string(index=False))
