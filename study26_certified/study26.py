"""Study 26 ("certified delivery"): fixes for the post-Study-25 weakness review and the adversarial proof review.

Common to all blocks (changes from Study 25):
  * Per-USER level. A user (source-destination pair) is served on a data-chosen path among its candidate shortest paths, so the
    per-path guarantee of Prop. 6 does not carry over: the union bound runs over every link the user could touch (U links),
    giving |U| alpha / Lmax. Guard arms here run each link's confidence sequence at alpha / Umax (Umax = the largest candidate
    link set of any user; 4 for Lmax = 2, 7 for Lmax = 3 on the 5 x 5 grid), so P(a user ever receives a bad pair) <= alpha.
    Legacy arms (suffix L) keep alpha / Lmax for the cost comparison.
  * Per-user outcome. For every user we record whether it EVER received a pair below threshold (users_bad), over ALL users of the
    network (users_total), not only users that were served. The safety bar is the per-user risk users_bad / users_total.
  * The valid AI arm. The guard's prior must be independent of the link's own data that the confidence sequence uses (Lemma B of
    the proof review, which replaces the withdrawn Prop. 10). ag2t (prior frozen from neighbours' data up to epoch 2; confidence
    sequence on own data after the freeze) satisfies this whenever the shared noise does not persist across epochs; ag2 is not
    run here.
Block U (per-user level; published baselines at matched risk). Pattern 'field', no shared noise, serial service (the G-series
  model). Arms: bg, kg, ag2t (corrected level) and bgL, kgL, ag2tL (legacy level); baselines with NO risk controller and NO
  guard, same belief (fleet) and the same greedy routing:
    plug   - plug-in fidelity rule (EFiRAP / Q-PATH / Q-GUARD class): deliver iff F(point estimate of every link) >= tau;
    plugM  - plug-in with a fidelity margin m, tuned per hardware on the dev pilot (smallest m with dev pooled r <= 1%);
    cut    - memory cut-off (Rozpedek et al. 2018 class): deliver iff the first pair's storage wait 'hold' <= t_cut, with t_cut
             (in units of the mean link generation time) tuned per hardware on the dev pilot (largest t_cut with dev r <= 1%).
Block R (shared noise at levels measured on REAL hardware; recipe-declared dispersion). Each node adds a common-mode shift to the
  parity probability of every link touching it (as Study 25 Block T); link shift sd = rel x the fleet-mean error probability
  qbar, rel in {0.033 (ICFO median), 0.075 (ICFO max), 0.184 (USTC)}, from the pre-registered re-analyses (ledger E92-E97;
  recipe/dispersion_levels.py). 'h' variants: node noise multipliers g_v = exp(N(0, 0.5^2)) / e^0.25 (E g^2 = 1), so links
  differ (ICFO runs ranged 0-7.5%). 'a' variant: AR(1) persistence 0.9 across epochs (USTC level, homogeneous).
  Arms: bg, kg, ag2t (undeclared), and declared over-dispersion phi with counts deflated by phi (quasi-likelihood; approximate):
    kgR, ag2tR     - phi = one-sided 95% upper bound (t interval over the campaign's independent epochs) of the FLEET-MEAN dispersion,
                     from an independent 30-epoch campaign on all links (links sharing a node are correlated, epochs are not);
    kgRp, ag2tRp   - per-link phi_l = each link's own one-sided 95% upper bound from the same campaign;
    kgO, ag2tO     - oracle: each link's true per-epoch phi_l (in the AR variant this under-states the cumulative dispersion).
Block O (model optimism measured on real hardware; recipe-declared margin). Controller and guard both add an undeclared optimistic
  offset Delta to every model fidelity, Delta in {0.02, 0.044} (the USTC gap range, recipe/ustc_margin.py). The guard declares a
  margin d and requires F_model - d >= tau:  m0 (d = 0), mM for M in {4, 16, 64, 256} tomography points (d = one-sided 95% upper
  bound from M points with the USTC precision: se = 0.0436 sqrt(4 / M), Delta_hat ~ N(Delta, se^2) per network), orc (d = Delta).
  Arm kg (corrected level). Theory: with the recipe, P(a user ever receives a bad pair) <= alpha + 0.05.
Block S (finite memory). Parallel service at 4x load, 50 km/hop (Study 25 'par4'), plus Q qubits per node: a request needs 1
  qubit at each end node and 2 at each intermediate node of its path, for the whole service; it starts when its links and enough
  qubits are free (no back-filling; requests in arrival order). Q in {2, 4, inf}. Arms bg, kg, ag2t.
"""
import hashlib, json, os, sys
import numpy as np
from scipy.special import logsumexp
from scipy.stats import chi2, t as tdist
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), "/home/claude/s18c", "/home/claude/s25"):
    if p and p not in sys.path: sys.path.append(p)
import ptm_model as ptm
import drift_queue_des_g1 as g1
import drift_queue_des_g2 as g2
import corr_net24 as cn
import study23 as s23
import study24 as s24
import study25 as s25

ALPHA = 0.05; BETA_RECIPE = 0.05
HWS = ("ion2020", "ionproj", "nv2", "siv")
RELS = (0.033, 0.075, 0.184); HET_SD = 0.5; AR_RHO = 0.9; EC = 30           # campaign epochs for the dispersion recipe
DELTAS = (0.02, 0.044); MTOM = (4, 16, 64, 256); SE4 = 0.0436                # USTC GLS standard error with 4 points
QS = (2, 4, 0)                                                                # 0 = unlimited
PLUG_M = (0.0, 0.01, 0.02, 0.04, 0.06, 0.08, 0.1, 0.15); CUT_X = (0.01, 0.03, 0.1, 0.25, 0.5, 1.0, 2.0, 4.0)
LEGACY = ("bgL", "kgL", "ag2tL")
TUNED = {"ion2020": {"plugM": 0.01, "cut": 0.01}, "ionproj": {"plugM": 0.01, "cut": 0.1}, "nv2": {"plugM": 0.06, "cut": 0.01},
         "siv": {"plugM": 0.1, "cut": 0.01}}   # dev pilot (runs.csv a38182dc), analyze_26.py tune; cut infeasible on ion2020, nv2, siv
SEEDS = (19281, 19282, 19283, 19284)                                         # fresh confirmatory; dev pilot 20281-20284
DEV = (20281, 20282, 20283, 20284)
NNET = 32
BASE = {"bg": "bg", "kg": "kg", "ag2t": "ag2t", "plug": "b", "plugM": "b", "cut": "b"}


def base_of(arm):
    a = arm[:-1] if arm in LEGACY else arm
    for suf in ("Rp", "R", "O"):
        if a.endswith(suf) and a[:-len(suf)] in ("kg", "ag2t"): a = a[:-len(suf)]; break
    return BASE[a]


def configs(pilot=False):
    """block -> list of (hw, pattern, arm, cfg)."""
    U = [(hw, "field", a, "-") for hw in HWS for a in ("bg", "kg", "ag2t", "bgL", "kgL", "ag2tL", "plug")]
    if pilot:
        U += [(hw, "field", "plugM", f"m{m}") for hw in HWS for m in PLUG_M] + [(hw, "field", "cut", f"x{x}") for hw in HWS for x in CUT_X]
    else:
        U += [(hw, "field", "plugM", f"m{TUNED[hw]['plugM']}") for hw in HWS] + [(hw, "field", "cut", f"x{TUNED[hw]['cut']}") for hw in HWS]
    RA = ("bg", "kg", "ag2t", "kgR", "ag2tR", "kgRp", "ag2tRp", "kgO", "ag2tO")
    R = [(hw, "field", a, f"n{rel}_{v}") for hw in HWS for rel in RELS for v in ("e", "h") for a in RA] + \
        [(hw, "field", a, f"n{RELS[-1]}_a") for hw in HWS for a in RA]
    O = [(hw, "field", "kg", f"o{d}_{m}") for hw in ("ion2020", "ionproj") for d in DELTAS
         for m in ["m0"] + [f"m{k}" for k in MTOM] + ["orc"]]
    S = [(hw, "field", a, f"q{q}") for hw in ("ion2020", "nv2", "siv") for q in QS for a in ("bg", "kg", "ag2t")]
    return {"U": U, "R": R, "O": O, "S": S}


def parse26(cfg):
    o = dict(rel=0.0, het=False, ar=False, off=0.0, tom=None, orc=False, Q=None, m=None, x=None, par=False)
    if cfg.startswith("n"):
        a, v = cfg[1:].split("_"); o["rel"] = float(a); o["het"] = v == "h"; o["ar"] = v == "a"
    elif cfg.startswith("o"):
        a, m = cfg[1:].split("_"); o["off"] = float(a)
        if m == "orc": o["orc"] = True
        else: o["tom"] = int(m[1:])
    elif cfg.startswith("q"):
        o["Q"] = int(cfg[1:]) or None; o["par"] = True
    elif cfg.startswith("m"): o["m"] = float(cfg[1:])
    elif cfg.startswith("x"): o["x"] = float(cfg[1:])
    return o


class Net26(s25.Net25):
    def __init__(s, hw, pat, arm, cfg, seed):
        o = parse26(cfg)
        super().__init__(hw, pat, base_of(arm), "par4" if o["par"] else "-", seed)
        s.arm26, s.cfg26, s.o26 = arm, cfg, o; s.kind = arm if arm in ("plug", "plugM", "cut") else "guard"
        assert s.nl == cn.NL and len(s.cands) > 0
        s.Umax = max(len(set().union(*[set(c) for c in cs])) for cs in s.cands)
        s.lvl = ALPHA / (s.Lmax if arm in LEGACY else s.Umax)
        # ---- shared noise at real-hardware levels (Block R): redraw the pre-drawn calibration counts
        s.phi_true = np.ones(s.nl); s.phi_decl = 1.0
        if o["rel"] > 0:
            er = np.random.default_rng(list(seed[2:]) + [261]); P = s.P
            nbar = s.rho_cal * P["R"] * g1.T; qbar = (1 - s.r * s.lam_mu) / 2
            A = np.zeros((cn.NL, len(cn.NODES)))
            for l, (u, v) in enumerate(cn.ENDS): A[l, cn.cn._NIDX[u]] = 0.5; A[l, cn.cn._NIDX[v]] = 0.5
            gmul = np.exp(er.normal(0, HET_SD, len(cn.NODES))) / np.exp(HET_SD ** 2) if o["het"] else np.ones(len(cn.NODES))
            snode = o["rel"] * qbar * np.sqrt(2) * gmul                     # node sd; link sd = rel*qbar when g = 1
            pl = (1 + s.r * s.lam) / 2
            link_var = (A ** 2) @ (snode ** 2); s.phi_true = 1 + nbar * link_var / (pl * (1 - pl))
            def draw(rng, ne):
                nn = np.zeros((ne, s.nl), int); kk = np.zeros((ne, s.nl), int); x = rng.normal(0, 1, len(cn.NODES))
                for j in range(ne):
                    if j > 0: x = AR_RHO * x + np.sqrt(1 - AR_RHO ** 2) * rng.normal(0, 1, len(cn.NODES)) if o["ar"] else rng.normal(0, 1, len(cn.NODES))
                    n = rng.poisson(nbar, s.nl); nn[j] = n; kk[j] = rng.binomial(n, np.clip(pl + A @ (snode * x), 1e-6, 1 - 1e-6))
                return nn, kk
            s.n_e, s.k_e = draw(er, s.NE)
            s.N_c = np.cumsum(s.n_e, 0); s.K_c = np.cumsum(s.k_e, 0); s.cache = {}
            # recipe: an independent campaign of EC epochs on all links (same nodes, independent noise realisation)
            cn_, ck_ = draw(np.random.default_rng(list(seed[2:]) + [262]), EC)
            ph = ck_.sum(0) / np.maximum(cn_.sum(0), 1)
            z2 = ((ck_ - cn_ * ph) ** 2) / np.maximum(cn_ * ph * (1 - ph), 1e-12)                # (EC, nl) Pearson terms
            dl = z2.sum(0) / (EC - 1); df = EC - 1                                                   # per-link dispersion
            Sj = z2.mean(1) * EC / (EC - 1)                         # per-epoch fleet statistic; epochs are independent (not links)
            s.phi_R = max(1.0, float(Sj.mean() + tdist.ppf(1 - BETA_RECIPE, EC - 1) * Sj.std(ddof=1) / np.sqrt(EC)))
            s.phi_Rp = np.maximum(1.0, dl * df / chi2.ppf(BETA_RECIPE, df))                      # per-link upper bounds
            s.phi_hat = float(dl.mean())
        if arm.endswith(("R", "Rp", "O")) and arm not in ("plug",): assert o["rel"] > 0, (arm, cfg)
        if arm.endswith("Rp"): s.phi_decl = s.phi_Rp
        elif arm.endswith("R"): s.phi_decl = s.phi_R
        elif arm.endswith("O"): s.phi_decl = s.phi_true      # per-link array
        # ---- model optimism (Block O)
        s.off = o["off"]; s.dec = 0.0; s.dec_viol = 0
        if o["off"] > 0:
            if o["orc"]: s.dec = o["off"]
            elif o["tom"]:
                se = SE4 * np.sqrt(4 / o["tom"]); trng = np.random.default_rng(list(seed[2:]) + [263, o["tom"]])
                s.dec = float(o["off"] + se * trng.normal() + 1.645 * se)
            s.dec_viol = int(s.dec < o["off"])
        # ---- baselines
        s.plug_m = o["m"] if arm == "plugM" else 0.0
        s.cut_t = o["x"] / ((1 - g1.RHO) * s.P["R"]) if arm == "cut" else None
        s.Q = o["Q"]; s.ustat = {}; s.ureq = set()

    def st(s, e):
        """as Study 25, with level s.lvl and declared dispersion s.phi_decl (scalar or per link) for every guard."""
        s.emax = max(s.emax, int(e)); e = int(min(max(e, s.E0), s.E0 + s.NE - 1)); j = e - s.E0
        if j in s.cache: return s.cache[j]
        n, k = s.n_e[j], s.k_e[j]; Nc, Kc = s.N_c[j], s.K_c[j]
        b = s.belief
        if b == "fleet": lpr = s.lprior[None]
        elif b == "known": lpr = s.belief_prior(np.zeros(s.nl), np.ones(s.nl))
        else:
            zh, v = s25.hw24.zv(s.hw, Nc, Kc); mz, sz = s25.am.predict(s.W2, cn.features2(zh, v)); lpr = s.belief_prior(mz, sz)
            if e == s.freeze and s.ai_prior is None: s.ai_prior = (mz, sz)
        ll = k[:, None, None] * s.lp[None] + (n - k)[:, None, None] * s.lq[None] + lpr
        ll -= ll.max(axis=(1, 2), keepdims=True); w = np.exp(ll).reshape(s.nl, -1); w /= w.sum(1, keepdims=True)
        cdf = np.cumsum(w, axis=1); est = w @ s.lgrid.ravel()
        g = s.guard; ph = s.phi_decl; Ng, Kg = Nc / ph, Kc / ph
        if g is None: lo = np.zeros(s.nl)
        elif g == "fleetmix": lo = s23.cs_lower_mix(Ng, Kg, s.r, s.lam_g, np.broadcast_to(s.fleet_lp, (s.nl, len(s.lam_g))), s.lvl)
        elif g == "hedge":
            assert s.tsplit
            if e <= s.freeze: lo = np.zeros(s.nl)
            else:
                if s.ai_prior is None: s.st(s.freeze)
                mz, sz = s.ai_prior; mu = s.lam_mu + s.sd_l * mz; sd = s.sd_l * sz
                la = -0.5 * ((s.lam_g[None, :] - mu[:, None]) / sd[:, None]) ** 2; la = la - logsumexp(la, axis=1, keepdims=True)
                wo = (1 - s24.W_AI) / 2
                lp = logsumexp(np.stack([np.log(s24.W_AI) + la, np.broadcast_to(np.log(wo) + s.fleet_lp, la.shape),
                                         np.broadcast_to(np.log(wo) + s.jef_lp, la.shape)]), axis=0)
                jf = s.freeze - s.E0
                lo = s23.cs_lower_mix((Nc - s.N_c[jf]) / ph, (Kc - s.K_c[jf]) / ph, s.r, s.lam_g, lp, s.lvl)
        else:
            plo = g2.cs_lower(Ng, Kg, s.lvl); lo = np.clip((2 * plo - 1) / s.r, 0, 1)
        s.cache[j] = (cdf, est, lo); return s.cache[j]

    def path_nodes(s, path):
        cnt = {}
        for l in path:
            for v in cn.ENDS[l]: cnt[v] = cnt.get(v, 0) + 1
        return {v: (2 if c == 2 else 1) for v, c in cnt.items()}            # qubits needed: 1 at ends, 2 in the middle

    def run(s):
        P = s.P; H = g1.NEPOCH * g1.T; par = s.o["mode"] == "parallel"
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0)
        L = dict(e2e=[], queue=[], svc=[], att=[], hold=[], osvc=[])
        busy = np.zeros(s.nl); obusy = np.zeros(s.nl); tser = 0.0
        slots = {v: np.zeros(s.Q) for v in cn.NODES} if s.Q else None; oslots = {v: np.zeros(s.Q) for v in cn.NODES} if s.Q else None
        arr = s.rng.exponential(1 / s.rate25)
        while arr < H:
            a0 = arr; arr += s.rng.exponential(1 / s.rate25)
            ci = int(s.rng.integers(len(s.cands))); cset = s.cands[ci]
            _, est0, _ = s.st(int((a0 if par else max(a0, tser)) // g1.T) - 1)
            path = cset[int(np.argmax([np.log(np.maximum(est0[list(c)], 1e-9)).sum() for c in cset]))] if len(cset) > 1 else cset[0]
            op = cset[int(np.argmax([np.log(np.maximum(s.lam[list(c)], 1e-9)).sum() for c in cset]))]
            lk, olk = list(path), list(op)
            if par:
                t = max(a0, busy[lk].max()); to = max(a0, obusy[olk].max())
                if s.Q:
                    need, oneed = s.path_nodes(path), s.path_nodes(op)
                    t = max([t] + [np.sort(slots[v])[q - 1] for v, q in need.items()])
                    to = max([to] + [np.sort(oslots[v])[q - 1] for v, q in oneed.items()])
            else:
                t = max(a0, tser); to = t
            t_start, to_start = t, to
            meas = t_start >= g1.WARM_EPOCH * g1.T
            if meas: out["requests"] += 1; s.abserr.append(float(np.abs(est0[lk] - s.lam[lk]).mean())); s.ureq.add(ci)
            for _ in range(g1.BUDGET):
                w1_, w2_, hold, to = s.chains_d(s.orng, to, len(op))
                if s.trueF(op, w1_, w2_, hold) >= s.tau:
                    if meas: out["oracle_qual"] += 1; L["osvc"].append(to - to_start)
                    break
            if par:
                obusy[olk] = to
                if s.Q:
                    for v, q in oneed.items(): idx = np.argsort(oslots[v])[:q]; oslots[v][idx] = to
            for att in range(g1.BUDGET):
                w1_, w2_, hold, t = s.chains_d(s.rng, t, len(path)); cdf, est, lamlo = s.st(int(t // g1.T) - 1)
                Ft = s.trueF(path, w1_, w2_, hold); ld = s.draws_at(lk, cdf)
                Fs = ptm.delivered_F(ld, w1_, w2_, hold, s.Pm["e"], np.inf, s.Pm["T2"]) + s.off
                pbad = ((Fs < s.tau).sum() + 0.5) / (g1.M + 1)
                thr = s.choose_t(); s.pb[s.nb % g1.WIN] = pbad; s.nb += 1
                if s.kind == "guard":
                    ok = pbad <= thr
                    if ok and s.guard:
                        Fg = float(ptm.delivered_F(lamlo[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0]) + s.off - s.dec
                        if Fg < s.tau:
                            ok = False
                            if meas: out["guard_blocks"] += 1
                elif s.kind in ("plug", "plugM"):
                    Fp = float(ptm.delivered_F(est[lk][None, :], w1_, w2_, hold, s.Pm["e"], np.inf, s.Pm["T2"])[0]) + s.off
                    ok = Fp >= s.tau + s.plug_m
                else:
                    ok = hold <= s.cut_t
                if ok:
                    if meas:
                        bad = int(Ft < s.tau); out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                        st_ = s.pstat.setdefault(path, [0, 0]); st_[0] += 1; st_[1] += bad
                        su = s.ustat.setdefault(ci, [0, 0]); su[0] += 1; su[1] += bad
                        L["e2e"].append(t - a0); L["queue"].append(t_start - a0); L["svc"].append(t - t_start); L["att"].append(att + 1); L["hold"].append(float(hold))
                    break
            if par:
                busy[lk] = t
                if s.Q:
                    for v, q in need.items(): idx = np.argsort(slots[v])[:q]; slots[v][idx] = t
            else: tser = t
        v = list(s.pstat.values()); u = list(s.ustat.values())
        out["paths_delivered"] = sum(1 for x in v if x[0] > 0); out["paths_bad"] = sum(1 for x in v if x[1] > 0)
        out["users_total"] = len(s.cands); out["users_served"] = sum(1 for x in u if x[0] > 0); out["users_requested"] = len(s.ureq); out["users_bad"] = sum(1 for x in u if x[1] > 0)
        out["max_path_bad"] = max([x[1] for x in v] or [0]); out["est_abserr"] = float(np.mean(s.abserr)) if s.abserr else -1.0
        e = np.array(L["e2e"])
        for kk in ("e2e", "queue", "svc", "att", "hold", "osvc"): out[f"lat_{kk}_mean"] = float(np.mean(L[kk])) if L[kk] else -1.0
        for q in (50, 95, 99): out[f"lat_e2e_p{q}"] = float(np.percentile(e, q)) if len(e) else -1.0
        out["lat_e2e_hist"] = ";".join(str(int(c)) for c in np.histogram(e, s24.LAT_BINS)[0])
        out["max_epoch"] = s.emax; out["epoch_clamped"] = int(s.emax > s.E0 + s.NE - 1)
        # identical columns in every row (the PSC runner appends rows under the first row's header)
        out["Umax"] = s.Umax; out["level"] = s.lvl
        out["phi_true_mean"] = float(np.mean(s.phi_true)); out["phi_true_max"] = float(np.max(s.phi_true))
        out["phi_decl_mean"] = float(np.mean(s.phi_decl))
        out["dec"] = s.dec; out["dec_viol"] = s.dec_viol
        return out


PILOT_NETS = {"U": 16, "R": 8, "O": 8, "S": 8}


def tasks(prefix="S26", nnet=NNET, pilot=False):
    assert pilot or TUNED is not None, "TUNED must be set from the dev pilot before writing confirmatory tasks"
    out = []
    for b, cl in configs(pilot).items():
        for (hw, pat, arm, cfg) in cl:
            for i in range(PILOT_NETS[b] if pilot else nnet): out.append([f"{prefix}{b}", hw, pat, arm, cfg, i])
    return out


def run_id(t):
    return hashlib.sha256("s26|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, cfg, idx = t
    if blk.startswith("P26"): seeds = DEV
    nseed = int(hashlib.sha256(f"s26net|{blk[-1]}|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s26run|{blk[-1]}|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net26(hw, pat, arm, cfg, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, cfg=cfg, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        pil = sys.argv[1] == "--write-pilot"
        ts = tasks("P26", pilot=True) if pil else tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
