"""Locked analysis for Study 18C G2 (README_G2.md). Usage: python3 analyze_g2.py des_g2_psc/runs.csv"""
import sys
import numpy as np, pandas as pd

KEYS = ["block", "hw", "topo", "k", "ctrl", "route"]; MIND = 200; ALPHA = 0.05


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (4000, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def main(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261009); rows = []
    for key, g in R.groupby(KEYS):
        d, b = g.delivered.to_numpy(), g.bad.to_numpy()
        rows.append(dict(zip(KEYS, key), nets=len(g), delivered=int(d.sum()), bad=int(b.sum()),
                         r_pct=100 * b.sum() / max(d.sum(), 1), boot95_pct=boot_ub(d, b, rng),
                         frac_oracle=g.qual.sum() / max(g.oracle_qual.sum(), 1), paths_delivered=int(g.paths_delivered.sum()),
                         paths_bad=int(g.paths_bad.sum()), max_path_bad=int(g.max_path_bad.max()), guard_blocks=int(g.guard_blocks.sum())))
    G = pd.DataFrame(rows); G.to_csv(path.replace("runs.csv", "g2_groups.csv"), index=False)
    pd.set_option("display.width", 220); print(G.round(4).to_string(index=False))
    cg = G[(G.ctrl == "calg") & (G.delivered >= MIND)]; ca = G[(G.ctrl == "cal") & (G.delivered >= MIND)]
    print(f"\nH1 (primary) calg r <= 1% in every tested group: {'PASS' if (cg.r_pct <= 1).all() else 'FAIL'} "
          f"({int((cg.r_pct <= 1).sum())}/{len(cg)}; max {cg.r_pct.max():.3f}%); untested: {int(((G.ctrl == 'calg') & (G.delivered < MIND)).sum())}")
    print(f"H1b calg network-bootstrap 95% UB <= 1% in every tested group: {'PASS' if (cg.boot95_pct <= 1).all() else 'FAIL'} (max {cg.boot95_pct.max():.3f}%)")
    pdl, pbd = int(G[G.ctrl == "calg"].paths_delivered.sum()), int(G[G.ctrl == "calg"].paths_bad.sum())
    print(f"H2 (per-path guarantee) calg: paths with >= 1 bad delivery / paths with >= 1 delivery = {pbd}/{pdl} = "
          f"{100 * pbd / max(pdl, 1):.2f}% (bar <= {100 * ALPHA:.0f}%): {'PASS' if pbd <= ALPHA * pdl else 'FAIL'}")
    cpd, cpb = int(G[G.ctrl == "cal"].paths_delivered.sum()), int(G[G.ctrl == "cal"].paths_bad.sum())
    print(f"     (cal, for comparison: {cpb}/{cpd} = {100 * cpb / max(cpd, 1):.2f}%)")
    m = G.pivot_table(index=["block", "hw", "topo", "k", "route"], columns="ctrl", values=["frac_oracle", "r_pct", "boot95_pct"])
    print("\nH3 (descriptive) cost of the guard: frac_oracle calg / cal, and risk, per group")
    print(m.round(4).to_string())
    print(f"\nH4 (descriptive) cal replication of G1 on fresh seeds: max r {ca.r_pct.max():.3f}%, groups > 1%: "
          f"{int((ca.r_pct > 1).sum())}/{len(ca)}; max UB {ca.boot95_pct.max():.3f}%")


if __name__ == "__main__":
    main(sys.argv[1])
