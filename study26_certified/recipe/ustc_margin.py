"""Real-data model-optimism estimate (USTC 2026, Stage 1 output) and its one-sided 95% upper bound.
gap_i = (F0_meas + dF_pred_i) - F_meas_i for t_i > 0; Var = s0^2 + s_i^2, Cov = s0^2 (shared t=0 anchor). GLS common offset."""
import json, sys, numpy as np
d = json.load(open(sys.argv[1]))["U1"]["rows"]
F0, s0 = d[0]["F_meas"], d[0]["F_sd"]
rows = d[1:]
g = np.array([F0 + r["dF_pred"] - r["F_meas"] for r in rows]); s = np.array([r["F_sd"] for r in rows])
C = np.diag(s ** 2) + s0 ** 2; Ci = np.linalg.inv(C); one = np.ones(len(g))
var = 1 / (one @ Ci @ one); mu = var * (one @ Ci @ g); se = np.sqrt(var)
out = dict(gaps=g.round(4).tolist(), gls_offset=round(mu, 4), se=round(se, 4), ucb95=round(mu + 1.645 * se, 4),
           max_gap=round(g.max(), 4), naive_mean=round(g.mean(), 4))
print(json.dumps(out))
