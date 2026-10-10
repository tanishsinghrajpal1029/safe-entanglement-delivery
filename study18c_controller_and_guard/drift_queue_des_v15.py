"""Study 18C v15: generality / assumption stress sweep (pre-registered in README_v15.md; fresh seeds; exploratory scope).

Answers 'show the finding survives materially different conditions' and stress-tests assumptions A3 (bias) and A6
(window represents current state). Controller = RunV11 (Agresti-Coull SE) with a generalised threshold tau and an
optional controller-side model that differs from the truth. Variants (each x g {0,1e-5} x est {static, ols_reset}
x method {adaptive (+oracle), fixed z=2} x 64 paths):
  tau085_ion2020   ion-2020 L2, tau 0.85            tau085_ionproj  ion-proj L3, tau 0.85
  tau095_ionproj1  ion-proj L1, tau 0.95            tau095_ionfut3  ion-future L3, tau 0.95
  nv_tau080        NV-like  L1 (F0 .82, R 9 Hz,  T2 1 s, q .03, e .005), tau 0.80, deadline 5/R
  siv_tau080_L1/L2 SiV-like L1/L2 (F0 .86, R 1 Hz, T2 2 s, q .01, e .005), tau 0.80, deadline 5/R
  uneven           ion-proj L3, per-link quality spread x3 (one link often much worse)
  bestof3          ion-proj L3, path chosen as the best of 3 candidates by a 200-pair pilot estimate
  t2_opt / t2_pes  ion-proj L3, controller assumes memory T2 = 1.3 s (optimistic) / 0.7 s (pessimistic); truth 1.0 s
All other settings as the final run (rho 0.3, T 100 s, load 0.9, horizon 300 s + 300 s warm-up).
"""
import hashlib, math
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v11 as v11

ION2020 = dict(F0=0.940, R=182.0, T2=1.0, q=0.001, e=0.005); IONPROJ = dict(F0=0.970, R=200.0, T2=1.0, q=0.001, e=0.003)
IONFUT = dict(F0=0.990, R=1000.0, T2=1.0, q=0.001, e=0.003)
NV = dict(F0=0.820, R=9.0, T2=1.0, q=0.03, e=0.005); SIV = dict(F0=0.860, R=1.0, T2=2.0, q=0.01, e=0.005)
VARIANTS = {  # name: (truth preset, L, tau, controller overrides, deadline, spread multiplier, best_of)
    "tau085_ion2020": (ION2020, 2, 0.85, {}, 0.25, 1.0, 1), "tau085_ionproj": (IONPROJ, 3, 0.85, {}, 0.25, 1.0, 1),
    "tau095_ionproj1": (IONPROJ, 1, 0.95, {}, 0.25, 1.0, 1), "tau095_ionfut3": (IONFUT, 3, 0.95, {}, 0.25, 1.0, 1),
    "nv_tau080": (NV, 1, 0.80, {}, 5 / 9.0, 1.0, 1), "siv_tau080_L1": (SIV, 1, 0.80, {}, 5.0, 1.0, 1),
    "siv_tau080_L2": (SIV, 2, 0.80, {}, 5.0, 1.0, 1), "uneven": (IONPROJ, 3, 0.90, {}, 0.25, 3.0, 1),
    "bestof3": (IONPROJ, 3, 0.90, {}, 0.25, 1.0, 3), "t2_opt": (IONPROJ, 3, 0.90, {"T2": 1.3}, 0.25, 1.0, 1),
    "t2_pes": (IONPROJ, 3, 0.90, {"T2": 0.7}, 0.25, 1.0, 1)}
GS = (1e-9, 1e-5); ESTS = ("static", "ols_reset"); METHODS = ("adaptive", "fixed2"); NP = 64
Phi = v9.Phi


class RunV15(v11.RunV11):
    def __init__(s, *a, tau=0.9, Pc=None, **k):
        super().__init__(*a, **k); s.tau = tau; s.Pc = Pc if Pc is not None else s.P

    def serve(s, t0, deadline):
        t = t0; pairs = 0; att = 0; P = s.P; Pc = s.Pc
        while True:
            att += 1; lam = s.lam_true(t)
            d1, w1 = s.chain(t); pairs += s.L
            d2, w2 = s.chain(d1); pairs += s.L; hold = d2 - d1
            Ft = v4.dej(v4.chainF(lam, P, s.L, w1 + hold), v4.chainF(lam, P, s.L, w2), P["e"]); tdone = d2
            if tdone > deadline: return deadline, "miss", None, pairs
            if s.or_:
                lt = s.lam_true(tdone)
                deliver = v4.dej(v4.chainF(lt, P, s.L, w1 + hold), v4.chainF(lt, P, s.L, w2), P["e"]) >= s.tau
            else:
                lh, se = s.est_se(tdone); deliver = False
                if not np.any(np.isnan(lh)):
                    lp = np.clip(lh, 0, 1); l1 = np.clip(lh - se, 0, 1)
                    Fp = v4.dej(v4.chainF(lp, Pc, s.L, w1 + hold), v4.chainF(lp, Pc, s.L, w2), Pc["e"])
                    F1 = v4.dej(v4.chainF(l1, Pc, s.L, w1 + hold), v4.chainF(l1, Pc, s.L, w2), Pc["e"])
                    sF = max(Fp - F1, 1e-9); d = Fp - s.tau
                    z = s.choose_z(); deliver = d >= z * sF
                    s.push(d, sF, Phi(-d / sF))
                    if tdone >= s.warm: s.zs.append(z)
            if deliver: return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


def draw_paths_spread(P, L, n, seed, spread):
    rng = np.random.default_rng(seed)
    return [((4 * np.clip(P["F0"] + rng.normal(0, (1 - P["F0"]) * 0.2 * spread, L), 0.3, 0.9999) - 1) / 3, float(rng.uniform(0, 1)))
            for _ in range(n)]


def pick_path(P, L, cand, seed):
    """Choose the best of several candidate paths by a 200-pair-per-link pilot estimate (Agresti-Coull centre)."""
    rng = np.random.default_rng(seed); r = (1 - 2 * P["q"]) ** 2; best, bF = None, -1
    for lam0, ph in cand:
        k = rng.binomial(200, (1 + r * lam0) / 2); lh = np.clip((2 * (k + 2) / 204 - 1) / r, 0, 1)
        F = v4.chainF(lh, P, L, 0.0)
        if F > bF: best, bF = (lam0, ph), F
    return best


def tasks():
    return [[v, g, e, m, i] for v in VARIANTS for g in GS for e in ESTS for m in METHODS for i in range(NP)]


def run_id(t):
    return hashlib.sha256("v15|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    var, g, est, method, idx = t
    P, L, tau, ctrl, D, spread, k = VARIANTS[var]; Pc = dict(P, **ctrl)
    pseed = int(hashlib.sha256(f"v15path|{var}".encode()).hexdigest()[:8], 16)
    cands = draw_paths_spread(P, L, NP * k, [18921, pseed], spread)
    lam0, ph = cands[idx] if k == 1 else pick_path(P, L, cands[idx * k:(idx + 1) * k], [18922, pseed, idx])
    phase = ph * 0.02 / g
    seed = [int(hashlib.sha256(f"v15|{var}|{g}|{idx}".encode()).hexdigest()[:8], 16), 18923]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV15(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
               est=est, method=method, tau=tau, Pc=Pc)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    oq = -1
    if method == "adaptive":
        orr = RunV15(P, L, True, g, v9.LOAD, "none", 0.0, 1.0, 0.0, D, v9.H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase, tau=tau)
        oo = pd.DataFrame(orr.go(), columns="t res F pairs latency".split()); oq = int((oo[oo.res == "deliver"].F >= tau).sum())
    return dict(run=run_id(t), variant=var, L=L, tau=tau, g=g, est=est, method=method, idx=idx, lam0_min=float(np.min(lam0)),
                requests=len(o), delivered=len(x), qual=int((x.F >= tau).sum()), bad=int((x.F < tau).sum()), oracle_qual=oq,
                z_inf_frac=float(np.mean(np.isinf(r.zs))) if r.zs else float("nan"))


if __name__ == "__main__":
    import json, sys
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
    elif sys.argv[1:2] == ["--smoke"]:
        import time
        for t in (["nv_tau080", 1e-5, "static", "adaptive", 0], ["siv_tau080_L2", 1e-9, "ols_reset", "adaptive", 1],
                  ["bestof3", 1e-5, "static", "adaptive", 2], ["t2_opt", 1e-9, "static", "fixed2", 3], ["tau095_ionfut3", 1e-5, "static", "adaptive", 0]):
            t0 = time.time(); r = run_one(t); print(round(time.time() - t0, 1), "s", r)
