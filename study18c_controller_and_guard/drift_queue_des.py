"""Study 18C v4: discrete-event test of the load x drift effect WITH queueing (development; independent NumPy
implementation using the NetSquid-validated primitives of E14: Werner links, depolarizing storage, noisy BSM,
exact DEJMPS-with-gate-error table).

One L-link path, FIFO single-server (whole-path reservation as in the Study-18 prototype). Requests arrive Poisson;
deadline D counts from arrival (queue wait included). A request in service generates L link pairs in parallel
(each link heralds at rate R_user), swaps, optionally purifies with a second chain (first chain held), then the
controller estimates F from its CURRENT calibration estimate and delivers if F_hat >= 0.9+m, else retries until D.
Link Werner parameter drifts down at rate g and is physically re-aligned every T_re = 0.02/g (sawtooth).
Calibration (per link, independent): consumed pairs in random X/Y/Z bases -> parity counts. Policies:
  fixed rho      : calibration at rate rho*R always; users get (1-rho)*R
  opportunistic  : calibration at rate R only while the path is idle; users get R
  hybrid rho     : rho*R always + R while idle; users get (1-rho)*R
Estimator: sliding window of length T over parity records (counts drawn exactly: Poisson number of calibration
pairs from the realized busy/idle timeline, Binomial parities with the window-average true lambda), unbiased
inversion of the known readout flip q. Oracle reference: true lambda, no calibration cost, same arrival process.
Metrics: qualified deliveries per second (/oracle), r_cond, deadline-miss fraction, mean latency.
Retry budget 4 attempts per request; 300 s warm-up excluded; path draws (lambda0 per link, drift phase) are the
replication unit: dev and eval use disjoint path draws and disjoint random streams.
Dev grid: rho in {0.01,0.03,0.1}, T in {30,100,300} s, margin in {0.005,0.0125,0.025,0.04}."""
import numpy as np, pandas as pd, itertools, hashlib, sys, bisect
from pathlib import Path
from scipy.interpolate import RegularGridInterpolator
GRID=np.round(np.arange(0.5,1.0001,0.005),6); _t={}
def dej(F1,F2,e):
    # bilinear lookup on the exact-circuit table (same arithmetic as RegularGridInterpolator 'linear')
    if e not in _t: _t[e]=np.load(f"dejmps_table_e{e}.npy")
    Z=_t[e]; n=len(GRID)-1
    x=(min(max(F1,0.5),1.0)-0.5)/0.005; y=(min(max(F2,0.5),1.0)-0.5)/0.005
    i=min(int(x),n-1); j=min(int(y),n-1); fx=x-i; fy=y-j
    return float((1-fx)*(1-fy)*Z[i,j]+fx*(1-fy)*Z[i+1,j]+(1-fx)*fy*Z[i,j+1]+fx*fy*Z[i+1,j+1])
PRE={"ion_2020":dict(F0=0.940,R=182.,T2=1.0,q=0.001,e=0.005),"ion_proj":dict(F0=0.970,R=200.,T2=1.0,q=0.001,e=0.003)}
Flam=lambda l:(1+3*l)/4
def chainF(lams,P,L,waits):
    return Flam(np.prod(lams)*(1-P["e"])**(2*(L-1))*np.exp(-2*waits/P["T2"]))
class Run:
    def __init__(s,P,L,purify,g,load,policy,rho,T,m,D,horizon,seed,oracle=False,mu=None,lam0=None,phase=0.0,budget=4,warm=300.0):
        s.P,s.L,s.pur,s.g,s.pol,s.rho,s.T,s.m,s.D,s.H,s.or_=P,L,purify,g,policy,rho,T,m,D,horizon,oracle
        s.rng=np.random.default_rng(seed); s.Tre=0.02/g; s.phase=phase; s.budget=budget; s.warm=warm
        s.lam0=lam0
        s.Ruser=P["R"]*(1-(rho if policy in ("fixed","hybrid") else 0)) if not oracle else P["R"]
        s.lam_arr=load*(mu if mu else 1.0)
        s.busy=[]   # list of (start,end) busy intervals, sorted
        s.bs=[]; s.be=[]; s.cum=[0.0]   # starts, ends, cumulative busy time (for O(log n) window queries)
    def lam_true(s,t): return s.lam0-s.g*((t+s.phase)%s.Tre)
    def lam_avg(s,a,b):
        # average of sawtooth over [a,b]: integrate piecewise
        if b<=a: return s.lam_true(b)
        # exact average of the sawtooth lam0 - g*((t+phase) mod Tre) over [a,b]
        def I(t):   # integral of ((t+phase) mod Tre) dt from 0 to t
            u=t+s.phase; k=np.floor(u/s.Tre); r=u-k*s.Tre
            return k*s.Tre**2/2+r**2/2
        return s.lam0-s.g*(I(b)-I(a))/(b-a)
    def B(s,t):
        # total busy time in [0,t]; intervals are disjoint and sorted (single FIFO server)
        i=bisect.bisect_right(s.bs,t)
        if i==0: return 0.0
        base=s.cum[i-1]; x,y=s.bs[i-1],s.be[i-1]
        return base+max(0.0,min(t,y)-x)
    def busy_in(s,a,b): return s.B(b)-s.B(a)
    def estimate(s,t):
        if s.or_: return s.lam_true(t)
        a=max(0.0,t-s.T); W=t-a
        if W<=0: return np.full(s.L,0.95)
        busy=s.busy_in(a,t); idle=W-busy
        rate_time=(s.rho*s.P["R"]*W if s.pol in ("fixed","hybrid") else 0)+(s.P["R"]*idle if s.pol in ("opportunistic","hybrid") else 0)
        r=(1-2*s.P["q"])**2; lb=np.clip(s.lam_avg(a,t),0,1); out=np.empty(s.L)
        for i in range(s.L):
            n=s.rng.poisson(rate_time)
            if n<5: out[i]=np.nan; continue
            k=s.rng.binomial(n,(1+r*lb[i])/2); out[i]=(2*k/n-1)/r
        return out
    def chain(s,t):
        tt=s.rng.exponential(1/s.Ruser,s.L); done=t+tt.max(); waits=(tt.max()-tt).sum()
        return done,waits
    def serve(s,t0,deadline):
        t=t0; pairs=0; att=0
        while True:
            att+=1
            lam=s.lam_true(t)
            d1,w1=s.chain(t); pairs+=s.L
            if s.pur:
                d2,w2=s.chain(d1); pairs+=s.L; hold=d2-d1
                F1=chainF(lam,s.P,s.L,w1+hold); F2=chainF(lam,s.P,s.L,w2); Ft=dej(F1,F2,s.P["e"])
                psucc=None; tdone=d2
            else:
                Ft=chainF(lam,s.P,s.L,w1); tdone=d1
            if tdone>deadline: return deadline,"miss",None,pairs
            lh=s.estimate(tdone)
            if np.any(np.isnan(lh)): Fh=0.0
            else:
                lh=np.clip(lh,0,1)
                if s.pur: Fh=dej(chainF(lh,s.P,s.L,w1+hold),chainF(lh,s.P,s.L,w2),s.P["e"])
                else: Fh=chainF(lh,s.P,s.L,w1)
            if Fh>=0.9+s.m: return tdone,"deliver",Ft,pairs
            if att>=s.budget: return tdone,"budget",None,pairs
            t=tdone
    def go(s):
        t=0.0; free=0.0; out=[]
        while True:
            t+=s.rng.exponential(1/s.lam_arr)
            if t>s.H+s.warm: break
            start=max(t,free); dl=t+s.D
            if start>=dl:
                if t>=s.warm: out.append((t,"miss",None,0,start-t))
                continue
            end,res,F,pairs=s.serve(start,dl)
            s.busy.append((start,end)); s.bs.append(start); s.be.append(end); s.cum.append(s.cum[-1]+(end-start)); free=end
            if t>=s.warm: out.append((t,res,F,pairs,end-t))
        return out
def summarize(out,H):
    d=pd.DataFrame(out,columns="t res F pairs latency".split()); dl=d[d.res=="deliver"]
    good=(dl.F>=0.9).sum(); bad=(dl.F<0.9).sum()
    return dict(n=len(d),qual_rate=good/H,r_cond=bad/max(len(dl),1),miss=(d.res=="miss").mean(),latency_ms=1e3*d.latency.mean())
CELLS=[("ion_2020",2,True),("ion_proj",3,True)]
def draw_paths(P,L,n,seed):
    rng=np.random.default_rng(seed)
    return [((4*np.clip(P["F0"]+rng.normal(0,(1-P["F0"])*0.2,L),0.3,0.9999)-1)/3, float(rng.uniform(0,1))) for _ in range(n)]
def service_mu(P,L,pur,lam0,D):
    r=Run(P,L,pur,1e-6,1.0,"none",0,1,0.0,D,200,[9,1],oracle=True,lam0=lam0,warm=0.0); r.lam_arr=0.5
    o=r.go(); busy=sum(y-x for x,y in r.busy); return max(len(r.busy),1)/max(busy,1e-9)
def run_cell(P,L,pur,g,load,pol,rho,T,m,D,H,paths,seed0,oracle=False):
    q=bad=dl=miss=n=0; lat=[]
    for j,(lam0,ph) in enumerate(paths):
        mu=service_mu(P,L,pur,lam0,D)
        r=Run(P,L,pur,g,load,pol,rho,T,m,D,H,[seed0,j],oracle=oracle,mu=mu,lam0=lam0,phase=ph*0.02/g)
        o=r.go(); d=pd.DataFrame(o,columns="t res F pairs latency".split()); x=d[d.res=="deliver"]
        q+=(x.F>=0.9).sum(); bad+=(x.F<0.9).sum(); dl+=len(x); miss+=(d.res=="miss").sum(); n+=len(d); lat+=list(d.latency)
    return dict(qual_per_s=q/(H*len(paths)),r_cond=bad/max(dl,1),miss=miss/max(n,1),latency_ms=1e3*float(np.mean(lat)) if lat else np.nan,n=n,delivered=dl)
COMBOS=[(c,g,load) for c in CELLS for g in (1e-5,1e-4) for load in (0.5,0.9,0.97)]
def run_combo(idx,outdir,H=300.0,NP=8,D=0.25):
    (pre,L,pur),g,load=COMBOS[idx]; P=PRE[pre]; out=Path(outdir)/f"combo_{idx:02d}.csv"
    if out.exists(): return f"skip {out} (exists)"
    dev_paths=draw_paths(P,L,NP,[18801,L]); eval_paths=draw_paths(P,L,NP,[18802,L])
    key=int(hashlib.sha256(f"{pre}|{L}|{g}|{load}".encode()).hexdigest()[:8],16)
    orc=run_cell(P,L,pur,g,load,"none",0,1,0.0,D,H,eval_paths,key,oracle=True); rows=[]
    for pol in ("fixed","opportunistic","hybrid"):
        best=None; tried=0
        for rho,T,m in itertools.product((0,) if pol=="opportunistic" else (0.01,0.03,0.1),(100,300),(0.0125,0.025,0.04)):
            dev=run_cell(P,L,pur,g,load,pol,rho,T,m,D,H,dev_paths,key+1); tried+=1
            if dev["r_cond"]<=0.01 and (best is None or dev["qual_per_s"]>best[0]): best=(dev["qual_per_s"],rho,T,m)
        base=dict(combo=idx,preset=pre,L=L,drift_g=g,load=load,policy=pol,dev_settings_tried=tried,
                  oracle_qual_per_s=round(orc["qual_per_s"],4),oracle_miss=round(orc["miss"],4),oracle_latency_ms=round(orc["latency_ms"],1))
        if best is None: rows.append({**base,"note":"no dev setting met r_cond<=1%"}); continue
        _,rho,T,m=best; ev=run_cell(P,L,pur,g,load,pol,rho,T,m,D,H,eval_paths,key)
        rows.append({**base,"rho":rho,"T_s":T,"margin":m,
                     "EVAL_qual_frac_of_oracle":round(ev["qual_per_s"]/max(orc["qual_per_s"],1e-12),4),
                     "EVAL_r_cond_pct":round(100*ev["r_cond"],3),"EVAL_delivered":ev["delivered"],
                     "EVAL_miss":round(ev["miss"],4),"EVAL_latency_ms":round(ev["latency_ms"],1)})
    pd.DataFrame(rows).to_csv(out,index=False); return f"done {out}"
if __name__=="__main__":
    import argparse, multiprocessing as mp, time, json, platform
    ap=argparse.ArgumentParser(); ap.add_argument("--outdir",default="des_v4"); ap.add_argument("--workers",type=int,default=max(1,mp.cpu_count()-1))
    ap.add_argument("--combos",default="all"); ap.add_argument("--horizon",type=float,default=300.0); ap.add_argument("--paths",type=int,default=8)
    a=ap.parse_args(); Path(a.outdir).mkdir(exist_ok=True)
    idx=list(range(len(COMBOS))) if a.combos=="all" else [int(x) for x in a.combos.split(",")]
    t0=time.time(); print(f"{len(idx)} combos on {a.workers} workers; horizon {a.horizon}s + 300s warm-up; {a.paths} dev + {a.paths} eval paths",flush=True)
    with mp.Pool(a.workers) as pool:
        for msg in pool.starmap(run_combo,[(i,a.outdir,a.horizon,a.paths) for i in idx]): print(msg,flush=True)
    files=sorted(Path(a.outdir).glob("combo_*.csv"))
    if len(files)==len(COMBOS):
        D_=pd.concat([pd.read_csv(f) for f in files]); D_.to_csv(Path(a.outdir)/"ALL.csv",index=False)
        pd.set_option("display.width",250)
        cols=[c for c in ("EVAL_qual_frac_of_oracle",) if c in D_]
        print(D_.pivot_table(index=["preset","L","drift_g"],columns=["load","policy"],values="EVAL_qual_frac_of_oracle").round(3).to_string())
        print("max EVAL r_cond %:",D_.get("EVAL_r_cond_pct",pd.Series(dtype=float)).max())
        print("ALL.csv sha256:",hashlib.sha256(open(Path(a.outdir)/"ALL.csv","rb").read()).hexdigest())
    json.dump({"elapsed_s":round(time.time()-t0,1),"python":platform.python_version(),"workers":a.workers,"combos":idx},open(Path(a.outdir)/f"run_meta_{int(t0)}.json","w"))
    print(f"elapsed {time.time()-t0:.0f} s")
