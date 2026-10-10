"""Locked analysis for Study 18C G3 (README_G3.md). Usage: python3 analyze_g3.py des_g3_psc/runs.csv"""
import sys
import numpy as np, pandas as pd

KEYS = ["hw", "ctrl", "fleet"]; MIND = 200; ALPHA = 0.05


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (4000, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def main(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261011); rows = []
    print("tasks:", len(R), "(expected 256)")
    for key, g in R.groupby(KEYS):
        d, b = g.delivered.to_numpy(), g.bad.to_numpy()
        rows.append(dict(zip(KEYS, key), nets=len(g), delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                         boot95_pct=boot_ub(d, b, rng), frac_oracle=g.qual.sum() / max(g.oracle_qual.sum(), 1),
                         paths_delivered=int(g.paths_delivered.sum()), paths_bad=int(g.paths_bad.sum()),
                         pct_paths_bad=100 * g.paths_bad.sum() / max(g.paths_delivered.sum(), 1), max_path_bad=int(g.max_path_bad.max()),
                         s_hat_over_true=float((g.s_hat / g.s_true).mean()), guard_blocks=int(g.guard_blocks.sum())))
    G = pd.DataFrame(rows); G.to_csv(path.replace("runs.csv", "g3_groups.csv"), index=False)
    pd.set_option("display.width", 220); print(G.round(4).to_string(index=False))
    cg = G[(G.ctrl == "calg") & (G.delivered >= MIND)]; ca = G[(G.ctrl == "cal") & (G.delivered >= MIND)]
    print(f"\nH1 (primary) calg r <= 1% in every group: {'PASS' if (cg.r_pct <= 1).all() and len(cg) == 4 else 'FAIL'} "
          f"({int((cg.r_pct <= 1).sum())}/4; max {cg.r_pct.max():.4f}%)")
    print(f"H1b calg network-bootstrap 95% UB <= 1% in every group: {'PASS' if (cg.boot95_pct <= 1).all() and len(cg) == 4 else 'FAIL'} (max {cg.boot95_pct.max():.4f}%)")
    pdl, pbd = int(G[G.ctrl == "calg"].paths_delivered.sum()), int(G[G.ctrl == "calg"].paths_bad.sum())
    print(f"H2 (Prop. 6) calg bad paths / delivering paths = {pbd}/{pdl} = {100 * pbd / max(pdl, 1):.3f}% (bar <= 5%): {'PASS' if pbd <= ALPHA * pdl else 'FAIL'}")
    print(f"H3 cal pooled r <= 1% in every group: {'PASS' if (ca.r_pct <= 1).all() and len(ca) == 4 else 'FAIL'} "
          f"({int((ca.r_pct <= 1).sum())}/4; max {ca.r_pct.max():.4f}%; max UB {ca.boot95_pct.max():.4f}%)")
    print("H4 (descriptive) own vs ext fleet prior:")
    print(G.pivot_table(index=["hw", "ctrl"], columns="fleet", values=["r_pct", "frac_oracle", "s_hat_over_true", "pct_paths_bad"]).round(4).to_string())
    print("H5 (descriptive) cost of the guard (frac_oracle calg / cal):")
    print(G.pivot_table(index=["hw", "fleet"], columns="ctrl", values="frac_oracle").round(4).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
