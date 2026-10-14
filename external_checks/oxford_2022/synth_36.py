"""Study 36 pre-run: calibrate the locked tests on synthetic data before the real data are read.
(i) Anytime coverage of the kept-pair loss bound (O1) under stationary, drifting, step, persistent (AR) and adaptive
    sources; (ii) false over-dispersion rate (O2) and lag-1 persistence test (S3) under a stationary link, and their power
    under persistent noise. Usage: python3 synth_36.py > synth_36.txt   (numpy + scipy; seed 36)
"""
import numpy as np
from oxford_core import kept_loss_upper, kept_fidelity_lower, dispersion_test, lag1_perm, SQ2

RNG = np.random.default_rng(36)
P_TEST = 0.5


def q_of_v(v):                       # CHSH loss probability of a Werner pair with visibility v at optimal settings
    return (1 - v / SQ2) / 2


def run(vfun, n, adaptive=False):
    T = (RNG.random(n) < P_TEST).astype(np.int64)
    v = vfun(n)
    q = q_of_v(v)
    if adaptive:                     # adversary lowers quality after each test-round win (allowed: depends on the past)
        L = np.zeros(n, np.int64); qq = q.copy()
        u = RNG.random(n)
        for i in range(n):
            L[i] = T[i] * (u[i] < qq[i])
            if T[i] and not L[i] and i + 1 < n: qq[i + 1] = min(qq[i + 1] + 0.02, 0.5)
        q = qq
    else:
        L = T * (RNG.random(n) < q)
    QK, K = kept_loss_upper(T, L, P_TEST)
    true_QK = np.cumsum((1 - T) * q)
    viol = np.any(true_QK > QK)
    FL, _, _ = kept_fidelity_lower(T, L, P_TEST)
    Ftrue = SQ2 * (1 - 2 * true_QK[-1] / K[-1])
    return viol, Ftrue - FL[-1]


SC = {
    "stationary v=0.946": lambda n: np.full(n, 0.946),
    "drift 0.96 -> 0.90": lambda n: np.linspace(0.96, 0.90, n),
    "steps (3 random levels)": lambda n: np.repeat(RNG.uniform(0.88, 0.97, 3), int(np.ceil(n / 3)))[:n],
    "persistent AR(0.999)": lambda n: np.clip(0.946 + 0.01 * np.cumsum(RNG.normal(0, 0.03, n)) * np.exp(-np.arange(n) * 0) / 30, 0.8, 1.0),
}
print("== O1 anytime coverage of the kept-pair bound (rate of ANY violation over the run; bar <= 0.05) and final F margin")
for name, f in SC.items():
    for n, reps in ((200_000, 400), (1_920_000, 20)):
        res = [run(f, n) for _ in range(reps)]
        print(f"   {name:24s} n={n:>9,d} reps={reps:4d}: violation rate {np.mean([r[0] for r in res]):.4f}; "
              f"mean margin (true bound - F_L at end) {np.mean([r[1] for r in res]):.4f}")
res = [run(SC["stationary v=0.946"], 20_000, adaptive=True) for _ in range(200)]
print(f"   {'adaptive adversary':24s} n=   20,000 reps= 200: violation rate {np.mean([r[0] for r in res]):.4f}; mean margin {np.mean([r[1] for r in res]):.4f}")

print("\n== O2 / S3 under a stationary link (96 chunks x 10,000 test rounds, q = 0.165): false-positive rates (bar ~0.05)")
fp_d = fp_a = 0; R = 1000
for _ in range(R):
    k = RNG.binomial(10000, 0.165, 96); n = np.full(96, 10000)
    fp_d += dispersion_test(k, n)["p"] < 0.05
    fp_a += lag1_perm(k / n, reps=499, seed=int(RNG.integers(1e9)))[1] < 0.05
print(f"   over-dispersion false-positive rate {fp_d / R:.3f}; persistence false-positive rate {fp_a / R:.3f}")
print("== power under persistent chunk-level noise (AR(1) rho = 0.9 on the loss rate)")
for rel in (0.01, 0.02, 0.04):
    pw_d = pw_a = 0; R = 300
    for _ in range(R):
        z = np.zeros(96); e = RNG.normal(0, 1, 96)
        for j in range(96): z[j] = (0.9 * z[j - 1] if j else 0) + np.sqrt(1 - 0.81) * e[j]
        q = np.clip(0.165 * (1 + rel * z), 0, 1); k = RNG.binomial(10000, q)
        pw_d += dispersion_test(k, np.full(96, 10000))["p"] < 0.05
        pw_a += lag1_perm(k / 10000, reps=499, seed=int(RNG.integers(1e9)))[1] < 0.05
    print(f"   relative sd {rel:.0%}: over-dispersion power {pw_d / R:.2f}; persistence power {pw_a / R:.2f}")
