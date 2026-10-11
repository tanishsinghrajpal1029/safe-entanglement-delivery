"""Study 30 locked analysis. Usage: python3 analyze_30.py runs.csv
Hypotheses and bars fixed after the dev pilot (des_p30_psc, runs.csv sha f6f1c34173bea250) and before any confirmatory run.
Bootstrap: 4,000 resamples of networks (idx) within each hardware type, one-sided 95%, seed 30 (as Study 29).
"""
import sys
import numpy as np, pandas as pd
from scipy.stats import beta as betad

B = 4000; RNG = np.random.default_rng(30); BETA = 0.05
HWS = ("ion2020", "ionproj"); PS = ("p10", "p20")
GATED = ("kgMC", "kgMCp", "kgMCh")
CONST = ("o0.02", "o0.044", "o0.044F", "o0.08", "L0.044")


def boot(df, num, den=None, a=0.05, side="upper"):
    parts = []
    for hw, x in df.groupby("hw"):
        g = x.groupby("idx").agg(n=(num, "sum"), d=(den, "sum") if den else (num, "size"))
        parts.append(g[["n", "d"]].to_numpy(float))
    stats = np.empty(B)
    for b in range(B):
        tot = np.zeros(2)
        for arr in parts: tot += arr[RNG.integers(0, len(arr), len(arr))].sum(0)
        stats[b] = tot[0] / max(tot[1], 1e-12)
    return float(np.quantile(stats, 1 - a if side == "upper" else a))


def cp_ub(k, n, a=0.05):
    return 1.0 if k >= n else float(betad.ppf(1 - a, k + 1, n - k))


def main(path):
    d = pd.read_csv(path); d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]
    d["fq"] = d.qual / d.oracle_qual.clip(lower=1); d["one"] = 1.0; d["anyb"] = (d.bad_after_alarm_all > 0).astype(float)
    d["exc"] = d.dec_mean_after - d.opt_mean_after
    P = lambda *a: print(*a, flush=True); out = []
    P(f"rows {len(d)}; clamped {int(d.epoch_clamped.sum())}; nepoch {sorted(d.nepoch.unique())}; arms {sorted(d.arm.unique())}")

    # P1 (primary): Theorem 2 in class: per-user and per-pair post-alarm risk, gated provable arms (constant class) + kgMCs (storage)
    x = d[(d.arm.isin(GATED) & d.sc.isin(CONST)) | ((d.arm == "kgMCs") & (d.sc == "s0.044"))]
    ku, nu = int(x.users_bad_post.sum()), int(x.users_post.sum()); ub_u = boot(x, "users_bad_post", "users_post")
    kb, nb = int(x.bad_after_alarm_all.sum()), int(x.deliv_after_alarm_all.sum()); ub_r = boot(x, "bad_after_alarm_all", "deliv_after_alarm_all")
    out.append(("P1", "primary", ub_u <= 0.10 and ub_r <= 0.01, f"users with a post-alarm bad pair {ku}/{nu}, UB {ub_u:.4f} (bar <= 0.10, the theorem's per-user bound); "
                f"post-alarm bad pairs {kb}/{nb}, UB {ub_r:.5f} (bar <= 0.01); {len(x)} runs"))

    # P2 (primary): Study 28's failure case (forced alarm at the 8th test, offset 0.044): runs with any post-alarm bad pair
    x = d[d.arm.isin(GATED) & (d.sc == "o0.044F")]; k, n = int(x.anyb.sum()), len(x)
    xm = d[(d.arm == "kgMT") & (d.sc == "o0.044F")]
    out.append(("P2", "primary", cp_ub(k, n) <= 0.05, f"runs with a post-alarm bad pair {k}/{n}; CP95 UB {cp_ub(k, n):.4f} (bar <= 0.05) [kgMT {int(xm.anyb.sum())}/{len(xm)}]"))

    # P3 (primary): always-on arm, whole-run per-user risk where (B2) holds from t = 0 (constant offsets, incl. none and forced)
    x = d[(d.arm == "kgMCa") & d.sc.isin(["-", "-F", "o0.02", "o0.044", "o0.044F", "o0.08"])]
    k, n = int(x.users_bad_all.sum()), int(x.users_total.sum()); ub = boot(x, "users_bad_all", "users_total")
    out.append(("P3", "primary", ub <= 0.10, f"kgMCa users with any bad pair (whole run) {k}/{n}; UB {ub:.4f} (bar <= 0.10)"))

    # P4 (primary): validity of the new checks: false segment alarms per run in '-' (no stressor), kgMCp and kgMCh
    res = []
    for a in ("kgMCp", "kgMCh"):
        x = d[(d.arm == a) & (d.sc == "-")]; rate = float(x.fa_seg_t.mean()); ub = boot(x, "fa_seg_t", "one"); res.append((a, rate, ub, len(x)))
    out.append(("P4", "primary", all(r <= BETA and u <= 0.08 for _, r, u, _ in res), "; ".join(f"{a}: {r:.4f}/run, UB {u:.4f} ({n} runs)" for a, r, u, n in res) + " (bars: rate <= 0.05, UB <= 0.08)"))

    # P5 (primary): offset-bound accuracy: median over runs of (mean post-alarm margin - mean true offset) in [0, 0.03],
    # kgMCh at o0.044 and kgMCs at s0.044, each hw and p
    res = []
    for a, sc in (("kgMCh", "o0.044"), ("kgMCs", "s0.044")):
        for hw in HWS:
            for p in PS:
                x = d[(d.arm == a) & (d.sc == sc) & (d.hw == hw) & (d.p == p) & d.exc.notna()]
                res.append((a, hw, p, float(x.exc.median()) if len(x) else float("nan"), len(x)))
    out.append(("P5", "primary", all(0 <= m <= 0.03 for *_, m, _ in res), "; ".join(f"{a} {hw} {p}: {m:+.4f} (n={n})" for a, hw, p, m, n in res) + " (bar: 0 <= median excess <= 0.03)"))

    # S1 (secondary, prediction informed by the pilot): price of provability at o0.044: fq(kgMT) - fq(kgMCh) in [0, 0.15], each hw and p
    res = []
    for hw in HWS:
        for p in PS:
            a = d[(d.arm == "kgMT") & (d.sc == "o0.044") & (d.hw == hw) & (d.p == p)].fq.mean()
            b = d[(d.arm == "kgMCh") & (d.sc == "o0.044") & (d.hw == hw) & (d.p == p)].fq.mean(); res.append((hw, p, a - b))
    out.append(("S1", "secondary (prediction)", all(0 <= c <= 0.15 for *_, c in res), "; ".join(f"{hw} {p}: {100 * c:+.1f} pts" for hw, p, c in res) + " (prediction: 0 to 15 points)"))

    # S2 (secondary, prediction): debt: under a late onset the plug-in check alarms in more runs than the mixture (pooled)
    a = d[(d.arm == "kgMCp") & (d.sc == "L0.044")]; b = d[(d.arm == "kgMC") & (d.sc == "L0.044")]
    ra, rb = float((a.alarms > 0).mean()), float((b.alarms > 0).mean())
    out.append(("S2", "secondary (prediction)", ra > rb, f"L0.044 alarm rate: plug-in {ra:.3f} vs mixture {rb:.3f}"))

    # S3 (secondary): the hybrid is robust: its alarm rate is >= min(mixture, plug-in) - 0.05 in each of L0.044, o0.044, s0.044, h0.044
    res = []
    for sc in ("L0.044", "o0.044", "s0.044", "h0.044"):
        r = {a: float((d[(d.arm == a) & (d.sc == sc)].alarms > 0).mean()) for a in GATED}; res.append((sc, r))
    out.append(("S3", "secondary", all(r["kgMCh"] >= min(r["kgMC"], r["kgMCp"]) - 0.05 for _, r in res),
                "; ".join(f"{sc}: mix {r['kgMC']:.2f}, plug {r['kgMCp']:.2f}, hyb {r['kgMCh']:.2f}" for sc, r in res)))

    # S4 (secondary, predictions of failure outside the theorem): post-alarm per-user risk > 0.10 in each cell below
    cells = [("L0.044F", GATED + ("kgMT",)), ("h0.044", GATED + ("kgMT",)), ("s0.044", GATED + ("kgMT",)), ("o0.044F", ("kgMCs",))]
    res = []
    for sc, arms in cells:
        x = d[d.arm.isin(arms) & (d.sc == sc)]; res.append((sc, x.users_bad_post.sum() / max(x.users_post.sum(), 1)))
    x = d[(d.arm == "kgMCa") & (d.sc == "L0.044")]; res.append(("kgMCa L0.044 (whole run)", x.users_bad_all.sum() / x.users_total.sum()))
    out.append(("S4", "secondary (prediction: unsafe)", all(r > 0.10 for _, r in res), "; ".join(f"{c}: {r:.3f}" for c, r in res)))

    # S5 (secondary): certificate validity under feedback (all runs)
    for tag in ("p10", "p20"):
        k, n = int(d[f"{tag}_viol"].sum()), len(d)
        out.append((f"S5_{tag}", "secondary", cp_ub(k, n) <= 0.05, f"certificate violated in {k}/{n}; CP95 UB {cp_ub(k, n):.4f} (bar <= 0.05)"))

    # S6 (secondary, prediction): the static competitor (fixed margin 0.10 from t = 0) delivers < 5% of oracle on both hw
    res = [(hw, d[(d.hw == hw) & d.sc.str.endswith("_fix")].fq.mean()) for hw in HWS]
    out.append(("S6", "secondary (prediction)", all(f < 0.05 for _, f in res), "; ".join(f"{hw}: {f:.4f}" for hw, f in res)))

    P("\n== VERDICTS ==")
    for h, tier, ok, s in out: P(f"{h:6s} {tier:32s} {'PASS' if ok else 'FAIL'}  {s}")

    P("\n== D1 detection: alarm rate and median first-alarm epoch (onset at 30 in L0.044) ==")
    x = d[d.arm.isin(GATED + ("kgMT", "kgMCs")) & ~d.sc.str.endswith("F") & (d.sc != "-") & ~d.sc.str.contains("_")]
    P(x.groupby(["hw", "sc", "p", "arm"]).agg(alarm=("alarms", lambda s: (s > 0).mean()), ep1=("first_alarm_ep", "median")).round(3).unstack("arm").to_string())
    P("\n== D2 worst-user risk over the whole run (users ever given a bad pair / users) ==")
    P(d.groupby(["sc", "arm"]).apply(lambda z: z.users_bad_all.sum() / z.users_total.sum(), include_groups=False).round(4).unstack("arm").to_string())
    P("\n== D3 post-alarm per-user risk and pair risk by cell ==")
    g = d[d.arm.str.startswith("kgM")].groupby(["sc", "arm"]).agg(ubp=("users_bad_post", "sum"), up=("users_post", "sum"),
        b=("bad_after_alarm_all", "sum"), dl=("deliv_after_alarm_all", "sum"), anyb=("anyb", "mean"), exc=("exc", "median"), probes=("probes", "mean"))
    g["pu_post"] = g.ubp / g.up.clip(lower=1); g["r_after"] = g.b / g.dl.clip(lower=1)
    P(g[["pu_post", "r_after", "anyb", "exc", "probes"]].round(4).to_string())
    P("\n== D4 throughput (fraction of oracle) ==")
    P(d.groupby(["hw", "sc", "arm"]).fq.mean().round(4).unstack("arm").to_string())


if __name__ == "__main__":
    main(sys.argv[1])
