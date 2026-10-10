"""Study 23, day 1: correlated link qualities on the 5 x 5 grid, and the global AI model's training data.

Link quality model (per network). Node values a_v ~ Gaussian field over node coordinates with squared-exponential kernel
(length scale ELL grid units); link factor f_l = (a_u + a_v)/2, standardised to unit variance; z_l = sqrt(RHO_C) f_l +
sqrt(1 - RHO_C) eps_l, eps ~ N(0, 1). F0_l = F0_fleet + sd_F z_l (same marginal law as the fleet, so the fleet prior stays
calibrated on average); lambda0_l = (4 F0_l - 1)/3 - AMP u_l (as G1). RHO_C = 0 gives independent links (control).
"""
import numpy as np
import sys
sys.path.insert(0, "/home/claude/s18c")
import drift_queue_des_g1 as g1

ELL = 1.5


def grid_links(n=g1.GRID_N):
    nodes, edges = g1.grid_topology(n)
    inv = {v: k for k, v in edges.items()}                     # link id -> frozenset(nodes)
    ends = [tuple(sorted(inv[l])) for l in range(len(edges))]
    return nodes, ends


NODES, ENDS = grid_links()
NL = len(ENDS)
_xy = np.array(NODES, float); _d2 = ((_xy[:, None, :] - _xy[None, :, :]) ** 2).sum(-1)
_K = np.exp(-_d2 / (2 * ELL ** 2)) + 1e-8 * np.eye(len(NODES)); _CH = np.linalg.cholesky(_K)
_NIDX = {v: i for i, v in enumerate(NODES)}
_A = np.zeros((NL, len(NODES)))
for l, (u, v) in enumerate(ENDS): _A[l, _NIDX[u]] = 0.5; _A[l, _NIDX[v]] = 0.5
_FSD = np.sqrt(np.diag(_A @ _K @ _A.T))                       # sd of each link factor (for standardising)
# neighbour structure: 1-hop = links sharing a node; 2-hop = links sharing a node with a 1-hop neighbour (excluding self, 1-hop)
NB1 = [[m for m in range(NL) if m != l and set(ENDS[m]) & set(ENDS[l])] for l in range(NL)]
NB2 = [sorted(set(x for m in NB1[l] for x in NB1[m]) - set(NB1[l]) - {l}) for l in range(NL)]
CORR_TRUE = None


def draw_z(rng, rho_c):
    a = _CH @ rng.normal(0, 1, len(NODES)); f = (_A @ a) / _FSD
    return np.sqrt(rho_c) * f + np.sqrt(1 - rho_c) * rng.normal(0, 1, NL)


def link_corr(rho_c):
    C = (_A @ _K @ _A.T) / np.outer(_FSD, _FSD); return rho_c * C + (1 - rho_c) * np.eye(NL)


def features(lhat, nobs, sd_l):
    """Per-link features for the global model, from OTHER links only: standardised mean of 1-hop and 2-hop neighbour
    estimates, their information weights, and degree. lhat, nobs: (NL,) neighbour point estimates of lambda and counts."""
    X = np.zeros((NL, 6))
    for l in range(NL):
        a, b = NB1[l], NB2[l]
        X[l] = [np.mean(lhat[a]), np.mean(lhat[b]) if b else 0.0, len(a) / 6.0, len(b) / 12.0,
                np.log1p(np.mean(nobs[a])) / 10, np.std(lhat[a])]
    return X
