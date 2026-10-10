"""Locked analysis for Study 18C G7 (README_G7.md). Usage: python3 analyze_g7.py des_g7_psc/runs.csv"""
import sys
import numpy as np, pandas as pd

KEYS = ["hw", "scen", "ctrl"]; ALPHA = 0.05; NB = 4000
SUM = ["delivered", "bad", "qual", "oracle_qual", "post_delivered", "post_bad", "post_bad_early", "post_bad_late", "prefault_bad",
       "paths_delivered", "paths_bad", "n_faulted", "detected", "alarms_true", "alarms_false", "guard_blocks"]


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (NB, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def main(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261015); rows = []
    print("tasks:", len(R), "(expected 1024)")
    for key, g in R.groupby(KEYS):
        s = g[SUM].sum()
        rows.append(dict(zip(KEYS, key), nets=len(g), **{k: int(s[k]) for k in SUM},
                         r_pct=100 * s.bad / max(s.delivered, 1), boot95_pct=boot_ub(g.delivered.to_numpy(), g.bad.to_numpy(), rng),
                         frac_oracle=s.qual / max(s.oracle_qual, 1), pct_paths_bad=100 * s.paths_bad / max(s.paths_delivered, 1),
                         detect_pct=100 * s.detected / max(s.n_faulted, 1), max_path_bad=int(g.max_path_bad.max())))
    G = pd.DataFrame(rows); G.to_csv(path.replace("runs.csv", "g7_groups.csv"), index=False)
    pd.set_option("display.width", 260); print(G.round(4).to_string(index=False))

    def grp(c): return G[G.ctrl == c].set_index(["hw", "scen"]).sort_index()

    gg, ga = grp("gglr"), grp("galarm")
    late_g = gg.groupby(level=0).post_bad_late.sum(); late_a = ga.groupby(level=0).post_bad_late.sum()
    rate_g = late_g / gg.groupby(level=0).post_delivered.sum()
    h1 = (rate_g <= 0.001).all() and (late_g <= late_a).all()
    print(f"\nH1 (primary) gglr late post-fault bad <= 0.1% of post-fault deliveries AND <= galarm's, per hw pooled over F2+F1: "
          f"{'PASS' if h1 else 'FAIL'} (gglr late {late_g.to_dict()}, rate {(100 * rate_g).round(4).to_dict()}%; galarm late {late_a.to_dict()})")
    f2 = gg.xs("F2", level=1); det2 = f2.detected.sum() / max(f2.n_faulted.sum(), 1)
    print(f"H2 (primary) gglr detects >= 90% of 2-sd faults (both hw pooled): {'PASS' if det2 >= 0.9 else 'FAIL'} "
          f"({f2.detected.sum()}/{f2.n_faulted.sum()} = {det2:.3f}; galarm {ga.xs('F2', level=1).detected.sum()}/{ga.xs('F2', level=1).n_faulted.sum()})")
    fa = gg.alarms_false.sum() / (4 * 64)
    print(f"H3 (secondary) gglr false alarms <= 1 per 10 networks: {'PASS' if fa <= 0.1 else 'FAIL'} ({gg.alarms_false.sum()} in 256 networks)")
    h4 = (gg.r_pct <= 1).all() and (gg.boot95_pct <= 1).all() and (gg.paths_bad <= ALPHA * gg.paths_delivered).all()
    print(f"H4 (secondary) gglr r <= 1%, UB <= 1%, bad paths <= 5% in all 4 groups: {'PASS' if h4 else 'FAIL'} "
          f"(r max {gg.r_pct.max():.4f}%, UB max {gg.boot95_pct.max():.4f}%)")
    d5 = gg.frac_oracle - ga.frac_oracle
    print(f"H5 (secondary) gglr frac_oracle >= galarm - 0.02 in all groups: {'PASS' if (d5 >= -0.02).all() else 'FAIL'} (diff {d5.round(4).tolist()})")
    print("H6 (descriptive) all controllers: late / early post-fault bad, detection %, false alarms, throughput:")
    print(G.pivot_table(index=["scen", "hw"], columns="ctrl", values=["post_bad_late", "post_bad_early", "detect_pct", "alarms_false", "frac_oracle"]).round(3).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
