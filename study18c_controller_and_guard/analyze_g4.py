"""Locked analysis for Study 18C G4 (README_G4.md). Usage: python3 analyze_g4.py des_g4_psc/runs.csv"""
import sys
import numpy as np, pandas as pd

KEYS = ["hw", "scen", "ctrl"]; MIND = 200; ALPHA = 0.05


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (4000, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def main(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261012); rows = []
    print("tasks:", len(R), "(expected 1152)")
    for key, g in R.groupby(KEYS):
        d, b = g.delivered.to_numpy(), g.bad.to_numpy()
        rows.append(dict(zip(KEYS, key), nets=len(g), delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                         boot95_pct=boot_ub(d, b, rng), frac_oracle=g.qual.sum() / max(g.oracle_qual.sum(), 1),
                         paths_delivered=int(g.paths_delivered.sum()), paths_bad=int(g.paths_bad.sum()),
                         pct_paths_bad=100 * g.paths_bad.sum() / max(g.paths_delivered.sum(), 1), max_path_bad=int(g.max_path_bad.max()),
                         guard_blocks=int(g.guard_blocks.sum())))
    G = pd.DataFrame(rows); G.to_csv(path.replace("runs.csv", "g4_groups.csv"), index=False)
    pd.set_option("display.width", 220); print(G.round(4).to_string(index=False))

    def grp(scen, ctrl): return G[(G.scen == scen) & (G.ctrl == ctrl)]

    def safe(x): return len(x) == 2 and (x.delivered >= MIND).all() and (x.r_pct <= 1).all() and (x.boot95_pct <= 1).all() and \
        x.paths_bad.sum() <= ALPHA * x.paths_delivered.sum()

    gd, gn, gm, gr = grp("D", "gdrift"), grp("D", "gnaive"), grp("M", "gnom"), grp("M", "grobust")
    print(f"\nH1 (primary, drift) gdrift: r <= 1%, UB <= 1% in both hw, bad paths <= 5%: {'PASS' if safe(gd) else 'FAIL'} "
          f"(r max {gd.r_pct.max():.4f}%, UB max {gd.boot95_pct.max():.4f}%, bad paths {int(gd.paths_bad.sum())}/{int(gd.paths_delivered.sum())})")
    print(f"H2 (prediction: naive guard breaks under drift) gnaive delivers bad pairs (bad > 0 in >= 1 hw): "
          f"{'CONFIRMED' if (gn.bad > 0).any() else 'NOT CONFIRMED'} (bad {gn.bad.tolist()}, bad paths {gn.paths_bad.tolist()})")
    print(f"H3 (open question; no guarantee) nominal guard under 25% optimistic model error delivers bad pairs: "
          f"{'YES' if (gm.bad > 0).any() else 'NO'} (bad {gm.bad.tolist()}, r {gm.r_pct.round(4).tolist()}, bad paths {gm.paths_bad.tolist()})")
    print(f"H4 (primary, model error) grobust: r <= 1%, UB <= 1% in both hw, bad paths <= 5%: {'PASS' if safe(gr) else 'FAIL'} "
          f"(r max {gr.r_pct.max():.4f}%, UB max {gr.boot95_pct.max():.4f}%, bad paths {int(gr.paths_bad.sum())}/{int(gr.paths_delivered.sum())})")
    g5n, g5r = grp("M50", "gnom"), grp("M50", "grobust")
    print(f"H6 (open question; declared set does NOT cover the truth) M50: gnom bad {g5n.bad.tolist()} r {g5n.r_pct.round(4).tolist()}; "
          f"grobust bad {g5r.bad.tolist()} r {g5r.r_pct.round(4).tolist()}; bad paths gnom {g5n.paths_bad.tolist()} grobust {g5r.paths_bad.tolist()}")
    print("H5 (descriptive) throughput (fraction of oracle) and risk per scenario:")
    print(G.pivot_table(index=["scen", "hw"], columns="ctrl", values=["frac_oracle", "r_pct", "pct_paths_bad"]).round(4).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
