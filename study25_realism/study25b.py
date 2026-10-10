"""Study 25 Block D: the drift-restart cost as a design curve (weak spot 5b). Pre-registered in README_25.md.

Prop. 7 and Study 24 Block B showed that a guard which must stay valid for ANY re-alignment cannot reuse the previous cycle's
information (gcarry bought +0.3 points). Re-use needs a promise. New guard (stated before any run):
  gb<B>  gexact (restart per cycle, alpha spending as G5) PLUS a carried bound: with the DECLARED promise that each
         re-alignment moves the level by at most B (|theta_c - theta_{c-1}| <= B), the combined lower bound for cycle c is
             comb_c = max(CS lower bound of cycle c, comb_{c-1} - B),
         valid by induction whenever the promise holds (each CS at its own spent alpha; union bound as G5). It is available
         from the first moment of a new cycle, before any of the new cycle's data exist.
Scenarios as Study 24 Block B: D (exact re-alignment; true jump 0), Dj (independent level jitter sd 0.005 per cycle, so
jumps have sd 0.0071), Djb (sd 0.02; jumps sd 0.028). B in {0.005, 0.01, 0.02, 0.04, 0.08, 0.16}.
Controllers: cal (no guard), gexact, gpersist (B = 0 in effect, no restart), gb<B>.
"""
import hashlib, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), "/home/claude/s18c"):
    if p and p not in sys.path: sys.path.append(p)
import drift_queue_des_g1 as g1
import drift_queue_des_g5 as g5
import study24b as b24

BS = (0.005, 0.01, 0.02, 0.04, 0.08, 0.16)
CTRLS = ("cal", "gexact", "gpersist") + tuple(f"gb{b}" for b in BS)
SEEDS = (19271, 19272, 19273, 19274)       # fresh confirmatory; dev pilot 20271-20274
DEV = (20271, 20272, 20273, 20274)
NNET = 64


class NetD(b24.NetB):
    def __init__(s, hw, scen, ctrl, seed):
        s.B = float(ctrl[2:]) if ctrl.startswith("gb") else None
        super().__init__(hw, scen, "gexact" if s.B is not None else ctrl, seed)
        s.ctrl25 = ctrl
        s.comb = np.full(s.nl, -np.inf); s.carry = np.full(s.nl, -np.inf)

    def epoch_data(s, e):
        if s.B is None: return b24.NetB.epoch_data(s, e)
        first = e > s.acc_ep and e != s.ep
        if first:
            cid = s.cycle_of(np.full(s.nl, e * g1.T)); sw = cid != s.lastc
            s.carry = np.where(sw, s.comb - s.B, s.carry)                       # previous cycle's final combined bound, minus B
        g5.NetG5.epoch_data(s, e)                                               # gexact's CS for the current cycle (restart)
        if first: s.comb = np.maximum(s.theta_lo, s.carry)

    def guard_lam(s, links, t):
        if s.B is None: return b24.NetB.guard_lam(s, links, t)
        lk = list(links); cyc = s.cycle_of(np.full(s.nl, t))[lk]; ph = s.phase(t)[lk]
        lo = np.where(cyc == s.thc[lk], s.comb[lk], np.where(cyc == s.thc[lk] + 1, s.comb[lk] - s.B, -np.inf))
        return np.clip(lo - g5.G * ph, 0, 1)


def tasks(blk="S25D", nnet=NNET):
    return [[blk, hw, scen, c, i] for hw in ("ion2020", "ionproj") for scen in b24.JIT for c in CTRLS for i in range(nnet)]


def run_id(t):
    return hashlib.sha256("s25d|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, scen, ctrl, idx = t
    if blk == "P25D": seeds = DEV
    nseed = int(hashlib.sha256(f"s25dnet|{blk}|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s25drun|{blk}|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    net = NetD(hw, scen, ctrl, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    o = net.run()
    # realised re-alignment jumps: only the cycles each link actually visits during the run (code review fix)
    c0 = net.cycle_of(np.full(net.nl, -g1.T)); c1 = net.cycle_of(np.full(net.nl, g1.NEPOCH * g1.T + g1.T)); mj = 0.0
    for l in range(net.nl):
        cs = np.clip(np.arange(c0[l], c1[l] + 1), 0, 5); lev = np.clip(net.lam0[l] + net.jit[l, cs], 0, 1)
        if len(lev) > 1: mj = max(mj, float(np.abs(np.diff(lev)).max()))
    return dict(run=run_id(t), block=blk, hw=hw, scen=scen, ctrl=ctrl, idx=idx, max_jump=mj, **o)


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P25D", int(sys.argv[3]) if len(sys.argv) > 3 else 4)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
