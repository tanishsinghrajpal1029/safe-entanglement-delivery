"""Locked analysis for Study 18C G6 (README_G6.md). Usage: python3 analyze_g6.py des_g6_psc/runs.csv"""
import sys
import numpy as np, pandas as pd

KEYS = ["hw", "scen", "ctrl"]; ALPHA = 0.05; NB = 4000
SUM = ["delivered", "bad", "qual", "oracle_qual", "post_delivered", "post_bad", "post_bad_early", "post_bad_late", "prefault_bad",
       "paths_delivered", "paths_bad", "n_faulted", "detected", "alarms_true", "alarms_false", "guard_blocks"]


def boot_ub(d, b, rng):
    I = rng.integers(0, len(d), (NB, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def main(path):
    R = pd.read_csv(path); rng = np.random.default_rng(20261014); rows = []
    print("tasks:", len(R), "(expected 1024)")
    for key, g in R.groupby(KEYS):
        s = g[SUM].sum()
        rows.append(dict(zip(KEYS, key), nets=len(g), **{k: int(s[k]) for k in SUM},
                         r_pct=100 * s.bad / max(s.delivered, 1), boot95_pct=boot_ub(g.delivered.to_numpy(), g.bad.to_numpy(), rng),
                         frac_oracle=s.qual / max(s.oracle_qual, 1), pct_paths_bad=100 * s.paths_bad / max(s.paths_delivered, 1),
                         late_rate_pct=100 * s.post_bad_late / max(s.post_delivered, 1), max_path_bad=int(g.max_path_bad.max())))
    G = pd.DataFrame(rows); G.to_csv(path.replace("runs.csv", "g6_groups.csv"), index=False)
    pd.set_option("display.width", 260); print(G.round(4).to_string(index=False))

    def grp(c): return G[G.ctrl == c].set_index(["hw", "scen"]).sort_index()

    ga, ca, gn = grp("galarm"), grp("cal"), grp("gnaive")
    # H1 (primary): after the first post-fault epoch, the alarm guard stops bad deliveries on faulted paths
    h1a = all(ga.groupby(level=0).post_bad_late.sum() <= 0.001 * ga.groupby(level=0).post_delivered.sum())
    h1b = all(ga.post_bad_late < ca.post_bad_late)
    print(f"\nH1 (primary) galarm late post-fault bad <= 0.1% of post-fault deliveries (pooled per hw) AND < cal's late bad in every group: "
          f"{'PASS' if (h1a and h1b) else 'FAIL'} (galarm late {ga.post_bad_late.tolist()} of {ga.post_delivered.tolist()}; cal late {ca.post_bad_late.tolist()})")
    # H2 (primary): overall safety of galarm
    h2 = (ga.r_pct <= 1).all() and (ga.boot95_pct <= 1).all() and (ga.paths_bad <= ALPHA * ga.paths_delivered).all()
    print(f"H2 (primary) galarm r <= 1%, UB <= 1%, bad paths <= 5% in all 4 groups: {'PASS' if h2 else 'FAIL'} "
          f"(r max {ga.r_pct.max():.4f}%, UB max {ga.boot95_pct.max():.4f}%, bad paths {ga.paths_bad.tolist()}/{ga.paths_delivered.tolist()})")
    # H3 (secondary): detection and false alarms
    det = ga.detected.sum() / max(ga.n_faulted.sum(), 1); fa = ga.alarms_false.sum() / (4 * 64)
    print(f"H3 (secondary) galarm detects >= 90% of faults and false alarms <= 1 per 10 networks: {'PASS' if (det >= 0.9 and fa <= 0.1) else 'FAIL'} "
          f"(detected {ga.detected.sum()}/{ga.n_faulted.sum()} = {det:.3f}; false alarms {ga.alarms_false.sum()} in 256 networks)")
    # H4 (secondary): the alarm costs little throughput relative to the naive guard
    d4 = (ga.frac_oracle - gn.frac_oracle)
    print(f"H4 (secondary) galarm frac_oracle >= gnaive - 0.02 in all groups: {'PASS' if (d4 >= -0.02).all() else 'FAIL'} (differences {d4.round(4).tolist()})")
    print("H5 (descriptive) early (first-epoch, unavoidable with epoch data) vs late post-fault bad pairs, throughput:")
    print(G.pivot_table(index=["scen", "hw"], columns="ctrl", values=["post_bad_early", "post_bad_late", "frac_oracle", "r_pct"]).round(4).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
