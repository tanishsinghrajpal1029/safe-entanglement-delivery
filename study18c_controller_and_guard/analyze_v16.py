"""LOCKED analysis for v16 (README_v16.md, H1-H5). Usage: python3 analyze_v16.py des_v16_psc"""
import math, sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv")
ION = ("ion2020_tau090", "ionproj_tau090", "tau085_ion2020"); BIG = 200


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


G = R.groupby(["variant", "g", "est", "method"]).agg(paths=("idx", "count"), delivered=("delivered", "sum"), bad=("bad", "sum"),
                                                     qual=("qual", "sum"), oracle_qual=("oracle_qual", "sum"),
                                                     abstain=("abstain_frac", "mean")).reset_index()
G["g"] = G.g.map("{:.0e}".format)
G["r_pct"] = 100 * G.bad / G.delivered.clip(lower=1)
G["ucb_pct"] = [100 * cp_up(int(b), int(n)) for b, n in zip(G.bad, G.delivered)]
G["frac_oracle"] = G.qual / G.oracle_qual.clip(lower=1)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
print(G.round(4).to_string(index=False)); G.to_csv(f"{D}/v16_groups.csv", index=False)
print("tasks:", len(R), "(expected 3584)")


def big(m, est=None, var=None):
    x = G[(G.method == m) & (G.delivered >= BIG)]
    if est: x = x[x.est == est]
    if var is not None: x = x[x.variant.isin(var)]
    return x


p = big("pop"); v = p[p.r_pct > 1]
print(f"\nH1 pop (correct fleet prior) r<=1% in every group with >={BIG} deliveries: {len(v)} violations of {len(p)} -> {'PASS' if len(v) == 0 and len(p) > 0 else 'FAIL'}")
if len(v): print(v[["variant", "g", "delivered", "bad", "r_pct"]].to_string(index=False))
e = big("exact", var=["nv_tau080"]); ev = e[e.r_pct > 1]
print(f"H2 Jeffreys exact exceeds 1% in >=1 NV group: {len(ev)} of {len(e)} -> {'CONFIRMED (likelihood alone insufficient)' if len(ev) else 'NOT SEEN (exact likelihood suffices on NV)'}")
a = big("adaptive", var=["nv_tau080"]); av = a[a.r_pct > 1]
print(f"H3 Gaussian adaptive reproduces NV violation on fresh seeds: {len(av)} of {len(a)} -> {'REPLICATED' if len(av) else 'NOT REPLICATED'}")
P = G[(G.method == "pop") & G.variant.isin(ION)][["variant", "g", "qual"]]
A = G[(G.method == "adaptive") & (G.est == "static") & G.variant.isin(ION)][["variant", "g", "qual"]]
W = P.merge(A, on=["variant", "g"], suffixes=("_pop", "_adapt")); W["ratio"] = W.qual_pop / W.qual_adapt.clip(lower=1)
print(f"H4 pop qualified >= 0.8 x Gaussian adaptive (static) in every ion group: min ratio {W.ratio.min():.3f} -> {'PASS' if (W.ratio >= 0.8).all() else 'FAIL'}")
print(W.round(3).to_string(index=False))
o = big("popopt"); ov = o[o.r_pct > 1]
print(f"H5 optimistic prior (popopt) exceeds 1% in >=1 group: {len(ov)} of {len(o)} -> {'CONFIRMED (limitation)' if len(ov) else 'NOT SEEN (robust to +1 sd optimism)'}")
w = big("popwide"); print(f"   popwide (descriptive): max r {w.r_pct.max():.3f}%, violations {(w.r_pct > 1).sum()} of {len(w)}")
print("\nDescriptive: fraction of oracle by method x variant (mean over g, est)")
print(G.pivot_table(index="variant", columns="method", values="frac_oracle", aggfunc="mean").round(3).to_string())
