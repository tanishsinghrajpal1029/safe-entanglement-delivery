"""LOCKED analysis for v19 (README_v19.md, N1-N4). Usage: python3 analyze_v19.py des_v19"""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); BIG = 200; rng = np.random.default_rng(0); rows = []
for (v, mem), x in R.groupby(["variant", "mem"]):
    d = x.delivered.values; b = x.bad.values; I = rng.integers(0, len(d), (4000, len(d))); rs = b[I].sum(1) / np.maximum(d[I].sum(1), 1)
    rows.append(dict(variant=v, mem=mem, paths=len(x), delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                     boot95_pct=100 * float(np.quantile(rs, .95)), bad_model_truth=int(x.bad_under_model_truth.sum()),
                     r_model_truth_pct=100 * x.bad_under_model_truth.sum() / max(d.sum(), 1),
                     mean_true_minus_model=float(np.nansum(x.mean_true_minus_model * x.delivered) / max(d.sum(), 1))))
G = pd.DataFrame(rows); pd.set_option("display.width", 250); print(G.round(4).to_string(index=False)); G.to_csv(f"{D}/v19_groups.csv", index=False)
print("tasks:", len(R), "(expected 768)"); big = G[G.delivered >= BIG]
for h, mem, want in (("N1 dephasing-only memories (T1 >> T2)", "deph", "safe"), ("N2 T1 = T2", "t1eq", "safe"), ("N3 amplitude-damping limit (T2 = 2 T1), expected limitation", "ad", "break")):
    x = big[big.mem == mem]; v = x[x.r_pct > 1]
    verdict = ("PASS" if len(v) == 0 and len(x) else "FAIL") if want == "safe" else ("CONFIRMED (limitation)" if len(v) else "NOT SEEN")
    print(f"{h}: violations {len(v)} of {len(x)}; max r {x.r_pct.max():.3f}% -> {verdict}")
x = G[G.mem == "deph"]; print(f"N4 (paired) dephasing truth never adds bad deliveries vs the model's own truth: {'YES' if (x.bad <= x.bad_model_truth).all() else 'NO'}")
