#!/usr/bin/env python3
"""B: Is the parity likelihood our controller uses (k ~ Binomial(n, p), Jeffreys Beta posterior for p) calibrated on
NetSquid-generated calibration bits from the OTHER agent's loaded four-node runs?  READ-ONLY use of
../../../Files11-EndToEnd-PRX/prx_work/21_live_parity_law/runs/seed_*_n30_loaded_dev_01.json (20 seeds x 54 cells x 30 shots).
For each cell: known-channel positive-parity probability p (computed by that study AFTER bits were generated), observed k of n.
Checks (posterior-predictive calibration of the Jeffreys posterior, which v16-v18 rely on):
  * PIT u = P_post(p' <= p_true) (exact posterior CDF); compared with a 2,000-replicate parametric null (discreteness-aware); should be ~Uniform(0,1)
  * lower-tail events: P_post(p' >= p_true) <= a  (posterior optimistic about p) at a = 1%, 5%, 10%: expected rates a
  * two-sided 90% / 95% credible-interval coverage
Caveat: that study inspected seed 69601 before fixing the seed set (not pre-registered); cells within a seed share a timeline.
"""
import glob, json, sys
import numpy as np
SRC = sys.argv[1] if len(sys.argv) > 1 else "../../../Files11-EndToEnd-PRX/prx_work/21_live_parity_law/runs"
rng = np.random.default_rng(22001); rows = []
for f in sorted(glob.glob(f"{SRC}/seed_*_n30_loaded_dev_01.json")):
    s = json.load(open(f))
    for c in s["cells"]:
        rows.append((s["seed"], c["basis"], c["hold_ns"], int(c["positive_parities"]), int(c["shots"]), float(c["predicted_positive_probability_known_channel"])))
seed, basis, hold, k, n, p = map(np.array, zip(*rows)); N = len(k)
assert (n == n[0]).all(); n0 = int(n[0])
G = np.linspace(0, 1, 400001); from math import lgamma
CDF = []
for kk in range(n0 + 1):                       # exact Jeffreys posterior CDFs (fine-grid integration; 31 distinct posteriors)
    a_, b_ = kk + 0.5, n0 - kk + 0.5; x = G[1:-1]
    lp = (a_ - 1) * np.log(x) + (b_ - 1) * np.log1p(-x) + lgamma(a_ + b_) - lgamma(a_) - lgamma(b_)
    pdf = np.concatenate([[0], np.exp(lp), [0]]); c = np.concatenate([[0], np.cumsum((pdf[1:] + pdf[:-1]) / 2 * np.diff(G))]); CDF.append(c / c[-1])
CDF = np.array(CDF)
def pit(kv): return np.array([np.interp(pp, G, CDF[kk]) for kk, pp in zip(kv, p)])
u = pit(k)
def stats(uu):
    srt = np.sort(uu); return float(np.max(np.abs(srt - (np.arange(1, len(uu) + 1) - 0.5) / len(uu)))), float((1 - uu <= 0.01).mean()), float(((uu > .025) & (uu < .975)).mean())
ks_obs, opt_obs, cov_obs = stats(u); NULL = []
for r in range(2000):                           # null: same cells, k* ~ Binomial(n, p_true) exactly as the model says
    NULL.append(stats(pit(rng.binomial(n, p))))
NULL = np.array(NULL)
out = {"source": SRC, "cells": int(N), "seeds": int(len(set(seed))), "shots_total": int(n.sum())}
for a in (0.01, 0.05, 0.10):
    out[f"optimistic_tail_rate_at_{a}"] = float((1 - u <= a).mean()); out[f"pessimistic_tail_rate_at_{a}"] = float((u <= a).mean())
for lvl in (0.90, 0.95):
    lo = (1 - lvl) / 2; out[f"coverage_{int(lvl*100)}"] = float(((u > lo) & (u < 1 - lo)).mean())
hist = np.histogram(u, bins=10, range=(0, 1))[0]; out["pit_decile_counts"] = hist.tolist()
out["ks_D_obs"] = ks_obs; out["ks_D_null_p_value"] = float((NULL[:, 0] >= ks_obs).mean())
out["opt_tail_1pct_null_mean"] = float(NULL[:, 1].mean()); out["opt_tail_1pct_null_p_upper"] = float((NULL[:, 1] >= opt_obs).mean())
out["coverage_95_null_mean"] = float(NULL[:, 2].mean()); out["coverage_95_null_p_lower"] = float((NULL[:, 2] <= cov_obs).mean())
by = {}
for b in ("X", "Y", "Z"):
    for h in sorted(set(hold)):
        m = (basis == b) & (hold == h); by[f"{b}@{int(h/1000)}us"] = dict(cells=int(m.sum()), opt_tail_1pct=float((1 - u[m] <= 0.01).mean()), cov95=float(((u[m] > .025) & (u[m] < .975)).mean()))
out["by_basis_hold"] = by
print(json.dumps(out, indent=1)); json.dump(out, open("parity_posterior_calibration.json", "w"), indent=1)
