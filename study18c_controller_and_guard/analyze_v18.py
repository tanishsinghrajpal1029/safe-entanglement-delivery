"""LOCKED analysis for v18 (README_v18.md, S1-S3). Usage: python3 analyze_v18.py des_v18_psc"""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); BIG = 200; B = 4000
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
rng = np.random.default_rng(0); rows = []
for (v, g, st, m), x in R.groupby(["variant", "g", "stress", "method"], sort=True):
    d = x.delivered.values; b = x.bad.values; I = rng.integers(0, len(d), (B, len(d)))
    rs = b[I].sum(1) / np.maximum(d[I].sum(1), 1)
    rows.append(dict(variant=v, g=f"{g:.0e}", stress=st, method=m, paths=len(x), delivered=int(d.sum()), bad=int(b.sum()),
                     qual=int(x.qual.sum()), oracle_qual=int(x.oracle_qual.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                     boot95_pct=100 * float(np.quantile(rs, 0.95)), top_path_bad=int(b.max()), m_hat_mean=x.m_hat.mean()))
G = pd.DataFrame(rows); G["frac_oracle"] = G.qual / G.oracle_qual.clip(lower=1)
print(G.round(4).to_string(index=False)); G.to_csv(f"{D}/v18_groups.csv", index=False)
print("tasks:", len(R), "(expected 10240)")
big = G[G.delivered >= BIG]
for name, sts in (("S1 fleet-law shape (t3, mixlow, mixhigh)", ["t3", "mixlow", "mixhigh"]), ("S2 drift amplitude +-50% (amp01, amp03)", ["amp01", "amp03"])):
    x = big[big.stress.isin(sts)]; v = x[x.r_pct > 1]
    print(f"\n{name}: r<=1% in every group: {len(v)} violations of {len(x)} -> {'PASS' if len(v) == 0 and len(x) else 'FAIL'}")
    for st in sts:
        y = x[x.stress == st]; print(f"   {st:8s} violations {int((y.r_pct > 1).sum())} of {len(y)}; max r {y.r_pct.max():.3f}%; max boot95 {y.boot95_pct.max():.3f}%")
    if len(v): print(v[["variant", "g", "stress", "method", "delivered", "bad", "r_pct", "boot95_pct", "top_path_bad"]].round(3).to_string(index=False))
print("\nS3 (descriptive) max pooled r % by stress x variant")
print(G.pivot_table(index="variant", columns="stress", values="r_pct", aggfunc="max").round(3).to_string())
print("\nS3 (descriptive) fraction of oracle (mean over g, method)")
print(G.pivot_table(index="variant", columns="stress", values="frac_oracle", aggfunc="mean").round(3).to_string())
