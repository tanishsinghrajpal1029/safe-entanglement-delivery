"""Fixed-K vs anytime certificate (referee v0.3 M16; computation, not pre-registered).
For a planned number K of kept pairs, a single bet lambda chosen in advance gives a certificate (Ville/Markov, same threshold);
C1 mixes G = 8 bets so that no K or error rate has to be planned. Compare kept pairs needed to certify tau, alpha = 0.05:
  K_C1      C1 as published (cert.Certifier, G = 8)
  K_fix     best single lambda for that (p, F, K), chosen with knowledge of F and K (optimistic for the fixed design)
  K_LB      converse floor (perfect pairs; lb.k_lb)
Errors are set to their expected count round((K p/(1-p)) (2/3)(1-F)) (deterministic, as in Fig. 4c)."""
import sys, json
import numpy as np
sys.path.insert(0, "/home/claude/s27"); sys.path.insert(0, "/home/claude/s28")
from cert import Certifier, lam_max, kprime
import lb as LB
ALPHA = 0.05

def lower_single(lam, p, err, K):
    c = 1.5 * kprime(lam, p); D = c * err + np.log(1 / ALPHA) / lam
    return 1 - D / K

def k_needed(fn, start=10):
    K = start
    while not fn(K) and K < 10 ** 7: K = int(K * 1.02) + 1
    lo = max(10, int(K / 1.02) - 2)
    for k in range(lo, K + 1):
        if fn(k): return k
    return K

out = {}
for tau in (0.9, 0.8):
    for p in (0.05, 0.1, 0.2):
        lams = lam_max(p) * np.linspace(0.02, 0.999, 400)
        c1 = Certifier(p, ALPHA)
        for F in (1.0, 0.97, 0.95):
            if F <= tau: continue
            err = lambda K: int(round(K * p / (1 - p) * (2 / 3) * (1 - F)))
            kc1 = k_needed(lambda K: c1.lower(err(K), K) >= tau)
            kfx = k_needed(lambda K: max(lower_single(l, p, err(K), K) for l in lams) >= tau)
            out[f"tau{tau}_p{p}_F{F}"] = dict(K_C1=kc1, K_fixed=kfx, ratio=round(kc1 / kfx, 2))
        out[f"tau{tau}_p{p}_LB"] = LB.k_lb(p, tau)
print(json.dumps(out, indent=0))
json.dump(out, open("fixedk_out.json", "w"), indent=1)
