"""Proposition LB (converse): resource floor for ANY valid model-free certifier, versus the anytime certificate C1.

Setting: each delivered pair is tested with probability p (fresh, hidden) in a uniformly random basis of {X, Y, Z}, or kept.
A certifier is a rule that maps the observed record (test/keep pattern, bases, outcomes) to a lower bound L on the fraction
of kept pairs that would pass a Phi+ test; it is valid if P(L > that fraction) <= alpha for every source.
Claim: let a rule certify L >= tau on EVERY all-pass record with K kept pairs (equivalently: with probability 1 on a perfect
source). Then validity forces
    max_{f > 1-tau}  ((1-p)/(1-p+p nu f))^K * P(Bin(K,f) > (1-tau)K)  <=  alpha,      nu = 2/3,
and K_LB(tau) (the first K for which this holds) is a floor for any such rule.
Proof: take the iid source A_f that emits Phi+ w.p. 1-f and some state orthogonal to Phi+ w.p. f. For any orthogonal state
e_X + e_Y + e_Z = 2 (Lemma F with F = 0), so a test in a uniformly random basis fails with probability exactly 2/3 (the
per-basis rates need not be equal). Kept and tested pairs are disjoint and independent, and the test/keep pattern does not
depend on the states. Summing over patterns with n tests before the K-th kept pair,
    P_f(all tests pass, B_K > (1-tau)K) = E[(1 - nu f)^{n_K}] * P(Bin(K, f) > (1-tau)K),
because each tested pair passes with probability 1 - f * E_b[e_b] = 1 - nu f whatever its basis. On this event the rule
certifies tau (the record is all-pass) while the kept failed fraction B_K/K exceeds 1 - tau: a violation. n_K is
negative binomial, E[x^{n_K}] = ((1-p)/(1-p x))^K. Taking the worst f gives the claim.
Remarks. (i) The hypothesis 'on every all-pass record' matters: a rule that certifies only on a fraction gamma of all-pass
records (those with the most tests) can partly escape the bound (k_lb_gamma, tau = 0.9, p = 0.1: gamma = 1 gives 330,
gamma = 0.9 gives 300, gamma = 0.5 gives 205; at gamma = 0.1 the bound is vacuous). Cert C1 at zero errors is deterministic, so the comparison is fair.
(ii) For iid sources the bound is tight: 'after exactly K kept pairs, output tau if every test passed' is valid against all
iid sources (product states with failed-label probability f give the same expression) exactly when the condition holds. So the
factor K_C1/K_LB of about 2 is the price of validity at all times and against adaptive sources, not slack in the converse.
(iii) If the certificate may be issued at any time before the (K+1)-th kept pair, the exponent K becomes K+1 (minor).
(iv) Any test strategy whose rejection probability for every orthogonal state is at least nu gives the same bound with that nu;
the best local strategy for a Bell state has nu = 2/3 (Pallister et al. 2018), so the bound holds for every local test scheme;
nu = 1 (a Bell measurement) is shown for reference.
"""
import json, sys
import numpy as np
from scipy.stats import binom
sys.path.insert(0, "/home/claude/s27")
from cert import Certifier

NU = 2 / 3


def lhs(K, p, tau, nu=NU, fs=None):
    fs = np.linspace(1 - tau, min(1.0, 4 * (1 - tau)), 400)[1:] if fs is None else fs
    a = ((1 - p) / (1 - p + p * nu * fs)) ** K
    b = binom.sf(np.floor((1 - tau) * K + 1e-9), K, fs)          # P(B > (1-tau) K)
    return float(np.max(a * b))


def k_lb(p, tau, alpha=0.05, nu=NU):
    """first K at which certifying tau is not ruled out (lhs is not monotone in K because of the binomial floor: scan)."""
    K = 1
    while lhs(K, p, tau, nu) > alpha: K += 1
    return K


def k_c1(p, tau, alpha=0.05):
    c = Certifier(p, alpha); K = 1
    while c.lower(0, K) < tau: K += 1
    return K


def k_simple(p, tau, alpha=0.05, nu=NU):
    return (1 - p) * np.log(1 / alpha) / (p * nu * (1 - tau))


def k_lb_gamma(p, tau, gamma, alpha=0.05, nu=NU, kmax=5000):
    """floor for rules that certify on a fraction gamma of all-pass records, choosing the records with the most tests
    (the best evasion): P(viol) >= sum over the top-gamma tail of n_K of P(n)(1 - nu f)^n * P(Bin(K,f) > (1-tau)K)."""
    from scipy.stats import nbinom
    fs = np.linspace(1 - tau, min(1.0, 4 * (1 - tau)), 200)[1:]
    for K in range(1, kmax):
        n = np.arange(0, int(20 * K * p / (1 - p) + 200)); pn = nbinom.pmf(n, K, 1 - p)
        cum = np.cumsum(pn[::-1])[::-1]                                                 # cum[i] = P(n_K >= n[i])
        i0 = int(np.max(np.nonzero(cum >= gamma - 1e-12)[0])); keep = n >= n[i0]       # smallest top tail with mass >= gamma
        a = (pn[keep][None, :] * (1 - nu * fs[:, None]) ** n[keep][None, :]).sum(1)
        b = binom.sf(np.floor((1 - tau) * K + 1e-9), K, fs)
        if np.max(a * b) <= alpha: return K
    return None


if __name__ == "__main__":
    out = {}
    for tau in (0.8, 0.9, 0.95):
        for p in (0.05, 0.1, 0.2):
            lb, c1 = k_lb(p, tau), k_c1(p, tau)
            out[f"tau{tau}_p{p}"] = dict(K_LB=lb, K_C1=c1, ratio=round(c1 / lb, 3), approx=round(k_simple(p, tau), 1),
                                         K_LB_bell_meas=k_lb(p, tau, nu=1.0))
    out["gamma_tau0.9_p0.1"] = {g: k_lb_gamma(0.1, 0.9, g) for g in (1.0, 0.9, 0.5)}
    print(json.dumps(out, indent=1))
