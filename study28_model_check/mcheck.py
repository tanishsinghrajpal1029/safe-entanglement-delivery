"""Model check (Proposition MC): an e-process on the user tests that are already run for certification.

Null hypothesis for each delivered pair i (the guard's own validity condition): F_true(i) >= Fg(i), where Fg(i) is the
fidelity the guard used to approve the pair (lower confidence bounds on the links, declared model, declared margin).
A tested pair is measured in a uniformly random basis of {X, Y, Z}; by Lemma F, P(error | past) = (2/3)(1 - F_true(i))
<= q_i := (2/3)(1 - Fg(i)) under the null.  For predictable bets lambda in [0, 1/q_i),
    M_t = sum_g w_g prod_{tested i <= t} (1 + lambda_{g,i} (E_i - q_i))
is a nonnegative supermartingale up to the first pair that violates the null, so (Ville)
    P(alarm, i.e. M_t >= 1/beta, before any delivered pair violates the null) <= beta.
On an alarm the network raises its declared margin by STEP and restarts the check at level beta * 6/(pi^2 k^2) for the
k-th restart (total false-alarm probability <= beta).  Raising the margin only makes the guard more conservative.
"""
import numpy as np

LAMS = np.array([0.25, 0.5, 1.0, 2.0, 4.0, 8.0])        # bet sizes (capped at CAP / q_i); fixed before any study data
CAP = 0.9


def null_bound(Fg, smax):
    """q for a tested pair approved at fidelity Fg, when each test outcome may be flipped by readout with probability <= smax
    (parity flip; smax = 2 r (1 - r) for independent per-qubit flips r): P(E=1) = s + (1-2s) e <= smax + (1-2 smax)(2/3)(1-Fg)
    for e <= (2/3)(1-Fg) <= 1/2 and s <= smax <= 1/2 (P is increasing in both)."""
    return smax + (1 - 2 * smax) * (2 / 3) * (1 - Fg)


class ModelCheck:
    def __init__(s, beta=0.05, lams=LAMS):
        s.beta, s.lams = beta, np.asarray(lams, float); s.w = np.full(len(s.lams), 1 / len(s.lams))
        s.k = 1; s.logm = np.zeros(len(s.lams)); s.ntest = 0; s.alarms = []

    def level(s):
        return s.beta * 6 / (np.pi ** 2 * s.k ** 2)

    def update(s, E, q):
        """one tested pair: error indicator E, null bound q on its error probability. Returns True on an alarm."""
        q = float(min(max(q, 1e-6), 1 - 1e-6)); lam = np.minimum(s.lams, CAP / q)
        s.logm += np.log1p(lam * (E - q)); s.ntest += 1
        m = float(np.sum(s.w * np.exp(np.minimum(s.logm, 700))))
        if m >= 1 / s.level():
            s.alarms.append(s.ntest); s.k += 1; s.logm[:] = 0.0
            return True
        return False


def growth(q, delta, lam):
    """expected log-increment of one bet when P(E=1) = q + delta (linear in P(E=1), so this is a lower bound whenever P >= q+delta)."""
    lam = min(lam, CAP / q); pi = q + delta
    return pi * np.log1p(lam * (1 - q)) + (1 - pi) * np.log1p(-lam * q)


def delay_bound(q, delta, beta):
    """Proposition MC (detection): if every tested pair has P(E=1|past) >= q + delta (q fixed), then
    E[tests to alarm] <= min_g [ln(1/(beta w_g)) + ln(1 + lam_g (1-q))] / growth_g   (Wald / optional stopping)."""
    best = np.inf
    for lam in LAMS:
        g = growth(q, delta, lam)
        if g > 0: best = min(best, (np.log(len(LAMS) / beta) + np.log1p(min(lam, CAP / q) * (1 - q))) / g)
    return best


def _vec_run(rng, R, T, qfun, dfun=None, beta=0.05):
    """vectorised first-alarm times for R independent runs of the FIRST check level (k = 1) over T tests.
    qfun(i, lastE) -> (R,) null bounds; dfun(i, q) -> (R,) excess (0 = errors exactly at the null bound)."""
    logm = np.zeros((R, len(LAMS))); alive = np.ones(R, bool); t_al = np.full(R, -1); lastE = np.zeros(R, int)
    thr = np.log(1 / (beta * 6 / np.pi ** 2)); lw = np.log(1 / len(LAMS))
    for i in range(T):
        q = np.clip(qfun(i, lastE), 1e-6, 1 - 1e-6); pi = q + (0 if dfun is None else dfun(i, q))
        E = (rng.random(R) < pi).astype(int); lastE = E
        lam = np.minimum(LAMS[None, :], CAP / q[:, None])
        logm += np.log1p(lam * (E - q)[:, None])
        lm = lw + logm; mx = lm.max(1); m = mx + np.log(np.exp(lm - mx[:, None]).sum(1))
        hit = alive & (m >= thr); t_al[hit] = i + 1; alive &= ~hit
        if not alive.any(): break
    return t_al


if __name__ == "__main__":
    import json
    rng = np.random.default_rng(28); out = {}; R = 20000; T = 10000
    for name, qf in (("q_const_0.05", lambda i, e: np.full(R, 0.05)), ("q_random", lambda i, e: rng.uniform(0.01, 0.13, R)),
                     ("q_adaptive", lambda i, e: np.where(e == 1, 0.02, 0.12))):
        t = _vec_run(rng, R, T, qf); r = float((t > 0).mean())
        out[f"false_alarm_{name}"] = dict(runs=R, tests=T, rate=r, ub95=round(r + 1.645 * np.sqrt(r * (1 - r) / R), 5),
                                          level=round(0.05 * 6 / np.pi ** 2, 5))
    # (c) restarts: errors exactly at the null bound, every alarm restarts at the next spending level; total alarms per run
    tot = 0; R2 = 3000
    for _ in range(R2):
        mc = ModelCheck(0.05); E = (rng.random(10000) < 0.05).astype(int)
        for e in E: mc.update(int(e), 0.05)
        tot += len(mc.alarms)
    out["restarts_total_alarms_per_run"] = dict(runs=R2, tests=10000, mean_alarms=tot / R2, bound=0.05)
    for q, d in ((0.05, 0.01), (0.05, 0.03), (0.04, 0.06), (0.067, 0.03)):
        t = _vec_run(rng, 4000, 60000, lambda i, e: np.full(4000, q), lambda i, qq: d)
        out[f"delay_q{q}_d{d}"] = dict(detected=float((t > 0).mean()), mean=float(t[t > 0].mean()), median=float(np.median(t[t > 0])),
                                       bound=round(delay_bound(q, d, 0.05 * 6 / np.pi ** 2), 1))
    print(json.dumps(out, indent=1))
