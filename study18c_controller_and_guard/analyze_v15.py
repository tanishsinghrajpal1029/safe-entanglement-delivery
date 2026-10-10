"""LOCKED analysis for v15 (README_v15.md, G1-G4). Usage: python3 analyze_v15.py des_v15_psc"""
import math, sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv")


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


G = R.groupby(["variant", "g", "est", "method"]).agg(delivered=("delivered", "sum"), bad=("bad", "sum"), qual=("qual", "sum"),
                                                     oracle_qual=("oracle_qual", "sum"), z_inf=("z_inf_frac", "mean")).reset_index()
G["r_pct"] = 100 * G.bad / G.delivered.clip(lower=1)
G["ucb_pct"] = [100 * cp_up(int(b), int(n)) for b, n in zip(G.bad, G.delivered)]
A = G[G.method == "adaptive"].copy(); A["frac_oracle"] = A.qual / A.oracle_qual.clip(lower=1)
F2 = G[G.method == "fixed2"]
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
W = A.merge(F2[["variant", "g", "est", "delivered", "r_pct"]], on=["variant", "g", "est"], suffixes=("", "_z2"))
print(W[["variant", "g", "est", "delivered", "bad", "r_pct", "ucb_pct", "frac_oracle", "z_inf", "delivered_z2", "r_pct_z2"]].round(4).to_string(index=False))
W.to_csv(f"{D}/v15_groups.csv", index=False)
big = A[A.delivered >= 200]
g1v = big[(big.variant != "t2_opt") & (big.r_pct > 1)]
print(f"G1 adaptive r<=1% in all groups with >=200 deliveries outside t2_opt: {len(g1v)} violations of {(big.variant != 't2_opt').sum()} -> {'PASS' if len(g1v) == 0 else 'FAIL'}")
if len(g1v): print(g1v[["variant", "g", "est", "bad", "delivered", "r_pct"]].to_string(index=False))
t2 = big[(big.variant == "t2_opt")]
print(f"G2 t2_opt (optimistic memory model) adaptive violates in >=1 group: {(t2.r_pct > 1).sum()} of {len(t2)} -> {'CONFIRMED (limitation)' if (t2.r_pct > 1).any() else 'NOT SEEN (robust to 30% optimistic T2)'}")
fz = F2[(F2.delivered >= 200) & (F2.r_pct > 1)]
print(f"G3 fixed z=2 exceeds 1% in >=1 group in >=3 distinct variants: {fz.variant.nunique()} variants -> {'PASS' if fz.variant.nunique() >= 3 else 'FAIL'}")
print("G4 (descriptive) adaptive fraction of oracle and abstention by variant:")
print(A.groupby("variant").agg(frac_oracle=("frac_oracle", "mean"), z_inf=("z_inf", "mean"), deliv=("delivered", "sum")).round(3).to_string())
