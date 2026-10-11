"""Study 27 ("certified delivery"): the model-free certificate of Theorem C1 on top of the model-based control layer.

Every delivered pair (measurement period) is, with fresh user randomness independent of the network, TESTED with probability p
in a uniformly random basis of {X, Y, Z} (error drawn from the pair's TRUE correlators, ptm_corr.py) or KEPT. The three test
fractions p in PS are evaluated on the same delivery stream with independent test streams (testing happens after delivery,
so it never changes what the network does). For every user and for the network as a whole, the certificate
L_t = 1 - D_ub(Err_t)/K_t (cert.py) is compared with the TRUE running average fidelity of the kept pairs after EVERY kept pair;
a certificate that is ever above the truth is a violation. Theorem C1: P(violation) <= alpha for each user and for the pooled
network certificate, whatever the network does.
Scenarios (cfg): '-' (no stressor); 'o0.044_m0' (undeclared model optimism Delta = 0.044, Study 26 Block O); 'n0.184_a'
(USTC-level persistent shared noise, Study 26 Block R); 'fault' (from epoch FAULT_EP on, every memory's true T2 drops by
FAULT_FAC; calibration counts and all models are unaware). Traffic: 'uni' (users uniform, as before) or 'hot' (fraction HOT
of requests from HOTN fixed users per network). Arms: kg (corrected guard), b (risk controller, no guard), plug (plug-in rule).
"""
import hashlib, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), os.environ.get("S26_DIR", ""), "/home/claude/s18c", "/home/claude/s26", "/home/claude/s25"):
    if p and p not in sys.path: sys.path.append(p)
import ptm_model as ptm
import drift_queue_des_g1 as g1
import corr_net24 as cn
import study24 as s24
import study26 as s26
import ptm_corr
from cert import Certifier

ALPHA = 0.05; PS = (0.05, 0.1, 0.2); HOT, HOTN = 0.8, 4; FAULT_EP, FAULT_FAC = 15, 5.0; KMIN_TIGHT = 500
HWS = ("ion2020", "ionproj", "nv2", "siv"); SCEN = ("-", "o0.044_m0", "n0.184_a", "fault"); TRAF = ("uni", "hot")
ARMS = ("kg", "b", "plug")
SEEDS = (19291, 19292, 19293, 19294); DEV = (20291, 20292, 20293, 20294); NNET = 32
CERTS = {p: Certifier(p, ALPHA) for p in PS}
s26.BASE.setdefault("b", "b")                        # the risk controller without a guard (Study 24 arm b); study26.py is not modified


def configs():
    return [(hw, "field", a, f"{sc}|{tr}") for hw in HWS for sc in SCEN for tr in TRAF for a in ARMS]


class Net27(s26.Net26):
    def __init__(s, hw, pat, arm, cfg, seed):
        sc, tr = cfg.split("|"); s.fault = sc == "fault"
        super().__init__(hw, pat, arm, "-" if s.fault else sc, seed)
        s.tr = tr; hr = np.random.default_rng(list(seed[2:]) + [271])
        one_hop = [i for i, cs in enumerate(s.cands) if len(cs[0]) == 1]          # hot users are 1-hop users (servable on every hw)
        s.hot = list(hr.choice(one_hop, HOTN, replace=False)) if tr == "hot" else []
        s.trng = {p: np.random.default_rng(list(seed[2:]) + [272, int(p * 1000)]) for p in PS}   # user test randomness

    def T2true(s, t):
        return s.P["T2"] / FAULT_FAC if (s.fault and t >= FAULT_EP * g1.T) else s.P["T2"]

    def true_state(s, links, w1, w2, hold, t):
        C, F = ptm_corr.delivered_corr(s.lam[list(links)][None, :], w1, w2, hold, s.P["e"], np.inf, s.T2true(t))
        return float(F[0]), ptm_corr.errs(C)[0]

    def pick_user(s):
        if s.hot and s.rng.random() < HOT: return int(s.hot[int(s.rng.integers(len(s.hot)))])
        return int(s.rng.integers(len(s.cands)))

    def run(s):
        P = s.P; H = g1.NEPOCH * g1.T
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0)
        cs = {p: dict(u={}, net=[0, 0, 0.0, 0, 0]) for p in PS}  # [K, Err, D, violated, eligible (certificate ever > 0)]
        kept_qual = {p: 0 for p in PS}
        tser = 0.0
        arr = s.rng.exponential(1 / s.rate25)
        while arr < H:
            a0 = arr; arr += s.rng.exponential(1 / s.rate25)
            ci = s.pick_user(); cset = s.cands[ci]
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
                if s.kind == "guard":
                    ok = pbad <= thr
                    if ok and s.guard:
                        Fg = float(ptm.delivered_F(lamlo[lk][None, :], w1_, w2_, hold, s.Pd["e"], np.inf, s.Pd["T2"])[0]) + s.off - s.dec
                        if Fg < s.tau:
                            ok = False
                            if meas: out["guard_blocks"] += 1
                else:
                    Fp = float(ptm.delivered_F(est[lk][None, :], w1_, w2_, hold, s.Pm["e"], np.inf, s.Pm["T2"])[0]) + s.off
                    ok = Fp >= s.tau
                if ok:
                    if meas:
                        bad = int(Ft < s.tau); out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                        su = s.ustat.setdefault(ci, [0, 0]); su[0] += 1; su[1] += bad
                        for p in PS:                                               # the certification layer
                            r = s.trng[p]; T = r.random() < p; b = int(r.integers(3)); E = int(r.random() < eB[b])
                            uu = cs[p]["u"].setdefault(ci, [0, 0, 0.0, 0, 0]); nn = cs[p]["net"]
                            for st_ in (uu, nn):
                                if T: st_[1] += E
                                else:
                                    st_[0] += 1; st_[2] += 1 - Ft
                                    Lc = CERTS[p].lower(st_[1], st_[0])
                                    if Lc > 0: st_[4] = 1
                                    if not st_[3] and Lc > 1 - st_[2] / st_[0] + 1e-12: st_[3] = 1
                            if not T: kept_qual[p] += 1 - bad
                    break
            tser = t
        u = list(s.ustat.values())
        out["users_total"] = len(s.cands); out["users_served"] = sum(1 for x in u if x[0] > 0); out["users_bad"] = sum(1 for x in u if x[1] > 0)
        for p in PS:
            tag = f"p{int(round(p * 100)):02d}"; U = list(cs[p]["u"].values()); C = CERTS[p]
            out[f"{tag}_u_cert"] = sum(1 for x in U if x[0] > 0); out[f"{tag}_u_viol"] = sum(x[3] for x in U); out[f"{tag}_u_elig"] = sum(x[4] for x in U)
            K, Err, D, V, El = cs[p]["net"]; out[f"{tag}_net_viol"] = V; out[f"{tag}_net_K"] = K; out[f"{tag}_net_elig"] = El
            out[f"{tag}_net_L"] = C.lower(Err, K) if K else float("nan"); out[f"{tag}_net_F"] = 1 - D / K if K else float("nan")
            big = [x for x in U if x[0] >= KMIN_TIGHT]
            out[f"{tag}_u_big"] = len(big)
            out[f"{tag}_u_big_L"] = float(np.mean([C.lower(x[1], x[0]) for x in big])) if big else float("nan")
            out[f"{tag}_u_big_F"] = float(np.mean([1 - x[2] / x[0] for x in big])) if big else float("nan")
            out[f"{tag}_kept_qual"] = kept_qual[p]
        out["max_epoch"] = s.emax; out["epoch_clamped"] = int(s.emax > s.E0 + s.NE - 1)
        return out


def tasks(prefix="S27", nnet=NNET):
    return [[prefix, hw, pat, arm, cfg, i] for (hw, pat, arm, cfg) in configs() for i in range(nnet)]


def run_id(t):
    return hashlib.sha256("s27|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, cfg, idx = t
    if blk.startswith("P27"): seeds = DEV
    nseed = int(hashlib.sha256(f"s27net|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s27run|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net27(hw, pat, arm, cfg, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, cfg=cfg, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P27", int(sys.argv[3]) if len(sys.argv) > 3 else 8)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
