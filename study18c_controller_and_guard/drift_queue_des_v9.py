"""Study 18C v9: base-rate-aware (self-calibrating) delivery controller (development, NOT a final run).

Background: E22 (dev-certified risk did not transfer to fresh paths), E23/E24 (r_cond is predicted by integrating a
Gaussian per-attempt error model over the attempt histogram; replicated on fresh conditions).
Error model used here: within the estimator window every attempt on a path shares the SAME estimator error e
(common mode), e ~ N(mu, s^2) in F-space, while attempt-to-attempt variation of F comes from heralding waits that the
controller knows. For an attempt with point estimate d = F_hat - 0.9 the probability it is bad is Phi(-d/s) (mu=0 for
an unbiased estimator). So the controller can PREDICT its own conditional risk from observables only:
    r_hat(z) = mean_{recent attempts i with d_i >= z s_i} Phi(-d_i / s_i)
and choose, per path and online, the smallest z on a grid with r_hat(z) <= delta. No dev set, no oracle.
Methods compared on identical paths/seeds:  fixed z in {1,2,3} (deliver iff d >= z s)  vs  adaptive (delta = 1%).
  s = F(lambda_hat) - F(lambda_hat - SE) (F-space 1-SE, from the v6 estimator SE).
  adaptive: window = last 500 attempts on this path (observables d_i, s_i); fewer than 100 -> z = 4 (cold start);
  z grid 0..6 step 0.25; a z is admissible only if >= 20 window attempts would pass it (else: do not deliver).
  (Smoke test found that treating 'no window attempt passes' as zero risk lets sub-threshold paths deliver.)
Populations: (A) random paths as in v6 (32 eval paths, seed 18822, lam0 drawn per link);
             (B) fixed-F0 sweep as in v7 (13 F0 per cell, 1 replicate, new seed tag).
Grid: cell {ion_2020 L2, ion_proj L3} x g {0, 1e-5, 1e-4} x est {static, ols_reset}; rho 0.3, T 100 s, load 0.9,
D 0.25 s. Outputs: <outdir>/runs.csv (one row per path-run), resumable.
"""
import argparse, hashlib, json, math, platform, sys, time
import multiprocessing as mp
from pathlib import Path
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v6 as v6
import drift_queue_des_v7 as v7

ZGRID = np.arange(0.0, 6.0001, 0.25); WIN, MINW, ZCOLD, DELTA, CMIN = 500, 100, 4.0, 0.01, 20
RHO, T, LOAD, D, H = 0.3, 100.0, 0.9, 0.25, 300.0
CELLS = {"ion_2020": 2, "ion_proj": 3}; GS = (1e-9, 1e-5, 1e-4); ESTS = ("static", "ols_reset")
METHODS = ("fixed1", "fixed2", "fixed3", "adaptive")
_SQ2 = math.sqrt(2.0)


def Phi(x):
    return 0.5 * (1.0 + math.erf(x / _SQ2))


class RunV9(v6.RunV6):
    def __init__(s, *a, method="adaptive", **k):
        super().__init__(*a, **k); s.method = method; s.buf = np.zeros((3, WIN)); s.nw = 0; s.zs = []

    def choose_z(s):
        if s.method != "adaptive": return float(s.method[-1])
        n = min(s.nw, WIN)
        if n < MINW: return ZCOLD
        d, sd, pb = s.buf[0, :n], s.buf[1, :n], s.buf[2, :n]
        M = d[None, :] >= ZGRID[:, None] * sd[None, :]          # (z, window)
        cnt = M.sum(1); risk = (M * pb[None, :]).sum(1) / np.maximum(cnt, 1)
        ok = np.nonzero((risk <= DELTA) & (cnt >= CMIN))[0]      # a z needs >= CMIN supporting attempts
        return float(ZGRID[ok[0]]) if len(ok) else float("inf")    # no supported z: do not deliver

    def push(s, d, sF, pb):
        s.buf[:, s.nw % WIN] = (d, sF, pb); s.nw += 1

    def serve(s, t0, deadline):
        t = t0; pairs = 0; att = 0; P = s.P
        while True:
            att += 1; lam = s.lam_true(t)
            d1, w1 = s.chain(t); pairs += s.L
            d2, w2 = s.chain(d1); pairs += s.L; hold = d2 - d1
            Ft = v4.dej(v4.chainF(lam, P, s.L, w1 + hold), v4.chainF(lam, P, s.L, w2), P["e"]); tdone = d2
            if tdone > deadline: return deadline, "miss", None, pairs
            lh, se = s.est_se(tdone); deliver = False
            if not np.any(np.isnan(lh)):
                lp = np.clip(lh, 0, 1); l1 = np.clip(lh - se, 0, 1)
                Fp = v4.dej(v4.chainF(lp, P, s.L, w1 + hold), v4.chainF(lp, P, s.L, w2), P["e"])
                F1 = v4.dej(v4.chainF(l1, P, s.L, w1 + hold), v4.chainF(l1, P, s.L, w2), P["e"])
                sF = max(Fp - F1, 1e-9); d = Fp - 0.9
                z = s.choose_z(); deliver = d >= z * sF
                s.push(d, sF, Phi(-d / sF))
                if tdone >= s.warm: s.zs.append(z)
            if deliver: return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


def run_one(t):
    pop, cell, g, est, method, idx = t
    L = CELLS[cell]; P = v4.PRE[cell]
    if pop == "A":
        lam0, ph = v4.draw_paths(P, L, 32, [18822, L])[idx]; phase = ph * 0.02 / g; F0 = float("nan")
        seed = [int(hashlib.sha256(f"v9A|{cell}|{g}|{idx}".encode()).hexdigest()[:8], 16), 18841]
    else:
        F0 = float(v7.F0GRID[cell][idx]); lam0 = np.full(L, (4 * F0 - 1) / 3); phase = 0.5 * 0.02 / g
        seed = [int(hashlib.sha256(f"v9B|{cell}|{g}|{F0}".encode()).hexdigest()[:8], 16), 18842]
    rid = hashlib.sha256("v9|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV9(P, L, True, g, LOAD, "fixed", RHO, T, 0.0, D, H, seed, mu=mu, lam0=lam0, phase=phase, est=est, method=method)
    o = r.go(); d = pd.DataFrame(o, columns="t res F pairs latency".split()); x = d[d.res == "deliver"]
    o_r = v6.RunV6(P, L, True, g, LOAD, "none", 0.0, 1.0, 0.0, D, H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase)
    oo = pd.DataFrame(o_r.go(), columns="t res F pairs latency".split()); ox = oo[oo.res == "deliver"]
    return dict(run=rid, pop=pop, cell=cell, L=L, g=g, est=est, method=method, idx=idx, F0=F0,
                requests=len(d), delivered=len(x), qual=int((x.F >= 0.9).sum()), bad=int((x.F < 0.9).sum()),
                oracle_qual=int((ox.F >= 0.9).sum()), z_mean=float(np.mean(np.minimum(r.zs, 99))) if r.zs else float("nan"), z_inf_frac=float(np.mean(np.isinf(r.zs))) if r.zs else float("nan"),
                z_p10=float(np.quantile(np.minimum(r.zs, 99), .1)) if r.zs else float("nan"), z_p90=float(np.quantile(np.minimum(r.zs, 99), .9)) if r.zs else float("nan"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", default="des_v9"); ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args(); out = Path(a.outdir); out.mkdir(exist_ok=True); runs_csv = out / "runs.csv"
    tasks = [("A", c, g, e, m, i) for c in CELLS for g in GS for e in ESTS for m in METHODS for i in range(32)]
    tasks += [("B", c, g, e, m, i) for c in CELLS for g in GS for e in ESTS for m in METHODS for i in range(13)]
    if a.smoke: tasks = [("B", "ion_proj", 1e-5, "ols_reset", m, 4) for m in METHODS]
    if runs_csv.exists():
        have = set(pd.read_csv(runs_csv).run)
        tasks = [t for t in tasks if hashlib.sha256("v9|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12] not in have]
    t0 = time.time()
    (out / f"run_meta_{int(t0)}.json").write_text(json.dumps(dict(
        script="drift_queue_des_v9.py", self_sha=hashlib.sha256(open(__file__, "rb").read()).hexdigest(),
        v7_sha=hashlib.sha256(open(v7.__file__, "rb").read()).hexdigest(), python=platform.python_version(),
        numpy=np.__version__, workers=a.workers, smoke=a.smoke, n_tasks=len(tasks)), indent=1))
    print(f"v9: {len(tasks)} path-runs on {a.workers} workers", flush=True); k = 0
    with mp.Pool(a.workers) as pool:
        for row in pool.imap_unordered(run_one, tasks, chunksize=1):
            pd.DataFrame([row]).to_csv(runs_csv, mode="a", header=not runs_csv.exists(), index=False); k += 1
            if k % 100 == 0 or k == len(tasks): print(f"  {k}/{len(tasks)}, {time.time() - t0:.0f} s", flush=True)
    R = pd.read_csv(runs_csv)
    S = R.groupby(["pop", "cell", "g", "est", "method"])[["qual", "bad", "delivered", "oracle_qual"]].sum()
    S["r_cond_pct"] = (100 * S.bad / S.delivered.clip(lower=1)).round(3); S["frac_oracle"] = (S.qual / S.oracle_qual.clip(lower=1)).round(4)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(S.to_string()); S.to_csv(out / "SUMMARY.csv")
    print("runs.csv sha256:", hashlib.sha256(open(runs_csv, "rb").read()).hexdigest())
    print(f"elapsed {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
