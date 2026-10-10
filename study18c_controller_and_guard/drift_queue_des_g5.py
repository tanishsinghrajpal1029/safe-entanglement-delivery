"""Study 18C G5: cheaper drift-valid guards (pre-registered in README_G5.md).

G4 (E76): the drift-valid guard 'gdrift' (Prop. 6') delivered 0 bad pairs but kept only 0.63-0.68 of oracle throughput
(vs 0.85-0.95 without a guard). Two sources of cost: (i) it subtracts the WORST-CASE drift since the last re-alignment,
g (t - t_reset), from a bound that treats the counts as iid; (ii) it restarts after every re-alignment.

Two new guards (stated before any confirmatory run):
  gexact   Prop. 6'': the drift is a KNOWN deterministic offset, so the parity probability of epoch j in the current cycle is
           p_j(theta) = (1 + r (theta - g * phibar_j))/2, with theta = the link's level at its last re-alignment and phibar_j
           the epoch-average time since re-alignment (exact for uniform event times). The likelihood ratio
           M_t(theta) = Int prod_j Bin(k_j | n_j, p_j(theta')) pi(dtheta') / prod_j Bin(k_j | n_j, p_j(theta)) is a nonnegative
           martingale with mean 1 under the true theta for ANY mixing prior pi (we use the fleet prior), so
           CS_t = {theta : M_t(theta) < Lmax / alpha_c} covers theta at all times (Ville). Then lambda_now >= theta_lo -
           g * (t - t_reset) EXACTLY (no worst-case margin). Restart per cycle; alpha_c = 6 alpha / (pi^2 c^2).
  gpersist as gexact, but ONE confidence sequence over the whole run for a level theta assumed to be RESTORED EXACTLY at
           every re-alignment (no restart, no alpha spending). Valid only if that assumption holds.
Scenarios: D (G4's drift: every re-alignment restores the same level) and Dj (re-alignment restores the level plus an
independent jitter N(0, 0.005) per cycle, i.e. a quarter of the drift amplitude; gpersist's assumption is then false).
'cal' (no guard) and 'gdrift' (G4) are re-run as references. Everything else is G4.
"""
import hashlib, json, sys
import numpy as np
from scipy.special import logsumexp
import drift_queue_des_g1 as g1
import drift_queue_des_g4 as g4

ALPHA, G, TRE, NNET, JIT = g4.ALPHA, g4.G, g4.TRE, 64, 0.005
SEEDS = (19141, 19142, 19143, 19144)       # fresh confirmatory; cloud dev pilot used 20141-20144
CTRLS = ("cal", "gdrift", "gexact", "gpersist")


def cs_lower_drift(n, k, off, r, lam_grid, logprior, level):
    """Lower end of the mixture CS for theta, per link. n, k, off: (nl, J) arrays (J epochs, zero-padded with n = 0)."""
    def loglik(theta):                          # theta: (nl,) or (nl, Gr)
        th = theta[..., None] if theta.ndim == 1 else theta[:, :, None]
        o = off[:, None, :] if theta.ndim == 2 else off
        p = (1 + r * np.clip(th - o, 0, 1)) / 2; p = np.clip(p, 1e-12, 1 - 1e-12)
        kk = k[:, None, :] if theta.ndim == 2 else k; nn = n[:, None, :] if theta.ndim == 2 else n
        return (kk * np.log(p) + (nn - kk) * np.log1p(-p)).sum(-1)
    nl = n.shape[0]; LG = loglik(np.broadcast_to(lam_grid[None, :], (nl, len(lam_grid))))       # (nl, Gr)
    logmix = logsumexp(LG + logprior[None, :], axis=1); thr = np.log(1 / level)
    hi = lam_grid[np.argmax(LG, axis=1)].astype(float); lo = np.zeros(nl)
    for _ in range(50):
        mid = (lo + hi) / 2; inside = logmix - loglik(mid) < thr
        hi = np.where(inside, mid, hi); lo = np.where(inside, lo, mid)
    return np.where(n.sum(1) > 0, hi, 0.0)


class NetG5(g4.NetG4):
    def __init__(s, hw, scen, ctrl, seed):
        super().__init__(hw, "D", ctrl if ctrl in ("cal", "gdrift") else "cal_x", seed)
        s.gctrl = ctrl; s.scen5 = scen
        jr = np.random.default_rng(list(seed[2:]) + [53])
        s.jit = jr.normal(0, JIT, (s.nl, 6)) if scen == "Dj" else np.zeros((s.nl, 6))
        s.lam = s.lam_at(0.0)
        s.hist = [[] for _ in range(s.nl)]        # per link: list of (n, k, drift offset g*phibar)
        s.ncyc5 = np.zeros(s.nl, int); s.lastc = np.full(s.nl, -10 ** 6); s.theta_lo = np.zeros(s.nl); s.thc = np.full(s.nl, -10 ** 6)
        s.lam_g = np.clip((4 * g1.v17.FG - 1) / 3, 0, 1); s.logpri = np.log(np.maximum(s.pF / s.pF.sum(), 1e-300))

    def level(s, t):                                  # re-alignment level of the current cycle (jitter only in Dj)
        if not hasattr(s, "jit"): return s.lam0
        c = s.cycle_of(np.full(s.nl, t)); return np.clip(s.lam0 + s.jit[np.arange(s.nl), np.clip(c, 0, 5)], 0, 1)

    def lam_at(s, t): return np.clip(s.level(t) - G * s.phase(t), 0, 1)

    def epoch_data(s, e):
        first = e > s.acc_ep and e != s.ep
        g4.NetG4.epoch_data(s, e)
        if not first or s.gctrl not in ("gexact", "gpersist"): return
        a = e * g1.T; cid = s.cycle_of(np.full(s.nl, a)); phibar = s.phase(a) + g1.T / 2
        for l in range(s.nl):
            if s.gctrl == "gexact" and cid[l] != s.lastc[l]:
                s.hist[l] = []; s.ncyc5[l] += 1; s.lastc[l] = cid[l]
            s.hist[l].append((int(s.n[l]), int(s.kc[l]), G * phibar[l]))
        J = max(len(h) for h in s.hist); n = np.zeros((s.nl, J)); k = np.zeros((s.nl, J)); off = np.zeros((s.nl, J))
        for l, h in enumerate(s.hist):
            if h: n[l, :len(h)], k[l, :len(h)], off[l, :len(h)] = np.array(h).T
        if s.gctrl == "gexact":
            lev = ALPHA * 6 / (np.pi ** 2 * np.maximum(s.ncyc5, 1) ** 2) / s.Lmax
        else:
            lev = np.full(s.nl, ALPHA / s.Lmax)
        s.theta_lo = cs_lower_drift(n, k, off, s.r, s.lam_g, s.logpri, lev); s.thc = cid.copy()

    def guard_lam(s, links, t):
        if s.gctrl not in ("gexact", "gpersist"): return g4.NetG4.guard_lam(s, links, t)
        lk = list(links); lo = np.clip(s.theta_lo[lk] - G * s.phase(t)[lk], 0, 1)
        if s.gctrl == "gexact":
            same = s.cycle_of(np.full(s.nl, t))[lk] == s.thc[lk]
            lo = np.where(same, lo, 0.0)
        return lo


def tasks():
    return [["G5", hw, scen, c, i] for hw in ("ion2020", "ionproj") for scen in ("D", "Dj") for c in CTRLS for i in range(NNET)]


def run_id(t):
    return hashlib.sha256("g5|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, scen, ctrl, idx = t
    nseed = int(hashlib.sha256(f"g5net|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)        # paired across controllers
    rseed = int(hashlib.sha256(f"g5run|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    net = NetG5(hw, scen, ctrl, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, scen=scen, ctrl=ctrl, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
