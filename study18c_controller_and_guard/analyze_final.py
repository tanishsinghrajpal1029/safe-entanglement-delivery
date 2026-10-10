"""LOCKED analysis for the Study 18C final run (FINAL_PROTOCOL.md, hypotheses F2-F5; F1 uses analyze_v7.py).
Usage: python3 analyze_final.py des_final_psc"""
import math, sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); DELTA = 0.01; ALPHA = 0.05


def cdf(b, n, p):
    if n == 0: return 1.0
    lp, lq = math.log(p), math.log1p(-p)
    return min(1.0, sum(math.exp(math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1) + k * lp + (n - k) * lq) for k in range(b + 1)))


def cp_up(b, n):
    if n == 0 or b >= n: return 1.0
    lo, hi = b / n, 1.0
    for _ in range(60):
        p = (lo + hi) / 2; lo, hi = (p, hi) if cdf(b, n, p) > 0.05 else (lo, p)
    return hi


def boot_frac(d, B=2000, seed=0):
    rng = np.random.default_rng(seed); q = d.qual.values; o = d.oracle_qual.values; n = len(q)
    s = [q[i].sum() / max(o[i].sum(), 1) for i in (rng.integers(0, n, n) for _ in range(B))]
    return np.percentile(s, [2.5, 97.5])


def ltt_bonf(dev):
    g = dev.groupby("method")[["bad", "delivered"]].sum(); m = len(g)
    rej = [float(k[1:]) for k, r in g.iterrows() if cdf(int(r.bad), int(r.delivered), DELTA) <= ALPHA / m]
    return min(rej) if rej else None


ev = R[R.role == "eval"]; rows = []
for (c, g, e), E in ev.groupby(["cell", "g", "est"]):
    ad = E[E.method == "adaptive"]; z2 = E[E.method == "z2.0"]
    lo, hi = boot_frac(ad)
    row = dict(cell=c, g=g, est=e, ad_deliv=int(ad.delivered.sum()), ad_bad=int(ad.bad.sum()),
               ad_r=100 * ad.bad.sum() / max(ad.delivered.sum(), 1), ad_ucb=100 * cp_up(int(ad.bad.sum()), int(ad.delivered.sum())),
               ad_frac=ad.qual.sum() / max(ad.oracle_qual.sum(), 1), ad_frac_lo=lo, ad_frac_hi=hi,
               z2_deliv=int(z2.delivered.sum()), z2_r=100 * z2.bad.sum() / max(z2.delivered.sum(), 1), ad_qual=int(ad.qual.sum()))
    for sc in ("S0", "S1"):
        dv = R[(R.role == "dev") & (R.scen == sc) & (R.cell == c) & (R.g == g) & (R.est == e)]
        z = ltt_bonf(dv); row[f"ltt{sc}_z"] = z
        x = E[E.method == f"z{z}"] if z is not None else E.iloc[0:0]
        row[f"ltt{sc}_qual"] = int(x.qual.sum()); row[f"ltt{sc}_deliv"] = int(x.delivered.sum())
        row[f"ltt{sc}_r"] = 100 * x.bad.sum() / max(x.delivered.sum(), 1)
    rows.append(row)
T = pd.DataFrame(rows); pd.set_option("display.width", 300); pd.set_option("display.max_columns", 40)
print(T.round(4).to_string(index=False)); T.to_csv(f"{D}/final_groups.csv", index=False)
big = T[T.ad_deliv >= 200]; A = ev[ev.method == "adaptive"]
pool_ucb = 100 * cp_up(int(A.bad.sum()), int(A.delivered.sum()))
f2 = (big.ad_r <= 1).all() and pool_ucb <= 1
print(f"F2 adaptive r<=1% in all {len(big)} groups with >=200 deliveries: {(big.ad_r <= 1).sum()}/{len(big)}; pooled r = "
      f"{100 * A.bad.sum() / A.delivered.sum():.4f}% (CP95 upper {pool_ucb:.4f}%) -> {'PASS' if f2 else 'FAIL'}")
f3 = (T[T.z2_deliv >= 200].z2_r > 1).sum()
print(f"F3 fixed z=2 r>1% in >=1 group: {f3} groups -> {'PASS' if f3 >= 1 else 'FAIL'}")
s0v = (T[T.lttS0_deliv > 0].lttS0_r > 1).sum(); s1v = (T[T.lttS1_deliv > 0].lttS1_r > 1).sum()
print(f"F4 LTT-Bonferroni: S0 violations {s0v} (expect 0), S1 violations {s1v} (expect >=1) -> {'PASS' if s0v == 0 and s1v >= 1 else 'FAIL'}")
both = T[T.lttS0_qual > 0]
print(f"F5 (descriptive) adaptive/LTT-S0 qualified ratio, median over {len(both)} groups where LTT delivers: "
      f"{np.median(both.ad_qual / both.lttS0_qual):.3f}; LTT-S0 abstains in {(T.lttS0_qual == 0).sum()} of {len(T)} groups")
