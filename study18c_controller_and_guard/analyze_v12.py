"""Pre-registered analysis of v12 (README_v12.md L1-L3). Usage: python3 analyze_v12.py des_v12_psc des_v11_psc"""
import math, sys
import numpy as np, pandas as pd
D, D11 = sys.argv[1], sys.argv[2]; DELTA, ALPHA = 0.01, 0.05
R = pd.read_csv(f"{D}/runs.csv"); A = pd.read_csv(f"{D11}/runs.csv")


def binom_cdf(b, n, p):
    if n == 0: return 1.0
    lp, lq = math.log(p), math.log1p(-p)
    return min(1.0, sum(math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * lp + (n - k) * lq)
                        for k in range(b + 1)))


def ltt(dev):  # fixed-sequence from the most conservative z downward
    zs = sorted(dev.z.unique(), reverse=True); zstar = None
    for z in zs:
        r = dev[dev.z == z]; p = binom_cdf(int(r.bad.sum()), int(r.delivered.sum()), DELTA)
        if p <= ALPHA: zstar = z
        else: break
    return zstar


groups = [(c, g, e) for c in ("ion_2020", "ion_proj") for g in (1e-9, 1e-5, 1e-4) for e in ("static", "ols_reset")
          if not (g == 1e-4 and e == "static")]
ev = R[R.role == "eval"]; rows = []
for c, g, e in groups:
    E = ev[(ev.cell == c) & (ev.g == g) & (ev.est == e)]
    ad = A[(A["pop"] == "A") & (A.cell == c) & (A.g == g) & (A.est == e) & (A.method == "adaptive")]
    oq = int(A[(A["pop"] == "A") & (A.cell == c) & (A.g == g) & (A.est == e) & (A.method == "adaptive")].oracle_qual.sum())
    row = dict(cell=c, g=g, est=e, oracle_qual=oq, ad_qual=int(ad.qual.sum()), ad_bad=int(ad.bad.sum()),
               ad_r=100 * ad.bad.sum() / max(ad.delivered.sum(), 1))
    for sc in ("S0", "S1"):
        dv = R[(R.role == "dev") & (R.scen == sc) & (R.cell == c) & (R.g == g) & (R.est == e)]
        z = ltt(dv); row[f"{sc}_z"] = z
        if z is None: row[f"{sc}_qual"] = 0; row[f"{sc}_bad"] = 0; row[f"{sc}_r"] = 0.0; continue
        x = E[E.z == z]; row[f"{sc}_qual"] = int(x.qual.sum()); row[f"{sc}_bad"] = int(x.bad.sum())
        row[f"{sc}_r"] = 100 * x.bad.sum() / max(x.delivered.sum(), 1)
    rows.append(row)
T = pd.DataFrame(rows); pd.set_option("display.width", 250)
print(T.round(3).to_string(index=False))
# reproducibility check: v12 eval z=2 must equal v11 fixed2 path-by-path
f2 = A[(A["pop"] == "A") & (A.method == "fixed2")][["cell", "g", "est", "idx", "qual", "bad", "delivered"]]
e2 = ev[ev.z == 2.0][["cell", "g", "est", "idx", "qual", "bad", "delivered"]]
m = f2.merge(e2, on=["cell", "g", "est", "idx"], suffixes=("_v11", "_v12"))
same = ((m.qual_v11 == m.qual_v12) & (m.bad_v11 == m.bad_v12) & (m.delivered_v11 == m.delivered_v12)).mean()
print(f"repro: v12 eval z=2 vs v11 fixed2, identical in {same:.3f} of {len(m)} path-runs")
l1 = (T.S0_r <= 1).sum()
print(f"L1 (S0 LTT eval r<=1% in all {len(T)} groups): {l1}/{len(T)} -> {'PASS' if l1 == len(T) else 'FAIL'}")
l2a = (T.S1_r > 1).sum(); l2b = (T.ad_r <= 1).sum()
print(f"L2 (S1 LTT violates in >=1 group: {l2a}; adaptive safe in {l2b}/{len(T)}) -> {'PASS' if l2a >= 1 and l2b == len(T) else 'FAIL'}")
both = T[(T.S0_r <= 1) & (T.ad_r <= 1) & (T.S0_qual > 0)]
k = (both.ad_qual >= 0.8 * both.S0_qual).sum()
print(f"L3 (adaptive >= 0.8x LTT-S0 goodput where both safe): {k}/{len(both)} -> {'PASS' if len(both) and k / len(both) >= 0.5 else 'FAIL'}")
T.to_csv(f"{D}/ltt_vs_adaptive.csv", index=False)
