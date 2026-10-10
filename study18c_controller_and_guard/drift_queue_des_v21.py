"""Study 18C v21: robust fleet prior (post hoc, motivated by the C1 failures; pre-registered before its confirmatory run C2).

C1 (E54) failed in two mechanisms, both 'p_i is not the true posterior' (Proposition 2):
  (1) thin data (SiV-like, ~30 pairs/window): the empirical-Bayes hyperposterior over the fleet spread s, under a
      log-uniform hyperprior, piles mass at tiny s when the fleet data cannot resolve s -> over-confident prior;
  (2) exchangeability: an unannounced link fault is shrunk back toward the fleet (prior tighter than one window).
v21 changes ONLY the fleet prior handed to the frozen C1 controller:
  M1  hyperprior on s uniform in s (weakly informative; Gelman 2006) instead of log-uniform;
  M3  drift-aware window likelihood: the parity counts measure the WINDOW-AVERAGE lambda, which under the known
      sawtooth drift (rate g, amplitude 0.02) differs from the current lambda by an exactly computable offset for each
      phase on the U grid (C1 treated the counts as measuring the current lambda: an optimistic bias ~ g T / 2 per link);
  M2  explicit fault component: each link's F0 prior = (1-eps) * fleet + eps * (fleet shifted down by D),
      D ~ Uniform(0, DMAX_SD * s_hat)  (an operator-declared fault model; eps = 0.05, DMAX_SD = 4).
Everything else (T1-aware PTM fidelity, window local-fdr threshold, delta 1%) is C1's frozen controller.
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v16 as v16
import drift_queue_des_v17 as v17
import drift_queue_des_v18 as v18
import drift_queue_des_c1 as c1

EPS, DMAX_SD = 0.05, 4.0
FAULT_P = 0.05                     # block R: each path is faulted with this probability (matches the declared EPS)
VARIANTS = {"c1": (0, 0.0, False), "m1": (1, 0.0, False), "m13": (1, 0.0, True), "m123": (1, EPS, True)}
# name -> (hyperprior power on s, fault eps, drift-aware likelihood)


class RunV21(c1.RunC1):
    drift_aware = True

    def window_shift(s, W):
        """Window-average minus current lambda for each phase u on the U grid (exact for the sawtooth)."""
        A = v16.AMP; Tre = s.Tre; g = s.g; ts = v16.UG * Tre                 # time since last re-alignment
        avg_minus_l0 = np.where(ts >= W, -g * ts + g * W / 2,
                                (ts * (-g * ts / 2) + (W - ts) * (-A + g * (W - ts) / 2)) / W)
        return avg_minus_l0 + A * v16.UG                                    # (avg - lambda0) - (cur - lambda0)

    def lam_draws_pop(s, t):
        if not s.drift_aware: return super().lam_draws_pop(t)
        L = s.L; r = (1 - 2 * s.P["q"]) ** 2; rng = s.rng; a = max(0.0, t - s.T)
        if t - a <= 0: return None
        NPRI, UG, M = v16.NPRI, v16.UG, v16.M
        pe = (1 + r * np.clip(s.pri + s.window_shift(t - a)[:, None], 0, 1)) / 2; lp, lq = np.log(pe), np.log1p(-pe)
        rt = s._rate_time(a, t); lb = np.clip(s.lam_avg(a, t), 0, 1)
        LW = np.empty((L, len(UG), NPRI))
        for i in range(L):
            n = rng.poisson(rt)
            if n < 5: return None
            k = rng.binomial(n, (1 + r * lb[i]) / 2); LW[i] = k * lp + (n - k) * lq
        LW -= LW.max(axis=(1, 2), keepdims=True); W = np.exp(LW)
        Z = W.sum(2); lz = np.log(Z).sum(0); pu = np.exp(lz - lz.max()); pu /= pu.sum()
        js = rng.choice(len(UG), M, p=pu); C = np.cumsum(W, axis=2); C /= C[:, :, -1:]
        C += np.arange(len(UG))[None, :, None]; out = np.empty((M, L))
        for i in range(L):
            idx = np.searchsorted(C[i].ravel(), js + rng.random(M)) - js * NPRI
            out[:, i] = s.pri[js, np.minimum(idx, NPRI - 1)]
        return out


def eb_prior_F_v21(P, n, k, s_power):
    """v17.eb_prior_F with hyperprior density proportional to s**s_power on the log-spaced s grid
    (s_power = 0: log-uniform, as v17/C1; s_power = 1: uniform in s)."""
    FG, MG, SG = v17.FG, v17.MG, v17.SG; r = (1 - 2 * P["q"]) ** 2
    lam = np.clip((4 * FG - 1) / 3, 0, 1)[None, :] - v16.AMP * v16.UG[:, None]
    pe = (1 + r * np.clip(lam, 0, 1)) / 2; lp, lq = np.log(pe), np.log1p(-pe)
    ll = k[:, :, None, None] * lp + (n - k)[:, :, None, None] * lq
    mx = ll.max(axis=(2, 3), keepdims=True); Lk = np.exp(ll - mx)
    pdf = np.exp(-0.5 * ((FG[None, None, :] - MG[:, None, None]) / SG[None, :, None]) ** 2); pdf /= pdf.sum(2, keepdims=True)
    W = pdf.reshape(-1, len(FG))
    K_, L_, U_, _ = Lk.shape; pl = (Lk.reshape(-1, len(FG)) @ W.T).reshape(K_, L_, U_, -1)
    pp = np.log(np.maximum(pl, 1e-300)).sum(1)
    a = pp.max(1, keepdims=True); lpath = np.log(np.exp(pp - a).mean(1)) + a[:, 0, :]
    lh = lpath.sum(0) + s_power * np.log(np.tile(SG, len(MG))); w = np.exp(lh - lh.max()); w /= w.sum()
    hw = w.reshape(len(MG), len(SG)); s_hat = float(hw.sum(0) @ SG)
    return w @ W, hw, s_hat


def fault_mix(pF, s_hat, eps, nd=24):
    """(1-eps) pF + eps * pF shifted down by D ~ U(0, DMAX_SD * s_hat), on the F grid."""
    if eps <= 0: return pF
    FG = v17.FG; acc = np.zeros_like(pF)
    for d in (np.arange(nd) + 0.5) / nd * DMAX_SD * s_hat:
        acc += np.interp(FG + d, FG, pF, left=0.0, right=0.0)          # density of F0 - D at FG
    acc /= acc.sum(); return (1 - eps) * pF / pF.sum() + eps * acc


def run_one(t, variant, npaths=None, seeds=None):
    """C1 task semantics (blocks A/B/C) plus block R (fault with probability FAULT_P), with the v21 prior variant."""
    blk, cell, g, mem, law, idx = t
    S = seeds or c1.SEEDS
    P, L, tau, ctrl, D, spread, k = c1.CELLS[cell]; Pc = dict(P, **ctrl)
    npth = (npaths or {"A": c1.NA, "B": c1.NB, "C": c1.NC, "R": c1.NA})[blk]
    pseed = int(hashlib.sha256(f"c1path|{blk}|{cell}|{law}".encode()).hexdigest()[:8], 16)
    lam0, ph = v18.draw_paths_law(P, L, npth, [S[0], pseed], law, spread)[idx]
    phase = ph * 0.02 / g
    seed = [int(hashlib.sha256(f"c1|{blk}|{cell}|{law}|{g}|{idx}".encode()).hexdigest()[:8], 16), S[1]]
    mu = v4.service_mu(P, L, True, lam0, D)
    s_power, eps, da = VARIANTS[variant]
    r = RunV21(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
                 est="static", method="eb128t1", tau=tau, Pc=Pc, spread=spread, mem=mem, t1mult=1.0)
    r.drift_aware = da
    orc = c1.OracleC1(P, L, True, g, v9.LOAD, "none", 0.0, 1.0, 0.0, D, v9.H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase,
                      tau=tau, mem=r.mem)
    fault = None
    if blk in ("C", "R"):
        fr = np.random.default_rng([S[3], pseed, idx]); hit = fr.uniform() < (1.0 if blk == "C" else FAULT_P)
        ts = r.warm + fr.uniform(0, r.H); j = int(fr.integers(0, L))
        dl = float(min(lam0[j], 4 / 3 * c1.SWITCH_SD * (1 - P["F0"]) * 0.2 * spread))
        if hit: fault = (ts, j, dl); r.set_fault(*fault); orc.set_fault(*fault)
    n_, k_ = v18.fleet_counts_law(P, L, 128, spread, [S[2], pseed + idx], 1, law)
    pF, hw, s_hat = eb_prior_F_v21(P, n_, k_, s_power); r.set_prior_F(fault_mix(pF, s_hat, eps))
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    oo = pd.DataFrame(orc.go(), columns="t res F pairs latency".split()); oq = int((oo.res == "deliver").sum())
    post = x[x.t >= fault[0]] if fault else x.iloc[0:0]
    return dict(faulted=int(fault is not None), block=blk, cell=cell, g=g, mem=mem, law=law, idx=idx, variant=variant, requests=len(o), delivered=len(x),
                qual=int((x.F >= tau).sum()), bad=int((x.F < tau).sum()), oracle_qual=oq, s_hat=s_hat,
                post_fault_delivered=len(post), post_fault_bad=int((post.F < tau).sum()))
