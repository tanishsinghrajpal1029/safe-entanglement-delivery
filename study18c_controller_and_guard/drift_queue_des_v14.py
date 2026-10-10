"""Study 18C v14: statistically appropriate baselines (pre-registered in README_v14.md; fresh seeds).

Answers the critique "compare against a statistically appropriate baseline". Same simulator, controller and run
structure as the frozen final run (drift_queue_des_final.py, imported unchanged), with:
  * cells ion_2020 L2 and ion_proj L3 (ion_future dropped: risk is ~0 for every method there; PSC budget);
  * z grid {0, 0.5, 1, 1.2816, 1.5, 2, 2.3263, 2.5, 3, 3.5, 4}: 1.2816 = Phi^-1(0.90) is a delta-quantile / belief
    controller at delta = 0.10 (Clayton et al. 2608.07163); 2.3263 = Phi^-1(0.99) is a Bayesian flat-prior
    per-decision rule 'deliver iff P_post(F < 0.9) <= 1%';
  * dev populations S0 (same distribution) and S1 (link F0 + 0.005) with 64 labelled paths each, used by
    CLUSTER-AWARE Learn-then-Test (paths are the resampling unit) in analyze_v14.py;
  * fresh seed tags (18911-18913).
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v6 as v6
import drift_queue_des_v9 as v9
import drift_queue_des_v11 as v11
import drift_queue_des_v12 as v12
import drift_queue_des_final as fin

PRESETS = {k: fin.PRESETS[k] for k in ("ion_2020", "ion_proj")}
GS = fin.GS; ESTS = fin.ESTS
ZG = (0.0, 0.5, 1.0, 1.2816, 1.5, 2.0, 2.3263, 2.5, 3.0, 3.5, 4.0)
NP = 64; SHIFT = {"S0": 0.0, "S1": +0.005}; SEEDTAG = {"eval": 18911, "S0": 18912, "S1": 18913}


def groups():
    return [(c, g, e) for c in PRESETS for g in GS for e in ESTS if not (g == 1e-4 and e == "static")]


def tasks():
    ts = []
    for c, g, e in groups():
        for i in range(NP):
            ts.append(["eval", "E", c, g, e, "adaptive", i])
            for z in ZG: ts.append(["eval", "E", c, g, e, f"z{z}", i])
            for sc in ("S0", "S1"):
                for z in ZG: ts.append(["dev", sc, c, g, e, f"z{z}", i])
    return ts


def run_id(t):
    return hashlib.sha256("v14|{}|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    role, sc, cell, g, est, method, idx = t
    P, L = PRESETS[cell]; Pd = dict(P)
    key = "eval" if role == "eval" else sc
    if role == "dev": Pd["F0"] = P["F0"] + SHIFT[sc]
    lam0, ph = v4.draw_paths(Pd, L, NP, [SEEDTAG[key], L, int(round(P["F0"] * 1000))])[idx]
    phase = ph * 0.02 / g
    seed = [int(hashlib.sha256(f"v14|{key}|{cell}|{g}|{idx}".encode()).hexdigest()[:8], 16), 18914]
    mu = v4.service_mu(P, L, True, lam0, v9.D)
    common = dict(mu=mu, lam0=lam0, phase=phase, est=est)
    if method == "adaptive":
        r = v11.RunV11(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, v9.D, v9.H, seed, method="adaptive", **common)
    else:
        r = v12.RunV12(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, v9.D, v9.H, seed, zfix=float(method[1:]), **common)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    oq = -1
    if method == "adaptive":
        orr = v6.RunV6(P, L, True, g, v9.LOAD, "none", 0.0, 1.0, 0.0, v9.D, v9.H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase)
        oo = pd.DataFrame(orr.go(), columns="t res F pairs latency".split()); oq = int((oo[oo.res == "deliver"].F >= 0.9).sum())
    return dict(run=run_id(t), role=role, scen=sc, cell=cell, L=L, g=g, est=est, method=method, idx=idx,
                lam0_min=float(np.min(lam0)), delivered=len(x), qual=int((x.F >= 0.9).sum()), bad=int((x.F < 0.9).sum()),
                oracle_qual=oq)


if __name__ == "__main__":
    import json, sys
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
    elif sys.argv[1:2] == ["--smoke"]:
        for t in (["eval", "E", "ion_proj", 1e-5, "static", "z1.2816", 0], ["dev", "S1", "ion_2020", 1e-4, "ols_reset", "adaptive", 3]):
            print(run_one(t))
