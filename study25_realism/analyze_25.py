"""Locked analysis for Study 25 (README_25.md).
Usage: python3 analyze_25.py A des_s25_psc/runs.csv     (Blocks M, K, T, C)
       python3 analyze_25.py D des_s25d_psc/runs.csv    (Block D)"""
import sys
import numpy as np, pandas as pd

ALPHA = 0.05; NB = 4000
KAP = (0.0, 0.1, 0.25, 0.5); DEC = (0.0, 0.1, 0.25, 0.5)


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (NB, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def groups(R, key, rng):
    rows = []
    for k, g in R.groupby(key):
        d, b = g.delivered.to_numpy(), g.bad.to_numpy()
        rows.append(dict(zip(key, k), nets=len(g), delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                         boot95_pct=boot_ub(d, b, rng), frac_oracle=g.qual.sum() / g.oracle_qual.sum(), paths_delivered=int(g.paths_delivered.sum()),
                         paths_bad=int(g.paths_bad.sum()), pct_paths_bad=100 * g.paths_bad.sum() / max(g.paths_delivered.sum(), 1)))
    return pd.DataFrame(rows)


def safe(G):
    return bool(len(G) > 0 and (G.r_pct <= 1).all() and (G.boot95_pct <= 1).all() and (G.paths_bad <= ALPHA * G.paths_delivered).all())


def gain(R, sel, a, b, akey, rng):
    """pooled over the cells in `sel` (list of boolean masks): mean of per-cell ratio-of-sums differences (points), paired network
    bootstrap. Returns point, 5% and 95% quantiles, per-cell points."""
    pts, boots = [], []
    for m in sel:
        x = R[m]; A = x[x[akey] == a].set_index("idx").sort_index(); B = x[x[akey] == b].set_index("idx").sort_index()
        assert (A.index == B.index).all() and len(A) > 0
        qa, oa, qb, ob = A.qual.to_numpy(), A.oracle_qual.to_numpy(), B.qual.to_numpy(), B.oracle_qual.to_numpy()
        pts.append(100 * (qa.sum() / oa.sum() - qb.sum() / ob.sum()))
        I = rng.integers(0, len(qa), (NB, len(qa))); boots.append(100 * (qa[I].sum(1) / oa[I].sum(1) - qb[I].sum(1) / ob[I].sum(1)))
    bt = np.mean(boots, axis=0)
    return float(np.mean(pts)), float(np.quantile(bt, .05)), float(np.quantile(bt, .95)), [round(float(p), 2) for p in pts]


def verdict(tag, ok, detail):
    print(f"{tag}: {'PASS' if ok else 'FAIL'} ({detail})")


def block_a(path):
    assert path.endswith("runs.csv"); R = pd.read_csv(path); rng = np.random.default_rng(20261025); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    R["blk"] = R.block.str[-1]
    print("tasks:", len(R), "(expected 5760)")
    G = groups(R, ["blk", "hw", "cfg", "arm"], rng); G.to_csv(path.replace("runs.csv", "s25_groups.csv"), index=False)
    print(G.drop(columns=["paths_delivered"]).round(4).to_string(index=False))
    # ---------------- Block M
    M = G[G.blk == "M"].copy(); M["kappa"] = M.cfg.str.extract(r"k([\d.]+)_")[0].astype(float); M["D"] = M.cfg.str.extract(r"_d([\d.]+)")[0].astype(float)
    m1 = M[(M.arm == "kg") & (M.D >= M.kappa)]
    verdict("M1 (primary) declared robustness D >= kappa keeps the guard safe: kg in all 30 cells with D >= kappa", safe(m1) and len(m1) == 30,
            f"{len(m1)} cells; bad {int(m1.bad.sum())} in {int(m1.delivered.sum())}; max r {m1.r_pct.max():.4f}%; max bad paths {m1.pct_paths_bad.max():.2f}%")
    m2 = M[(M.arm == "kg") & (M.hw == "ion2020") & (M.kappa == 0.5) & (M.D == 0.0)]
    verdict("M2 (primary, prediction) undeclared optimism breaks the per-path bound: ion2020, kappa 0.5, D 0: bad paths > 5%", bool((m2.pct_paths_bad > 5).all()) and len(m2) == 1,
            f"bad {int(m2.bad.sum())}, r {float(m2.r_pct.iloc[0]):.3f}%, bad paths {float(m2.pct_paths_bad.iloc[0]):.2f}%")
    print("M3 (descriptive) guard map, % of delivering paths with a bad pair (rows kappa, columns D), and no-guard b:")
    for hw in ("ion2020", "nv2", "siv"):
        x = M[(M.hw == hw) & (M.arm == "kg")]; print(" ", hw); print(x.pivot_table(index="kappa", columns="D", values="pct_paths_bad").round(2).to_string())
        print("   cost of declaring D at kappa 0 (fraction of oracle):", x[x.kappa == 0].set_index("D").frac_oracle.round(4).to_dict())
        y = M[(M.hw == hw) & (M.arm == "b")]; print("   b (no guard) r %:", y.set_index("kappa").r_pct.round(3).to_dict())
    # ---------------- Block K
    K = R[R.blk == "K"]; GK = G[G.blk == "K"].set_index(["hw", "arm"])
    k1 = G[(G.blk == "K") & G.arm.str.match(r"c\d+")]
    verdict("K1 (primary) campaign-informed arms safe in all 12 cells", safe(k1) and len(k1) == 12, f"bad {int(k1.bad.sum())} in {int(k1.delivered.sum())}")
    fb, fk = GK.loc[("siv", "bg"), "frac_oracle"], GK.loc[("siv", "kg"), "frac_oracle"]
    assert fk - fb > 0.01, "known-law gain over bg vanished; K2 undefined"
    rec = {k: (GK.loc[("siv", f"c{k}"), "frac_oracle"] - fb) / (fk - fb) for k in (16, 64, 256, 1024)}
    verdict("K2 (primary, Prop. 3) SiV: every campaign with I >= 3 (K = 64, 256, 1024) recovers >= 80% of the known-law gain over bg",
            all(rec[k] >= 0.8 for k in (64, 256, 1024)), "recovered fraction " + ", ".join(f"K{k}: {v:.3f}" for k, v in rec.items()) + f"; kg - bg = {100 * (fk - fb):.2f} points")
    C = K[K.arm.str.match(r"c\d+")]
    print("K3 (descriptive) campaign estimates: mean F0 error and spread ratio by hw and K:")
    print(C.groupby(["hw", "arm"])[["camp_muF_err", "camp_sdF_ratio"]].agg(["mean", "std"]).round(4).to_string())
    for hw in ("ion2020", "nv2"):
        print(f"   {hw} fraction of oracle:", {a: round(float(GK.loc[(hw, a), 'frac_oracle']), 4) for a in ("bg", "kg", "c16", "c64", "c256", "c1024")})
    # ---------------- Block T
    T = G[G.blk == "T"]
    t1 = T[T.cfg.isin(["c0.0", "c0.5"])]
    verdict("T1 (primary) all six arms safe without strong shared noise (c in {0, 0.5}; 36 cells)", safe(t1) and len(t1) == 36, f"bad {int(t1.bad.sum())}")
    t2 = T[T.arm.isin(["kgphi", "ag2phi"])]
    verdict("T2 (primary) declaring the over-dispersion restores safety: kgphi, ag2phi in all 18 cells", safe(t2) and len(t2) == 18,
            f"bad {int(t2.bad.sum())} in {int(t2.delivered.sum())}; max bad paths {t2.pct_paths_bad.max():.2f}%")
    t3 = T[T.cfg == "c2.0"].set_index(["hw", "arm"]); ok3 = True; det = []
    for hw in ("ion2020", "nv2", "siv"):
        k = t3.loc[(hw, "kg"), "pct_paths_bad"]; a = t3.loc[(hw, "ag2"), "pct_paths_bad"]; s = t3.loc[(hw, "ag2t"), "pct_paths_bad"]
        ok3 &= (a <= k + 2) and (s <= k + 2); det.append(f"{hw}: kg {k:.2f}, ag2 {a:.2f}, ag2t {s:.2f}")
    verdict("T3 (secondary, Prop. 10) under strong shared noise (c = 2) the AI prior adds no failures beyond the known-law guard: % bad paths of ag2 and ag2t <= kg + 2 points, every hw", ok3, "; ".join(det))
    print("T4 (descriptive) fraction of oracle by noise level:")
    print(T.pivot_table(index=["hw", "cfg"], columns="arm", values="frac_oracle").round(4).to_string())
    print("   bad pairs:"); print(T.pivot_table(index=["hw", "cfg"], columns="arm", values="bad").to_string())
    # ---------------- Block C
    Cg = G[G.blk == "C"]
    verdict("C1 (primary) bg, kg, ag2 safe in all 48 network-model cells", safe(Cg) and len(Cg) == 48, f"bad {int(Cg.bad.sum())} in {int(Cg.delivered.sum())}")
    RC = R[R.blk == "C"]
    sel = [(RC.hw == hw) & (RC.cfg == "par4") for hw in ("nv2", "siv")]
    p, lb, ub, cells = gain(RC, sel, "ag2", "bg", "arm", rng)
    verdict("C2 (secondary) the thin-hardware gain survives parallel load and 50 km/hop signalling: ag2 - bg, NV and SiV, par4: >= 10 points AND LB > 0",
            p >= 10 and lb > 0, f"gain {p:+.2f} points, 90% CI [{lb:+.2f}, {ub:+.2f}], cells {cells}")
    print("C3 (descriptive) fraction of oracle and mean end-to-end latency (s) by condition:")
    print(Cg.pivot_table(index=["hw", "cfg"], columns="arm", values="frac_oracle").round(4).to_string())
    L = RC[RC.delivered > 0].assign(w=lambda d: d.lat_e2e_mean * d.delivered).groupby(["hw", "cfg", "arm"]).agg(w=("w", "sum"), n=("delivered", "sum"))
    print((L.w / L.n).unstack("arm").round(4).to_string())


def block_d(path):
    assert path.endswith("runs.csv"); R = pd.read_csv(path); rng = np.random.default_rng(20261026); pd.set_option("display.width", 250)
    print("tasks:", len(R), "(expected 3456)")
    G = groups(R, ["hw", "scen", "ctrl"], rng); G.to_csv(path.replace("runs.csv", "s25d_groups.csv"), index=False)
    print(G.pivot_table(index=["hw", "scen"], columns="ctrl", values="frac_oracle").round(4).to_string())
    print(G.pivot_table(index=["hw", "scen"], columns="ctrl", values="bad").to_string())
    sdj = {"D": 0.0, "Dj": 0.005 * np.sqrt(2), "Djb": 0.02 * np.sqrt(2)}
    gb = G[G.ctrl.str.startswith("gb")].copy(); gb["B"] = gb.ctrl.str[2:].astype(float)
    d1 = gb[gb.apply(lambda r: r.B >= 3 * sdj[r.scen], axis=1)]
    verdict("D1 (primary) the declared-bound guard is safe whenever B >= 3 sd of the true re-alignment jump (20 cells)", safe(d1) and len(d1) == 20,
            f"{len(d1)} cells; bad {int(d1.bad.sum())} in {int(d1.delivered.sum())}")
    Gi = G.set_index(["hw", "scen", "ctrl"]); rec = {}
    for hw in ("ion2020", "ionproj"):
        e, p_, g = (Gi.loc[(hw, "D", c), "frac_oracle"] for c in ("gexact", "gpersist", "gb0.005"))
        assert p_ - e > 0.01, "gexact -> gpersist gap vanished; D2 undefined"
        rec[hw] = (g - e) / (p_ - e)
    verdict("D2 (primary, design curve) with exact re-alignment, a declared B = 0.005 recovers >= 40% of the gexact -> gpersist gap, both hw",
            all(v >= 0.4 for v in rec.values()), ", ".join(f"{k}: {v:.3f}" for k, v in rec.items()))
    d3 = G[(G.scen == "Djb") & (G.ctrl == "gb0.005")]
    print(f"D3 (secondary, prediction) a broken promise (Djb, B = 0.005) produces bad pairs on both hw: {'CONFIRMED' if (d3.bad > 0).all() and len(d3) == 2 else 'NOT CONFIRMED'} (bad {d3.bad.tolist()}, % bad paths {d3.pct_paths_bad.round(2).tolist()})")
    print("D4 (descriptive) promise check per network: bad pairs in networks whose realised max jump <= B, by cell:")
    gbr = R[R.ctrl.str.startswith("gb")].copy(); gbr["B"] = gbr.ctrl.str[2:].astype(float); kept = gbr[gbr.max_jump <= gbr.B]
    print(kept.groupby(["hw", "scen", "ctrl"]).agg(nets=("idx", "size"), bad=("bad", "sum"), delivered=("delivered", "sum")).to_string())


if __name__ == "__main__":
    {"A": block_a, "D": block_d}[sys.argv[1]](sys.argv[2])
