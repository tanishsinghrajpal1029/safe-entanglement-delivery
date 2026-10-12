"""Study 34 locked analysis. Usage: python3 analyze_34.py runs_g5.csv runs_g10.csv runs_g30.csv
Hypotheses and bars fixed after the dev pilot (des_p34_g5/g10/g30, runs.csv sha c78898336e352538 / 7e296f0546541df3 /
2db35cfb03bafeca) and before any confirmatory run. Bootstrap: 4,000 network-cluster resamples (idx) within grid x variant x
hardware type, one-sided 95%, seed 34. Per-user measures use SERVED users (users with >= 1 measured delivery), because users
dilute ~60x on the 30 x 30 grid at the base rate (review B1).
"""
import sys
import numpy as np, pandas as pd
from scipy.stats import beta as betad

B = 4000; RNG = np.random.default_rng(34)


def boot(df, num, den, a=0.05):
    parts = [x.groupby("idx").agg(n=(num, "sum"), d=(den, "sum"))[["n", "d"]].to_numpy(float) for _, x in df.groupby(["grid", "var", "hw"])]
    st = np.empty(B)
    for b in range(B):
        t = np.zeros(2)
        for arr in parts: t += arr[RNG.integers(0, len(arr), len(arr))].sum(0)
        st[b] = t[0] / max(t[1], 1e-12)
    return float(np.quantile(st, 1 - a))


def cp_ub(k, n, a=0.05):
    return 1.0 if k >= n else float(betad.ppf(1 - a, k + 1, n - k))


def main(paths):
    d = pd.concat([pd.read_csv(f) for f in paths], ignore_index=True)
    d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]; d["var"] = d.cfg.str.split("|").str[2]
    d["fq"] = np.where(d.oracle_qual > 0, d.qual / d.oracle_qual.clip(lower=1), np.nan)
    P = lambda *a: print(*a, flush=True); out = []
    P(f"rows {len(d)}; clamped {int(d.epoch_clamped.sum())}; grids {d.grid.value_counts().to_dict()}")
    big = d[d.grid.isin([10, 30])]

    # K1 (primary): Theorem 2 on the larger grids: gated arm (kgMChN), offset 0.044 and forced early alarm, all load variants
    x = big[(big.arm == "kgMChN") & big.sc.isin(["o0.044", "o0.044F"])]
    ubr = boot(x, "bad_after_alarm_all", "deliv_after_alarm_all"); ubu = boot(x, "users_bad_post", "users_post")
    out.append(("K1", "primary", ubr <= 0.01 and ubu <= 0.10, f"10x10 + 30x30, kgMChN: post-alarm pairs {int(x.bad_after_alarm_all.sum())}/{int(x.deliv_after_alarm_all.sum())} "
                f"UB {ubr:.5f} (bar <= 0.01); post-alarm users {int(x.users_bad_post.sum())}/{int(x.users_post.sum())} UB {ubu:.4f} (bar <= 0.10)"))
    # K2 (primary): Corollary 3 on the larger grids: always-on arm, all scenarios and variants
    x = big[big.arm == "kgMCa"]
    ubr = boot(x, "bad_all", "delivered_all"); ubu = boot(x, "users_bad_served", "users_served")
    out.append(("K2", "primary", ubr <= 0.01 and ubu <= 0.10, f"10x10 + 30x30, kgMCa: bad pairs {int(x.bad_all.sum())}/{int(x.delivered_all.sum())} UB {ubr:.5f} (bar <= 0.01); "
                f"served users ever bad {int(x.users_bad_served.sum())}/{int(x.users_served.sum())} UB {ubu:.4f} (bar <= 0.10)"))
    # K3 (primary): the 5 x 5 reference reproduces Studies 30/32 with fresh seeds (same bars as K1 and K2)
    x = d[(d.grid == 5) & (d.arm == "kgMChN") & d.sc.isin(["o0.044", "o0.044F"])]; y = d[(d.grid == 5) & (d.arm == "kgMCa")]
    ub1 = boot(x, "bad_after_alarm_all", "deliv_after_alarm_all"); ub2 = boot(y, "users_bad_served", "users_served")
    out.append(("K3", "primary", ub1 <= 0.01 and ub2 <= 0.10, f"5x5 reference: kgMChN post-alarm pairs UB {ub1:.5f} (<= 0.01); kgMCa served users UB {ub2:.4f} (<= 0.10)"))
    # S1 (secondary, prediction): discriminating cells: without a check the offset harms > 10% of served users on every grid and variant
    res = [(g, v, z.users_bad_served.sum() / max(z.users_served.sum(), 1)) for (g, v), z in d[(d.arm == "kg") & (d.sc == "o0.044")].groupby(["grid", "var"])]
    out.append(("S1", "secondary (prediction)", all(r > 0.10 for *_, r in res), "; ".join(f"{g}x{g} {v}: {r:.3f}" for g, v, r in res)))
    # S2 (secondary, prediction): detection carries over: alarm rate at offset 0.044 (kgMChN, base load) on 30x30 within 0.15 of 5x5
    a5 = d[(d.grid == 5) & (d["var"] == "base") & (d.arm == "kgMChN") & (d.sc == "o0.044")]; a30 = d[(d.grid == 30) & (d["var"] == "base") & (d.arm == "kgMChN") & (d.sc == "o0.044")]
    r5, r30 = float((a5.alarms > 0).mean()), float((a30.alarms > 0).mean())
    out.append(("S2", "secondary (prediction)", abs(r30 - r5) <= 0.15, f"alarm rate at offset 0.044: 5x5 {r5:.3f}, 30x30 {r30:.3f} (|diff| <= 0.15)"))
    # S3 (secondary, prediction): three times the load detects earlier: median first-alarm epoch m3 < base, on 5x5 and on 30x30
    res = []
    for g in (5, 30):
        z = d[(d.grid == g) & (d.arm == "kgMChN") & (d.sc == "o0.044")]
        res.append((g, z[z["var"] == "m3"].first_alarm_ep.median(), z[z["var"] == "base"].first_alarm_ep.median()))
    out.append(("S3", "secondary (prediction)", all(m < b for _, m, b in res), "; ".join(f"{g}x{g}: m3 {m:.1f} vs base {b:.1f} epochs" for g, m, b in res)))
    # S4 (secondary): matched exposure: served-user risk of the gated arm at offset 0.044 on 30x30 'u' within 0.10 of 5x5 'base'
    z5 = d[(d.grid == 5) & (d["var"] == "base") & (d.arm == "kgMChN") & (d.sc == "o0.044")]; zu = d[(d.grid == 30) & (d["var"] == "u") & (d.arm == "kgMChN") & (d.sc == "o0.044")]
    q5 = z5.users_bad_served.sum() / max(z5.users_served.sum(), 1); qu = zu.users_bad_served.sum() / max(zu.users_served.sum(), 1)
    out.append(("S4", "secondary", abs(qu - q5) <= 0.10, f"served-user risk, gated, offset 0.044: 5x5 base {q5:.3f}, 30x30 matched {qu:.3f} (|diff| <= 0.10)"))
    # S5 (secondary): certificate validity under feedback
    for tag in ("p10", "p20"):
        k, n = int(d[f"{tag}_viol"].sum()), len(d)
        out.append((f"S5_{tag}", "secondary", cp_ub(k, n) <= 0.05, f"certificate violated in {k}/{n}; CP95 UB {cp_ub(k, n):.4f} (bar <= 0.05)"))

    P("\n== VERDICTS ==")
    for h, tier, ok, s in out: P(f"{h:6s} {tier:24s} {'PASS' if ok else 'FAIL'}  {s}")
    P("\n== D1 by grid, load, hardware, scenario, arm ==")
    g = d.groupby(["grid", "var", "hw", "sc", "arm", "p"]).agg(n=("run", "size"), users=("users_total", "mean"), tests=("p10_tests", "mean"),
        alarm=("alarms", lambda s: (s > 0).mean()), ep1=("first_alarm_ep", "median"), bad=("bad", "sum"), dl=("delivered", "sum"),
        baa=("bad_after_alarm_all", "sum"), daa=("deliv_after_alarm_all", "sum"), ubs=("users_bad_served", "sum"), us=("users_served", "sum"),
        fq=("fq", "mean"), dmean=("dec_mean_after", "median"))
    g["r"] = g.bad / g.dl.clip(lower=1); g["r_after"] = g.baa / g.daa.clip(lower=1); g["pu_served"] = g.ubs / g.us.clip(lower=1)
    P(g[["n", "users", "tests", "alarm", "ep1", "r", "r_after", "pu_served", "fq", "dmean"]].round(4).to_string())


if __name__ == "__main__":
    main(sys.argv[1:])
