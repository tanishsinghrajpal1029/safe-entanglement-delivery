"""Study 30 core: the pieces of the provable closed loop (THEORY_30.md).

  cs_upper_mix   upper end of the same mixture confidence sequence that the guard already uses for its lower end
  OffsetCS       time-uniform UPPER confidence sequence on the model offset theta (Theorem 2), restartable
  PlugInCheck    model check with predictable plug-in bets (Prop. D): an e-process with no "pre-change debt"

Everything here is a pure function of past data (predictable), so the guarantees hold under adaptive routing and feedback.
"""
import numpy as np
from scipy.special import logsumexp

# ---------------------------------------------------------------- link confidence sequence: upper end
def cs_upper_mix(N, K, r, lam_g, logpri, level):
    """Upper end of the mixture confidence sequence for lambda (mirror of study23.cs_lower_mix).
    The set {lam : log mix_t - log lik_t(lam) < log(1/level)} contains the true lambda for all t with probability >= 1 - level
    (Ville); lik is concave in lam, so the set is an interval and its upper end is found by bisection from the MLE grid point."""
    N = np.asarray(N, float); K = np.asarray(K, float)
    def loglik(lam):
        p = np.clip((1 + r * np.clip(lam, 0, 1)) / 2, 1e-12, 1 - 1e-12)
        return K[..., None] * np.log(p) + (N - K)[..., None] * np.log1p(-p) if np.ndim(lam) == 2 else K * np.log(p) + (N - K) * np.log1p(-p)
    LG = loglik(np.broadcast_to(lam_g[None, :], (len(N), len(lam_g))))
    logmix = logsumexp(LG + logpri, axis=1); thr = np.log(1 / level)
    lo = np.clip(lam_g[np.argmax(LG, axis=1)], 0, 1).astype(float); hi = np.ones(len(N))
    top_in = logmix - loglik(hi) < thr
    for _ in range(45):
        mid = (lo + hi) / 2; inside = logmix - loglik(mid) < thr
        lo = np.where(inside, mid, lo); hi = np.where(inside, hi, mid)
    return np.where(N > 0, np.where(top_in, 1.0, hi), 1.0)          # hi: just outside the set (conservative by <= 2^-45)


# ---------------------------------------------------------------- offset confidence sequence (Theorem 2)
NUS = 0.01 * 2.0 ** np.arange(7)          # fixed bet grid 0.01 ... 0.64 (capped per pair at 0.9/amax); fixed before study data
A_MAX = 1.5                               # default bound on a_i = F_hi - 1 + 1.5 E_i when F_hi <= 1; callers pass a_hat = F_hi + 0.5


class OffsetCS:
    """Upper confidence sequence on theta in the offset class Delta_i = theta * phi_i (phi_i >= 0 known when pair i is tested).

    Each tested pair contributes a_i = F_hi_i - 1 + 1.5 E_i, with F_hi_i = min(1, model fidelity at the UPPER link bounds).
    On the event that every link's upper bound holds (prob >= 1 - alpha_hi), and with readout bias s >= 0 only increasing
    P(E=1) (THEORY_30, Lemma A), E[a_i | past] >= theta * phi_i.  For m <= theta the process
        K_t(m) = mean_j prod_i (1 + nu_j (m phi_i - a_i)),   nu_j in NUS (fixed, so K_t is nondecreasing in m)
    is a nonnegative supermartingale, so U_t = min_{s<=t} sup{m : K_s(m) < 1/level} >= theta for all t w.p. >= 1 - level.
    restart(): open a new window (at an alarm, or at t = 0 for the always-on arm); the k-th window is run at
    level0 * 6/(pi^2 k^2), so all windows together cost <= level0. No window is open until the first restart().
    If even m = 0 is excluded (K_t(0) >= 1/level: the tests look BETTER than the model at its upper link bounds), U = 0.
    """
    def __init__(s, level0=0.025, m_hi=1.0):
        s.level0, s.m_hi = level0, m_hi; s.k = 0; s.level = None; s.n = 0; s.U = m_hi; s._a = []; s._phi = []; s._cap = []

    def restart(s):
        s.k += 1; s.level = s.level0 * 6 / (np.pi ** 2 * s.k ** 2)
        s.n = 0; s.U = s.m_hi; s._a = []; s._phi = []; s._cap = []   # K(m) is not linear in m: the window's data are kept

    def add(s, a, phi, amax=A_MAX):
        """amax: a known (predictable) upper bound on a_i; the bets for this pair are capped at 0.9/amax so every factor
        1 + nu (m phi - a) stays >= 0.1 for all m >= 0 (and nu stays independent of m, so K_t(m) is nondecreasing in m)."""
        s._a.append(float(a)); s._phi.append(float(phi)); s._cap.append(0.9 / max(float(amax), 1e-9)); s.n += 1

    def _arrays(s):
        s._A = np.asarray(s._a); s._P = np.asarray(s._phi); s._NU = np.minimum(NUS[:, None], np.asarray(s._cap)[None, :])

    def _logK(s, m):
        f = 1 + s._NU * (m * s._P[None, :] - s._A[None, :])           # (J, n), all >= 0.1 for m >= 0
        return logsumexp(np.log(f).sum(1)) - np.log(len(NUS))

    def update(s):
        """recompute U from all tests in the current window (call at scheduled looks)."""
        if s.n == 0: return s.U
        thr = np.log(1 / s.level); s._arrays()
        if s._logK(s.m_hi) < thr: return s.U                        # nothing excluded below m_hi yet
        lo, hi = 0.0, s.m_hi
        if s._logK(0.0) >= thr: s.U = 0.0; return s.U                # theta >= 0 assumed; the whole range is excluded -> 0
        for _ in range(40):
            mid = (lo + hi) / 2
            if s._logK(mid) < thr: lo = mid
            else: hi = mid
        s.U = min(s.U, hi); return s.U


# ---------------------------------------------------------------- debt-free model check (Prop. D)
W_PI = 100; N_MIN_PI = 10; CAP_PI = 0.5


class PlugInCheck:
    """Same null and spending as mcheck.ModelCheck (H0: P(E_i=1 | past) <= q_i for every tested pair), but one e-process
    whose bet is a predictable plug-in (aGRAPA-style) estimate from the last W_PI tested pairs of the current segment:
        nu_i = clip( m / (v + m^2), 0, CAP_PI / q_i ),  m = mean(E - q), v = var(E - q)  over the window.
    Any predictable nu_i in [0, 1/q_i) keeps prod (1 + nu_i (E_i - q_i)) a nonnegative supermartingale under H0, so the
    false-alarm guarantee is Prop. MC's.  When the recent excess is negative the bet is 0 and wealth does not fall: a long
    stretch in which errors are BELOW the null bound (a conservative declared model) leaves no debt to repay."""
    def __init__(s, beta=0.05):
        s.beta = beta; s.k = 1; s.logm = 0.0; s.ntest = 0; s.alarms = []; s.win = []

    def level(s):
        return s.beta * 6 / (np.pi ** 2 * s.k ** 2)

    def reset(s):
        s.k += 1; s.logm = 0.0; s.win = []

    def update(s, E, q):
        q = float(min(max(q, 1e-6), 1 - 1e-6))
        if len(s.win) >= N_MIN_PI:
            x = np.asarray(s.win[-W_PI:]); m = x.mean(); v = x.var()
            nu = float(np.clip(m / max(v + m * m, 1e-9), 0.0, CAP_PI / q))
        else: nu = 0.0
        s.logm += np.log1p(nu * (E - q)); s.win.append(E - q); s.ntest += 1
        if len(s.win) > 4 * W_PI: s.win = s.win[-W_PI:]
        if s.logm >= np.log(1 / s.level()):
            s.alarms.append(s.ntest); s.reset(); return True
        return False


class HybridCheck:
    """Average of the fixed-bet mixture (Prop. MC) and the plug-in e-process (Prop. D): M = (M_mix + M_plug)/2.
    An average of e-processes for the same null is an e-process, so the guarantee is unchanged; the price is ln 2 nats of
    threshold on whichever component is winning. Robust default: fast after an abrupt change (mixture), and immune to a
    long conservative stretch (plug-in)."""
    def __init__(s, beta=0.05):
        from mcheck import LAMS
        s.beta = beta; s.k = 1; s.lams = np.asarray(LAMS, float); s.ntest = 0; s.alarms = []; s._zero()

    def _zero(s):
        s.logm = np.zeros(len(s.lams)); s.lp = 0.0; s.win = []

    def level(s):
        return s.beta * 6 / (np.pi ** 2 * s.k ** 2)

    def reset(s):
        s.k += 1; s._zero()

    def update(s, E, q):
        from mcheck import CAP
        q = float(min(max(q, 1e-6), 1 - 1e-6))
        s.logm += np.log1p(np.minimum(s.lams, CAP / q) * (E - q))
        if len(s.win) >= N_MIN_PI:
            x = np.asarray(s.win[-W_PI:]); m = x.mean(); v = x.var()
            nu = float(np.clip(m / max(v + m * m, 1e-9), 0.0, CAP_PI / q))
        else: nu = 0.0
        s.lp += np.log1p(nu * (E - q)); s.win.append(E - q); s.ntest += 1
        if len(s.win) > 4 * W_PI: s.win = s.win[-W_PI:]
        lm = np.logaddexp(logsumexp(s.logm) - np.log(len(s.lams)), s.lp) - np.log(2)
        if lm >= np.log(1 / s.level()):
            s.alarms.append(s.ntest); s.reset(); return True
        return False
