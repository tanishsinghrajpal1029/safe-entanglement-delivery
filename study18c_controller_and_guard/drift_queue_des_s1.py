"""Study 18C S1: sensitivity re-check of C2 with REALISTIC overlapping calibration windows (pre-registered in README_S1.md).

Why (found in G1, ledger E67). Every single-path run from v16 to C2 and P1 drew FRESH window counts for each decision
(n ~ Poisson(rho R W), k ~ Binomial(n, (1 + r lambda_avg)/2) at every decision). Real consecutive decisions share almost all
of their 100-s window. Fresh draws are valid for the MEAN risk, but they remove the correlation between decisions on a path,
so the path-level clustering of bad deliveries, and hence the path-bootstrap upper bounds, may have been understated.

Change (ONLY the data model). Each link gets one pre-generated calibration stream for the whole run: Poisson event times
at rate rho R, each a parity bit with P(even) = (1 + r lambda_true(t_event))/2 (true drifting / faulted lambda at that time).
A decision at time t uses the events in (t - T, t]. The controller (C2 'm123'), paths, fleet samples, seeds and everything
else are C2's; the run stream differs only through the counts.  Design: C2 block A, first 128 of C2's 256 paths per group
(paired with C2 runs idx < 128), 6,144 tasks.
"""
import hashlib, json, sys
import numpy as np
import drift_queue_des_v16 as v16
import drift_queue_des_v21 as v21
import drift_queue_des_c1 as c1
import drift_queue_des_c2 as c2

NPS = 128


class RunV21S(v21.RunV21):
    def _stream(s):
        if getattr(s, "_st", None) is not None: return s._st
        srng = np.random.default_rng(int(s.rng.integers(2 ** 62))); r = (1 - 2 * s.P["q"]) ** 2
        Hend = s.H + s.warm + 60.0; rate = s.rho * s.P["R"]; st = []
        for i in range(s.L):
            n = srng.poisson(rate * Hend); te = np.sort(srng.uniform(0, Hend, n))
            lam = s.lam0[i] - s.g * ((te + s.phase) % s.Tre)
            if getattr(s, "ts_f", None) is not None and i == s.j_f: lam = lam - s.dl_f * (te >= s.ts_f)
            bit = srng.uniform(size=n) < (1 + r * np.clip(lam, 0, 1)) / 2
            st.append((te, np.concatenate([[0], np.cumsum(bit)])))
        s._st = st; return st

    def _counts(s, i, a, t):
        te, ck = s._stream()[i]; i0 = np.searchsorted(te, a, "right"); i1 = np.searchsorted(te, t, "right")
        return int(i1 - i0), int(ck[i1] - ck[i0])

    def lam_draws_pop(s, t):
        L = s.L; r = (1 - 2 * s.P["q"]) ** 2; rng = s.rng; a = max(0.0, t - s.T)
        if t - a <= 0: return None
        NPRI, UG, M = v16.NPRI, v16.UG, v16.M
        pe = (1 + r * np.clip(s.pri + s.window_shift(t - a)[:, None], 0, 1)) / 2; lp, lq = np.log(pe), np.log1p(-pe)
        LW = np.empty((L, len(UG), NPRI))
        for i in range(L):
            n, k = s._counts(i, a, t)
            if n < 5: return None
            LW[i] = k * lp + (n - k) * lq
        LW -= LW.max(axis=(1, 2), keepdims=True); W = np.exp(LW)
        Z = W.sum(2); lz = np.log(Z).sum(0); pu = np.exp(lz - lz.max()); pu /= pu.sum()
        js = rng.choice(len(UG), M, p=pu); C = np.cumsum(W, axis=2); C /= C[:, :, -1:]
        C += np.arange(len(UG))[None, :, None]; out = np.empty((M, L))
        for i in range(L):
            idx = np.searchsorted(C[i].ravel(), js + rng.random(M)) - js * NPRI
            out[:, i] = s.pri[js, np.minimum(idx, NPRI - 1)]
        return out


def tasks():
    return [["A", c, g, m, "normal", i] for c in c1.CELLS for g in (1e-9, 1e-5) for m in c1.MEMS for i in range(NPS)]


def run_id(t):
    return hashlib.sha256("s1|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    orig = v21.RunV21; v21.RunV21 = RunV21S
    try:
        r = v21.run_one(t, c2.VARIANT, npaths=c2.NP, seeds=c2.SEEDS)
    finally:
        v21.RunV21 = orig
    r["run"] = run_id(t); return r


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
