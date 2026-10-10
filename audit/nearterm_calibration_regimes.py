"""Near-term regime map: is verified (threshold-qualified) delivery calibration-limited?
Independent NumPy model (no NetSquid). Bell-diagonal / Werner algebra is adequate near F_th>=0.85
(ledger E3: max Pauli-model error 0.0013 for F>=0.9 in heterogeneous T1/T2 chains).

Per platform preset: link Werner fidelity F0 (heterogeneous +-), heralded rate R (Hz), memory T2 (s),
readout flip q, BSM/gate depolarization e, drift period T_d (s).
Delivery strategies on an L-link chain: raw swap, or 1 round of end-to-end DEJMPS on two raw chain pairs.
Calibration: each link's Werner parameter lambda is estimated from n consumed pairs measured in X/Y/Z
(unbiased parity estimator with known readout q). Memory T2 and gate errors treated as known (stated assumption).
Decision: deliver iff F_hat >= F_th + m. Outputs: oracle-qualified fraction, kept fraction at r_cond<=1%,
pairs/link needed, and calibration overhead = n / (R * T_d)."""
import numpy as np, pandas as pd, itertools
rng=np.random.default_rng(18301)
PRESETS={ # name: F0, R_Hz, T2_s, q, e_gate, T_drift_s, source
 "ion_2020":   dict(F0=0.940,R=182.0,T2=1.0,q=0.001,e=0.005,Td=1e4),   # Stephenson+ PRL 2020 (F, R); T2,q,e,Td assumed
 "ion_proj":   dict(F0=0.970,R=200.0,T2=1.0,q=0.001,e=0.003,Td=1e4),   # projected
 "nv_2021":    dict(F0=0.820,R=9.0,  T2=0.01,q=0.03, e=0.01, Td=1e4),  # Pompili+ 2021 (F, R); T2 network-active ~10 ms assumed
 "aspir_cfg":  dict(F0=0.9978,R=1e4, T2=0.08,q=0.01, e=0.0,  Td=1e4),  # project config (lambda~0.997, ideal BSM)
}
def lam_from_F(F): return (4*F-1)/3
def F_from_lam(l): return (1+3*l)/4
def chain_lam(lams,e,waits,T2):
    L=len(lams); return np.prod(lams)*(1-e)**(2*max(L-1,0))*np.exp(-2*np.sum(waits)/T2)
def dejmps_werner(F1,F2):
    # Werner inputs: Bell-diagonal weights (F,(1-F)/3,(1-F)/3,(1-F)/3); DEJMPS closed form
    a1,b1=F1,(1-F1)/3; a2,b2=F2,(1-F2)/3
    A1,B1,C1,D1=a1,b1,b1,b1; A2,B2,C2,D2=a2,b2,b2,b2
    N=(A1+B1)*(A2+B2)+(C1+D1)*(C2+D2)
    return (A1*A2+B1*B2)/N, N
def est_lam(lam_true,q,n,rng):
    r=(1-2*q)**2; E=r*lam_true; m=max(n//3,1)
    vals=[ (2*rng.binomial(m,(1+E)/2)/m-1) for _ in range(3)]   # XX, -YY, ZZ all have expectation r*lambda
    return float(np.mean(vals))/r
Fth=0.9; rows=[]
for name,P in PRESETS.items():
    for L in (1,2,3,4):
        for strat in ("raw","purify1"):
            for n in (300,1000,3000,10000,30000,100000):
                Ft=[];Fh=[]
                for net in range(120):
                    F0s=np.clip(P["F0"]+rng.normal(0,(1-P["F0"])*0.2,L),0.3,0.99999); lt=lam_from_F(F0s)
                    lh=np.array([est_lam(x,P["q"],n,rng) for x in lt])
                    for req in range(40):
                        # storage: each link waits for the slowest link ~ Exp(1/R) order stats; use per-link wait
                        t=rng.exponential(1/P["R"],L); waits=(t.max()-t)
                        if strat=="raw":
                            Ft.append(F_from_lam(chain_lam(lt,P["e"],waits,P["T2"]))); Fh.append(F_from_lam(chain_lam(lh,P["e"],waits,P["T2"])))
                        else:
                            t2=rng.exponential(1/P["R"],L); w2=(t2.max()-t2); hold=t2.max()   # first pair waits for second chain
                            f1=F_from_lam(chain_lam(lt,P["e"],waits,P["T2"])*np.exp(-2*hold/P["T2"])); f2=F_from_lam(chain_lam(lt,P["e"],w2,P["T2"]))
                            g1=F_from_lam(chain_lam(lh,P["e"],waits,P["T2"])*np.exp(-2*hold/P["T2"])); g2=F_from_lam(chain_lam(lh,P["e"],w2,P["T2"]))
                            Ft.append(dejmps_werner(f1,f2)[0]*(1-P["e"])+P["e"]/4); Fh.append(dejmps_werner(g1,g2)[0]*(1-P["e"])+P["e"]/4)
                Ft=np.array(Ft);Fh=np.array(Fh); orc=(Ft>=Fth).mean()
                best=None
                for m in np.arange(0,0.061,0.0025):
                    d=Fh>=Fth+m; rc=((d)&(Ft<Fth)).sum()/max(d.sum(),1)
                    if rc<=0.01: best=(m,(d&(Ft>=Fth)).mean()); break
                rows.append(dict(preset=name,L=L,strategy=strat,n=n,oracle_qualified=orc,
                                 margin=None if best is None else round(best[0],4),
                                 kept_frac=None if (best is None or orc==0) else best[1]/orc,
                                 overhead_frac=n/(P["R"]*P["Td"])))
D=pd.DataFrame(rows); D.to_csv("nearterm_regime_map.csv",index=False)
pd.set_option("display.width",220)
feas=D.groupby(["preset","L","strategy"]).oracle_qualified.first().unstack().round(3)
print("ORACLE-qualified fraction at F_th=0.9 (perfect knowledge):\n",feas.to_string())
ok=D[(D.oracle_qualified>=0.05)]
need=ok[ok.kept_frac>=0.9].groupby(["preset","L","strategy"]).agg(n_needed=("n","min"),overhead=("overhead_frac","min")).reset_index()
print("\nMin calibration pairs/link (per drift period) to keep >=90% of oracle-qualified at r_cond<=1%, and overhead fraction:")
print(need.to_string(index=False))
miss=ok.groupby(["preset","L","strategy"]).kept_frac.max().reset_index(); miss=miss[miss.kept_frac<0.9]
print("\nfeasible cells NOT reaching 90% kept even at 1e5 pairs/link:\n",miss.round(3).to_string(index=False))
