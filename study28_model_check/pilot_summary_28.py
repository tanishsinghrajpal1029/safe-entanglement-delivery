"""Study 28 dev-pilot summary (descriptive; used only to set the pre-registered bars and the power map).
Usage: python3 pilot_summary_28.py runs.csv"""
import sys
import numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1]); d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]
d["fq"] = d.qual / d.oracle_qual.clip(lower=1)
d["tests"] = np.where(d.p == "p20", d.p20_tests, d.p10_tests)
d["kept_bad"] = np.where(d.p == "p20", d.p20_kept_bad, d.p10_kept_bad)
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 600)
g = d.groupby(["hw", "sc", "arm", "p"])
T = g.agg(n=("run", "size"), deliv=("delivered", "sum"), bad=("bad", "sum"), ubad=("users_bad_all", "sum"), utot=("users_total", "sum"),
          anybad=("any_bad_all", "mean"), fq=("fq", "mean"), tests=("tests", "mean"), alarm=("alarms", lambda x: (x > 0).mean()),
          alarms=("alarms", "mean"), ep1=("first_alarm_ep", "median"), fa_d=("fa_first_d", "sum"), fa_t=("fa_first_t", "sum"),
          fas_t=("fa_seg_t", "sum"), baa=("bad_after_alarm", "sum"), daa=("deliv_after_alarm", "sum"), dec=("dec_final", "mean"),
          incmax=("inc_max", "max"), v10=("p10_viol", "mean"), v20=("p20_viol", "mean"), L10=("p10_L", "mean"), F10=("p10_F", "mean"),
          clamp=("epoch_clamped", "sum"))
T["r_%"] = 100 * T.bad / T.deliv.clip(lower=1); T["pu_%"] = 100 * T.ubad / T.utot; T["r_after_%"] = 100 * T.baa / T.daa.clip(lower=1)
print(T[["n", "deliv", "r_%", "pu_%", "anybad", "fq", "tests", "alarm", "alarms", "ep1", "fa_d", "fa_t", "fas_t", "r_after_%", "dec", "incmax",
         "v10", "v20", "L10", "F10", "clamp"]].round(4).to_string())
print("\n== bad delivered pairs: feedback arm / its reference (same networks) ==")
ref = {"kgM": "kg", "kgP": "kg", "kgNM": "kgN"}
for (hw, sc), x in d.groupby(["hw", "sc"]):
    for a, b in ref.items():
        B = x[x.arm == b].bad.sum(); Bq = x[x.arm == b].fq.mean()
        for p in ("p10", "p20"):
            A = x[(x.arm == a) & (x.p == p)]
            if len(A) and B > 0: print(f"{hw:8s} {sc:11s} {a:5s} {p}  bad {int(A.bad.sum()):7d} / {int(B):7d} = {A.bad.sum() / B:.3f}   fq {A.fq.mean():.3f} vs {Bq:.3f}")
print("\n== o0.044 baselines (ion): kg undeclared, tomography m16, oracle; vs kgM ==")
for hw in ("ion2020", "ionproj"):
    x = d[d.hw == hw]
    for lab, sel in (("kg m0", (x.sc == "o0.044_m0") & (x.arm == "kg")), ("kg m16", x.sc == "o0.044_m16"), ("kg orc", x.sc == "o0.044_orc"),
                     ("kgM p10", (x.sc == "o0.044_m0") & (x.arm == "kgM") & (x.p == "p10")), ("kgM p20", (x.sc == "o0.044_m0") & (x.arm == "kgM") & (x.p == "p20"))):
        y = x[sel]
        if len(y): print(f"{hw:8s} {lab:8s} bad {int(y.bad.sum()):7d}  r {100 * y.bad.sum() / max(y.delivered.sum(), 1):6.2f}%  fq {y.fq.mean():.3f}  dec {y.dec_final.mean():.3f}")
print("\n== power map: mean tests per run (own stream) and alarm rate, feedback arms ==")
print(d[d.arm.isin(["kgM", "kgNM", "kgP"])].groupby(["hw", "sc", "arm", "p"]).agg(tests=("tests", "mean"), alarm=("alarms", lambda x: (x > 0).mean())).round(3).unstack(["arm", "p"]).to_string())
M = d[d.arm.isin(["kgM", "kgNM"])]
print("\nfirst-alarm false alarms (tested null), '-' and 'ro':", int(M[M.sc.isin(["-", "ro"])].fa_first_t.sum()), "/", int(M.sc.isin(["-", "ro"]).sum()),
      "| segment false alarms, all scenarios:", int(M.fa_seg_t.sum()), "| runs with an alarm:", int((M.alarms > 0).sum()), "/", len(M))
print("kgN any_bad_all in '-':", d[(d.arm == "kgN") & (d.sc == "-")].any_bad_all.mean(), " kg:", d[(d.arm == "kg") & (d.sc == "-")].any_bad_all.mean())
print("certificate violations p10/p20:", d.p10_viol.mean().round(4), d.p20_viol.mean().round(4), " clamped:", int(d.epoch_clamped.sum()))
