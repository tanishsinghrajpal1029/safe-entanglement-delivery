"""Study 18C v10: frontier map (PSC array job via psc_array_runner.py). Development/descriptive map, NOT the final run.

Question: across hardware presets, path length L, drift rate g, calibration share rho and readout error q, what
fraction of the oracle's qualified deliveries can a calibrated controller keep while holding r_cond <= 1%, and how
does that track the risk-law quantities (estimator error s, base rate of sub-threshold attempts)?
Controller: v9 RunV9 with the unbiased drift-aware estimator 'ols_reset'; methods 'fixed3' and 'adaptive' (v9).
Population: 32 random paths per cell (v6-style draw; seed tag 'v10'), oracle run on the same path and seed.
Presets (link Werner F0, heralding rate R per link [Hz], T2 [s], gate error e; q = readout flip, swept):
  ion_2020   F0 0.940 R 182  T2 1.0 e 0.005   (Stephenson et al. PRL 124, 110501 (2020) link fidelity and rate)
  ion_proj   F0 0.970 R 200  T2 1.0 e 0.003   (projection)
  ion_future F0 0.990 R 1000 T2 1.0 e 0.003   (projection)
Grid: L {1,2,3,4} (purify always) x g {1e-6,1e-5,1e-4} x rho {0.1,0.3} x q {0.001,0.01,0.03} x method x 32 paths.
T = 100 s, load 0.9, D 0.25 s, horizon 300 s + 300 s warm-up.
"""
import hashlib, math
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v6 as v6
import drift_queue_des_v9 as v9

BASE = {"ion_2020": dict(F0=0.940, R=182.0, T2=1.0, e=0.005), "ion_proj": dict(F0=0.970, R=200.0, T2=1.0, e=0.003),
        "ion_future": dict(F0=0.990, R=1000.0, T2=1.0, e=0.003)}
LS = (1, 2, 3, 4); GS = (1e-6, 1e-5, 1e-4); RHOS = (0.1, 0.3); QS = (0.001, 0.01, 0.03); METHODS = ("fixed3", "adaptive")
NP = 32; T, LOAD, D, H = 100.0, 0.9, 0.25, 300.0


def tasks():
    return [[p, L, g, rho, q, m, i] for p in BASE for L in LS for g in GS for rho in RHOS for q in QS for m in METHODS for i in range(NP)]


def run_id(t):
    return hashlib.sha256("v10|{}|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    pre, L, g, rho, q, method, idx = t
    P = dict(BASE[pre], q=q)
    lam0, ph = v4.draw_paths(P, L, NP, [18851, L, int(round(P["F0"] * 1000))])[idx]
    phase = ph * 0.02 / g
    seed = [int(hashlib.sha256(f"v10|{pre}|{L}|{g}|{idx}".encode()).hexdigest()[:8], 16), 18852]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = v9.RunV9(P, L, True, g, LOAD, "fixed", rho, T, 0.0, D, H, seed, mu=mu, lam0=lam0, phase=phase,
                 est="ols_reset", method=method)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    orr = v6.RunV6(P, L, True, g, LOAD, "none", 0.0, 1.0, 0.0, D, H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase)
    oo = pd.DataFrame(orr.go(), columns="t res F pairs latency".split()); ox = oo[oo.res == "deliver"]
    zs = np.array(r.zs) if r.zs else np.array([np.nan])
    return dict(run=run_id(t), preset=pre, L=L, g=g, rho=rho, q=q, method=method, idx=idx,
                lam0_min=float(np.min(lam0)), requests=len(o), delivered=len(x), qual=int((x.F >= 0.9).sum()),
                bad=int((x.F < 0.9).sum()), oracle_qual=int((ox.F >= 0.9).sum()), oracle_requests=len(oo),
                z_inf_frac=float(np.mean(np.isinf(zs))), z_med=float(np.median(np.minimum(zs, 99))))


if __name__ == "__main__":
    import json, sys
    if len(sys.argv) > 1 and sys.argv[1] == "--write-tasks":
        ts = tasks(); out = sys.argv[2] if len(sys.argv) > 2 else "tasks_v10.jsonl"
        with open(out, "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks -> {out}")
    elif len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        for t in (["ion_2020", 1, 1e-5, 0.3, 0.001, "fixed3", 0], ["ion_future", 4, 1e-4, 0.1, 0.03, "adaptive", 3]):
            print(run_one(t))
