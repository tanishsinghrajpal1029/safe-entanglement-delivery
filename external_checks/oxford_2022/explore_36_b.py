"""DESCRIPTIVE/EXPLORATORY additions to Study 36 (fact-check items): (a) last time the anytime bound is <= 0.9,
(b) the bound with a union over all 8 CHSH conventions (alpha/8 each)."""
import lzma, sys
import numpy as np
from oxford_core import loss_indicator, kept_fidelity_lower
lines = [l for l in lzma.open(sys.argv[1], "rt") if not l.startswith("#")][1:]
d = np.loadtxt(lines, delimiter=",", dtype=np.int64); t, x, y, a, b = d.T
T = (y != 2).astype(np.int64); L = np.zeros(len(d), np.int64)
L[T == 1] = loss_indicator(x[T == 1], y[T == 1], a[T == 1], b[T == 1], (1, 1), -1)
for p in (0.5, 130 / 256):
    for alpha, lab in ((0.05, "pre-registered"), (0.05 / 8, "union over 8 conventions")):
        FL, qbar, K = kept_fidelity_lower(T, L, p, alpha)
        first = int(np.argmax(FL > 0.9)); below = np.where(FL <= 0.9)[0]; last = int(below[-1]) if len(below) else -1
        print(f"p={p:.5f} {lab:26s}: final F_L {FL[-1]:.4f}; first > 0.9 at kept {int(K[first])}; last <= 0.9 at kept {int(K[last]) if last >= 0 else 0} (round {last + 1})")
