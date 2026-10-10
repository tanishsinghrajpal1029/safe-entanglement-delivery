"""Synthetic ICFO-like data to test icfo_stage1.py (known V = 0.80, p10 = p01 = 0.006, h_c = 0.04)."""
import os, sys, numpy as np
rng = np.random.default_rng(1); root = sys.argv[1]
def w(path, x): os.makedirs(os.path.dirname(path), exist_ok=True); np.sort(x).astype("<u8").tofile(path)
for tau in (2, 7, 12, 19, 25):
    base = f"{root}/{tau}us"; eta = 0.006 * np.exp(-tau / 40)
    def run(name, folder, dur, mode, phase=0.0):
        n = int(1400 * dur); i = np.sort(rng.uniform(0, dur, n) * 1e12).astype(np.int64)
        d = i + tau * 1_000_000 + int(rng.uniform(-150e3, 150e3))     # echo delay
        if mode == "both":   pa = pb = eta
        elif mode == "tom":  pa, pb = eta, 0.0
        elif mode == "jerry": pa, pb = 0.0, eta
        else: pa = pb = eta
        sig = rng.random(n) < (pa + pb); P1 = 0.5 * (1 + (0.80 * np.cos(phase) if mode == "coh" else 0.0))
        to1 = rng.random(n) < P1; s1 = d[sig & to1] + rng.integers(-150_000, 150_000, (sig & to1).sum()); s2 = d[sig & ~to1] + rng.integers(-150_000, 150_000, (sig & ~to1).sum())
        noise = lambda r: rng.uniform(0, dur, int(r * dur)) * 1e12
        w(f"{base}/{folder}/i_{name}.pt", i); w(f"{base}/{folder}/s1_{name}.pt", np.r_[s1, noise(300)]); w(f"{base}/{folder}/s2_{name}.pt", np.r_[s2, noise(400)])
    for k in range(7): run(f"afc{tau}us_coh_{k+1}", "data - coherences", 120, "coh", 2 * np.pi * k / 7)
    run(f"afc{tau}us_tom", "data - diagonal", 120, "tom"); run(f"afc{tau}us_jerry", "data - diagonal", 120, "jerry"); run(f"afc{tau}us", "data - diagonal", 600, "both")
