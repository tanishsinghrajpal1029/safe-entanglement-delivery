"""Study 34 dev-pilot summary (descriptive). Usage: python3 pilot_summary_34.py runs_g5.csv runs_g10.csv runs_g30.csv"""
import sys
import numpy as np, pandas as pd
d = pd.concat([pd.read_csv(f) for f in sys.argv[1:]], ignore_index=True)
d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]; d["mult"] = d.cfg.str.split("|").str[2]
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
print(f"rows {len(d)}; clamped {int(d.epoch_clamped.sum())}; grids {d.grid.value_counts().to_dict()}")
g = d.groupby(["grid", "mult", "hw", "sc", "arm", "p"]).agg(n=("run", "size"), users=("users_total", "mean"), oracle=("oracle_qual", "sum"),
    qual=("qual", "sum"), alarm=("alarms", lambda s: (s > 0).mean()), ep1=("first_alarm_ep", "median"), baa=("bad_after_alarm_all", "sum"),
    daa=("deliv_after_alarm_all", "sum"), ubp=("users_bad_post", "sum"), up=("users_post", "sum"), uba=("users_bad_all", "sum"), ut=("users_total", "sum"),
    tests=("p10_tests", "mean"), dmean=("dec_mean_after", "median"), viol10=("p10_viol", "sum"), viol20=("p20_viol", "sum"),
    us=("users_served", "sum"), ubs=("users_bad_served", "sum"), bad=("bad", "sum"), dl=("delivered", "sum"))
g["fq"] = g.qual / g.oracle.clip(lower=1); g["r_after"] = g.baa / g.daa.clip(lower=1); g["pu_post"] = g.ubp / g.up.clip(lower=1); g["pu_all"] = g.uba / g.ut; g["pu_served"] = g.ubs / g.us.clip(lower=1); g["r"] = g.bad / g.dl.clip(lower=1)
print(g[["n", "users", "tests", "alarm", "ep1", "r", "r_after", "pu_post", "pu_all", "pu_served", "fq", "dmean", "viol10", "viol20"]].round(4).to_string())
