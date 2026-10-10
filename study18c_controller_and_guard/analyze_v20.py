"""LOCKED analysis for v20 (README_v20.md, Q1-Q4). Usage: python3 analyze_v20.py des_v20_psc"""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); BIG = 200; rng = np.random.default_rng(0); rows = []
for (v, c), x in R.groupby(["variant", "config"]):
    d = x.delivered.values; b = x.bad.values; I = rng.integers(0, len(d), (4000, len(d))); rs = b[I].sum(1) / np.maximum(d[I].sum(1), 1)
    rows.append(dict(variant=v, config=c, paths=len(x), delivered=int(d.sum()), bad=int(b.sum()), qual=int(x.qual.sum()),
                     r_pct=100 * b.sum() / max(d.sum(), 1), boot95_pct=100 * float(np.quantile(rs, .95)), top_path_bad=int(b.max())))
G = pd.DataFrame(rows); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
print(G.round(4).to_string(index=False)); G.to_csv(f"{D}/v20_groups.csv", index=False); print("tasks:", len(R), "(expected 1536)")
big = G[G.delivered >= BIG]
x = big[big.config.isin(["ad_eb128t1", "t1eq_eb128t1", "deph_eb128t1"])]; v = x[x.r_pct > 1]
print(f"\nQ1 T1-aware controller (correct T1) r<=1% in every cell under ad, t1eq, deph: {len(v)} violations of {len(x)} -> {'PASS' if len(v) == 0 and len(x) else 'FAIL'}")
if len(v): print(v[["variant", "config", "delivered", "bad", "r_pct", "boot95_pct", "top_path_bad"]].round(3).to_string(index=False))
print(f"   (descriptive) max path-bootstrap 95% upper among Q1 groups: {x.boot95_pct.max():.3f}%")
x = big[big.config == "ad_eb128"]; print(f"Q2 depolarising controller under amplitude damping exceeds 1% in >=1 cell: {(x.r_pct > 1).sum()} of {len(x)} -> {'REPLICATED' if (x.r_pct > 1).any() else 'NOT REPLICATED'}")
x = big[big.config == "ad_eb128t1opt"]; print(f"Q3 T1 over-estimated by 25% exceeds 1% in >=1 cell: {(x.r_pct > 1).sum()} of {len(x)} -> {'CONFIRMED (sensitivity limit)' if (x.r_pct > 1).any() else 'NOT SEEN (robust to 25% T1 optimism)'}")
a = G[G.config == "deph_eb128t1"].set_index("variant"); b = G[G.config == "deph_eb128"].set_index("variant"); W = (a.qual / b.qual.clip(lower=1)).rename("ratio")
ok = W[(b.qual >= BIG)]
print(f"Q4 dephasing memories: T1-aware / depolarising qualified deliveries >= 1 in every cell with >= {BIG}: min {ok.min():.3f} -> {'PASS' if (ok >= 1).all() else 'FAIL'}")
print(W.round(3).to_string())
