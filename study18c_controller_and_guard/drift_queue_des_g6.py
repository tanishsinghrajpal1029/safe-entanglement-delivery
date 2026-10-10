"""Study 18C G6: protecting each user after SUDDEN LINK FAULTS (pre-registration: README_G6.md, written after the dev pilot).

Background. C1/C2 (single paths): with faults on 5% of paths the pooled risk stayed <= 1%, but right after a fault the bad share
was 2.2-59% in 5 of 8 cells. On networks the per-path guard (G2, Prop. 6) assumes STATIONARY links: an unannounced fault makes
its accumulated counts stale, so it can keep delivering on a broken link.

Scenario (5 x 5 grid, best routing, exact physics, no drift; otherwise G2/G4). Each link is faulted independently with
probability PF = 0.05 (the fault rate the controller's prior already declares, eps = 0.05). A fault happens at the start of a
random epoch in [WARM_EPOCH + 1, NEPOCH - 4] and lowers the link's quality lambda by DROP_SD standard deviations of the fleet
(C1/C2 used 2): F2 (2 sd) and F4 (4 sd, the edge of the declared fault range).

Controllers
  cal     frozen Bayesian controller, no guard (reference)
  gnaive  G2 guard: one confidence sequence per link over all counts (assumes no faults)
  galarm  G2 guard + per-link CHANGE ALARM: after each epoch, if the epoch's own upper confidence bound on the link's parity
          probability (one-sided Clopper-Pearson, level BETA) falls below the link's current guard lower bound, the alarm fires:
          the link's counts are discarded (restart) and alpha is spent over restarts as 6 alpha / (pi^2 c^2) (as Prop. 6').
  gwin    G2 guard AND a last-epoch bound: deliver only if the pair also clears tau at the lower bound from the most recent
          epoch alone (Clopper-Pearson; alpha split as alpha/2 to the long-run sequence and alpha/(2 NEPOCH) per epoch window).
Inherent limit: the controller sees an epoch's counts only after it ends, so no method can react within the first epoch
after a fault. We therefore report post-fault bad pairs separately for the first epoch ('early') and afterwards ('late').
"""
import hashlib, json, sys
import numpy as np
from scipy.stats import beta as betad
import ptm_model as ptm
import drift_queue_des_g1 as g1
import drift_queue_des_g2 as g2

ALPHA, PF, BETA, NNET = 0.05, 0.05, 1e-3, 64
DROP = {"F2": 2.0, "F4": 4.0}
SEEDS = (19151, 19152, 19153, 19154)        # fresh confirmatory; dev pilot used 20151-20154
CTRLS = ("cal", "gnaive", "galarm", "gwin")


def cp_upper(n, k, a):
    return np.where(n > 0, betad.ppf(1 - a, k + 1, np.maximum(n - k, 1e-9)), 1.0)


def cp_lower(n, k, a):
    return np.where((n > 0) & (k > 0), betad.ppf(a, np.maximum(k, 1e-9), n - k + 1), 0.0)


class NetG6(g1.Net):
    def __init__(s, hw, scen, ctrl, seed):
        super().__init__(hw, "grid", 0, "cal", "best", seed)
        s.gctrl, s.scen = ctrl, scen; P = s.P
        fr = np.random.default_rng(list(seed[2:]) + [61])            # same faults for every controller (paired)
        s.lam0 = s.lam.copy()
        s.faulted = fr.random(s.nl) < PF
        s.fep = fr.integers(g1.WARM_EPOCH + 1, g1.NEPOCH - 3, s.nl)
        dl = DROP[scen] * 4 / 3 * (1 - P["F0"]) * 0.2
        s.drop = np.where(s.faulted, np.minimum(s.lam0, dl), 0.0)
        s.N = np.zeros(s.nl); s.K = np.zeros(s.nl); s.ncyc = np.ones(s.nl, int); s.acc_ep = -10 ** 9
        s.lamlo = np.zeros(s.nl); s.winlo = np.zeros(s.nl); s.pstat = {}; s.alarms = np.zeros(s.nl, int)
        s.alarm_ep = np.full(s.nl, -1)

    def lam_epoch(s, e):
        return np.clip(s.lam0 - s.drop * (e >= s.fep), 0, 1)

    def level(s):
        if s.gctrl == "galarm": return ALPHA * 6 / (np.pi ** 2 * s.ncyc ** 2) / s.Lmax
        if s.gctrl == "gwin": return np.full(s.nl, ALPHA / 2 / s.Lmax)
        return np.full(s.nl, ALPHA / s.Lmax)

    def epoch_data(s, e):
        if e == s.ep: return
        keep = s.lam; s.lam = s.lam_epoch(e); g1.Net.epoch_data(s, e); s.lam = keep
        if e <= s.acc_ep or s.gctrl == "cal": return
        s.acc_ep = e
        if s.gctrl == "galarm":
            plo_prev = np.where(s.N > 0, g2.cs_lower(s.N, s.K, s.level()), 0.0)
            fire = (s.N > 0) & (cp_upper(s.n, s.kc, BETA) < plo_prev)
            if fire.any():
                s.N[fire] = 0; s.K[fire] = 0; s.ncyc[fire] += 1; s.alarms[fire] += 1
                s.alarm_ep = np.where(fire & (s.alarm_ep < 0), e, s.alarm_ep)
                s.n = np.where(fire, 0, s.n); s.kc = np.where(fire, 0, s.kc)       # the alarming epoch is not reused
        s.N += s.n; s.K += s.kc
        plo = g2.cs_lower(s.N, s.K, s.level()); s.lamlo = np.clip((2 * plo - 1) / s.r, 0, 1)
        if s.gctrl == "gwin":
            wlo = cp_lower(s.n.astype(float), s.kc.astype(float), ALPHA / (2 * s.Lmax * g1.NEPOCH))
            s.winlo = np.clip((2 * wlo - 1) / s.r, 0, 1)

    def guard_F(s, links, w1, w2, hold):
        lk = list(links); lo = s.lamlo[lk]
        if s.gctrl == "gwin": lo = np.minimum(lo, s.winlo[lk])
        return float(ptm.delivered_F(lo[None, :], w1, w2, hold, s.P["e"], np.inf, s.P["T2"])[0])

    def trueF(s, links, w1, w2, hold):
        return float(ptm.delivered_F(s.lam[list(links)][None, :], w1, w2, hold, s.P["e"], np.inf, s.P["T2"])[0])

    def run(s):
        P = s.P; t = 0.0; H = g1.NEPOCH * g1.T; guard = s.gctrl != "cal"
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0, post_delivered=0, post_bad=0,
                   post_bad_early=0, post_bad_late=0, prefault_bad=0)
        arr = s.rng.exponential(1 / s.rate)
        while arr < H:
            t = max(t, arr); arr += s.rng.exponential(1 / s.rate)
            s.lam = s.lam_epoch(int(t // g1.T))
            cset = s.cands[int(s.rng.integers(len(s.cands)))]
            s.epoch_data(int(t // g1.T) - 1)
            path = cset[int(np.argmax([np.log(np.maximum(s.est[list(c)], 1e-9)).sum() for c in cset]))] if len(cset) > 1 else cset[0]
            meas = t >= g1.WARM_EPOCH * g1.T
            if meas: out["requests"] += 1
            op = cset[int(np.argmax([np.log(np.maximum(s.lam[list(c)], 1e-9)).sum() for c in cset]))]; to = t
            for _ in range(g1.BUDGET):
                w1, w2, hold, to = s.chains(s.orng, to, len(op))
                if s.trueF(op, w1, w2, hold) >= s.tau:
                    if meas: out["oracle_qual"] += 1
                    break
            for _ in range(g1.BUDGET):
                w1, w2, hold, t = s.chains(s.rng, t, len(path)); s.epoch_data(int(t // g1.T) - 1)
                s.lam = s.lam_epoch(int(t // g1.T))
                Ft = s.trueF(path, w1, w2, hold); ld = s.draws(path)
                Fs = ptm.delivered_F(ld, w1, w2, hold, P["e"], np.inf, P["T2"]); pbad = ((Fs < s.tau).sum() + 0.5) / (g1.M + 1)
                thr = s.choose_t(); s.pb[s.nb % g1.WIN] = pbad; s.nb += 1
                ok = pbad <= thr
                if ok and guard and s.guard_F(path, w1, w2, hold) < s.tau:
                    ok = False
                    if meas: out["guard_blocks"] += 1
                if ok:
                    if meas:
                        bad = int(Ft < s.tau)
                        out["delivered"] += 1; out["bad"] += bad; out["qual"] += 1 - bad
                        st = s.pstat.setdefault(path, [0, 0]); st[0] += 1; st[1] += bad
                        lk = list(path); fe = s.fep[lk][s.faulted[lk]]; ep = int(t // g1.T)
                        if fe.size and ep >= fe.min():
                            out["post_delivered"] += 1; out["post_bad"] += bad
                            if ep == fe.min(): out["post_bad_early"] += bad
                            else: out["post_bad_late"] += bad
                        else:
                            out["prefault_bad"] += bad
                    break
        vals = list(s.pstat.values())
        out["paths_delivered"] = sum(1 for v in vals if v[0] > 0)
        out["paths_bad"] = sum(1 for v in vals if v[1] > 0)
        out["max_path_bad"] = max([v[1] for v in vals] or [0])
        out["n_faulted"] = int(s.faulted.sum())
        out["alarms_true"] = int(s.alarms[s.faulted].sum()); out["alarms_false"] = int(s.alarms[~s.faulted].sum())
        det = [(s.alarm_ep[l] - s.fep[l]) for l in np.where(s.faulted & (s.alarm_ep >= 0))[0]]
        out["detected"] = len(det); out["mean_delay_ep"] = float(np.mean(det)) if det else -1.0
        return out


def tasks():
    return [["G6", hw, scen, c, i] for hw in ("ion2020", "ionproj") for scen in ("F2", "F4") for c in CTRLS for i in range(NNET)]


def run_id(t):
    return hashlib.sha256("g6|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, scen, ctrl, idx = t
    nseed = int(hashlib.sha256(f"g6net|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"g6run|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    net = NetG6(hw, scen, ctrl, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, scen=scen, ctrl=ctrl, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
