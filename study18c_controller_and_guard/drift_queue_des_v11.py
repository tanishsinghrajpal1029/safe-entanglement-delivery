"""Study 18C v11: v9 controller with small-sample-honest (Agresti-Coull) standard errors (development, NOT final).

Problem found in v9 (partial results, ledger E27): right after a re-alignment the 'ols_reset'/'reset' window holds few
parity records. When all n parities are even the Wald variance (1 - (r*lambda_hat)^2)/n collapses (v6 floored it at
1/n^2 in p-space), so the controller is 'very sure' exactly when it knows least: ion_2020, g = 1e-5, ols_reset gave
r_cond 6.2% (adaptive) and 37.8% (fixed z=3). P(all 20 parities even | lambda = 0.92) = 0.44.
Fix (standard): Agresti-Coull variance for the even-parity probability, p~ = (k + 2)/(n + 4),
Var(p_hat) ~ p~(1-p~)/(n + 4), so Var(lambda_hat) = 4 Var(p_hat)/r^2. Used for 'static'/'reset' SE and as the per-bin
variance in the weighted-LS fit of 'ols_reset'. Point estimates are unchanged. Everything else is v9.
Same tasks, seeds and populations as v9 (run ids are tagged v11, so v9 and v11 compare path-by-path).
"""
import argparse, hashlib, json, math, platform, sys, time
import multiprocessing as mp
from pathlib import Path
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v6 as v6
import drift_queue_des_v7 as v7
import drift_queue_des_v9 as v9


def ac_var_lambda(k, n, r):
    pt = (k + 2.0) / (n + 4.0)
    return 4.0 * pt * (1.0 - pt) / (n + 4.0) / (r * r)


class RunV11(v9.RunV9):
    def est_se(s, t):
        L = s.L; r = (1 - 2 * s.P["q"]) ** 2
        a = max(0.0, t - s.T) if s.est == "static" else max(0.0, t - s.T, t - ((t + s.phase) % s.Tre))
        W = t - a; lh = np.full(L, np.nan); se = np.full(L, np.nan)
        if W <= 0: return lh, se
        if s.est in ("static", "reset"):
            rt = s._rate_time(a, t); lb = np.clip(s.lam_avg(a, t), 0, 1)
            for i in range(L):
                n = s.rng.poisson(rt)
                if n < 5: continue
                k = s.rng.binomial(n, (1 + r * lb[i]) / 2)
                lh[i] = (2 * k / n - 1) / r; se[i] = math.sqrt(ac_var_lambda(k, n, r))
            return lh, se
        K = 4; edges = np.linspace(a, t, K + 1); mids = (edges[:-1] + edges[1:]) / 2 - t
        rts = [s._rate_time(edges[j], edges[j + 1]) for j in range(K)]
        lbs = [np.clip(s.lam_avg(edges[j], edges[j + 1]), 0, 1) for j in range(K)]
        for i in range(L):
            ns = np.array([s.rng.poisson(rt) for rt in rts])
            ks = np.array([s.rng.binomial(n, (1 + r * lb[i]) / 2) if n > 0 else 0 for n, lb in zip(ns, lbs)])
            if ns.sum() < 5: continue
            ok = ns >= 5
            if ok.sum() < 2:
                N, Kk = int(ns.sum()), int(ks.sum())
                lh[i] = (2 * Kk / N - 1) / r; se[i] = math.sqrt(ac_var_lambda(Kk, N, r)); continue
            y = (2 * ks[ok] / ns[ok] - 1) / r; xm = mids[ok]
            v = np.array([ac_var_lambda(k, n, r) for k, n in zip(ks[ok], ns[ok])])
            w = 1 / v; X = np.column_stack([np.ones_like(xm), xm]); A = X.T @ (X * w[:, None])
            cov = np.linalg.inv(A); coef = cov @ (X.T @ (w * y))
            lh[i] = coef[0]; se[i] = math.sqrt(max(cov[0, 0], 0.0))
        return lh, se


def run_one(t):
    pop, cell, g, est, method, idx = t
    L = v9.CELLS[cell]; P = v4.PRE[cell]
    if pop == "A":
        lam0, ph = v4.draw_paths(P, L, 32, [18822, L])[idx]; phase = ph * 0.02 / g; F0 = float("nan")
        seed = [int(hashlib.sha256(f"v9A|{cell}|{g}|{idx}".encode()).hexdigest()[:8], 16), 18841]
    else:
        F0 = float(v7.F0GRID[cell][idx]); lam0 = np.full(L, (4 * F0 - 1) / 3); phase = 0.5 * 0.02 / g
        seed = [int(hashlib.sha256(f"v9B|{cell}|{g}|{F0}".encode()).hexdigest()[:8], 16), 18842]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV11(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase, est=est, method=method)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    orr = v6.RunV6(P, L, True, g, v9.LOAD, "none", 0.0, 1.0, 0.0, D, v9.H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase)
    oo = pd.DataFrame(orr.go(), columns="t res F pairs latency".split()); ox = oo[oo.res == "deliver"]
    zs = np.array(r.zs) if r.zs else np.array([np.nan])
    return dict(run=run_id(t), pop=pop, cell=cell, L=L, g=g, est=est, method=method, idx=idx, F0=F0,
                requests=len(o), delivered=len(x), qual=int((x.F >= 0.9).sum()), bad=int((x.F < 0.9).sum()),
                oracle_qual=int((ox.F >= 0.9).sum()), z_inf_frac=float(np.mean(np.isinf(zs))),
                z_med=float(np.median(np.minimum(zs, 99))))


D = v9.D


def run_id(t):
    return hashlib.sha256("v11|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def tasks():
    ts = [["A", c, g, e, m, i] for c in v9.CELLS for g in v9.GS for e in v9.ESTS for m in v9.METHODS for i in range(32)]
    ts += [["B", c, g, e, m, i] for c in v9.CELLS for g in v9.GS for e in v9.ESTS for m in v9.METHODS for i in range(13)]
    return ts


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write-tasks"); ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.write_tasks:
        with open(a.write_tasks, "w") as f:
            for t in tasks(): f.write(json.dumps(t) + "\n")
        print(f"wrote {len(tasks())} tasks -> {a.write_tasks}")
    if a.smoke:
        for t in (["A", "ion_2020", 1e-5, "ols_reset", "fixed3", 0], ["B", "ion_proj", 1e-5, "ols_reset", "adaptive", 10]):
            print(run_one(t))


if __name__ == "__main__":
    main()
