"""Study 30 ("provable closed loop"): replace Study 29's heuristic margin by a margin with a guarantee (THEORY_30.md, Thm 2),
and replace the fixed-bet model check by a debt-free plug-in check (Prop. D).

Network, hardware (ion2020, ionproj), horizon (90 epochs), test streams (p = 0.1, 0.2), guard and Theorem 1 levels: as Study 29.
Arms (all use the same guard, routing and user tests; they differ only in the response):
  kg     no model check (reference)
  kgMT   Study 29's tracking response (heuristic), unchanged: mixture check, Clopper-Pearson offset estimate, margin <= DMAX
  kgMC   provable response: on an alarm the offset confidence sequence (core30.OffsetCS) is (re)started at the declared maximum
         offset THMAX and the margin for pair i is U_t * phi_i with phi_i = 1 (constant class). Mixture check (Prop. MC).
         Margin-blocked pairs are probe-tested, as in Study 29. The check keeps running against the new margin; a later alarm
         restarts the confidence sequence (spending 6 a'/(pi^2 k^2)).
  kgMCp  as kgMC with the plug-in check (Prop. D)
  kgMCh  as kgMC with the hybrid check (average of the mixture and plug-in e-processes; core30.HybridCheck)
  kgMCs  as kgMCh with the storage class phi_i = hold_i / HBAR (offset proportional to storage time)
  kgMCa  always-on: as kgMCh but the confidence sequence and the margin (starting at THMAX) run from t = 0, no alarm gate
Scenarios: the model is unchanged and the TRUTH is worse than the model by Delta_i (extra depolarizing noise on the
delivered pair: F -> F - Delta_i, every basis error e -> (1-x) e + x/2 with x = Delta_i/(F - 1/4)), so model fidelities never
exceed 1 (review blocker 4; Studies 28-29 added the offset to the model instead, which let F_M exceed 1):
  '-'       none
  'oD'      constant Delta = D in {0.02, 0.044, 0.08}
  's0.044'  storage-proportional Delta_i = 0.044 * phi(hold_i), phi = min(hold/HBAR, PHICAP)   (in class for kgMCs only)
  'h0.044'  heterogeneous per link: Delta_i = mean over the path's links of delta_l, delta_l ~ Gamma(mean 0.044, sd 0.02),
            drawn once per network (out of class for every arm)
  'L0.044'  constant 0.044 from epoch LON = 30 onward (late onset); the model is exact before (guard slack only)
  '...F'    forced alarm at the 8th feedback test (Study 28's failure case). In '-' it is a false alarm; in 'L0.044F' it is a
            false alarm BEFORE the onset, so (B2) fails in the first window and protection needs a second (real) alarm
Baselines (arm kg): exact per-pair margin 'o0.044_orc', 's0.044_orc'; fixed margin THMAX from t = 0 '-_fix', 'o0.044_fix'
(provable under B2 + B4 for the constant class, with no data at all: the "static" competitor of kgMC/kgMCa).
"""
import hashlib, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), os.environ.get("S26_DIR", ""), os.environ.get("S27_DIR", ""), os.environ.get("S29_DIR", ""),
          "/home/claude/s18c", "/home/claude/s26", "/home/claude/s25", "/home/claude/s27", "/home/claude/s29"):
    if p and p not in sys.path: sys.path.append(p)
import drift_queue_des_g1 as g1
NEPOCH30 = 90
g1.NEPOCH = NEPOCH30
from scipy.stats import beta as betad
import ptm_model as ptm
import study26 as s26
import ptm_corr
from cert import Certifier
from mcheck import ModelCheck, null_bound
from core30 import cs_upper_mix, OffsetCS, PlugInCheck, HybridCheck

ALPHA = 0.05; BETA = 0.05; ALPHA_HI = 0.025; ALPHA_TH = 0.025      # Theorem 1 / model check / link upper ends / offset CS
DMAX = 0.10; NMIN = 50; UPD = 10; LOOKS = 9; FORCE_AT = 8           # Study 29 (kgMT) constants, unchanged
THMAX = 0.10                                                        # declared max offset per unit phi (B4): ~2x the measured gaps 0.02-0.044
HBAR = 0.0105; PHICAP = 3.0                                         # storage unit (mean hold over attempts, dev network 0) and phi cap
LON = 30                                                            # late-onset epoch
DSTEP = 0.01                                                        # restart the check (with spending) when the margin has fallen by DSTEP
HET_MEAN, HET_SD = 0.044, 0.02
HWS = ("ion2020", "ionproj"); PS = (0.1, 0.2)
SCEN = ("-", "-F", "o0.02", "o0.044", "o0.044F", "o0.08", "s0.044", "h0.044", "L0.044", "L0.044F")
FEED = ("kgMT", "kgMC", "kgMCp", "kgMCh", "kgMCs", "kgMCa"); NOFEED = ("kg",)
MC_ARMS = ("kgMC", "kgMCp", "kgMCh", "kgMCs", "kgMCa")
BASELINES = ("o0.044_orc", "s0.044_orc", "-_fix", "o0.044_fix")
SEEDS = (19321, 19322, 19323, 19324); DEV = (20321, 20322, 20323, 20324); NNET = 32


def configs():
    C = []
    for hw in HWS:
        for sc in SCEN:
            if not sc.endswith("F"): C += [(hw, "field", a, f"{sc}|p00") for a in NOFEED]
            C += [(hw, "field", a, f"{sc}|p{int(round(p * 100)):02d}") for p in PS for a in FEED]
        C += [(hw, "field", "kg", f"{b}|p00") for b in BASELINES]
    return C


def cp_ub(k, n, a):
    return 1.0 if k >= n else float(betad.ppf(1 - a, k + 1, n - k))


class Net30(s26.Net26):
    def __init__(s, hw, pat, arm, cfg, seed, ttag=301):
        assert g1.NEPOCH == NEPOCH30
        sc, pt = cfg.split("|"); s.orc = sc.endswith("_orc"); s.fix = sc.endswith("_fix"); sc = sc.replace("_orc", "").replace("_fix", "")
        s.forced = sc.endswith("F"); sc0 = sc[:-1] if s.forced else sc
        s.p = int(pt[1:]) / 100; s.arm30 = arm
        assert (arm in FEED) == (s.p > 0) and arm in FEED + NOFEED
        super().__init__(hw, pat, "kg", "-", seed)                  # no Net26 offset: Study 30 adds its own per-pair optimism
        assert s.guard == "fleetmix" and s.off == 0.0 and s.dec == 0.0
        s.okind = "-" if sc0 == "-" else sc0[0]; s.theta = 0.0 if sc0 == "-" else float(sc0[1:])
        hr = np.random.default_rng(list(seed[2:]) + [303]); k_ = (HET_MEAN / HET_SD) ** 2
        s.delta_l = hr.gamma(k_, HET_MEAN / k_, s.nl)                     # per-link offsets (used only in 'h'); network-level seed
        s.rmax = float(s.P["q"]); s.smax = 2 * s.rmax * (1 - s.rmax)
        s.feed = arm in FEED
        s.mc = ({"kgMCp": PlugInCheck, "kgMCh": HybridCheck, "kgMCs": HybridCheck, "kgMCa": HybridCheck}.get(arm, ModelCheck))(BETA) if s.feed else None
        s.prov = arm in MC_ARMS; s.storage_cls = arm == "kgMCs"
        s.cs = OffsetCS(ALPHA_TH, THMAX) if s.prov else None
        if arm == "kgMCa": s.cs.restart()                                 # always-on: first window opens at t = 0 (k = 1)
        s.reset_dec = None                                                # margin at the last check restart (MC arms)
        s.trng = {p: np.random.default_rng(list(seed[2:]) + [ttag, int(p * 1000)]) for p in PS}   # same role as Study 29
        s.certs = {p: Certifier(p, ALPHA, rmax=s.smax) for p in PS}
        s.prng = np.random.default_rng(list(seed[2:]) + [302])
        s.hcache = {}

    # ---- per-pair model optimism (truth unchanged) and the arm's declared offset shape
    def opt(s, t, hold, links):
        """true offset Delta_i of a pair (how much worse the truth is than the model)."""
        if s.okind == "-": return 0.0
        if s.okind == "o": return s.theta
        if s.okind == "s": return s.theta * min(hold / HBAR, PHICAP)
        if s.okind == "h": return float(np.mean(s.delta_l[list(links)]))
        if s.okind == "L": return s.theta if t >= LON * g1.T else 0.0
        raise ValueError(s.okind)

    def phi_of(s, hold):
        return min(hold / HBAR, PHICAP) if s.storage_cls else 1.0

    def st(s, e):
        r = super().st(e)
        if len(s.cache) > 4:
            for k in sorted(s.cache)[:-4]: del s.cache[k]
        return r

    def hi_at(s, e):
        """upper ends of the guard's own mixture CS, all links, level ALPHA_HI / |E| (network-wide union: THEORY_30, B1)."""
        e = int(min(max(e, s.E0), s.E0 + s.NE - 1)); j = e - s.E0
        if j not in s.hcache:
            ph = s.phi_decl
            s.hcache[j] = cs_upper_mix(s.N_c[j] / ph, s.K_c[j] / ph, s.r, s.lam_g, np.broadcast_to(s.fleet_lp, (s.nl, len(s.lam_g))), ALPHA_HI / s.nl)
            if len(s.hcache) > 4:
                for k in sorted(s.hcache)[:-4]: del s.hcache[k]
        return s.hcache[j]

    def true_state(s, links, w1, w2, hold, t):
        C, F = ptm_corr.delivered_corr(s.lam[list(links)][None, :], w1, w2, hold, s.P["e"], np.inf, s.P["T2"])
        F = float(F[0]); eB = np.asarray(ptm_corr.errs(C)[0], float); D = s.opt(t, hold, links)
        if D > 0:                                                         # extra depolarizing noise: F - D exactly
            x = min(D / max(F - 0.25, 1e-9), 1.0); F = (1 - x) * F + x * 0.25; eB = (1 - x) * eB + x / 2
        return F, eB

    def run(s):
        P = s.P; H = g1.NEPOCH * g1.T
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0, delivered_all=0, bad_all=0, probes=0)
        st = {p: dict(K=0, Err=0, D=0.0, viol=0, kq=0, kb=0, nt=0) for p in PS}
        ub_all = {}; ub_post = {}
        first_viol_t = first_alarm = None
        post = dict(deliv=0, bad=0, qual=0, viol=0, below=0, dsum=0.0, osum=0.0, dmin=np.inf, tests=0)
        pall = dict(deliv=0, bad=0); whole = dict(viol=0, below=0)          # all pairs incl. warm-up (review major 4)
        seg = dict(n=0, vt=0); segs = []
        trk = dict(on=s.arm30 == "kgMCa", k=0, n=0, qc=0.0, d=0.0, t0_ep=0, looks=0, decreases=0, restarts=0)
        nfeed = [0]; cs_n = [0]
        if s.arm30 == "kgMCa": s.dec = THMAX

        def look_mt():
            """Study 29 kgMT margin update (unchanged)."""
            if trk["n"] < NMIN: s.dec = DMAX; return
            ue = cp_ub(trk["k"], trk["n"], BETA / LOOKS)
            new = float(np.clip(1.5 * (ue - trk["qc"] / trk["n"]) + trk["d"] / trk["n"], 0.0, DMAX))
            if new < s.dec - 1e-12:
                trk["decreases"] += 1; trk["restarts"] += 1; s.mc.k += 1; s.mc.logm[:] = 0.0
            s.dec = new; trk["looks"] += 1

        def alarm(t, forced=False):
            nonlocal first_alarm
            d0 = s.dec
            if s.arm30 == "kgMT":
                trk.update(on=True, k=0, n=0, qc=0.0, d=0.0, t0_ep=int(t // g1.T)); s.dec = DMAX
                if forced: s.mc.k += 1; s.mc.logm[:] = 0.0
            elif s.prov:
                trk.update(on=True, t0_ep=int(t // g1.T)); s.cs.restart(); s.dec = THMAX; trk["restarts"] += 1; s.reset_dec = THMAX
                if forced:
                    if isinstance(s.mc, ModelCheck): s.mc.k += 1; s.mc.logm[:] = 0.0
                    else: s.mc.reset()
            segs.append(dict(t=t, n=seg["n"], vt=seg["vt"], inc=s.dec - d0, forced=forced))
            seg.update(n=0, vt=0)
            if first_alarm is None: first_alarm = t

        def cs_add(Fhi, E, ph):
            s.cs.add(Fhi - 1 + 1.5 * E, ph, Fhi + 0.5); cs_n[0] += 1

        last_ep = [None]
        arr = s.rng.exponential(1 / s.rate25); tser = 0.0
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
                w1_, w2_, hold, t = s.chains_d(s.rng, t, len(path)); ep = int(t // g1.T) - 1; cdf, est, lamlo = s.st(ep)
                e_now = int(t // g1.T)
                if trk["on"] and e_now != last_ep[0]:                                     # epoch boundary
                    if s.arm30 == "kgMT":
                        since = e_now - trk["t0_ep"]
                        if trk["n"] < NMIN: s.dec = DMAX
                        elif since > 0 and since % UPD == 0: look_mt()
                    elif s.prov:
                        s.dec = s.cs.update(); trk["looks"] += 1                           # time-uniform: any look is allowed
                        if s.reset_dec is None: s.reset_dec = s.dec
                        if s.dec < s.reset_dec - DSTEP:                                    # fresh wealth for the new guard
                            trk["decreases"] += 1; s.reset_dec = s.dec
                            if isinstance(s.mc, ModelCheck): s.mc.k += 1; s.mc.logm[:] = 0.0
                            else: s.mc.reset()
                last_ep[0] = e_now
                o_i = s.opt(t, hold, lk); ph_i = s.phi_of(hold)
                d_i = o_i if s.orc else (THMAX if s.fix else (s.dec * ph_i if s.prov else s.dec))
                Ft, eB = s.true_state(path, w1_, w2_, hold, t); ld = s.draws_at(lk, cdf)
                Fs = ptm.delivered_F(ld, w1_, w2_, hold, s.Pm["e"], np.inf, s.Pm["T2"])
                pbad = ((Fs < s.tau).sum() + 0.5) / (g1.M + 1)
                thr = s.choose_t(); s.pb[s.nb % g1.WIN] = pbad; s.nb += 1
                ok = pbad <= thr; Fg = None; Fhi = None
                if ok:
                    F0 = float(ptm.delivered_F(lamlo[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0])
                    Fg = F0 - d_i
                    if Fg < s.tau:
                        ok = False
                        if meas: out["guard_blocks"] += 1
                        if trk["on"] and F0 >= s.tau:                                        # blocked only by the margin: probe
                            bb = int(s.prng.integers(3)); E = int(s.prng.random() < eB[bb]); s.prng.random(); out["probes"] += 1
                            if s.arm30 == "kgMT":
                                Fc = float(ptm.delivered_F(est[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0]) - d_i
                                trk["k"] += E; trk["n"] += 1; trk["qc"] += (2 / 3) * (1 - Fc); trk["d"] += d_i
                            else:
                                Fhi = float(ptm.delivered_F(s.hi_at(ep)[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0])
                                cs_add(Fhi, E, ph_i)
                if not ok: continue
                bad = int(Ft < s.tau); viol = Ft < Fg - 1e-12
                out["delivered_all"] += 1; out["bad_all"] += bad; whole["viol"] += int(viol); whole["below"] += int(d_i < o_i - 1e-12)
                if first_alarm is not None: pall["deliv"] += 1; pall["bad"] += bad
                ub_all[ci] = ub_all.get(ci, 0) + bad
                if meas:
                    out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                    su = s.ustat.setdefault(ci, [0, 0]); su[0] += 1; su[1] += bad
                    if first_alarm is not None:
                        post["deliv"] += 1; post["bad"] += bad; post["qual"] += 1 - bad; post["viol"] += int(viol)
                        post["below"] += int(d_i < o_i - 1e-12); post["dsum"] += d_i; post["osum"] += o_i; post["dmin"] = min(post["dmin"], d_i)
                        up = ub_post.setdefault(ci, [0, 0]); up[0] += 1; up[1] += bad
                q = null_bound(Fg, s.smax)
                if s.arm30 == "kgMT":
                    Fc = float(ptm.delivered_F(est[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0]) - d_i
                    qc = (2 / 3) * (1 - Fc)
                for p in PS:
                    r = s.trng[p]; T = r.random() < p; b = int(r.integers(3)); E = int(r.random() < eB[b])
                    r.random()
                    S = st[p]
                    if T:
                        if meas: S["nt"] += 1; S["Err"] += E
                        if s.feed and p == s.p:
                            nfeed[0] += 1
                            if viol and first_viol_t is None: first_viol_t = t
                            seg["vt"] |= int(viol); seg["n"] += 1
                            if first_alarm is not None: post["tests"] += 1
                            if trk["on"]:
                                if s.arm30 == "kgMT": trk["k"] += E; trk["n"] += 1; trk["qc"] += qc; trk["d"] += d_i
                                else:
                                    if Fhi is None:
                                        Fhi = float(ptm.delivered_F(s.hi_at(ep)[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0])
                                    cs_add(Fhi, E, ph_i)
                            if s.forced and first_alarm is None and nfeed[0] == FORCE_AT: alarm(t, forced=True)
                            elif s.mc.update(E, q): alarm(t)
                    elif meas:
                        S["K"] += 1; S["D"] += 1 - Ft; S["kq"] += 1 - bad; S["kb"] += bad
                        if not S["viol"] and s.certs[p].lower(S["Err"], S["K"]) > 1 - S["D"] / S["K"] + 1e-12: S["viol"] = 1
                break
            tser = t
        u = list(s.ustat.values())
        out["users_total"] = len(s.cands); out["users_bad"] = sum(1 for x in u if x[1] > 0)
        out["users_bad_all"] = sum(1 for v in ub_all.values() if v > 0); out["any_bad_all"] = int(out["bad_all"] > 0)
        out["users_post"] = len(ub_post); out["users_bad_post"] = sum(1 for x in ub_post.values() if x[1] > 0)
        real = [g for g in segs if not g["forced"]]
        out["alarms"] = len(real); out["forced"] = len(segs) - len(real)
        out["first_alarm_ep"] = first_alarm / g1.T if first_alarm is not None else float("nan")
        out["fa_first_t"] = int(bool(real) and (first_viol_t is None or real[0]["t"] < first_viol_t))
        out["fa_seg_t"] = sum(1 for g in real if not g["vt"]); out["seg_n_first"] = segs[0]["n"] if segs else -1
        out["bad_after_alarm_all"] = pall["bad"]; out["deliv_after_alarm_all"] = pall["deliv"]
        out["viol_all"] = whole["viol"]; out["below_all"] = whole["below"]
        out["bad_after_alarm"] = post["bad"]; out["deliv_after_alarm"] = post["deliv"]; out["qual_after_alarm"] = post["qual"]
        out["viol_after_alarm"] = post["viol"]; out["below_after_alarm"] = post["below"]; out["tests_after_alarm"] = post["tests"]
        out["dec_mean_after"] = post["dsum"] / post["deliv"] if post["deliv"] else float("nan")
        out["opt_mean_after"] = post["osum"] / post["deliv"] if post["deliv"] else float("nan")
        out["dec_min_after"] = post["dmin"] if post["deliv"] else float("nan"); out["dec_final"] = s.dec
        out["looks"] = trk["looks"]; out["decreases"] = trk["decreases"]; out["restarts"] = trk["restarts"]
        out["mc_k"] = s.mc.k if s.mc else 0; out["cs_n"] = cs_n[0]; out["cs_k"] = s.cs.k if s.cs else 0
        out["theta"] = s.theta; out["okind"] = s.okind; out["nepoch"] = g1.NEPOCH
        for p in PS:
            S = st[p]; tag = f"p{int(round(p * 100)):02d}"
            out[f"{tag}_tests"] = S["nt"]; out[f"{tag}_K"] = S["K"]; out[f"{tag}_viol"] = S["viol"]
            out[f"{tag}_kept_qual"] = S["kq"]; out[f"{tag}_kept_bad"] = S["kb"]
            out[f"{tag}_L"] = s.certs[p].lower(S["Err"], S["K"]) if S["K"] else float("nan")
            out[f"{tag}_F"] = 1 - S["D"] / S["K"] if S["K"] else float("nan")
        out["max_epoch"] = s.emax; out["epoch_clamped"] = int(s.emax > s.E0 + s.NE - 1)
        return out


def tasks(prefix="S30", nnet=NNET):
    return [[prefix, hw, pat, arm, cfg, i] for (hw, pat, arm, cfg) in configs() for i in range(nnet)]


def run_id(t):
    return hashlib.sha256("s30|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, cfg, idx = t
    if blk.startswith("P30"): seeds = DEV
    nseed = int(hashlib.sha256(f"s30net|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s30run|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net30(hw, pat, arm, cfg, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, cfg=cfg, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P30", int(sys.argv[3]) if len(sys.argv) > 3 else 8)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
