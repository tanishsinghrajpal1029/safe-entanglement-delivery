"""Study 24: link-quality PATTERNS on the 5 x 5 grid (extends corr_net.py, which is unchanged and still used by AI v1).

Every pattern gives z_l with mean 0 and variance 1 per link, so F0_l = F0_fleet + sd_F z_l keeps the fleet's mean and spread.
  field(ell, rho)  Gaussian spatial field over node coordinates, squared-exponential kernel, length scale ell (grid units);
                   link factor = mean of its two end nodes, standardised; z = sqrt(rho) f + sqrt(1 - rho) eps.  (Study 23 used
                   ell = 1.5, rho = 0.7.)  rho = 0 gives independent links.
  region(rho)      a straight cut (random orientation and position) splits the grid into two regions with levels +-1
                   (random sign); z = sqrt(rho) s_region + sqrt(1 - rho) eps.  A step, not a smooth field.
  outlier(rho)     field(1.5, rho), then 8% of links (at least 1) get an independent shift of +-2.5, rescaled by sqrt(1.5) so the
                   variance stays 1.  Outlier links do NOT resemble their neighbours.
"""
import sys
import numpy as np
sys.path.insert(0, "/home/claude/s18c")
import drift_queue_des_g1 as g1
import corr_net as cn

NODES, ENDS, NL, NB1, NB2 = cn.NODES, cn.ENDS, cn.NL, cn.NB1, cn.NB2
_xy = np.array(NODES, float); _d2 = ((_xy[:, None, :] - _xy[None, :, :]) ** 2).sum(-1)
_A = cn._A
_CH = {}
MID = np.array([(_xy[[cn._NIDX[u], cn._NIDX[v]]]).mean(0) for (u, v) in ENDS])      # link mid-points
ADJ = [(l, m) for l in range(NL) for m in NB1[l] if m > l]                               # adjacent link pairs


def _chol(ell):
    if ell not in _CH:
        K = np.exp(-_d2 / (2 * ell ** 2)) + 1e-8 * np.eye(len(NODES)); fsd = np.sqrt(np.diag(_A @ K @ _A.T))
        _CH[ell] = (np.linalg.cholesky(K), fsd)
    return _CH[ell]


def field(rng, ell, rho):
    ch, fsd = _chol(ell); f = (_A @ (ch @ rng.normal(0, 1, len(NODES)))) / fsd
    return np.sqrt(rho) * f + np.sqrt(1 - rho) * rng.normal(0, 1, NL)


def region(rng, rho):
    ang = rng.uniform(0, np.pi); c = np.array([np.cos(ang), np.sin(ang)]); proj = MID @ c
    cut = rng.uniform(np.quantile(proj, 0.25), np.quantile(proj, 0.75)); s = np.where(proj > cut, 1.0, -1.0) * rng.choice([-1, 1])
    return np.sqrt(rho) * s + np.sqrt(1 - rho) * rng.normal(0, 1, NL)


def outlier(rng, rho):
    z = field(rng, 1.5, rho); m = max(1, int(round(0.08 * NL))); idx = rng.choice(NL, m, replace=False)
    z[idx] += 2.5 * rng.choice([-1, 1], m); return z / np.sqrt(1 + 0.08 * 2.5 ** 2)


PATTERNS = {"ind": lambda r: field(r, 1.5, 0.0), "field": lambda r: field(r, 1.5, 0.7), "short": lambda r: field(r, 0.4, 0.7),
            "region": lambda r: region(r, 0.7), "outlier": lambda r: outlier(r, 0.7)}
TRAIN_ELLS = (0.75, 1.0, 1.5, 2.0, 3.0)        # AI v2 training: smooth fields only, ell in [0.75, 3], rho ~ U(0, 0.9)


def draw_train(rng):
    return field(rng, TRAIN_ELLS[rng.integers(len(TRAIN_ELLS))], rng.uniform(0, 0.9))


def features2(z, v, l_excl=None):
    """AI v2 features for every link, from OTHER links' accumulated data only.
    z: (NL,) standardised accumulated estimates; v: (NL,) their noise variances (standardised units).
    Per link: shrunk inverse-variance means of 1-hop and 2-hop neighbours, log mean noise variance of each ring, ring sizes,
    spread of the 1-hop ring, and two leave-one-out network statistics (noise-corrected adjacent-pair correlation and the
    noise-corrected variance of all other links)."""
    X = np.zeros((NL, 9)); w = 1 / (1 + v)
    zz = z * w                                           # shrunk toward 0 (the fleet mean) by its own noise
    pa = np.array(ADJ)
    for l in range(NL):
        a, b = NB1[l], NB2[l]
        keep = (pa[:, 0] != l) & (pa[:, 1] != l)
        x1, x2 = z[pa[keep, 0]], z[pa[keep, 1]]
        oth = np.r_[0:l, l + 1:NL]
        var_o = max(np.var(z[oth]) - np.mean(v[oth]), 0.05)
        X[l] = [np.sum(zz[a] * w[a]) / np.sum(w[a]), np.sum(zz[b] * w[b]) / np.sum(w[b]) if b else 0.0,
                np.log(np.mean(v[a]) + 1e-6) / 5, np.log(np.mean(v[b]) + 1e-6) / 5 if b else 0.0, len(a) / 6.0, len(b) / 12.0,
                np.std(zz[a]), np.clip(np.mean((x1 - x1.mean()) * (x2 - x2.mean())) / var_o, -1, 1.5), var_o]
    return X
