"""Study 18C v17: empirical-Bayes fleet prior (pre-registered in README_v17.md; fresh seeds).

v16 (ledger E41) showed the window-threshold controller is safe when its per-decision risk is the posterior under the
TRUE fleet prior ('pop'), but in simulation that prior was handed to it (oracle prior). v17 removes that: the prior is
ESTIMATED from parity counts of K other fleet paths (no fidelity labels), by hierarchical Bayes:
  * each fleet path reports one controller window of parity counts per link (n ~ Poisson(rho R T), k ~ Binomial),
    taken at an unknown sawtooth phase U ~ Uniform(0,1) common to its links;
  * model: link F0 ~ Normal(m, s) (clipped as the path law), current lambda = lambda0 - A U, A = 0.02 known
    (re-alignment schedule and drift spec are operator knowledge; same assumption as v16 'pop');
  * flat hyperprior on a grid (m in [0.70, 0.9995], s log-spaced in [0.001, 0.08]); exact marginal likelihood by
    quadrature over F0 (fine grid) and U (20 points);
  * the controller's prior is the posterior-PREDICTIVE law of F0 (mixture over the hyper-posterior), so hyperparameter
    uncertainty is carried, then the v16 machinery (current-lambda grid, exact posterior pbad, window threshold) runs.
Each evaluation path gets its own independently drawn fleet sample, so pooled risk averages over fleet draws.
Methods: 'adaptive' (Gaussian v11), 'pop' (oracle prior, v16), and estimated priors 'eb8', 'eb32', 'eb128'
(K fleet paths, one window each) and 'eb32x10' (32 fleet paths, ten windows each): a fleet-data dose-response.
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v15 as v15
import drift_queue_des_v16 as v16

FG = np.linspace(0.5, 0.9999, 600)                       # F0 quadrature grid
MG = np.linspace(0.70, 0.9995, 121); SG = np.geomspace(0.001, 0.08, 30)
EBK = {"eb8": (8, 1), "eb32": (32, 1), "eb128": (128, 1), "eb32x10": (32, 10)}   # (fleet paths K, window multiple)


def fleet_counts(P, L, K, spread, seed, mult=1):
    """Parity counts from K fleet paths (each observed for mult controller windows): arrays n, k of shape (K, L)."""
    rng = np.random.default_rng(seed); r = (1 - 2 * P["q"]) ** 2
    paths = v15.draw_paths_spread(P, L, K, [seed[0] + 1, seed[1]], spread)
    n = np.empty((K, L), int); k = np.empty((K, L), int)
    for j, (lam0, _) in enumerate(paths):
        lc = np.clip(lam0 - v16.AMP * rng.uniform(), 0, 1)
        n[j] = rng.poisson(mult * v9.RHO * P["R"] * v9.T, L); k[j] = rng.binomial(n[j], (1 + r * lc) / 2)
    return n, k


def eb_prior_F(P, n, k):
    """Posterior-predictive law of link F0 on FG (probabilities), from fleet counts; flat hyperprior on (MG, SG)."""
    r = (1 - 2 * P["q"]) ** 2
    lam = np.clip((4 * FG - 1) / 3, 0, 1)[None, :] - v16.AMP * v16.UG[:, None]        # (U, F)
    pe = (1 + r * np.clip(lam, 0, 1)) / 2; lp, lq = np.log(pe), np.log1p(-pe)
    ll = k[:, :, None, None] * lp + (n - k)[:, :, None, None] * lq                     # (K, L, U, F)
    mx = ll.max(axis=(2, 3), keepdims=True); Lk = np.exp(ll - mx)
    pdf = np.exp(-0.5 * ((FG[None, None, :] - MG[:, None, None]) / SG[None, :, None]) ** 2)   # (m, s, F)
    pdf /= pdf.sum(2, keepdims=True)
    W = pdf.reshape(-1, len(FG))                                                       # (H, F)
    K_, L_, U_, _ = Lk.shape; pl = (Lk.reshape(-1, len(FG)) @ W.T).reshape(K_, L_, U_, -1)    # per-link marginal over F0
    pp = np.log(np.maximum(pl, 1e-300)).sum(1)                                         # (K, U, H): product over links
    a = pp.max(1, keepdims=True); lpath = np.log(np.exp(pp - a).mean(1)) + a[:, 0, :]  # average over U
    lh = lpath.sum(0); w = np.exp(lh - lh.max()); w /= w.sum()
    return w @ W, w.reshape(len(MG), len(SG))


class RunV17(v16.RunV16):
    def set_prior_F(s, pF):
        """Install a prior on link F0 (probabilities on FG) as the v16 equal-mass current-lambda grid."""
        c = np.cumsum(pF); c /= c[-1]
        F = np.interp((np.arange(v16.NPRI) + 0.5) / v16.NPRI, c, FG)
        l0 = np.clip((4 * F - 1) / 3, 0, 1); r = (1 - 2 * s.P["q"]) ** 2
        s.pri = np.clip(l0[None, :] - v16.AMP * v16.UG[:, None], 0, 1)
        pe = (1 + r * s.pri) / 2; s.lp, s.lq = np.log(pe), np.log1p(-pe)

    def serve(s, t0, deadline):
        if s.or_ or s.method not in EBK: return super().serve(t0, deadline)
        t = t0; pairs = 0; att = 0; P = s.P; Pc = s.Pc
        while True:
            att += 1; lam = s.lam_true(t)
            d1, w1 = s.chain(t); pairs += s.L
            d2, w2 = s.chain(d1); pairs += s.L; hold = d2 - d1
            Ft = v4.dej(v4.chainF(lam, P, s.L, w1 + hold), v4.chainF(lam, P, s.L, w2), P["e"]); tdone = d2
            if tdone > deadline: return deadline, "miss", None, pairs
            ld = s.lam_draws_pop(tdone); deliver = False
            if ld is not None:
                Fs = v16.dej_vec(v16.chainF_vec(ld, Pc, s.L, w1 + hold), v16.chainF_vec(ld, Pc, s.L, w2), Pc["e"])
                pbad = ((Fs < s.tau).sum() + 0.5) / (v16.M + 1)
                thr = s.choose_t(); deliver = pbad <= thr
                s.pb[s.nb % v16.WIN] = pbad; s.nb += 1
                if tdone >= s.warm: s.ts.append(thr)
            if deliver: return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


VARIANTS = v16.VARIANTS
SEEDS = (18951, 18952, 18953)   # eval paths / run streams / fleet samples (fresh; cloud dev pilot used 19951-19953)
GS = (1e-9, 1e-5); METHODS = ("adaptive", "pop", "eb8", "eb32", "eb128", "eb32x10"); NP = 128


def tasks():
    return [[v, g, "static", m, i] for v in VARIANTS for g in GS for m in METHODS for i in range(NP)]


def run_id(t):
    return hashlib.sha256("v17|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    var, g, est, method, idx = t
    P, L, tau, ctrl, D, spread, k = VARIANTS[var]; Pc = dict(P, **ctrl)
    pseed = int(hashlib.sha256(f"v17path|{var}".encode()).hexdigest()[:8], 16)
    lam0, ph = v15.draw_paths_spread(P, L, NP, [SEEDS[0], pseed], spread)[idx]
    phase = ph * 0.02 / g
    seed = [int(hashlib.sha256(f"v17|{var}|{g}|{idx}".encode()).hexdigest()[:8], 16), SEEDS[1]]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV17(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
               est=est, method=method, tau=tau, Pc=Pc, spread=spread)
    mhat = shat = float("nan")
    if method in EBK:
        n_, k_ = fleet_counts(P, L, EBK[method][0], spread, [SEEDS[2], pseed + idx], EBK[method][1])
        pF, hw = eb_prior_F(P, n_, k_); r.set_prior_F(pF)
        mhat = float(hw.sum(1) @ MG); shat = float(np.exp(hw.sum(0) @ np.log(SG)))
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    orr = v15.RunV15(P, L, True, g, v9.LOAD, "none", 0.0, 1.0, 0.0, D, v9.H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase, tau=tau)
    oo = pd.DataFrame(orr.go(), columns="t res F pairs latency".split()); oq = int((oo[oo.res == "deliver"].F >= tau).sum())
    ab = (np.mean(np.array(r.ts) < 0) if r.ts else float("nan")) if method != "adaptive" else (float(np.mean(np.isinf(r.zs))) if r.zs else float("nan"))
    return dict(run=run_id(t), variant=var, L=L, tau=tau, g=g, est=est, method=method, idx=idx, lam0_min=float(np.min(lam0)),
                requests=len(o), delivered=len(x), qual=int((x.F >= tau).sum()), bad=int((x.F < tau).sum()), oracle_qual=oq,
                abstain_frac=ab, m_hat=mhat, s_hat=shat)


if __name__ == "__main__":
    import json, sys, time
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
    elif sys.argv[1:2] == ["--check-eb"]:   # recovery of (m, s) on fleet samples only; no controller runs
        for var in VARIANTS:
            P, L, tau, ctrl, D, spread, k = VARIANTS[var]
            for K in (8, 32):
                t0 = time.time(); n_, k_ = fleet_counts(P, L, K, spread, [99, K]); pF, hw = eb_prior_F(P, n_, k_)
                mF = pF @ FG; sF = np.sqrt(pF @ (FG - mF) ** 2)
                print(f"{var:15s} K={K:2d} true m={P['F0']:.4f} s={(1 - P['F0']) * 0.2:.4f} | predictive mean {mF:.4f} sd {sF:.4f} | {time.time() - t0:.1f}s")
