"""Synthetic events file in the Oxford export format, with known truth, to test analyze_36.py end to end.
Usage: python3 make_synth_csv_36.py OUT.csv.xz [S] [QBER] [variant: ok | badfrac | drift]
Convention planted: minus sign on (x, y) = (1, 1) and Alice's outcomes inverted (sign -1)."""
import lzma, sys
import numpy as np

rng = np.random.default_rng(3636)
out = sys.argv[1]; S = float(sys.argv[2]) if len(sys.argv) > 2 else 2.677; Q = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0144
variant = sys.argv[4] if len(sys.argv) > 4 else "ok"
n = 1_920_000; pt = 0.3 if variant == "badfrac" else 0.5
test = rng.random(n) < pt
x = np.where(test, rng.integers(0, 2, n), 0); y = np.where(test, rng.integers(0, 2, n), 2)
s = np.where((x == 1) & (y == 1), -1, 1)
Sv = np.full(n, S) if variant != "drift" else S + 0.08 * np.sin(np.arange(n) / n * 12)   # chunk-scale persistent drift
E = s * Sv / 4
same = np.where(test, rng.random(n) < (1 + E) / 2, rng.random(n) >= Q)
b = rng.integers(0, 2, n); a_true = np.where(same, b, 1 - b); a = 1 - a_true                       # Alice inverted
t = np.cumsum(rng.exponential(1.6e7, n)).astype(np.int64); t -= t[0]
with lzma.open(out, "wt") as f:
    f.write("# synthetic file in the Oxford export format (Study 36 harness)\n#\n")
    f.write("time_ns,alice_basis,bob_basis,alice_outcome,bob_outcome\n")
    np.savetxt(f, np.column_stack([t, x, y, a, b]), fmt="%d", delimiter=",")
print(f"synthetic: S {S}, QBER {Q}, test fraction {pt}, variant {variant}")
