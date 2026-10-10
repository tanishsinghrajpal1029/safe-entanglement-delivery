#!/usr/bin/env python3
"""A: NetSquid check of the exact T1/T2-memory model (memory_t1t2_exact.py) used to measure the controller's model bias.

Part 1 (deterministic): NetSquid's T1T2NoiseModel applied to a Werner pair for a grid of (T1, T2, t) versus the NumPy
        channel memory_t1t2_exact.t1t2 -> max |density-matrix element difference|.  Pre-set pass: < 1e-9.
Part 2 (sampled end-to-end): the full delivered-pair protocol in NetSquid (Werner links, T1/T2 storage of every waiting
        qubit, noisy BSM swaps with Pauli corrections, extra hold of chain 1, one DEJMPS round, postselection) for
        24 random cases (L 1-3; memories: dephasing-only, T1 = T2, T1 = T2/2) versus the exact branch-summed value.
        Pre-set pass: every |F_netsquid - F_exact| < 4 standard errors + 1e-4.
Run (Mac, NetSquid env), from this folder:   python3 netsquid_t1t2_check.py --seed 22201
Writes netsquid_t1t2_check.json (refuses to overwrite).
"""
import argparse, json, platform, sys, time
from pathlib import Path
import numpy as np
import memory_t1t2_exact as mx

OUT = Path(__file__).resolve().parent / "netsquid_t1t2_check.json"
S = 1e9   # NetSquid time unit is ns; model times are seconds


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=22201); ap.add_argument("--trials", type=int, default=1500)
    a = ap.parse_args()
    if OUT.exists(): sys.exit(f"{OUT} exists; refusing to overwrite")
    import netsquid as ns
    from netsquid.qubits import ketstates as ks, operators as ops, qubitapi as qapi
    from netsquid.components.models.qerrormodels import T1T2NoiseModel
    ns.set_qstate_formalism(ns.QFormalism.DM); ns.set_random_state(seed=a.seed); rng = np.random.default_rng(a.seed); t0 = time.time()

    def bell(lam):
        q = qapi.create_qubits(2); qapi.operate(q[0], ops.H); qapi.operate(q, ops.CNOT); qapi.depolarize(q[1], prob=1 - lam); return q

    import inspect
    try: constraint_src = inspect.getsource(T1T2NoiseModel.__init__)
    except Exception as ex: constraint_src = f"unavailable: {ex}"
    BIG_T1 = 1e6     # "T1 = infinity" is represented by T1 = 1e6 x T2 in BOTH NetSquid and NumPy (avoids T1 = 0 conventions)
    fin = lambda T1, T2: BIG_T1 * T2 if not np.isfinite(T1) else T1
    route = {}

    def model(T1, T2):
        """NetSquid T1T2NoiseModel if it accepts (T1, T2); otherwise None (NetSquid may enforce T2 <= T1)."""
        try: return T1T2NoiseModel(T1=fin(T1, T2) * S, T2=T2 * S)
        except ValueError as ex: route[(T1, T2)] = f"T1T2NoiseModel rejected: {ex}"; return None

    def store_prim(qs, t, T1, T2):
        """Fallback with NetSquid primitives: amplitude damping then dephasing, total coherence exp(-t/T2)."""
        g = 1 - np.exp(-t / fin(T1, T2)); coh = np.exp(-t / T2); pz = max(0.0, 0.5 * (1 - coh / np.sqrt(1 - g)))
        for q in qs:
            qapi.amplitude_dampen(q, gamma=g, prob=1)
            if pz > 0: qapi.dephase(q, prob=pz)

    def make_store(T1, T2):
        mdl = model(T1, T2)
        if mdl is not None: return lambda qs, t: (mdl.error_operation(qs, delta_time=t * S) if t > 0 else None), "T1T2NoiseModel"
        return lambda qs, t: (store_prim(qs, t, T1, T2) if t > 0 else None), "primitives(amplitude_dampen+dephase)"

    # ---- Part 1: channel
    ch = []
    for T1, T2, t, lam in [(np.inf, 1.0, 0.05, 0.9), (np.inf, 1.0, 0.3, 0.95), (1.0, 1.0, 0.05, 0.9), (1.0, 1.0, 0.3, 0.8),
                           (0.5, 1.0, 0.05, 0.9), (0.5, 1.0, 0.3, 0.95), (2.0, 1.0, 0.2, 0.85), (10.0, 1.0, 0.1, 0.9)]:
        st, how = make_store(T1, T2); q = bell(lam); st(q, t); dm_ns = np.array(qapi.reduced_dm(q))
        dm_np = mx.store(mx.werner_lam(lam), (0, 1), t, ("t1t2", fin(T1, T2), T2), 2)
        ch.append(dict(T1=str(T1), T2=T2, t=t, lam=lam, netsquid_route=how, max_abs_diff=float(np.max(np.abs(dm_ns - dm_np)))))
    ch_max = max(r["max_abs_diff"] for r in ch)

    # ---- Part 2: end-to-end protocol
    rot_a = ops.create_rotation_op(np.pi / 2, (1, 0, 0)); rot_b = ops.create_rotation_op(-np.pi / 2, (1, 0, 0))

    def swap_chain(lams, waits, e, st):
        pairs = [bell(l) for l in lams]
        for p, w in zip(pairs, waits): st(p, w)
        left, right = pairs[0]
        for k in range(1, len(pairs)):
            m1, m2 = right, pairs[k][0]
            if e:
                for q in (m1, m2): qapi.depolarize(q, prob=e)
            qapi.operate([m1, m2], ops.CNOT); qapi.operate(m1, ops.H)
            b1, _ = qapi.measure(m1, observable=ops.Z); b2, _ = qapi.measure(m2, observable=ops.Z)
            far = pairs[k][1]
            if b2: qapi.operate(far, ops.X)
            if b1: qapi.operate(far, ops.Z)
            right = far
        return left, right

    cases = []
    for c in range(24):
        L = int(rng.integers(1, 4)); memk = ["deph", "T1eqT2", "AD"][c % 3]; T2 = 1.0; T1 = {"deph": np.inf, "T1eqT2": 1.0, "AD": 0.5}[memk]
        e = float(rng.choice([0.003, 0.005])); lams = (4 * rng.uniform(0.88, 0.99, L) - 1) / 3
        t1 = rng.exponential(0.02, L); t2 = rng.exponential(0.02, L); w1 = t1.max() - t1; w2 = t2.max() - t2; hold = float(t2.max())
        st, how = make_store(T1, T2); fs = []
        for _ in range(a.trials):
            A1, B1 = swap_chain(lams, w1, e, st); st([A1, B1], hold)
            A2, B2 = swap_chain(lams, w2, e, st)
            for q in (A1, A2): qapi.operate(q, rot_a)
            for q in (B1, B2): qapi.operate(q, rot_b)
            qapi.operate([A1, A2], ops.CNOT); qapi.operate([B1, B2], ops.CNOT)
            for q in (A1, B1, A2, B2): qapi.depolarize(q, prob=e)
            ma, _ = qapi.measure(A2, observable=ops.Z); mb, _ = qapi.measure(B2, observable=ops.Z)
            if ma == mb: fs.append(float(qapi.fidelity([A1, B1], ks.b00, squared=True)))
        fs = np.array(fs); f_ns = float(fs.mean()); se = float(fs.std(ddof=1) / np.sqrt(len(fs))) if len(fs) > 1 else 1.0
        f_ex = float(mx.delivered_F(lams, w1, w2, hold, e, ("t1t2", fin(T1, T2), T2)))
        cases.append(dict(L=L, memory=memk, netsquid_route=how, e=e, successes=len(fs), F_netsquid=f_ns, se=se, F_exact=f_ex, diff=f_ns - f_ex,
                          pass_=bool(abs(f_ns - f_ex) < 4 * se + 1e-4)))
    res = dict(script="22_external_checks/netsquid_t1t2_check.py", seed=a.seed, trials=a.trials, netsquid_version=getattr(ns, "__version__", "?"),
               python=sys.version.split()[0], platform=platform.platform(), elapsed_s=round(time.time() - t0, 1),
               t1t2_init_source=constraint_src, rejected=dict((str(k), v) for k, v in route.items()),
               part1_channel=dict(cases=ch, max_abs_diff=ch_max, pass_=bool(ch_max < 1e-9)),
               part2_end_to_end=dict(cases=cases, all_pass=all(r["pass_"] for r in cases), max_abs_z=max(abs(r["diff"]) / max(r["se"], 1e-12) for r in cases)))
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(f"Part 1 channel: max |DM diff| = {ch_max:.2e} -> {'PASS' if ch_max < 1e-9 else 'FAIL'}")
    for r in ch: print(f"   T1={r['T1']:>4} t={r['t']}: {r['max_abs_diff']:.2e}   [{r['netsquid_route']}]")
    for k, v in route.items(): print(f"   note: (T1, T2) = {k}: {v}")
    print(f"Part 2 end-to-end: {sum(r['pass_'] for r in cases)}/{len(cases)} within 4 SE -> {'PASS' if res['part2_end_to_end']['all_pass'] else 'FAIL'}")
    for r in cases: print(f"   L={r['L']} {r['memory']:7s} F_ns={r['F_netsquid']:.5f} +-{r['se']:.5f}  exact={r['F_exact']:.5f}  diff={r['diff']:+.5f}")
    print(f"wrote {OUT} ({res['elapsed_s']} s)")


if __name__ == "__main__":
    main()
