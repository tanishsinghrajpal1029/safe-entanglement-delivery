"""Study 35 (Delft) core statistics: pure numpy/scipy, no I/O. Locked with PREREG_35.md.

Conventions
- Bases are named 'X', 'Y', 'Z' (both nodes measure the same basis).
- Outcomes are two-bit labels '00','01','10','11'; parity +1 for 00/11, -1 for 01/10.
- Target Bell states are given by correlator signs (s_X, s_Y, s_Z):
    Phi+ (+1,-1,+1)   Phi- (-1,+1,+1)   Psi+ (+1,+1,-1)   Psi- (-1,-1,-1)
- Fidelity with the target: F = (1 + sum_b s_b c_b)/4 = 1 - sum_b e_b/2, where c_b is the correlator in basis b and
  e_b = P(outcome parity != s_b) (Lemma F in the manuscript; exact for any two-qubit state).
"""
import re
import numpy as np
from scipy.stats import beta as _beta

BELL = {"Phi+": {"X": 1, "Y": -1, "Z": 1}, "Phi-": {"X": -1, "Y": 1, "Z": 1},
        "Psi+": {"X": 1, "Y": 1, "Z": -1}, "Psi-": {"X": -1, "Y": -1, "Z": -1}}
Z95 = 1.6448536269514722


def parse_bell(label):
    """Map a state label (e.g. '$\\Psi^+$', 'Psi-', 'Ψ−') to a key of BELL; None if not recognisable."""
    t = str(label).replace("−", "-").replace("–", "-")
    fam = "Psi" if re.search(r"psi|Ψ|ψ", t, re.I) else ("Phi" if re.search(r"phi|Φ|φ|ϕ", t, re.I) else None)
    sign = "+" if "+" in t else ("-" if "-" in t else None)
    return f"{fam}{sign}" if fam and sign else None


def parity(label):
    return 1 if label[0] == label[1] else -1


def correlator_from_p(p, outcome_labels):
    return float(sum(pi * parity(l) for pi, l in zip(p, outcome_labels)))


def errors_from_counts(N, outcome_labels, s):
    """Number of outcomes whose parity disagrees with target sign s, and the total."""
    k = int(sum(n for n, l in zip(N, outcome_labels) if parity(l) != s))
    return k, int(sum(N))


def cp_ub(k, n, a):
    """One-sided Clopper-Pearson upper bound on a binomial proportion at level a."""
    if n <= 0: return 1.0
    return 1.0 if k >= n else float(_beta.ppf(1 - a, k + 1, n - k))


def certificate(err_by_basis, alpha=0.05):
    """Fixed-sample, model-free lower bound on fidelity from per-basis error counts {b: (k, n)}.
    Bonferroni over the three bases (alpha/3 each), Clopper-Pearson per basis. Valid if, within each basis, the
    measured pairs are i.i.d. and the measurements are trusted (no readout correction)."""
    a = alpha / len(err_by_basis)
    e_hat = {b: k / n for b, (k, n) in err_by_basis.items()}
    e_ub = {b: cp_ub(k, n, a) for b, (k, n) in err_by_basis.items()}
    return dict(F_hat=1 - sum(e_hat.values()) / 2, F_lo=max(0.0, 1 - sum(e_ub.values()) / 2), e_hat=e_hat, e_ub=e_ub)


def fid_from_corr(c, s):
    """c, s: dicts basis -> correlator / sign."""
    return (1 + sum(s[b] * c[b] for b in ("X", "Y", "Z"))) / 4


def u_fid_from_corr(u):
    """Uncertainty of F from independent per-basis correlator uncertainties."""
    return float(np.sqrt(sum(u[b] ** 2 for b in ("X", "Y", "Z")))) / 4


def offset_test(F_model, F_data, u_data, u_model):
    """D2: Delta = F_model - F_data with u = sqrt(u_data^2 + u_model^2) (independence assumed, stated)."""
    d = F_model - F_data; u = float(np.hypot(u_data, u_model))
    bar = 2 * u + 0.02
    lb = d - Z95 * u
    # adequate = within the USTC bar AND no detected optimism (a model shown to be optimistic is never "adequate")
    return dict(delta=d, u=u, lb=lb, ub=d + Z95 * u, bar=bar, adequate=(abs(d) <= bar) and (lb <= 0), weak=bar > 0.06,
                optimism_detected=lb > 0)
