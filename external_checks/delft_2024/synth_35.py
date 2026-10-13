"""Study 35 pre-run: calibrate the locked tests on synthetic data BEFORE the real data are read.
Measures (i) the false-certification rate of D1 at the boundary F = 0.5, (ii) coverage of the D1 bound,
(iii) the false-'inadequate' and false-'optimism' rates of D2 when the model is exactly right, and
(iv) D2's power at true offsets 0.02-0.05, for per-basis sample sizes n in {200, 500, 1000, 3000}.
Usage: python3 synth_35.py > synth_35.txt     (numpy + scipy; seed 35)
"""
import numpy as np
from delft_core import certificate, offset_test, Z95

RNG = np.random.default_rng(35)
NS = (200, 500, 1000, 3000)
REPS = 10000
B = ("X", "Y", "Z")
S = {"X": 1, "Y": 1, "Z": -1}            # Psi+ target (the choice does not matter by symmetry)


def counts_err(c_true, n):
    """Per-basis error counts for a state with correlators c_true (relative to target signs S)."""
    out = {}
    for b in B:
        e = (1 - S[b] * c_true[b]) / 2          # P(parity != s_b)
        out[b] = (int(RNG.binomial(n, e)), n)
    return out


def corr_and_u(errs):
    c = {b: S[b] * (1 - 2 * k / n) for b, (k, n) in errs.items()}
    u = {b: float(np.sqrt(max(1 - c[b] ** 2, 1e-12) / n)) for b, (k, n) in errs.items()}
    return c, u


# signed correlators (s_b * c_b) at F = 0.5: equal split, dephasing-like, extreme
SPLITS_05 = {"equal": (1 / 3, 1 / 3, 1 / 3), "dephasing": (0.05, 0.05, 0.9), "extreme": (0.0, 0.0, 1.0)}

print("== D1 false certification at the boundary F = 0.5 (rate of F_lo > 0.5; must be <= 0.05)")
for name, sc in SPLITS_05.items():
    c_true = {b: S[b] * v for b, v in zip(B, sc)}
    row = []
    for n in NS:
        hits = sum(certificate(counts_err(c_true, n))["F_lo"] > 0.5 for _ in range(REPS))
        row.append(f"n={n}: {hits / REPS:.4f}")
    print(f"   {name:9s}", "  ".join(row))

print("\n== D1 coverage (rate of F_lo <= true F; must be >= 0.95) and mean margin F - F_lo")
for F in (0.55, 0.60, 0.70):
    v = (4 * F - 1) / 3
    c_true = {b: S[b] * v for b in B}
    row = []
    for n in NS:
        lo = np.array([certificate(counts_err(c_true, n))["F_lo"] for _ in range(REPS)])
        row.append(f"n={n}: cov {np.mean(lo <= F):.4f}, margin {np.mean(F - lo):.3f}")
    print(f"   F={F:.2f}", "  ".join(row))

print("\n== D2 with an exact model (true Delta = 0): rate of D2 FAIL (= false 'inadequate'; <= ~0.05), rate of 'optimism detected' (<= ~0.05), weak-test rate")
for n in NS:
    inad = opt = weak = 0
    for _ in range(REPS):
        F = RNG.uniform(0.52, 0.65); v = (4 * F - 1) / 3
        c_true = {b: S[b] * v for b in B}
        F_states, u_states = [], []
        for _s in range(2):                                # two heralded states, as in the data
            c, u = corr_and_u(counts_err(c_true, n))
            F_states.append((1 + sum(S[b] * c[b] for b in B)) / 4)
            u_states.append(np.sqrt(sum(u[b] ** 2 for b in B)) / 4)
        Fd = np.mean(F_states); ud = 0.5 * np.hypot(*u_states)
        r = offset_test(F, Fd, ud, 0.0)
        inad += not r["adequate"]; opt += r["optimism_detected"]; weak += r["weak"]
    print(f"   n={n}: inadequate {inad / REPS:.4f}; optimism detected {opt / REPS:.4f}; weak test {weak / REPS:.4f}")

print("\n== D2 power: rate of 'optimism detected' when the model is optimistic by Delta (F_true = F_model - Delta)")
for d in (0.02, 0.03, 0.05):
    row = []
    for n in NS:
        det = 0
        for _ in range(REPS // 4):
            Fm = 0.58; F = Fm - d; v = (4 * F - 1) / 3
            c_true = {b: S[b] * v for b in B}
            F_states, u_states = [], []
            for _s in range(2):
                c, u = corr_and_u(counts_err(c_true, n))
                F_states.append((1 + sum(S[b] * c[b] for b in B)) / 4)
                u_states.append(np.sqrt(sum(u[b] ** 2 for b in B)) / 4)
            r = offset_test(Fm, np.mean(F_states), 0.5 * np.hypot(*u_states), 0.0)
            det += r["optimism_detected"]
        row.append(f"n={n}: {det / (REPS // 4):.3f}")
    print(f"   Delta={d:.2f}", "  ".join(row))
