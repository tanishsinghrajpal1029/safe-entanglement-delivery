"""LOCKED analysis for v14 (README_v14.md, B1-B4). Usage: python3 analyze_v14.py des_v14_psc
Cluster-aware LTT: paths are the resampling unit. For each z, the risk r(z) = sum(bad)/sum(delivered) over dev paths;
UCB(z) = (1 - 0.05/m) quantile of r(z) over B = 2000 path-bootstrap resamples (seed 14), m = number of z values.
Choose the smallest z with UCB(z) <= 1% (Bonferroni over z); abstain if none. Naive pooled-binomial LTT (as in the
final run) is reported alongside for contrast."""
import math, sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); DELTA, ALPHA, B = 0.01, 0.05, 2000


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


def ltt_cluster(dev, rng):
    zs = sorted(dev.method.unique()); m = len(zs); ok = []
    for zname in zs:
        d = dev[dev.method == zname].sort_values("idx"); bad = d.bad.values.astype(float); dl = d.delivered.values.astype(float)
        if dl.sum() == 0: continue
        idx = rng.integers(0, len(d), size=(B, len(d)))
        rb = bad[idx].sum(1) / np.maximum(dl[idx].sum(1), 1.0)
        rb[dl[idx].sum(1) == 0] = 1.0
        if np.quantile(rb, 1 - ALPHA / m) <= DELTA: ok.append(float(zname[1:]))
    return min(ok) if ok else None


def ltt_pooled(dev):
    g = dev.groupby("method")[["bad", "delivered"]].sum(); m = len(g)
    rej = [float(k[1:]) for k, r in g.iterrows() if cdf(int(r.bad), int(r.delivered), DELTA) <= ALPHA / m]
    return min(rej) if rej else None


rng = np.random.default_rng(14); ev = R[R.role == "eval"]; rows = []
for (c, g, e), E in ev.groupby(["cell", "g", "est"]):
    ad = E[E.method == "adaptive"]
    row = dict(cell=c, g=g, est=e, ad_deliv=int(ad.delivered.sum()), ad_bad=int(ad.bad.sum()),
               ad_r=100 * ad.bad.sum() / max(ad.delivered.sum(), 1), ad_ucb=100 * cp_up(int(ad.bad.sum()), int(ad.delivered.sum())),
               ad_qual=int(ad.qual.sum()), oracle_qual=int(ad.oracle_qual.sum()))
    for zn, lab in (("z1.2816", "q10"), ("z2.3263", "q01")):
        x = E[E.method == zn]; row[f"{lab}_deliv"] = int(x.delivered.sum()); row[f"{lab}_r"] = 100 * x.bad.sum() / max(x.delivered.sum(), 1)
        row[f"{lab}_qual"] = int(x.qual.sum())
    for sc in ("S0", "S1"):
        dv = R[(R.role == "dev") & (R.scen == sc) & (R.cell == c) & (R.g == g) & (R.est == e)]
        for kind, z in (("clus", ltt_cluster(dv, rng)), ("pool", ltt_pooled(dv))):
            x = E[E.method == f"z{z}"] if z is not None else E.iloc[0:0]
            row[f"{kind}{sc}_z"] = z; row[f"{kind}{sc}_qual"] = int(x.qual.sum()); row[f"{kind}{sc}_deliv"] = int(x.delivered.sum())
            row[f"{kind}{sc}_r"] = 100 * x.bad.sum() / max(x.delivered.sum(), 1)
    rows.append(row)
T = pd.DataFrame(rows); pd.set_option("display.width", 320); pd.set_option("display.max_columns", 60)
print(T.round(4).to_string(index=False)); T.to_csv(f"{D}/v14_groups.csv", index=False)
bigA = T[T.ad_deliv >= 200]
b1 = (T[T.clusS0_deliv > 0].clusS0_r > 1).sum()
print(f"B1 cluster-aware LTT (S0) violations among groups where it delivers: {b1} of {(T.clusS0_deliv > 0).sum()} -> {'PASS' if b1 == 0 else 'FAIL'}")
b2c = (T[T.clusS1_deliv > 0].clusS1_r > 1).sum(); b2a = (bigA.ad_r > 1).sum()
print(f"B2 cluster-aware LTT (S1) violations: {b2c}; adaptive violations (>=200 deliv): {b2a} of {len(bigA)} -> {'PASS' if b2c >= 1 and b2a == 0 else 'FAIL'}")
q10 = (T[T.q10_deliv >= 200].q10_r > 1).sum(); q01 = (T[T.q01_deliv >= 200].q01_r > 1).sum()
print(f"B3 per-decision rules exceed 1% in >=1 group (>=200 deliv): delta=0.10 quantile (z=1.28): {q10}; Bayes flat-prior 1% (z=2.33): {q01} -> {'PASS' if q10 >= 1 and q01 >= 1 else 'FAIL'}")
both = T[T.clusS0_qual > 0]
print(f"B4 (descriptive) adaptive / cluster-LTT-S0 qualified ratio, median over {len(both)} groups: "
      f"{np.median(both.ad_qual / both.clusS0_qual) if len(both) else float('nan'):.3f}; cluster-LTT-S0 abstains in {(T.clusS0_qual == 0).sum()} of {len(T)}")
print(f"(contrast) pooled-binomial LTT S0 violations: {(T[T.poolS0_deliv > 0].poolS0_r > 1).sum()}; S1: {(T[T.poolS1_deliv > 0].poolS1_r > 1).sum()}")
