"""Locked analysis for Study 18C S1 (README_S1.md). Usage: python3 analyze_s1.py des_s1_psc des_c2_psc
Compares S1 (realistic overlapping windows) with C2 restricted to the SAME paths (block A, idx < 128)."""
import sys
import numpy as np, pandas as pd

KEYS = ["cell", "g", "mem"]; MIND = 200; NPS = 128


def boot(d, b, rng):
    if len(d) == 0: return np.nan
    I = rng.integers(0, len(d), (4000, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


def groups(R, tag, rng):
    rows = []
    for key, x in R.groupby(KEYS):
        d, b = x.delivered.values, x.bad.values
        rows.append(dict(zip(KEYS, key), paths=len(x), delivered=int(d.sum()), bad=int(b.sum()), r_pct=100 * b.sum() / max(d.sum(), 1),
                         boot95_pct=boot(d, b, rng), top_path_bad=int(b.max()), frac_oracle=x.qual.sum() / max(x.oracle_qual.sum(), 1)))
    return pd.DataFrame(rows).add_suffix("_" + tag).rename(columns={k + "_" + tag: k for k in KEYS})


def main(ds1, dc2):
    rng = np.random.default_rng(20261010)
    S = pd.read_csv(f"{ds1}/runs.csv"); C = pd.read_csv(f"{dc2}/runs.csv"); C = C[(C.block == "A") & (C.idx < NPS)]
    print("S1 tasks:", len(S), "(expected 6144); paired C2 rows:", len(C))
    M = groups(S, "s1", rng).merge(groups(C, "c2", rng), on=KEYS)
    M["g"] = M.g.map(lambda v: f"{v:.0e}"); M.to_csv(f"{ds1}/s1_groups.csv", index=False)
    pd.set_option("display.width", 260)
    cols = KEYS + ["delivered_s1", "bad_s1", "r_pct_s1", "boot95_pct_s1", "top_path_bad_s1", "r_pct_c2", "boot95_pct_c2", "frac_oracle_s1", "frac_oracle_c2"]
    print(M[cols].round(4).to_string(index=False))
    ns = M[(M.cell != "siv_tau080_L1") & (M.delivered_s1 >= MIND)]
    print(f"\nS1-a (primary) non-SiV groups r <= 1% under realistic windows: {'PASS' if (ns.r_pct_s1 <= 1).all() else 'FAIL'} "
          f"({int((ns.r_pct_s1 <= 1).sum())}/{len(ns)}; max {ns.r_pct_s1.max():.3f}%)")
    both = ns[(ns.delivered_c2 >= MIND)]
    ratio = (both.boot95_pct_s1 / both.boot95_pct_c2.replace(0, np.nan)).dropna()
    print(f"S1-b (prediction: bounds widen) median UB ratio S1/C2 over {len(ratio)} non-SiV groups: {ratio.median():.2f} -> "
          f"{'CONFIRMED' if ratio.median() > 1 else 'NOT CONFIRMED'}")
    print(f"S1-c (descriptive) non-SiV groups with UB <= 1%: S1 {int((ns.boot95_pct_s1 <= 1).sum())}/{len(ns)}, "
          f"C2 (same paths) {int((both.boot95_pct_c2 <= 1).sum())}/{len(both)}; max UB S1 {ns.boot95_pct_s1.max():.3f}%")
    sv = M[M.cell == "siv_tau080_L1"]
    print("SiV (reported, outside the claimed regime):"); print(sv[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
