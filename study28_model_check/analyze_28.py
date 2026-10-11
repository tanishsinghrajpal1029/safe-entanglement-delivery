"""Study 28 locked analysis. Usage: python3 analyze_28.py runs.csv
Every hypothesis, bar and statistic below was fixed after the dev pilot (des_p28_psc, sha ba9d197c) and before any
confirmatory run. Bootstrap: 4,000 resamples of networks (idx) within each hardware, seed 28.
"""
import sys
import numpy as np, pandas as pd
from scipy.stats import beta as betad

B = 4000; RNG = np.random.default_rng(28); BETA = 0.05; BETA1 = 6 * BETA / np.pi ** 2
ION = ("ion2020", "ionproj"); POWERED = [(hw, p) for hw in ION for p in ("p10", "p20")]


def cp_ub(k, n, a=0.05):
    return 1.0 if n == 0 else float(betad.ppf(1 - a, k + 1, n - k)) if k < n else 1.0


def boot_ub(df, stat, a=0.05):
    """one-sided (1-a) upper bound of stat(df) by resampling networks (idx) within hw."""
    groups = {hw: x for hw, x in df.groupby("hw")}; ids = {hw: x.idx.unique() for hw, x in groups.items()}
    vals = []
    for _ in range(B):
        parts = []
        for hw, x in groups.items():
            pick = RNG.choice(ids[hw], len(ids[hw]), replace=True)
            parts.append(pd.concat([x[x.idx == i] for i in pick]))
        vals.append(stat(pd.concat(parts)))
    return float(np.quantile(vals, 1 - a))


def main(path):
    d = pd.read_csv(path); d["sc"] = d.cfg.str.split("|").str[0]; d["p"] = d.cfg.str.split("|").str[1]
    d["fq"] = d.qual / d.oracle_qual.clip(lower=1)
    R = []; P = lambda *a: print(*a, flush=True)
    P(f"rows {len(d)}; blocks {sorted(d.block.unique())}; clamped {int(d.epoch_clamped.sum())}; nepoch {sorted(d.nepoch.unique())}")

    # ---- H1 (primary): validity of the model check, no-stressor and readout-at-bound scenarios
    M = d[d.arm.isin(["kgM", "kgNM"]) & d.sc.isin(["-", "ro"])]
    r1 = float(M.fa_first_t.mean()); ub1 = boot_ub(M, lambda z: float(z.fa_first_t.mean()))
    r2 = float(M.fa_seg_t.mean()); ub2 = boot_ub(M, lambda z: float(z.fa_seg_t.mean()))
    ok = (r1 <= BETA1) and (ub1 <= BETA) and (ub2 <= BETA)
    R.append(("H1", "primary", ok, f"kgM/kgNM runs in '-' and 'ro' ({len(M)}): false first alarm (tested null) rate {r1:.4f} (bar <= {BETA1:.4f}), "
              f"cluster UB {ub1:.4f} (bar <= {BETA}); false segment alarms per run {r2:.4f}, UB {ub2:.4f} (bar <= {BETA})"))

    # ---- H2 (primary): detection in the powered cells (ion, undeclared optimism)
    det = []
    for hw, p in POWERED:
        x = d[(d.hw == hw) & (d.sc == "o0.044_m0") & (d.arm == "kgM") & (d.p == p)]
        det.append((hw, p, float((x.alarms > 0).mean()), len(x), float(x.first_alarm_ep.median())))
    ok = all(r >= 0.9 for _, _, r, _, _ in det)
    R.append(("H2", "primary", ok, "; ".join(f"{hw} {p}: alarm in {r:.3f} of {n} (median epoch {e:.1f})" for hw, p, r, n, e in det) + " (bar >= 0.90 each)"))

    # ---- H3 (primary): harm reduction, bad delivered pairs kgM / kg on the same networks, powered cells
    out = []
    for hw, p in POWERED:
        x = d[(d.hw == hw) & (d.sc == "o0.044_m0")]
        a = x[(x.arm == "kgM") & (x.p == p)][["idx", "bad"]]; b = x[x.arm == "kg"][["idx", "bad"]]
        m = a.merge(b, on="idx", suffixes=("_m", "_k")); m["hw"] = hw
        ratio = m.bad_m.sum() / max(m.bad_k.sum(), 1)
        ub = boot_ub(m, lambda z: z.bad_m.sum() / max(z.bad_k.sum(), 1))
        out.append((hw, p, ratio, ub))
    ok = all(ub <= 0.5 for *_, ub in out)
    R.append(("H3", "primary", ok, "; ".join(f"{hw} {p}: {r:.3f} (UB {u:.3f})" for hw, p, r, u in out) + " (bar: UB <= 0.50 each)"))

    # ---- H4 (primary): delivered-pair risk after the first alarm, powered cells pooled
    x = d[d.hw.isin(ION) & (d.sc == "o0.044_m0") & (d.arm == "kgM")]
    r = x.bad_after_alarm.sum() / max(x.deliv_after_alarm.sum(), 1)
    ub = boot_ub(x, lambda z: z.bad_after_alarm.sum() / max(z.deliv_after_alarm.sum(), 1))
    R.append(("H4", "primary", ub <= 0.01, f"bad after first alarm {int(x.bad_after_alarm.sum())}/{int(x.deliv_after_alarm.sum())} = {r:.5f}; UB {ub:.5f} (bar <= 0.01)"))

    # ---- H5 (primary): no cost without a stressor (ion hardware): fq(kg) - fq(kgM) <= 1 point, each hw and p
    out = []
    for hw, p in POWERED:
        x = d[(d.hw == hw) & (d.sc == "-")]
        a = x[(x.arm == "kgM") & (x.p == p)][["idx", "fq"]]; b = x[x.arm == "kg"][["idx", "fq"]]
        m = a.merge(b, on="idx", suffixes=("_m", "_k")); m["hw"] = hw
        diff = float((m.fq_k - m.fq_m).mean()); ub = boot_ub(m, lambda z: float((z.fq_k - z.fq_m).mean()))
        out.append((hw, p, diff, ub))
    ok = all(ub <= 0.01 for *_, ub in out)
    R.append(("H5", "primary", ok, "; ".join(f"{hw} {p}: {100 * dd:.2f} pts (UB {100 * u:.2f})" for hw, p, dd, u in out) + " (bar: UB <= 1 point)"))

    # ---- H6 (primary): network-wide guarantee, kgN, no stressor: networks with any bad delivered pair
    x = d[(d.arm == "kgN") & (d.sc == "-")]; k, n = int(x.any_bad_all.sum()), len(x); ub = cp_ub(k, n)
    xk = d[(d.arm == "kg") & (d.sc == "-")]
    R.append(("H6", "primary", ub <= 0.05, f"kgN networks with any bad pair: {k}/{n}; CP95 UB {ub:.4f} (bar <= 0.05); [kg reference: {int(xk.any_bad_all.sum())}/{len(xk)}]"))

    # ---- H7 (primary): cost of the network-wide guard, no stressor: fq(kg) - fq(kgN) <= 5 points, every hw
    out = []
    for hw in sorted(d.hw.unique()):
        x = d[(d.hw == hw) & (d.sc == "-")]
        m = x[x.arm == "kgN"][["idx", "fq"]].merge(x[x.arm == "kg"][["idx", "fq"]], on="idx", suffixes=("_n", "_k")); m["hw"] = hw
        diff = float((m.fq_k - m.fq_n).mean()); ub = boot_ub(m, lambda z: float((z.fq_k - z.fq_n).mean()))
        out.append((hw, diff, ub))
    ok = all(ub <= 0.05 for *_, ub in out)
    R.append(("H7", "primary", ok, "; ".join(f"{hw}: {100 * dd:.2f} pts (UB {100 * u:.2f})" for hw, dd, u in out) + " (bar: UB <= 5 points)"))

    # ---- S1 (secondary): free test data versus a 16-point tomography campaign: fq(kgM p10) >= fq(m16) - 5 points
    out = []
    for hw in ION:
        a = d[(d.hw == hw) & (d.sc == "o0.044_m0") & (d.arm == "kgM") & (d.p == "p10")].fq.mean()
        b = d[(d.hw == hw) & (d.sc == "o0.044_m16")].fq.mean(); c = d[(d.hw == hw) & (d.sc == "o0.044_orc")].fq.mean()
        out.append((hw, a, b, c))
    R.append(("S1", "secondary", all(a >= b - 0.05 for _, a, b, _ in out),
              "; ".join(f"{hw}: kgM p10 {a:.3f} vs m16 {b:.3f} (oracle {c:.3f})" for hw, a, b, c in out) + " (bar: kgM >= m16 - 0.05)"))

    # ---- S2 (secondary): the e-process beats the naive per-epoch detector in the powered cells
    out = []
    for hw, p in POWERED:
        x = d[(d.hw == hw) & (d.sc == "o0.044_m0") & (d.p == p)]
        am, ap = (x[x.arm == "kgM"].alarms > 0).mean(), (x[x.arm == "kgP"].alarms > 0).mean()
        bm, bp = x[x.arm == "kgM"].bad.sum(), x[x.arm == "kgP"].bad.sum()
        out.append((hw, p, am, ap, bm, bp))
    R.append(("S2", "secondary", all(bm < bp for *_, bm, bp in out),
              "; ".join(f"{hw} {p}: alarm {am:.2f} vs {ap:.2f}, bad {int(bm)} vs {int(bp)}" for hw, p, am, ap, bm, bp in out) + " (bar: kgM bad < kgP bad, each cell)"))

    # ---- S3 (secondary, predicted null): no detection where the theory predicts no power
    x = d[d.arm.isin(["kgM", "kgNM"]) & (d.hw.isin(["nv2", "siv"]) | d.sc.isin(["n0.184_a", "fault"]))]
    rate = float((x.alarms > 0).mean())
    R.append(("S3", "secondary (prediction)", rate <= 0.10, f"alarm rate in unpowered cells (NV, SiV; persistent noise; fault): {rate:.4f} over {len(x)} runs (prediction <= 0.10)"))

    # ---- S4 (secondary): the network certificate stays valid (replication of Study 27 under feedback)
    for tag in ("p10", "p20"):
        k, n = int(d[f"{tag}_viol"].sum()), len(d); ub = cp_ub(k, n)
        R.append((f"S4_{tag}", "secondary", ub <= 0.05, f"network certificate violated in {k}/{n} runs; CP95 UB {ub:.4f} (bar <= 0.05)"))

    P("\n== VERDICTS ==")
    for h, tier, ok, s in R: P(f"{h:6s} {tier:22s} {'PASS' if ok else 'FAIL'}  {s}")

    # ---- descriptive
    P("\n== D1 powered cells: risk, per-user risk, margins, throughput ==")
    x = d[d.hw.isin(ION) & d.sc.str.startswith("o0.044")]
    g = x.groupby(["hw", "sc", "arm", "p"]).agg(n=("run", "size"), bad=("bad", "sum"), dl=("delivered", "sum"), ub=("users_bad_all", "sum"),
                                                ut=("users_total", "sum"), ep=("first_alarm_ep", "median"), dec=("dec_final", "mean"), fq=("fq", "mean"))
    g["r_%"] = 100 * g.bad / g.dl.clip(lower=1); g["pu_%"] = 100 * g.ub / g.ut
    P(g[["n", "r_%", "pu_%", "ep", "dec", "fq"]].round(3).to_string())
    P("\n== D2 alarm rates, all cells (feedback arms) ==")
    P(d[d.arm.isin(["kgM", "kgNM", "kgP"])].groupby(["hw", "sc", "arm", "p"]).alarms.apply(lambda s: (s > 0).mean()).unstack(["arm", "p"]).round(3).to_string())
    P("\n== D3 throughput (fraction of oracle), no stressor ==")
    P(d[d.sc == "-"].groupby(["hw", "arm", "p"]).fq.mean().unstack(["arm", "p"]).round(4).to_string())


if __name__ == "__main__":
    main(sys.argv[1])
