"""Study 24 Block A: a better AI (v2) under the per-path guard, across five hardware types and five link-quality patterns,
three of which the AI never saw in training. Pre-registration: README_24.md.

Arms (all greedy routing; the RL router is not re-tested: Study 23 measured it at +0.34 points):
  b    fleet belief / no guard                      (frozen C2 controller; shows the risk without a guard)
  bg   fleet belief / Beta(1/2,1/2) mixture guard   (today's guarded controller, G2)
  fg   fleet belief / fleet-Gaussian mixture guard  (informed prior without any AI; Study 23's key control)
  ag1  AI v1 belief / AI v1 guard                   (exactly Study 23's 'ag': latest window only, told rho = 0.7, frozen at warm-up)
  lg   linear-model belief / hedged guard           (AI v2's machinery with LINEAR regressions: is the neural network needed?)
  kg   known-fleet-law belief / fleet-Gaussian guard (the belief uses the fleet's true Gaussian law instead of the EB estimate:
                                                    separates "the AI belief knows the fleet spread" from "the AI learns links")
  ag2  AI v2 belief / hedged guard                  (the improved proposal)
Latency (added before the confirmatory run, at the advisor's request; recorded only, no random draws, so it cannot change any
delivery): per delivered request, end-to-end latency = completion time - request arrival = queue wait (requests are served one
at a time) + service time (entanglement generation over all attempts, including attempts the controller or guard rejected);
attempts used; memory hold time of the delivered pair; and the oracle's service time on its own stream as the reference.
Classical signalling delay is not modelled (it adds a fixed per-hop delay to every arm alike).
AI v2 / linear model (ai_model24.py): predict a link's standardised quality, and their own uncertainty, from OTHER links'
ACCUMULATED calibration counts (features2 in corr_net24.py).
Hedged guard (Proposition 6 with an informative, hedged mixing prior; the code allows J pre-set refresh epochs with a union
  bound, J = 1 is used: dev runs showed that refreshing later did not pay for the extra ln J in the threshold):
  at the end of epoch e_1 = 2 (the last warm-up epoch) the prior pi(lambda) = 0.5 N(mu, sd) + 0.25 N(fleet mean, fleet sd)
  + 0.25 Jeffreys (on the parity probability) is frozen, where (mu, sd) come from the model applied to OTHER links' data
  only. Given the link qualities, other links' counts are independent of this link's counts, so each
  M^j_t(lam) = Int Lik_t(lam') pi_j(dlam') / Lik_t(lam) (this link's own counts from time 0) is a test martingale and
  CS^j = {lam : M^j_t(lam) < J Lmax / alpha} covers lambda at all times with probability >= 1 - alpha/(J Lmax) (Ville).
  The guard uses the largest lower end among the CS^j available; by the union bound over j and the path's <= Lmax links,
  P(a path ever delivers a bad pair) <= alpha, exactly as Prop. 6, whatever the AI predicts. The hedge caps the cost of a
  wrong prediction at ln 2 (vs the fleet-Gaussian or Jeffreys component alone, each at weight 1/4: ln 4) in the threshold.
"""
import hashlib, json, os, sys
import numpy as np
from scipy.special import logsumexp
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), "/home/claude/s18c"):
    if p and p not in sys.path: sys.path.append(p)
import hw24
import ptm_model as ptm
import drift_queue_des_g1 as g1
import drift_queue_des_g2 as g2
import corr_net as cn1
import corr_net24 as cn
import study23 as s23
import ai_model24 as am

ALPHA = 0.05; REFRESH = (2,); J = len(REFRESH); W_AI = 0.5     # chosen on the cloud dev runs (README_24.md, "Design choices")
ARMS = {"b": ("fleet", None), "bg": ("fleet", "beta"), "fg": ("fleet", "fleetmix"), "kg": ("known", "fleetmix"), "ag1": ("ai1", "ai1"),
        "lg": ("lin", "hedge"), "ag2": ("mlp", "hedge")}
PATS = tuple(cn.PATTERNS)                        # ind, field, short, region, outlier
SEEDS = (19241, 19242, 19243, 19244)             # fresh confirmatory; cloud dev pilot 20241-20244
DEV = (20241, 20242, 20243, 20244)
NNET = 64
LAT_BINS = np.r_[0.0, np.logspace(-3, 4, 141)]     # seconds; latency histograms (bin 0 = [0, 1 ms))
_W2 = {}; _W1 = {}


def w2(hw, kind):
    if hw not in _W2: _W2[hw] = np.load(os.path.join(HERE, f"ai2_{hw}.npz"))
    z = _W2[hw]; return {k[len(kind) + 1:]: z[k] for k in z.files if k.startswith(kind + "_")}


def w1(hw):
    if hw not in _W1:
        z = np.load(os.path.join(HERE, f"ai_weights_{hw}.npz")); W = {k[6:]: z[k] for k in z.files if k.startswith("dense_")}
        sd = json.load(open(os.path.join(HERE, f"ai_check_{hw}.json")))["dense_rho0.7"]["ai_resid_sd_z"]; _W1[hw] = (W, sd)
    return _W1[hw]


class Net24(g1.Net):
    def __init__(s, hw, pat, arm, seed):
        super().__init__(hw, "grid", 0, "cal", "best", seed)
        s.hw, s.pat, s.arm = hw, pat, arm; s.belief, s.guard = ARMS[arm]
        P = s.P; s.Pc, s.r_, s.sdf, s.lam_mu, s.sd_l = hw24.consts(hw)
        nr = np.random.default_rng(list(seed[2:]) + [71])                     # same network for every arm (paired)
        s.z_true = cn.PATTERNS[pat](nr); s.lam = hw24.lam_from_z(nr, hw, s.z_true)
        s.rho_cal = hw24.RHO_CAL
        s.pF_fleet = s.pF / s.pF.sum()
        s.lam_g = np.linspace(max(0.0, s.lam_mu - 8 * s.sd_l), min(1.0, s.lam_mu + 6 * s.sd_l), 241)
        lp = -0.5 * ((s.lam_g - s.lam_mu) / s.sd_l) ** 2; s.fleet_lp = lp - logsumexp(lp)
        pg = np.clip((1 + s.r * s.lam_g) / 2, 1e-9, 1 - 1e-9); jl = -0.5 * np.log(pg * (1 - pg)); s.jef_lp = jl - logsumexp(jl)
        s.N = np.zeros(s.nl); s.K = np.zeros(s.nl); s.acc_ep = -10 ** 9; s.lamlo = np.zeros(s.nl)
        s.gpri = None; s.gpris = []
        if s.belief in ("lin", "mlp"): s.W2 = w2(hw, s.belief)
        if s.belief == "ai1": s.W1, s.s_ai1 = w1(hw)
        s.pstat = {}; s.abserr = []; s.prior_err = []

    # ---------------- models
    def ai1_z(s, n, k):                                                       # Study 23's v1 (latest window, rho = 0.7)
        lhat = np.clip((2 * (k + 0.5) / (n + 1) - 1) / s.r, 0, 1)
        X = np.c_[cn1.features((lhat - s.lam_mu) / s.sd_l, n, s.sd_l), np.full(s.nl, s23.AI_RHO)]
        return s23.mlp(s.W1, X)

    def ai2_z(s):                                                             # v2 / linear: other links' accumulated data
        zh, v = hw24.zv(s.hw, s.N, s.K); return am.predict(s.W2, cn.features2(zh, v))

    def belief_prior(s, mu_z, sd_z):
        mu = s.Pc["F0"] + s.sdf * mu_z; sd = s.sdf * sd_z
        g = np.exp(-0.5 * ((g1.v17.FG[None, :] - mu[:, None]) / sd[:, None]) ** 2); g /= np.maximum(g.sum(1, keepdims=True), 1e-300)
        pr = (1 - g1.EPS) * g + g1.EPS * s.pF_fleet[None, :]
        return (np.log(np.maximum(pr, 1e-300)) - np.log(len(g1.UG)))[:, None, :]

    def epoch_data(s, e):
        if e == s.ep: return
        s.ep = e; P = s.P
        s.n = s.rng.poisson(s.rho_cal * P["R"] * g1.T, s.nl); s.kc = s.rng.binomial(s.n, (1 + s.r * s.lam) / 2)
        first = e > s.acc_ep
        if first: s.acc_ep = e; s.N += s.n; s.K += s.kc
        if s.belief == "fleet":
            lpr = s.lprior[None]
        elif s.belief == "known":
            lpr = s.belief_prior(np.zeros(s.nl), np.ones(s.nl))
        elif s.belief == "ai1":
            lpr = s.belief_prior(s.ai1_z(s.n, s.kc), np.full(s.nl, s.s_ai1))
        else:
            if first or not hasattr(s, "_mz"): s._mz, s._sz = s.ai2_z()
            lpr = s.belief_prior(s._mz, s._sz)
            if first and e >= g1.WARM_EPOCH - 1: s.prior_err.append(float(np.sqrt(np.mean((s._mz - s.z_true) ** 2))))
        ll = s.kc[:, None, None] * s.lp[None] + (s.n - s.kc)[:, None, None] * s.lq[None] + lpr
        ll -= ll.max(axis=(1, 2), keepdims=True); w = np.exp(ll).reshape(s.nl, -1); w /= w.sum(1, keepdims=True)
        s.cdf = np.cumsum(w, axis=1); s.est = w @ s.lgrid.ravel()
        if not first or s.guard is None: return
        if s.guard == "ai1":
            if e == g1.WARM_EPOCH - 1:
                zp = s.ai1_z(s.n, s.kc); mu = s.lam_mu + s.sd_l * zp; sd = s.sd_l * s.s_ai1
                lp = -0.5 * ((s.lam_g[None, :] - mu[:, None]) / sd) ** 2; s.gpri = lp - logsumexp(lp, axis=1, keepdims=True)
            s.lamlo = s23.cs_lower_mix(s.N, s.K, s.r, s.lam_g, s.gpri, ALPHA / s.Lmax) if s.gpri is not None else np.zeros(s.nl)
        elif s.guard == "fleetmix":
            s.lamlo = s23.cs_lower_mix(s.N, s.K, s.r, s.lam_g, np.broadcast_to(s.fleet_lp, (s.nl, len(s.lam_g))), ALPHA / s.Lmax)
        elif s.guard == "hedge":
            if e in REFRESH:
                mu = s.lam_mu + s.sd_l * s._mz; sd = s.sd_l * s._sz
                la = -0.5 * ((s.lam_g[None, :] - mu[:, None]) / sd[:, None]) ** 2; la = la - logsumexp(la, axis=1, keepdims=True)
                wo = (1 - W_AI) / 2
                lp = la if W_AI >= 1 else logsumexp(np.stack([np.log(W_AI) + la, np.broadcast_to(np.log(wo) + s.fleet_lp, la.shape),
                                                              np.broadcast_to(np.log(wo) + s.jef_lp, la.shape)]), axis=0)
                s.gpris.append(lp)
            lo = [s23.cs_lower_mix(s.N, s.K, s.r, s.lam_g, lp, ALPHA / (J * s.Lmax)) for lp in s.gpris]
            s.lamlo = np.max(lo, axis=0) if lo else np.zeros(s.nl)
        else:
            plo = g2.cs_lower(s.N, s.K, ALPHA / s.Lmax); s.lamlo = np.clip((2 * plo - 1) / s.r, 0, 1)

    def run(s):
        P = s.P; t = 0.0; H = g1.NEPOCH * g1.T
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0)
        arr = s.rng.exponential(1 / s.rate)
        L = dict(e2e=[], queue=[], svc=[], att=[], hold=[], osvc=[])                  # latency records (no random draws)
        while arr < H:
            a0 = arr; t = max(t, arr); arr += s.rng.exponential(1 / s.rate); t_start = t
            cset = s.cands[int(s.rng.integers(len(s.cands)))]
            s.epoch_data(int(t // g1.T) - 1)
            path = cset[int(np.argmax([np.log(np.maximum(s.est[list(c)], 1e-9)).sum() for c in cset]))] if len(cset) > 1 else cset[0]
            meas = t >= g1.WARM_EPOCH * g1.T
            if meas: out["requests"] += 1; s.abserr.append(float(np.abs(s.est[list(path)] - s.lam[list(path)]).mean()))
            op = cset[int(np.argmax([np.log(np.maximum(s.lam[list(c)], 1e-9)).sum() for c in cset]))]; to = t
            for _ in range(g1.BUDGET):
                w1_, w2_, hold, to = s.chains(s.orng, to, len(op))
                if s.trueF(op, w1_, w2_, hold) >= s.tau:
                    if meas: out["oracle_qual"] += 1; L["osvc"].append(to - t_start)
                    break
            for att in range(g1.BUDGET):
                w1_, w2_, hold, t = s.chains(s.rng, t, len(path)); s.epoch_data(int(t // g1.T) - 1)
                Ft = s.trueF(path, w1_, w2_, hold); ld = s.draws(path)
                Fs = ptm.delivered_F(ld, w1_, w2_, hold, P["e"], np.inf, P["T2"]); pbad = ((Fs < s.tau).sum() + 0.5) / (g1.M + 1)
                thr = s.choose_t(); s.pb[s.nb % g1.WIN] = pbad; s.nb += 1
                ok = pbad <= thr
                if ok and s.guard:
                    Fg = float(ptm.delivered_F(s.lamlo[list(path)][None, :], w1_, w2_, hold, P["e"], np.inf, P["T2"])[0])
                    if Fg < s.tau:
                        ok = False
                        if meas: out["guard_blocks"] += 1
                if ok:
                    if meas:
                        bad = int(Ft < s.tau); out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                        st = s.pstat.setdefault(path, [0, 0]); st[0] += 1; st[1] += bad
                        L["e2e"].append(t - a0); L["queue"].append(t_start - a0); L["svc"].append(t - t_start)
                        L["att"].append(att + 1); L["hold"].append(float(hold))
                    break
        v = list(s.pstat.values())
        out["paths_delivered"] = sum(1 for x in v if x[0] > 0); out["paths_bad"] = sum(1 for x in v if x[1] > 0)
        out["max_path_bad"] = max([x[1] for x in v] or [0]); out["est_abserr"] = float(np.mean(s.abserr)) if s.abserr else -1.0
        out["prior_rmse_z"] = float(np.mean(s.prior_err)) if s.prior_err else -1.0
        e = np.array(L["e2e"])
        for k in ("e2e", "queue", "svc", "att", "hold", "osvc"):
            out[f"lat_{k}_mean"] = float(np.mean(L[k])) if L[k] else -1.0
        for q in (50, 95, 99): out[f"lat_e2e_p{q}"] = float(np.percentile(e, q)) if len(e) else -1.0
        out["lat_e2e_hist"] = ";".join(str(int(c)) for c in np.histogram(e, LAT_BINS)[0])     # pooled percentiles in the analysis
        out["lat_osvc_hist"] = ";".join(str(int(c)) for c in np.histogram(np.array(L["osvc"]), LAT_BINS)[0])
        return out


def tasks(blk="S24", nnet=NNET):
    return [[blk, hw, pat, arm, i] for hw in hw24.HWS for pat in PATS for arm in ARMS for i in range(nnet)]


def run_id(t):
    return hashlib.sha256("s24|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, idx = t
    if blk == "P24": seeds = DEV
    nseed = int(hashlib.sha256(f"s24net|{blk}|{hw}|{pat}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s24run|{blk}|{hw}|{pat}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net24(hw, pat, arm, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P24", int(sys.argv[3]) if len(sys.argv) > 3 else 4)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
