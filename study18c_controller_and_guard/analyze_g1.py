"""Locked analysis for Study 18C G1 (pre-registered in README_G1.md). Usage: python3 analyze_g1.py des_g1_psc/runs.csv"""
import sys
import numpy as np, pandas as pd

KEYS = ["block", "hw", "topo", "k", "ctrl", "route"]; B = 2000; MIND = 200


def boot_ub(g, rng):
    d = g.delivered.to_numpy(); b = g.bad.to_numpy(); n = len(g); r = []
    for _ in range(B):
        i = rng.integers(0, n, n); D = d[i].sum(); r.append(b[i].sum() / D if D else 0.0)
    return 100 * float(np.quantile(r, 0.95))


def main(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261008); rows = []
    for key, g in R.groupby(KEYS):
        D, Bd = int(g.delivered.sum()), int(g.bad.sum())
        rows.append(dict(zip(KEYS, key), nets=len(g), delivered=D, bad=Bd, r_pct=100 * Bd / D if D else np.nan,
                         boot95_pct=boot_ub(g, rng) if D else np.nan, frac_oracle=g.qual.sum() / max(g.oracle_qual.sum(), 1),
                         sel_bias=float((g.sel_bias * g.nsel).sum() / max(g.nsel.sum(), 1)), top_net_bad=int(g.bad.max())))
    G = pd.DataFrame(rows); G.to_csv(path.replace("runs.csv", "g1_groups.csv"), index=False)
    pd.set_option("display.width", 200); print(G.round(4).to_string(index=False))
    cal = G[(G.ctrl == "cal") & (G.delivered >= MIND)]; flat = G[(G.ctrl == "flat") & (G.delivered >= MIND)]
    print(f"\nH1 (primary) cal: r <= 1% in every tested group: {'PASS' if (cal.r_pct <= 1).all() else 'FAIL'} "
          f"({int((cal.r_pct <= 1).sum())}/{len(cal)} groups; max {cal.r_pct.max():.3f}%); untested (<{MIND} deliveries): "
          f"{int(((G.ctrl == 'cal') & (G.delivered < MIND)).sum())}")
    print(f"H1b cal: bootstrap 95% UB <= 1% in every tested group: {'PASS' if (cal.boot95_pct <= 1).all() else 'FAIL'} (max {cal.boot95_pct.max():.3f}%)")
    K = G[G.block == "K"]
    def get(hw, k, c, col): x = K[(K.hw == hw) & (K.k == k) & (K.ctrl == c)][col]; return float(x.iloc[0]) if len(x) else np.nan
    h2 = []; h3 = []
    for hw in ("nv", "ion2020"):
        fb1, fb8, cb8 = get(hw, 1, "flat", "sel_bias"), get(hw, 8, "flat", "sel_bias"), get(hw, 8, "cal", "sel_bias")
        h2.append(fb8 > fb1 and cb8 <= 0); print(f"H2 {hw}: flat sel_bias k1 {fb1:+.4f} -> k8 {fb8:+.4f}; cal k8 {cb8:+.4f}")
        r1, r8 = get(hw, 1, "flat", "r_pct"), get(hw, 8, "flat", "r_pct"); h3.append(r8 > r1)
        print(f"H3 {hw}: flat r k1 {r1:.3f}% -> k8 {r8:.3f}%; cal r k1 {get(hw, 1, 'cal', 'r_pct'):.3f}% -> k8 {get(hw, 8, 'cal', 'r_pct'):.3f}%")
    print(f"H2 (mechanism: winner's curse for flat, none for cal): {'CONFIRMED' if all(h2) else 'NOT CONFIRMED'}")
    print(f"H3 (selection raises flat risk, k1 -> k8, both hw): {'CONFIRMED' if all(h3) else 'NOT CONFIRMED'}")
    Gg = G[G.block == "G"]
    for hw in ("ion2020", "ionproj"):
        for c in ("cal", "flat"):
            x = Gg[(Gg.hw == hw) & (Gg.ctrl == c)].set_index("route")
            if {"random", "best"} <= set(x.index):
                print(f"H4 grid {hw} {c}: r random {x.r_pct['random']:.3f}% best {x.r_pct['best']:.3f}%; "
                      f"frac_oracle random {x.frac_oracle['random']:.3f} best {x.frac_oracle['best']:.3f}")


if __name__ == "__main__":
    main(sys.argv[1])
