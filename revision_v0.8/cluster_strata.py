"""Design check and per-stratum bounds for Table tab:cluster (not pre-registered).
For each claim: runs per network (is the design balanced?), and networks with any harm per stratum (hardware type,
and grid for S34) with exact one-sided 95% Clopper-Pearson bounds."""
import sys, os, pandas as pd
from scipy.stats import beta

_REPO = {"26_certified": "study26_certified", "27_certification": "study27_certification", "30_closed_loop": "study30_closed_loop",
         "32_robustness": "study32_robustness", "34_grids": "study34_grids"}
def _path(W, p):
    """Accept both the working layout (prx_work/26_certified/...) and the public repository (study26_certified/...)."""
    q = os.path.join(W, p)
    if os.path.exists(q): return q
    top, rest = p.split("/", 1); return os.path.join(W, _REPO.get(top, top), rest)
W = sys.argv[1]; cp = lambda k, n: 1.0 if k >= n else float(beta.ppf(0.95, k + 1, n - k))
def rd(p):
    d = pd.read_csv(_path(W, p)); d["sc"] = d.cfg.str.split("|").str[0]
    if "grid" not in d: d["grid"] = 5
    return d
s26 = rd("26_certified/des_s26_psc/runs.csv"); s30 = rd("30_closed_loop/des_s30_psc/runs.csv")
s32 = rd("32_robustness/des_s32_psc/runs.csv"); s32["blk"] = s32.block.str[-1]
s34 = pd.concat([rd(f"34_grids/des_s34_g{g}/runs.csv") for g in (5, 10, 30)], ignore_index=True); big = s34[s34.grid.isin([10, 30])]
G = ("kgMC", "kgMCp", "kgMCh"); C = ("o0.02", "o0.044", "o0.044F", "o0.08", "L0.044")
R = s32[s32.blk == "R"]; E = s32[s32.blk == "E"]
claims = [("S26 guard, no stressor", s26[(s26.block == "S26U") & s26.arm.isin(["bg", "kg", "ag2t"])], "users_bad"),
          ("S26 finite memory", s26[(s26.block == "S26S") & s26.arm.isin(["bg", "kg", "ag2t"])], "bad"),
          ("S30 after alarm, in class", s30[(s30.arm.isin(G) & s30.sc.isin(C)) | ((s30.arm == "kgMCs") & (s30.sc == "s0.044"))], "users_bad_post"),
          ("S30 always-on", s30[(s30.arm == "kgMCa") & s30.sc.isin(["-", "-F", "o0.02", "o0.044", "o0.044F", "o0.08"])], "users_bad_all"),
          ("S32 current-look, in class", R[(R.arm == "kgMChN") & R.sc.isin(["o0.044", "L0.044"])], "users_bad_post"),
          ("S32 variants after alarm", E[(E.arm == "kgMCh") & (E.sc == "o0.044")], "users_bad_post"),
          ("S32 always-on", E[E.arm == "kgMCa"], "users_bad_all"),
          ("S34 after alarm, large grids", big[(big.arm == "kgMChN") & big.sc.isin(["o0.044", "o0.044F"])], "users_bad_post"),
          ("S34 always-on, large grids", big[big.arm == "kgMCa"], "users_bad_served")]
for name, x, col in claims:
    rpn = x.groupby(["hw", "grid", "idx"]).size(); g = x.assign(h=x[col] > 0).groupby(["hw", "grid", "idx"]).h.any().reset_index()
    st = g.groupby(["hw", "grid"]).h.agg(["sum", "size"])
    strata = "; ".join(f"{hw}{'' if gr == 5 else f' {gr}x{gr}'}: {int(r['sum'])}/{int(r['size'])} (UB {100 * cp(int(r['sum']), int(r['size'])):.1f}%)" for (hw, gr), r in st.iterrows())
    print(f"{name}: runs/network min {rpn.min()} max {rpn.max()} (balanced: {rpn.min() == rpn.max()}); {strata}")
