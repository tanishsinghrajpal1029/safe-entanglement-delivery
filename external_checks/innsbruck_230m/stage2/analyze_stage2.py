"""Innsbruck Stage 2 analysis (LOCKED before the event table exists; see PREREG_INNSBRUCK_STAGE2.md).

Inputs (written by the decoder, schema fixed in the pre-registration):
  events.csv : run, t_s, herald, basisA, basisB, a, b
               run    - run label (Node A folder name, e.g. "1819")
               t_s    - herald time in seconds since the run's start (BSM clock)
               herald - "psi+" or "psi-"
               basisA, basisB - "X", "Y" or "Z"
               a, b   - ion outcomes, 0 or 1
  runs.csv   : run, t_start_s, t_end_s   (run window on the BSM clock; duration = t_end_s - t_start_s)
Usage: python3 analyze_stage2.py events.csv runs.csv out.json [--seed 20261007]
"""
import json, sys
import numpy as np, pandas as pd
from scipy import stats

BIN_S = 60.0
SEED = 20261007


def poisson_tests(ev, runs):
    """S2-d: heralds a Poisson process at constant rate within each run (pooled dispersion test), and across runs."""
    chi2, df, per = 0.0, 0, []
    for _, r in runs.iterrows():
        t = ev.loc[ev.run == r.run, "t_s"].to_numpy(); dur = r.t_end_s - r.t_start_s
        nb = int(np.floor(dur / BIN_S))
        if nb < 2: continue
        n, _ = np.histogram(t, bins=nb, range=(0.0, nb * BIN_S)); m = n.mean()
        if m <= 0: continue
        c = float(((n - m) ** 2).sum() / m); chi2 += c; df += nb - 1
        per.append(dict(run=str(r.run), events=int(n.sum()), bins=nb, dispersion=float(n.var(ddof=1) / m)))
    p_within = float(stats.chi2.sf(chi2, df)) if df else None
    cnt = np.array([int((ev.run == r).sum()) for r in runs.run]); dur = (runs.t_end_s - runs.t_start_s).to_numpy()
    exp = cnt.sum() * dur / dur.sum(); c_across = float(((cnt - exp) ** 2 / exp).sum())
    p_across = float(stats.chi2.sf(c_across, len(cnt) - 1))
    return dict(within_chi2=chi2, within_df=df, p_within=p_within, across_chi2=c_across, across_df=int(len(cnt) - 1),
                p_across=p_across, per_run=per, rates_per_min=[float(x) for x in 60 * cnt / dur])


def strata(ev, runs):
    """Strata = run x herald type; each split at its median herald time into early / late halves; outcome = oriented success."""
    out = []; dur = dict(zip(runs.run, runs.t_end_s - runs.t_start_s))
    for (run, h), g in ev.groupby(["run", "herald"]):
        g = g.sort_values("t_s"); n = len(g)
        if n < 4: continue
        k = n // 2; agree = (g.a.to_numpy() == g.b.to_numpy()).astype(int)
        # orient so that "success" = the stratum's majority correlation (agree or disagree); symmetric in early/late,
        # so a loss of correlation over time shows up as a common early->late DROP in the success rate
        orient = 1 if agree.mean() >= 0.5 else 0; succ = agree if orient else 1 - agree
        out.append(dict(run=str(run), herald=h, basis=g.basisA.iloc[0] + g.basisB.iloc[0], orient_agree=orient, n1=k,
                        k1=int(succ[:k].sum()), n2=n - k, k2=int(succ[k:].sum()),
                        u=[float(x) for x in g.t_s.to_numpy() / dur[str(run)]], succ=[int(x) for x in succ]))
    return out


def homogeneity(S):
    """S2-a: early vs late agreement rate. Fisher exact per stratum, combined by Fisher's method; plus CMH common shift."""
    ps = [stats.fisher_exact([[s["k1"], s["n1"] - s["k1"]], [s["k2"], s["n2"] - s["k2"]]])[1] for s in S]
    X = -2 * np.sum(np.log(np.clip(ps, 1e-300, 1))); p_comb = float(stats.chi2.sf(X, 2 * len(ps)))
    num = var = 0.0
    for s in S:
        N = s["n1"] + s["n2"]; K = s["k1"] + s["k2"]
        if N < 2: continue
        e = s["n1"] * K / N; v = s["n1"] * s["n2"] * K * (N - K) / (N ** 2 * (N - 1)); num += s["k1"] - e; var += v
    cmh = (abs(num) - 0.5) ** 2 / var if var > 0 else 0.0
    shift = sum(s["k2"] for s in S) / sum(s["n2"] for s in S) - sum(s["k1"] for s in S) / sum(s["n1"] for s in S)
    return dict(fisher_ps=[float(p) for p in ps], fisher_combined_p=p_comb, cmh_chi2=float(cmh), cmh_p=float(stats.chi2.sf(cmh, 1)),
                pooled_late_minus_early=float(shift), n_strata=len(S))


INFORMATIVE = 0.20   # |stratum success rate - 0.5| >= 0.20 (time-symmetric selection; the test conditions on margins)


def van_elteren(S):
    """S2-a PRIMARY: stratified Wilcoxon (van Elteren) test of whether successes occur earlier than failures within a run,
    over informative strata. Exact conditional on each stratum's margins under H0; normal approximation for the sum.
    Z > 0 means successes come EARLIER (correlation decays over the run)."""
    num = var = 0.0; used = 0
    for s in S:
        y = np.array(s["succ"]); u = np.array(s["u"]); n = len(y); k = int(y.sum())
        if abs(k / n - 0.5) < INFORMATIVE or k in (0, n): continue
        r = stats.rankdata(u); w = 1.0 / (n + 1)
        W = r[y == 0].sum()                       # rank sum of FAILURES: large if failures come late
        EW = (n - k) * (n + 1) / 2; VW = k * (n - k) * (n + 1) / 12
        num += w * (W - EW); var += w * w * VW; used += 1
    z = num / np.sqrt(var) if var > 0 else 0.0
    return dict(z=float(z), p_two_sided=float(2 * stats.norm.sf(abs(z))), strata_used=used)


def power_trend(S, rng, reps=1000):
    """Smallest relative linear loss of correlation over one run (|2p-1| -> |2p-1|(1-d)) that the primary test detects
    with 80% power at two-sided 5%, keeping the observed times and stratum sizes."""
    def pw(d):
        hit = 0
        for _ in range(reps):
            T = []
            for s in S:
                u = np.array(s["u"]); p = np.clip(np.mean(s["succ"]), 0.5, 0.99)
                q = 0.5 + (p - 0.5) * (1 - d * u) / (1 - d / 2)
                T.append(dict(u=list(u), succ=list(rng.uniform(size=len(u)) < np.clip(q, 0, 1))))
            if van_elteren(T)["p_two_sided"] < 0.05: hit += 1
        return hit / reps
    for d in np.arange(0.1, 2.01, 0.1):
        if pw(d) >= 0.8: return float(round(d, 1))
    return None


def betabinom_cdf(k, n, a, b):
    return float(stats.betabinom.cdf(k, n, a, b)) if k >= 0 else 0.0


def predictive(S, rng):
    """S2-c: Jeffreys posterior from the early half predicts the late-half agree count (beta-binomial)."""
    pit, cover = [], []
    for s in S:
        a, b = 0.5 + s["k1"], 0.5 + s["n1"] - s["k1"]; n2, k2 = s["n2"], s["k2"]
        lo, hi = betabinom_cdf(k2 - 1, n2, a, b), betabinom_cdf(k2, n2, a, b)
        pit.append(lo + rng.uniform() * (hi - lo))
        ql = int(stats.betabinom.ppf(0.05, n2, a, b)); qh = int(stats.betabinom.ppf(0.95, n2, a, b)); cover.append(ql <= k2 <= qh)
    pit = np.array(pit); ks = stats.kstest(pit, "uniform")
    m = len(cover); c = int(np.sum(cover)); band = stats.binom.ppf([0.025, 0.975], m, 0.90)
    return dict(pit=[float(x) for x in pit], ks_p=float(ks.pvalue), coverage=c, n=m, coverage_band95=[int(band[0]), int(band[1])])


def power_note(S, rng, reps=2000):
    """Minimum common early->late shift in agreement rate detectable by the CMH test with 80% power (simulated)."""
    def pw(d):
        hit = 0
        for _ in range(reps):
            T = []
            for s in S:
                p = np.clip((s["k1"] + s["k2"] + 1) / (s["n1"] + s["n2"] + 2), 0.02, 0.98)
                T.append(dict(n1=s["n1"], k1=int(rng.binomial(s["n1"], np.clip(p - d / 2, 0, 1))),
                              n2=s["n2"], k2=int(rng.binomial(s["n2"], np.clip(p + d / 2, 0, 1)))))
            num = var = 0.0
            for t in T:
                N = t["n1"] + t["n2"]; K = t["k1"] + t["k2"]
                if N < 2 or K in (0, N): continue
                num += t["k1"] - t["n1"] * K / N; var += t["n1"] * t["n2"] * K * (N - K) / (N ** 2 * (N - 1))
            if var > 0 and stats.chi2.sf((abs(num) - 0.5) ** 2 / var, 1) < 0.05: hit += 1
        return hit / reps
    for d in np.arange(0.02, 0.62, 0.02):
        if pw(d) >= 0.8: return float(round(d, 2))
    return None


def main(evf, runf, outf, seed=SEED):
    ev = pd.read_csv(evf, dtype={"run": str}); runs = pd.read_csv(runf, dtype={"run": str}); rng = np.random.default_rng(seed)
    S = strata(ev, runs)
    res = dict(n_events=int(len(ev)), n_runs=int(len(runs)), S2d=poisson_tests(ev, runs), S2a_primary=van_elteren(S),
               S2a_secondary=homogeneity(S), S2c=predictive(S, rng), mde_relative_decay_80=power_trend(S, rng),
               mde_cmh_80=power_note(S, rng), strata=S)
    a, c, d, v = res["S2a_secondary"], res["S2c"], res["S2d"], res["S2a_primary"]
    res["verdicts"] = dict(
        H_d_within="CONSISTENT" if d["p_within"] is not None and d["p_within"] >= 0.01 else "REJECTED",
        H_d_across="CONSISTENT" if d["p_across"] >= 0.01 else "REJECTED",
        H_a="CONSISTENT" if v["p_two_sided"] >= 0.05 else "REJECTED",
        H_c="CONSISTENT" if (c["ks_p"] >= 0.05 and c["coverage_band95"][0] <= c["coverage"] <= c["coverage_band95"][1]) else "REJECTED")
    json.dump(res, open(outf, "w"), indent=1)
    print(json.dumps(dict(n_events=res["n_events"], verdicts=res["verdicts"], p_within=d["p_within"], p_across=d["p_across"],
                          fisher_comb=a["fisher_combined_p"], cmh_p=a["cmh_p"], shift=a["pooled_late_minus_early"],
                          ks_p=c["ks_p"], coverage=f'{c["coverage"]}/{c["n"]} band {c["coverage_band95"]}', trend_z=v["z"], trend_p=v["p_two_sided"],
                          trend_strata=v["strata_used"], mde_decay=res["mde_relative_decay_80"], mde_cmh=res["mde_cmh_80"]), indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]; seed = int(a[a.index("--seed") + 1]) if "--seed" in a else SEED
    main(a[0], a[1], a[2], seed)
