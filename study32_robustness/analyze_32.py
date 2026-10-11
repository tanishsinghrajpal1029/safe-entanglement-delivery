"""Study 32 locked analysis. Usage: python3 analyze_32.py runs.csv
Hypotheses and bars fixed after the dev pilot (des_p32_psc, runs.csv sha 2a7d2da377d947b9) and before any confirmatory run.
Bootstrap: 4,000 network-cluster resamples (idx) within hardware type, one-sided 95%, seed 32.
"""
import sys
import numpy as np, pandas as pd
from scipy.stats import beta as betad

B = 4000; RNG = np.random.default_rng(32)


def boot(df, num, den=None, a=0.05, side="upper"):
    parts = []
    for hw, x in df.groupby("hw"):
        g = x.groupby("idx").agg(n=(num, "sum"), d=(den, "sum") if den else (num, "size"))
        parts.append(g[["n", "d"]].to_numpy(float))
    st = np.empty(B)
    for b in range(B):
        tot = np.zeros(2)
        for arr in parts: tot += arr[RNG.integers(0, len(arr), len(arr))].sum(0)
        st[b] = tot[0] / max(tot[1], 1e-12)
    return float(np.quantile(st, 1 - a if side == "upper" else a))


def boot_ratio(da, db, num, den, a=0.05):
    """upper bound of [sum num_a / sum den_a] / [sum num_b / sum den_b], resampling networks (same idx, hw) jointly."""
    m = da.merge(db, on=["hw", "idx", "cfg"], suffixes=("_a", "_b"))
    parts = [g[[f"{num}_a", f"{den}_a", f"{num}_b", f"{den}_b"]].groupby(g.idx).sum().to_numpy(float) for _, g in m.groupby("hw")]
    st = np.empty(B)
    for b in range(B):
        t = np.zeros(4)
        for arr in parts: t += arr[RNG.integers(0, len(arr), len(arr))].sum(0)
        st[b] = (t[0] / max(t[1], 1e-12)) / max(t[2] / max(t[3], 1e-12), 1e-12)
    return float(np.quantile(st, 1 - a))


def boot_diff(da, db, col, a=0.05):
    m = da[["hw", "idx", "cfg", col]].merge(db[["hw", "idx", "cfg", col]], on=["hw", "idx", "cfg"], suffixes=("_a", "_b"))
    m["d"] = m[f"{col}_a"] - m[f"{col}_b"]; m["one"] = 1.0
    return float(m.d.mean()), boot(m, "d", "one", a=a, side="lower")


def cp_ub(k, n, a=0.05):
    return 1.0 if k >= n else float(betad.ppf(1 - a, k + 1, n - k))


def main(path):
    d = pd.read_csv(path); d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]; d["blk"] = d.block.str[-1]
    d["fq"] = np.where(d.oracle_qual > 0, d.qual / d.oracle_qual.clip(lower=1), np.nan)
    P = lambda *a: print(*a, flush=True); out = []
    P(f"rows {len(d)}; clamped {int(d.epoch_clamped.sum())}; blocks {d.blk.value_counts().to_dict()}")
    R = d[d.blk == "R"]; E = d[d.blk == "E"]; T = d[d.blk == "T"]

    # R1 (primary): the bound without intersection keeps Theorem 2 in class (o0.044, L0.044)
    x = R[(R.arm == "kgMChN") & R.sc.isin(["o0.044", "L0.044"])]
    ubu = boot(x, "users_bad_post", "users_post"); ubr = boot(x, "bad_after_alarm_all", "deliv_after_alarm_all")
    out.append(("R1", "primary", ubu <= 0.10 and ubr <= 0.01, f"kgMChN in class: users {int(x.users_bad_post.sum())}/{int(x.users_post.sum())} UB {ubu:.4f} "
                f"(bar <= 0.10); pairs {int(x.bad_after_alarm_all.sum())}/{int(x.deliv_after_alarm_all.sum())} UB {ubr:.5f} (bar <= 0.01)"))
    # R2 (primary): no throughput cost in class ('-', o0.044, L0.044): paired mean fq(N) - fq(min) >= -0.02 (bootstrap LB)
    a = R[(R.arm == "kgMChN") & R.sc.isin(["-", "o0.044", "L0.044"])]; b = R[(R.arm == "kgMCh") & R.sc.isin(["-", "o0.044", "L0.044"])]
    mean, lb = boot_diff(a, b, "fq")
    out.append(("R2", "primary", lb >= -0.02, f"fq(kgMChN) - fq(kgMCh): {100 * mean:+.2f} pts, LB {100 * lb:+.2f} (bar LB >= -2 pts)"))
    # R3 (primary): recovery after a forced miscoverage (o0.044FM): post-alarm bad-pair rate ratio N / running-min, UB <= 0.5
    a = R[(R.arm == "kgMChN") & (R.sc == "o0.044FM")]; b = R[(R.arm == "kgMCh") & (R.sc == "o0.044FM")]
    ra = a.bad_after_alarm_all.sum() / max(a.deliv_after_alarm_all.sum(), 1); rb = b.bad_after_alarm_all.sum() / max(b.deliv_after_alarm_all.sum(), 1)
    ub = boot_ratio(a, b, "bad_after_alarm_all", "deliv_after_alarm_all")
    out.append(("R3", "primary", ub <= 0.5, f"post-alarm bad-pair rate: no-intersection {ra:.4f} vs running minimum {rb:.4f}; ratio {ra / max(rb, 1e-12):.3f}, UB {ub:.3f} (bar <= 0.5)"))
    # R4 (primary): the no-intersection bound recovers: among o0.044FM runs whose window-1 bound went below theta, share that came back
    k = int(((a.w1_looks_below > 0) & (a.w1_recover >= 0)).sum()); n = int((a.w1_looks_below > 0).sum())
    lbk = float(betad.ppf(0.05, k, n - k + 1)) if k > 0 else 0.0
    out.append(("R4", "primary", n > 0 and lbk >= 0.8, f"recovered {k}/{n} (CP95 lower bound {lbk:.3f}; bar >= 0.8); median tests to recover "
                f"{a.w1_recover_tests[a.w1_recover_tests >= 0].median():.0f} [running minimum: {int((b.w1_recover >= 0).sum())}/{int((b.w1_looks_below > 0).sum())}, by construction]"))
    # E1 (primary): Theorem 2 robustness (kgMCh, o0.044) at tau 0.85, tau 0.92 and less calibration data, pooled
    x = E[(E.arm == "kgMCh") & (E.sc == "o0.044")]
    ubu = boot(x, "users_bad_post", "users_post"); ubr = boot(x, "bad_after_alarm_all", "deliv_after_alarm_all")
    out.append(("E1", "primary", ubu <= 0.10 and ubr <= 0.01, f"kgMCh post-alarm: users {int(x.users_bad_post.sum())}/{int(x.users_post.sum())} UB {ubu:.4f} (bar <= 0.10); "
                f"pairs {int(x.bad_after_alarm_all.sum())}/{int(x.deliv_after_alarm_all.sum())} UB {ubr:.5f} (bar <= 0.01)"))
    # E2 (primary): Corollary 3 robustness: always-on, whole run, all Block E cells (base and variants)
    x = E[E.arm == "kgMCa"]; ub = boot(x, "users_bad_all", "users_total")
    out.append(("E2", "primary", ub <= 0.10, f"kgMCa users ever given a bad pair {int(x.users_bad_all.sum())}/{int(x.users_total.sum())}; UB {ub:.4f} (bar <= 0.10)"))
    # S1 (secondary, prediction): after a false alarm before an onset (L0.044F), the no-intersection bound lowers post-alarm pair risk
    a = R[(R.arm == "kgMChN") & (R.sc == "L0.044F")]; b = R[(R.arm == "kgMCh") & (R.sc == "L0.044F")]
    ra = a.bad_after_alarm_all.sum() / max(a.deliv_after_alarm_all.sum(), 1); rb = b.bad_after_alarm_all.sum() / max(b.deliv_after_alarm_all.sum(), 1)
    out.append(("S1", "secondary (prediction)", ra < rb, f"L0.044F post-alarm bad-pair rate: no-intersection {ra:.4f} vs running minimum {rb:.4f} (per-user risk stays high: B2 fails)"))
    # S2 (secondary, prediction): fewer re-alarms with the no-intersection bound in o0.044FM
    a = R[(R.arm == "kgMChN") & (R.sc == "o0.044FM")]; b = R[(R.arm == "kgMCh") & (R.sc == "o0.044FM")]
    out.append(("S2", "secondary (prediction)", a.alarms.mean() < b.alarms.mean(), f"mean real alarms per run: {a.alarms.mean():.3f} vs {b.alarms.mean():.3f}"))
    # S3 (secondary, predictions): thin hardware documents the limit: alarms in <= 10% of kgMCh runs; kgMCa delivers < 5% of oracle
    x = T[T.arm == "kgMCh"]; y = T[T.arm == "kgMCa"]
    fa = float((x.alarms > 0).mean()); fqa = float(y.qual.sum() / max(y.oracle_qual.sum(), 1))
    out.append(("S3", "secondary (prediction)", fa <= 0.10 and fqa < 0.05, f"thin hardware: kgMCh runs with an alarm {fa:.3f} (<= 0.10); kgMCa throughput {fqa:.4f} (< 0.05)"))
    # S4 (secondary): certificate validity under feedback
    for tag in ("p10", "p20"):
        k, n = int(d[f"{tag}_viol"].sum()), len(d)
        out.append((f"S4_{tag}", "secondary", cp_ub(k, n) <= 0.05, f"certificate violated in {k}/{n}; CP95 UB {cp_ub(k, n):.4f} (bar <= 0.05)"))

    P("\n== VERDICTS ==")
    for h, tier, ok, s in out: P(f"{h:6s} {tier:24s} {'PASS' if ok else 'FAIL'}  {s}")
    P("\n== D1 Block R ==")
    g = R.groupby(["hw", "sc", "p", "arm"]).agg(n=("run", "size"), alarm=("alarms", "mean"), baa=("bad_after_alarm_all", "sum"), daa=("deliv_after_alarm_all", "sum"),
        ubp=("users_bad_post", "sum"), up=("users_post", "sum"), uba=("users_bad_all", "sum"), ut=("users_total", "sum"), fq=("fq", "mean"),
        dmean=("dec_mean_after", "median"), npois=("npois", "mean"), wbelow=("w1_looks_below", "mean"), wrec=("w1_recover_tests", "median"))
    g["r_after"] = g.baa / g.daa.clip(lower=1); g["pu_post"] = g.ubp / g.up.clip(lower=1); g["pu_all"] = g.uba / g.ut
    P(g[["n", "alarm", "r_after", "pu_post", "pu_all", "fq", "dmean", "npois", "wbelow", "wrec"]].round(4).to_string())
    for blk, X in (("E", E), ("T", T)):
        P(f"\n== D2 Block {blk} ==")
        g = X.groupby(["hw", "var", "sc", "p", "arm"]).agg(n=("run", "size"), oracle=("oracle_qual", "sum"), alarm=("alarms", lambda s: (s > 0).mean()),
            ep1=("first_alarm_ep", "median"), baa=("bad_after_alarm_all", "sum"), daa=("deliv_after_alarm_all", "sum"), uba=("users_bad_all", "sum"),
            ut=("users_total", "sum"), fq=("fq", "mean"), dmean=("dec_mean_after", "median"))
        g["r_after"] = g.baa / g.daa.clip(lower=1); g["pu_all"] = g.uba / g.ut
        P(g[["n", "oracle", "alarm", "ep1", "r_after", "pu_all", "fq", "dmean"]].round(4).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
