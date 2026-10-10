"""Study 18C P1: safety / throughput phase diagram of the frozen C2 controller (v21 'm123') versus information
(pre-registered in README_P1.md; fresh seeds).

Theory (THEORY_NOTE, Prop. 3): the fleet prior is calibrated only if the fleet spread s is identifiable from the fleet
sample. With K fleet windows per link (K*L observations), each a noisy look at lambda with variance
sigma_w^2 = 4 p(1-p) / (n r^2) (n pairs per window, readout factor r) plus the unknown drift phase (A^2/12), the
method-of-moments relative precision of s^2 is the identifiability index
        I = sqrt(K L / 2) / (1 + (sigma_w^2 + A^2/12) / s^2).
C1/C2: SiV I = 0.72 (failed / abstained), NV 3.73 and every ion cell >= 2.37 (passed in C2).
P1 varies the controller/fleet window length T (so n = rho R T) and the number of fleet windows K on two thin-data
hardware types, at g ~ 0 (no drift) with dephasing-only memory, to map safety and throughput against I.
"""
import hashlib, json, sys
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v15 as v15
import drift_queue_des_v18 as v18
import drift_queue_des_c1 as c1
import drift_queue_des_v21 as v21

HW = {"siv": v15.VARIANTS["siv_tau080_L1"], "nv": v15.VARIANTS["nv_tau080"]}
TS = (50.0, 100.0, 200.0, 400.0); KS = (16, 64, 256, 512); NP = 256; G = 1e-9
SEEDS = (19021, 19022, 19023)            # fresh


def ident_index(P, L, T, K, spread=1.0):
    r = (1 - 2 * P["q"]) ** 2; lam = (4 * P["F0"] - 1) / 3; p = (1 + r * lam) / 2; n = v9.RHO * P["R"] * T
    sw2 = 4 * p * (1 - p) / n / r ** 2; s = 4 / 3 * (1 - P["F0"]) * 0.2 * spread
    return float(np.sqrt(K * L / 2) / (1 + (sw2 + 0.02 ** 2 / 12) / s ** 2))


def tasks():
    return [[hw, T, K, i] for hw in HW for T in TS for K in KS for i in range(NP)]


def run_id(t):
    return hashlib.sha256("p1|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    hw, T, K, idx = t
    P, L, tau, ctrl, D, spread, k = HW[hw]; Pc = dict(P, **ctrl)
    pseed = int(hashlib.sha256(f"p1path|{hw}".encode()).hexdigest()[:8], 16)
    lam0, ph = v18.draw_paths_law(P, L, NP, [SEEDS[0], pseed], "normal", spread)[idx]
    phase = ph * 0.02 / G
    seed = [int(hashlib.sha256(f"p1|{hw}|{T}|{K}|{idx}".encode()).hexdigest()[:8], 16), SEEDS[1]]
    mu = v4.service_mu(P, L, True, lam0, D); warm = max(300.0, T)
    r = v21.RunV21(P, L, True, G, v9.LOAD, "fixed", v9.RHO, T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
                   est="static", method="eb128t1", tau=tau, Pc=Pc, spread=spread, mem="deph", t1mult=1.0, warm=warm)
    r.drift_aware = True
    orc = c1.OracleC1(P, L, True, G, v9.LOAD, "none", 0.0, 1.0, 0.0, D, v9.H, seed, oracle=True, mu=mu, lam0=lam0,
                      phase=phase, tau=tau, mem=r.mem, warm=warm)
    s_power, eps, _ = v21.VARIANTS["m123"]
    n_, k_ = v18.fleet_counts_law(P, L, K, spread, [SEEDS[2], pseed + idx], T / v9.T, "normal")
    pF, hw_, s_hat = v21.eb_prior_F_v21(P, n_, k_, s_power); r.set_prior_F(v21.fault_mix(pF, s_hat, eps))
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    oo = pd.DataFrame(orc.go(), columns="t res F pairs latency".split()); oq = int((oo.res == "deliver").sum())
    return dict(run=run_id(t), hw=hw, T=T, K=K, idx=idx, I=ident_index(P, L, T, K, spread), s_hat=s_hat,
                s_true=(1 - P["F0"]) * 0.2 * spread, requests=len(o), delivered=len(x),
                qual=int((x.F >= tau).sum()), bad=int((x.F < tau).sum()), oracle_qual=oq)


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
    elif sys.argv[1:2] == ["--index"]:
        for hw in HW:
            P, L = HW[hw][0], HW[hw][1]
            print(hw, {(T, K): round(ident_index(P, L, T, K), 2) for T in TS for K in KS})
