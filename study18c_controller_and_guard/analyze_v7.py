"""Pre-registered analysis of des_v7_mac (README_v7.md R1-R3). Pure numpy/pandas (no scipy)."""
import math, sys, hashlib
import numpy as np, pandas as pd
D = sys.argv[1] if len(sys.argv) > 1 else "des_v7_mac"
R = pd.read_csv(f"{D}/runs.csv"); B = pd.read_csv(f"{D}/bins.csv")
Phi = np.vectorize(lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2))))
B = B[np.isfinite(B.h_lo) & np.isfinite(B.h_hi)].copy(); B["h"] = (B.h_lo + B.h_hi) / 2
X = B.merge(R[["run", "cell", "g", "est", "z", "F0", "err_mean", "err_sd", "off_mean", "delivered", "bad"]], on="run")
X["pred"] = Phi((X.h + X.err_mean - X.off_mean) / X.err_sd); X["obs"] = X.delivered_x / X.attempts
def rank(a): return pd.Series(a).rank().values
def spearman(a, b): return float(np.corrcoef(rank(a), rank(b))[0, 1])
def kendall(a, b):
    n = len(a); s = 0
    for i in range(n):
        for j in range(i + 1, n): s += np.sign(a[i] - a[j]) * np.sign(b[i] - b[j])
    return s / (n * (n - 1) / 2)
print("=== R1: Gaussian error model, max |obs-pred| over bins with >=200 attempts (per run), z>=1")
r1 = X[(X.attempts >= 200) & (X.z >= 1)].assign(dev=lambda d: (d.obs - d.pred).abs()).groupby(["run", "cell", "g", "est"]).dev.max().reset_index()
print(r1.groupby(["g", "est"]).dev.median().round(4).to_string())
pre = r1[r1.g <= 1e-5].dev.median()
print(f"R1 pre-registered statistic (g<=1e-5): median of per-run max dev = {pre:.4f}  -> {'PASS' if pre <= 0.05 else 'FAIL'} (bar 0.05)")
print("=== R2: r_cond predicted from each run's own attempt histogram")
X["pa"] = X.attempts * X.pred
P = X.groupby("run").apply(lambda d: d.loc[d.h < 0, "pa"].sum() / max(d.pa.sum(), 1e-12)).rename("r_pred").reset_index()
Q = R.merge(P, on="run"); Q["r_meas"] = Q.bad / Q.delivered.clip(lower=1)
q = Q[(Q.delivered >= 100) & (Q.z >= 1)]
rho = spearman(q.r_pred.values, q.r_meas.values)
nz = q[(q.bad > 0) & (q.r_pred > 0)]; mlr = float(np.median(np.abs(np.log(nz.r_meas / nz.r_pred))))
cc = float(np.median(np.abs(np.log(((q.bad + 0.5) / (q.delivered + 1)) / q.r_pred.clip(lower=1e-9)))))
print(f"runs={len(q)}  Spearman={rho:.3f} (bar 0.9)  median|ln ratio| (bad>0, n={len(nz)})={mlr:.3f}  (0.5-corrected, all)={cc:.3f}  bar ln1.5={math.log(1.5):.3f}")
print("R2:", "PASS" if rho >= 0.9 and mlr <= math.log(1.5) else "FAIL")
for (g, est), d in q.groupby(["g", "est"]):
    dd = d[(d.bad > 0)]
    print(f"   g={g:g} {est:9s} n={len(d):3d} spearman={spearman(d.r_pred.values, d.r_meas.values):.3f} med|lnratio|={np.median(np.abs(np.log(dd.r_meas/dd.r_pred.clip(lower=1e-12)))) if len(dd) else float('nan'):.3f} pooled meas={d.bad.sum()/d.delivered.sum():.4f} pooled pred={(d.r_pred*d.delivered).sum()/d.delivered.sum():.4f}")
print("=== R3: base-rate dependence, Kendall tau(F0, r_cond) per (cell,g,est,z>=1) series")
A = R[R.z >= 1].groupby(["cell", "g", "est", "z", "F0"])[["bad", "delivered"]].sum().reset_index()
A["r"] = A.bad / A.delivered.clip(lower=1)
taus = A.groupby(["cell", "g", "est", "z"]).apply(lambda d: kendall(d.F0.values, d.r.values)).rename("tau").reset_index()
print(taus.to_string(index=False)); frac = (taus.tau <= -0.6).mean()
print(f"R3: {frac:.2f} of {len(taus)} series have tau <= -0.6 (bar 0.75) -> {'PASS' if frac >= 0.75 else 'FAIL'}")
Q.to_csv(f"{D}/analysis_v7_runs.csv", index=False)
print("analysis script sha256:", hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
