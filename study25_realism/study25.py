"""Study 25 ("realism"): four stress tests of the guard and the learned prior, pre-registered in README_25.md.

Block M (model error; weak spot 2). The controller AND the guard use an OPTIMISTIC physics model it was never told is wrong:
    memory T2_model = T2 (1 + kappa), gate error e_model = e / (1 + kappa), kappa in {0, 0.1, 0.25, 0.5}.
  The guard may DECLARE robustness D: it evaluates the delivered fidelity with T2_model/(1 + D) and e_model (1 + D).
  Prediction (monotonicity of the fidelity map in T2 and e): the guard is safe whenever D >= kappa; below that it can fail.
  Arms: kg (known-law belief, fleet-Gaussian guard prior, see Study 24) with D in {0, 0.1, 0.25, 0.5}; b (no guard).
Block K (finite characterisation campaign; weak spot 3). The 'known fleet law' of Study 24 is replaced by a law ESTIMATED from
  a campaign of K dedicated calibration windows (each a random fleet link measured at the full pair rate for TC = 1000 s):
  moment estimates of the fleet mean and spread (Prop. 3), then used exactly where kg used the true law (belief and guard
  prior). Arms: bg, kg, c16, c64, c256, c1024. Prop. 3 predicts how large K must be (identifiability I >= 3).
Block T (shared measurement noise; weak spot 4). Each node adds a common-mode shift to the parity probability of every link
  touching it, independently each epoch (link shift sd = c x the per-epoch binomial sd, c in {0, 0.5, 2}): neighbours' data
  are then NOT independent of a link's own data given the link qualities. Arms: bg, kg, ag2 (Study 24's AI v2, prior from
  neighbours' data up to the end of warm-up, confidence sequence on ALL own data) and ag2t ('time-split': the confidence
  sequence uses only own data from AFTER the prior was frozen, so the prior is independent of the data it is combined with
  whenever the shared noise does not persist across epochs), kgphi and ag2phi (the guard DECLARES the over-dispersion
  phi = 1 + c^2 that this noise causes and deflates its counts by phi, a quasi-likelihood correction: approximate, not a
  theorem). Code review before the pilot showed that this noise also makes a link's OWN counts over-dispersed, so it breaks
  every guard that assumes binomial counts, not only the AI's prior; Block T therefore asks (i) whether the AI prior adds
  failures beyond the baseline guards, and (ii) whether a declared over-dispersion restores safety.
Block C (network realism; weak spot 7). Conditions: ser0 (one request at a time, no signalling delay: the G-series model),
  ser50 (50 km per hop, classical signalling at 5 us/km), par1 (requests served in parallel whenever their paths' links are
  free, links busy while used, 50 km/hop), par4 (as par1 with 4x the request rate). Signalling delay: every attempt adds the
  one-hop delay to each link's storage before the swap and the full-path delay to the hold of the first chain and to every
  link wait of the second chain (an approximation of its storage while messages travel); truth, controller and guard all
  use the same waits. In parallel mode requests are processed in arrival order (the controller's threshold window is
  updated in processing order, not strictly in simulated time). Arms: bg, kg, ag2.
Common to all blocks: 5 x 5 grid, greedy best-path routing, exact physics (PTM model), stationary links, 30 epochs of 100 s,
3 warm-up epochs. Calibration counts are pre-drawn per epoch (so the state at any time is a deterministic function of the
epoch, which parallel service needs). Networks are paired across arms and configurations within a block.
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
import corr_net24 as cn
import study23 as s23
import study24 as s24
import ai_model24 as am

ALPHA = 0.05; TC = 1000.0; C_FIBRE = 5e-6          # s per km
KAPPAS = (0.0, 0.1, 0.25, 0.5); DECL = (0.0, 0.1, 0.25, 0.5); KS = (16, 64, 256, 1024); NOISE = (0.0, 0.5, 2.0)
CONDS = {"ser0": ("serial", 1, 0.0), "ser50": ("serial", 1, 50.0), "par1": ("parallel", 1, 50.0), "par4": ("parallel", 4, 50.0)}
SEEDS = (19261, 19262, 19263, 19264)               # fresh confirmatory; dev pilot 20261-20264
DEV = (20261, 20262, 20263, 20264)
NNET = 32


def configs():
    """block -> list of (hw, pattern, arm, cfg)."""
    M = [(hw, "ind", "kg", f"k{k}_d{d}") for hw in ("ion2020", "nv2", "siv") for k in KAPPAS for d in DECL] + \
        [(hw, "ind", "b", f"k{k}_d0.0") for hw in ("ion2020", "nv2", "siv") for k in KAPPAS]
    K = [(hw, "ind", a, "-") for hw in ("ion2020", "nv2", "siv") for a in ("bg", "kg", "c16", "c64", "c256", "c1024")]
    T = [(hw, "field", a, f"c{c}") for hw in ("ion2020", "nv2", "siv") for c in NOISE for a in ("bg", "kg", "ag2", "ag2t", "kgphi", "ag2phi")]
    C = [(hw, "field", a, cond) for hw in ("ion2020", "ionproj", "nv2", "siv") for cond in CONDS for a in ("bg", "kg", "ag2")]
    return {"M": M, "K": K, "T": T, "C": C}


def parse(cfg):
    o = dict(kappa=0.0, D=0.0, noise=0.0, mode="serial", ratemult=1, km=0.0)
    if cfg.startswith("k"):
        a, b = cfg.split("_"); o["kappa"] = float(a[1:]); o["D"] = float(b[1:])
    elif cfg.startswith("c") and cfg != "-": o["noise"] = float(cfg[1:])
    elif cfg in CONDS: o["mode"], o["ratemult"], o["km"] = CONDS[cfg]
    return o


class Net25(s24.Net24):
    def __init__(s, hw, pat, arm, cfg, seed):
        base = {"ag2t": "ag2", "ag2phi": "ag2", "kgphi": "kg"}.get(arm, "kg" if arm.startswith("c") and arm[1:].isdigit() else arm)
        super().__init__(hw, pat, base, seed)
        s.arm25, s.cfg = arm, cfg; s.o = parse(cfg); s.tsplit = arm == "ag2t"
        s.phi = (1 + s.o["noise"] ** 2) if arm.endswith("phi") else 1.0      # declared over-dispersion (fleet-average value)
        s.campK = int(arm[1:]) if arm.startswith("c") and arm[1:].isdigit() else None
        P = s.P; k, D = s.o["kappa"], s.o["D"]
        s.Pm = dict(P, T2=P["T2"] * (1 + k), e=P["e"] / (1 + k))                  # controller's (optimistic) model
        s.Pd = dict(s.Pm, T2=s.Pm["T2"] / (1 + D), e=s.Pm["e"] * (1 + D))       # guard's declared-robust model
        s.rate25 = s.rate * s.o["ratemult"]
        s.d_hop = s.o["km"] * C_FIBRE
        # ---- pre-drawn calibration counts per epoch (e = -1 .. NEPOCH + 1), with optional node common-mode noise
        er = np.random.default_rng(list(seed[2:]) + [131]); s.E0 = -1; s.NE = g1.NEPOCH + 12
        nbar = s.rho_cal * P["R"] * g1.T; p0 = (1 + s.r * s.lam_mu) / 2; sd_bin = np.sqrt(p0 * (1 - p0) / nbar)
        A = np.zeros((cn.NL, len(cn.NODES)))
        for l, (u, v) in enumerate(cn.ENDS): A[l, cn.cn._NIDX[u]] = 0.5; A[l, cn.cn._NIDX[v]] = 0.5
        s.n_e = np.zeros((s.NE, s.nl), int); s.k_e = np.zeros((s.NE, s.nl), int); pl = (1 + s.r * s.lam) / 2
        for j in range(s.NE):
            n = er.poisson(nbar, s.nl); shift = A @ er.normal(0, s.o["noise"] * sd_bin * np.sqrt(2), len(cn.NODES))
            s.n_e[j] = n; s.k_e[j] = er.binomial(n, np.clip(pl + shift, 1e-6, 1 - 1e-6))
        s.N_c = np.cumsum(s.n_e, 0); s.K_c = np.cumsum(s.k_e, 0); s.cache = {}; s.emax = -10
        if s.campK: s.campaign(np.random.default_rng(list(seed[2:]) + [s.campK, 211]))
        s.ai_prior = None; s.freeze = s24.REFRESH[0]

    def campaign(s, rng):
        """moment estimates of the fleet law from K full-rate windows of TC seconds (Prop. 3)."""
        K = s.campK; P = s.P
        z = rng.normal(0, 1, K); lam = hw24.lam_from_z(rng, s.hw, z)
        n = np.maximum(rng.poisson(P["R"] * TC, K), 1); k = rng.binomial(n, (1 + s.r * lam) / 2)
        ph = k / n; lh = (2 * ph - 1) / s.r; vw = 4 * ph * (1 - ph) / (n * s.r ** 2)
        mu_l = float(lh.mean()); s2 = max(float(lh.var(ddof=1) - vw.mean()), 1e-8)
        sdf2 = max(s2 - g1.AMP ** 2 / 12, 1e-8) * 9 / 16
        s.c_muF = (3 * (mu_l + g1.AMP / 2) + 1) / 4; s.c_sdF = float(np.sqrt(sdf2)); s.c_mul = mu_l; s.c_sdl = float(np.sqrt(s2))
        lp = -0.5 * ((s.lam_g - mu_l) / s.c_sdl) ** 2; s.camp_lp = lp - logsumexp(lp)

    # ---------------- per-epoch state (deterministic in e)
    def st(s, e):
        s.emax = max(s.emax, int(e)); e = int(min(max(e, s.E0), s.E0 + s.NE - 1)); j = e - s.E0
        if j in s.cache: return s.cache[j]
        n, k = s.n_e[j], s.k_e[j]; Nc, Kc = s.N_c[j], s.K_c[j]
        b = s.belief
        if s.campK: lpr = s.belief_prior(np.full(s.nl, (s.c_muF - s.Pc["F0"]) / s.sdf), np.full(s.nl, s.c_sdF / s.sdf))
        elif b == "fleet": lpr = s.lprior[None]
        elif b == "known": lpr = s.belief_prior(np.zeros(s.nl), np.ones(s.nl))
        else:
            zh, v = hw24.zv(s.hw, Nc, Kc); mz, sz = am.predict(s.W2, cn.features2(zh, v)); lpr = s.belief_prior(mz, sz)
            if e == s.freeze and s.ai_prior is None: s.ai_prior = (mz, sz)
        ll = k[:, None, None] * s.lp[None] + (n - k)[:, None, None] * s.lq[None] + lpr
        ll -= ll.max(axis=(1, 2), keepdims=True); w = np.exp(ll).reshape(s.nl, -1); w /= w.sum(1, keepdims=True)
        cdf = np.cumsum(w, axis=1); est = w @ s.lgrid.ravel()
        g = s.guard; Ng, Kg = Nc / s.phi, Kc / s.phi                          # declared over-dispersion: effective counts
        if g is None: lo = np.zeros(s.nl)
        elif s.campK: lo = s23.cs_lower_mix(Ng, Kg, s.r, s.lam_g, np.broadcast_to(s.camp_lp, (s.nl, len(s.lam_g))), ALPHA / s.Lmax)
        elif g == "fleetmix": lo = s23.cs_lower_mix(Ng, Kg, s.r, s.lam_g, np.broadcast_to(s.fleet_lp, (s.nl, len(s.lam_g))), ALPHA / s.Lmax)
        elif g == "hedge":
            if e < s.freeze: lo = np.zeros(s.nl)
            else:
                if s.ai_prior is None: s.st(s.freeze)                         # prior frozen from data up to the end of warm-up
                mz, sz = s.ai_prior; mu = s.lam_mu + s.sd_l * mz; sd = s.sd_l * sz
                la = -0.5 * ((s.lam_g[None, :] - mu[:, None]) / sd[:, None]) ** 2; la = la - logsumexp(la, axis=1, keepdims=True)
                wo = (1 - s24.W_AI) / 2
                lp = logsumexp(np.stack([np.log(s24.W_AI) + la, np.broadcast_to(np.log(wo) + s.fleet_lp, la.shape),
                                         np.broadcast_to(np.log(wo) + s.jef_lp, la.shape)]), axis=0)
                jf = s.freeze - s.E0
                No, Ko = (Nc - s.N_c[jf], Kc - s.K_c[jf]) if s.tsplit else (Ng, Kg)
                lo = s23.cs_lower_mix(No, Ko, s.r, s.lam_g, lp, ALPHA / s.Lmax) if s.tsplit is False or e > s.freeze else np.zeros(s.nl)
        else:
            plo = g2.cs_lower(Ng, Kg, ALPHA / s.Lmax); lo = np.clip((2 * plo - 1) / s.r, 0, 1)
        s.cache[j] = (cdf, est, lo); return s.cache[j]

    def draws_at(s, links, cdf):
        out = np.empty((g1.M, len(links)))
        for jj, l in enumerate(links):
            idx = np.minimum(np.searchsorted(cdf[l], s.rng.random(g1.M)), cdf.shape[1] - 1); out[:, jj] = s.lgrid.ravel()[idx]
        return out

    def chains_d(s, rng, t, L):
        w1, w2, hold, t2 = s.chains(rng, t, L); dc = L * s.d_hop
        return w1 + s.d_hop, w2 + s.d_hop + dc, hold + dc, t2 + dc

    def run(s):
        P = s.P; H = g1.NEPOCH * g1.T; par = s.o["mode"] == "parallel"
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0)
        L = dict(e2e=[], queue=[], svc=[], att=[], hold=[], osvc=[])
        busy = np.zeros(s.nl); obusy = np.zeros(s.nl); tser = 0.0; oser = 0.0
        arr = s.rng.exponential(1 / s.rate25)
        while arr < H:
            a0 = arr; arr += s.rng.exponential(1 / s.rate25)
            cset = s.cands[int(s.rng.integers(len(s.cands)))]
            _, est0, _ = s.st(int((a0 if par else max(a0, tser)) // g1.T) - 1)
            path = cset[int(np.argmax([np.log(np.maximum(est0[list(c)], 1e-9)).sum() for c in cset]))] if len(cset) > 1 else cset[0]
            op = cset[int(np.argmax([np.log(np.maximum(s.lam[list(c)], 1e-9)).sum() for c in cset]))]
            lk, olk = list(path), list(op)
            t = max(a0, busy[lk].max()) if par else max(a0, tser); t_start = t
            to = max(a0, obusy[olk].max()) if par else t; to_start = to
            meas = t_start >= g1.WARM_EPOCH * g1.T
            if meas: out["requests"] += 1; s.abserr.append(float(np.abs(est0[lk] - s.lam[lk]).mean()))
            for _ in range(g1.BUDGET):
                w1_, w2_, hold, to = s.chains_d(s.orng, to, len(op))
                if s.trueF(op, w1_, w2_, hold) >= s.tau:
                    if meas: out["oracle_qual"] += 1; L["osvc"].append(to - to_start)
                    break
            if par: obusy[olk] = to
            for att in range(g1.BUDGET):
                w1_, w2_, hold, t = s.chains_d(s.rng, t, len(path)); cdf, est, lamlo = s.st(int(t // g1.T) - 1)
                Ft = s.trueF(path, w1_, w2_, hold); ld = s.draws_at(lk, cdf)
                Fs = ptm.delivered_F(ld, w1_, w2_, hold, s.Pm["e"], np.inf, s.Pm["T2"]); pbad = ((Fs < s.tau).sum() + 0.5) / (g1.M + 1)
                thr = s.choose_t(); s.pb[s.nb % g1.WIN] = pbad; s.nb += 1
                ok = pbad <= thr
                if ok and s.guard:
                    Fg = float(ptm.delivered_F(lamlo[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0])
                    if Fg < s.tau:
                        ok = False
                        if meas: out["guard_blocks"] += 1
                if ok:
                    if meas:
                        bad = int(Ft < s.tau); out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                        st_ = s.pstat.setdefault(path, [0, 0]); st_[0] += 1; st_[1] += bad
                        L["e2e"].append(t - a0); L["queue"].append(t_start - a0); L["svc"].append(t - t_start); L["att"].append(att + 1); L["hold"].append(float(hold))
                    break
            if par: busy[lk] = t
            else: tser = t
        v = list(s.pstat.values())
        out["paths_delivered"] = sum(1 for x in v if x[0] > 0); out["paths_bad"] = sum(1 for x in v if x[1] > 0)
        out["max_path_bad"] = max([x[1] for x in v] or [0]); out["est_abserr"] = float(np.mean(s.abserr)) if s.abserr else -1.0
        e = np.array(L["e2e"])
        for kk in ("e2e", "queue", "svc", "att", "hold", "osvc"): out[f"lat_{kk}_mean"] = float(np.mean(L[kk])) if L[kk] else -1.0
        for q in (50, 95, 99): out[f"lat_e2e_p{q}"] = float(np.percentile(e, q)) if len(e) else -1.0
        out["lat_e2e_hist"] = ";".join(str(int(c)) for c in np.histogram(e, s24.LAT_BINS)[0])
        out["max_epoch"] = s.emax; out["epoch_clamped"] = int(s.emax > s.E0 + s.NE - 1)
        # same columns in every row (the PSC runner appends rows under the first row's header)
        out["camp_muF_err"] = s.c_muF - s.Pc["F0"] if s.campK else float("nan")
        out["camp_sdF_ratio"] = s.c_sdF / s.sdf if s.campK else float("nan")
        return out


def tasks(blk_prefix="S25", nnet=NNET):
    out = []
    for b, cl in configs().items():
        for (hw, pat, arm, cfg) in cl:
            for i in range(nnet): out.append([f"{blk_prefix}{b}", hw, pat, arm, cfg, i])
    return out


def run_id(t):
    return hashlib.sha256("s25|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, cfg, idx = t
    if blk.startswith("P25"): seeds = DEV
    nseed = int(hashlib.sha256(f"s25net|{blk}|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s25run|{blk}|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net25(hw, pat, arm, cfg, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, cfg=cfg, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P25", int(sys.argv[3]) if len(sys.argv) > 3 else 4)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
