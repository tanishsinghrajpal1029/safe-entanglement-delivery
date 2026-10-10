"""Analysis of v9/v11 runs.csv against README_v9 T1-T4 (and README_v11 U1-U2). Usage: python3 analyze_v9.py <dir>"""
import sys, math, numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv")
def _cdf(b, n, p):
    lp, lq = math.log(p), math.log1p(-p)
    return sum(math.exp(math.lgamma(n+1) - math.lgamma(k+1) - math.lgamma(n-k+1) + k*lp + (n-k)*lq) for k in range(b + 1))
def cp_up(b, n):  # Clopper-Pearson 95% upper bound (bisection on the binomial cdf, log-space; no scipy)
    if n == 0 or b >= n: return 1.0
    lo, hi = b / n, 1.0
    for _ in range(60):
        p = (lo + hi) / 2
        lo, hi = (p, hi) if _cdf(b, n, p) > 0.05 else (lo, p)
    return hi
S = R.groupby(["pop", "cell", "g", "est", "method"])[["qual", "bad", "delivered", "oracle_qual"]].sum().reset_index()
S["r_pct"] = 100 * S.bad / S.delivered.clip(lower=1); S["frac"] = S.qual / S.oracle_qual.clip(lower=1)
S["ucb_pct"] = [100 * cp_up(int(b), int(n)) for b, n in zip(S.bad, S.delivered)]
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
W = S.pivot_table(index=["pop", "cell", "g", "est"], columns="method", values=["delivered", "r_pct", "frac"])
print(W.round(3).to_string())
tgt = S[(S.g <= 1e-5) | (S.est == "ols_reset")]
ad = tgt[tgt.method == "adaptive"]; f2 = tgt[tgt.method == "fixed2"]; f3 = tgt[tgt.method == "fixed3"]
t1 = (ad.r_pct <= 1).all()
print(f"T1/U1 adaptive r<=1% in all {len(ad)} target groups: {'PASS' if t1 else 'FAIL'}; violations:")
print(ad[ad.r_pct > 1][["pop", "cell", "g", "est", "bad", "delivered", "r_pct", "ucb_pct"]].round(3).to_string(index=False))
print(f"T2 fixed2 r>1% in >=1 target group: {'PASS' if (f2.r_pct > 1).any() else 'FAIL'} ({int((f2.r_pct > 1).sum())} groups)")
print(f"U2 fixed3 r<=1% in all target groups: {'PASS' if (f3.r_pct <= 1).all() else 'FAIL'} ({int((f3.r_pct > 1).sum())} violations)")
m = ad.merge(f3, on=["pop", "cell", "g", "est"], suffixes=("_a", "_f3")); both = m[(m.r_pct_a <= 1) & (m.r_pct_f3 <= 1)]
print(f"T3 adaptive qual >= fixed3 qual in {int((both.qual_a >= both.qual_f3).sum())}/{len(both)} groups where both safe: "
      f"{'PASS' if len(both) and (both.qual_a >= both.qual_f3).mean() >= 0.5 else 'FAIL'}")
st = S[(S.g == 1e-4) & (S.est == "static") & (S.method == "adaptive")]
print(f"T4 static g=1e-4 adaptive r>1% in >=1 cell (expected limitation): {'CONFIRMED' if (st.r_pct > 1).any() else 'NOT SEEN'}")
print(st[["pop", "cell", "bad", "delivered", "r_pct"]].round(3).to_string(index=False))
