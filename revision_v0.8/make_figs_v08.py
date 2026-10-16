"""Figures 1, 3, 4, 5 and 6 for manuscript v0.8. Every number is read from the pre-registered study outputs (runs.csv of
S26, S27, S30), the recorded IBM outcomes (replayed by replay_ibm.py -> ibm_traj.json) and the S36 trajectory
(trajectory_36.py -> trajectory_36.csv). New in v0.8: 95% intervals from a bootstrap over networks (4,000 resamples
of network idx within hardware type, percentile, seed 8), Fig. 1 relabelled, Fig. 6 added. Fig. 2 is unchanged (v0.6.3).
Usage: python3 make_figs_v08.py <prx_work dir> <ibm_traj.json> <trajectory_36.csv>"""
import sys, json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(ROOT, "study27_certification"), os.path.join(ROOT, "study28_model_check")]
from cert import Certifier
import lb as LB


_REPO = {"26_certified": "study26_certified", "27_certification": "study27_certification", "30_closed_loop": "study30_closed_loop",
         "32_robustness": "study32_robustness", "34_grids": "study34_grids"}
def _path(W, p):
    """Accept both the working layout (prx_work/26_certified/...) and the public repository (study26_certified/...)."""
    q = os.path.join(W, p)
    if os.path.exists(q): return q
    top, rest = p.split("/", 1); return os.path.join(W, _REPO.get(top, top), rest)
W, IBM, OXF = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs("figs", exist_ok=True)
C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#8a63d2"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6, "font.family": "DejaVu Sans",
                     "legend.frameon": False, "savefig.dpi": 300})
W2 = 7.0
RNG = np.random.default_rng(8); B = 4000
ERR = dict(ecolor=INK2, elinewidth=0.7, capsize=1.5, capthick=0.7, lw=0)


def panel(ax, s, x=-0.14):
    ax.text(x, 1.04, s, transform=ax.transAxes, fontweight="bold", fontsize=9, color=INK)


def ratio_ci(df, num, den):
    """Pooled ratio sum(num)/sum(den) and a 95% percentile interval, resampling networks (idx) within hardware type."""
    parts = [x.groupby("idx")[[num, den]].sum().to_numpy(float) for _, x in df.groupby("hw")]
    est = sum(p[:, 0].sum() for p in parts) / max(sum(p[:, 1].sum() for p in parts), 1e-12)
    st = np.empty(B)
    for b in range(B):
        t = np.zeros(2)
        for p in parts: t += p[RNG.integers(0, len(p), len(p))].sum(0)
        st[b] = t[0] / max(t[1], 1e-12)
    lo, hi = np.quantile(st, [0.025, 0.975]); return est, est - lo, hi - est


def mean_ci(df, col):
    df = df.assign(one=1.0); return ratio_ci(df.assign(_v=df[col]), "_v", "one")


def yerr(cis): return np.array([[c[1] for c in cis], [c[2] for c in cis]])


# ---------------- Fig 1: the two layers (labels moved clear of each other)
fig, ax = plt.subplots(figsize=(W2, 2.3)); ax.axis("off"); ax.set_xlim(0, 10.6); ax.set_ylim(-0.1, 3.05)
def box(x, y, w, h, t, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12", fc=fc, ec=INK2, lw=0.6))
    ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=6.8, color=INK)
box(0.1, 1.0, 2.0, 1.1, "Network\n(links, memories,\nrouting, drift, faults)", "#f1f0ec")
box(2.7, 1.8, 3.5, 1.15, "Model-based guard (layer 1)\nanytime bounds on link parameters\n+ physics model + declared margin\n→ decides WHAT to deliver", "#e6f0fb")
box(2.7, 0.0, 3.5, 1.15, "Model-free certificate (layer 2)\nusers test a random fraction p\nin X/Y/Z, hidden from the network\n→ certifies the kept pairs' average\n→ runs the model check", "#e4f6ee")
box(7.0, 1.0, 3.5, 1.1, "User receives:\n• per-pair claim (rests on the model)\n• certified average fidelity\n   (model-free, anytime,\n   trusted measurements)", "#f1f0ec")
for (x0, y0, x1, y1) in ((2.1, 1.55, 2.7, 2.3), (6.2, 2.35, 7.0, 1.75), (6.2, 0.6, 7.0, 1.35)):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8))
ax.annotate("", xy=(3.6, 1.15), xytext=(3.6, 1.8), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.8))
ax.text(3.5, 1.47, "delivered\npairs", fontsize=6.2, color=INK2, ha="right", va="center")
ax.annotate("", xy=(5.3, 1.8), xytext=(5.3, 1.15), arrowprops=dict(arrowstyle="-|>", color=C3, lw=1.1))
ax.text(5.4, 1.47, "alarm →\nraise margin", fontsize=6.2, color=C3, ha="left", va="center")
fig.savefig("figs/fig1_layers.pdf", bbox_inches="tight"); fig.savefig("figs/fig1_layers.png", bbox_inches="tight", dpi=150); plt.close(fig)

# ---------------- Fig 3: model-based layer (S26), with 95% intervals over networks
d = pd.read_csv(_path(W, "26_certified/des_s26_psc/runs.csv")); d["blk"] = d.block.str[-1]
R = d[(d.blk == "R") & (d.hw == "ion2020")]
conds = [("n0.033_e", "ICFO\nmedian"), ("n0.075_e", "ICFO\nmax"), ("n0.184_e", "USTC"), ("n0.184_h", "USTC\nhetero."), ("n0.184_a", "USTC\npersistent")]
arms = [("kg", "undeclared (fleet prior)", C2), ("kgR", "declared from data (recipe)", C1), ("kgO", "declared exactly (oracle)", C3)]
fig, (a, b) = plt.subplots(1, 2, figsize=(W2, 2.5), gridspec_kw=dict(width_ratios=[1.35, 1]))
x = np.arange(len(conds)); wd = 0.26; F3 = {}
for i, (arm, lab, col) in enumerate(arms):
    cis = [ratio_ci(R[(R.cfg == cf) & (R.arm == arm)], "users_bad", "users_total") for cf, _ in conds]
    F3[arm] = [c[0] for c in cis]
    a.bar(x + (i - 1) * wd, [100 * c[0] for c in cis], width=wd - 0.03, color=col, label=lab, zorder=3)
    a.errorbar(x + (i - 1) * wd, [100 * c[0] for c in cis], yerr=100 * yerr(cis), zorder=4, **ERR)
a.axhline(5, color=INK2, lw=0.8, ls="--", zorder=2); a.text(-0.45, 5.4, "5% safety bar (on upper bounds)", fontsize=6.0, color=INK2)
a.set_xticks(x); a.set_xticklabels([l for _, l in conds], fontsize=6.5); a.set_ylabel("users ever given a bad pair (%)")
a.legend(fontsize=6.3, loc="upper left"); a.grid(axis="y", color=GRID, lw=0.5, zorder=0); panel(a, "(a)")
O = d[(d.blk == "O")]
for hw, col, mk in (("ion2020", C1, "o"), ("ionproj", C3, "s")):
    o = O[O.hw == hw]; Ms = [4, 16, 64, 256]
    cis = [ratio_ci(o[o.cfg == f"o0.044_m{m}"], "qual", "oracle_qual") for m in Ms]
    b.errorbar(Ms, [c[0] for c in cis], yerr=yerr(cis), color=col, lw=1.6, marker=mk, ms=4, capsize=1.5, elinewidth=0.7, label=hw)
    b.axhline(ratio_ci(o[o.cfg == "o0.044_orc"], "qual", "oracle_qual")[0], color=col, lw=0.8, ls=":")
    F3[hw] = [c[0] for c in cis]
b.set_xscale("log", base=2); b.set_xticks([4, 16, 64, 256]); b.set_xticklabels(["4\n(USTC-like)", "16", "64", "256"])
b.set_xlabel("tomography points M (Δ = 0.044)"); b.set_ylabel("declared-margin guard throughput\n(fraction of oracle)")
b.set_ylim(0, 1); b.legend(fontsize=6.5, loc="lower right"); b.grid(axis="y", color=GRID, lw=0.5); panel(b, "(b)")
b.text(4.2, 0.93, "dotted: margin known exactly", fontsize=6, color=INK2)
fig.tight_layout(); fig.savefig("figs/fig3_control_layer.pdf", bbox_inches="tight"); fig.savefig("figs/fig3_control_layer.png", bbox_inches="tight", dpi=150); plt.close(fig)

# ---------------- Fig 4: certification layer (S27), with intervals
d = pd.read_csv(_path(W, "27_certification/des_s27_psc/runs.csv")); d["scen"] = d.cfg.str.split("|").str[0]
sc = [("-", "none"), ("fault", "memory\nfault"), ("n0.184_a", "persist.\nnoise"), ("o0.044_m0", "model\noptimism")]
k = d[(d.hw == "ion2020") & (d.arm == "kg")]
fig, (a, b, cc) = plt.subplots(1, 3, figsize=(W2, 2.4), gridspec_kw=dict(width_ratios=[1, 1.15, 1.1]))
x = np.arange(len(sc)); F4 = {}
cis = [ratio_ci(k[k.scen == s], "bad", "delivered") for s, _ in sc]; F4["bad"] = [c[0] for c in cis]
a.bar(x, [100 * c[0] for c in cis], width=0.6, color=C2, zorder=3); a.errorbar(x, [100 * c[0] for c in cis], yerr=100 * yerr(cis), zorder=4, **ERR)
a.set_xticks(x); a.set_xticklabels([l for _, l in sc], fontsize=6)
a.set_ylabel("delivered pairs below threshold (%)"); a.grid(axis="y", color=GRID, lw=0.5, zorder=0); panel(a, "(a)")
for xi, c in zip(x, cis): a.text(xi + 0.08, 100 * (c[0] + c[2]) + 0.6, f"{100 * c[0]:.1f}", ha="center", fontsize=6, color=INK)
tru = [mean_ci(k[k.scen == s], "p10_net_F") for s, _ in sc]; cer = [mean_ci(k[k.scen == s], "p10_net_L") for s, _ in sc]
F4["tru"] = [c[0] for c in tru]; F4["cer"] = [c[0] for c in cer]
b.errorbar(x - 0.08, [c[0] for c in tru], yerr=yerr(tru), color=C1, marker="o", ms=4, lw=0, elinewidth=0.8, capsize=1.5, zorder=3, label="true average (kept)")
b.errorbar(x + 0.08, [c[0] for c in cer], yerr=yerr(cer), color=C3, marker="D", ms=4, lw=0, elinewidth=0.8, capsize=1.5, zorder=3, label="certified (p = 0.1)")
b.axhline(0.9, color=INK2, lw=0.8, ls="--"); b.text(-0.35, 0.902, "τ = 0.9", fontsize=6, color=INK2)
b.set_xticks(x); b.set_xticklabels([l for _, l in sc], fontsize=6); b.set_ylabel("kept-pair average fidelity"); b.set_ylim(0.86, 0.96)
b.legend(fontsize=6, loc="lower left"); b.grid(axis="y", color=GRID, lw=0.5); panel(b, "(b)")
targets = np.linspace(0.80, 0.94, 15)
for p, col in ((0.05, C2), (0.1, C1), (0.2, C3)):
    ce = Certifier(p, 0.05); need = []
    for Ft in targets:
        K = 10
        while ce.lower(int(round(K * p / (1 - p) * (2 / 3) * 0.03)), K) < Ft and K < 10 ** 6: K = int(K * 1.05) + 1
        need.append(K)
    cc.plot(targets, need, color=col, lw=2, label=f"p = {p}")
cc.set_yscale("log"); cc.set_xlabel("average fidelity to certify"); cc.set_ylabel("kept pairs needed (α = 0.05)")
cc.legend(fontsize=6.3); cc.grid(color=GRID, lw=0.5); panel(cc, "(c)")
fig.tight_layout(); fig.savefig("figs/fig4_certification.pdf", bbox_inches="tight"); fig.savefig("figs/fig4_certification.png", bbox_inches="tight", dpi=150); plt.close(fig)

# ---------------- Fig 5: closed loop (S30), with intervals; the label window is now stated per bar group
d = pd.read_csv(_path(W, "30_closed_loop/des_s30_psc/runs.csv")); d["sc"] = d.cfg.str.split("|").str[0]
rows = [("no\ncheck", (d.sc == "o0.044") & (d.arm == "kg"), "whole"), ("tracking\n(heuristic)", (d.sc == "o0.044") & (d.arm == "kgMT"), "post"),
        ("provable,\ngated", (d.sc == "o0.044") & (d.arm == "kgMCh"), "post"), ("provable,\nalways-on", (d.sc == "o0.044") & (d.arm == "kgMCa"), "whole"),
        ("fixed\nmargin", d.sc == "o0.044_fix", "whole"), ("exact\nmargin", d.sc == "o0.044_orc", "whole")]
fig, ((a, b), (c, e)) = plt.subplots(2, 2, figsize=(W2, 4.5))
xs = np.arange(len(rows)); wbar = 0.38; F5 = {}
for hi_, (hw, col) in enumerate((("ion2020", C1), ("ionproj", C3))):
    off = (hi_ - 0.5) * wbar
    for xi, (lab, sel, kind) in zip(xs, rows):
        y = d[sel & (d.hw == hw)]
        fq = mean_ci(y.assign(fq=y.qual / y.oracle_qual.clip(lower=1)), "fq")   # mean of per-run throughput, as in v0.6.3
        if kind == "post": risk = y.bad_after_alarm_all.sum() / max(y.deliv_after_alarm_all.sum(), 1)
        else: risk = y.bad.sum() / max(y.delivered.sum(), 1)
        a.bar(xi + off, fq[0], width=wbar, color=col, zorder=3, label=hw if xi == 0 else None, hatch="////" if kind == "post" else None, edgecolor="white", lw=0)
        a.errorbar([xi + off], [fq[0]], yerr=[[fq[1]], [fq[2]]], zorder=4, **ERR)
        a.text(xi + off, fq[0] + fq[2] + 0.03, "n/a" if y.delivered.sum() == 0 else f"{100 * risk:.0f}", ha="center", fontsize=5.2, color=INK)
        pu = ratio_ci(y, "users_bad_all", "users_total")
        b.bar(xi + off, pu[0], width=wbar, color=col, zorder=3, label=hw if xi == 0 else None)
        b.errorbar([xi + off], [pu[0]], yerr=[[pu[1]], [pu[2]]], zorder=4, **ERR)
        b.text(xi + off, pu[0] + pu[2] + 0.015, f"{pu[0]:.2f}" if pu[0] > 0 else "0", ha="center", fontsize=5.0, color=INK)
        F5[(lab.replace("\n", " "), hw)] = (round(fq[0], 3), round(risk, 3), round(pu[0], 3))
for ax in (a, b):
    ax.set_xticks(xs); ax.set_xticklabels([r[0] for r in rows], fontsize=6.2); ax.grid(axis="y", color=GRID, lw=0.5, zorder=0)
    ax.legend(fontsize=6, loc="upper right")
a.set_ylim(0, 1.3); a.set_ylabel("throughput (good pairs / oracle)"); panel(a, "(a)", -0.11)
a.set_title("offset 0.044; labels: % bad, after the alarm (hatched) or whole run", fontsize=6.0, color=INK2, loc="right")
b.set_ylim(0, 0.8); b.set_ylabel("users ever given a bad pair"); b.set_title("offset 0.044; whole run", fontsize=6.4, color=INK2, loc="right"); panel(b, "(b)", -0.11)
for (arm, scs, col, mk, lab) in (("kgMCh", ["o0.02", "o0.044"], C1, "o", "constant class"), ("kgMCs", ["s0.044"], C3, "s", "storage class")):
    for s_ in scs:
        y = d[(d.arm == arm) & (d.sc == s_) & d.dec_mean_after.notna()]
        c.scatter(y.opt_mean_after, y.dec_mean_after, s=6, color=col, alpha=0.55, marker=mk, lw=0, label=lab if s_ == scs[-1] else None)
c.plot([0, 0.08], [0, 0.08], color=INK2, lw=0.8, ls="--"); c.set_xlim(0, 0.07); c.set_ylim(0, 0.08)
c.set_xlabel("true offset (mean, post-alarm)"); c.set_ylabel("provable margin (mean)"); c.legend(fontsize=5.6, loc="upper left", markerscale=1.5)
c.grid(color=GRID, lw=0.5); panel(c, "(c)", -0.11)
ps = np.array([0.05, 0.075, 0.1, 0.15, 0.2])
e.plot(ps, [LB.k_c1(p, 0.9) for p in ps], color=C1, marker="o", ms=4, lw=1.6, label="our certificate")
e.plot(ps, [LB.k_lb(p, 0.9) for p in ps], color=C2, marker="s", ms=4, lw=1.6, label="converse floor (Pauli tests, all pass)")
e.set_yscale("log"); e.set_yticks([150, 300, 600, 1200]); e.set_yticklabels(["150", "300", "600", "1200"]); e.minorticks_off()
e.set_xlabel("test fraction p"); e.set_ylabel("kept pairs to certify 0.9"); e.legend(fontsize=5.8); e.grid(color=GRID, lw=0.5); panel(e, "(d)", -0.11)
fig.tight_layout(); fig.savefig("figs/fig5_loop.pdf", bbox_inches="tight"); fig.savefig("figs/fig5_loop.png", bbox_inches="tight", dpi=150); plt.close(fig)

if not os.path.exists(OXF):
    print("Fig. 6 skipped: " + OXF + " not found (it is made by trajectory_36.py from the Oxford data, which are not redistributed)")
else:
    # ---------------- Fig 6 (new): hardware and Oxford trajectories
    R6 = json.load(open(IBM)); T36 = pd.read_csv(OXF)
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(W2, 2.7), gridspec_kw=dict(width_ratios=[1, 1.1, 1.1]))
    for name, col in (("S31", C1), ("S31b", C2)):
        C_ = R6[name]["C"]; K = np.array(C_["K"])
        a.fill_between(K, C_["lo"], C_["hi"], color=col, alpha=0.18, lw=0)
        a.plot(K, C_["bell"], color=col, lw=0.9, ls="--")
        a.plot(K, C_["L"], color=col, lw=1.6, label=f"{name}: certificate")
    a.plot([], [], color=INK2, lw=0.9, ls="--", label="Bell reference\n(approx. pointwise 95% intervals)")
    a.set_xlabel("kept pairs"); a.set_ylabel("fraction passing a Φ⁺ test"); a.set_ylim(0, 1.0); a.legend(fontsize=5.2, loc="lower right", handlelength=1.6)
    a.grid(color=GRID, lw=0.5); panel(a, "(a)")
    for name, col in (("S31", C1), ("S31b", C2)):
        T_ = R6[name]["T"]; t = np.array(T_["t"]) - R6[name]["nA"]
        b.plot(t, T_["mix"], color=col, lw=1.0, ls=":")
        b.plot(t, T_["hyb"], color=col, lw=1.5, label=name)
    b.axhline(R6["S31"]["thr"], color=INK2, lw=0.8, ls="--"); b.text(470, R6["S31"]["thr"] + 0.2, "alarm level", fontsize=6, color=INK2, ha="right")
    b.axvspan(0, max(len(R6[n]["T"]["t"]) - R6[n]["nA"] for n in R6), color=GRID, alpha=0.35, lw=0); b.text(10, -5.2, "phase B (20% bad pairs)", fontsize=6, color=INK2)
    b.plot([], [], color=INK2, lw=1.5, label="hybrid check"); b.plot([], [], color=INK2, lw=1.0, ls=":", label="fixed-bet check")
    b.set_xlabel("tests since the start of phase B"); b.set_ylabel("log evidence against the model"); b.set_ylim(-6, 7.5)
    b.legend(fontsize=5.2, loc="upper left", ncol=1, handlelength=1.6); b.grid(color=GRID, lw=0.5); panel(b, "(b)")
    K = T36.kept.to_numpy(); m = K >= 1000
    m3 = K >= 3000; c.plot(K[m3], T36.point_estimate[m3], color=INK2, lw=0.9, label="point estimate")
    c.plot(K[m], T36["F_L_p0.5"][m], color=C1, lw=1.6, label="certificate (pre-registered)")
    c.plot(K[m], T36["F_L_p130_256"][m], color=C1, lw=0.9, ls="--", label="with p = 130/256 (exploratory)")
    c.plot(K[m], T36.F_selftest[m], color=C4, lw=1.3, label="without trusting settings")
    c.axhline(0.9, color=INK2, lw=0.7, ls=":"); c.set_xscale("log"); c.set_ylim(0.5, 1.0)
    c.set_xlabel("kept pairs (Oxford record)"); c.set_ylabel("average fidelity, lower bound"); c.legend(fontsize=5.0, loc="lower right", handlelength=1.6); c.grid(color=GRID, lw=0.5); panel(c, "(c)")
    fig.tight_layout(w_pad=1.2); fig.savefig("figs/fig6_hw_oxford.pdf", bbox_inches="tight"); fig.savefig("figs/fig6_hw_oxford.png", bbox_inches="tight", dpi=150); plt.close(fig)


print(json.dumps(dict(F3=F3, F4=F4, F5={f"{k[0]}|{k[1]}": v for k, v in F5.items()}), indent=0, default=float))
