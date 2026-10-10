"""EXPLORATORY (not pre-registered): LTT with Bonferroni over the z grid (alpha/11) instead of fixed-sequence,
choosing the smallest rejected z. Same data as analyze_v12.py."""
import math, pandas as pd
import importlib.util, sys
spec = importlib.util.spec_from_file_location("a12", "analyze_v12.py")
R = pd.read_csv("des_v12_psc/runs.csv"); A = pd.read_csv("des_v11_psc/runs.csv")
def cdf(b, n, p):
    if n == 0: return 1.0
    lp, lq = math.log(p), math.log1p(-p)
    return min(1.0, sum(math.exp(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)+k*lp+(n-k)*lq) for k in range(b+1)))
groups = [(c, g, e) for c in ("ion_2020", "ion_proj") for g in (1e-9, 1e-5, 1e-4) for e in ("static", "ols_reset") if not (g == 1e-4 and e == "static")]
ev = R[R.role == "eval"]; out = []
for c, g, e in groups:
    ad = A[(A["pop"] == "A") & (A.cell == c) & (A.g == g) & (A.est == e) & (A.method == "adaptive")]
    row = dict(cell=c, g=g, est=e, ad_qual=int(ad.qual.sum()), ad_r=round(100*ad.bad.sum()/max(ad.delivered.sum(),1),3))
    for sc in ("S0", "S1"):
        dv = R[(R.role == "dev") & (R.scen == sc) & (R.cell == c) & (R.g == g) & (R.est == e)].groupby("z")[["bad","delivered"]].sum()
        rej = [z for z, r in dv.iterrows() if cdf(int(r.bad), int(r.delivered), 0.01) <= 0.05/len(dv)]
        z = min(rej) if rej else None; row[f"{sc}_z"] = z
        x = ev[(ev.cell == c) & (ev.g == g) & (ev.est == e) & (ev.z == z)] if z is not None else ev.iloc[0:0]
        row[f"{sc}_qual"] = int(x.qual.sum()); row[f"{sc}_r"] = round(100*x.bad.sum()/max(x.delivered.sum(),1),3)
    out.append(row)
T = pd.DataFrame(out); pd.set_option("display.width", 250); print(T.to_string(index=False))
print("S0 violations:", int((T.S0_r > 1).sum()), " S1 violations:", int((T.S1_r > 1).sum()), " adaptive violations:", int((T.ad_r > 1).sum()))
print("groups where LTT-Bonf(S0) delivers >0:", int((T.S0_qual > 0).sum()), "; adaptive qual >= LTT(S0) qual in", int((T.ad_qual >= T.S0_qual).sum()), "of", len(T))
