"""Study 28 ("model-checked delivery"): the certification tests also check the model behind the per-pair guard.

Every delivered pair is, with fresh user randomness hidden from the network, TESTED with probability p in a uniformly random
basis of {X, Y, Z} or KEPT. Two independent test streams (p = 0.1 and 0.2) are drawn for every pair, as in Study 27; an arm
with feedback uses the stream of its own p. A tested pair's outcome comes from its TRUE correlators, flipped by readout with
probability s = 2 r (1 - r) (r = true per-qubit readout error of the scenario). Every check and certificate declares the
hardware's own readout error as the bound (r_max = P['q']: ions 0.001, NV 0.03, SiV 0.01; s_max = 2 r_max (1 - r_max)).
Arms
  kg     the Study 26/27 guard (reference; no feedback)
  kgN    network-wide guard: every link CS at alpha/|E| (40 links), so P(ANY user ever receives a bad pair) <= alpha
  kgM    kg + model check (mcheck.ModelCheck): null for each delivered pair F_true >= Fg (the guard's own validity
         condition), q = null_bound(Fg, s_max). On an alarm the declared margin rises by
         clip(1.5 * UB, STEP, DMAX), UB = an empirical-Bernstein upper estimate of mean(E - q) over the segment's n tests
         (1.5 converts error probability to fidelity), if n >= NMIN, else STEP; DMAX = 0.10 (the USTC 95% bound); restart.
         The response is a heuristic; the formal content is the e-process (validity and detection).
  kgNM   kgN + model check
  kgP    kg + naive per-epoch detector: one-sided binomial test of each epoch's tests at mean q, Bonferroni over NEPOCH
         epochs at level beta (valid: a binomial tail at the mean q dominates the Poisson-binomial tail); same response.
Scenarios: '-' none; 'o0.044_m0' undeclared model optimism 0.044; 'n0.184_a' USTC-level persistent noise; 'fault' (from
FAULT_EP every memory's true T2 / FAULT_FAC); 'ro' true readout error at the declared bound (r = r_max) and no other stressor.
Baselines on o0.044 (ion hardware, arm kg): 'o0.044_m16' (margin declared from 16 tomography points, Study 26) and
'o0.044_orc' (margin known exactly).
Horizon: NEPOCH = 90 epochs of 100 s (2.5 h), 3x Studies 26-27, because detection needs hundreds of tests.
"""
import hashlib, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), os.environ.get("S26_DIR", ""), os.environ.get("S27_DIR", ""),
          "/home/claude/s18c", "/home/claude/s26", "/home/claude/s25", "/home/claude/s27"):
    if p and p not in sys.path: sys.path.append(p)
import drift_queue_des_g1 as g1
NEPOCH28 = 90
g1.NEPOCH = NEPOCH28                                  # set before any network is built (Net25 sizes its arrays from it)
from scipy.stats import binom
import ptm_model as ptm
import study26 as s26
import ptm_corr
from cert import Certifier
from mcheck import ModelCheck, null_bound

ALPHA = 0.05; BETA = 0.05; STEP = 0.02; DMAX = 0.10; NMIN = 50
FAULT_EP, FAULT_FAC = 45, 5.0
HWS = ("ion2020", "ionproj", "nv2", "siv"); SCEN = ("-", "o0.044_m0", "n0.184_a", "fault", "ro"); PS28 = (0.1, 0.2)
FEED = ("kgM", "kgNM", "kgP"); NOFEED = ("kg", "kgN"); BASELINES = ("o0.044_m16", "o0.044_orc")
SEEDS = (19301, 19302, 19303, 19304); DEV = (20301, 20302, 20303, 20304); NNET = 32


def configs():
    C = []
    for hw in HWS:
        for sc in SCEN:
            C += [(hw, "field", a, f"{sc}|p00") for a in NOFEED]
            C += [(hw, "field", a, f"{sc}|p{int(round(p * 100)):02d}") for p in PS28 for a in FEED]
        if hw.startswith("ion"): C += [(hw, "field", "kg", f"{b}|p00") for b in BASELINES]
    return C


class Net28(s26.Net26):
    def __init__(s, hw, pat, arm, cfg, seed):
        assert g1.NEPOCH == NEPOCH28
        sc, pt = cfg.split("|"); s.fault = sc == "fault"; s.ro = sc == "ro"
        s.p = int(pt[1:]) / 100; s.arm28 = arm
        assert (arm in FEED) == (s.p > 0) and arm in FEED + NOFEED
        super().__init__(hw, pat, "kg", "-" if (s.fault or s.ro) else sc, seed)
        s.rmax = float(s.P["q"]); s.smax = 2 * s.rmax * (1 - s.rmax); s.r_true = s.rmax if s.ro else 0.0
        s.netwide = arm in ("kgN", "kgNM")
        if s.netwide: s.lvl = ALPHA / s.nl; s.cache = {}
        s.feed = arm in FEED; s.mc = ModelCheck(BETA) if arm in ("kgM", "kgNM") else None
        s.trng = {p: np.random.default_rng(list(seed[2:]) + [281, int(p * 1000)]) for p in PS28}   # user test randomness (hidden)
        s.certs = {p: Certifier(p, ALPHA, rmax=s.smax) for p in PS28}

    def st(s, e):
        r = super().st(e)
        if len(s.cache) > 4:                           # memory: keep recent epochs only (st is deterministic, so a re-request recomputes the same value)
            for k in sorted(s.cache)[:-4]: del s.cache[k]
        return r

    def T2true(s, t):
        return s.P["T2"] / FAULT_FAC if (s.fault and t >= FAULT_EP * g1.T) else s.P["T2"]

    def true_state(s, links, w1, w2, hold, t):
        C, F = ptm_corr.delivered_corr(s.lam[list(links)][None, :], w1, w2, hold, s.P["e"], np.inf, s.T2true(t))
        return float(F[0]), ptm_corr.errs(C)[0]

    def run(s):
        P = s.P; H = g1.NEPOCH * g1.T; s_true = 2 * s.r_true * (1 - s.r_true)
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0, delivered_all=0, bad_all=0)
        st = {p: dict(K=0, Err=0, D=0.0, viol=0, kq=0, kb=0, nt=0) for p in PS28}      # certificate / kept stats per test stream
        ub_all = {}
        first_viol_d = first_viol_t = first_alarm = None; bad_after_alarm = deliv_after_alarm = 0
        bad_post_fault = deliv_post_fault = 0
        seg = dict(n=0, exc=[], vd=0, vt=0, gap=0.0, nd=0)                              # current check segment
        segs = []                                                                       # closed segments that ended in an alarm
        ep = dict(e=None, n=0, c=0, qs=0.0, exc=[])                                     # naive detector, current epoch
        tser = 0.0

        def alarm(t, exc):
            nonlocal first_alarm
            n = len(exc)                              # empirical-Bernstein upper estimate of the mean gap (heuristic response, not a guarantee)
            if n >= NMIN:
                x = np.asarray(exc); L = np.log(1 / BETA)
                ub = x.mean() + np.sqrt(2 * x.var(ddof=1) * L / n) + 7 * L / (3 * (n - 1))
                inc = float(np.clip(1.5 * ub, STEP, DMAX))
            else: inc = STEP
            s.dec += inc
            segs.append(dict(t=t, n=seg["n"], vd=seg["vd"], vt=seg["vt"], gap=seg["gap"] / max(seg["nd"], 1), inc=inc))
            seg.update(n=0, exc=[], vd=0, vt=0, gap=0.0, nd=0)
            if first_alarm is None: first_alarm = t

        def naive_close():
            if ep["n"] > 0:
                qb = ep["qs"] / ep["n"]
                if binom.sf(ep["c"] - 1, ep["n"], qb) <= BETA / g1.NEPOCH: alarm(ep_t[0], ep["exc"])
            ep.update(n=0, c=0, qs=0.0, exc=[])
        ep_t = [0.0]

        arr = s.rng.exponential(1 / s.rate25)
        while arr < H:
            a0 = arr; arr += s.rng.exponential(1 / s.rate25)
            ci = int(s.rng.integers(len(s.cands))); cset = s.cands[ci]
            _, est0, _ = s.st(int(max(a0, tser) // g1.T) - 1)
            path = cset[int(np.argmax([np.log(np.maximum(est0[list(c)], 1e-9)).sum() for c in cset]))] if len(cset) > 1 else cset[0]
            op = cset[int(np.argmax([np.log(np.maximum(s.lam[list(c)], 1e-9)).sum() for c in cset]))]
            lk = list(path); t = max(a0, tser); to = t; t_start = t
            meas = t_start >= g1.WARM_EPOCH * g1.T
            if meas: out["requests"] += 1
            for _ in range(g1.BUDGET):
                w1_, w2_, hold, to = s.chains_d(s.orng, to, len(op))
                if s.true_state(op, w1_, w2_, hold, to)[0] >= s.tau:
                    if meas: out["oracle_qual"] += 1
                    break
            for att in range(g1.BUDGET):
                w1_, w2_, hold, t = s.chains_d(s.rng, t, len(path)); cdf, est, lamlo = s.st(int(t // g1.T) - 1)
                Ft, eB = s.true_state(path, w1_, w2_, hold, t); ld = s.draws_at(lk, cdf)
                Fs = ptm.delivered_F(ld, w1_, w2_, hold, s.Pm["e"], np.inf, s.Pm["T2"]) + s.off
                pbad = ((Fs < s.tau).sum() + 0.5) / (g1.M + 1)
                thr = s.choose_t(); s.pb[s.nb % g1.WIN] = pbad; s.nb += 1
                ok = pbad <= thr; Fg = None
                if ok:
                    Fg = float(ptm.delivered_F(lamlo[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0]) + s.off - s.dec
                    if Fg < s.tau:
                        ok = False
                        if meas: out["guard_blocks"] += 1
                if not ok: continue
                bad = int(Ft < s.tau); viol = Ft < Fg - 1e-12
                out["delivered_all"] += 1; out["bad_all"] += bad
                ua = ub_all.setdefault(ci, 0); ub_all[ci] = ua + bad
                if viol and first_viol_d is None: first_viol_d = t
                seg["vd"] |= int(viol); seg["gap"] += Fg - Ft; seg["nd"] += 1
                if meas:
                    out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                    su = s.ustat.setdefault(ci, [0, 0]); su[0] += 1; su[1] += bad
                    if first_alarm is not None: deliv_after_alarm += 1; bad_after_alarm += bad
                    if s.fault and t >= FAULT_EP * g1.T: deliv_post_fault += 1; bad_post_fault += bad
                q = null_bound(Fg, s.smax)
                for p in PS28:                                                   # two independent test streams
                    r = s.trng[p]; T = r.random() < p; b = int(r.integers(3)); E = int(r.random() < eB[b])
                    if r.random() < s_true: E = 1 - E                            # readout parity flip
                    S = st[p]
                    if T:
                        if meas: S["nt"] += 1; S["Err"] += E
                        if s.feed and p == s.p:                                  # feedback stream
                            if viol and first_viol_t is None: first_viol_t = t
                            seg["vt"] |= int(viol); seg["n"] += 1; seg["exc"].append(E - q)
                            if s.mc is not None:
                                if s.mc.update(E, q): alarm(t, seg["exc"])
                            else:
                                e_now = int(t // g1.T)
                                if ep["e"] is None: ep["e"] = e_now
                                if e_now != ep["e"]: naive_close(); ep["e"] = e_now
                                ep_t[0] = t; ep["n"] += 1; ep["c"] += E; ep["qs"] += q; ep["exc"].append(E - q)
                    elif meas:
                        S["K"] += 1; S["D"] += 1 - Ft; S["kq"] += 1 - bad; S["kb"] += bad
                        if not S["viol"] and s.certs[p].lower(S["Err"], S["K"]) > 1 - S["D"] / S["K"] + 1e-12: S["viol"] = 1
                break
            tser = t
        u = list(s.ustat.values())
        out["users_total"] = len(s.cands); out["users_served"] = sum(1 for x in u if x[0] > 0); out["users_bad"] = sum(1 for x in u if x[1] > 0)
        out["users_bad_all"] = sum(1 for v in ub_all.values() if v > 0); out["any_bad_all"] = int(out["bad_all"] > 0)
        out["alarms"] = len(segs); out["first_alarm_ep"] = first_alarm / g1.T if first_alarm is not None else float("nan")
        out["first_viol_d_ep"] = first_viol_d / g1.T if first_viol_d is not None else float("nan")
        out["first_viol_t_ep"] = first_viol_t / g1.T if first_viol_t is not None else float("nan")
        out["fa_first_d"] = int(first_alarm is not None and (first_viol_d is None or first_alarm < first_viol_d))
        out["fa_first_t"] = int(first_alarm is not None and (first_viol_t is None or first_alarm < first_viol_t))
        out["fa_seg_d"] = sum(1 for g in segs if not g["vd"]); out["fa_seg_t"] = sum(1 for g in segs if not g["vt"])
        out["seg_gap_mean"] = float(np.mean([g["gap"] for g in segs])) if segs else float("nan")
        out["inc_max"] = max([g["inc"] for g in segs], default=0.0); out["seg_n_min"] = min([g["n"] for g in segs], default=-1)
        out["bad_after_alarm"] = bad_after_alarm; out["deliv_after_alarm"] = deliv_after_alarm; out["dec_final"] = s.dec
        out["bad_post_fault"] = bad_post_fault; out["deliv_post_fault"] = deliv_post_fault; out["fault_ep"] = FAULT_EP if s.fault else -1
        out["r_true"] = s.r_true; out["nepoch"] = g1.NEPOCH
        for p in PS28:
            S = st[p]; tag = f"p{int(round(p * 100)):02d}"
            out[f"{tag}_tests"] = S["nt"]; out[f"{tag}_K"] = S["K"]; out[f"{tag}_viol"] = S["viol"]
            out[f"{tag}_kept_qual"] = S["kq"]; out[f"{tag}_kept_bad"] = S["kb"]
            out[f"{tag}_L"] = s.certs[p].lower(S["Err"], S["K"]) if S["K"] else float("nan")
            out[f"{tag}_F"] = 1 - S["D"] / S["K"] if S["K"] else float("nan")
        out["max_epoch"] = s.emax; out["epoch_clamped"] = int(s.emax > s.E0 + s.NE - 1)
        return out


def tasks(prefix="S28", nnet=NNET):
    return [[prefix, hw, pat, arm, cfg, i] for (hw, pat, arm, cfg) in configs() for i in range(nnet)]


def run_id(t):
    return hashlib.sha256("s28|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, cfg, idx = t
    if blk.startswith("P28"): seeds = DEV
    nseed = int(hashlib.sha256(f"s28net|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s28run|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net28(hw, pat, arm, cfg, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, cfg=cfg, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P28", int(sys.argv[3]) if len(sys.argv) > 3 else 8)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
