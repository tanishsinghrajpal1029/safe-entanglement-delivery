"""Study 18C v7: controlled-headroom sweep to measure the per-attempt error model (development, NOT a final run).

Motivation (des_v6_mac, SUMMARY sha 0578583b...; ledger E22): with the confidence-bound controller, dev-selected
settings that met Clopper-Pearson r_cond <= 1% on dev paths gave EVAL r_cond up to 6% on fresh paths. Bad deliveries
concentrate on paths whose mean true F is below 0.9, and eval path sets had MORE such paths (91% vs 84%; 97% vs 91%).
Hypothesis: threshold delivery is a false-discovery problem. Each sub-threshold attempt is delivered with some
probability alpha(h) set by the estimator error; r_cond = P(bad | delivered) then depends on the BASE RATE of
sub-threshold attempts, which per-decision confidence (z) cannot control.

v7 isolates the per-attempt error model. One path per run; all L links share Werner fidelity F0, swept across the
threshold. Every attempt is logged into bins of h = F_true - 0.9 (width 0.0025, [-0.06, 0.06]) with the number of
attempts and deliveries, plus per-run moments of the estimator error e = F_hat(point) - F_true and of the
confidence offset F_hat(point) - F_hat(low).
Grid: cell {ion_2020 L2, ion_proj L3} (purify) x g {0, 1e-5, 1e-4} x F0 (13 values, cell-specific) x
  est {static, ols_reset} x z {0, 1, 2, 3} x 3 replicate seeds; rho 0.3, T 100 s, m 0, load 0.9, D 0.25 s.
  (g = 0 is run as 1e-9: no drift within the horizon.)
Outputs: <outdir>/bins.csv (run, h-bin, attempts, delivered), runs.csv (one row per run). Resumable by run id.
"""
import argparse, hashlib, itertools, json, platform, sys, time
import multiprocessing as mp
from pathlib import Path
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v6 as v6

EDGES = np.round(np.arange(-0.06, 0.06001, 0.0025), 6)
F0GRID = {"ion_2020": np.round(np.linspace(0.925, 0.961, 13), 4), "ion_proj": np.round(np.linspace(0.955, 0.985, 13), 4)}
CELLS = {"ion_2020": 2, "ion_proj": 3}
GS = (1e-9, 1e-5, 1e-4); ESTS = ("static", "ols_reset"); ZS = (0.0, 1.0, 2.0, 3.0); REPS = (0, 1, 2)
RHO, T, M, LOAD, D, H = 0.3, 100.0, 0.0, 0.9, 0.25, 300.0


class RunV7(v6.RunV6):
    def __init__(s, *a, **k):
        super().__init__(*a, **k)
        s.att = np.zeros(len(EDGES) + 1, int); s.dlv = np.zeros(len(EDGES) + 1, int); s.err = []; s.off = []

    def serve(s, t0, deadline):
        t = t0; pairs = 0; att = 0; P = s.P
        while True:
            att += 1; lam = s.lam_true(t)
            d1, w1 = s.chain(t); pairs += s.L
            d2, w2 = s.chain(d1); pairs += s.L; hold = d2 - d1
            Ft = v4.dej(v4.chainF(lam, P, s.L, w1 + hold), v4.chainF(lam, P, s.L, w2), P["e"]); tdone = d2
            if tdone > deadline: return deadline, "miss", None, pairs
            lh, se = s.est_se(tdone); ok = not np.any(np.isnan(lh))
            if ok:
                lp = np.clip(lh, 0, 1); ll = np.clip(lh - s.z * se, 0, 1)
                Fp = v4.dej(v4.chainF(lp, P, s.L, w1 + hold), v4.chainF(lp, P, s.L, w2), P["e"])
                Fl = v4.dej(v4.chainF(ll, P, s.L, w1 + hold), v4.chainF(ll, P, s.L, w2), P["e"])
                if tdone >= s.warm: s.err.append(Fp - Ft); s.off.append(Fp - Fl)
            else:
                Fl = 0.0
            dl = Fl >= 0.9 + s.m
            if tdone >= s.warm:
                b = int(np.searchsorted(EDGES, Ft - 0.9, side="right")); s.att[b] += 1; s.dlv[b] += int(dl)
            if dl: return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


def run_one(t):
    cell, g, F0, est, z, rep = t
    L = CELLS[cell]; P = v4.PRE[cell]; lam0 = np.full(L, (4 * F0 - 1) / 3)
    rid = hashlib.sha256(f"v7|{cell}|{g}|{F0}|{est}|{z}|{rep}".encode()).hexdigest()[:12]
    seed = [int(hashlib.sha256(f"v7seed|{cell}|{g}|{F0}|{rep}".encode()).hexdigest()[:8], 16), 18831]
    phase = (rep + 0.5) / len(REPS) * 0.02 / g
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV7(P, L, True, g, LOAD, "fixed", RHO, T, M, D, H, seed, mu=mu, lam0=lam0, phase=phase, est=est, z=z)
    o = r.go(); d = pd.DataFrame(o, columns="t res F pairs latency".split()); x = d[d.res == "deliver"]
    err = np.array(r.err) if r.err else np.array([np.nan]); off = np.array(r.off) if r.off else np.array([np.nan])
    run = dict(run=rid, cell=cell, L=L, g=g, F0=F0, est=est, z=z, rep=rep, requests=len(d), delivered=len(x),
               qual=int((x.F >= 0.9).sum()), bad=int((x.F < 0.9).sum()), attempts=int(r.att.sum()),
               attempts_above=int(r.att[np.searchsorted(EDGES, 0.0, side="right"):].sum()),
               err_mean=float(np.nanmean(err)), err_sd=float(np.nanstd(err)), off_mean=float(np.nanmean(off)),
               err_q05=float(np.nanquantile(err, 0.05)), err_q95=float(np.nanquantile(err, 0.95)))
    lo = np.concatenate([[-np.inf], EDGES]); hi = np.concatenate([EDGES, [np.inf]])
    bins = [dict(run=rid, h_lo=lo[i], h_hi=hi[i], attempts=int(r.att[i]), delivered=int(r.dlv[i]))
            for i in range(len(lo)) if r.att[i] > 0]
    return run, bins


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default="des_v7"); ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(); out = Path(a.outdir); out.mkdir(exist_ok=True)
    tasks = [(c, g, float(F0), e, z, rp) for c in CELLS for g in GS for F0 in F0GRID[c] for e in ESTS for z in ZS for rp in REPS]
    if a.smoke: tasks = [("ion_proj", 1e-4, 0.97, e, 2.0, 0) for e in ESTS]
    runs_csv, bins_csv = out / "runs.csv", out / "bins.csv"
    if runs_csv.exists():
        have = set(pd.read_csv(runs_csv).run)
        tasks = [t for t in tasks if hashlib.sha256("v7|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12] not in have]
    t0 = time.time()
    (out / f"run_meta_{int(t0)}.json").write_text(json.dumps(dict(
        script="drift_queue_des_v7.py", self_sha=hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
        v6_sha=hashlib.sha256(open(v6.__file__, "rb").read()).hexdigest(), python=platform.python_version(),
        numpy=np.__version__, workers=a.workers, smoke=a.smoke, n_tasks=len(tasks)), indent=1))
    print(f"v7: {len(tasks)} runs on {a.workers} workers", flush=True); k = 0
    with mp.Pool(a.workers) as pool:
        for run, bins in pool.imap_unordered(run_one, tasks, chunksize=1):
            pd.DataFrame(bins).to_csv(bins_csv, mode="a", header=not bins_csv.exists(), index=False)
            pd.DataFrame([run]).to_csv(runs_csv, mode="a", header=not runs_csv.exists(), index=False); k += 1
            if k % 100 == 0 or k == len(tasks): print(f"  {k}/{len(tasks)} runs, {time.time() - t0:.0f} s", flush=True)
    R = pd.read_csv(runs_csv)
    print(R.groupby(["cell", "g", "est", "z"])[["qual", "bad", "delivered"]].sum().assign(
        r_cond_pct=lambda x: (100 * x.bad / x.delivered.clip(lower=1)).round(3)).to_string())
    print("runs.csv sha256:", hashlib.sha256(open(runs_csv, "rb").read()).hexdigest())
    print(f"elapsed {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
