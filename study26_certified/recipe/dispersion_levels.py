"""Real-data shared-noise levels: between-block extra sd of the event probability, sigma_p = sqrt((phi-1) p(1-p)/n),
absolute and relative to p, for each ICFO run (out_all_fix1.json) and the USTC run (out_ustc.json)."""
import json, numpy as np
rows = []
for st, v in json.load(open("out_all_fix1.json")).items():
    for r in v["r3"]:
        n = r["heralds"] / r["blocks"]; p = r["p"]; phi = r["dispersion"]
        sp = np.sqrt(max(phi - 1, 0) * p * (1 - p) / n); rows.append(("ICFO " + r["file"], n, p, phi, sp, sp / p))
u = json.load(open("out_ustc.json"))["U2"]; n = u["n_per_set"]; p = u["qber_mean"]; phi = u["dispersion"]
sp = np.sqrt((phi - 1) * p * (1 - p) / n); rows.append(("USTC QBER", n, p, phi, sp, sp / p))
print(f"{'run':24s} {'n/block':>9s} {'p':>8s} {'phi':>6s} {'sigma_abs':>10s} {'sigma_rel':>9s}")
for r in rows: print(f"{r[0]:24s} {r[1]:9.0f} {r[2]:8.4f} {r[3]:6.2f} {r[4]:10.5f} {r[5]:9.3f}")
rel = np.array([r[5] for r in rows[:-1]]); print("ICFO sigma_rel: median %.3f, max %.3f; USTC %.3f" % (np.median(rel), rel.max(), rows[-1][5]))
