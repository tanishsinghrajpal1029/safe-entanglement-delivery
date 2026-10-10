#!/usr/bin/env python3
"""Study 18C, Gate 1: NetSquid check of the NumPy surrogate used in the drift-frontier analysis.

Self-contained (imports no project code). Uses NetSquid's density-matrix formalism to simulate:
  A) L-link swap chains: Werner links (depolarize one qubit with p = 1 - lambda), depolarizing memory storage
     (p = 1 - exp(-t/T2) per stored qubit), BSM with depolarization e on both measured qubits, Pauli
     corrections. Compared with the closed form lambda_path = prod(lambda) * (1-e)^(2(L-1)) * exp(-2*sum(t)/T2).
  B) One DEJMPS round on two Werner pairs, with depolarization e on all four qubits after the bilateral
     CNOTs. Compared with (i) an exact NumPy 4-qubit circuit (independent implementation) and (ii) the
     drift-study surrogate (1-e)*F' + e/4 (expected to be optimistic; see check_surrogate_numpy.py).

Writes logs/netsquid_surrogate_check.json (refuses to overwrite) and prints a summary.
    python3 netsquid_surrogate_check.py --seed 18401
"""
from __future__ import annotations

import argparse
import itertools
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
OUT = HERE / "logs" / "netsquid_surrogate_check.json"


# ---------------------------------------------------------------- exact NumPy references
I2 = np.eye(2); X = np.array([[0, 1], [1, 0]]); Yp = np.array([[0, -1j], [1j, 0]]); Zp = np.diag([1, -1])
PHI = np.outer(np.array([1, 0, 0, 1]) / 2 ** .5, np.array([1, 0, 0, 1]) / 2 ** .5)


def kron(*m):
    o = m[0]
    for x in m[1:]:
        o = np.kron(o, x)
    return o


def op(U, q, n=4):
    return kron(*[U if i == q else I2 for i in range(n)])


def cnot(c, t, n=4):
    P0, P1 = np.diag([1, 0]), np.diag([0, 1])
    a, b = [I2] * n, [I2] * n
    a[c], b[c], b[t] = P0, P1, X
    return kron(*a) + kron(*b)


def depol(rho, q, e, n=4):
    return (1 - e) * rho + e / 4 * sum(op(P, q, n) @ rho @ op(P, q, n).conj().T for P in (I2, X, Yp, Zp))


def Rx(th):
    return np.cos(th / 2) * I2 - 1j * np.sin(th / 2) * X


def werner(F):
    return F * PHI + (1 - F) / 3 * (np.eye(4) - PHI)


def dejmps_numpy(F1, F2, e):
    rho = np.kron(werner(F1), werner(F2))                     # order A1 B1 A2 B2
    U = op(Rx(np.pi / 2), 0) @ op(Rx(-np.pi / 2), 1) @ op(Rx(np.pi / 2), 2) @ op(Rx(-np.pi / 2), 3)
    rho = U @ rho @ U.conj().T
    C = cnot(0, 2) @ cnot(1, 3)
    rho = C @ rho @ C.conj().T
    for q in range(4):
        rho = depol(rho, q, e)
    keep = fsum = 0.0
    for m in (0, 1):
        P = op(np.diag([1 - m, m]), 2) @ op(np.diag([1 - m, m]), 3)
        r = (P @ rho @ P).reshape(2, 2, 2, 2, 2, 2, 2, 2)
        ab = np.einsum('abijcdij->abcd', r).reshape(4, 4)
        keep += float(np.real(np.trace(ab)))
        fsum += float(np.real(np.trace(PHI @ ab)))
    return fsum / keep, keep


def dejmps_surrogate(F1, F2, e):
    b1, b2 = (1 - F1) / 3, (1 - F2) / 3
    N = (F1 + b1) * (F2 + b2) + 4 * b1 * b2
    return (1 - e) * (F1 * F2 + b1 * b2) / N + e / 4, N


def chain_formula(lams, waits, T2, e):
    L = len(lams)
    lam = np.prod(lams) * (1 - e) ** (2 * (L - 1)) * np.exp(-2 * np.sum(waits) / T2)
    return (1 + 3 * lam) / 4


# ---------------------------------------------------------------- NetSquid implementations
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=18401)
    ap.add_argument("--trials", type=int, default=3000, help="NetSquid trials per DEJMPS case")
    a = ap.parse_args()
    if OUT.exists():
        sys.exit(f"{OUT} exists; refusing to overwrite (rename it or delete it yourself to rerun)")
    import netsquid as ns
    from netsquid.qubits import ketstates as ks
    from netsquid.qubits import operators as ops
    from netsquid.qubits import qubitapi as qapi
    ns.set_qstate_formalism(ns.QFormalism.DM)
    ns.set_random_state(seed=a.seed)
    rng = np.random.default_rng(a.seed)
    t0 = time.time()

    def bell_pair(lam):
        q = qapi.create_qubits(2)
        qapi.operate(q[0], ops.H)
        qapi.operate(q, ops.CNOT)
        qapi.depolarize(q[1], prob=1 - lam)                   # Werner with Pauli eigenvalue lam
        return q

    def store(q, t, T2):
        if t > 0:
            qapi.depolarize(q, prob=1 - np.exp(-t / T2))

    # ---- A) swap chains
    chain_rows = []
    for case in range(60):
        L = int(rng.integers(2, 5))
        F0 = rng.uniform(0.85, 0.995, L)
        lams = (4 * F0 - 1) / 3
        T2 = 1.0
        waits = rng.exponential(0.01, L)
        e = float(rng.choice([0.0, 0.003, 0.005, 0.01]))
        pairs = [bell_pair(l) for l in lams]
        for (qa, qb), t in zip(pairs, waits):
            store(qa, t, T2)
            store(qb, t, T2)
        left = pairs[0][0]
        right = pairs[0][1]
        for k in range(1, L):
            m1, m2 = right, pairs[k][0]
            for q in (m1, m2):
                if e:
                    qapi.depolarize(q, prob=e)
            qapi.operate([m1, m2], ops.CNOT)
            qapi.operate(m1, ops.H)
            b1, _ = qapi.measure(m1, observable=ops.Z)
            b2, _ = qapi.measure(m2, observable=ops.Z)
            far = pairs[k][1]
            if b2:
                qapi.operate(far, ops.X)
            if b1:
                qapi.operate(far, ops.Z)
            right = far
        f_ns = float(qapi.fidelity([left, right], ks.b00, squared=True))
        f_th = float(chain_formula(lams, waits, T2, e))
        chain_rows.append(dict(L=L, e=e, F_netsquid=f_ns, F_formula=f_th, abs_diff=abs(f_ns - f_th)))

    # ---- B) DEJMPS
    rot_a = ops.create_rotation_op(np.pi / 2, (1, 0, 0))
    rot_b = ops.create_rotation_op(-np.pi / 2, (1, 0, 0))
    dej_rows = []
    for F1, F2, e in itertools.product((0.85, 0.92, 0.99), (0.85, 0.95), (0.0, 0.005, 0.01)):
        succ = 0
        fsum = 0.0
        for _ in range(a.trials):
            p1 = bell_pair((4 * F1 - 1) / 3)
            p2 = bell_pair((4 * F2 - 1) / 3)
            A1, B1 = p1
            A2, B2 = p2
            for q in (A1, A2):
                qapi.operate(q, rot_a)
            for q in (B1, B2):
                qapi.operate(q, rot_b)
            qapi.operate([A1, A2], ops.CNOT)
            qapi.operate([B1, B2], ops.CNOT)
            if e:
                for q in (A1, B1, A2, B2):
                    qapi.depolarize(q, prob=e)
            ma, _ = qapi.measure(A2, observable=ops.Z)
            mb, _ = qapi.measure(B2, observable=ops.Z)
            if ma == mb:
                succ += 1
                fsum += float(qapi.fidelity([A1, B1], ks.b00, squared=True))
        p_ns = succ / a.trials
        f_ns = fsum / max(succ, 1)
        f_np, p_np = dejmps_numpy(F1, F2, e)
        f_sur, p_sur = dejmps_surrogate(F1, F2, e)
        se_f = 0.0  # conditional fidelity is deterministic per branch; MC noise only via branch mixing
        dej_rows.append(dict(F1=F1, F2=F2, e=e, trials=a.trials,
                             p_succ_netsquid=p_ns, p_succ_numpy=p_np, p_succ_se=float(np.sqrt(p_np * (1 - p_np) / a.trials)),
                             F_netsquid=f_ns, F_numpy_exact=f_np, F_surrogate=f_sur,
                             netsquid_minus_numpy=f_ns - f_np, netsquid_minus_surrogate=f_ns - f_sur))

    res = {
        "script": "18c_drift_frontier/netsquid_surrogate_check.py", "seed": a.seed,
        "netsquid_version": getattr(ns, "__version__", "unknown"), "python": sys.version.split()[0],
        "platform": platform.platform(), "elapsed_s": round(time.time() - t0, 1),
        "chain": {"cases": len(chain_rows), "max_abs_diff": max(r["abs_diff"] for r in chain_rows), "rows": chain_rows},
        "dejmps": dej_rows,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(f"A) swap chains: {len(chain_rows)} cases, max |F_netsquid - F_formula| = {res['chain']['max_abs_diff']:.2e}")
    print("B) DEJMPS (F1,F2,e): p_succ NS vs numpy (+-se) | F NS, F exact-numpy, F surrogate")
    for r in dej_rows:
        print(f"   ({r['F1']},{r['F2']},{r['e']}): p {r['p_succ_netsquid']:.4f} vs {r['p_succ_numpy']:.4f} (+-{r['p_succ_se']:.4f}) | "
              f"F {r['F_netsquid']:.5f}, {r['F_numpy_exact']:.5f}, {r['F_surrogate']:.5f}")
    print(f"wrote {OUT}  ({res['elapsed_s']} s)")


if __name__ == "__main__":
    main()
