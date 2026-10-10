"""Study 18C G1: the frozen final controller (C2 'm123') on NETWORKS with ROUTE CHOICE (pre-registered in README_G1.md).

Question. Real networks are not one line: a router picks a path, usually the one that LOOKS best from the same calibration
data the delivery controller then uses. Picking the best-looking of several noisy estimates is a selection effect (winner's
curse). Does the label-free controller stay calibrated when the path itself is chosen from the data?

Theory (Proposition 2 extended; stated before any run). If the router's choice is a function of the data D, and the
controller's p = P(F < tau | D) is the posterior under the true law given ALL of D (including the data used to choose the
path), then {path chosen, p <= t} is D-measurable and the tower property still gives r(t) = E[p | delivered].
Selection on D therefore does NOT bias a calibrated controller. A controller whose p is not the true posterior (flat prior,
'flat') is exposed: selection picks paths whose estimates are optimistic by luck.

Model (simplified relative to the single-path DES; all simplifications stated in README_G1.md):
  * topology 'grid': 5 x 5 nodes, 40 nearest-neighbour links; requests between random node pairs at hop distance 1..Lmax;
    candidates = all shortest paths.  topology 'par': two end nodes joined by k disjoint paths of Lmax links (best-of-k).
  * each link: F0 ~ fleet law Normal(F0, 0.2(1-F0)) (clipped as v18), drift phase u ~ U(0,1), current lambda =
    (4F0-1)/3 - 0.02 u (g ~ 0, no drift in time; as P1).
  * calibration: fraction rho = 0.3 of each link's heralded pairs; every T = 100 s epoch each link yields
    n ~ Poisson(rho R T) parity pairs, k ~ Binomial(n, (1 + r lambda)/2). Decisions at time t use the previous complete
    epoch (a batched 100-s window), so the router and the controller see the SAME counts.
  * requests: Poisson arrivals, served one at a time (no link contention); the router picks a candidate path once per
    request; up to 4 attempts; each attempt makes two chains (link heralds Exp((1-rho)R)), purifies (DEJMPS), and the
    true delivered fidelity is the PTM T1/T2 model (dephasing memory, T1 = inf) with the true lambdas and actual waits.
  * controllers: 'cal' = frozen C2 controller (EB fleet prior from 128 fleet link-windows, uniform-s hyperprior, 5% fault
    component, exact binomial likelihood, PTM physics, window local-fdr threshold delta = 1%); 'flat' = same rule with a
    Jeffreys (flat) posterior per link.  Routers: 'random' (ignores data) or 'best' (max sum log of the controller's own
    point estimate of lambda over the path's links).
  * oracle: knows true lambdas; picks the truly best candidate; delivers iff true F >= tau (throughput reference).
"""
import hashlib, itertools, json, sys
import numpy as np
import ptm_model as ptm
import drift_queue_des_v15 as v15
import drift_queue_des_v16 as v16
import drift_queue_des_v17 as v17
import drift_queue_des_v18 as v18
import drift_queue_des_v21 as v21

RHO, T, AMP, BUDGET = 0.3, 100.0, 0.02, 4
M, DELTA, CMIN, WIN, MINW = 256, 0.01, 20, 500, 100
TGRID = v16.TGRID; UG = v16.UG
HW = {"ion2020": (v15.ION2020, 0.90, 2, 3.0), "ionproj": (v15.IONPROJ, 0.90, 3, 3.0), "nv": (v15.NV, 0.80, 1, 0.3)}
# name -> (preset, tau, Lmax, request rate per s)
GRID_N, NEPOCH, WARM_EPOCH, NNET = 5, 30, 3, 64
SEEDS = (19101, 19102, 19103, 19104)           # confirmatory (fresh); the cloud dev pilot uses 20101-20104
EPS = v21.EPS


def grid_topology(n):
    nodes = [(i, j) for i in range(n) for j in range(n)]; edges = {}
    for (i, j) in nodes:
        for (a, b) in ((i + 1, j), (i, j + 1)):
            if a < n and b < n: edges[frozenset(((i, j), (a, b)))] = len(edges)
    return nodes, edges


def shortest_paths(src, dst, edges):
    (i0, j0), (i1, j1) = src, dst; di, dj = i1 - i0, j1 - j0
    moves = [(np.sign(di), 0)] * abs(di) + [(0, np.sign(dj))] * abs(dj); out = set()
    for perm in set(itertools.permutations(range(len(moves)))):
        cur = src; path = []
        for p in perm:
            nxt = (cur[0] + moves[p][0], cur[1] + moves[p][1]); path.append(edges[frozenset((cur, nxt))]); cur = nxt
        out.add(tuple(path))
    return sorted(out)


class Net:
    def __init__(s, hw, topo, k, ctrl, route, seed):
        s.P, s.tau, s.Lmax, s.rate = HW[hw]; s.topo, s.k, s.ctrl, s.route = topo, k, ctrl, route
        s.rng = np.random.default_rng(seed[:2]); s.orng = np.random.default_rng(seed[:2] + [7])
        s.r = (1 - 2 * s.P["q"]) ** 2; P = s.P
        if topo == "grid":
            nodes, edges = grid_topology(GRID_N); s.nl = len(edges); pairs = []
            for a in nodes:
                for b in nodes:
                    d = abs(a[0] - b[0]) + abs(a[1] - b[1])
                    if 1 <= d <= s.Lmax: pairs.append(shortest_paths(a, b, edges))
            s.cands = pairs
        else:
            s.nl = k * s.Lmax; s.cands = [[tuple(range(c * s.Lmax, (c + 1) * s.Lmax)) for c in range(k)]]
        net_rng = np.random.default_rng(seed[2:])
        F0 = v18.draw_F0(P, 1, s.nl, net_rng, "normal")[:, 0]; u = net_rng.uniform(0, 1, s.nl)
        s.lam = np.clip((4 * F0 - 1) / 3 - AMP * u, 0, 1)
        s.pb = np.zeros(WIN); s.nb = 0; s.ep = None
        if ctrl == "cal":
            n_, k_ = v18.fleet_counts_law(P, 1, 128, 1.0, [seed[3], seed[2]], 1, "normal")
            pF, _, s_hat = v21.eb_prior_F_v21(P, n_, k_, 1); s.pF = v21.fault_mix(pF, s_hat, EPS); s.s_hat = s_hat
            s.lgrid = np.clip((4 * v17.FG - 1) / 3, 0, 1)[None, :] - AMP * UG[:, None]        # (U, F) current lambda
            s.lgrid = np.clip(s.lgrid, 0, 1); pe = (1 + s.r * s.lgrid) / 2; s.lp, s.lq = np.log(pe), np.log1p(-pe)
            s.lprior = np.log(np.maximum(s.pF, 1e-300))[None, :] - np.log(len(UG))

    def epoch_data(s, e):
        if e == s.ep: return
        s.ep = e; P = s.P
        s.n = s.rng.poisson(RHO * P["R"] * T, s.nl); s.kc = s.rng.binomial(s.n, (1 + s.r * s.lam) / 2)
        if s.ctrl == "cal":
            ll = s.kc[:, None, None] * s.lp[None] + (s.n - s.kc)[:, None, None] * s.lq[None] + s.lprior[None]
            ll -= ll.max(axis=(1, 2), keepdims=True); w = np.exp(ll).reshape(s.nl, -1); w /= w.sum(1, keepdims=True)
            s.cdf = np.cumsum(w, axis=1); s.est = w @ s.lgrid.ravel()
        else:
            s.est = np.clip((2 * (s.kc + 0.5) / (s.n + 1) - 1) / s.r, 1e-6, 1)

    def draws(s, links):
        out = np.empty((M, len(links)))
        for j, l in enumerate(links):
            if s.ctrl == "cal":
                idx = np.minimum(np.searchsorted(s.cdf[l], s.rng.random(M)), s.cdf.shape[1] - 1); out[:, j] = s.lgrid.ravel()[idx]
            else:
                out[:, j] = np.clip((2 * s.rng.beta(s.kc[l] + 0.5, s.n[l] - s.kc[l] + 0.5, M) - 1) / s.r, 0, 1)
        return out

    def choose_t(s):
        n = min(s.nb, WIN)
        if n < MINW: return 1e-3
        pb = s.pb[:n]; Mk = pb[None, :] <= TGRID[:, None]; cnt = Mk.sum(1)
        risk = (Mk * pb[None, :]).sum(1) / np.maximum(cnt, 1)
        ok = np.nonzero((risk <= DELTA) & (cnt >= CMIN))[0]
        return float(TGRID[ok[-1]]) if len(ok) else -1.0

    def chains(s, rng, t, L):
        rt = (1 - RHO) * s.P["R"]
        h1 = t + rng.exponential(1 / rt, L); d1 = h1.max(); h2 = d1 + rng.exponential(1 / rt, L); d2 = h2.max()
        return d1 - h1, d2 - h2, d2 - d1, d2

    def trueF(s, links, w1, w2, hold):
        return float(ptm.delivered_F(s.lam[list(links)][None, :], w1, w2, hold, s.P["e"], np.inf, s.P["T2"])[0])

    def run(s):
        P = s.P; t = 0.0; H = NEPOCH * T; out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, sel_bias=0.0, nsel=0)
        arr = s.rng.exponential(1 / s.rate)
        while arr < H:
            t = max(t, arr); arr += s.rng.exponential(1 / s.rate)
            cset = s.cands[int(s.rng.integers(len(s.cands)))]
            e = int(t // T); s.epoch_data(e - 1)
            if s.route == "best" and len(cset) > 1:
                sc = [np.log(np.maximum(s.est[list(c)], 1e-9)).sum() for c in cset]; path = cset[int(np.argmax(sc))]
            else:
                path = cset[int(s.rng.integers(len(cset)))]
            meas = t >= WARM_EPOCH * T
            if meas:
                out["requests"] += 1; out["nsel"] += 1
                out["sel_bias"] += float(np.log(np.maximum(s.est[list(path)], 1e-9)).sum() - np.log(np.maximum(s.lam[list(path)], 1e-9)).sum())
            # oracle on its own stream: truly best candidate, deliver iff true F >= tau
            op = cset[int(np.argmax([np.log(np.maximum(s.lam[list(c)], 1e-9)).sum() for c in cset]))]; to = t
            for _ in range(BUDGET):
                w1, w2, hold, to = s.chains(s.orng, to, len(op))
                if s.trueF(op, w1, w2, hold) >= s.tau:
                    if meas: out["oracle_qual"] += 1
                    break
            for _ in range(BUDGET):
                w1, w2, hold, t = s.chains(s.rng, t, len(path)); s.epoch_data(int(t // T) - 1)
                Ft = s.trueF(path, w1, w2, hold); ld = s.draws(path)
                Fs = ptm.delivered_F(ld, w1, w2, hold, P["e"], np.inf, P["T2"]); pbad = ((Fs < s.tau).sum() + 0.5) / (M + 1)
                thr = s.choose_t(); s.pb[s.nb % WIN] = pbad; s.nb += 1
                if pbad <= thr:
                    if meas: out["delivered"] += 1; out["bad"] += int(Ft < s.tau); out["qual"] += int(Ft >= s.tau)
                    break
        out["sel_bias"] = out["sel_bias"] / max(out["nsel"], 1)
        return out


def tasks():
    G = [["G", hw, "grid", 0, ctrl, route, i] for hw in ("ion2020", "ionproj") for route in ("random", "best")
         for ctrl in ("cal", "flat") for i in range(NNET)]
    K = [["K", hw, "par", k, ctrl, "best", i] for hw in ("nv", "ion2020") for k in (1, 3, 8) for ctrl in ("cal", "flat") for i in range(NNET)]
    return G + K


def run_id(t):
    return hashlib.sha256("g1|{}|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, topo, k, ctrl, route, idx = t
    # network (links, fleet sample) depends only on (block, hw, topo, k, idx): paired across controllers and routers
    nseed = int(hashlib.sha256(f"g1net|{blk}|{hw}|{topo}|{k}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"g1run|{blk}|{hw}|{topo}|{k}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net(hw, topo, k, ctrl, route, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    o = net.run()
    return dict(run=run_id(t), block=blk, hw=hw, topo=topo, k=k, ctrl=ctrl, route=route, idx=idx, **o)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
