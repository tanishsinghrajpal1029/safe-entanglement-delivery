"""Study 18C v5: sensitivity / artifact check of the v4 DES result (development, NOT a final run).

v4 (des_v4_mac/ALL.csv, sha a966c00f...) found calibrated delivery at <=32% of the oracle, ~0% at drift g=1e-4,
opportunistic calibration never feasible, and EVAL r_cond up to 4.6% after a dev point-estimate selection.
v4 design weaknesses that could create that result (each addressed here):
  W1 grid edges binding: rho max 0.1 chosen often; margin min 0.0125 chosen often; window T only {100,300} s
     although the docstring promised {30,100,300} and drift re-aligns every 200 s at g=1e-4.
  W2 estimator naive: sliding window ignores the KNOWN re-alignment instants and the linear drift.
  W3 selection: point estimate r_cond<=1% on 8 dev paths (winner's curse; zero-delivery settings 'pass').
  W4 deadline 0.25 s tight (oracle itself misses 10-58%).
v5 changes (everything else imported unchanged from drift_queue_des.py v4, sha cc954805...):
  grid    rho {0.03,0.1,0.3} x T {10,30,100,300} s x margin {0.005,0.0125,0.025,0.04,0.06}   (fixed policy only;
          v4 showed hybrid == fixed within noise and opportunistic infeasible everywhere)
  est     static (v4) | reset (window truncated at the last known re-alignment) |
          ols_reset (reset window split into 4 equal bins; Binomial parities per bin with the bin-average true
          lambda, which for linear drift equals lambda at the bin midpoint; weighted LS line extrapolated to now)
  deadline D in {0.25, 1.0} s
  select  'point' (v4 rule, but >=50 dev deliveries required) and 'ucb' (Clopper-Pearson 95% upper bound on dev
          r_cond <= 1%; needs >=299 clean deliveries)
  paths   16 dev + 16 eval, FRESH draws (seeds 18811/18812), so v4 eval paths are never used for selection.
Combos: both cells (ion_2020 L2 purify; ion_proj L3 purify) x g {1e-5,1e-4} x load 0.9.
Outputs (refuses to overwrite finished files; resumable): <outdir>/dev_cells.csv, eval_cells.csv, SUMMARY.csv.
"""
import argparse, hashlib, itertools, json, math, os, platform, sys, time
import multiprocessing as mp
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import beta
import drift_queue_des as v4

RHO = (0.03, 0.1, 0.3); TW = (10.0, 30.0, 100.0, 300.0); MARG = (0.005, 0.0125, 0.025, 0.04, 0.06)
ESTS = ("static", "reset", "ols_reset"); DEADLINES = (0.25, 1.0)
COMBOS = [(c, g, 0.9) for c in v4.CELLS for g in (1e-5, 1e-4)]
MIN_DELIV_POINT = 50


class RunV5(v4.Run):
    def __init__(s, *a, est="static", **k):
        super().__init__(*a, **k); s.est = est

    def _rate_time(s, a, b):
        W = b - a; busy = s.busy_in(a, b); idle = W - busy
        return ((s.rho * s.P["R"] * W if s.pol in ("fixed", "hybrid") else 0) +
                (s.P["R"] * idle if s.pol in ("opportunistic", "hybrid") else 0))

    def estimate(s, t):
        if s.or_ or s.est == "static":
            return super().estimate(t)
        last_reset = t - ((t + s.phase) % s.Tre)
        a = max(0.0, t - s.T, last_reset); W = t - a
        if W <= 0: return np.full(s.L, np.nan)
        r = (1 - 2 * s.P["q"]) ** 2
        if s.est == "reset":
            n_rt = s._rate_time(a, t); lb = np.clip(s.lam_avg(a, t), 0, 1); out = np.empty(s.L)
            for i in range(s.L):
                n = s.rng.poisson(n_rt)
                if n < 5: out[i] = np.nan; continue
                k = s.rng.binomial(n, (1 + r * lb[i]) / 2); out[i] = (2 * k / n - 1) / r
            return out
        # ols_reset
        K = 4; edges = np.linspace(a, t, K + 1); mids = (edges[:-1] + edges[1:]) / 2 - t
        rts = [s._rate_time(edges[j], edges[j + 1]) for j in range(K)]
        lbs = [np.clip(s.lam_avg(edges[j], edges[j + 1]), 0, 1) for j in range(K)]
        out = np.empty(s.L)
        for i in range(s.L):
            ns = np.array([s.rng.poisson(rt) for rt in rts])
            ks = np.array([s.rng.binomial(n, (1 + r * lb[i]) / 2) if n > 0 else 0 for n, lb in zip(ns, lbs)])
            ok = ns >= 5
            if ns.sum() < 5: out[i] = np.nan; continue
            if ok.sum() < 2:   # cannot fit a slope: fall back to pooled estimate
                out[i] = (2 * ks.sum() / ns.sum() - 1) / r; continue
            y = (2 * ks[ok] / ns[ok] - 1) / r; x = mids[ok]; w = ns[ok].astype(float)
            X = np.column_stack([np.ones_like(x), x]); WX = X * w[:, None]
            coef = np.linalg.solve(X.T @ WX, WX.T @ y); out[i] = coef[0]
        return out


def run_cell5(P, L, pur, g, load, rho, T, m, D, H, paths, seed0, est, oracle=False):
    q = bad = dl = miss = n = 0; lat = []
    for j, (lam0, ph) in enumerate(paths):
        mu = v4.service_mu(P, L, pur, lam0, D)
        r = RunV5(P, L, pur, g, load, "none" if oracle else "fixed", rho, T, m, D, H, [seed0, j],
                  oracle=oracle, mu=mu, lam0=lam0, phase=ph * 0.02 / g, est=est)
        o = r.go(); d = pd.DataFrame(o, columns="t res F pairs latency".split()); x = d[d.res == "deliver"]
        q += int((x.F >= 0.9).sum()); bad += int((x.F < 0.9).sum()); dl += len(x)
        miss += int((d.res == "miss").sum()); n += len(d); lat += list(d.latency)
    return dict(qual=q, bad=bad, delivered=dl, n=n, miss=miss / max(n, 1),
                qual_per_s=q / (H * len(paths)), r_cond=bad / max(dl, 1),
                latency_ms=1e3 * float(np.mean(lat)) if lat else float("nan"))


def cp_upper(bad, n, a=0.05):
    return 1.0 if n == 0 else (1.0 if bad >= n else float(beta.ppf(1 - a, bad + 1, n - bad)))


def ckey(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:8], 16)


def _paths(ci, which):
    (pre, L, pur), g, load = COMBOS[ci]; P = v4.PRE[pre]
    return v4.draw_paths(P, L, NPATHS, [18811 if which == "dev" else 18812, L])


def dev_task(t):
    ci, D, est, rho, T, m = t
    (pre, L, pur), g, load = COMBOS[ci]; P = v4.PRE[pre]
    res = run_cell5(P, L, pur, g, load, rho, T, m, D, HORIZON, _paths(ci, "dev"), ckey("dev", pre, L, g, load, D), est)
    return dict(combo=ci, preset=pre, L=L, drift_g=g, load=load, D=D, est=est, rho=rho, T=T, margin=m, **res)


def eval_task(t):
    ci, D, est, rule, rho, T, m = t
    (pre, L, pur), g, load = COMBOS[ci]; P = v4.PRE[pre]; oracle = est == "oracle"
    res = run_cell5(P, L, pur, g, load, rho, T, m, D, HORIZON, _paths(ci, "eval"),
                    ckey("eval", pre, L, g, load, D), "static" if oracle else est, oracle=oracle)
    return dict(combo=ci, preset=pre, L=L, drift_g=g, load=load, D=D, est=est, rule=rule, rho=rho, T=T, margin=m, **res)


def _init(h, npaths, smoke=False):
    # also called in every worker: macOS uses the 'spawn' start method, so module globals must be re-applied
    global HORIZON, NPATHS, RHO, TW, MARG, ESTS, DEADLINES, COMBOS
    HORIZON, NPATHS = h, npaths
    if smoke:
        RHO, TW, MARG, DEADLINES = (0.1,), (30.0,), (0.0125,), (0.25,)
        COMBOS = [(v4.CELLS[1], 1e-4, 0.9)]


def run_pool(tasks, fn, out_csv, workers, h, npaths, smoke=False):
    done = pd.read_csv(out_csv) if out_csv.exists() else None
    if done is not None:
        cols = ["combo", "D", "est", "rho", "T", "margin"] + (["rule"] if "rule" in done else [])
        have = set(map(tuple, done[cols].astype(str).values.tolist()))
        def key(t):
            return tuple(map(str, (t[0], t[1], t[2], t[3], t[4], t[5]) if len(t) == 6 else (t[0], t[1], t[2], t[4], t[5], t[6], t[3])))
        tasks = [t for t in tasks if key(t) not in have]
    print(f"{fn.__name__}: {len(tasks)} cells to run -> {out_csv}", flush=True)
    t0 = time.time(); k = 0
    with mp.Pool(workers, initializer=_init, initargs=(h, npaths, smoke)) as pool:
        for row in pool.imap_unordered(fn, tasks, chunksize=1):
            df = pd.DataFrame([row]); df.to_csv(out_csv, mode="a", header=not out_csv.exists(), index=False); k += 1
            if k % 25 == 0 or k == len(tasks):
                print(f"  {k}/{len(tasks)} cells, {time.time() - t0:.0f} s", flush=True)
    return pd.read_csv(out_csv)


def select(dev):
    rows = []
    for (ci, D, est), g in dev.groupby(["combo", "D", "est"]):
        g = g.copy(); g["ucb"] = [cp_upper(b, n) for b, n in zip(g.bad, g.delivered)]
        for rule, ok in (("point", (g.r_cond <= 0.01) & (g.delivered >= MIN_DELIV_POINT)), ("ucb", g.ucb <= 0.01)):
            c = g[ok]
            if len(c) == 0:
                rows.append(dict(combo=ci, D=D, est=est, rule=rule, rho=np.nan, T=np.nan, margin=np.nan, feasible=False))
                continue
            b = c.sort_values(["qual_per_s", "rho", "margin"], ascending=[False, True, False]).iloc[0]
            grid_edge = ",".join(n for n, v, lo, hi in (("rho", b.rho, RHO[0], RHO[-1]), ("T", b["T"], TW[0], TW[-1]),
                                                         ("margin", b.margin, MARG[0], MARG[-1])) if v in (lo, hi))
            rows.append(dict(combo=ci, D=D, est=est, rule=rule, rho=b.rho, T=b["T"], margin=b.margin, feasible=True,
                             dev_qual_per_s=b.qual_per_s, dev_r_cond=b.r_cond, dev_delivered=b.delivered,
                             dev_ucb=b.ucb, grid_edge=grid_edge))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default="des_v5"); ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    ap.add_argument("--horizon", type=float, default=300.0); ap.add_argument("--paths", type=int, default=16)
    ap.add_argument("--smoke", action="store_true", help="tiny grid, for correctness only")
    a = ap.parse_args(); out = Path(a.outdir); out.mkdir(exist_ok=True)
    if (out / "SUMMARY.csv").exists(): sys.exit(f"{out}/SUMMARY.csv exists; refusing to overwrite")
    _init(a.horizon, a.paths, a.smoke)
    t0 = time.time()
    meta = dict(script="drift_queue_des_v5.py", v4_sha=hashlib.sha256(open(v4.__file__, "rb").read()).hexdigest(),
                self_sha=hashlib.sha256(open(__file__, "rb").read()).hexdigest(), python=platform.python_version(),
                numpy=np.__version__, horizon=a.horizon, paths=a.paths, workers=a.workers, smoke=a.smoke,
                grid=dict(rho=RHO, T=TW, margin=MARG, est=ESTS, D=DEADLINES), combos=[str(c) for c in COMBOS])
    (out / f"run_meta_{int(t0)}.json").write_text(json.dumps(meta, indent=1))
    print(f"v5: {len(COMBOS)} combos x D{DEADLINES} x est{ESTS} x {len(RHO)*len(TW)*len(MARG)} settings; "
          f"{a.paths} dev + {a.paths} eval paths; horizon {a.horizon}s; {a.workers} workers", flush=True)
    dev_tasks = [(ci, D, est, rho, T, m) for ci in range(len(COMBOS)) for D in DEADLINES for est in ESTS
                 for rho, T, m in itertools.product(RHO, TW, MARG)]
    dev = run_pool(dev_tasks, dev_task, out / "dev_cells.csv", a.workers, a.horizon, a.paths, a.smoke)
    sel = select(dev); sel.to_csv(out / "selection.csv", index=False)
    ev_tasks = [(ci, D, "oracle", "oracle", 0.0, 1.0, 0.0) for ci in range(len(COMBOS)) for D in DEADLINES]
    ev_tasks += [(int(r.combo), float(r.D), r.est, r.rule, float(r.rho), float(r["T"]), float(r.margin))
                 for _, r in sel[sel.feasible].iterrows()]
    ev = run_pool(ev_tasks, eval_task, out / "eval_cells.csv", a.workers, a.horizon, a.paths, a.smoke)
    orc = ev[ev.est == "oracle"].set_index(["combo", "D"])
    rows = []
    for _, r in sel.iterrows():
        o = orc.loc[(r.combo, r.D)]; (pre, L, pur), g, load = COMBOS[int(r.combo)]
        base = dict(combo=int(r.combo), preset=pre, L=L, drift_g=g, load=load, D=r.D, est=r.est, rule=r.rule,
                    oracle_qual_per_s=round(o.qual_per_s, 4), oracle_miss=round(o.miss, 4))
        if not r.feasible: rows.append({**base, "note": "no dev setting met rule"}); continue
        e = ev[(ev.combo == r.combo) & (ev.D == r.D) & (ev.est == r.est) & (ev.rule == r.rule)].iloc[0]
        rows.append({**base, "rho": r.rho, "T": r["T"], "margin": r.margin, "grid_edge": r.grid_edge,
                     "EVAL_frac_of_oracle": round(e.qual_per_s / max(o.qual_per_s, 1e-12), 4),
                     "EVAL_bad": int(e.bad), "EVAL_delivered": int(e.delivered),
                     "EVAL_r_cond_pct": round(100 * e.r_cond, 3),
                     "EVAL_r_cond_ucb_pct": round(100 * cp_upper(int(e.bad), int(e.delivered)), 3),
                     "EVAL_miss": round(e.miss, 4), "note": ""})
    S = pd.DataFrame(rows); S.to_csv(out / "SUMMARY.csv", index=False)
    pd.set_option("display.width", 250)
    if "EVAL_frac_of_oracle" in S: print(S.pivot_table(index=["preset", "L", "drift_g", "D"], columns=["rule", "est"],
                        values="EVAL_frac_of_oracle").round(3).to_string())
    print("rows with EVAL r_cond > 1%:", int((S.get("EVAL_r_cond_pct", pd.Series(dtype=float)) > 1).sum()),
          "of", int(S.get("EVAL_r_cond_pct", pd.Series(dtype=float)).notna().sum()))
    print("infeasible (no dev setting met rule):", int((S.note == "no dev setting met rule").sum()), "of", len(S))
    print("SUMMARY.csv sha256:", hashlib.sha256(open(out / "SUMMARY.csv", "rb").read()).hexdigest())
    print(f"elapsed {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
