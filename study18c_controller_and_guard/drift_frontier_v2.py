"""Study 18C drift-frontier analysis, v2 (development stage; NumPy surrogate validated against NetSquid 1.1.6:
logs/netsquid_surrogate_check.json -- swap chains to 4e-16, DEJMPS with gate depolarization to 4e-14).
Changes vs drift_floor.py (E11): (1) EXACT DEJMPS with depolarizing gate error e on all four qubits after the
CNOTs (bilinear table from the exact 4-qubit circuit, grid step 0.002); (2) estimators simulated from their exact
sampling distributions, including ROLLING (continuously updated) variants; (3) operating points (rho, T, margin)
selected on DEV draws only and scored once on independent EVAL draws (different seed stream).
Estimators of each link's Werner parameter lambda(t) = lambda0 - g*t (unknown g), from parity pairs at rate rho*R:
  batch_static : window mean, used during next window       -> bias g*(T/2+u), var s^2/n          (u~U(0,T))
  batch_ols    : window OLS extrapolated, used next window    -> bias 0, var s^2/n*(1+12(1/2+u/T)^2)
  roll_static  : sliding-window mean, always current          -> bias g*T/2,      var s^2/n
  roll_ols     : sliding-window OLS extrapolated to now       -> bias 0,          var s^2/n*4
  oracle_known : perfect knowledge (upper reference)
Score = (1-rho) * qualified-and-delivered / oracle-qualified at pooled r_cond <= 1% (EVAL)."""
import numpy as np, pandas as pd, itertools, json, hashlib, sys
from pathlib import Path
from scipy.interpolate import RegularGridInterpolator
sys.path.insert(0,".")
from netsquid_surrogate_check import dejmps_numpy
GRID=np.round(np.arange(0.5,1.0001,0.005),6)
_tables={}
def dej_exact(F1,F2,e):
    if e not in _tables:
        cache=Path(f"dejmps_table_e{e}.npy")
        if cache.exists(): Z=np.load(cache)
        else:
            Z=np.array([[dejmps_numpy(a,b,e)[0] for b in GRID] for a in GRID]); np.save(cache,Z)
        _tables[e]=RegularGridInterpolator((GRID,GRID),Z)
    return _tables[e](np.stack([np.clip(F1,0.5,1),np.clip(F2,0.5,1)],-1))
PRE={"ion_2020":dict(F0=0.940,R=182.,T2=1.0,q=0.001,e=0.005),
     "ion_proj":dict(F0=0.970,R=200.,T2=1.0,q=0.001,e=0.003),
     "aspir_cfg":dict(F0=0.9978,R=1e4,T2=0.08,q=0.01,e=0.0)}
CELLS=[("ion_2020",1,"raw"),("ion_2020",2,"purify1"),("ion_proj",2,"raw"),("ion_proj",3,"purify1"),("aspir_cfg",20,"raw")]
EST=("batch_static","batch_ols","roll_static","roll_ols","oracle_known")
lamF=lambda F:(4*F-1)/3; Flam=lambda l:(1+3*l)/4
def path_F(lams,P,L,strat,w1,w2,hold):
    base=np.prod(lams,axis=-1)*(1-P["e"])**(2*max(L-1,0))
    if strat=="raw": return Flam(base*np.exp(-2*w1/P["T2"]))
    f1=Flam(base*np.exp(-2*(w1+hold)/P["T2"])); f2=Flam(base*np.exp(-2*w2/P["T2"]))
    return dej_exact(f1,f2,P["e"])
def draw(P,L,N,rng):
    F0=np.clip(P["F0"]+rng.normal(0,(1-P["F0"])*0.2,(N,L)),0.3,0.99999)
    t=rng.exponential(1/P["R"],(N,L)); t2=rng.exponential(1/P["R"],(N,L))
    return dict(lam=lamF(F0),w1=(t.max(1,keepdims=True)-t).sum(1),w2=(t2.max(1,keepdims=True)-t2).sum(1),hold=t2.max(1),u=rng.uniform(0,1,(N,L)),z=rng.normal(0,1,(N,L)))
def estimate(est,lam,P,g,rho,T,u,z):
    r=(1-2*P["q"])**2; s=np.sqrt(np.maximum(1-(r*lam)**2,1e-6))/r; n=rho*P["R"]*T
    if est=="oracle_known": return lam
    if est=="batch_static": return lam+g*T*(0.5+u)+z*s/np.sqrt(n)
    if est=="batch_ols":    return lam+z*s/np.sqrt(n)*np.sqrt(1+12*(0.5+u)**2)
    if est=="roll_static":  return lam+g*T*0.5+z*s/np.sqrt(n)
    if est=="roll_ols":     return lam+z*s/np.sqrt(n)*2.0
def score(d,Ft,oracle,P,L,strat,est,g,rho,T,m):
    lh=np.clip(estimate(est,d["lam"],P,g,rho,T,d["u"],d["z"]),0,1)
    Fh=path_F(lh,P,L,strat,d["w1"],d["w2"],d["hold"]); dl=Fh>=0.9+m
    rc=(dl&(Ft<0.9)).sum()/max(dl.sum(),1)
    return rc,(1-(0 if est=="oracle_known" else rho))*(dl&(Ft>=0.9)).mean()/oracle
RHO=(0.01,0.03,0.1,0.3); TS=(1,3,10,30,100,300,1000,3000); MS=np.round(np.arange(0,0.0801,0.0025),4)
rows=[]; NDEV=NEVAL=6000
for (pre,L,strat),g in itertools.product(CELLS,(1e-6,1e-5,1e-4)):
    P=PRE[pre]
    key=int(hashlib.sha256(f"{pre}|{L}|{strat}|{g}".encode()).hexdigest()[:8],16)
    dev=draw(P,L,NDEV,np.random.default_rng([18501,key]))
    ev=draw(P,L,NEVAL,np.random.default_rng([18502,key]))
    Fd=path_F(dev["lam"],P,L,strat,dev["w1"],dev["w2"],dev["hold"]); od=(Fd>=0.9).mean()
    Fe=path_F(ev["lam"],P,L,strat,ev["w1"],ev["w2"],ev["hold"]); oe=(Fe>=0.9).mean()
    if od<0.02: continue
    for est in EST:
        best=None
        grid=[(0,1)] if est=="oracle_known" else [(r,T) for r,T in itertools.product(RHO,TS) if r*P["R"]*T>=30]
        for rho,T in grid:
            for m in MS:
                rc,sc=score(dev,Fd,od,P,L,strat,est,g,rho,T,m)
                if rc<=0.01:
                    if best is None or sc>best[0]: best=(sc,rho,T,m)
                    break
        if best is None: rows.append(dict(preset=pre,L=L,strategy=strat,drift_g=g,estimator=est,note="no dev setting met 1%")); continue
        _,rho,T,m=best
        rc_e,sc_e=score(ev,Fe,oe,P,L,strat,est,g,rho,T,m)
        rows.append(dict(preset=pre,L=L,strategy=strat,drift_g=g,estimator=est,oracle_qualified_eval=round(oe,3),
                         rho=rho,T_s=T,margin=m,dev_score=round(best[0],3),EVAL_net_frac=round(sc_e,3),EVAL_r_cond_pct=round(100*rc_e,3)))
OUTCSV=sys.argv[1] if len(sys.argv)>1 else "drift_frontier_v2_table.csv"
if Path(OUTCSV).exists(): sys.exit(f"{OUTCSV} exists; refusing to overwrite")
D=pd.DataFrame(rows); D.to_csv(OUTCSV,index=False)
pd.set_option("display.width",250)
print(D.to_string(index=False))
piv=D[D.estimator!="oracle_known"].pivot_table(index=["preset","L","strategy","drift_g"],columns="estimator",values="EVAL_net_frac")
print("\nEVAL net fraction of oracle qualified goodput (rows: cell x drift; cols: estimator):\n",piv.round(3).to_string())
print("\nmax EVAL r_cond (%) across all rows:", D.EVAL_r_cond_pct.max())
print("table sha256:", hashlib.sha256(open(OUTCSV,"rb").read()).hexdigest())
