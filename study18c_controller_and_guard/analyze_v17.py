"""LOCKED analysis for v17 (README_v17.md, V1-V5). Usage: python3 analyze_v17.py des_v17_psc"""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); BIG = 200; B = 4000
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
rng = np.random.default_rng(0); rows = []
for (v, g, m), x in R.groupby(["variant", "g", "method"], sort=True):
    d = x.delivered.values; b = x.bad.values; I = rng.integers(0, len(d), (B, len(d)))
    rs = b[I].sum(1) / np.maximum(d[I].sum(1), 1)
    rows.append(dict(variant=v, g=f"{g:.0e}", method=m, paths=len(x), delivered=int(d.sum()), bad=int(b.sum()),
                     qual=int(x.qual.sum()), oracle_qual=int(x.oracle_qual.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                     boot95_pct=100 * float(np.quantile(rs, 0.95)), top_path_bad=int(b.max()),
                     abstain=x.abstain_frac.mean(), m_hat_mean=x.m_hat.mean(), m_hat_sd=x.m_hat.std()))
G = pd.DataFrame(rows); G["frac_oracle"] = G.qual / G.oracle_qual.clip(lower=1)
print(G.round(4).to_string(index=False)); G.to_csv(f"{D}/v17_groups.csv", index=False)
print("tasks:", len(R), "(expected 6144)")
big = G[G.delivered >= BIG]


def viol(ms, col="r_pct"):
    x = big[big.method.isin(ms)]; return x, x[x[col] > 1]


x, v = viol(["eb128", "eb32x10"])
print(f"\nV1 eb128 and eb32x10 r<=1% in every group: {len(v)} violations of {len(x)} -> {'PASS' if len(v) == 0 and len(x) else 'FAIL'}")
if len(v): print(v[["variant", "g", "method", "delivered", "bad", "r_pct"]].to_string(index=False))
x, v = viol(["eb128", "eb32x10"], "boot95_pct")
print(f"V2 (stricter) path-bootstrap 95% upper <=1% for eb128 and eb32x10: {len(v)} exceed of {len(x)} -> {'PASS' if len(v) == 0 and len(x) else 'FAIL'}")
if len(v): print(v[["variant", "g", "method", "delivered", "bad", "r_pct", "boot95_pct", "top_path_bad"]].round(3).to_string(index=False))
x, v = viol(["eb8", "eb32"]); vn = v[v.variant == "nv_tau080"]
print(f"V3 small fleets (eb8/eb32) exceed 1% in >=1 NV group: {len(vn)} -> {'CONFIRMED' if len(vn) else 'NOT SEEN'}; all small-fleet violations: {len(v)} of {len(x)}")
if len(v): print(v[["variant", "g", "method", "delivered", "bad", "r_pct"]].round(3).to_string(index=False))
x, v = viol(["pop"])
print(f"V4 oracle prior 'pop' replicates v16 H1 (<=1% every group): {len(v)} violations of {len(x)} -> {'REPLICATED' if len(v) == 0 else 'NOT REPLICATED'}")
P = G[G.method == "pop"][["variant", "g", "qual"]]; E = G[G.method == "eb128"][["variant", "g", "qual"]]
W = P.merge(E, on=["variant", "g"], suffixes=("_pop", "_eb128")); W = W[W.qual_pop >= BIG]
W["ratio"] = W.qual_eb128 / W.qual_pop
print(f"V5 eb128 qualified >= 0.8 x pop where pop qualified >= {BIG}: min ratio {W.ratio.min():.3f} -> {'PASS' if (W.ratio >= 0.8).all() else 'FAIL'}")
print(W.round(3).to_string(index=False))
print("\nDescriptive: fraction of oracle (mean over g)")
print(G.pivot_table(index="variant", columns="method", values="frac_oracle", aggfunc="mean").round(3).to_string())
print("\nDescriptive: pooled r % (max over g)")
print(G.pivot_table(index="variant", columns="method", values="r_pct", aggfunc="max").round(3).to_string())
