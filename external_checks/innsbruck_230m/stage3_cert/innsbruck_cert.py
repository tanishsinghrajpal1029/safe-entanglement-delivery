"""Innsbruck Stage 3: model-free fidelity certificate from the six diagonal scans (PREREG_INNSBRUCK_CERT.md).
Usage: python innsbruck_cert.py stage1_counts.csv"""
import json, sys
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import fisher_exact

ALPHA = 0.05; NCAND = 8; LEVEL = ALPHA / (3 * NCAND)
SCANS = {"Z": ["1651", "1655"], "X": ["1653.02", "1659"], "Y": ["1656", "1702.02"]}
PLUS = {"H", "D", "R"}                                    # +1 eigenstates of sigma_z, sigma_x, sigma_y
TARGETS = {"Phi+": {"X": 1, "Y": -1, "Z": 1}, "Phi-": {"X": -1, "Y": 1, "Z": 1}, "Psi+": {"X": 1, "Y": 1, "Z": -1}, "Psi-": {"X": -1, "Y": -1, "Z": -1}}


def kl(a, b):
    a = min(max(a, 1e-15), 1 - 1e-15); b = min(max(b, 1e-15), 1 - 1e-15)
    return a * np.log(a / b) + (1 - a) * np.log((1 - a) / (1 - b))


def kl_ucb(k, n, level):
    ph = k / n; c = np.log(1 / level) / n
    if kl(ph, 1 - 1e-12) <= c: return 1.0
    return brentq(lambda e: kl(ph, e) - c, ph, 1 - 1e-12)


def outcomes(row, mapping):
    """per-scan counts of (ion sign, photon sign): {(i, f): count}. APD3 sees the 2nd-named label under M2, the 1st under M1."""
    a, b = row["photon_basis"].split("/")
    apd3, apd4 = (b, a) if mapping == "M2" else (a, b)
    s3, s4 = (1 if apd3 in PLUS else -1), (1 if apd4 in PLUS else -1)
    return {(1, s3): row["APD3_bright"], (-1, s3): row["APD3_dark"], (1, s4): row["APD4_bright"], (-1, s4): row["APD4_dark"]}


def main(path):
    df = pd.read_csv(path, dtype={"scan": str}); df["scan"] = df.scan.astype(str)
    out = {"level_per_basis": LEVEL, "candidates": {}}
    for mapping in ("M1", "M2"):
        for tname, sg in TARGETS.items():
            res = {}
            for B, scans in SCANS.items():
                k = n = 0; per = []
                for sc in scans:
                    row = df[df.scan == sc].iloc[0]; assert row["ion_basis"] == B, (sc, row["ion_basis"], B)
                    oc = outcomes(row, mapping); ks = sum(c for (i, f), c in oc.items() if i * f != sg[B]); ns = sum(oc.values())
                    k += ks; n += ns; per.append((int(ks), int(ns)))
                res[B] = dict(k=int(k), n=int(n), e_hat=k / n, e_ub=kl_ucb(k, n, LEVEL), per_scan=per)
            Fh = 1 - sum(res[B]["e_hat"] for B in "XYZ") / 2; FL = 1 - sum(res[B]["e_ub"] for B in "XYZ") / 2
            out["candidates"][f"{mapping}/{tname}"] = dict(F_hat=Fh, F_L=FL, bases=res)
    head = out["candidates"]["M2/Phi+"]
    print(f"HEADLINE M2/Phi+: F_hat = {head['F_hat']:.4f}, certified F_L = {head['F_L']:.4f} (95%, simultaneous over 8 candidates)")
    for B in "XYZ":
        r = head["bases"][B]; print(f"  {B}: {r['k']}/{r['n']} errors, e_hat {r['e_hat']:.4f}, e_ub {r['e_ub']:.4f}, per scan {r['per_scan']}")
    print(f"R1-A (primary) F_L > 1/2: {'PASS' if head['F_L'] > 0.5 else 'FAIL'}")
    pv = {}
    for B in "XYZ":
        (k1, n1), (k2, n2) = head["bases"][B]["per_scan"]; pv[B] = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])[1]
    ok = all(p > 0.01 / 3 for p in pv.values())
    print(f"R1-C (diagnostic) detector-swapped scans agree in every basis (Fisher exact, Bonferroni 0.01/3): {'PASS' if ok else 'FAIL'} {pv}")
    print(f"R1-D (descriptive) F_hat {head['F_hat']:.4f} vs Stage 1 Phi+ 0.913 (|diff| <= 0.01 expected): "
          f"{'consistent' if abs(head['F_hat'] - 0.913) <= 0.01 else 'INCONSISTENT'}; F_L {head['F_L']:.4f} vs 0.920 / 0.924 (F_L above flags an error)")
    print("all candidates (for the union only):", {k: round(v["F_L"], 4) for k, v in out["candidates"].items()})
    out["R1C_p"] = pv
    json.dump(out, open("innsbruck_cert_result.json", "w"), indent=1, default=float)


if __name__ == "__main__":
    main(sys.argv[1])
