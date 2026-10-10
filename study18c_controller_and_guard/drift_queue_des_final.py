"""Study 18C FINAL confirmatory run (pre-registered in FINAL_PROTOCOL.md; run ONCE on fresh seeds).

Components (all code paths already exercised in v9-v12; only seeds, path draws and the third cell are new):
  eval  : fresh random path populations (64 paths per cell, seed 18901) under
            - 'adaptive' (label-free self-calibrating controller, RunV11 Agresti-Coull SE), with matched oracle;
            - fixed z in {0,0.5,...,4} (RunV12), used for the fixed-rule test and for LTT evaluation.
  dev   : labelled dev populations for Learn-then-Test (fixed z grid), 64 paths each:
            S0 = same distribution as eval (seed 18902); S1 = link F0 + 0.005 (seed 18903).
            (An S2 = F0 - 0.005 arm was dropped before running, for PSC budget.)
Cells: ion_2020 L2, ion_proj L3, ion_future L4 (purify); g in {0, 1e-5, 1e-4}; est in {static, ols_reset};
static at g = 1e-4 excluded (known, pre-declared drift-bias failure E28/T4).
rho 0.3, T 100 s, load 0.9, D 0.25 s, horizon 300 s + 300 s warm-up, q 0.001.
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v6 as v6
import drift_queue_des_v9 as v9
import drift_queue_des_v11 as v11
import drift_queue_des_v12 as v12

PRESETS = {"ion_2020": (dict(F0=0.940, R=182.0, T2=1.0, q=0.001, e=0.005), 2),
           "ion_proj": (dict(F0=0.970, R=200.0, T2=1.0, q=0.001, e=0.003), 3),
           "ion_future": (dict(F0=0.990, R=1000.0, T2=1.0, q=0.001, e=0.003), 4)}
GS = (1e-9, 1e-5, 1e-4); ESTS = ("static", "ols_reset"); ZG = tuple(float(z) for z in np.arange(0.0, 4.0001, 0.5))
NP = 64; SHIFT = {"S0": 0.0, "S1": +0.005, "S2": -0.005}; SEEDTAG = {"eval": 18901, "S0": 18902, "S1": 18903, "S2": 18904}


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
    return hashlib.sha256("final|{}|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    role, sc, cell, g, est, method, idx = t
    P, L = PRESETS[cell]; Pd = dict(P)
    key = "eval" if role == "eval" else sc
    if role == "dev": Pd["F0"] = P["F0"] + SHIFT[sc]
    lam0, ph = v4.draw_paths(Pd, L, NP, [SEEDTAG[key], L, int(round(P["F0"] * 1000))])[idx]
    phase = ph * 0.02 / g
    seed = [int(hashlib.sha256(f"final|{key}|{cell}|{g}|{idx}".encode()).hexdigest()[:8], 16), 18905]
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
        for t in (["eval", "E", "ion_future", 1e-5, "static", "adaptive", 0], ["dev", "S2", "ion_2020", 1e-4, "ols_reset", "z2.0", 5]):
            print(run_one(t))
