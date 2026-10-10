"""Locked analysis for Study 24 (README_24.md).
Usage: python3 analyze_24.py A des_s24_psc/runs.csv      (Block A)
       python3 analyze_24.py B des_s24b_psc/runs.csv     (Block B)"""
import sys
import numpy as np, pandas as pd

ALPHA = 0.05; NB = 4000
HWS = ("ion2020", "ionproj", "ionfut", "nv2", "siv"); THIN = ("nv2", "siv")
PATS = ("ind", "field", "short", "region", "outlier"); CORR = ("field", "short", "region", "outlier"); UNSEEN = ("short", "region", "outlier")
GUARDED = ("bg", "fg", "kg", "ag1", "lg", "ag2")
LAT_BINS = np.r_[0.0, np.logspace(-3, 4, 141)]


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (NB, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def gain(R, a, b, cells, ckey, akey, rng):
    """Pooled gain (points of fraction of oracle) of arm a over arm b: mean over cells of the per-cell ratio-of-sums difference;
    paired network bootstrap inside each cell. Returns point, 5% and 95% bootstrap quantiles, per-cell points."""
    pts, boots = [], []
    for c in cells:
        x = R[(R[ckey[0]] == c[0]) & (R[ckey[1]] == c[1])]
        A = x[x[akey] == a].set_index("idx").sort_index(); B = x[x[akey] == b].set_index("idx").sort_index()
        assert (A.index == B.index).all()
        qa, oa, qb, ob = A.qual.to_numpy(), A.oracle_qual.to_numpy(), B.qual.to_numpy(), B.oracle_qual.to_numpy()
        pts.append(100 * (qa.sum() / oa.sum() - qb.sum() / ob.sum()))
        I = rng.integers(0, len(qa), (NB, len(qa)))
        boots.append(100 * (qa[I].sum(1) / oa[I].sum(1) - qb[I].sum(1) / ob[I].sum(1)))
    bt = np.mean(boots, axis=0)
    return float(np.mean(pts)), float(np.quantile(bt, .05)), float(np.quantile(bt, .95)), [round(float(p), 2) for p in pts]


def groups(R, cell, akey, rng):
    rows = []
    for key, g in R.groupby(cell + [akey]):
        d, b = g.delivered.to_numpy(), g.bad.to_numpy()
        rows.append(dict(zip(cell + [akey], key), nets=len(g), delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                         boot95_pct=boot_ub(d, b, rng), frac_oracle=g.qual.sum() / g.oracle_qual.sum(),
                         paths_delivered=int(g.paths_delivered.sum()), paths_bad=int(g.paths_bad.sum()),
                         pct_paths_bad=100 * g.paths_bad.sum() / max(g.paths_delivered.sum(), 1)))
    return pd.DataFrame(rows)


def safe(G):
    return bool((G.r_pct <= 1).all() and (G.boot95_pct <= 1).all() and (G.paths_bad <= ALPHA * G.paths_delivered).all())


def pooled_pct(hists, q):
    h = np.sum([np.array([int(v) for v in s.split(";")]) for s in hists], axis=0)
    if h.sum() == 0: return np.nan
    c = np.cumsum(h) / h.sum(); i = int(np.searchsorted(c, q / 100)); return float(LAT_BINS[i + 1])     # upper edge of the bin


def show(tag, ok, p, lb, ub, cells, extra=""):
    print(f"{tag}: {'PASS' if ok else 'FAIL'} (gain {p:+.2f} points, 90% CI [{lb:+.2f}, {ub:+.2f}]{extra}, cells {cells})")


def block_a(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261024); pd.set_option("display.width", 250)
    print("tasks:", len(R), "(expected 11200)")
    G = groups(R, ["hw", "pat"], "arm", rng); G.to_csv(path.replace("runs.csv", "s24_groups.csv"), index=False)
    print(G.pivot_table(index=["hw", "pat"], columns="arm", values="frac_oracle").round(4).to_string())
    gd = G[G.arm.isin(GUARDED)]
    print(f"\nH1 (primary, safety) every guarded arm {GUARDED} in all 25 cells: r <= 1%, UB <= 1%, bad paths <= 5%: "
          f"{'PASS' if safe(gd) else 'FAIL'} (guarded bad pairs {int(gd.bad.sum())} in {int(gd.delivered.sum())} deliveries; "
          f"max r {gd.r_pct.max():.4f}%; max UB {gd.boot95_pct.max():.4f}%; max bad paths {gd.pct_paths_bad.max():.3f}%)")
    ck = ("hw", "pat")
    c_thin = [(h, p) for h in THIN for p in PATS]; c_thin_corr = [(h, p) for h in THIN for p in CORR]
    c_unseen = [(h, p) for h in HWS for p in UNSEEN]; c_ind = [(h, "ind") for h in HWS]
    c_all = [(h, p) for h in HWS for p in PATS]; c_corr = [(h, p) for h in HWS for p in CORR]
    p, lb, ub, cl = gain(R, "ag2", "bg", c_thin, ck, "arm", rng); show("H2 (primary) thin hardware rescued: ag2 - bg over NV and SiV (10 cells) >= 10 points AND LB > 0", p >= 10 and lb > 0, p, lb, ub, cl)
    p, lb, ub, cl = gain(R, "ag2", "kg", c_thin_corr, ck, "arm", rng); show("H3 (primary) the AI's own value: ag2 - kg, NV and SiV, correlated patterns (8 cells), LB > 0", lb > 0, p, lb, ub, cl)
    p, lb, ub, cl = gain(R, "ag2", "kg", c_unseen, ck, "arm", rng); show("H4 (primary) patterns never seen in training: ag2 - kg, short/region/outlier x 5 hw (15 cells), LB > 0", lb > 0, p, lb, ub, cl)
    p, lb, ub, cl = gain(R, "ag2", "kg", c_ind, ck, "arm", rng); show("H5 (secondary) no harm on independent links: ag2 - kg, ind x 5 hw, LB > -1", lb > -1, p, lb, ub, cl)
    p, lb, ub, cl = gain(R, "ag2", "ag1", c_all, ck, "arm", rng); show("H6 (secondary) AI v2 better than AI v1: ag2 - ag1, all 25 cells, LB > 0", lb > 0, p, lb, ub, cl)
    p, lb, ub, cl = gain(R, "ag2", "lg", c_corr, ck, "arm", rng); show("H7 (secondary) neural net needed: ag2 - lg, correlated patterns x 5 hw (20 cells), LB > 0", lb > 0, p, lb, ub, cl)
    print("\nH8 (descriptive) pooled gains [90% CI] per hardware:")
    for a, b in (("fg", "bg"), ("kg", "fg"), ("ag2", "kg"), ("ag2", "bg"), ("ag1", "kg"), ("lg", "kg")):
        for h in HWS:
            p, lb, ub, cl = gain(R, a, b, [(h, x) for x in PATS], ck, "arm", rng)
            print(f"  {a}-{b} {h:8s} {p:+6.2f} [{lb:+6.2f}, {ub:+6.2f}] cells {cl}")
    ng = G[G.arm == "b"]
    print("H8 (descriptive) no guard (b): r % and % of paths with a bad pair:")
    print(ng.pivot_table(index="hw", columns="pat", values=["r_pct", "pct_paths_bad"]).round(3).to_string())
    print("\nLAT (descriptive, pre-registered reporting) end-to-end latency of delivered requests, seconds, pooled over networks:")
    rows = []
    for (h, a), g in R.groupby(["hw", "arm"]):
        w = g.delivered.clip(lower=0)
        rows.append(dict(hw=h, arm=a, p50=pooled_pct(g.lat_e2e_hist, 50), p95=pooled_pct(g.lat_e2e_hist, 95), p99=pooled_pct(g.lat_e2e_hist, 99),
                         mean=float((g.lat_e2e_mean.clip(lower=0) * w).sum() / max(w.sum(), 1)),
                         queue=float((g.lat_queue_mean.clip(lower=0) * w).sum() / max(w.sum(), 1)),
                         service=float((g.lat_svc_mean.clip(lower=0) * w).sum() / max(w.sum(), 1)),
                         attempts=float((g.lat_att_mean.clip(lower=0) * w).sum() / max(w.sum(), 1)),
                         hold=float((g.lat_hold_mean.clip(lower=0) * w).sum() / max(w.sum(), 1)),
                         oracle_service_p50=pooled_pct(g.lat_osvc_hist, 50), served_pct=100 * g.delivered.sum() / max(g.requests.sum(), 1)))
    Lt = pd.DataFrame(rows); Lt.to_csv(path.replace("runs.csv", "s24_latency.csv"), index=False)
    print(Lt.round(4).to_string(index=False))


def block_b(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261025); pd.set_option("display.width", 250)
    print("tasks:", len(R), "(expected 1536)")
    G = groups(R, ["hw", "scen"], "ctrl", rng); G.to_csv(path.replace("runs.csv", "s24b_groups.csv"), index=False)
    print(G.pivot_table(index=["hw", "scen"], columns="ctrl", values="frac_oracle").round(4).to_string())
    gc = G[G.ctrl == "gcarry"]
    print(f"\nB1 (primary, safety) gcarry in all 6 cells (D, Dj, Djb x 2 hw): r <= 1%, UB <= 1%, bad paths <= 5%: {'PASS' if safe(gc) else 'FAIL'} "
          f"(bad pairs {int(gc.bad.sum())} in {int(gc.delivered.sum())})")
    cells = [(h, s) for h in ("ion2020", "ionproj") for s in ("D", "Dj", "Djb")]
    p, lb, ub, cl = gain(R, "gcarry", "gexact", cells, ("hw", "scen"), "ctrl", rng)
    show("B2 (primary, Prop. 7 prediction) carrying the previous cycle buys little: gcarry - gexact, 90% CI inside [-2, +2]", lb > -2 and ub < 2, p, lb, ub, cl)
    gp = G[(G.ctrl == "gpersist") & (G.scen != "D")]
    print(f"B3 (secondary, replication of G5) gpersist delivers bad pairs whenever re-alignment jitters (all 4 Dj/Djb cells bad > 0): "
          f"{'CONFIRMED' if (gp.bad > 0).all() else 'NOT CONFIRMED'} (bad {gp.bad.tolist()}, r % {gp.r_pct.round(4).tolist()})")
    ge = G[G.ctrl == "gexact"]
    print(f"B4 (descriptive) gexact safe in all 6 cells: {safe(ge)} (bad {int(ge.bad.sum())}); cost vs no guard (cal) per cell:")
    for c in cells:
        p, lb, ub, cl = gain(R, "gexact", "cal", [c], ("hw", "scen"), "ctrl", rng); q, *_ = gain(R, "gcarry", "cal", [c], ("hw", "scen"), "ctrl", rng)
        print(f"  {c}: gexact {p:+.2f}, gcarry {q:+.2f} points vs cal")


if __name__ == "__main__":
    {"A": block_a, "B": block_b}[sys.argv[1]](sys.argv[2])
