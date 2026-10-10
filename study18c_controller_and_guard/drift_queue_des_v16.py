"""Study 18C v16: exact-likelihood (Beta-posterior) self-calibrating controller (pre-registered in README_v16.md).

Motivation (post hoc, stated as such): v15 (ledger E39) found the Gaussian plug-in Phi(-d/s) under-estimates risk
on NV-like hardware (low rate, readout error 3%) because estimator errors have heavier-than-Gaussian tails there.
v16 replaces the Gaussian plug-in by a likelihood-based posterior that uses the raw parity counts:
  * per link (static / reset window): even-parity probability p ~ Beta(k + 1/2, n - k + 1/2) (Jeffreys), lambda = (2p-1)/r;
  * ols_reset: per bin p_j ~ Beta(k_j + 1/2, n_j - k_j + 1/2), weighted-LS intercept per posterior draw;
  * pbad_i = P_post(F_i < tau) by Monte Carlo (M = 256 draws, smoothed (count + 1/2)/(M + 1)).
Fleet-prior methods ('pop', 'popwide', 'popopt'; static window): the same window-threshold rule, but pbad is the posterior
under a population prior on the CURRENT link quality (path law of lambda0, minus a uniform sawtooth offset of amplitude
0.02 common to the path), sampled exactly on a 20 x 200 grid. 'pop' = correctly specified prior; 'popwide' = prior sd x2
(conservative mis-specification); 'popopt' = prior mean shifted +1 population sd (optimistic mis-specification).
Cloud dev pilot (seeds 19931/19932, disclosed in README_v16.md) motivated the fleet prior: Jeffreys alone still
violated on NV-like hardware (winner's curse under a flat prior), and the prior must include the drift offset.
Decision ('exact' method): deliver iff pbad_i <= t, where t is the largest grid value whose mean pbad among recent
window attempts with pbad <= t is <= delta (1%), with >= 20 supporting attempts (else no delivery); cold start t = 0.001.
This is a local-fdr (Bayesian false-discovery) threshold rule. The Gaussian 'adaptive' controller runs on identical
paths and seeds for comparison. Everything else as v15 (RunV15: general tau, rho 0.3, T 100 s, load 0.9).
"""
import hashlib, math
from statistics import NormalDist
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v15 as v15

# fleet-prior methods: name -> (mean shift in population sd units, sd multiplier). 'pop' = correctly specified.
PRIORS = {"pop": (0.0, 1.0), "popwide": (0.0, 2.0), "popopt": (1.0, 1.0)}
NPRI = 200; AMP = 0.02; UG = (np.arange(20) + 0.5) / 20
QN = np.array([NormalDist().inv_cdf((j + 0.5) / NPRI) for j in range(NPRI)])
M = 256; DELTA = 0.01; CMIN = 20; WIN = 500; MINW = 100
TGRID = np.unique(np.concatenate([np.geomspace(1e-3, 0.5, 40), [1.0]]))


def dej_vec(F1, F2, e):
    if e not in v4._t: v4._t[e] = np.load(f"dejmps_table_e{e}.npy")
    Z = v4._t[e]; n = len(v4.GRID) - 1
    x = (np.clip(F1, 0.5, 1.0) - 0.5) / 0.005; y = (np.clip(F2, 0.5, 1.0) - 0.5) / 0.005
    i = np.minimum(x.astype(int), n - 1); j = np.minimum(y.astype(int), n - 1); fx = x - i; fy = y - j
    return (1 - fx) * (1 - fy) * Z[i, j] + fx * (1 - fy) * Z[i + 1, j] + (1 - fx) * fy * Z[i, j + 1] + fx * fy * Z[i + 1, j + 1]


def chainF_vec(lams, P, L, waits):          # lams: (M, L)
    return (1 + 3 * (np.prod(lams, axis=1) * (1 - P["e"]) ** (2 * (L - 1)) * np.exp(-2 * waits / P["T2"]))) / 4


class RunV16(v15.RunV15):
    def __init__(s, *a, **k):
        sp = k.pop("spread", 1.0)
        super().__init__(*a, **k); s.pb = np.zeros(WIN); s.nb = 0; s.ts = []; s.pri = None; s.spread = sp

    def lam_draws(s, t):
        """(M, L) posterior draws of link lambda, or None if any link has < 5 pairs."""
        L = s.L; r = (1 - 2 * s.P["q"]) ** 2; rng = s.rng
        a = max(0.0, t - s.T) if s.est == "static" else max(0.0, t - s.T, t - ((t + s.phase) % s.Tre))
        W = t - a
        if W <= 0: return None
        out = np.empty((M, L))
        if s.est in ("static", "reset"):
            rt = s._rate_time(a, t); lb = np.clip(s.lam_avg(a, t), 0, 1)
            for i in range(L):
                n = rng.poisson(rt)
                if n < 5: return None
                k = rng.binomial(n, (1 + r * lb[i]) / 2)
                out[:, i] = (2 * rng.beta(k + 0.5, n - k + 0.5, M) - 1) / r
            return np.clip(out, 0, 1)
        K = 4; edges = np.linspace(a, t, K + 1); mids = (edges[:-1] + edges[1:]) / 2 - t
        rts = [s._rate_time(edges[j], edges[j + 1]) for j in range(K)]
        lbs = [np.clip(s.lam_avg(edges[j], edges[j + 1]), 0, 1) for j in range(K)]
        for i in range(L):
            ns = np.array([rng.poisson(rt) for rt in rts])
            ks = np.array([rng.binomial(n, (1 + r * lb[i]) / 2) if n > 0 else 0 for n, lb in zip(ns, lbs)])
            if ns.sum() < 5: return None
            ok = ns >= 5
            if ok.sum() < 2:
                N, Kk = int(ns.sum()), int(ks.sum()); out[:, i] = (2 * rng.beta(Kk + 0.5, N - Kk + 0.5, M) - 1) / r; continue
            p = rng.beta(ks[ok] + 0.5, ns[ok] - ks[ok] + 0.5, size=(M, ok.sum())); y = (2 * p - 1) / r
            x = mids[ok]; w = ns[ok].astype(float); X = np.column_stack([np.ones_like(x), x])
            Hm = np.linalg.solve(X.T @ (X * w[:, None]), (X * w[:, None]).T)     # (2, nb): coef = Hm @ y
            out[:, i] = y @ Hm[0]
        return np.clip(out, 0, 1)

    def lam_draws_pop(s, t):
        """(M, L) posterior draws of current link lambda under a fleet (population) prior, static window.
        Prior: lambda_i = lambda0_i - A*U, lambda0_i iid from the path law (mean F0 + shift*sd, sd x width),
        U ~ Uniform(0,1) common to the path (sawtooth phase), A = drift amplitude 0.02. Exact joint sampling on a
        U grid: per-link importance weights over NPRI prior draws, U from its marginal posterior, then lambda0 | U."""
        L = s.L; r = (1 - 2 * s.P["q"]) ** 2; rng = s.rng; a = max(0.0, t - s.T)
        if t - a <= 0: return None
        if s.pri is None:
            P = s.P; sd = (1 - P["F0"]) * 0.2 * s.spread; sh, wd = PRIORS[s.method]
            l0 = np.clip((4 * np.clip(P["F0"] + sh * sd + sd * wd * QN, 0.3, 0.9999) - 1) / 3, 0, 1)  # equal-mass grid
            s.pri = np.clip(l0[None, :] - AMP * UG[:, None], 0, 1)          # (J, NPRI) current lambda
            pe = (1 + r * s.pri) / 2; s.lp, s.lq = np.log(pe), np.log1p(-pe)
        rt = s._rate_time(a, t); lb = np.clip(s.lam_avg(a, t), 0, 1)
        LW = np.empty((L, len(UG), NPRI))
        for i in range(L):
            n = rng.poisson(rt)
            if n < 5: return None
            k = rng.binomial(n, (1 + r * lb[i]) / 2); LW[i] = k * s.lp + (n - k) * s.lq
        LW -= LW.max(axis=(1, 2), keepdims=True); W = np.exp(LW)                 # (L, J, NPRI)
        Z = W.sum(2); lz = np.log(Z).sum(0); pu = np.exp(lz - lz.max()); pu /= pu.sum()   # U posterior on grid
        js = rng.choice(len(UG), M, p=pu); C = np.cumsum(W, axis=2); C /= C[:, :, -1:]     # (L, J, NPRI)
        C += np.arange(len(UG))[None, :, None]; out = np.empty((M, L))
        for i in range(L):                                                                 # inverse-CDF draw of lambda0 | U
            idx = np.searchsorted(C[i].ravel(), js + rng.random(M)) - js * NPRI
            out[:, i] = s.pri[js, np.minimum(idx, NPRI - 1)]
        return out

    def choose_t(s):
        n = min(s.nb, WIN)
        if n < MINW: return 1e-3
        pb = s.pb[:n]; Mk = pb[None, :] <= TGRID[:, None]; cnt = Mk.sum(1)
        risk = (Mk * pb[None, :]).sum(1) / np.maximum(cnt, 1)
        ok = np.nonzero((risk <= DELTA) & (cnt >= CMIN))[0]
        return float(TGRID[ok[-1]]) if len(ok) else -1.0

    def serve(s, t0, deadline):
        if s.or_ or s.method not in ("exact",) + tuple(PRIORS): return super().serve(t0, deadline)
        t = t0; pairs = 0; att = 0; P = s.P; Pc = s.Pc
        while True:
            att += 1; lam = s.lam_true(t)
            d1, w1 = s.chain(t); pairs += s.L
            d2, w2 = s.chain(d1); pairs += s.L; hold = d2 - d1
            Ft = v4.dej(v4.chainF(lam, P, s.L, w1 + hold), v4.chainF(lam, P, s.L, w2), P["e"]); tdone = d2
            if tdone > deadline: return deadline, "miss", None, pairs
            ld = s.lam_draws(tdone) if s.method == "exact" else s.lam_draws_pop(tdone); deliver = False
            if ld is not None:
                Fs = dej_vec(chainF_vec(ld, Pc, s.L, w1 + hold), chainF_vec(ld, Pc, s.L, w2), Pc["e"])
                pbad = ((Fs < s.tau).sum() + 0.5) / (M + 1)
                thr = s.choose_t(); deliver = pbad <= thr
                s.pb[s.nb % WIN] = pbad; s.nb += 1
                if tdone >= s.warm: s.ts.append(thr)
            if deliver: return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


VARIANTS = {"nv_tau080": v15.VARIANTS["nv_tau080"],
            "ion2020_tau090": (v15.ION2020, 2, 0.90, {}, 0.25, 1.0, 1),
            "ionproj_tau090": (v15.IONPROJ, 3, 0.90, {}, 0.25, 1.0, 1),
            "tau085_ion2020": v15.VARIANTS["tau085_ion2020"]}
SEEDS = (18931, 18932)   # confirmatory seeds; the cloud dev pilot used (19931, 19932)
GS = (1e-9, 1e-5); ESTS = ("static", "ols_reset"); METHODS = ("adaptive", "exact"); NP = 64


def tasks():   # fleet-prior methods use the static window only
    return ([[v, g, e, m, i] for v in VARIANTS for g in GS for e in ESTS for m in METHODS for i in range(NP)] +
            [[v, g, "static", m, i] for v in VARIANTS for g in GS for m in PRIORS for i in range(NP)])


def run_id(t):
    return hashlib.sha256("v16|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    var, g, est, method, idx = t
    P, L, tau, ctrl, D, spread, k = VARIANTS[var]; Pc = dict(P, **ctrl)
    pseed = int(hashlib.sha256(f"v16path|{var}".encode()).hexdigest()[:8], 16)
    lam0, ph = v15.draw_paths_spread(P, L, NP, [SEEDS[0], pseed], spread)[idx]
    phase = ph * 0.02 / g
    seed = [int(hashlib.sha256(f"v16|{var}|{g}|{idx}".encode()).hexdigest()[:8], 16), SEEDS[1]]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV16(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
               est=est, method=method, tau=tau, Pc=Pc, spread=spread)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    orr = v15.RunV15(P, L, True, g, v9.LOAD, "none", 0.0, 1.0, 0.0, D, v9.H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase, tau=tau)
    oo = pd.DataFrame(orr.go(), columns="t res F pairs latency".split()); oq = int((oo[oo.res == "deliver"].F >= tau).sum())
    ab = (np.mean(np.array(r.ts) < 0) if r.ts else float("nan")) if method != "adaptive" else (float(np.mean(np.isinf(r.zs))) if r.zs else float("nan"))
    return dict(run=run_id(t), variant=var, L=L, tau=tau, g=g, est=est, method=method, idx=idx, lam0_min=float(np.min(lam0)),
                requests=len(o), delivered=len(x), qual=int((x.F >= tau).sum()), bad=int((x.F < tau).sum()), oracle_qual=oq, abstain_frac=ab)


if __name__ == "__main__":
    import json, sys, time
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
    elif sys.argv[1:2] == ["--smoke"]:
        for t in (["nv_tau080", 1e-9, "ols_reset", "exact", 0], ["nv_tau080", 1e-9, "ols_reset", "adaptive", 0],
                  ["nv_tau080", 1e-5, "static", "exact", 1], ["ionproj_tau090", 1e-5, "static", "exact", 2], ["ionproj_tau090", 1e-5, "static", "adaptive", 2]):
            t0 = time.time(); r = run_one(t); print(round(time.time() - t0, 1), "s", r)
