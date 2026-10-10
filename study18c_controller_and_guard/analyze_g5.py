"""Locked analysis for Study 18C G5 (README_G5.md). Usage: python3 analyze_g5.py des_g5_psc/runs.csv"""
import sys
import numpy as np, pandas as pd

KEYS = ["hw", "scen", "ctrl"]; MIND = 200; ALPHA = 0.05; NB = 4000


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (NB, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def paired_gain(a, b, rng):
    """a, b: DataFrames for two controllers on the same networks. Returns (point, 95% lower bound) of
    frac_oracle(a) - frac_oracle(b), network (paired) bootstrap."""
    m = a.merge(b, on="idx", suffixes=("_a", "_b")); qa, oa, qb, ob = (m[c].to_numpy() for c in ("qual_a", "oracle_qual_a", "qual_b", "oracle_qual_b"))
    pt = qa.sum() / max(oa.sum(), 1) - qb.sum() / max(ob.sum(), 1)
    I = rng.integers(0, len(m), (NB, len(m)))
    bs = qa[I].sum(1) / np.maximum(oa[I].sum(1), 1) - qb[I].sum(1) / np.maximum(ob[I].sum(1), 1)
    return float(pt), float(np.quantile(bs, .05))


def main(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261013); rows = []
    print("tasks:", len(R), "(expected 1024)")
    for key, g in R.groupby(KEYS):
        d, b = g.delivered.to_numpy(), g.bad.to_numpy()
        rows.append(dict(zip(KEYS, key), nets=len(g), delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                         boot95_pct=boot_ub(d, b, rng), frac_oracle=g.qual.sum() / max(g.oracle_qual.sum(), 1),
                         paths_delivered=int(g.paths_delivered.sum()), paths_bad=int(g.paths_bad.sum()),
                         pct_paths_bad=100 * g.paths_bad.sum() / max(g.paths_delivered.sum(), 1), max_path_bad=int(g.max_path_bad.max()),
                         guard_blocks=int(g.guard_blocks.sum())))
    G = pd.DataFrame(rows); G.to_csv(path.replace("runs.csv", "g5_groups.csv"), index=False)
    pd.set_option("display.width", 220); print(G.round(4).to_string(index=False))

    def grp(scen, ctrl): return G[(G.scen == scen) & (G.ctrl == ctrl)]

    def safe(x, n): return len(x) == n and (x.delivered >= MIND).all() and (x.r_pct <= 1).all() and (x.boot95_pct <= 1).all() and \
        (x.paths_bad <= ALPHA * x.paths_delivered).all()

    ge = G[G.ctrl == "gexact"]
    print(f"\nH1 (primary, safety) gexact under D and Dj, both hw: r <= 1%, UB <= 1%, bad paths <= 5% in each of 4 groups: "
          f"{'PASS' if safe(ge, 4) else 'FAIL'} (bad {ge.bad.tolist()}, r max {ge.r_pct.max():.4f}%, UB max {ge.boot95_pct.max():.4f}%, "
          f"bad paths {int(ge.paths_bad.sum())}/{int(ge.paths_delivered.sum())})")
    h2 = []
    for hw in ("ion2020", "ionproj"):
        for scen in ("D", "Dj"):
            a = R[(R.hw == hw) & (R.scen == scen) & (R.ctrl == "gexact")]; b = R[(R.hw == hw) & (R.scen == scen) & (R.ctrl == "gdrift")]
            pt, lb = paired_gain(a, b, rng); h2.append((hw, scen, pt, lb))
    ok2 = all(lb > 0 for *_, lb in h2)
    print(f"H2 (primary, cost) gexact keeps more of oracle than gdrift in all 4 cells (paired-bootstrap 95% lower bound of the gain > 0): "
          f"{'PASS' if ok2 else 'FAIL'}")
    for hw, scen, pt, lb in h2: print(f"    {hw:8s} {scen:3s} gain {pt:+.4f} (95% LB {lb:+.4f})")
    gp = grp("D", "gpersist"); h3s = safe(gp, 2); h3t = []
    for hw in ("ion2020", "ionproj"):
        a = R[(R.hw == hw) & (R.scen == "D") & (R.ctrl == "gpersist")]; b = R[(R.hw == hw) & (R.scen == "D") & (R.ctrl == "gexact")]
        h3t.append((hw,) + paired_gain(a, b, rng))
    print(f"H3 (secondary) gpersist under D: safe (as H1) {'PASS' if h3s else 'FAIL'}; frac_oracle >= gexact (point gain >= 0) in both hw "
          f"{'PASS' if all(pt >= 0 for _, pt, _ in h3t) else 'FAIL'}")
    for hw, pt, lb in h3t: print(f"    {hw:8s} gpersist - gexact {pt:+.4f} (95% LB {lb:+.4f})")
    gj = grp("Dj", "gpersist")
    print(f"H4 (open; assumption violated) gpersist under Dj: bad {gj.bad.tolist()}, r {gj.r_pct.round(4).tolist()}, "
          f"UB {gj.boot95_pct.round(4).tolist()}, bad paths {gj.paths_bad.tolist()}/{gj.paths_delivered.tolist()}")
    print("H5 (descriptive) fraction of oracle, risk and bad-path share:")
    print(G.pivot_table(index=["scen", "hw"], columns="ctrl", values=["frac_oracle", "r_pct", "pct_paths_bad"]).round(4).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
