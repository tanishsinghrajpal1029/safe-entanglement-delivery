"""Summarise a Study 24 dev pilot (Block A or B). Usage: python3 summarize_p24.py <outdir>/runs.csv"""
import sys, pandas as pd
R = pd.read_csv(sys.argv[1]); pd.set_option("display.width", 250)
cell = ["hw", "pat"] if "pat" in R else ["hw", "scen"]; arm = "arm" if "arm" in R else "ctrl"
G = R.groupby(cell + [arm]).agg(nets=("run", "size"), deliv=("delivered", "sum"), bad=("bad", "sum"), q=("qual", "sum"), oq=("oracle_qual", "sum"),
                                pb=("paths_bad", "sum"), pd_=("paths_delivered", "sum")).reset_index()
G["frac"] = G.q / G.oq; G["r_pct"] = 100 * G.bad / G.deliv.clip(lower=1); G["pct_paths_bad"] = 100 * G.pb / G.pd_.clip(lower=1)
print(G.pivot_table(index=cell, columns=arm, values="frac").round(3).to_string())
print("\nbad pairs:"); print(G.pivot_table(index=cell, columns=arm, values="bad").to_string())
if "prior_rmse_z" in R:
    print("\nprior rmse (z):"); print(R[R.prior_rmse_z > 0].pivot_table(index=cell, columns=arm, values="prior_rmse_z").round(3).to_string())
