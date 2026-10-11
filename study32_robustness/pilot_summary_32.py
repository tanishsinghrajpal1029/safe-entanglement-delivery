"""Study 32 dev-pilot summary (descriptive; sets the pre-registered bars). Usage: python3 pilot_summary_32.py runs.csv"""
import sys
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1]); d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]
d["blk"] = d.block.str[-1]; d["fq"] = np.where(d.oracle_qual > 0, d.qual / d.oracle_qual.clip(lower=1), np.nan)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
P = lambda *a: print(*a, flush=True)
P(f"rows {len(d)}; clamped {int(d.epoch_clamped.sum())}; blocks {d.blk.value_counts().to_dict()}")
agg = dict(n=("run", "size"), alarm=("alarms", lambda s: (s > 0).mean()), ep1=("first_alarm_ep", "median"), baa=("bad_after_alarm_all", "sum"),
           daa=("deliv_after_alarm_all", "sum"), anyb=("bad_after_alarm_all", lambda s: int((s > 0).sum())), ubp=("users_bad_post", "sum"),
           up=("users_post", "sum"), uba=("users_bad_all", "sum"), ut=("users_total", "sum"), fq=("fq", "mean"), dmean=("dec_mean_after", "median"),
           omean=("opt_mean_after", "median"), restarts=("mc_k", "mean"), dl=("delivered", "sum"), bad=("bad", "sum"), oracle=("oracle_qual", "sum"),
           npois=("npois", "mean"), wbelow=("w1_looks_below", "mean"), wrec=("w1_recover_tests", "median"), nal=("alarms", "mean"))
for blk, keys in (("R", ["hw", "sc", "p", "arm"]), ("E", ["hw", "var", "sc", "arm"]), ("T", ["hw", "sc", "p", "arm"])):
    x = d[d.blk == blk]
    if not len(x): continue
    g = x.groupby(keys).agg(**agg)
    g["r_after"] = g.baa / g.daa.clip(lower=1); g["pu_post"] = g.ubp / g.up.clip(lower=1); g["pu_all"] = g.uba / g.ut; g["r_all"] = g.bad / g.dl.clip(lower=1)
    P(f"\n== Block {blk} ==")
    P(g[["n", "oracle", "alarm", "nal", "ep1", "r_after", "anyb", "pu_post", "pu_all", "r_all", "fq", "dmean", "omean", "restarts", "npois", "wbelow", "wrec"]].round(4).to_string())
