"""Study 18C v18: misspecification stress for the empirical-Bayes fleet-prior controller (pre-registered in README_v18.md).

v17 (ledger E43) passed with an EB model whose family matches the simulator: Normal fleet law and known drift amplitude
0.02. v18 keeps the controller's model FIXED (Normal fleet law, flat hyperprior, posterior-predictive prior, assumed
drift amplitude) and changes the TRUTH or the assumption:
  fleet-law stresses (truth non-Normal; eval paths AND fleet paths drawn from it; controller still fits a Normal):
    t3       link F0 = F0 + sd * t_3 / sqrt(3)               (heavy tails, same sd)
    mixlow   85% Normal(F0, sd), 15% Normal(F0 - 3 sd, sd)   (a sub-population of bad links)
    mixhigh  85% Normal(F0, sd), 15% Normal(F0 + 3 sd, sd)   (a sub-population of excellent links)
  drift-amplitude stresses (truth Normal, amplitude 0.02; controller assumes):
    amp01    0.01 (optimistic: under-states drift)       amp03   0.03 (pessimistic)
Methods: eb128 and eb32x10 (the two v17 passes). Variants as v16/v17, g in {0, 1e-5}, 128 fresh paths.
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v15 as v15
import drift_queue_des_v16 as v16
import drift_queue_des_v17 as v17

TRUE_AMP = 0.02
STRESS = {"t3": ("t3", 0.02), "mixlow": ("mixlow", 0.02), "mixhigh": ("mixhigh", 0.02),
          "amp01": ("normal", 0.01), "amp03": ("normal", 0.03)}       # name -> (true fleet law, controller-assumed amplitude)


def draw_F0(P, L, n, rng, law, spread=1.0):
    sd = (1 - P["F0"]) * 0.2 * spread
    if law == "normal": z = rng.normal(0, 1, (n, L))
    elif law == "t3": z = rng.standard_t(3, (n, L)) / np.sqrt(3.0)
    elif law in ("mixlow", "mixhigh"):
        z = rng.normal(0, 1, (n, L)) + (-3.0 if law == "mixlow" else 3.0) * (rng.uniform(size=(n, L)) < 0.15)
    else: raise ValueError(law)
    return np.clip(P["F0"] + sd * z, 0.3, 0.9999)


def draw_paths_law(P, L, n, seed, law, spread=1.0):
    rng = np.random.default_rng(seed); F = draw_F0(P, L, n, rng, law, spread); ph = rng.uniform(0, 1, n)
    return [((4 * F[i] - 1) / 3, float(ph[i])) for i in range(n)]


def fleet_counts_law(P, L, K, spread, seed, mult, law):
    rng = np.random.default_rng(seed); r = (1 - 2 * P["q"]) ** 2
    paths = draw_paths_law(P, L, K, [seed[0] + 1, seed[1]], law, spread)
    n = np.empty((K, L), int); k = np.empty((K, L), int)
    for j, (lam0, _) in enumerate(paths):
        lc = np.clip(lam0 - TRUE_AMP * rng.uniform(), 0, 1)
        n[j] = rng.poisson(mult * v9.RHO * P["R"] * v9.T, L); k[j] = rng.binomial(n[j], (1 + r * lc) / 2)
    return n, k


def eb_prior_F_amp(P, n, k, amp):
    """v17.eb_prior_F with the controller-assumed drift amplitude as a parameter."""
    FG, MG, SG = v17.FG, v17.MG, v17.SG; r = (1 - 2 * P["q"]) ** 2
    lam = np.clip((4 * FG - 1) / 3, 0, 1)[None, :] - amp * v16.UG[:, None]
    pe = (1 + r * np.clip(lam, 0, 1)) / 2; lp, lq = np.log(pe), np.log1p(-pe)
    ll = k[:, :, None, None] * lp + (n - k)[:, :, None, None] * lq
    mx = ll.max(axis=(2, 3), keepdims=True); Lk = np.exp(ll - mx)
    pdf = np.exp(-0.5 * ((FG[None, None, :] - MG[:, None, None]) / SG[None, :, None]) ** 2); pdf /= pdf.sum(2, keepdims=True)
    W = pdf.reshape(-1, len(FG))
    K_, L_, U_, _ = Lk.shape; pl = (Lk.reshape(-1, len(FG)) @ W.T).reshape(K_, L_, U_, -1)
    pp = np.log(np.maximum(pl, 1e-300)).sum(1)
    a = pp.max(1, keepdims=True); lpath = np.log(np.exp(pp - a).mean(1)) + a[:, 0, :]
    lh = lpath.sum(0); w = np.exp(lh - lh.max()); w /= w.sum()
    return w @ W, w.reshape(len(MG), len(SG))


class RunV18(v17.RunV17):
    def set_prior_F_amp(s, pF, amp):
        c = np.cumsum(pF); c /= c[-1]
        F = np.interp((np.arange(v16.NPRI) + 0.5) / v16.NPRI, c, v17.FG)
        l0 = np.clip((4 * F - 1) / 3, 0, 1); r = (1 - 2 * s.P["q"]) ** 2
        s.pri = np.clip(l0[None, :] - amp * v16.UG[:, None], 0, 1)
        pe = (1 + r * s.pri) / 2; s.lp, s.lq = np.log(pe), np.log1p(-pe)


VARIANTS = v16.VARIANTS
SEEDS = (18961, 18962, 18963)   # fresh; the cloud dev pilot used 19961-19963
GS = (1e-9, 1e-5); METHODS = ("eb128", "eb32x10"); NP = 128


def tasks():
    return [[v, g, st, m, i] for v in VARIANTS for g in GS for st in STRESS for m in METHODS for i in range(NP)]


def run_id(t):
    return hashlib.sha256("v18|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    var, g, stress, method, idx = t
    P, L, tau, ctrl, D, spread, k = VARIANTS[var]; Pc = dict(P, **ctrl); law, amp = STRESS[stress]
    pseed = int(hashlib.sha256(f"v18path|{var}|{law}".encode()).hexdigest()[:8], 16)
    lam0, ph = draw_paths_law(P, L, NP, [SEEDS[0], pseed], law, spread)[idx]
    phase = ph * TRUE_AMP / g
    seed = [int(hashlib.sha256(f"v18|{var}|{law}|{g}|{idx}".encode()).hexdigest()[:8], 16), SEEDS[1]]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV18(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
               est="static", method=method, tau=tau, Pc=Pc, spread=spread)
    K, mult = v17.EBK[method]
    n_, k_ = fleet_counts_law(P, L, K, spread, [SEEDS[2], pseed + idx], mult, law)
    pF, hw = eb_prior_F_amp(P, n_, k_, amp); r.set_prior_F_amp(pF, amp)
    mhat = float(hw.sum(1) @ v17.MG); shat = float(np.exp(hw.sum(0) @ np.log(v17.SG)))
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    orr = v15.RunV15(P, L, True, g, v9.LOAD, "none", 0.0, 1.0, 0.0, D, v9.H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase, tau=tau)
    oo = pd.DataFrame(orr.go(), columns="t res F pairs latency".split()); oq = int((oo[oo.res == "deliver"].F >= tau).sum())
    ab = float(np.mean(np.array(r.ts) < 0)) if r.ts else float("nan")
    return dict(run=run_id(t), variant=var, L=L, tau=tau, g=g, stress=stress, method=method, idx=idx, lam0_min=float(np.min(lam0)),
                requests=len(o), delivered=len(x), qual=int((x.F >= tau).sum()), bad=int((x.F < tau).sum()), oracle_qual=oq,
                abstain_frac=ab, m_hat=mhat, s_hat=shat)


if __name__ == "__main__":
    import json, sys
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
