"""Study 29 locked analysis. Usage: python3 analyze_29.py runs.csv
Hypotheses and bars fixed after the dev pilot (des_p29_psc, sha 8d2888f6) and before any confirmatory run.
Bootstrap: 4,000 resamples of networks (idx) within each hardware type, one-sided 95%, seed 29. Ratios of sums are
resampled at the network level (vectorised). Block R28 (replay of Study 28's network 19) is descriptive only.
"""
import sys
import numpy as np, pandas as pd
from scipy.stats import beta as betad

B = 4000; RNG = np.random.default_rng(29); BETA = 0.05; BETA1 = 6 * BETA / np.pi ** 2
HWS = ("ion2020", "ionproj"); PS = ("p10", "p20"); MODEL_ERR = ("o0.02_m0", "o0.044_m0", "o0.08_m0", "o0.044_m0F")
OFF = {"o0.02_m0": 0.02, "o0.044_m0": 0.044, "o0.08_m0": 0.08, "o0.044_m0F": 0.044}


def boot(df, num, den=None, a=0.05, side="upper"):
    """network-cluster bootstrap bound for sum(num)/sum(den) (or mean(num) if den is None), resampling idx within hw."""
    parts = []
    for hw, x in df.groupby("hw"):
        g = x.groupby("idx").agg(n=(num, "sum"), d=(den, "sum") if den else (num, "size"))
        parts.append(g[["n", "d"]].to_numpy(float))
    stats = np.empty(B)
    for b in range(B):
        tot = np.zeros(2)
        for arr in parts:
            tot += arr[RNG.integers(0, len(arr), len(arr))].sum(0)
        stats[b] = tot[0] / max(tot[1], 1e-12)
    return float(np.quantile(stats, 1 - a if side == "upper" else a))


def boot_diff(df_a, df_b, col, a=0.05):
    """paired (same idx, same hw) bootstrap lower bound of mean(col_a - col_b)."""
    m = df_a[["hw", "idx", col]].merge(df_b[["hw", "idx", col]], on=["hw", "idx"], suffixes=("_a", "_b"))
    m["d"] = m[f"{col}_a"] - m[f"{col}_b"]; m["one"] = 1.0
    return float(m.d.mean()), boot(m, "d", "one", a=a, side="lower")


def cp_ub(k, n, a=0.05):
    return 1.0 if k >= n else float(betad.ppf(1 - a, k + 1, n - k))


def main(path):
    d = pd.read_csv(path); d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]
    d["fq"] = d.qual / d.oracle_qual.clip(lower=1)
    R = d[d.block == "R28"]; d = d[d.block != "R28"]
    P = lambda *a: print(*a, flush=True); out = []
    P(f"rows {len(d)} (+{len(R)} replay); blocks {sorted(d.block.unique())}; clamped {int(d.epoch_clamped.sum())}; nepoch {sorted(d.nepoch.unique())}")

    # T1 (primary): kgMT post-alarm delivered-pair risk, all model-error cells pooled (both hw, both p)
    x = d[(d.arm == "kgMT") & d.sc.isin(MODEL_ERR)]
    r = x.bad_after_alarm.sum() / max(x.deliv_after_alarm.sum(), 1); ub = boot(x, "bad_after_alarm", "deliv_after_alarm")
    out.append(("T1", "primary", ub <= 0.01, f"kgMT bad after alarm {int(x.bad_after_alarm.sum())}/{int(x.deliv_after_alarm.sum())} = {r:.5f}; UB {ub:.5f} (bar <= 0.01)"))

    # T2 (primary): the Study 28 failure case (forced alarm at the 8th test, offset 0.044): networks with any post-alarm bad pair
    x = d[(d.arm == "kgMT") & (d.sc == "o0.044_m0F")]; k, n = int((x.bad_after_alarm > 0).sum()), len(x); ub = cp_ub(k, n)
    xm = d[(d.arm == "kgM") & (d.sc == "o0.044_m0F")]
    out.append(("T2", "primary", ub <= 0.05, f"kgMT runs with a bad pair after the forced early alarm: {k}/{n}; CP95 UB {ub:.4f} (bar <= 0.05) "
                f"[kgM: {int((xm.bad_after_alarm > 0).sum())}/{len(xm)}]"))

    # T3 (primary): margin accuracy: median over networks of (time-averaged post-alarm margin - offset) in [0, 0.02], each cell
    res = []
    for hw in HWS:
        for sc in ("o0.044_m0", "o0.08_m0"):
            for p in PS:
                x = d[(d.hw == hw) & (d.sc == sc) & (d.arm == "kgMT") & (d.p == p) & d.dec_mean_after.notna()]
                m = float((x.dec_mean_after - OFF[sc]).median()) if len(x) else float("nan"); res.append((hw, sc, p, m, len(x)))
    ok = all(0 <= m <= 0.02 for *_, m, _ in res)
    out.append(("T3", "primary", ok, "; ".join(f"{hw} {sc[1:6]} {p}: {m:+.4f} (n={n})" for hw, sc, p, m, n in res) + " (bar: 0 <= median excess <= 0.02 each)"))

    # T4 (primary): throughput gain over Study 28's response at offset 0.044: fq(kgMT) - fq(kgM) >= 0.10 (bootstrap LB), each hw and p
    res = []
    for hw in HWS:
        for p in PS:
            a = d[(d.hw == hw) & (d.sc == "o0.044_m0") & (d.arm == "kgMT") & (d.p == p)]
            b = d[(d.hw == hw) & (d.sc == "o0.044_m0") & (d.arm == "kgM") & (d.p == p)]
            mean, lb = boot_diff(a, b, "fq"); res.append((hw, p, mean, lb))
    out.append(("T4", "primary", all(lb >= 0.10 for *_, lb in res), "; ".join(f"{hw} {p}: {100 * m:+.1f} pts (LB {100 * l:+.1f})" for hw, p, m, l in res) + " (bar: LB >= +10 points each)"))

    # T5 (primary): validity of the check when the margin can fall (restarts on decreases): false segment alarms per run
    # (alarms with no tested violation since the previous reset), kgMT in the null cells '-' and '-F'
    x = d[(d.arm == "kgMT") & d.sc.isin(["-", "-F"])]; x = x.assign(one=1.0)
    rate = float(x.fa_seg_t.mean()); ub = boot(x, "fa_seg_t", "one")
    out.append(("T5", "primary", rate <= BETA and ub <= 0.08, f"kgMT false segment alarms per run, '-' and '-F' ({len(x)} runs): {int(x.fa_seg_t.sum())} "
                f"= {rate:.4f}/run (bar <= {BETA}); UB {ub:.4f} (bar <= 0.08); restarts per run {x.restarts.mean():.2f}"))

    # T6 (primary): recovery from a false alarm ('-F'): median time-averaged post-alarm margin <= 0.02, each hw and p
    res = []
    for hw in HWS:
        for p in PS:
            x = d[(d.hw == hw) & (d.sc == "-F") & (d.arm == "kgMT") & (d.p == p)]
            res.append((hw, p, float(x.dec_mean_after.median())))
    out.append(("T6", "primary", all(m <= 0.02 for *_, m in res), "; ".join(f"{hw} {p}: {m:.4f}" for hw, p, m in res) + " (bar <= 0.02 each) [kgMJ stays at 0.10]"))

    # U1 (secondary, prediction): the upper bound matters: networks with a post-alarm bad pair, kgMTp > kgMT (model-error cells)
    a = d[(d.arm == "kgMTp") & d.sc.isin(MODEL_ERR)]; b = d[(d.arm == "kgMT") & d.sc.isin(MODEL_ERR)]
    ka, kb = int((a.bad_after_alarm > 0).sum()), int((b.bad_after_alarm > 0).sum())
    out.append(("U1", "secondary (prediction)", ka > kb, f"runs with a post-alarm bad pair: point estimate {ka}/{len(a)} vs bound {kb}/{len(b)}"))

    # U2 (secondary): tracking beats a 16-point tomography campaign at offset 0.044 (throughput), each hw (mean over p)
    res = [(hw, d[(d.hw == hw) & (d.sc == "o0.044_m0") & (d.arm == "kgMT")].fq.mean(), d[(d.hw == hw) & (d.sc == "o0.044_m16")].fq.mean(),
            d[(d.hw == hw) & (d.sc == "o0.044_orc")].fq.mean()) for hw in HWS]
    out.append(("U2", "secondary", all(a > b for _, a, b, _ in res), "; ".join(f"{hw}: kgMT {a:.3f} vs m16 {b:.3f} (oracle {c:.3f})" for hw, a, b, c in res)))

    # U3 (secondary, prediction): the alarm gate is worth it: always-tracking costs >= 5 points without a stressor, each hw (mean over p)
    res = [(hw, d[(d.hw == hw) & (d.sc == "-") & (d.arm == "kg")].fq.mean() - d[(d.hw == hw) & (d.sc == "-") & (d.arm == "kgMTa")].fq.mean()) for hw in HWS]
    out.append(("U3", "secondary (prediction)", all(c >= 0.05 for _, c in res), "; ".join(f"{hw}: {100 * c:.1f} pts" for hw, c in res) + " (prediction >= 5 points)"))

    # U4 (secondary): certificate validity under feedback
    for tag in ("p10", "p20"):
        k, n = int(d[f"{tag}_viol"].sum()), len(d)
        out.append((f"U4_{tag}", "secondary", cp_ub(k, n) <= 0.05, f"network certificate violated in {k}/{n}; CP95 UB {cp_ub(k, n):.4f} (bar <= 0.05)"))

    P("\n== VERDICTS ==")
    for h, tier, ok, s in out: P(f"{h:6s} {tier:24s} {'PASS' if ok else 'FAIL'}  {s}")

    P("\n== D1 by cell (model-error and forced cells) ==")
    x = d[d.sc != "-"]
    g = x.groupby(["hw", "sc", "arm", "p"]).agg(n=("run", "size"), bad=("bad", "sum"), dl=("delivered", "sum"), baa=("bad_after_alarm", "sum"),
        daa=("deliv_after_alarm", "sum"), ub=("users_bad_all", "sum"), ut=("users_total", "sum"), alarm=("alarms", lambda s: (s > 0).mean()),
        dmean=("dec_mean_after", "median"), below=("below_after_alarm", "sum"), fq=("fq", "mean"))
    g["r_%"] = 100 * g.bad / g.dl.clip(lower=1); g["r_after_%"] = 100 * g.baa / g.daa.clip(lower=1); g["pu_%"] = 100 * g.ub / g.ut
    g["below_%"] = 100 * g.below / g.daa.clip(lower=1)
    P(g[["n", "r_%", "r_after_%", "pu_%", "alarm", "dmean", "below_%", "fq"]].round(4).to_string())
    P("\n== D2 no stressor ==")
    P(d[d.sc == "-"].groupby(["hw", "arm", "p"]).agg(fq=("fq", "mean"), alarm=("alarms", lambda s: (s > 0).mean()), fa=("fa_first_t", "sum")).round(4).to_string())
    P("\n== D3 replay of Study 28's network 19 (R28) ==")
    if len(R):
        R = R.assign(fq=R.qual / R.oracle_qual.clip(lower=1))
        P(R[["arm", "delivered", "bad", "bad_after_alarm", "deliv_after_alarm", "dec_final", "dec_mean_after", "fq", "probes"]].to_string())


if __name__ == "__main__":
    main(sys.argv[1])
