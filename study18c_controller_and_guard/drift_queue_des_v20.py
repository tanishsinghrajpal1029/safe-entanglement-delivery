"""Study 18C v20: T1-aware controller (pre-registered in README_v20.md).

v19 (E49) showed the depolarising-storage controller model is unsafe for amplitude-damping-limited memories
(T2 = 2 T1): 10-39% bad deliveries on ion cells. v20 gives the controller the T1/T2 memory model: its per-draw
fidelity prediction uses ptm_model.delivered_F (vectorised Pauli-transfer form of the NetSquid-validated exact model;
matches it to 6e-16), with the per-link waits it observes. Everything else (eb128 fleet prior, window threshold) is v17.
Truth: exact T1/T2 model (memory_t1t2_exact), as in v19.
Configs (truth memory, controller):
  ad/eb128         replication of the v19 failure (depolarising model)
  ad/eb128t1       T1-aware controller, correct T1 = T2/2
  ad/eb128t1opt    T1-aware controller assuming T1 = 1.25 x true (optimistic: under-states damping)
  t1eq/eb128t1     T1 = T2
  deph/eb128t1     T1 = infinity (removes the depolarising model's pessimism: margin test)
  deph/eb128       paired efficiency reference
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v15 as v15
import drift_queue_des_v16 as v16
import drift_queue_des_v17 as v17
import drift_queue_des_v19 as v19
import memory_t1t2_exact as mx
import ptm_model as ptm

CONFIGS = {"ad_eb128": ("ad", "eb128", None), "ad_eb128t1": ("ad", "eb128t1", 1.0), "ad_eb128t1opt": ("ad", "eb128t1", 1.25),
           "t1eq_eb128t1": ("t1eq", "eb128t1", 1.0), "deph_eb128t1": ("deph", "eb128t1", 1.0), "deph_eb128": ("deph", "eb128", None)}
v17.EBK.setdefault("eb128t1", v17.EBK["eb128"])        # same fleet prior (128 path-windows)


class RunV20(v19.RunV19):
    def __init__(s, *a, t1mult=None, **k):
        super().__init__(*a, **k); s.t1mult = t1mult
        T1, T2 = s.mem[1], s.mem[2]; s.cT1 = T1 * t1mult if t1mult else None; s.cT2 = T2

    def serve(s, t0, deadline):
        if s.t1mult is None: return super().serve(t0, deadline)
        t = t0; pairs = 0; att = 0; Pc = s.Pc
        while True:
            att += 1; lam = s.lam_true(t)
            d1, w1 = s.chain(t); pw1 = s._w.copy(); pairs += s.L
            d2, w2 = s.chain(d1); pw2 = s._w.copy(); pairs += s.L; hold = d2 - d1; tdone = d2
            if tdone > deadline: return deadline, "miss", None, pairs
            ld = s.lam_draws_pop(tdone); deliver = False
            if ld is not None:
                Fs = ptm.delivered_F(ld, pw1, pw2, hold, Pc["e"], s.cT1, s.cT2)
                pbad = ((Fs < s.tau).sum() + 0.5) / (v16.M + 1)
                thr = s.choose_t(); deliver = pbad <= thr
                s.pb[s.nb % v16.WIN] = pbad; s.nb += 1
                if tdone >= s.warm: s.ts.append(thr)
            if deliver:
                Ft = float(mx.delivered_F(np.clip(lam, 0, 1), pw1, pw2, hold, s.P["e"], s.mem))
                s.fm.append(v4.dej(v4.chainF(lam, s.P, s.L, w1 + hold), v4.chainF(lam, s.P, s.L, w2), s.P["e"]))
                return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


VARIANTS = v16.VARIANTS
SEEDS = (18981, 18982, 18983)   # fresh; cloud dev pilot used 19981-19983
G = 1e-5; NP = 64


def tasks():
    return [[v, c, i] for v in VARIANTS for c in CONFIGS for i in range(NP)]


def run_id(t):
    return hashlib.sha256("v20|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    var, cfg, idx = t
    mem, method, t1mult = CONFIGS[cfg]
    P, L, tau, ctrl, D, spread, k = VARIANTS[var]; Pc = dict(P, **ctrl)
    pseed = int(hashlib.sha256(f"v20path|{var}".encode()).hexdigest()[:8], 16)
    lam0, ph = v15.draw_paths_spread(P, L, NP, [SEEDS[0], pseed], spread)[idx]
    phase = ph * 0.02 / G
    seed = [int(hashlib.sha256(f"v20|{var}|{idx}".encode()).hexdigest()[:8], 16), SEEDS[1]]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunV20(P, L, True, G, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
               est="static", method=method, tau=tau, Pc=Pc, spread=spread, mem=mem, t1mult=t1mult)
    r.fm = []
    K, mult = v17.EBK[method]
    n_, k_ = v17.fleet_counts(P, L, K, spread, [SEEDS[2], pseed + idx], mult)
    pF, hw = v17.eb_prior_F(P, n_, k_); r.set_prior_F(pF)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    return dict(run=run_id(t), variant=var, L=L, tau=tau, config=cfg, mem=mem, method=method, t1mult=t1mult or 0.0, idx=idx,
                requests=len(o), delivered=len(x), qual=int((x.F >= tau).sum()), bad=int((x.F < tau).sum()))


if __name__ == "__main__":
    import json, sys
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
