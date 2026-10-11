"""Study 29 dev-pilot summary (descriptive; sets the pre-registered bars). Usage: python3 pilot_summary_29.py runs.csv"""
import sys
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1]); d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]
d["fq"] = d.qual / d.oracle_qual.clip(lower=1)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
x = d[d.block != "R28"]
g = x.groupby(["hw", "sc", "arm", "p"]).agg(n=("run", "size"), deliv=("delivered", "sum"), bad=("bad", "sum"), ub=("users_bad_all", "sum"),
    ut=("users_total", "sum"), fq=("fq", "mean"), alarm=("alarms", lambda s: (s > 0).mean()), ep1=("first_alarm_ep", "median"),
    fa=("fa_first_t", "sum"), baa=("bad_after_alarm", "sum"), daa=("deliv_after_alarm", "sum"), below=("below_after_alarm", "sum"),
    dmean=("dec_mean_after", "mean"), dfin=("dec_final", "mean"), dmin=("dec_min_after", "min"), probes=("probes", "mean"),
    dec=("decreases", "mean"), v10=("p10_viol", "mean"), clamp=("epoch_clamped", "sum"))
g["r_%"] = 100 * g.bad / g.deliv.clip(lower=1); g["pu_%"] = 100 * g.ub / g.ut; g["r_after_%"] = 100 * g.baa / g.daa.clip(lower=1)
g["below_%"] = 100 * g.below / g.daa.clip(lower=1)
print(g[["n", "r_%", "pu_%", "fq", "alarm", "ep1", "fa", "r_after_%", "below_%", "dmean", "dfin", "dmin", "probes", "dec", "v10", "clamp"]].round(4).to_string())
print("\n== replay of Study 28's failing network (R28) ==")
print(d[d.block == "R28"][["arm", "delivered", "bad", "bad_after_alarm", "deliv_after_alarm", "dec_final", "dec_mean_after", "fq", "probes"]].to_string())
print("\n== post-alarm risk by arm (all model-error cells, pooled) ==")
y = x[x.sc.str.startswith("o0") & x.sc.str.endswith(("m0", "m0F")) & x.arm.str.startswith("kgM")]
print(y.groupby(["arm", "p"]).apply(lambda z: pd.Series(dict(r_after=z.bad_after_alarm.sum() / max(z.deliv_after_alarm.sum(), 1),
      nets_bad_after=int((z.bad_after_alarm > 0).sum()), runs=len(z), fq=z.fq.mean()))).round(5).to_string())
