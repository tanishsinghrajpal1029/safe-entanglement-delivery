"""Study 29 ("margin response"): how should the network react after the model check (Study 28, Prop. MC) alarms?

Study 28's H4 failed because one network alarmed after only 8 tests and its response raised the margin by just 0.02 (true
offset 0.044); post-alarm margins were also about twice the true offset. Study 29 keeps Study 28's network, check and
horizon (ion hardware only, where the check has power; 90 epochs; test streams p = 0.1 and 0.2; declared readout bound =
hardware spec) and compares responses after an alarm:
  kg     no model check (reference)
  kgM    Study 28's response, unchanged (paired: identical to kgM up to its first alarm)
  kgMJ   jump: as kgM, but an alarm from fewer than NMIN tests raises the margin to at least DMAX = 0.10
  kgMT   tracking: after an alarm the margin is DMAX until NMIN tests have arrived AFTER the alarm; then, every UPD epochs,
         it is set to an exact (Clopper-Pearson) one-sided upper bound on the model offset at level beta/LOOKS, computed from
         the post-alarm tests only, using the model's CENTRAL prediction with zero readout error:
             offset_ub = 1.5 * (CP_ub(errors, n; beta/LOOKS) - mean q_c) + mean d,  q_c = (2/3)(1 - (F(est) + off - d)).
         The margin may go down; whenever it goes down the e-process is restarted at its next spending level, so that it
         watches the new margin from fresh wealth. A later alarm resets the post-alarm window. While tracking, a pair that
         the guard blocks ONLY because of the margin (Fg < tau <= Fg + d) is not delivered but probe-tested (random basis),
         and the probe joins the offset estimate: blocked pairs are free test material, so a high margin cannot starve the
         estimate (Study 28's network 19 at margin 0.10 got about 140 user tests in 90 epochs).
  kgMTp  as kgMT with the point estimate (no upper bound): shows why the bound is needed (baseline)
  kgMTa  always-track: kgMT's estimator from the start of the run, with no alarm gate (margin 0 until the first look)
Scenarios: '-' none; undeclared model optimism of 0.02, 0.044 and 0.08 ('oD_m0'); forced-alarm cells ('...F': an alarm is
injected at the 8th feedback test, reproducing Study 28's failure case, in '-' (recovery from a false alarm) and o0.044).
Baselines (arm kg): exact margin 'oD_orc'; 16-point tomography 'o0.044_m16'. Block 'R28' replays Study 28's networks.
The response is a heuristic; the formal content remains the e-process (Prop. MC). With a margin that can go down,
Theorem 1's protection after a decrease is heuristic too (it assumes a margin that only rises).
"""
import hashlib, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), os.environ.get("S26_DIR", ""), os.environ.get("S27_DIR", ""),
          "/home/claude/s18c", "/home/claude/s26", "/home/claude/s25", "/home/claude/s27"):
    if p and p not in sys.path: sys.path.append(p)
import drift_queue_des_g1 as g1
NEPOCH29 = 90
g1.NEPOCH = NEPOCH29                                  # set before any network is built (Net25 sizes its arrays from it)
from scipy.stats import beta as betad
import ptm_model as ptm
import study26 as s26
import ptm_corr
from cert import Certifier
from mcheck import ModelCheck, null_bound

ALPHA = 0.05; BETA = 0.05; STEP = 0.02; DMAX = 0.10; NMIN = 50; UPD = 10; LOOKS = 9; FORCE_AT = 8
HWS = ("ion2020", "ionproj"); PS = (0.1, 0.2)
SCEN = ("-", "-F", "o0.02_m0", "o0.044_m0", "o0.044_m0F", "o0.08_m0")
FEED = ("kgM", "kgMJ", "kgMT", "kgMTp", "kgMTa"); NOFEED = ("kg",)
BASELINES = ("o0.02_orc", "o0.044_orc", "o0.08_orc", "o0.044_m16")
SEEDS = (19311, 19312, 19313, 19314); DEV = (20311, 20312, 20313, 20314); NNET = 32
S28_SEEDS = (19301, 19302, 19303, 19304)


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


class Net29(s26.Net26):
    def __init__(s, hw, pat, arm, cfg, seed, ttag=291):
        assert g1.NEPOCH == NEPOCH29
        sc, pt = cfg.split("|"); s.forced = sc.endswith("F"); sc0 = sc[:-1] if s.forced else sc
        s.p = int(pt[1:]) / 100; s.arm29 = arm
        assert (arm in FEED) == (s.p > 0) and arm in FEED + NOFEED
        super().__init__(hw, pat, "kg", sc0, seed)
        s.rmax = float(s.P["q"]); s.smax = 2 * s.rmax * (1 - s.rmax); s.r_true = 0.0
        s.feed = arm in FEED; s.mc = ModelCheck(BETA) if s.feed else None
        s.track = arm in ("kgMT", "kgMTp", "kgMTa")
        s.trng = {p: np.random.default_rng(list(seed[2:]) + [ttag, int(p * 1000)]) for p in PS}   # user test randomness (hidden)
        s.certs = {p: Certifier(p, ALPHA, rmax=s.smax) for p in PS}
        s.prng = np.random.default_rng(list(seed[2:]) + [292])                     # probe-test randomness (tracking arms)

    def st(s, e):
        r = super().st(e)
        if len(s.cache) > 4:
            for k in sorted(s.cache)[:-4]: del s.cache[k]
        return r

    def true_state(s, links, w1, w2, hold, t):
        C, F = ptm_corr.delivered_corr(s.lam[list(links)][None, :], w1, w2, hold, s.P["e"], np.inf, s.P["T2"])
        return float(F[0]), ptm_corr.errs(C)[0]

    def run(s):
        P = s.P; H = g1.NEPOCH * g1.T
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0, delivered_all=0, bad_all=0, probes=0)
        st = {p: dict(K=0, Err=0, D=0.0, viol=0, kq=0, kb=0, nt=0) for p in PS}
        ub_all = {}
        first_viol_t = first_alarm = None
        post = dict(deliv=0, bad=0, qual=0, viol=0, below=0, dsum=0.0, dmin=np.inf, tests=0)
        seg = dict(n=0, exc=[], vt=0); segs = []
        trk = dict(on=s.arm29 == "kgMTa", k=0, n=0, qc=0.0, d=0.0, t0_ep=0, looks=0, decreases=0, restarts=0)
        nfeed = [0]

        def look(e_now):
            """kgMT/kgMTp/kgMTa margin update from the post-alarm (or whole-run) tests."""
            if trk["n"] < NMIN:
                if s.arm29 != "kgMTa": s.dec = DMAX
                return
            mE = trk["k"] / trk["n"]
            ue = mE if s.arm29 == "kgMTp" else cp_ub(trk["k"], trk["n"], BETA / LOOKS)
            new = float(np.clip(1.5 * (ue - trk["qc"] / trk["n"]) + trk["d"] / trk["n"], 0.0, DMAX))
            if new < s.dec - 1e-12:
                trk["decreases"] += 1; trk["restarts"] += 1
                s.mc.k += 1; s.mc.logm[:] = 0.0                              # fresh wealth at the next spending level
            s.dec = new; trk["looks"] += 1

        def alarm(t, forced=False):
            nonlocal first_alarm
            n = len(seg["exc"]); d0 = s.dec
            if s.track:
                trk.update(on=True, k=0, n=0, qc=0.0, d=0.0, t0_ep=int(t // g1.T))
                s.dec = DMAX
            elif n >= NMIN:
                x = np.asarray(seg["exc"]); L = np.log(1 / BETA)
                ub = x.mean() + np.sqrt(2 * x.var(ddof=1) * L / n) + 7 * L / (3 * (n - 1))
                s.dec += float(np.clip(1.5 * ub, STEP, DMAX))
            elif s.arm29 == "kgMJ": s.dec = max(s.dec + STEP, DMAX)
            else: s.dec += STEP
            if forced: s.mc.k += 1; s.mc.logm[:] = 0.0                       # a forced alarm consumes a spending level too
            segs.append(dict(t=t, n=n, vt=seg["vt"], inc=s.dec - d0, forced=forced))
            seg.update(n=0, exc=[], vt=0)
            if first_alarm is None: first_alarm = t

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
                w1_, w2_, hold, t = s.chains_d(s.rng, t, len(path)); cdf, est, lamlo = s.st(int(t // g1.T) - 1)
                e_now = int(t // g1.T)
                if s.track and trk["on"] and e_now != last_ep[0]:               # epoch boundary: scheduled looks only
                    since = e_now - trk["t0_ep"]
                    if trk["n"] < NMIN and s.arm29 != "kgMTa": s.dec = DMAX
                    elif since > 0 and since % UPD == 0: look(e_now)
                last_ep[0] = e_now
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
                        if s.track and trk["on"] and Fg + s.dec >= s.tau:     # blocked only by the margin: probe-test it
                            Fc = float(ptm.delivered_F(est[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0]) + s.off - s.dec
                            bb = int(s.prng.integers(3)); E = int(s.prng.random() < eB[bb]); s.prng.random()
                            trk["k"] += E; trk["n"] += 1; trk["qc"] += (2 / 3) * (1 - Fc); trk["d"] += s.dec; out["probes"] += 1
                if not ok: continue
                bad = int(Ft < s.tau); viol = Ft < Fg - 1e-12; d_now = s.dec
                out["delivered_all"] += 1; out["bad_all"] += bad
                ub_all[ci] = ub_all.get(ci, 0) + bad
                if meas:
                    out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                    su = s.ustat.setdefault(ci, [0, 0]); su[0] += 1; su[1] += bad
                    if first_alarm is not None:
                        post["deliv"] += 1; post["bad"] += bad; post["qual"] += 1 - bad; post["viol"] += int(viol)
                        post["below"] += int(d_now < s.off - 1e-12); post["dsum"] += d_now; post["dmin"] = min(post["dmin"], d_now)
                q = null_bound(Fg, s.smax)
                if s.track:
                    Fc = float(ptm.delivered_F(est[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0]) + s.off - d_now
                    qc = (2 / 3) * (1 - Fc)                                       # central prediction, zero readout error
                for p in PS:
                    r = s.trng[p]; T = r.random() < p; b = int(r.integers(3)); E = int(r.random() < eB[b])
                    r.random()                                                    # readout draw (kept for stream parity; r_true = 0)
                    S = st[p]
                    if T:
                        if meas: S["nt"] += 1; S["Err"] += E
                        if s.feed and p == s.p:
                            nfeed[0] += 1
                            if viol and first_viol_t is None: first_viol_t = t
                            seg["vt"] |= int(viol); seg["n"] += 1; seg["exc"].append(E - q)
                            if first_alarm is not None: post["tests"] += 1
                            if s.track and trk["on"]:
                                trk["k"] += E; trk["n"] += 1; trk["qc"] += qc; trk["d"] += d_now
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
        real = [g for g in segs if not g["forced"]]
        out["alarms"] = len(real); out["forced"] = len(segs) - len(real)
        out["first_alarm_ep"] = first_alarm / g1.T if first_alarm is not None else float("nan")
        out["fa_first_t"] = int(bool(real) and (first_viol_t is None or real[0]["t"] < first_viol_t))
        out["fa_seg_t"] = sum(1 for g in real if not g["vt"]); out["seg_n_first"] = segs[0]["n"] if segs else -1
        out["seg_n_min"] = min([g["n"] for g in segs], default=-1); out["inc_max"] = max([g["inc"] for g in segs], default=0.0)
        out["bad_after_alarm"] = post["bad"]; out["deliv_after_alarm"] = post["deliv"]; out["qual_after_alarm"] = post["qual"]
        out["viol_after_alarm"] = post["viol"]; out["below_after_alarm"] = post["below"]; out["tests_after_alarm"] = post["tests"]
        out["dec_mean_after"] = post["dsum"] / post["deliv"] if post["deliv"] else float("nan")
        out["dec_min_after"] = post["dmin"] if post["deliv"] else float("nan"); out["dec_final"] = s.dec
        out["looks"] = trk["looks"]; out["decreases"] = trk["decreases"]; out["restarts"] = trk["restarts"]; out["mc_k"] = s.mc.k if s.mc else 0
        out["off"] = s.off; out["nepoch"] = g1.NEPOCH
        for p in PS:
            S = st[p]; tag = f"p{int(round(p * 100)):02d}"
            out[f"{tag}_tests"] = S["nt"]; out[f"{tag}_K"] = S["K"]; out[f"{tag}_viol"] = S["viol"]
            out[f"{tag}_kept_qual"] = S["kq"]; out[f"{tag}_kept_bad"] = S["kb"]
            out[f"{tag}_L"] = s.certs[p].lower(S["Err"], S["K"]) if S["K"] else float("nan")
            out[f"{tag}_F"] = 1 - S["D"] / S["K"] if S["K"] else float("nan")
        out["max_epoch"] = s.emax; out["epoch_clamped"] = int(s.emax > s.E0 + s.NE - 1)
        return out


def tasks(prefix="S29", nnet=NNET):
    return [[prefix, hw, pat, arm, cfg, i] for (hw, pat, arm, cfg) in configs() for i in range(nnet)]


def replay_tasks():
    """Study 28's H4 failure network (ion2020, o0.044_m0, p = 0.1, network 19), replayed with every response."""
    return [["R28", "ion2020", "field", a, "o0.044_m0|p10", 19] for a in FEED] + [["R28", "ion2020", "field", "kg", "o0.044_m0|p00", 19]]


def run_id(t):
    return hashlib.sha256("s29|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, cfg, idx = t
    pre, ttag = "s29", 291
    if blk.startswith("P29"): seeds = DEV
    if blk == "R28": seeds, pre, ttag = S28_SEEDS, "s28", 281            # same network, requests and tests as Study 28
    nseed = int(hashlib.sha256(f"{pre}net|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"{pre}run|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net29(hw, pat, arm, cfg, [rseed, seeds[1], nseed, seeds[0] + seeds[2]], ttag)
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, cfg=cfg, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P29", int(sys.argv[3]) if len(sys.argv) > 3 else 8) + replay_tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
