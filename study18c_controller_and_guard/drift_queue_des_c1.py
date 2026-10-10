"""Study 18C C1: confirmatory run of the FROZEN final controller (pre-registered in README_C1.md; fresh seeds).

Final controller (frozen; nothing tuned after this file's hash is recorded):
  * static 100 s parity window; exact posterior over current link lambda under a fleet prior (v16 machinery);
  * fleet prior estimated by hierarchical empirical Bayes from 128 other fleet paths x 1 window of parity counts
    (v17 eb128), assuming a Normal fleet law and drift amplitude 0.02;
  * per-draw fidelity from the T1/T2-aware Pauli-transfer model (ptm_model; v20) with the hardware's T1, T2;
  * window-threshold (local-fdr) rule, delta = 1%, >= 20 supporting attempts.
Truth: T1/T2 density-matrix model (ptm_model, identical to the NetSquid-validated memory_t1t2_exact to 6e-16; E48).
Blocks:
  A  core      : 8 hardware cells x g {0, 1e-5} x memory {deph, t1eq, ad} x Normal fleet          (256 paths)
  B  fleet law : 8 cells x g 1e-5 x deph x fleet {t3, mixlow, mixhigh} (eval + fleet paths both)  (128 paths)
  C  switch    : 8 cells x g 1e-5 x deph; at a uniform random time in the scored horizon one random link's
                 F0 drops by 2 population sd (unannounced fault); exploratory                     (128 paths)
Each task also runs a same-seed ORACLE (delivers iff the true pair fidelity >= tau) for the fraction-of-oracle cost.
"""
import hashlib
import numpy as np, pandas as pd
import drift_queue_des as v4
import drift_queue_des_v9 as v9
import drift_queue_des_v15 as v15
import drift_queue_des_v16 as v16
import drift_queue_des_v17 as v17
import drift_queue_des_v18 as v18
import drift_queue_des_v19 as v19
import drift_queue_des_v20 as v20
import memory_t1t2_exact as mx
import ptm_model as ptm

CELLS = {"nv_tau080": v15.VARIANTS["nv_tau080"], "ion2020_tau090": v16.VARIANTS["ion2020_tau090"],
         "ionproj_tau090": v16.VARIANTS["ionproj_tau090"], "tau085_ion2020": v15.VARIANTS["tau085_ion2020"],
         "tau085_ionproj": v15.VARIANTS["tau085_ionproj"], "tau095_ionproj1": v15.VARIANTS["tau095_ionproj1"],
         "tau095_ionfut3": v15.VARIANTS["tau095_ionfut3"], "siv_tau080_L1": v15.VARIANTS["siv_tau080_L1"]}
MEMS = v19.MEMS                                   # T1 in units of T2: deph inf, t1eq 1, ad 0.5
SWITCH_SD = 2.0


class FaultMixin:
    """Optional unannounced fault: from time ts, link j's lambda drops by dl (affects truth and calibration data)."""
    def set_fault(s, ts, j, dl): s.ts_f, s.j_f, s.dl_f = ts, j, dl

    def _fault(s, t):
        d = np.zeros(s.L)
        if getattr(s, "ts_f", None) is not None and t >= s.ts_f: d[s.j_f] = s.dl_f
        return d

    def lam_true(s, t): return super().lam_true(t) - s._fault(t)

    def lam_avg(s, a, b):
        base = super().lam_avg(a, b)
        if getattr(s, "ts_f", None) is None or b <= a or b <= s.ts_f: return base
        frac = (b - max(a, s.ts_f)) / (b - a); d = np.zeros(s.L); d[s.j_f] = s.dl_f * frac
        return base - d


class RunC1(FaultMixin, v20.RunV20):
    def serve(s, t0, deadline):
        """v20 T1-aware serve; truth via ptm_model (identical to the exact model to 6e-16, faster)."""
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
                Ft = float(ptm.delivered_F(np.clip(lam, 0, 1)[None, :], pw1, pw2, hold, s.P["e"], s.mem[1], s.mem[2])[0])
                return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


class OracleC1(FaultMixin, v4.Run):
    """Delivers iff the TRUE (T1/T2) fidelity of the produced pair >= tau."""
    def __init__(s, *a, tau=0.9, mem=("t1t2", np.inf, 1.0), **k):
        super().__init__(*a, **k); s.tau = tau; s.mem = mem

    def chain(s, t):
        tt = s.rng.exponential(1 / s.Ruser, s.L); s._w = tt.max() - tt
        return t + tt.max(), float(s._w.sum())

    def serve(s, t0, deadline):
        t = t0; pairs = 0; att = 0
        while True:
            att += 1; lam = np.clip(s.lam_true(t), 0, 1)
            d1, _ = s.chain(t); pw1 = s._w.copy(); pairs += s.L
            d2, _ = s.chain(d1); pw2 = s._w.copy(); pairs += s.L; hold = d2 - d1; tdone = d2
            if tdone > deadline: return deadline, "miss", None, pairs
            Ft = float(ptm.delivered_F(lam[None, :], pw1, pw2, hold, s.P["e"], s.mem[1], s.mem[2])[0])
            if Ft >= s.tau: return tdone, "deliver", Ft, pairs
            if att >= s.budget: return tdone, "budget", None, pairs
            t = tdone


SEEDS = (18991, 18992, 18993, 18994)   # eval paths / run streams / fleet samples / faults (fresh; dev pilot used 19991-19994)
NA, NB, NC = 256, 128, 128


def tasks():
    T = [["A", c, g, m, "normal", i] for c in CELLS for g in (1e-9, 1e-5) for m in MEMS for i in range(NA)]
    T += [["B", c, 1e-5, "deph", law, i] for c in CELLS for law in ("t3", "mixlow", "mixhigh") for i in range(NB)]
    T += [["C", c, 1e-5, "deph", "normal", i] for c in CELLS for i in range(NC)]
    return T


def run_id(t):
    return hashlib.sha256("c1|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    blk, cell, g, mem, law, idx = t
    P, L, tau, ctrl, D, spread, k = CELLS[cell]; Pc = dict(P, **ctrl); npth = {"A": NA, "B": NB, "C": NC}[blk]
    pseed = int(hashlib.sha256(f"c1path|{blk}|{cell}|{law}".encode()).hexdigest()[:8], 16)
    lam0, ph = v18.draw_paths_law(P, L, npth, [SEEDS[0], pseed], law, spread)[idx]
    phase = ph * 0.02 / g
    seed = [int(hashlib.sha256(f"c1|{blk}|{cell}|{law}|{g}|{idx}".encode()).hexdigest()[:8], 16), SEEDS[1]]
    mu = v4.service_mu(P, L, True, lam0, D)
    r = RunC1(P, L, True, g, v9.LOAD, "fixed", v9.RHO, v9.T, 0.0, D, v9.H, seed, mu=mu, lam0=lam0, phase=phase,
              est="static", method="eb128t1", tau=tau, Pc=Pc, spread=spread, mem=mem, t1mult=1.0)
    orc = OracleC1(P, L, True, g, v9.LOAD, "none", 0.0, 1.0, 0.0, D, v9.H, seed, oracle=True, mu=mu, lam0=lam0, phase=phase,
                   tau=tau, mem=r.mem)
    fault = None
    if blk == "C":
        fr = np.random.default_rng([SEEDS[3], pseed, idx]); ts = r.warm + fr.uniform(0, r.H); j = int(fr.integers(0, L))
        dl = float(min(lam0[j], 4 / 3 * SWITCH_SD * (1 - P["F0"]) * 0.2 * spread)); fault = (ts, j, dl)
        r.set_fault(*fault); orc.set_fault(*fault)
    r.fm = []
    n_, k_ = v18.fleet_counts_law(P, L, 128, spread, [SEEDS[2], pseed + idx], 1, law)
    pF, hw = v17.eb_prior_F(P, n_, k_); r.set_prior_F(pF)
    o = pd.DataFrame(r.go(), columns="t res F pairs latency".split()); x = o[o.res == "deliver"]
    oo = pd.DataFrame(orc.go(), columns="t res F pairs latency".split()); oq = int((oo.res == "deliver").sum())
    post = x[x.t >= fault[0]] if fault else x.iloc[0:0]
    return dict(run=run_id(t), block=blk, cell=cell, L=L, tau=tau, g=g, mem=mem, law=law, idx=idx, requests=len(o),
                delivered=len(x), qual=int((x.F >= tau).sum()), bad=int((x.F < tau).sum()), oracle_qual=oq,
                post_fault_delivered=len(post), post_fault_bad=int((post.F < tau).sum()),
                m_hat=float(hw.sum(1) @ v17.MG), abstain=float(np.mean(np.array(r.ts) < 0)) if r.ts else float("nan"))


if __name__ == "__main__":
    import json, sys
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
