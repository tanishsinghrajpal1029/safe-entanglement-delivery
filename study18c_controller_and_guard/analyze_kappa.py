"""Kappa analysis (exploratory on v7; PRE-REGISTERED test S2 for v8, see README_v8.md): does the single number kappa = p0*s/P(h>=0) predict r_cond?
r_kappa = kappa * G(a), G(a) = a*Phi(a) + phi(a), a = (mu - off)/s  (small-r, locally-flat-density limit)."""
import math, sys, numpy as np, pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else "des_v8_mac"
R = pd.read_csv(f"{D}/runs.csv"); B = pd.read_csv(f"{D}/bins.csv")
Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2))); phi = lambda x: math.exp(-x * x / 2) / math.sqrt(2 * math.pi)
near = B[(B.h_lo >= -0.005) & (B.h_hi <= 0.005)].groupby("run").attempts.sum().rename("near")
R = R.merge(near, on="run", how="left").fillna({"near": 0})
R["p0"] = R.near / R.attempts / 0.01; R["Pab"] = R.attempts_above / R.attempts
R["kappa"] = R.p0 * R.err_sd / R.Pab.clip(lower=1e-9)
R["a"] = (R.err_mean - R.off_mean) / R.err_sd
R["G"] = [ai * Phi(ai) + phi(ai) for ai in R.a]; R["r_kappa"] = R.kappa * R.G
R["r_meas"] = R.bad / R.delivered.clip(lower=1)
q = R[(R.delivered >= 100) & (R.z >= 1)]
rk = lambda v: pd.Series(v).rank().values
for nm, d in [("all", q)] + [(f"g={g:g} {e}", dd) for (g, e), dd in q.groupby(["g", "est"])]:
    nz = d[d.bad > 0]
    print(f"{nm:22s} n={len(d):3d} spearman(r_meas,r_kappa)={np.corrcoef(rk(d.r_meas), rk(d.r_kappa))[0,1]:.3f}"
          f"  med|ln ratio|(bad>0)={np.median(np.abs(np.log(nz.r_meas/nz.r_kappa))) if len(nz) else float('nan'):.3f}"
          f"  kappa range {d.kappa.min():.3f}-{d.kappa.max():.3f}")
# goodput loss vs kappa at fixed z: fraction of above-threshold attempts delivered
R["power"] = R.qual / R.attempts_above.clip(lower=1)
print(R[R.z >= 1].groupby(["z", pd.cut(R.kappa, [0, .05, .1, .2, .4, .8, 1e9])], observed=True)[["power", "r_meas"]].median().round(4).to_string())

# S2 (pre-registered for v8): at z in {1,2}, across kappa bins (0,.05],(.05,.1],(.1,.2],(.2,.4],(.4,.8]
# median power is non-increasing and median r_cond is non-decreasing (ties allowed).
bins = [0, .05, .1, .2, .4, .8]; ok = True
for z in (1.0, 2.0):
    d = R[(R.z == z) & (R.kappa <= .8)]
    t = d.groupby(pd.cut(d.kappa, bins), observed=False)[["power", "r_meas"]].median()
    mp = bool((t.power.diff().dropna() <= 1e-12).all()); mr = bool((t.r_meas.diff().dropna() >= -1e-12).all())
    print(f"S2 z={z}: power non-increasing={mp}, r_cond non-decreasing={mr}; bins n={d.groupby(pd.cut(d.kappa, bins), observed=False).size().tolist()}")
    ok &= mp and mr
print("S2:", "PASS" if ok else "FAIL")
