"""Study 24 Block B: carry what a link learned before a re-alignment into the guard after it, without trusting it.

G5 (E78): the drift-valid guard 'gexact' (Prop. 6'') costs 14-20% of oracle throughput, mostly because it RESTARTS its
confidence sequence at every re-alignment; 'gpersist' (one sequence, assumes each re-alignment restores exactly the same
level) recovers most of that but lost its guarantee as soon as re-alignment jittered (Dj: 254 bad pairs).

New guard (stated before any run):
  gcarry  gexact (restart per cycle, alpha_c = 6 alpha / (pi^2 c^2) / Lmax), but from the second cycle on, the cycle's mixing
          prior is a SCALE MIXTURE centred on the previous cycle's estimate of the level:
              pi_c = 0.25 N(th_prev, 0.002) + 0.25 N(th_prev, 0.006) + 0.25 N(th_prev, 0.02) + 0.25 fleet prior,
          th_prev = posterior mean of the previous cycle's level (fleet prior, exact drift-offset likelihood).
          Validity: the previous cycle's counts are independent of the current cycle's counts given the levels, so pi_c is a
          fixed prior for the current cycle's martingale; Ville + the same alpha spending as gexact give
          P(a path ever delivers a bad pair) <= alpha for ANY re-alignment jitter, including none and including large.
          No jitter has to be declared: the scale mixture adapts, and a wrong centre costs at most ln 4 in the threshold.
Scenarios: D (exact re-alignment), Dj (jitter sd 0.005, as G5), Djb (jitter sd 0.02, four times larger: re-alignment
moves the level by about one fleet spread; gpersist's assumption badly false).
Controllers: cal (no guard), gexact (G5), gpersist (G5; valid only in D), gcarry (new).
"""
import hashlib, json, os, sys
import numpy as np
from scipy.special import logsumexp
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), "/home/claude/s18c"):
    if p and p not in sys.path: sys.path.append(p)
import drift_queue_des_g1 as g1
import drift_queue_des_g5 as g5

ALPHA, G = g5.ALPHA, g5.G
JIT = {"D": 0.0, "Dj": 0.005, "Djb": 0.02}
SCALES = (0.002, 0.006, 0.02)
CTRLS = ("cal", "gexact", "gpersist", "gcarry")
SEEDS = (19251, 19252, 19253, 19254)      # fresh confirmatory; cloud dev pilot 20251-20254
DEV = (20251, 20252, 20253, 20254)
NNET = 64


def cs_lower_drift2(n, k, off, r, lam_grid, logprior2, level):
    """g5.cs_lower_drift with a per-link mixing prior logprior2 (nl, Gr)."""
    def loglik(theta):
        th = theta[..., None] if theta.ndim == 1 else theta[:, :, None]
        o = off[:, None, :] if theta.ndim == 2 else off
        p = (1 + r * np.clip(th - o, 0, 1)) / 2; p = np.clip(p, 1e-12, 1 - 1e-12)
        kk = k[:, None, :] if theta.ndim == 2 else k; nn = n[:, None, :] if theta.ndim == 2 else n
        return (kk * np.log(p) + (nn - kk) * np.log1p(-p)).sum(-1)
    nl = n.shape[0]; LG = loglik(np.broadcast_to(lam_grid[None, :], (nl, len(lam_grid))))
    logmix = logsumexp(LG + logprior2, axis=1); thr = np.log(1 / level)
    hi = lam_grid[np.argmax(LG, axis=1)].astype(float); lo = np.zeros(nl)
    for _ in range(50):
        mid = (lo + hi) / 2; inside = logmix - loglik(mid) < thr
        hi = np.where(inside, mid, hi); lo = np.where(inside, lo, mid)
    return np.where(n.sum(1) > 0, hi, 0.0), LG


class NetB(g5.NetG5):
    def __init__(s, hw, scen, ctrl, seed):
        base = "gexact" if ctrl == "gcarry" else ctrl
        super().__init__(hw, "Dj" if scen != "D" else "D", base, seed)
        s.ctrl24 = ctrl; s.scen24 = scen
        jr = np.random.default_rng(list(seed[2:]) + [53])
        s.jit = jr.normal(0, 1, (s.nl, 6)) * JIT[scen]                       # same draws for Dj and Djb, scaled
        s.lam = s.lam_at(0.0)
        s.pri2 = np.broadcast_to(s.logpri, (s.nl, len(s.lam_g))).copy()       # cycle 1: fleet prior (= gexact)
        s.carry_err = []

    def epoch_data(s, e):
        if s.ctrl24 != "gcarry": return g5.NetG5.epoch_data(s, e)
        first = e > s.acc_ep and e != s.ep
        g5.g4.NetG4.epoch_data(s, e)
        if not first: return
        a = e * g1.T; cid = s.cycle_of(np.full(s.nl, a)); phibar = s.phase(a) + g1.T / 2
        for l in range(s.nl):
            if cid[l] != s.lastc[l]:
                if s.hist[l]:                                                  # new cycle: carry the previous cycle's estimate
                    h = np.array(s.hist[l]); th = s.lam_g
                    p = np.clip((1 + s.r * np.clip(th[:, None] - h[None, :, 2], 0, 1)) / 2, 1e-12, 1 - 1e-12)
                    ll = (h[None, :, 1] * np.log(p) + (h[None, :, 0] - h[None, :, 1]) * np.log1p(-p)).sum(1) + s.logpri
                    w = np.exp(ll - ll.max()); w /= w.sum(); mu = float(w @ th)
                    comps = [np.log(0.25) + s.logpri]
                    for sc in SCALES:
                        lg_ = -0.5 * ((th - mu) / sc) ** 2; comps.append(np.log(0.25) + lg_ - logsumexp(lg_))
                    s.pri2[l] = logsumexp(np.stack(comps), axis=0)
                    s.carry_err.append(abs(mu - float(s.level(a)[l])))
                s.hist[l] = []; s.ncyc5[l] += 1; s.lastc[l] = cid[l]
            s.hist[l].append((int(s.n[l]), int(s.kc[l]), G * phibar[l]))
        Jm = max(len(h) for h in s.hist); n = np.zeros((s.nl, Jm)); k = np.zeros((s.nl, Jm)); off = np.zeros((s.nl, Jm))
        for l, h in enumerate(s.hist):
            if h: n[l, :len(h)], k[l, :len(h)], off[l, :len(h)] = np.array(h).T
        lev = ALPHA * 6 / (np.pi ** 2 * np.maximum(s.ncyc5, 1) ** 2) / s.Lmax
        s.theta_lo, _ = cs_lower_drift2(n, k, off, s.r, s.lam_g, s.pri2, lev); s.thc = cid.copy()

    def guard_lam(s, links, t):
        if s.ctrl24 == "gcarry":
            lk = list(links); lo = np.clip(s.theta_lo[lk] - G * s.phase(t)[lk], 0, 1)
            same = s.cycle_of(np.full(s.nl, t))[lk] == s.thc[lk]
            return np.where(same, lo, 0.0)
        return g5.NetG5.guard_lam(s, links, t)


def tasks(blk="S24B", nnet=NNET):
    return [[blk, hw, scen, c, i] for hw in ("ion2020", "ionproj") for scen in JIT for c in CTRLS for i in range(nnet)]


def run_id(t):
    return hashlib.sha256("s24b|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, scen, ctrl, idx = t
    if blk == "P24B": seeds = DEV
    nseed = int(hashlib.sha256(f"s24bnet|{blk}|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s24brun|{blk}|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    net = NetB(hw, scen, ctrl, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    o = net.run(); o["carry_abserr"] = float(np.mean(net.carry_err)) if net.carry_err else -1.0
    return dict(run=run_id(t), block=blk, hw=hw, scen=scen, ctrl=ctrl, idx=idx, **o)


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P24B", int(sys.argv[3]) if len(sys.argv) > 3 else 4)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
