"""LOCKED analysis for P1 (README_P1.md). Usage: python3 analyze_p1.py des_p1_psc"""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); BIG = 200; rng = np.random.default_rng(0); rows = []
pd.set_option("display.width", 220); pd.set_option("display.max_rows", 100)
for (hw, T, K), x in R.groupby(["hw", "T", "K"]):
    d = x.delivered.values; b = x.bad.values; I = rng.integers(0, len(d), (4000, len(d)))
    rows.append(dict(hw=hw, T=T, K=K, I=x.I.iloc[0], delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                     boot95_pct=100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95)),
                     frac_oracle=x.qual.sum() / max(x.oracle_qual.sum(), 1), s_hat_over_true=float((x.s_hat / x.s_true).median())))
G = pd.DataFrame(rows).sort_values(["hw", "I"]); print(G.round(4).to_string(index=False)); G.to_csv(f"{D}/p1_groups.csv", index=False)
print("tasks:", len(R), "(expected 8192)")
hi = G[(G.I >= 3) & (G.delivered >= BIG)]; v = hi[hi.r_pct > 1]
print(f"\nP-1 every tested group with I >= 3 has r <= 1%: {len(v)} violations of {len(hi)} -> {'PASS' if len(v) == 0 and len(hi) else 'FAIL'}")
if len(v): print(v.round(3).to_string(index=False))
lo = G[G.I < 1]; both = lo[(lo.delivered >= BIG) & (lo.r_pct <= 1) & (lo.frac_oracle >= 0.05)]
print(f"P-2 no group with I < 1 is both safe (r<=1%, >= {BIG} deliveries) and useful (>= 5% of oracle): {len(both)} of {len(lo)} -> {'PASS' if len(both) == 0 else 'FAIL'}")
if len(both): print(both.round(3).to_string(index=False))
t = G[G.delivered >= BIG].copy(); t["viol"] = (t.r_pct > 1).astype(int)
print("\nP-3 (descriptive) violation rate and median s_hat/s_true by I band (tested groups):")
t["band"] = pd.cut(t.I, [0, 0.5, 1, 2, 3, 5, 20])
print(t.groupby("band", observed=True).agg(groups=("viol", "size"), violations=("viol", "sum"), max_r=("r_pct", "max"),
                                         frac_oracle=("frac_oracle", "mean"), s_ratio=("s_hat_over_true", "median")).round(3).to_string())
print("\nP-4 (descriptive) fraction of oracle by hardware x T x K:")
print(G.pivot_table(index=["hw", "T"], columns="K", values="frac_oracle").round(3).to_string())
