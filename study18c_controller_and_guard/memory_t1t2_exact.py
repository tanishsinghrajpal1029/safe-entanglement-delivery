"""Exact density-matrix model of the Study 18C delivered pair with T1/T2 (non-Werner) memories.

The controller's model (drift_queue_des.chainF + DEJMPS table) assumes DEPOLARIZING storage: every Pauli correlator of a
stored pair decays as exp(-2 t / T2).  Real memories (and NetSquid's T1T2NoiseModel) apply amplitude damping
(gamma = 1 - exp(-t/T1)) plus pure dephasing so that coherences decay as exp(-t/T2) (requires T2 <= 2 T1).
This module computes the TRUE conditional fidelity of the delivered pair exactly (branch-summed, no sampling):
  link i: Werner(lambda_i) -> both qubits stored w_i -> sequential entanglement swaps (BSM qubits depolarized e,
  Pauli frame corrections, outcome-averaged) -> chain-1 end qubits stored 'hold' -> one DEJMPS round (all four qubits
  depolarized e after the bilateral CNOTs; success-postselected) -> fidelity with Phi+.
storage='depol' reproduces the controller model exactly (self-check); storage='t1t2' is the physical memory.
"""
import numpy as np

I2 = np.eye(2); X = np.array([[0, 1], [1, 0]], complex); Y = np.array([[0, -1j], [1j, 0]]); Z = np.diag([1., -1.]).astype(complex)
H = np.array([[1, 1], [1, -1]], complex) / np.sqrt(2)
PHI = np.zeros((4, 4), complex); PHI[0, 0] = PHI[0, 3] = PHI[3, 0] = PHI[3, 3] = 0.5


def kron(*m):
    o = m[0]
    for x in m[1:]: o = np.kron(o, x)
    return o


def op(U, q, n):
    return kron(*[U if i == q else I2 for i in range(n)])


def cnot(c, t, n):
    P0, P1 = np.diag([1., 0]), np.diag([0., 1])
    a = [I2] * n; b = [I2] * n; a[c] = P0; b[c] = P1; b[t] = X
    return kron(*a) + kron(*b)


def werner_lam(lam):
    return lam * PHI + (1 - lam) * np.eye(4) / 4


def apply1(rho, K, q, n):
    """K rho K^dagger for a single-qubit operator K on qubit q of an n-qubit density matrix (tensor contraction)."""
    t = rho.reshape((2,) * (2 * n))
    t = np.moveaxis(np.tensordot(K, t, axes=([1], [q])), 0, q)
    t = np.moveaxis(np.tensordot(K.conj(), t, axes=([1], [n + q])), 0, n + q)
    return t.reshape(2 ** n, 2 ** n)


def depol(rho, q, p, n):
    if p <= 0: return rho
    return (1 - p) * rho + p / 4 * (rho + apply1(rho, X, q, n) + apply1(rho, Y, q, n) + apply1(rho, Z, q, n))


def t1t2(rho, q, t, T1, T2, n):
    """NetSquid-style T1T2 memory channel on qubit q for time t (amplitude damping + extra pure dephasing)."""
    if t <= 0: return rho
    g = 0.0 if not np.isfinite(T1) else 1 - np.exp(-t / T1)
    if g > 0:
        K0 = np.array([[1, 0], [0, np.sqrt(1 - g)]], complex); K1 = np.array([[0, np.sqrt(g)], [0, 0]], complex)
        rho = apply1(rho, K0, q, n) + apply1(rho, K1, q, n)
    coh_ad = np.sqrt(1 - g); coh = np.exp(-t / T2)
    if coh > coh_ad + 1e-12: raise ValueError("T2 must be <= 2 T1")
    pz = max(0.0, 0.5 * (1 - coh / coh_ad))
    if pz > 0: rho = (1 - pz) * rho + pz * apply1(rho, Z, q, n)
    return rho


def store(rho, qubits, t, mem, n):
    for q in qubits:
        if mem[0] == "depol": rho = depol(rho, q, 1 - np.exp(-t / mem[1]), n)
        else: rho = t1t2(rho, q, t, mem[1], mem[2], n)
    return rho


_U_BSM = None; _PROJ_SW = None; _U_DEJ = None; _PROJ_DEJ = None


def _consts():
    global _U_BSM, _PROJ_SW, _U_DEJ, _PROJ_DEJ
    if _U_BSM is not None: return
    n = 4; _U_BSM = op(H, 1, n) @ cnot(1, 2, n); _PROJ_SW = []
    for b1 in (0, 1):
        for b2 in (0, 1):
            P = op(np.diag([1. - b1, b1]), 1, n) @ op(np.diag([1. - b2, b2]), 2, n)
            C = op(X, 3, n) if b2 else np.eye(16); C = (op(Z, 3, n) if b1 else np.eye(16)) @ C
            _PROJ_SW.append(C @ P)
    Rx = lambda th: np.cos(th / 2) * I2 - 1j * np.sin(th / 2) * X
    _U_DEJ = cnot(0, 2, n) @ cnot(1, 3, n) @ op(Rx(np.pi / 2), 0, n) @ op(Rx(-np.pi / 2), 1, n) @ op(Rx(np.pi / 2), 2, n) @ op(Rx(-np.pi / 2), 3, n)
    _PROJ_DEJ = [op(np.diag([1. - m, m]), 2, n) @ op(np.diag([1. - m, m]), 3, n) for m in (0, 1)]


def swap(rhoA, rhoB, e):
    """rhoA on (a, m1), rhoB on (m2, c); BSM on m1, m2 with depolarization e; returns averaged corrected state on (a, c)."""
    _consts(); n = 4; rho = np.kron(rhoA, rhoB)
    rho = depol(depol(rho, 1, e, n), 2, e, n)
    rho = _U_BSM @ rho @ _U_BSM.conj().T
    out = np.zeros((4, 4), complex)
    for CP in _PROJ_SW: out += _trace_mid(CP @ rho @ CP.conj().T)
    return out


def _trace_mid(r):
    t = r.reshape(2, 2, 2, 2, 2, 2, 2, 2)            # (a m1 m2 c ; a' m1' m2' c')
    return np.einsum("aijcbijd->acbd", t).reshape(4, 4)


def dejmps(r1, r2, e):
    _consts(); n = 4; rho = np.kron(r1, r2)                    # A1 B1 A2 B2
    rho = _U_DEJ @ rho @ _U_DEJ.conj().T
    for q in range(4): rho = depol(rho, q, e, n)
    keep = fs = 0.0
    for P in _PROJ_DEJ:
        ab = np.einsum("abijcdij->abcd", (P @ rho @ P).reshape(2, 2, 2, 2, 2, 2, 2, 2)).reshape(4, 4)
        keep += np.real(np.trace(ab)); fs += np.real(np.trace(PHI @ ab))
    return fs / keep


def chain_state(lams, waits, e, mem):
    st = None
    for lam, w in zip(lams, waits):
        r = store(werner_lam(lam), (0, 1), w, mem, 2)
        st = r if st is None else swap(st, r, e)
    return st


def delivered_F(lams, w1, w2, hold, e, mem):
    """w1, w2: per-link waits of chain 1 and chain 2; hold: extra storage of chain 1's end pair."""
    s1 = store(chain_state(lams, w1, e, mem), (0, 1), hold, mem, 2)
    s2 = chain_state(lams, w2, e, mem)
    return dejmps(s1, s2, e)
