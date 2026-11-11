"""Model-free, anytime-valid certificate of the average fidelity of KEPT entangled pairs (Theorem C1).

Protocol (per user): each delivered pair i is, AFTER delivery and with fresh randomness hidden from the network, tested with
probability p (T_i = 1) in a basis B_i uniform on {X, Y, Z}; a tested pair is measured on both sides and the error
E_i = 1 if the outcome pattern is the one that a perfect |Phi+> never gives (XX: outcomes differ; ZZ: differ; YY: agree).
Untested pairs are kept. For any two-qubit state, 1 - F(Phi+) = delta = (eX + eY + eZ)/2 with e_B = P(error | basis B),
so the mean error of a random-basis test is (2/3) delta.
Supermartingale: for lambda in (0, lam_max(p)) let k(lambda) solve f(1) = 1, where
    f(delta) = (1-p) e^{lambda delta} + p [1 - (2 delta / 3)(1 - e^{-1.5 lambda k})];
f is convex with f(0) = 1, so f(delta) <= 1 on [0, 1], hence prod_i exp(lambda [(1-T_i) delta_i - 1.5 k T_i E_i]) is a
nonnegative supermartingale whatever the (predictable) states are. A finite mixture over lambda is also one; Ville gives
    P( exists t: sum_g w_g exp(lambda_g (D_t - c_g Err_t)) >= 1/alpha ) <= alpha,   c_g = 1.5 k(lambda_g),
with D_t = sum of deficits of kept pairs up to t and Err_t = number of test errors. Inverting in D_t (monotone) gives an
upper bound D_ub(Err_t) valid simultaneously for all t, and the certificate  Fbar_kept(t) >= 1 - D_ub / K_t.
"""
import numpy as np
from scipy.optimize import brentq
from scipy.special import logsumexp


def lam_max(p, rmax=0.0):
    a = (2 / 3) * (1 - 2 * rmax)                    # guaranteed P(error | failed pair, random basis) under readout flips <= rmax
    return np.log((1 - p * (1 - a)) / (1 - p))


def kprime(lam, p, rmax=0.0):
    """k with (1-p) e^lam + p [1 - a (1 - e^{-1.5 lam k})] = 1, a = (2/3)(1 - 2 rmax)."""
    a = (2 / 3) * (1 - 2 * rmax)
    rhs = (1 - p * (1 - a) - (1 - p) * np.exp(lam)) / (p * a)
    assert 0 < rhs < 1, (lam, p, rhs)
    return -np.log(rhs) / (1.5 * lam)


class Certifier:
    def __init__(s, p, alpha, G=8, lo=1 / 16, rmax=0.0):
        s.p, s.alpha, s.rmax = p, alpha, rmax
        lm = lam_max(p, rmax); s.lams = lm * np.geomspace(lo, 0.98, G); s.w = np.full(G, 1 / G)        # grid chosen on synthetic Werner streams (G8 vs G4/G12/G16), before any study data
        s.c = np.array([1.5 * kprime(l, p, rmax) for l in s.lams]); s._cache = {}

    def d_ub(s, err):
        if err not in s._cache: s._cache[err] = s._d_ub(err)
        return s._cache[err]

    def _d_ub(s, err):
        """largest D with sum_g w_g exp(lam_g (D - c_g err)) < 1/alpha (monotone increasing in D)."""
        lw = np.log(s.w); target = np.log(1 / s.alpha)
        g = lambda D: logsumexp(lw + s.lams * (D - s.c * err)) - target
        if g(0.0) >= 0: return 0.0                                           # cannot happen for err >= 0 (checked below)
        hi = float(np.min(s.c * err + (target - lw) / s.lams))              # one term alone already reaches 1/alpha
        hi = hi * (1 + 1e-9) + 1e-9                                          # strictly past the root (G = 1 edge case)
        return brentq(g, 0.0, hi, xtol=1e-9)

    def lower(s, err, kept):
        return 1 - s.d_ub(err) / kept if kept > 0 else 0.0


def _test_err(rng, eB):
    """eB: (3,) error probabilities in X, Y, Z; returns (basis, error)."""
    b = rng.integers(3); return b, int(rng.random() < eB[b])


if __name__ == "__main__":
    import json, sys
    rng = np.random.default_rng(1)
    out = {}
    for p in (0.05, 0.1, 0.2):
        c = Certifier(p, 0.05)
        # tightness: Werner pairs of fidelity F, after K kept pairs
        for F in (0.8, 0.9, 0.95):
            res = []
            for K in (100, 1000, 10000):
                n = int(round(K * p / (1 - p))); errs = rng.binomial(n, (2 / 3) * (1 - F))
                res.append(round(c.lower(errs, K), 4))
            out[f"p{p}_F{F}"] = res
    print(json.dumps(out))
