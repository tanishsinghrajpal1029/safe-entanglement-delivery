"""Study 18C v6: confidence-bound (LCB) delivery controller + per-path outputs (development, NOT a final run).

Why v6 (diagnosed from des_v5_mac, SUMMARY sha 0ee68bf7...):
  v5 'reset'/'ols_reset' estimators were infeasible almost everywhere although they are less biased than 'static'.
  Diagnosis: they use only post-re-alignment data, so right after a re-alignment the window holds very few pairs
  (n >= 5). With a FIXED margin the controller trusts those estimates; e.g. at lambda=0.93, P(all of n=10 parities
  even) = 0.965^10 = 0.70, so lambda_hat = 1 and the pair is delivered whatever the margin. Dev r_cond for 'reset'
  even RISES with margin (0.14 -> 0.65 at rho 0.3, T 100). A fixed margin is unsafe for variable-precision
  estimators; the decision must use the estimator's own uncertainty.
v6 controller: per link, lambda_low = lambda_hat - z * SE, with SE from the parity variance (1-(r lambda)^2)/(n r^2)
  ('static','reset') or from the weighted-LS intercept covariance ('ols_reset'); deliver iff
  F(lambda_low) >= 0.9 + m. (F is increasing in every link lambda, so this is a per-link conservative bound.)
Grid: est {static,reset,ols_reset} x z {1,2,3} x rho {0.1,0.3,0.5} x T {10,30,100,300} s x m {0,0.005};
  deadline 0.25 s only (v5 P4: D 0.25 vs 1.0 changed nothing by more than 0.011). Combos as v5 (load 0.9).
Selection: Clopper-Pearson 95% upper bound on pooled dev r_cond <= 1% (v5 'ucb'), maximise dev qualified rate.
Paths: 32 dev + 32 eval, fresh draws (seeds 18821/18822). Oracle is run on BOTH dev and eval paths; every cell
  writes PER-PATH rows (qual, bad, delivered, oracle mean true F over attempts) so the loss can be studied as a
  function of each path's headroom above 0.9.
Outputs in <outdir>: dev_paths.csv, eval_paths.csv (resumable), selection.csv, SUMMARY.csv, run_meta_*.json.
"""
import argparse, hashlib, itertools, json, platform, sys, time
import multiprocessing as mp
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import beta
import drift_queue_des as v4
import drift_queue_des_v5 as v5

ESTS = ("static", "reset", "ols_reset"); ZS = (1.0, 2.0, 3.0); RHO = (0.1, 0.3, 0.5)
TW = (10.0, 30.0, 100.0, 300.0); MARG = (0.0, 0.005); D = 0.25
COMBOS = [(c, g, 0.9) for c in v4.CELLS for g in (1e-5, 1e-4)]
HORIZON, NPATHS = 300.0, 32


class RunV6(v5.RunV5):
    def __init__(s, *a, z=2.0, **k):
        super().__init__(*a, **k); s.z = z; s.trueF = []

    def est_se(s, t):
        """Return (lambda_hat, se) per link; nan where fewer than 5 pairs."""
        L = s.L; r = (1 - 2 * s.P["q"]) ** 2
        if s.est == "static":
            a = max(0.0, t - s.T)
        else:
            a = max(0.0, t - s.T, t - ((t + s.phase) % s.Tre))
        W = t - a; lh = np.full(L, np.nan); se = np.full(L, np.nan)
        if W <= 0: return lh, se
        if s.est in ("static", "reset"):
            rt = s._rate_time(a, t); lb = np.clip(s.lam_avg(a, t), 0, 1)
            for i in range(L):
                n = s.rng.poisson(rt)
                if n < 5: continue
                k = s.rng.binomial(n, (1 + r * lb[i]) / 2); x = (2 * k / n - 1) / r
                lh[i] = x; se[i] = np.sqrt(max(1 - (r * min(max(x, 0), 1)) ** 2, 1.0 / n) / n) / r
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
                N = ns.sum(); x = (2 * ks.sum() / N - 1) / r
                lh[i] = x; se[i] = np.sqrt(max(1 - (r * min(max(x, 0), 1)) ** 2, 1.0 / N) / N) / r; continue
            y = (2 * ks[ok] / ns[ok] - 1) / r; xm = mids[ok]
            v = np.array([max(1 - (r * min(max(yy, 0), 1)) ** 2, 1.0 / n) / (n * r * r) for yy, n in zip(y, ns[ok])])
            w = 1 / v; X = np.column_stack([np.ones_like(xm), xm]); A = X.T @ (X * w[:, None])
            cov = np.linalg.inv(A); coef = cov @ (X.T @ (w * y))
            lh[i] = coef[0]; se[i] = np.sqrt(max(cov[0, 0], 0.0))
        return lh, se

    def serve(s, t0, deadline):
        t = t0; pairs = 0; att = 0; P = s.P
        while True:
            att += 1; lam = s.lam_true(t)
            d1, w1 = s.chain(t); pairs += s.L
            d2, w2 = s.chain(d1); pairs += s.L; hold = d2 - d1
            Ft = v4.dej(v4.chainF(lam, P, s.L, w1 + hold), v4.chainF(lam, P, s.L, w2), P["e"]); tdone = d2
            s.trueF.append(Ft)
            if tdone > deadline: return deadline, "miss", None, pairs
            if s.or_:
                ll = s.lam_true(tdone); ok = True
            else:
                lh, se = s.est_se(tdone); ok = not np.any(np.isnan(lh))
                ll = np.clip(lh - s.z * se, 0, 1) if ok else None
            Fh = v4.dej(v4.chainF(ll, P, s.L, w1 + hold), v4.chainF(ll, P, s.L, w2), P["e"]) if ok else 0.0
            if Fh >= 0.9 + s.m: return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


def run_paths(ci, which, est, z, rho, T, m, oracle=False):
    (pre, L, pur), g, load = COMBOS[ci]; P = v4.PRE[pre]; assert pur
    paths = v4.draw_paths(P, L, NPATHS, [18821 if which == "dev" else 18822, L])
    seed0 = int(hashlib.sha256(f"v6|{which}|{pre}|{L}|{g}|{load}".encode()).hexdigest()[:8], 16)
    rows = []
    for j, (lam0, ph) in enumerate(paths):
        mu = v4.service_mu(P, L, True, lam0, D)
        r = RunV6(P, L, True, g, load, "none" if oracle else "fixed", rho, T, m, D, HORIZON, [seed0, j],
                  oracle=oracle, mu=mu, lam0=lam0, phase=ph * 0.02 / g, est=est, z=z)
        o = r.go(); d = pd.DataFrame(o, columns="t res F pairs latency".split()); x = d[d.res == "deliver"]
        rows.append(dict(combo=ci, preset=pre, L=L, drift_g=g, which=which, est="oracle" if oracle else est,
                         z=z, rho=rho, T=T, margin=m, path=j, qual=int((x.F >= 0.9).sum()), bad=int((x.F < 0.9).sum()),
                         delivered=len(x), n=len(d), miss=int((d.res == "miss").sum()),
                         meanF_attempts=float(np.mean(r.trueF)) if r.trueF else float("nan"),
                         lam0_min=float(np.min(lam0))))
    return rows


def task(t):
    return run_paths(*t)


def cp_upper(bad, n):
    return 1.0 if n == 0 or bad >= n else float(beta.ppf(0.95, bad + 1, n - bad))


def run_pool(tasks, out_csv, workers):
    keycols = ["combo", "which", "est", "z", "rho", "T", "margin"]
    if out_csv.exists():
        have = set(map(tuple, pd.read_csv(out_csv)[keycols].astype(str).drop_duplicates().values.tolist()))
        def key(t):
            ci, which, est, z, rho, T, m = t[:7]; o = len(t) > 7 and t[7]
            return tuple(map(str, (ci, which, "oracle" if o else est, z, rho, T, m)))
        tasks = [t for t in tasks if key(t) not in have]
    print(f"{len(tasks)} cells to run -> {out_csv}", flush=True); t0 = time.time(); k = 0
    with mp.Pool(workers) as pool:
        for rows in pool.imap_unordered(task, tasks, chunksize=1):
            pd.DataFrame(rows).to_csv(out_csv, mode="a", header=not out_csv.exists(), index=False); k += 1
            if k % 25 == 0 or k == len(tasks): print(f"  {k}/{len(tasks)} cells, {time.time() - t0:.0f} s", flush=True)
    return pd.read_csv(out_csv)


def main():
    global NPATHS, HORIZON
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default="des_v6"); ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(); out = Path(a.outdir); out.mkdir(exist_ok=True)
    if (out / "SUMMARY.csv").exists(): sys.exit(f"{out}/SUMMARY.csv exists; refusing to overwrite")
    combos = range(len(COMBOS)); grid = list(itertools.product(ESTS, ZS, RHO, TW, MARG))
    if a.smoke:
        combos = [3]; grid = [(e, 2.0, 0.3, 30.0, 0.0) for e in ESTS]
        NPATHS, HORIZON = 2, 60.0  # workers re-import the module: smoke values only reach them via fork
    t0 = time.time()
    (out / f"run_meta_{int(t0)}.json").write_text(json.dumps(dict(
        script="drift_queue_des_v6.py", self_sha=hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
        v5_sha=hashlib.sha256(open(v5.__file__, "rb").read()).hexdigest(),
        v4_sha=hashlib.sha256(open(v4.__file__, "rb").read()).hexdigest(), python=platform.python_version(),
        numpy=np.__version__, paths=NPATHS, horizon=HORIZON, smoke=a.smoke, workers=a.workers), indent=1))
    print(f"v6: {len(combos)} combos x {len(grid)} settings; {NPATHS} dev + {NPATHS} eval paths; {a.workers} workers", flush=True)
    dev_tasks = [(ci, "dev", "oracle", 0.0, 0.0, 1.0, 0.0, True) for ci in combos]
    dev_tasks += [(ci, "dev", e, z, rho, T, m) for ci in combos for (e, z, rho, T, m) in grid]
    dev = run_pool(dev_tasks, out / "dev_paths.csv", a.workers)
    agg = dev.groupby(["combo", "est", "z", "rho", "T", "margin"], as_index=False)[["qual", "bad", "delivered"]].sum()
    agg["ucb"] = [cp_upper(b, n) for b, n in zip(agg.bad, agg.delivered)]
    sel = []
    for (ci, est), g in agg[agg.est != "oracle"].groupby(["combo", "est"]):
        c = g[g.ucb <= 0.01]
        if len(c) == 0: sel.append(dict(combo=ci, est=est, feasible=False)); continue
        b = c.sort_values(["qual", "rho", "z"], ascending=[False, True, False]).iloc[0]
        sel.append(dict(combo=ci, est=est, feasible=True, z=b.z, rho=b.rho, T=b["T"], margin=b.margin,
                        dev_qual=int(b.qual), dev_bad=int(b.bad), dev_delivered=int(b.delivered)))
    sel = pd.DataFrame(sel); sel.to_csv(out / "selection.csv", index=False)
    ev_tasks = [(ci, "eval", "oracle", 0.0, 0.0, 1.0, 0.0, True) for ci in combos]
    ev_tasks += [(int(r.combo), "eval", r.est, float(r.z), float(r.rho), float(r["T"]), float(r.margin))
                 for _, r in sel[sel.feasible].iterrows()]
    ev = run_pool(ev_tasks, out / "eval_paths.csv", a.workers)
    eo = ev[ev.est == "oracle"].groupby("combo").qual.sum()
    rows = []
    for _, r in sel.iterrows():
        (pre, L, _), g, load = COMBOS[int(r.combo)]
        base = dict(combo=int(r.combo), preset=pre, L=L, drift_g=g, est=r.est, oracle_eval_qual=int(eo[r.combo]))
        if not r.feasible: rows.append({**base, "note": "no dev setting met ucb<=1%"}); continue
        e = ev[(ev.combo == r.combo) & (ev.est == r.est) & (ev.z == r.z) & (ev.rho == r.rho) & (ev["T"] == r["T"]) &
               (ev.margin == r.margin)][["qual", "bad", "delivered"]].sum()
        rows.append({**base, "z": r.z, "rho": r.rho, "T": r["T"], "margin": r.margin,
                     "EVAL_frac_of_oracle": round(e.qual / max(eo[r.combo], 1), 4), "EVAL_bad": int(e.bad),
                     "EVAL_delivered": int(e.delivered), "EVAL_r_cond_pct": round(100 * e.bad / max(e.delivered, 1), 3),
                     "EVAL_ucb_pct": round(100 * cp_upper(int(e.bad), int(e.delivered)), 3), "note": ""})
    S = pd.DataFrame(rows); S.to_csv(out / "SUMMARY.csv", index=False)
    pd.set_option("display.width", 250)
    print(S.drop(columns=["combo"]).to_string(index=False))
    print("SUMMARY.csv sha256:", hashlib.sha256(open(out / "SUMMARY.csv", "rb").read()).hexdigest())
    print(f"elapsed {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
