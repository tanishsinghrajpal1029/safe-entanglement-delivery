"""Study 23 dev-pilot summary (exploratory; not a locked analysis). Usage: python3 summarize_pilot.py des_p23_psc/runs.csv"""
import sys
import numpy as np, pandas as pd
R = pd.read_csv(sys.argv[1]); print("tasks:", len(R))
K = ["hw", "rho", "data", "arm"]
G = R.groupby(K).agg(nets=("idx", "size"), delivered=("delivered", "sum"), bad=("bad", "sum"), qual=("qual", "sum"),
                     oracle=("oracle_qual", "sum"), paths_bad=("paths_bad", "sum"), paths=("paths_delivered", "sum"),
                     err=("est_abserr", "mean")).reset_index()
G["frac"] = G.qual / G.oracle; G["r_pct"] = 100 * G.bad / G.delivered; G["pct_paths_bad"] = 100 * G.paths_bad / G.paths
pd.set_option("display.width", 250); print(G.round(4).to_string(index=False))
print("\nGain in fraction of oracle vs bg (paired by network), points:")
F = R.assign(f=R.qual / R.oracle_qual).pivot_table(index=["hw", "rho", "data", "idx"], columns="arm", values="f")
for arm in ("ag", "rg", "arg"):
    d = (F[arm] - F["bg"]).groupby(level=[0, 1, 2]); print(arm, (100 * d.mean()).round(2).to_dict())
