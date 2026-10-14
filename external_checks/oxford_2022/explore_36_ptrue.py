"""EXPLORATORY (not pre-registered): O1 recomputed with the test probability p' = 130/256 suggested by the observed
test fraction (0.5080), instead of the pre-registered 1/2. The pre-registered p = 1/2 < p' gives a valid but conservative bound."""
import lzma, sys
import numpy as np
from oxford_core import loss_indicator, kept_fidelity_lower, di_fidelity_from_q
lines = [l for l in lzma.open(sys.argv[1], "rt") if not l.startswith("#")][1:]
d = np.loadtxt(lines, delimiter=",", dtype=np.int64); t, x, y, a, b = d.T
T = (y != 2).astype(np.int64); L = np.zeros(len(d), np.int64)
L[T == 1] = loss_indicator(x[T == 1], y[T == 1], a[T == 1], b[T == 1], (1, 1), -1)
n = len(d); f = T.mean(); se = np.sqrt(f * (1 - f) / n)
print(f"observed test fraction {f:.5f} +- {se:.5f}; 130/256 = {130/256:.5f}; z vs 1/2 = {(f - 0.5) / se:.1f}")
for p in (0.5, 130 / 256):
    FL, qbar, K = kept_fidelity_lower(T, L, p)
    i9 = int(np.argmax(FL > 0.9)) + 1
    print(f"p = {p:.5f}: final F_L {FL[-1]:.4f}; certifies 0.9 from round {i9} ({int(K[i9-1])} kept pairs); DI F_ext >= {di_fidelity_from_q(qbar)[-1]:.4f}")
