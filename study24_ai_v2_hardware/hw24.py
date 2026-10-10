"""Study 24 hardware registry. Adds SiV, NV (paths up to 2 links) and ion-future to the G-series grid (g1.HW), with the
presets of drift_queue_des_v15 (unchanged). name -> (preset, tau, Lmax, request rate per s).
Request rates keep the offered load well below each hardware's capacity (SiV makes about 1 link pair per second)."""
import sys
sys.path.insert(0, "/home/claude/s18c")
import numpy as np
import drift_queue_des_g1 as g1
import drift_queue_des_v15 as v15

g1.HW.setdefault("siv", (v15.SIV, 0.80, 2, 0.05))
g1.HW.setdefault("nv2", (v15.NV, 0.80, 2, 0.3))
g1.HW.setdefault("ionfut", (v15.IONFUT, 0.95, 3, 3.0))
HWS = ("ion2020", "ionproj", "ionfut", "nv2", "siv")
RHO_CAL = 0.3                                    # every hardware at its native calibration fraction (the G-series default)


def consts(hw):
    """preset, readout factor r, fleet sd of F0, fleet mean of lambda, fleet sd of lambda (as Study 23)."""
    P = g1.HW[hw][0]; sdf = (1 - P["F0"]) * 0.2
    return P, (1 - 2 * P["q"]) ** 2, sdf, (4 * P["F0"] - 1) / 3 - g1.AMP * 0.5, np.sqrt((4 / 3 * sdf) ** 2 + g1.AMP ** 2 / 12)


def lam_from_z(rng, hw, z):
    P, r, sdf, mu, sdl = consts(hw); F0 = np.clip(P["F0"] + sdf * z, 0.3, 0.9999)
    return np.clip((4 * F0 - 1) / 3 - g1.AMP * rng.uniform(0, 1, len(z)), 0, 1)


def zv(hw, N, K):
    """standardised point estimate and its noise variance from accumulated counts (N, K)."""
    P, r, sdf, mu, sdl = consts(hw)
    ph = (K + 0.5) / (N + 1); lhat = np.clip((2 * ph - 1) / r, 0, 1)
    v = np.where(N > 0, (2 / r) ** 2 * np.clip(ph * (1 - ph), 1e-6, 1) / np.maximum(N, 1), 1e3) / sdl ** 2
    return (lhat - mu) / sdl, v
