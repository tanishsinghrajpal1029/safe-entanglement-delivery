"""Study 36 (Oxford) locked analysis. Usage: python3 analyze_36.py link-quality-events.csv.xz > results_36.txt
Locked with PREREG_36.md. numpy + scipy (+ lzma). Order: G1 (design), G2 (reproduction; fixes the convention), then
O1, O2 (primary), S1-S4 (secondary). A gate failure stops the run.
"""
import json, lzma, sys, hashlib
from datetime import datetime, timezone
import numpy as np
from oxford_core import (chsh_variants, loss_indicator, kept_fidelity_lower, di_fidelity_from_q, dispersion_test, lag1_perm, SQ2)

P_TEST = 0.5                  # characterisation run: gamma = 1/2 (paper, Fig. 3 caption and S4)
S_PUB, Q_PUB = 2.677, 0.0144  # published values for this run (main text)
NCHUNK, CHUNK = 96, 20000     # header: 96 ARTIQ chunks, 1,920,000 events


def main(path):
    P = lambda *a: print(*a, flush=True); out = {}
    P(f"run started {datetime.now(timezone.utc).isoformat(timespec='seconds')}; data sha256 {hashlib.sha256(open(path,'rb').read()).hexdigest()[:16]}")
    with lzma.open(path, "rt") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    assert lines[0].strip() == "time_ns,alice_basis,bob_basis,alice_outcome,bob_outcome", lines[0]
    d = np.loadtxt(lines[1:], delimiter=",", dtype=np.int64)
    tns, x, y, a, b = d.T; n = len(d)
    # ---------------- G1: design
    test = (y != 2).astype(np.int64)
    ftest = test.mean(); xs, ys = x[test == 1], y[test == 1]
    combos = {(i, j): float(np.mean((xs == i) & (ys == j))) for i in (0, 1) for j in (0, 1)}
    g1 = (n == NCHUNK * CHUNK and abs(ftest - P_TEST) <= 0.01 and np.all(x[test == 0] == 0) and np.all(np.diff(tns) >= 0)
          and all(abs(v - 0.25) <= 0.01 for v in combos.values()) and set(np.unique(a)) <= {0, 1} and set(np.unique(b)) <= {0, 1})
    P(f"G1 {'PASS' if g1 else 'FAIL'}  rows {n}; test fraction {ftest:.4f}; key rounds all x=0: {bool(np.all(x[test == 0] == 0))}; "
      f"time non-decreasing: {bool(np.all(np.diff(tns) >= 0))}; test-setting fractions {({k: round(v, 4) for k, v in combos.items()})}")
    out["G1"] = bool(g1)
    if not g1: P("STOP: gate G1 failed."); return out
    # ---------------- G2: reproduce the published S and QBER; this fixes the convention
    ta, tb = a[test == 1], b[test == 1]
    E = [[float(np.mean(1 - 2 * (ta[(xs == i) & (ys == j)] ^ tb[(xs == i) & (ys == j)]))) for j in (0, 1)] for i in (0, 1)]
    V = chsh_variants(E); match = [k for k, v in V.items() if abs(v - S_PUB) <= 0.02]
    ka, kb = a[test == 0], b[test == 0]
    P(f"G2 candidates: " + "; ".join(f"{k}: {v:+.4f}" for k, v in V.items()))
    if len(match) != 1:
        P(f"G2 FAIL: {len(match)} conventions within 0.02 of S = {S_PUB}. STOP."); out["G2"] = False; return out
    (pattern, sign) = match[0]
    qber = float(np.mean(ka != kb)) if sign == +1 else float(np.mean(ka == kb))   # Alice inversion flips the key-round parity
    g2 = abs(qber - Q_PUB) <= 0.002
    P(f"G2 {'PASS' if g2 else 'FAIL'}  convention {match[0]}: S = {V[match[0]]:.4f} (published {S_PUB}); key-round QBER {qber:.4%} (published {Q_PUB:.2%}, tol 0.2 pt)")
    out["G2"] = bool(g2); out["convention"] = [list(pattern), sign]
    if not g2: P("STOP: gate G2 failed."); return out

    # ---------------- per-round loss indicators (test rounds), time order
    L = np.zeros(n, dtype=np.int64)
    L[test == 1] = loss_indicator(xs, ys, ta, tb, pattern, sign)
    P("\n== PRIMARY")
    FL, qbar, K = kept_fidelity_lower(test, L, P_TEST)
    o1 = FL[-1] > 0.9
    first09 = int(np.argmax(FL > 0.9)) + 1 if np.any(FL > 0.9) else None
    P(f"O1 {'PASS' if o1 else 'FAIL'}  anytime certificate on kept (key) pairs: final F_L = {FL[-1]:.4f} (bar > 0.9) over {int(K[-1])} kept pairs; "
      f"first certifies 0.9 at round {first09} ({int(K[first09 - 1]) if first09 else '-'} kept pairs); point estimate sqrt2(1-2q) = {SQ2 * (1 - 2 * L[test == 1].mean()):.4f}")
    out["O1"] = dict(pass_=bool(o1), F_L=float(FL[-1]), kept=int(K[-1]), first_round_09=first09)
    blk = np.arange(n) // CHUNK
    kL = np.bincount(blk, weights=L * test, minlength=NCHUNK); nT = np.bincount(blk, weights=test, minlength=NCHUNK)
    dt = dispersion_test(kL, nT); o2 = dt["p"] < 0.05
    P(f"O2 {'PASS' if o2 else 'FAIL'}  over-dispersion of the CHSH loss rate across {NCHUNK} chunks: X2 = {dt['X2']:.1f} (df {dt['df']}), p = {dt['p']:.2e}, "
      f"ratio {dt['ratio']:.2f}, excess relative fluctuation {dt['excess_rel']:.1%}, mean loss {dt['rate']:.4f}")
    out["O2"] = dict(pass_=bool(o2), **dt)

    P("\n== SECONDARY")
    errK = (ka != kb) if sign == +1 else (ka == kb)
    kept_idx = np.where(test == 0)[0]
    zerr = np.zeros(n); zerr[kept_idx] = errK
    Zc = np.cumsum(zerr); ub = 1 - Zc / np.maximum(K, 1) / 2
    viol = np.where((K >= 1000) & (FL > ub))[0]
    P(f"S1 {'PASS' if len(viol) == 0 else 'FAIL'}  consistency: F_L(t) <= 1 - (kept Z-error fraction)/2 at every t with >= 1000 kept pairs; violations {len(viol)}; final upper value {ub[-1]:.4f}")
    DI = di_fidelity_from_q(qbar)
    P(f"S2 descriptive  device-independent (self-testing) bound on kept pairs: final F_ext >= {DI[-1]:.4f}")
    ac, pac = lag1_perm(kL / nT)
    P(f"S3 {'PASS' if pac < 0.05 else 'FAIL'}  persistence: lag-1 autocorrelation of chunk loss rates {ac:+.3f}, one-sided permutation p = {pac:.4f} (prediction: persistent, p < 0.05)")
    kZ = np.bincount(blk, weights=zerr, minlength=NCHUNK); nK = np.bincount(blk, weights=1 - test, minlength=NCHUNK)
    dz = dispersion_test(kZ, nK)
    P(f"S4 descriptive  QBER dispersion across chunks: X2 = {dz['X2']:.1f} (df {dz['df']}), p = {dz['p']:.2e}, ratio {dz['ratio']:.2f}, excess {dz['excess_rel']:.1%}")
    gaps = np.diff(tns) / 1e9; big = np.sort(gaps)[-5:]
    P(f"info: chunk rates min/median/max loss {np.min(kL / nT):.4f}/{np.median(kL / nT):.4f}/{np.max(kL / nT):.4f}; five largest gaps between heralds (s) {np.round(big, 1).tolist()}")
    out.update(S1=dict(violations=int(len(viol)), final_upper=float(ub[-1])), S2=float(DI[-1]), S3=dict(lag1=ac, p=pac), S4=dz)
    json.dump(out, open("results_36.json", "w"), indent=1, default=float)
    return out


if __name__ == "__main__":
    main(sys.argv[1])
