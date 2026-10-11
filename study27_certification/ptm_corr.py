"""Delivered-pair Pauli correlators <XX>, <YY>, <ZZ> (and F) in the same PTM model as ptm_model.delivered_F (Study 27).
For a tested pair the user measures both qubits in basis B in {X, Y, Z}; error probabilities against |Phi+>:
    eX = (1 - <XX>)/2, eY = (1 + <YY>)/2, eZ = (1 - <ZZ>)/2, and 1 - F = (eX + eY + eZ)/2 exactly."""
import numpy as np
import memory_t1t2_exact as mx
import ptm_model as ptm

_c = {}


def _consts(e):
    if e in _c: return _c[e]
    ptm._consts(e); mx._consts(); SIG = ptm.SIG; E = [s / 4 for s in SIG]
    ops = [np.kron(mx.X, mx.X), np.kron(mx.Y, mx.Y), np.kron(mx.Z, mx.Z)]
    O = np.zeros((3, 16, 16))
    for j in range(16):
        for k in range(16):
            rho = np.kron(E[j], E[k]); rho = mx._U_DEJ @ rho @ mx._U_DEJ.conj().T
            for q in range(4): rho = mx.depol(rho, q, e, 4)
            for P in mx._PROJ_DEJ:
                ab = np.einsum("abijcdij->abcd", (P @ rho @ P).reshape(2, 2, 2, 2, 2, 2, 2, 2)).reshape(4, 4)
                for m in range(3): O[m, j, k] += np.real(np.trace(ops[m] @ ab))
    _c[e] = O; return O


def delivered_corr(lams, w1, w2, hold, e, T1, T2):
    """(M,3) correlators <XX>,<YY>,<ZZ> of the delivered pair, and (M,) fidelity, for link lambdas lams (M, L)."""
    nzk = ptm._consts(e)[5]; O = _consts(e)
    s1 = ptm.store2(ptm.chain(lams, w1, e, T1, T2), hold, T1, T2); s2 = ptm.chain(lams, w2, e, T1, T2)
    norm = sum(v * s1[:, j] * s2[:, k] for j, k, v in nzk)
    C = np.einsum("mjk,nj,nk->nm", O, s1, s2) / norm[:, None]
    F = ptm.delivered_F(lams, w1, w2, hold, e, T1, T2)
    return C, F


def errs(C):
    return np.stack([(1 - C[:, 0]) / 2, (1 + C[:, 1]) / 2, (1 - C[:, 2]) / 2], 1)


if __name__ == "__main__":
    rng = np.random.default_rng(3); worst = 0
    for L in (1, 2, 3):
        for e in (0.003, 0.01):
            lams = (4 * rng.uniform(0.8, 0.99, (5, L)) - 1) / 3; w1 = rng.exponential(0.02, L); w2 = rng.exponential(0.02, L)
            C, F = delivered_corr(lams, w1, w2, rng.exponential(0.03), e, np.inf, 1.0)
            eb = errs(C); worst = max(worst, float(np.max(np.abs((1 - eb.sum(1) / 2) - F))))
            assert np.all((eb >= -1e-12) & (eb <= 1 + 1e-12))
    print("max |1 - (eX+eY+eZ)/2 - F| =", worst)
