"""Paper figures from the FINAL confirmatory run (reads locked outputs only; no re-analysis choices).
Fig1: risk law (predicted vs measured r_cond, des_final_law/analysis_v7_runs.csv).
Fig2: conditional risk per group: adaptive (CP95 upper bar) vs fixed z=2 vs LTT tuned on S0 / S1 (des_final_psc/final_groups.csv).
Fig3: adaptive fraction of oracle with path-bootstrap 95% CI (final_groups.csv)."""
import math, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"; INK, MUT, GRIDC = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT, "ytick.color": MUT,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRIDC, "grid.linewidth": 0.6,
                     "legend.frameon": False, "savefig.dpi": 220, "font.family": "DejaVu Sans"})
gname = {1e-9: "g=0", 1e-5: "g=1e-5", 1e-4: "g=1e-4"}; cname = {"ion_2020": "ion-2020 L2", "ion_proj": "ion-proj L3", "ion_future": "ion-future L4"}
# ---- Fig 1
R = pd.read_csv("des_final_law/analysis_v7_runs.csv"); q = R[(R.delivered >= 100) & (R.z >= 1) & (R.bad > 0)].copy()
fig, ax = plt.subplots(figsize=(4.2, 3.8))
for est, col, lab in (("static", C1, "static estimator"), ("ols_reset", C2, "drift-aware (OLS) estimator")):
    d = q[q.est == est]; ax.scatter(d.r_pred, d.r_meas, s=14, color=col, alpha=0.75, edgecolors="white", linewidths=0.4, label=lab)
lo, hi = 1e-4, 1.0; ax.plot([lo, hi], [lo, hi], color=MUT, lw=1, ls="--", label="measured = predicted")
ax.set(xscale="log", yscale="log", xlim=(lo, hi), ylim=(lo, hi), xlabel="predicted conditional risk (headroom-histogram law)",
       ylabel="measured conditional risk  $r_{cond}$")
rk = lambda v: pd.Series(v).rank().values
rho = np.corrcoef(rk(q.r_pred), rk(q.r_meas))[0, 1]; mlr = np.median(np.abs(np.log(q.r_meas / q.r_pred)))
ax.set_title("Risk law (final confirmatory run)", fontsize=9, color=INK, loc="left")
ax.text(0.98, 0.03, f"locked analysis (609 runs): Spearman 0.961\nshown: {len(q)} runs with ≥1 bad pair\n(Spearman {rho:.3f} on shown runs)", transform=ax.transAxes, ha="right", va="bottom", fontsize=7, color=MUT)
ax.legend(loc="upper left", fontsize=8); fig.tight_layout(); fig.savefig("figs_final/fig1_risk_law.png"); fig.savefig("figs_final/fig1_risk_law.pdf")
# ---- Fig 2
T = pd.read_csv("des_final_psc/final_groups.csv").sort_values(["cell", "g", "est"], key=lambda s: s.map({"ion_2020": 0, "ion_proj": 1, "ion_future": 2}).fillna(s) if s.name == "cell" else s)
T["label"] = [f"{cname[c]} · {gname[g]} · {'OLS' if e == 'ols_reset' else 'static'}" for c, g, e in zip(T.cell, T.g, T.est)]
y = np.arange(len(T))[::-1]; fl = 1e-4
def clip(v): return np.maximum(v / 100.0, fl)
fig, ax = plt.subplots(figsize=(6.6, 5.2))
ax.axvline(0.01, color=INK, lw=1, ls="--"); ax.text(0.0105, y.max() + 0.6, "target 1%", fontsize=7.5, color=INK, va="bottom")
ok = T.ad_deliv > 0
ax.hlines(y[ok], clip(T.ad_r[ok]), clip(T.ad_ucb[ok]), color=C1, lw=2, alpha=0.5)
ax.scatter(clip(T.ad_r[ok]), y[ok], s=36, color=C1, edgecolors="white", linewidths=0.8, zorder=3, label="label-free adaptive (bar: 95% upper bound)")
for yi, n in zip(y, T.ad_deliv):
    if n < 200: ax.text(1.05 * fl * 0.8, yi + 0.3, "adaptive: " + ("no deliveries" if n == 0 else f"only {n} deliveries (excluded from F2)"), fontsize=6.3, color=MUT, va="center")
m = T.z2_deliv > 0; ax.scatter(clip(T.z2_r[m]), y[m] + 0.18, s=28, marker="s", color=C2, edgecolors="white", linewidths=0.8, zorder=3, label="fixed z = 2")
m = T.lttS0_deliv > 0; ax.scatter(clip(T.lttS0_r[m]), y[m] - 0.18, s=30, marker="D", color=C3, edgecolors="white", linewidths=0.8, zorder=3, label="LTT tuned on matched dev paths (S0)")
m = T.lttS1_deliv > 0; ax.scatter(clip(T.lttS1_r[m]), y[m] - 0.32, s=30, marker="^", color=C4, edgecolors="white", linewidths=0.8, zorder=3, label="LTT tuned on shifted dev paths (S1)")
ax.set(xscale="log", xlim=(fl * 0.8, 1.0), yticks=y, xlabel="conditional risk among delivered pairs (values < 0.01% drawn at 0.01%)")
ax.set_yticklabels(T.label, fontsize=7.5); ax.grid(axis="y", visible=False)
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2, fontsize=7.5)
fig.tight_layout(); fig.savefig("figs_final/fig2_safety.png"); fig.savefig("figs_final/fig2_safety.pdf")
# ---- Fig 3
fig, ax = plt.subplots(figsize=(6.6, 4.6))
ax.hlines(y, T.ad_frac_lo, T.ad_frac_hi, color=C1, lw=2, alpha=0.5)
ax.scatter(T.ad_frac, y, s=36, color=C1, edgecolors="white", linewidths=0.8, zorder=3)
for yi, f, h in zip(y, T.ad_frac, T.ad_frac_hi): ax.text(max(h, f) + 0.012, yi, f"{f:.3f}", fontsize=7, color=MUT, va="center")
ax.axvline(0.7, color=MUT, lw=1, ls=":"); ax.text(0.695, y.max() + 0.6, "calibration-share ceiling, 1 − ρ = 0.7", fontsize=7, color=MUT, va="bottom", ha="right")
ax.set(xlim=(0, 0.8), yticks=y, xlabel="qualified deliveries as a fraction of the oracle (95% path-bootstrap CI)")
ax.set_yticklabels(T.label, fontsize=7.5); ax.grid(axis="y", visible=False)
fig.tight_layout(); fig.savefig("figs_final/fig3_frontier.png"); fig.savefig("figs_final/fig3_frontier.pdf")
print("figures written")
