"""Study 30 dev-pilot summary (descriptive; sets the pre-registered bars). Usage: python3 pilot_summary_30.py runs.csv"""
import sys
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1]); d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]
d["fq"] = d.qual / d.oracle_qual.clip(lower=1)
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 600)
P = lambda *a: print(*a, flush=True)
P(f"rows {len(d)}; clamped {int(d.epoch_clamped.sum())}; arms {sorted(d.arm.unique())}")
g = d.groupby(["hw", "sc", "arm", "p"]).agg(n=("run", "size"), deliv=("delivered", "sum"), bad=("bad", "sum"),
    ub=("users_bad_all", "sum"), ut=("users_total", "sum"), fq=("fq", "mean"), alarm=("alarms", lambda s: (s > 0).mean()),
    ep1=("first_alarm_ep", "median"), fa=("fa_first_t", "sum"), baa=("bad_after_alarm_all", "sum"), daa=("deliv_after_alarm_all", "sum"),
    runs_bad_after=("bad_after_alarm_all", lambda s: int((s > 0).sum())), ubp=("users_bad_post", "sum"), upost=("users_post", "sum"),
    dmean=("dec_mean_after", "mean"), omean=("opt_mean_after", "mean"), probes=("probes", "mean"), dec=("decreases", "mean"),
    v10=("p10_viol", "mean"), v20=("p20_viol", "mean"))
g["r_%"] = 100 * g.bad / g.deliv.clip(lower=1); g["pu_%"] = 100 * g.ub / g.ut; g["r_after_%"] = 100 * g.baa / g.daa.clip(lower=1)
g["pu_post_%"] = 100 * g.ubp / g.upost.clip(lower=1); g["excess"] = g.dmean - g.omean
P(g[["n", "r_%", "pu_%", "fq", "alarm", "ep1", "fa", "r_after_%", "runs_bad_after", "pu_post_%", "dmean", "omean", "excess", "probes", "dec"]].round(4).to_string())

P("\n== post-alarm risk, provable arms, in-class cells (constant class: o*, -F, L0.044; storage class: s0.044) ==")
inc = d[((d.arm.isin(["kgMC", "kgMCp", "kgMCh"])) & d.sc.isin(["o0.02", "o0.044", "o0.044F", "o0.08", "L0.044"])) | ((d.arm == "kgMCs") & (d.sc == "s0.044"))]
P(inc.groupby(["arm"]).apply(lambda z: pd.Series(dict(runs=len(z), runs_bad_after=int((z.bad_after_alarm_all > 0).sum()),
    r_after=z.bad_after_alarm_all.sum() / max(z.deliv_after_alarm_all.sum(), 1), users_bad_post=int(z.users_bad_post.sum()),
    users_post=int(z.users_post.sum()), fq=z.fq.mean()))).round(5).to_string())
P("\n== kgMT (heuristic) on the same cells ==")
mt = d[(d.arm == "kgMT") & d.sc.isin(["o0.02", "o0.044", "o0.044F", "o0.08", "L0.044"])]
P(pd.Series(dict(runs=len(mt), runs_bad_after=int((mt.bad_after_alarm_all > 0).sum()), r_after=mt.bad_after_alarm_all.sum() / max(mt.deliv_after_alarm_all.sum(), 1))).round(5).to_string())
P("\n== out-of-class and stress cells (descriptive) ==")
oc = d[d.sc.isin(["h0.044", "L0.044F", "s0.044", "o0.044F"]) & d.arm.str.startswith("kgM")]
P(oc.groupby(["sc", "arm"]).apply(lambda z: pd.Series(dict(runs=len(z), runs_bad_after=int((z.bad_after_alarm_all > 0).sum()),
    r_after=z.bad_after_alarm_all.sum() / max(z.deliv_after_alarm_all.sum(), 1), r_all=z.bad.sum() / max(z.delivered.sum(), 1),
    pu=z.users_bad_all.sum() / z.users_total.sum(), fq=z.fq.mean()))).round(5).to_string())
P("\n== detection: alarm rate and median first-alarm epoch by detector (L0.044: onset at epoch 30; o0.044) ==")
det = d[d.arm.isin(["kgMC", "kgMCp", "kgMCh"]) & d.sc.isin(["L0.044", "o0.044", "o0.02", "s0.044", "h0.044"])]
P(det.groupby(["hw", "sc", "p", "arm"]).agg(alarm=("alarms", lambda s: (s > 0).mean()), ep1=("first_alarm_ep", "median"),
    bad=("bad", "sum"), fq=("fq", "mean")).round(3).to_string())
P("\n== false alarms (no stressor, no forcing) ==")
fa = d[(d.sc == "-") & d.arm.str.startswith("kgM")]
P(fa.groupby(["arm", "p"]).agg(runs=("run", "size"), fa=("fa_seg_t", "sum"), anyalarm=("alarms", lambda s: (s > 0).mean()), fq=("fq", "mean")).round(4).to_string())
P("\n== worst-user risk over the whole run (all pairs, incl. before the alarm) ==")
P(d.groupby(["sc", "arm"]).apply(lambda z: pd.Series(dict(pu_all=z.users_bad_all.sum() / z.users_total.sum(),
    runs_any_bad=int((z.bad_all > 0).sum()), runs=len(z)))).round(4).unstack("arm").to_string())
P("\n== static and oracle baselines vs provable arms (throughput fq) ==")
P(d[d.sc.isin(["-", "o0.044", "s0.044"])].groupby(["hw", "sc", "arm", "p"]).fq.mean().round(4).unstack(["arm"]).to_string())
P(d[d.cfg.str.contains("_fix|_orc")].groupby(["hw", "cfg"]).agg(fq=("fq", "mean"), bad=("bad", "sum")).round(4).to_string())
