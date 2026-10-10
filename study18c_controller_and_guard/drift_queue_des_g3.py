"""Study 18C G3: 30 x 30 grid (900 nodes, 1,740 links) with route choice; frozen controller vs anytime-guarded controller;
fleet prior from an external sample vs from the network's OWN links (pre-registered in README_G3.md).

Everything is G2 (drift_queue_des_g2.NetG on top of G1) except:
  * grid size 30 x 30 (G1: 5 x 5); request rate 10 per s (G1/G2: 3 per s); router 'best' only;
  * fleet 'ext' = 128 external fleet link-windows (as G1/G2); fleet 'own' = one pre-run calibration window on 512 links
    sampled from the network itself (the network learns its prior from its own hardware).
"""
import hashlib, json, sys
import numpy as np
import drift_queue_des_g1 as g1
import drift_queue_des_g2 as g2
import drift_queue_des_v17 as v17
import drift_queue_des_v21 as v21

N30, RATE, NNET, NOWN = 30, 10.0, 32, 512
SEEDS = (19121, 19122, 19123, 19124)       # fresh confirmatory; cloud timing pilot used 20121-20124 (1 network)


class NetG3(g2.NetG):
    def __init__(s, hw, ctrl, fleet, seed):
        oldN, oldHW = g1.GRID_N, g1.HW[hw]
        g1.GRID_N = N30; g1.HW[hw] = (oldHW[0], oldHW[1], oldHW[2], RATE)
        try:
            super().__init__(hw, "grid", 0, "cal", "best", seed, guard=(ctrl == "calg"))
        finally:
            g1.GRID_N = oldN; g1.HW[hw] = oldHW
        s.fleet = fleet
        if fleet == "own":
            frng = np.random.default_rng([seed[2], seed[3], 77]); P = s.P
            links = frng.choice(s.nl, NOWN, replace=False)
            n = frng.poisson(g1.RHO * P["R"] * g1.T, NOWN); k = frng.binomial(n, (1 + s.r * s.lam[links]) / 2)
            pF, _, s_hat = v21.eb_prior_F_v21(P, n[:, None], k[:, None], 1)
            s.pF = v21.fault_mix(pF, s_hat, g1.EPS); s.s_hat = s_hat
            s.lprior = np.log(np.maximum(s.pF, 1e-300))[None, :] - np.log(len(g1.UG))


def tasks():
    return [["G3", hw, ctrl, fleet, i] for hw in ("ion2020", "ionproj") for ctrl in ("cal", "calg") for fleet in ("ext", "own")
            for i in range(NNET)]


def run_id(t):
    return hashlib.sha256("g3|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, ctrl, fleet, idx = t
    nseed = int(hashlib.sha256(f"g3net|{hw}|{idx}".encode()).hexdigest()[:8], 16)       # paired across ctrl and fleet
    rseed = int(hashlib.sha256(f"g3run|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = NetG3(hw, ctrl, fleet, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    o = net.run()
    return dict(run=run_id(t), block=blk, hw=hw, ctrl=ctrl, fleet=fleet, idx=idx, s_hat=float(net.s_hat),
                s_true=float((1 - net.P["F0"]) * 0.2), **o)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
