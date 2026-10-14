"""Study 36 (Oxford DIQKD characterisation run) core statistics. numpy/scipy only, no I/O. Locked with PREREG_36.md.

Rounds: one heralded Bell pair per round, in time order. Bob chooses the round type after the herald with private
randomness (QRNG): test (CHSH) round with probability p = 1/2 (y uniform in {0,1}), key round otherwise (y = 2, x = 0).

CHSH convention: E_xy = P(a = b) - P(a != b) on test rounds with settings (x, y); S = sum_xy s_xy E_xy for one sign pattern
s (exactly one s_xy = -1), possibly with an overall sign (Alice's outcome inversion). With uniform settings the CHSH game is
won with probability w = 1/2 + S/8; loss indicator L_i = 1 if s_xy (-1)^(a xor b) = -1.

Fidelity bound (trusted measurements at the nominal settings: Alice two orthogonal axes, Bob +-45 deg between them):
   F >= S / (2 sqrt 2) = sqrt2 (1 - 2 q),  q = 1 - w = loss probability,
to the maximally entangled state defined by the measurement frame; it holds for any two-qubit state (it is
F >= (<a0 b+> + <a1 b->)/2, from positivity of the Bell-diagonal weights).
Device-independent (self-testing) bound, Kaniewski PRL 117, 070402 (2016): F_ext >= 1/2 + (1/2)(S - b*)/(2 sqrt2 - b*),
b* = (16 + 14 sqrt2)/17; a fidelity after local isometries, reported as secondary.
"""
import numpy as np

SQ2 = np.sqrt(2.0)
BSTAR = (16 + 14 * SQ2) / 17


def chsh_variants(E):
    """E[x][y] correlators -> dict of the 8 candidate S values {(pattern, sign): S}; pattern = (x, y) carrying the minus."""
    out = {}
    for mx in (0, 1):
        for my in (0, 1):
            s = sum((-1 if (x, y) == (mx, my) else 1) * E[x][y] for x in (0, 1) for y in (0, 1))
            out[((mx, my), +1)] = s; out[((mx, my), -1)] = -s
    return out


def loss_indicator(x, y, a, b, pattern, sign):
    """Per test round: 1 if the CHSH game is lost under the convention (pattern, sign)."""
    sxy = np.where((x == pattern[0]) & (y == pattern[1]), -1, 1) * sign
    par = 1 - 2 * (a ^ b)                     # +1 same, -1 different
    return (sxy * par < 0).astype(np.int64)


def hoeffding_grid(alpha, G=20, tmin=1e3, tmax=4e6):
    tg = np.geomspace(tmin, tmax, G)
    lam = np.sqrt(8 * np.log(G / alpha) / tg)
    return lam, np.log(G / alpha)


def kept_loss_upper(T, L, p, alpha=0.05):
    """Anytime upper bound on Q_K(t) = sum over kept rounds i <= t of the conditional loss probability q_i.
    Martingale d_i = (1-p) T_i L_i - p (1-T_i) q_i (bounded range 1, mean 0 when the test choice is independent of the
    pair); Hoeffding supermartingales exp(-lam M_t - lam^2 t/8) on a grid of G values at level alpha/G each (union):
    with probability >= 1 - alpha, for all t:  p Q_K(t) <= (1-p) sum_{i<=t} T_i L_i + B_t,  B_t = min_g [ln(G/alpha)/lam_g + lam_g t/8].
    Returns arrays (Q_K upper bound, K_t) over t = 1..n."""
    t = np.arange(1, len(T) + 1, dtype=float)
    lam, lg = hoeffding_grid(alpha)
    B = np.min(lg / lam[:, None] + lam[:, None] * t[None, :] / 8, axis=0)
    TL = np.cumsum(T * L); K = np.cumsum(1 - T)
    return ((1 - p) * TL + B) / p, K


def kept_fidelity_lower(T, L, p, alpha=0.05):
    """Anytime lower bound on the kept pairs' average conditional fidelity (trusted-measurement bound), over time."""
    QK, K = kept_loss_upper(T, L, p, alpha)
    with np.errstate(divide="ignore", invalid="ignore"):
        qbar = np.where(K > 0, np.minimum(QK / np.maximum(K, 1), 1.0), 1.0)
    return np.clip(SQ2 * (1 - 2 * qbar), 0, 1), qbar, K


def di_fidelity_from_q(qbar):
    S = 8 * (0.5 - qbar)
    return np.clip(0.5 + 0.5 * (S - BSTAR) / (2 * SQ2 - BSTAR), 0, 1)


def dispersion_test(k, n):
    """Pearson chi-square for heterogeneity of binomial rates across blocks; returns X2, df, p (upper tail), ratio, excess."""
    from scipy.stats import chi2
    k = np.asarray(k, float); n = np.asarray(n, float); ph = k.sum() / n.sum()
    X2 = float(np.sum((k - n * ph) ** 2 / (n * ph * (1 - ph)))); df = len(k) - 1
    r = k / n; var_obs = np.var(r, ddof=1); var_bin = np.mean(ph * (1 - ph) / n)
    excess = float(np.sqrt(max(var_obs - var_bin, 0)) / ph)
    return dict(X2=X2, df=df, p=float(chi2.sf(X2, df)), ratio=X2 / df, excess_rel=excess, rate=float(ph))


def lag1_perm(rates, reps=10000, seed=36):
    r = np.asarray(rates, float); z = r - r.mean()
    ac = float(np.sum(z[1:] * z[:-1]) / np.sum(z * z))
    rng = np.random.default_rng(seed); cnt = 0
    for _ in range(reps):
        zz = rng.permutation(z); cnt += np.sum(zz[1:] * zz[:-1]) / np.sum(zz * zz) >= ac
    return ac, float((cnt + 1) / (reps + 1))
