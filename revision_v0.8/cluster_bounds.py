"""Exact cluster-level bounds for the headline simulation claims (re-reporting; not pre-registered).
For each claim: users harmed / users (as reported), and the independent replication units with ANY harm:
  runs (one simulated network under one arm/cell) and networks (hw, grid, idx: the bootstrap cluster of the locked analyses).
Bound: one-sided 95% Clopper-Pearson on the share of units with any harm. Since a user can be harmed only in a unit
that has some harm, P(a given user is harmed) <= P(its unit has any harm); the CP bound therefore bounds per-user risk
in the sense of Theorems 1-2 (averaged over the cells pooled), including when no unit had any harm.
Usage: python3 cluster_bounds.py <prx_work dir>"""
import sys, os, numpy as np, pandas as pd
from scipy.stats import beta

_REPO = {"26_certified": "study26_certified", "27_certification": "study27_certification", "30_closed_loop": "study30_closed_loop",
         "32_robustness": "study32_robustness", "34_grids": "study34_grids"}
def _path(W, p):
    """Accept both the working layout (prx_work/26_certified/...) and the public repository (study26_certified/...)."""
    q = os.path.join(W, p)
    if os.path.exists(q): return q
    top, rest = p.split("/", 1); return os.path.join(W, _REPO.get(top, top), rest)
W = sys.argv[1]
cp = lambda k, n, a=0.05: 1.0 if k >= n else float(beta.ppf(1 - a, k + 1, n - k))
def rd(p):
    d = pd.read_csv(_path(W, p)); d["sc"] = d.cfg.str.split("|").str[0]
    if "grid" not in d: d["grid"] = 5
    return d
rows = []
def claim(name, x, num, den, harm_col=None):
    harm = (x[harm_col or num] > 0)
    nets = x.assign(h=harm).groupby(["hw", "grid", "idx"]).h.any()
    rows.append(dict(claim=name, users=f"{int(x[num].sum())}/{int(x[den].sum())}",
        runs=f"{int(harm.sum())}/{len(x)}", run_ub=cp(int(harm.sum()), len(x)),
        nets=f"{int(nets.sum())}/{len(nets)}", net_ub=cp(int(nets.sum()), len(nets)),
        worst=max(((cp(int(v.sum()), len(v)), k, int(v.sum()), len(v)) for k, v in nets.groupby(level=["hw", "grid"])), key=lambda t: t[0])))
s26 = rd("26_certified/des_s26_psc/runs.csv")
claim("S26 U1 guard, no stressor (bg,kg,ag2t)", s26[(s26.block == "S26U") & s26.arm.isin(["bg", "kg", "ag2t"])], "users_bad", "users_total")
x = s26[(s26.block == "S26S") & s26.arm.isin(["bg", "kg", "ag2t"])]
claim("S26 S1 finite memory (bad pairs)", x, "bad", "delivered")
s30 = rd("30_closed_loop/des_s30_psc/runs.csv")
G = ("kgMC", "kgMCp", "kgMCh"); C = ("o0.02", "o0.044", "o0.044F", "o0.08", "L0.044")
p1 = s30[(s30.arm.isin(G) & s30.sc.isin(C)) | ((s30.arm == "kgMCs") & (s30.sc == "s0.044"))]
claim("S30 P1 post-alarm, in-class cells (as pre-registered)", p1, "users_bad_post", "users_post")
claim("S30 P1 without late-onset cell L0.044", p1[p1.sc != "L0.044"], "users_bad_post", "users_post")
claim("S30 P1 hybrid arm only (kgMCh)", p1[p1.arm == "kgMCh"], "users_bad_post", "users_post")
claim("S30 P3 always-on, whole run", s30[(s30.arm == "kgMCa") & s30.sc.isin(["-", "-F", "o0.02", "o0.044", "o0.044F", "o0.08"])], "users_bad_all", "users_total")
s32 = rd("32_robustness/des_s32_psc/runs.csv"); s32["blk"] = s32.block.str[-1]
R = s32[s32.blk == "R"]; E = s32[s32.blk == "E"]
claim("S32 R1 current-look bound, in class", R[(R.arm == "kgMChN") & R.sc.isin(["o0.044", "L0.044"])], "users_bad_post", "users_post")
claim("S32 R1 without late-onset cell", R[(R.arm == "kgMChN") & (R.sc == "o0.044")], "users_bad_post", "users_post")
claim("S32 E1 post-alarm, tau/calibration variants", E[(E.arm == "kgMCh") & (E.sc == "o0.044")], "users_bad_post", "users_post")
claim("S32 E2 always-on, Block E", E[E.arm == "kgMCa"], "users_bad_all", "users_total")
s34 = pd.concat([rd(f"34_grids/des_s34_g{g}/runs.csv") for g in (5, 10, 30)], ignore_index=True)
big = s34[s34.grid.isin([10, 30])]
claim("S34 K1 post-alarm, 10x10+30x30", big[(big.arm == "kgMChN") & big.sc.isin(["o0.044", "o0.044F"])], "users_bad_post", "users_post")
claim("S34 K2 always-on, 10x10+30x30 (served users)", big[big.arm == "kgMCa"], "users_bad_served", "users_served")
t = pd.DataFrame(rows); pd.set_option("display.width", 250); print(t.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
# detail of the harmed runs in S30 P1
h = p1[p1.users_bad_post > 0][["arm", "hw", "sc", "cfg", "idx", "users_bad_post", "users_post", "bad_after_alarm_all", "fa_first_t", "first_alarm_ep", "alarms"]]
print("\nS30 P1 harmed runs:\n", h.to_string(index=False))
# LaTeX rows for Table tab:cluster
lab = {"S26 U1 guard, no stressor (bg,kg,ag2t)": "S26: guard, per-user budget, no stressor",
       "S26 S1 finite memory (bad pairs)": "S26: finite memory (pairs, not users)",
       "S30 P1 post-alarm, in-class cells (as pre-registered)": "S30: provable margin after alarm, in class",
       "S30 P1 without late-onset cell L0.044": "\\quad same, without the late-onset cell",
       "S30 P1 hybrid arm only (kgMCh)": "\\quad same, hybrid check only",
       "S30 P3 always-on, whole run": "S30: always-on margin, whole run",
       "S32 R1 current-look bound, in class": "S32: current-look bound after alarm, in class",
       "S32 R1 without late-onset cell": "\\quad same, without the late-onset cell",
       "S32 E1 post-alarm, tau/calibration variants": "S32: after alarm, $\\tau$ and calibration variants",
       "S32 E2 always-on, Block E": "S32: always-on margin, variants",
       "S34 K1 post-alarm, 10x10+30x30": "S34: after alarm, $10\\times10$ and $30\\times30$",
       "S34 K2 always-on, 10x10+30x30 (served users)": "S34: always-on, larger grids (served users)"}
fmt = lambda f: f.replace("/", "\\,/\\,")
def num(x):
    k, n = x.split("/"); return f"{int(k):,}/{int(n):,}".replace(",", "{,}").replace("/", "\\,/\\,")
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cluster_rows.tex"), "w") as fh:
    for r_ in rows:
        w = r_["worst"]; hwname = {"ion2020": "ion2020", "ionproj": "ionproj", "nv2": "NV", "siv": "SiV"}[w[1][0]] + ("" if w[1][1] == 5 else f" {w[1][1]}$\\times${w[1][1]}")
        fh.write(f"{lab[r_['claim']]} & {num(r_['users'])} & {num(r_['runs'])} & {100*r_['run_ub']:.1f}\\% & {num(r_['nets'])} & {100*r_['net_ub']:.1f}\\% & {hwname}: {w[2]}\\,/\\,{w[3]}, {100*w[0]:.1f}\\%\\\\\n")
