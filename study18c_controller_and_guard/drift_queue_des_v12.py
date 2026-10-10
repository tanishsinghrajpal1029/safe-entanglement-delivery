"""Study 18C v12: Learn-then-Test (LTT) baseline vs the label-free self-calibrating controller (PSC array).

Baseline (generous): LTT [Angelopoulos et al., arXiv 2110.01052] with LABELLED dev data (the true F of every
delivered dev pair is given for free). Rule family: fixed z (deliver iff d >= z s) on the RunV11 estimator (AC SE).
Selection: fixed-sequence testing from the most conservative z downward; H0(z): r_cond(z) > delta (=1%),
p-value = P[Bin(n_deliv, delta) <= n_bad]; keep lowering z while p <= alpha (=0.05); z* = last rejected z.
(Pooling deliveries across paths treats them as iid; clustering by path makes this optimistic -- part of the test.)
Dev scenarios: S0 = fresh draws from the SAME path distribution as eval; S1 = dev paths drawn with link F0 + 0.005
(better paths -> fewer near-misses: the population shift that broke v6).
Eval paths and seeds are IDENTICAL to v11 population A, so v11's 'adaptive' rows are the label-free comparator.
Tasks: role in {dev, eval}; z grid {0,0.5,...,5}; cells ion_2020 L2, ion_proj L3; g {0,1e-5,1e-4}; est {static,ols_reset}.
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v6 as v6
import drift_queue_des_v9 as v9
import drift_queue_des_v11 as v11

ZG = tuple(np.round(np.arange(0.0, 5.0001, 0.5), 2)); SHIFT = 0.005


class RunV12(v11.RunV11):
    def __init__(s, *a, zfix=2.0, **k):
        super().__init__(*a, method="fixed", **k); s.zfix = zfix

    def choose_z(s):
        return s.zfix


def tasks():
    ts = []
    for c in v9.CELLS:
        for g in v9.GS:
            for e in v9.ESTS:
                for z in ZG:
                    for i in range(32):
                        ts.append(["eval", "E", c, g, e, float(z), i])
                        for sc in ("S0", "S1"): ts.append(["dev", sc, c, g, e, float(z), i])
    return ts


def run_id(t):
    return hashlib.sha256("v12|{}|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    role, sc, cell, g, est, z, idx = t
    L = v9.CELLS[cell]; P = dict(v4.PRE[cell])
    if role == "eval":   # identical to v11 population A
        lam0, ph = v4.draw_paths(P, L, 32, [18822, L])[idx]
        seed = [int(hashlib.sha256(f"v9A|{cell}|{g}|{idx}".encode()).hexdigest()[:8], 16), 18841]
    else:
        if sc == "S1": P["F0"] = P["F0"] + SHIFT
        lam0, ph = v4.draw_paths(P, L, 32, [18861 if sc == "S0" else 18862, L])[idx]
        seed = [int(hashlib.sha256(f"v12dev|{sc}|{cell}|{g}|{idx}".encode()).hexdigest()[:8], 16), 18863]
    Pr = v4.PRE[cell]; phase = ph * 0.02 / g
    mu = v4.service_mu(Pr, L, True, lam0, v9.D)
    r = RunV12(Pr, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, v9.D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
               est=est, zfix=z)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    return dict(run=run_id(t), role=role, scen=sc, cell=cell, L=L, g=g, est=est, z=z, idx=idx,
                lam0_min=float(np.min(lam0)), delivered=len(x), qual=int((x.F >= 0.9).sum()), bad=int((x.F < 0.9).sum()))


if __name__ == "__main__":
    import json, sys
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
    elif sys.argv[1:2] == ["--smoke"]:
        a = run_one(["eval", "E", "ion_proj", 1e-5, "static", 2.0, 0])
        print(a)
