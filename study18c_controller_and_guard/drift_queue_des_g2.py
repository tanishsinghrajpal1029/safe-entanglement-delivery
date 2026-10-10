"""Study 18C G2: per-path ANYTIME-VALID GUARD added to the frozen controller on networks (pre-registered in README_G2.md).

Why (post hoc, motivated by G1, ledger E66/E67). The fleet-prior posterior is calibrated MARGINALLY (averaged over paths
drawn from the fleet), so Proposition 2 bounds the pooled risk, not the risk of a given path. A path whose true delivered
fidelity sits at the threshold can, in one optimistic calibration window, receive many deliveries that are all bad (G1:
one network, 190 of 190 bad, while the controller's own mean prediction stayed 0.91%).

Remedy (stated before any confirmatory run). Keep the frozen Bayesian rule (marginal risk <= delta) and ADD a per-path guard:
  * every link keeps ALL its calibration counts since start (stationary links, g ~ 0, as G1);
  * for each link, a (1 - alpha/Lmax) anytime-valid lower confidence bound on its parity probability from the Beta(1/2,1/2)
    mixture martingale (Robbins; prior-posterior ratio): CS = {p : B(a+K, b+N-K)/B(a, b) / (p^K (1-p)^(N-K)) < Lmax/alpha};
  * deliver only if ALSO the PTM-model fidelity at the links' lower bounds, with the actual waits, is >= tau.
Proposition 6 (per-path anytime guarantee). If the physics model is exact and links are stationary, then for EVERY path,
P(the path ever delivers a pair with true F < tau) <= alpha, whatever its true quality, over the whole run.
(Proof: by Ville's inequality all of the path's link bounds hold at all times with probability >= 1 - alpha; F is increasing
in each lambda, so on that event every delivered pair has true F >= F_guard >= tau.)  alpha = 0.05.
Everything else (networks, routers, physics, oracle) is G1 unchanged.
"""
import hashlib, json, sys
import numpy as np
from scipy.special import betaln
import ptm_model as ptm
import drift_queue_des_g1 as g1

ALPHA = 0.05
SEEDS = (19111, 19112, 19113, 19114)     # fresh confirmatory; the cloud dev pilot used 20111-20114
NNET = 64


def cs_lower(N, K, level):
    """Vectorised lower end of the Beta(1/2,1/2)-mixture confidence sequence for a Bernoulli mean (level = alpha per link)."""
    N = np.asarray(N, float); K = np.asarray(K, float); thr = np.log(1 / level)
    lm = betaln(0.5 + K, 0.5 + N - K) - betaln(0.5, 0.5)
    lo = np.full(N.shape, 1e-12); hi = np.clip(K / np.maximum(N, 1), 1e-12, 1 - 1e-12)   # log M(p) decreases on (0, K/N]
    for _ in range(60):
        mid = (lo + hi) / 2; logM = lm - (K * np.log(mid) + (N - K) * np.log1p(-mid))
        inside = logM < thr; hi = np.where(inside, mid, hi); lo = np.where(inside, lo, mid)
    return np.where(N > 0, hi, 0.0)


class NetG(g1.Net):
    def __init__(s, *a, guard=True, **k):
        super().__init__(*a, **k); s.guard = guard; s.N = np.zeros(s.nl); s.K = np.zeros(s.nl); s.acc_ep = -10 ** 9
        s.lamlo = np.zeros(s.nl); s.pstat = {}

    def epoch_data(s, e):
        if e == s.ep: return
        super().epoch_data(e)
        if e > s.acc_ep:                         # accumulate each epoch once, in time order
            s.N += s.n; s.K += s.kc; s.acc_ep = e
            plo = cs_lower(s.N, s.K, ALPHA / s.Lmax); s.lamlo = np.clip((2 * plo - 1) / s.r, 0, 1)

    def run(s):
        P = s.P; t = 0.0; H = g1.NEPOCH * g1.T
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, sel_bias=0.0, nsel=0, guard_blocks=0)
        arr = s.rng.exponential(1 / s.rate)
        while arr < H:
            t = max(t, arr); arr += s.rng.exponential(1 / s.rate)
            cset = s.cands[int(s.rng.integers(len(s.cands)))]
            e = int(t // g1.T); s.epoch_data(e - 1)
            if s.route == "best" and len(cset) > 1:
                sc = [np.log(np.maximum(s.est[list(c)], 1e-9)).sum() for c in cset]; path = cset[int(np.argmax(sc))]
            else:
                path = cset[int(s.rng.integers(len(cset)))]
            meas = t >= g1.WARM_EPOCH * g1.T
            if meas:
                out["requests"] += 1; out["nsel"] += 1
                out["sel_bias"] += float(np.log(np.maximum(s.est[list(path)], 1e-9)).sum() - np.log(np.maximum(s.lam[list(path)], 1e-9)).sum())
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
                        out["delivered"] += 1; out["bad"] += int(Ft < s.tau); out["qual"] += int(Ft >= s.tau)
                        st = s.pstat.setdefault(path, [0, 0]); st[0] += 1; st[1] += int(Ft < s.tau)
                    break
        out["sel_bias"] = out["sel_bias"] / max(out["nsel"], 1)
        out["paths_delivered"] = sum(1 for v in s.pstat.values() if v[0] > 0)
        out["paths_bad"] = sum(1 for v in s.pstat.values() if v[1] > 0)
        out["max_path_bad"] = max([v[1] for v in s.pstat.values()] or [0])
        return out


def tasks():
    G = [["G", hw, "grid", 0, ctrl, route, i] for hw in ("ion2020", "ionproj") for route in ("random", "best")
         for ctrl in ("cal", "calg") for i in range(NNET)]
    K = [["K", hw, "par", k, ctrl, "best", i] for hw in ("nv", "ion2020") for k in (1, 3, 8) for ctrl in ("cal", "calg") for i in range(NNET)]
    return G + K


def run_id(t):
    return hashlib.sha256("g2|{}|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, topo, k, ctrl, route, idx = t
    nseed = int(hashlib.sha256(f"g1net|{blk}|{hw}|{topo}|{k}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"g1run|{blk}|{hw}|{topo}|{k}|{idx}".encode()).hexdigest()[:8], 16)
    net = NetG(hw, topo, k, "cal", route, [rseed, seeds[1], nseed, seeds[0] + seeds[2]], guard=(ctrl == "calg"))
    o = net.run()
    return dict(run=run_id(t), block=blk, hw=hw, topo=topo, k=k, ctrl=ctrl, route=route, idx=idx, **o)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
