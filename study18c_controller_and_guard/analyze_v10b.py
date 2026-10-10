"""Pre-registered analysis of v10b (README_v10b.md M1-M3) + frontier table. Usage: python3 analyze_v10b.py des_v10b_psc"""
import sys, numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv")
C = R.groupby(["preset", "L", "g", "q", "method"])[["qual", "bad", "delivered", "oracle_qual"]].sum().reset_index()
C["r_pct"] = 100 * C.bad / C.delivered.clip(lower=1); C["frac"] = C.qual / C.oracle_qual.clip(lower=1)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
print("=== frontier: fraction of oracle (q=0.001)")
print(C[C.q == 0.001].pivot_table(index=["preset", "L"], columns=["method", "g"], values="frac").round(3).to_string())
print("=== oracle qualified per path-run (q=0.001, static:adaptive rows) -> is the oracle itself feasible?")
print((C[(C.q == 0.001) & (C.method == "static:adaptive")].pivot_table(index=["preset", "L"], columns="g", values="oracle_qual") / 32).round(0).to_string())
# M1
big = C[C.delivered >= 200]
m1a = big[(big.method == "ols_reset:adaptive")]; m1b = big[(big.method == "static:adaptive") & (big.g <= 1e-5)]
v = pd.concat([m1a[m1a.r_pct > 1], m1b[m1b.r_pct > 1]])
print(f"M1: {len(m1a)+len(m1b)} cells checked; violations {len(v)} -> {'PASS' if len(v)==0 else 'FAIL'}")
if len(v): print(v[["preset","L","g","q","method","bad","delivered","r_pct"]].round(3).to_string(index=False))
print("static:fixed2 cells (>=200 deliv) with r>1%:", int(((C.method=="static:fixed2")&(C.delivered>=200)&(C.r_pct>1)).sum()), "of", int(((C.method=="static:fixed2")&(C.delivered>=200)).sum()))
print("static:adaptive at g=1e-4 cells with r>1% (known drift bias):", int(((C.method=="static:adaptive")&(C.g==1e-4)&(C.delivered>=200)&(C.r_pct>1)).sum()), "of", int(((C.method=="static:adaptive")&(C.g==1e-4)&(C.delivered>=200)).sum()))
# M2
s = C[(C.method == "static:adaptive") & (C.g == 1e-6) & (C.L == 2)].set_index(["preset", "q"]).frac
rel = {p: 1 - s[(p, 0.03)] / max(s[(p, 0.001)], 1e-12) for p in ("ion_2020", "ion_future")}
print(f"M2: relative loss q .001->.03: ion_future {rel['ion_future']:.3f} vs ion_2020 {rel['ion_2020']:.3f} -> {'PASS' if rel['ion_future'] > rel['ion_2020'] else 'FAIL'}")
print(C[(C.method == "static:adaptive") & (C.g == 1e-6)].pivot_table(index=["preset","L"], columns="q", values="frac").round(3).to_string())
# M3
S = C[C.method == "static:adaptive"].set_index(["preset", "L", "g", "q"]).frac; ok = n = 0
for (p, L, g, q), f in S.items():
    if L < 4 and (p, L + 1, g, q) in S: n += 1; ok += S[(p, L + 1, g, q)] <= f + 1e-12
    gi = (1e-6, 1e-5, 1e-4)
    if g != 1e-4 and (p, L, gi[gi.index(g) + 1], q) in S: n += 1; ok += S[(p, L, gi[gi.index(g) + 1], q)] <= f + 1e-12
print(f"M3: {ok}/{n} = {ok/n:.2f} adjacent pairs non-increasing (bar 0.80) -> {'PASS' if ok/n >= 0.8 else 'FAIL'}")
C.to_csv(f"{D}/cells.csv", index=False)
