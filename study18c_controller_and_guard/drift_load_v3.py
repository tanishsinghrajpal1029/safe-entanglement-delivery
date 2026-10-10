"""Study 18C v3: does LOAD change the drift-frontier result? (development; model-level)
Uses the same validated primitives as drift_frontier_v2.py (exact DEJMPS-with-gate-error table, Werner chains;
NetSquid-checked in E14) and the same eval/dev split. New: each link has capacity R (pairs/s) shared by user
traffic (offered load ell = demand/R) and calibration.
  fixed        : a fixed fraction rho of capacity is reserved for calibration (chosen on dev); users get (1-rho)R.
  opportunistic: calibration only uses idle capacity, n = (1-ell)*R*T pairs per window, no cost to users.
  hybrid       : opportunistic + an extra reserved rho (chosen on dev).
Score (EVAL) = served-qualified-and-delivered / (oracle-qualified * demand), i.e. fraction of the demand that a
perfect-knowledge, zero-overhead network would satisfy. Estimator: rolling static or rolling OLS (chosen on dev).
Simplifications (stated): fluid capacity sharing (no queueing dynamics), calibration preemptible, memory occupancy
of calibration pairs ignored, linear drift on lambda only."""
import numpy as np, pandas as pd, itertools, hashlib, sys
from pathlib import Path
from scipy.interpolate import RegularGridInterpolator
GRID=np.round(np.arange(0.5,1.0001,0.005),6); _t={}
def dej(F1,F2,e):
    if e not in _t: _t[e]=RegularGridInterpolator((GRID,GRID),np.load(f"dejmps_table_e{e}.npy"))
    return _t[e](np.stack([np.clip(F1,0.5,1),np.clip(F2,0.5,1)],-1))
PRE={"ion_2020":dict(F0=0.940,R=182.,T2=1.0,q=0.001,e=0.005),"ion_proj":dict(F0=0.970,R=200.,T2=1.0,q=0.001,e=0.003)}
CELLS=[("ion_2020",2,"purify1"),("ion_proj",3,"purify1"),("ion_proj",2,"raw")]
lamF=lambda F:(4*F-1)/3; Flam=lambda l:(1+3*l)/4
def path_F(l,P,L,s,w1,w2,h):
    b=np.prod(l,axis=-1)*(1-P["e"])**(2*max(L-1,0))
    if s=="raw": return Flam(b*np.exp(-2*w1/P["T2"]))
    return dej(Flam(b*np.exp(-2*(w1+h)/P["T2"])),Flam(b*np.exp(-2*w2/P["T2"])),P["e"])
def draw(P,L,N,rng):
    F0=np.clip(P["F0"]+rng.normal(0,(1-P["F0"])*0.2,(N,L)),0.3,0.99999)
    t=rng.exponential(1/P["R"],(N,L)); t2=rng.exponential(1/P["R"],(N,L))
    return dict(lam=lamF(F0),w1=(t.max(1,keepdims=True)-t).sum(1),w2=(t2.max(1,keepdims=True)-t2).sum(1),hold=t2.max(1),z=rng.normal(0,1,(N,L)))
def est(kind,lam,P,g,n,T,z):
    r=(1-2*P["q"])**2; s=np.sqrt(np.maximum(1-(r*lam)**2,1e-6))/r
    return lam+g*T*0.5+z*s/np.sqrt(n) if kind=="roll_static" else lam+2*z*s/np.sqrt(n)
def evaluate(d,Ft,orc,P,L,s,g,ell,pol,rho,T,kind,m):
    n_cal=((1-ell) if pol in ("opportunistic","hybrid") else 0)*P["R"]*T+(rho if pol in ("fixed","hybrid") else 0)*P["R"]*T
    if n_cal<30: return None
    lh=np.clip(est(kind,d["lam"],P,g,n_cal,T,d["z"]),0,1); Fh=path_F(lh,P,L,s,d["w1"],d["w2"],d["hold"])
    dl=Fh>=0.9+m; rc=(dl&(Ft<0.9)).sum()/max(dl.sum(),1)
    user_cap=1-(rho if pol in ("fixed","hybrid") else 0); served=min(1.0,user_cap/ell)
    return rc,served*(dl&(Ft>=0.9)).mean()/orc
RHO=(0.01,0.03,0.1,0.3); TS=(10,30,100,300,1000,3000); MS=np.round(np.arange(0,0.0801,0.0025),4)
rows=[]
for (pre,L,s),g,ell in itertools.product(CELLS,(1e-6,1e-5,1e-4),(0.3,0.6,0.9,0.99)):
    P=PRE[pre]; key=int(hashlib.sha256(f"{pre}|{L}|{s}|{g}|{ell}".encode()).hexdigest()[:8],16)
    dv=draw(P,L,6000,np.random.default_rng([18601,key])); ev=draw(P,L,6000,np.random.default_rng([18602,key]))
    Fd=path_F(dv["lam"],P,L,s,dv["w1"],dv["w2"],dv["hold"]); od=(Fd>=0.9).mean()
    Fe=path_F(ev["lam"],P,L,s,ev["w1"],ev["w2"],ev["hold"]); oe=(Fe>=0.9).mean()
    for pol in ("fixed","opportunistic","hybrid"):
        best=None
        rhos=(0,) if pol=="opportunistic" else RHO
        for rho,T,kind in itertools.product(rhos,TS,("roll_static","roll_ols")):
            for m in MS:
                r=evaluate(dv,Fd,od,P,L,s,g,ell,pol,rho,T,kind,m)
                if r is None: break
                if r[0]<=0.01:
                    if best is None or r[1]>best[0]: best=(r[1],rho,T,kind,m)
                    break
        if best is None: rows.append(dict(preset=pre,L=L,strategy=s,drift_g=g,load=ell,policy=pol,note="infeasible on dev")); continue
        _,rho,T,kind,m=best; rc,sc=evaluate(ev,Fe,oe,P,L,s,g,ell,pol,rho,T,kind,m)
        rows.append(dict(preset=pre,L=L,strategy=s,drift_g=g,load=ell,policy=pol,rho=rho,T_s=T,estimator=kind,margin=m,
                         EVAL_frac_of_ideal=round(sc,3),EVAL_r_cond_pct=round(100*rc,3)))
OUT=sys.argv[1] if len(sys.argv)>1 else "drift_load_v3_table.csv"
if Path(OUT).exists(): sys.exit(f"{OUT} exists; refusing to overwrite")
D=pd.DataFrame(rows); D.to_csv(OUT,index=False); pd.set_option("display.width",250)
print(D.pivot_table(index=["preset","L","strategy","drift_g"],columns=["load","policy"],values="EVAL_frac_of_ideal").round(3).to_string())
print("max EVAL r_cond %:",D.EVAL_r_cond_pct.max(),"| rows over 1%:",int((D.EVAL_r_cond_pct>1).sum()),"of",len(D))
print("table sha256:",hashlib.sha256(open(OUT,"rb").read()).hexdigest())
