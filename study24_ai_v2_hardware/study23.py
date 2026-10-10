"""Study 23: a global AI model and an RL router under the per-path safety guard, on correlated quantum networks.
Pre-registration: README_23.md (written after the dev pilot). Plan and stop rules: PLAN.md.

Network: the G-series 5 x 5 grid (best-of-candidates routing over shortest paths, exact physics, stationary links), but link
qualities are spatially CORRELATED (corr_net.py): rho_c = 0.7 (correlated) or 0 (independent control). Calibration data:
'dense' (rho_cal = 0.3, the G-series default) or 'thin' (rho_cal = 0.03, ten times fewer parity checks per epoch).

Arms (belief / router / guard):
  b    fleet prior / greedy / none           (the frozen Bayesian controller, reference)
  bg   fleet prior / greedy / Beta guard     (= G2 'calg')
  fg   fleet prior / greedy / fleet guard    (guard mixing prior = the fleet's Gaussian law: an informed prior WITHOUT AI;
                                              the control that separates 'any informed prior' from 'the AI's correlation learning')
  ag   AI prior    / greedy / AI guard
  rg   fleet prior / RL     / Beta guard
  arg  AI prior    / RL     / AI guard       (the full proposal)
  ar   AI prior    / RL     / none           (shows why the guard is needed)
AI prior: the global model (ai_weights_<hw>.npz, an MLP trained offline on separate simulated networks) predicts each link's
quality from its NEIGHBOURS' latest calibration window only. It always assumes rho_c = 0.7 (the correlation it was told
about), so in the rho_c = 0 control it is mis-specified on purpose.
AI guard (Proposition 6 with an informative mixing prior): for each link, the mixture likelihood ratio
M_t(lam) = Int Bin(K | N, p(lam')) pi_l(dlam') / Bin(K | N, p(lam)) with pi_l = N(AI prediction, AI residual sd) over a lambda
grid, frozen at the end of warm-up from neighbours' data only (independent of the link's own counts given the link qualities,
so M_t remains a test martingale for the link's own data); CS = {lam : M_t(lam) < Lmax / alpha}. The guarantee of Prop. 6
(P(a path ever delivers a bad pair) <= alpha) is unchanged; a good prior only makes the bound tighter.
RL router: a linear scoring policy over candidate paths, theta . phi(path), phi = [sum log estimate, sum log guard lower bound,
hops, sum (estimate - lower bound), guard pass margin at zero wait]; greedy = theta (1, 0, 0, 0, 0). theta is learned by the
cross-entropy method (policy search) on separate training networks (train_rl.py) and then frozen (policy_<hw>_<data>.json).
"""
import hashlib, json, os, sys
import numpy as np
from scipy.special import logsumexp
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), "/home/claude/s18c"):
    if p and p not in sys.path: sys.path.append(p)
import ptm_model as ptm
import drift_queue_des_g1 as g1
import drift_queue_des_g2 as g2
import corr_net as cn

ALPHA = 0.05; RHO_CAL = {"dense": 0.3, "thin": 0.03}; AI_RHO = 0.7
ARMS = {"b": ("fleet", "greedy", None), "bg": ("fleet", "greedy", "beta"), "fg": ("fleet", "greedy", "fleetmix"), "ag": ("ai", "greedy", "ai"),
        "rg": ("fleet", "rl", "beta"), "arg": ("ai", "rl", "ai"), "ar": ("ai", "rl", None)}
GREEDY = np.array([1.0, 0, 0, 0, 0])
SEEDS = (19231, 19232, 19233, 19234)       # fresh confirmatory; dev pilot 20231-20234; RL training networks 50000+
NNET = 64
_W = {}; _CHK = {}


def hw_consts(hw):
    P = g1.HW[hw][0]; sdf = (1 - P["F0"]) * 0.2
    return P, sdf, (4 * P["F0"] - 1) / 3 - g1.AMP * 0.5, np.sqrt((4 / 3 * sdf) ** 2 + g1.AMP ** 2 / 12)


def ai_weights(hw, data):
    if (hw, data) not in _W:
        z = np.load(os.path.join(HERE, f"ai_weights_{hw}.npz"))
        _W[(hw, data)] = {k[len(data) + 1:]: z[k] for k in z.files if k.startswith(data + "_")}
        _CHK[(hw, data)] = json.load(open(os.path.join(HERE, f"ai_check_{hw}.json")))[f"{data}_rho{AI_RHO}"]["ai_resid_sd_z"]
    return _W[(hw, data)], _CHK[(hw, data)]


def mlp(W, X):
    h = X; nlay = len(W) // 2
    for i in range(nlay - 1): h = np.maximum(0, h @ W[f"W{i}"] + W[f"b{i}"])
    return (h @ W[f"W{nlay - 1}"] + W[f"b{nlay - 1}"]).ravel()


def cs_lower_mix(N, K, r, lam_g, logpri, level):
    """Lower end of the mixture confidence sequence for lambda, per link, with per-link mixing prior logpri (nl, G)."""
    def loglik(lam):
        p = np.clip((1 + r * np.clip(lam, 0, 1)) / 2, 1e-12, 1 - 1e-12)
        return K[..., None] * np.log(p) + (N - K)[..., None] * np.log1p(-p) if np.ndim(lam) == 2 else K * np.log(p) + (N - K) * np.log1p(-p)
    LG = loglik(np.broadcast_to(lam_g[None, :], (len(N), len(lam_g))))
    logmix = logsumexp(LG + logpri, axis=1); thr = np.log(1 / level)
    hi = np.clip(lam_g[np.argmax(LG, axis=1)], 0, 1).astype(float); lo = np.zeros(len(N))
    for _ in range(45):
        mid = (lo + hi) / 2; inside = logmix - loglik(mid) < thr
        hi = np.where(inside, mid, hi); lo = np.where(inside, lo, mid)
    return np.where(N > 0, hi, 0.0)


class Net23(g1.Net):
    def __init__(s, hw, rho_c, data, arm, seed, theta=None):
        super().__init__(hw, "grid", 0, "cal", "best", seed)
        s.hw, s.rho_c, s.data, s.arm = hw, rho_c, data, arm
        s.belief, s.router, s.guard = ARMS[arm]
        P = s.P; s.Pc, s.sdf, s.lam_mu, s.sd_l = hw_consts(hw)
        nr = np.random.default_rng(list(seed[2:]) + [71])                       # same network for every arm (paired)
        z = cn.draw_z(nr, rho_c); F0 = np.clip(P["F0"] + s.sdf * z, 0.3, 0.9999)
        s.lam = np.clip((4 * F0 - 1) / 3 - g1.AMP * nr.uniform(0, 1, s.nl), 0, 1)
        s.rho_cal = RHO_CAL[data]
        s.theta = GREEDY if s.router == "greedy" else np.asarray(theta, float)
        s.W, s.s_ai = ai_weights(hw, data)
        s.pF_fleet = s.pF / s.pF.sum()
        s.lam_g = np.linspace(max(0.0, s.lam_mu - 8 * s.sd_l), min(1.0, s.lam_mu + 6 * s.sd_l), 241)
        s.N = np.zeros(s.nl); s.K = np.zeros(s.nl); s.acc_ep = -10 ** 9; s.lamlo = np.zeros(s.nl); s.gpri = None
        s.pstat = {}; s.abserr = []

    # ---------------- the global AI model
    def ai_z(s, n, k):
        lhat = np.clip((2 * (k + 0.5) / (n + 1) - 1) / s.r, 0, 1)
        X = np.c_[cn.features((lhat - s.lam_mu) / s.sd_l, n, s.sd_l), np.full(s.nl, AI_RHO)]
        return mlp(s.W, X)

    def epoch_data(s, e):
        if e == s.ep: return
        s.ep = e; P = s.P
        s.n = s.rng.poisson(s.rho_cal * P["R"] * g1.T, s.nl); s.kc = s.rng.binomial(s.n, (1 + s.r * s.lam) / 2)
        if s.belief == "fleet":
            lpr = s.lprior[None]                                                  # (1, 1, F)
        else:
            zp = s.ai_z(s.n, s.kc)                                                # neighbours only (features exclude self)
            mu = s.Pc["F0"] + s.sdf * zp; sd = s.sdf * s.s_ai
            g = np.exp(-0.5 * ((g1.v17.FG[None, :] - mu[:, None]) / sd) ** 2); g /= g.sum(1, keepdims=True)
            pr = (1 - g1.EPS) * g + g1.EPS * s.pF_fleet[None, :]
            lpr = (np.log(np.maximum(pr, 1e-300)) - np.log(len(g1.UG)))[:, None, :]    # (nl, 1, F)
        ll = s.kc[:, None, None] * s.lp[None] + (s.n - s.kc)[:, None, None] * s.lq[None] + lpr
        ll -= ll.max(axis=(1, 2), keepdims=True); w = np.exp(ll).reshape(s.nl, -1); w /= w.sum(1, keepdims=True)
        s.cdf = np.cumsum(w, axis=1); s.est = w @ s.lgrid.ravel()
        if e <= s.acc_ep: return
        s.acc_ep = e; s.N += s.n; s.K += s.kc
        gtype = s.guard or ("ai" if s.belief == "ai" else "beta")                 # bounds are also router features
        if gtype == "ai" and e == g1.WARM_EPOCH - 1:                                  # freeze the guard's prior (neighbours only)
            zp = s.ai_z(s.n, s.kc); mu = s.lam_mu + s.sd_l * zp; sd = s.sd_l * s.s_ai
            lp = -0.5 * ((s.lam_g[None, :] - mu[:, None]) / sd) ** 2; s.gpri = lp - logsumexp(lp, axis=1, keepdims=True)
        if gtype == "fleetmix" and s.gpri is None:                                    # fleet-informed prior, fixed in advance
            lp = -0.5 * ((s.lam_g - s.lam_mu) / s.sd_l) ** 2; lp = lp - logsumexp(lp)
            s.gpri = np.broadcast_to(lp[None, :], (s.nl, len(s.lam_g))).copy()
        if gtype in ("ai", "fleetmix") and s.gpri is not None:
            s.lamlo = cs_lower_mix(s.N, s.K, s.r, s.lam_g, s.gpri, ALPHA / s.Lmax)
        else:
            plo = g2.cs_lower(s.N, s.K, ALPHA / s.Lmax); s.lamlo = np.clip((2 * plo - 1) / s.r, 0, 1)

    def F0w(s, lam_links):
        L = len(lam_links); z = np.zeros(L)
        return float(ptm.delivered_F(np.asarray(lam_links)[None, :], z, z, 0.0, s.P["e"], np.inf, s.P["T2"])[0])

    def phi(s, c):
        lk = list(c); est = np.maximum(s.est[lk], 1e-9); lo = np.maximum(s.lamlo[lk], 1e-9)
        return np.array([np.log(est).sum(), np.log(lo).sum(), len(lk), (s.est[lk] - s.lamlo[lk]).sum(), s.F0w(s.lamlo[lk]) - s.tau])

    def pick(s, cset):
        if len(cset) == 1: return cset[0]
        if s.router == "greedy":
            return cset[int(np.argmax([np.log(np.maximum(s.est[list(c)], 1e-9)).sum() for c in cset]))]
        return cset[int(np.argmax([s.theta @ s.phi(c) for c in cset]))]

    def run(s):
        P = s.P; t = 0.0; H = g1.NEPOCH * g1.T
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0)
        arr = s.rng.exponential(1 / s.rate)
        while arr < H:
            t = max(t, arr); arr += s.rng.exponential(1 / s.rate)
            cset = s.cands[int(s.rng.integers(len(s.cands)))]
            s.epoch_data(int(t // g1.T) - 1)
            path = s.pick(cset)
            meas = t >= g1.WARM_EPOCH * g1.T
            if meas: out["requests"] += 1; s.abserr.append(float(np.abs(s.est[list(path)] - s.lam[list(path)]).mean()))
            op = cset[int(np.argmax([np.log(np.maximum(s.lam[list(c)], 1e-9)).sum() for c in cset]))]; to = t
            for _ in range(g1.BUDGET):
                w1, w2, hold, to = s.chains(s.orng, to, len(op))
                if s.trueF(op, w1, w2, hold) >= s.tau:
                    if meas: out["oracle_qual"] += 1
                    break
            for _ in range(g1.BUDGET):
                w1, w2, hold, t = s.chains(s.rng, t, len(path)); s.epoch_data(int(t // g1.T) - 1)
                Ft = s.trueF(path, w1, w2, hold); ld = s.draws(path)
                Fs = ptm.delivered_F(ld, w1, w2, hold, P["e"], np.inf, P["T2"]); pbad = ((Fs < s.tau).sum() + 0.5) / (g1.M + 1)
                thr = s.choose_t(); s.pb[s.nb % g1.WIN] = pbad; s.nb += 1
                ok = pbad <= thr
                if ok and s.guard:
                    Fg = float(ptm.delivered_F(s.lamlo[list(path)][None, :], w1, w2, hold, P["e"], np.inf, P["T2"])[0])
                    if Fg < s.tau:
                        ok = False
                        if meas: out["guard_blocks"] += 1
                if ok:
                    if meas:
                        bad = int(Ft < s.tau); out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                        st = s.pstat.setdefault(path, [0, 0]); st[0] += 1; st[1] += bad
                    break
        v = list(s.pstat.values())
        out["paths_delivered"] = sum(1 for x in v if x[0] > 0); out["paths_bad"] = sum(1 for x in v if x[1] > 0)
        out["max_path_bad"] = max([x[1] for x in v] or [0]); out["est_abserr"] = float(np.mean(s.abserr)) if s.abserr else -1.0
        return out


DEV = (20231, 20232, 20233, 20234)


def policy(hw, data, arm):
    """Frozen RL policy learned by train_rl.py for this hardware, data regime and belief ('rg' or 'arg'; 'ar' uses 'arg')."""
    f = os.path.join(HERE, f"policy_{hw}_{data}_{'rg' if arm == 'rg' else 'arg'}.json")
    if not os.path.exists(f): raise FileNotFoundError(f)
    return json.load(open(f))["theta"]


def tasks_pilot(nnet=8):
    return [["P23", hw, rho, data, arm, i] for hw in ("ion2020", "ionproj") for rho in (0.7, 0.0) for data in ("dense", "thin")
            for arm in ARMS for i in range(nnet)]


def tasks():
    return [["S23", hw, rho, data, arm, i] for hw in ("ion2020", "ionproj") for rho in (0.7, 0.0) for data in ("dense", "thin")
            for arm in ARMS for i in range(NNET)]


def run_id(t):
    return hashlib.sha256("s23|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS, theta=None):
    blk, hw, rho, data, arm, idx = t
    if blk == "P23": seeds = DEV                                                   # dev pilot uses the dev seeds
    nseed = int(hashlib.sha256(f"s23net|{hw}|{rho}|{data}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s23run|{hw}|{rho}|{data}|{idx}".encode()).hexdigest()[:8], 16)
    th = theta if theta is not None else (list(GREEDY) if ARMS[arm][1] == 'greedy' else policy(hw, data, arm))
    net = Net23(hw, rho, data, arm, [rseed, seeds[1], nseed, seeds[0] + seeds[2]], theta=th)
    return dict(run=run_id(t), block=blk, hw=hw, rho=rho, data=data, arm=arm, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks_pilot()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
