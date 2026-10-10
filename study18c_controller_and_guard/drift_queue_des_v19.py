"""Study 18C v19: end-to-end controller test with NON-Werner (T1/T2) memories as the truth (pre-registered, README_v19.md).

The controller (eb128, v17: estimated fleet prior, depolarizing-storage model) is unchanged.  Only the TRUTH changes:
the fidelity of every delivered pair is computed exactly (memory_t1t2_exact.delivered_F, NetSquid-validated by
netsquid_t1t2_check.py) with amplitude damping + dephasing memories of coherence time T2 (= the model's T2) and
  deph   T1 = infinity (pure dephasing; trapped-ion hyperfine-like)
  t1eq   T1 = T2
  ad     T1 = T2 / 2 (amplitude-damping limit, T2 = 2 T1)
Per-link waits are recorded from the same link-arrival draws (RNG stream unchanged). Elementary links stay Werner.
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v15 as v15
import drift_queue_des_v16 as v16
import drift_queue_des_v17 as v17
import memory_t1t2_exact as mx

MEMS = {"deph": np.inf, "t1eq": 1.0, "ad": 0.5}          # T1 in units of T2


class RunV19(v17.RunV17):
    def __init__(s, *a, mem="deph", **k):
        super().__init__(*a, **k); s.mem = ("t1t2", MEMS[mem] * s.P["T2"], s.P["T2"])

    def chain(s, t):
        tt = s.rng.exponential(1 / s.Ruser, s.L); s._w = tt.max() - tt
        return t + tt.max(), float(s._w.sum())

    def serve(s, t0, deadline):
        t = t0; pairs = 0; att = 0; Pc = s.Pc
        while True:
            att += 1; lam = s.lam_true(t)
            d1, w1 = s.chain(t); pw1 = s._w.copy(); pairs += s.L
            d2, w2 = s.chain(d1); pw2 = s._w.copy(); pairs += s.L; hold = d2 - d1; tdone = d2
            if tdone > deadline: return deadline, "miss", None, pairs
            ld = s.lam_draws_pop(tdone); deliver = False
            if ld is not None:
                Fs = v16.dej_vec(v16.chainF_vec(ld, Pc, s.L, w1 + hold), v16.chainF_vec(ld, Pc, s.L, w2), Pc["e"])
                pbad = ((Fs < s.tau).sum() + 0.5) / (v16.M + 1)
                thr = s.choose_t(); deliver = pbad <= thr
                s.pb[s.nb % v16.WIN] = pbad; s.nb += 1
                if tdone >= s.warm: s.ts.append(thr)
            if deliver:
                Ft = float(mx.delivered_F(np.clip(lam, 0, 1), pw1, pw2, hold, s.P["e"], s.mem))
                Fm = v4.dej(v4.chainF(lam, s.P, s.L, w1 + hold), v4.chainF(lam, s.P, s.L, w2), s.P["e"])
                s.fm.append(Fm)
                return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


VARIANTS = v16.VARIANTS
SEEDS = (18971, 18972, 18973)   # fresh
G = 1e-5; NP = 64; METHOD = "eb128"


def tasks():
    return [[v, m, i] for v in VARIANTS for m in MEMS for i in range(NP)]


def run_id(t):
    return hashlib.sha256("v19|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    var, mem, idx = t
    P, L, tau, ctrl, D, spread, k = VARIANTS[var]; Pc = dict(P, **ctrl)
    pseed = int(hashlib.sha256(f"v19path|{var}".encode()).hexdigest()[:8], 16)
    lam0, ph = v15.draw_paths_spread(P, L, NP, [SEEDS[0], pseed], spread)[idx]
    phase = ph * 0.02 / G
    seed = [int(hashlib.sha256(f"v19|{var}|{idx}".encode()).hexdigest()[:8], 16), SEEDS[1]]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV19(P, L, True, G, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
               est="static", method=METHOD, tau=tau, Pc=Pc, spread=spread, mem=mem)
    r.fm = []
    K, mult = v17.EBK[METHOD]
    n_, k_ = v17.fleet_counts(P, L, K, spread, [SEEDS[2], pseed + idx], mult)
    pF, hw = v17.eb_prior_F(P, n_, k_); r.set_prior_F(pF)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    fm = np.array(r.fm[-len(x):]) if len(x) else np.array([])
    return dict(run=run_id(t), variant=var, L=L, tau=tau, mem=mem, idx=idx, requests=len(o), delivered=len(x),
                bad=int((x.F < tau).sum()), bad_under_model_truth=int((fm < tau).sum()) if len(fm) else 0,
                mean_true_minus_model=float((x.F.values - fm).mean()) if len(x) and len(fm) == len(x) else float("nan"))


if __name__ == "__main__":
    import json, sys
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
