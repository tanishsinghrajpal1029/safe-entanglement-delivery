"""Fast, vectorised T1/T2-aware fidelity model for the controller (v20), in the Pauli-transfer (PTM) representation.

A two-qubit state is rho = (1/4) sum_ab c_ab sigma_a (x) sigma_b. Memory storage of both qubits for time t is
c -> (R(t) (x) R(t)) c with the single-qubit amplitude-damping + dephasing PTM
    R = [[1,0,0,0],[0,coh,0,0],[0,0,coh,0],[gam,0,0,1-gam]],  gam = 1 - exp(-t/T1), coh = exp(-t/T2).
The noisy entanglement swap is a fixed bilinear map B[i,j,k]; one DEJMPS round gives bilinear forms for the
(unnormalised) Phi+ fidelity Of and the success probability Ok. B, Of, Ok are computed once per gate-noise e from the
NetSquid-validated exact model (memory_t1t2_exact). Every Werner link state is affine in lambda, so posterior draws
(M, L) propagate as (M, 16) arrays. Validated against memory_t1t2_exact.delivered_F (see __main__).
"""
import numpy as np
import memory_t1t2_exact as mx

PAULI = [mx.I2, mx.X, mx.Y, mx.Z]
SIG = [np.kron(a, b) for a in PAULI for b in PAULI]                 # index 4a + b
C_PHI = np.array([np.real(np.trace(mx.PHI @ s)) for s in SIG]); C_I = np.zeros(16); C_I[0] = 1.0
_cache = {}


def _consts(e):
    if e in _cache: return _cache[e]
    E = [s / 4 for s in SIG]
    B = np.zeros((16, 16, 16))
    for j in range(16):
        for k in range(16):
            out = mx.swap(E[j], E[k], e); B[:, j, k] = [np.real(np.trace(s @ out)) for s in SIG]
    mx._consts(); Of = np.zeros((16, 16)); Ok = np.zeros((16, 16))
    for j in range(16):
        for k in range(16):
            rho = np.kron(E[j], E[k]); rho = mx._U_DEJ @ rho @ mx._U_DEJ.conj().T
            for q in range(4): rho = mx.depol(rho, q, e, 4)
            for P in mx._PROJ_DEJ:
                ab = np.einsum("abijcdij->abcd", (P @ rho @ P).reshape(2, 2, 2, 2, 2, 2, 2, 2)).reshape(4, 4)
                Ok[j, k] += np.real(np.trace(ab)); Of[j, k] += np.real(np.trace(mx.PHI @ ab))
    nzB = [(i, j, k, B[i, j, k]) for i, j, k in zip(*np.nonzero(np.abs(B) > 1e-14))]
    nzf = [(j, k, Of[j, k]) for j, k in zip(*np.nonzero(np.abs(Of) > 1e-14))]
    nzk = [(j, k, Ok[j, k]) for j, k in zip(*np.nonzero(np.abs(Ok) > 1e-14))]
    _cache[e] = (B, Of, Ok, nzB, nzf, nzk); return _cache[e]


def R1(t, T1, T2):
    g = 0.0 if not np.isfinite(T1) else 1 - np.exp(-t / T1); c = np.exp(-t / T2)
    return np.array([[1, 0, 0, 0], [0, c, 0, 0], [0, 0, c, 0], [g, 0, 0, 1 - g]])


def store2(C, t, T1, T2):
    if t <= 0: return C
    R = R1(t, T1, T2); return C @ np.kron(R, R).T


def chain(lams, waits, e, T1, T2):
    """lams: (M, L) link lambdas; waits: (L,) per-link storage times. Returns (M, 16) chain-end Pauli coefficients."""
    nzB = _consts(e)[3]; st = None
    for i in range(lams.shape[1]):
        c = C_I[None, :] + lams[:, i:i + 1] * (C_PHI - C_I)[None, :]
        c = store2(c, waits[i], T1, T2)
        if st is None: st = c; continue
        out = np.zeros_like(st)
        for a, j, k, v in nzB: out[:, a] += v * st[:, j] * c[:, k]       # B has 16 non-zeros
        st = out
    return st


def delivered_F(lams, w1, w2, hold, e, T1, T2):
    """Vectorised delivered fidelity for posterior draws lams (M, L)."""
    nzf, nzk = _consts(e)[4:6]
    s1 = store2(chain(lams, w1, e, T1, T2), hold, T1, T2); s2 = chain(lams, w2, e, T1, T2)
    return sum(v * s1[:, j] * s2[:, k] for j, k, v in nzf) / sum(v * s1[:, j] * s2[:, k] for j, k, v in nzk)


if __name__ == "__main__":
    import time
    rng = np.random.default_rng(3); worst = {}
    for mem, T1 in (("deph", np.inf), ("t1eq", 1.0), ("ad", 0.5)):
        for L in (1, 2, 3):
            for e in (0.003, 0.005):
                for _ in range(6):
                    lams = (4 * rng.uniform(0.85, 0.99, (4, L)) - 1) / 3; w1 = rng.exponential(0.02, L); w2 = rng.exponential(0.02, L); h = rng.exponential(0.03)
                    f = delivered_F(lams, w1, w2, h, e, T1, 1.0)
                    ex = [mx.delivered_F(l, w1, w2, h, e, ("t1t2", T1, 1.0)) for l in lams]
                    worst[mem] = max(worst.get(mem, 0), float(np.max(np.abs(f - ex))))
    print("max |PTM - exact| by memory:", worst)
    lams = (4 * rng.uniform(0.9, 0.99, (256, 3)) - 1) / 3; t0 = time.time()
    for _ in range(200): delivered_F(lams, np.array([.01, 0, .02]), np.array([0, .01, .005]), .02, .003, 0.5, 1.0)
    print(f"ms per attempt (M=256, L=3): {(time.time() - t0) / 200 * 1000:.2f}")
