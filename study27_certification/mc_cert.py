"""Monte Carlo coverage of the kept-pair certificate (Theorem C1) under hostile, drifting and adaptive state sequences.
A run fails if the certificate EVER exceeds the true running average fidelity of kept pairs. Target: P(fail) <= alpha."""
import json, sys, numpy as np
from cert import Certifier
ALPHA = 0.05; NRUN = int(sys.argv[1]) if len(sys.argv) > 1 else 2000; NPAIR = 3000


def run(scen, p, rng, c):
    D = 0.0; K = 0; err = 0; fail = 0; lastT = -10; dsum = 0.0
    for i in range(NPAIR):
        if scen == "iid": delta = 0.08
        elif scen == "drift": delta = 0.02 + 0.2 * (0.5 + 0.5 * np.sin(i / 300))
        elif scen == "fault": delta = 0.03 if i < 1500 else 0.6
        elif scen == "burst": delta = 1.0 if rng.random() < 0.02 else 0.0           # rare totally bad pairs
        elif scen == "adapt":                                                        # adversary: worse right after a test
            delta = 0.9 if (i > 0 and lastT == i - 1) else 0.01                      # (uses only the past: allowed)
        elif scen == "adapt2":                                                       # worse the longer since the last test
            delta = min(1.0, 0.002 * (i - lastT))
        # three-basis error probabilities of a valid Bell-diagonal state F = 1 - delta: hostile scenarios put the whole
        # deficit on Psi- (errors in X and Z, none in Y); others spread it evenly over Phi-, Psi+, Psi- (Werner-like)
        eB = np.array([delta, 0.0, delta]) if scen in ("adapt", "burst", "fault") else np.full(3, 2 * delta / 3)
        T = rng.random() < p
        if T:
            b = rng.integers(3); err += int(rng.random() < eB[b]); lastT = i
        else:
            K += 1; D += delta
            if True:                                                                 # check after EVERY kept pair
                if c.lower(err, K) > 1 - D / K + 1e-12: fail = 1; break
    return fail


out = {}
rng = np.random.default_rng(7)
for p in (0.05, 0.2):
    c = Certifier(p, ALPHA)
    for scen in ("iid", "drift", "fault", "burst", "adapt", "adapt2"):
        f = sum(run(scen, p, rng, c) for _ in range(NRUN)); out[f"p{p}_{scen}"] = [f, NRUN, round(f / NRUN, 4)]
        print(scen, p, f, NRUN, flush=True)
json.dump(out, open("mc_cert_results.json", "w"), indent=1); print(out)
