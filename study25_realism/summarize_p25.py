"""Summarise a Study 25 pilot. Usage: python3 summarize_p25.py <runs.csv> [D]"""
import sys, pandas as pd
R = pd.read_csv(sys.argv[1]); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
if len(sys.argv) > 2:
    key = ["hw", "scen", "ctrl"]
else:
    key = ["block", "hw", "cfg", "arm"]
G = R.groupby(key).agg(nets=("run", "size"), deliv=("delivered", "sum"), bad=("bad", "sum"), q=("qual", "sum"), oq=("oracle_qual", "sum"),
                      pb=("paths_bad", "sum"), pd_=("paths_delivered", "sum")).reset_index()
G["frac"] = (G.q / G.oq).round(4); G["r_pct"] = (100 * G.bad / G.deliv.clip(lower=1)).round(3); G["pct_paths_bad"] = (100 * G.pb / G.pd_.clip(lower=1)).round(2)
if "lat_e2e_mean" in R:
    L = R[R.delivered > 0].groupby(key).apply(lambda g: (g.lat_e2e_mean * g.delivered).sum() / g.delivered.sum()).rename("lat_mean").reset_index()
    G = G.merge(L, on=key, how="left")
if "camp_sdF_ratio" in R:
    C = R[R.camp_sdF_ratio.notna()].groupby(key)[["camp_muF_err", "camp_sdF_ratio"]].mean().reset_index(); G = G.merge(C, on=key, how="left")
print(G.drop(columns=["q", "oq", "pb", "pd_"]).to_string(index=False))
