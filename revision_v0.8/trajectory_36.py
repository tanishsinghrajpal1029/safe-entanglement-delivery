"""Exploratory (figure only, not a new test): time course of the pre-registered S36 certificate.
Re-uses the locked oxford_core functions and the convention fixed by gate G2 (results_36.json).
Writes trajectory_36.csv: kept pairs K, trusted-settings bound F_L (p = 1/2, as pre-registered), the same with
p = 130/256 (exploratory), the self-testing bound, and the consistency upper value, at ~2,000 points."""
import json, lzma, sys, numpy as np
from oxford_core import loss_indicator, kept_fidelity_lower, di_fidelity_from_q
path = sys.argv[1]; R = json.load(open("results_36.json")); pattern, sign = tuple(R["convention"][0]), R["convention"][1]
with lzma.open(path, "rt") as f: lines = [ln for ln in f if not ln.startswith("#")]
d = np.loadtxt(lines[1:], delimiter=",", dtype=np.int64); tns, x, y, a, b = d.T; n = len(d)
test = (y != 2).astype(np.int64); xs, ys, ta, tb = x[test == 1], y[test == 1], a[test == 1], b[test == 1]
L = np.zeros(n, dtype=np.int64); L[test == 1] = loss_indicator(xs, ys, ta, tb, pattern, sign)
FL, qbar, K = kept_fidelity_lower(test, L, 0.5); FLt, qbt, _ = kept_fidelity_lower(test, L, 130 / 256)
DI = di_fidelity_from_q(qbar)
ka, kb = a[test == 0], b[test == 0]; errK = (ka != kb) if sign == +1 else (ka == kb)
zerr = np.zeros(n); zerr[np.where(test == 0)[0]] = errK; ub = 1 - np.cumsum(zerr) / np.maximum(K, 1) / 2
cl = np.cumsum(L); ct = np.cumsum(test); pe = np.sqrt(2) * (1 - 2 * cl / np.maximum(ct, 1))
idx = np.unique(np.concatenate([np.geomspace(1, n, 2000).astype(int) - 1, [n - 1]]))
hours = (tns - tns[0]) / 3.6e12
np.savetxt("trajectory_36.csv", np.c_[idx + 1, hours[idx], K[idx], FL[idx], FLt[idx], DI[idx], ub[idx], pe[idx]], delimiter=",",
           header="round,hours,kept,F_L_p0.5,F_L_p130_256,F_selftest,consistency_upper,point_estimate", comments="", fmt="%.6g")
print("final", K[-1], FL[-1], FLt[-1], DI[-1], "after09", int(K[np.where(FL <= 0.9)[0].max() + 1]) if np.any(FL <= 0.9) else None)
