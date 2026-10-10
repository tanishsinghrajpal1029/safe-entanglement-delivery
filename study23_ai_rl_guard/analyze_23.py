"""Locked analysis for Study 23 (README_23.md). Usage: python3 analyze_23.py des_s23_psc/runs.csv"""
import sys
import numpy as np, pandas as pd

ALPHA = 0.05; NB = 4000; GUARDED = ("bg", "fg", "ag", "rg", "arg"); CELL = ["hw", "rho", "data"]


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (NB, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def gain(R, a, b, cells, rng):
    """Pooled gain in fraction of oracle (points) of arm a over arm b: mean over cells of the ratio-of-sums difference,
    with a network (paired) bootstrap inside each cell. Returns point, 95% lower bound, per-cell points."""
    pts, boots = [], []
    for c in cells:
        x = R[(R.hw == c[0]) & (R.rho == c[1]) & (R.data == c[2])]
        A = x[x.arm == a].set_index("idx").sort_index(); B = x[x.arm == b].set_index("idx").sort_index()
        qa, oa, qb, ob = A.qual.to_numpy(), A.oracle_qual.to_numpy(), B.qual.to_numpy(), B.oracle_qual.to_numpy()
        pts.append(100 * (qa.sum() / oa.sum() - qb.sum() / ob.sum()))
        I = rng.integers(0, len(qa), (NB, len(qa)))
        boots.append(100 * (qa[I].sum(1) / oa[I].sum(1) - qb[I].sum(1) / ob[I].sum(1)))
    bt = np.mean(boots, axis=0)
    return float(np.mean(pts)), float(np.quantile(bt, .05)), float(np.quantile(bt, .95)), [round(float(p), 2) for p in pts]


def main(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261016)
    print("tasks:", len(R), "(expected 3584)")
    rows = []
    for key, g in R.groupby(CELL + ["arm"]):
        d, b = g.delivered.to_numpy(), g.bad.to_numpy()
        rows.append(dict(zip(CELL + ["arm"], key), nets=len(g), delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                         boot95_pct=boot_ub(d, b, rng), frac_oracle=g.qual.sum() / g.oracle_qual.sum(),
                         paths_delivered=int(g.paths_delivered.sum()), paths_bad=int(g.paths_bad.sum()),
                         pct_paths_bad=100 * g.paths_bad.sum() / max(g.paths_delivered.sum(), 1), est_abserr=g.est_abserr.mean()))
    G = pd.DataFrame(rows); G.to_csv(path.replace("runs.csv", "s23_groups.csv"), index=False)
    pd.set_option("display.width", 250); print(G.round(4).to_string(index=False))
    corr = [(hw, 0.7, d) for hw in ("ion2020", "ionproj") for d in ("dense", "thin")]
    ind = [(hw, 0.0, d) for hw in ("ion2020", "ionproj") for d in ("dense", "thin")]

    gd = G[G.arm.isin(GUARDED)]
    h1 = (gd.r_pct <= 1).all() and (gd.boot95_pct <= 1).all() and (gd.paths_bad <= ALPHA * gd.paths_delivered).all()
    print(f"\nH1 (primary, safety) every guarded arm in all 16 cells: r <= 1%, UB <= 1%, bad paths <= 5%: {'PASS' if h1 else 'FAIL'} "
          f"(guarded bad pairs total {int(gd.bad.sum())}; max r {gd.r_pct.max():.4f}%; max UB {gd.boot95_pct.max():.4f}%)")
    p, lb, ub, cells = gain(R, "arg", "bg", corr, rng)
    print(f"H2 (primary) AI + RL + guard (arg) vs today's guarded controller (bg), correlated cells: gain >= 2 points AND 95% LB > 0: "
          f"{'PASS' if (p >= 2 and lb > 0) else 'FAIL'} (gain {p:+.2f} points, 90% CI [{lb:+.2f}, {ub:+.2f}], cells {cells})")
    p, lb, ub, cells = gain(R, "ag", "fg", corr, rng)
    print(f"H3 (primary) the AI's own value: ag vs fg (same guard type, informed prior without AI), correlated cells: 95% LB > 0: "
          f"{'PASS' if lb > 0 else 'FAIL'} (gain {p:+.2f}, 90% CI [{lb:+.2f}, {ub:+.2f}], cells {cells})")
    p, lb, ub, cells = gain(R, "ag", "fg", ind, rng)
    print(f"H4 (secondary, control) ag vs fg on INDEPENDENT links (AI mis-specified): gain within +-1 point: "
          f"{'PASS' if abs(p) <= 1 else 'FAIL'} (gain {p:+.2f}, 90% CI [{lb:+.2f}, {ub:+.2f}], cells {cells})")
    p, lb, ub, cells = gain(R, "arg", "ag", corr + ind, rng)
    print(f"H5 (secondary) RL router adds value: arg vs ag over all 8 cells, 95% LB > 0: {'PASS' if lb > 0 else 'FAIL'} "
          f"(gain {p:+.2f}, 90% CI [{lb:+.2f}, {ub:+.2f}], cells {cells})")
    p, lb, ub, cells = gain(R, "fg", "bg", corr + ind, rng)
    print(f"H6 (descriptive) informed fleet prior in the guard (fg vs bg), all cells: {p:+.2f} [{lb:+.2f}, {ub:+.2f}] cells {cells}")
    ng = G[G.arm.isin(("b", "ar"))]
    print("H6 (descriptive) no-guard arms: r % and % of paths with a bad pair:")
    print(ng.pivot_table(index=CELL, columns="arm", values=["r_pct", "pct_paths_bad", "frac_oracle"]).round(3).to_string())
    print("H6 (descriptive) fraction of oracle, all arms:")
    print(G.pivot_table(index=CELL, columns="arm", values="frac_oracle").round(4).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
