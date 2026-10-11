import sys, json, numpy as np
sys.path.insert(0, '.')
import ibm_testkeep_31b as t, ibm_testkeep as base
S = base.schedule(t.SEED_31B)
for dep0 in (None, 0.09, 0.12):
    R = dict(W1=0, W2=0, W3=0, W5=0, W5n=0, mixB=0, err0=[], delay=[])
    for sd in range(60):
        r = t.analyse(S, t.simulate(S, dep0=dep0, seed=1000 + sd))
        R["W1"] += r["W1"]; R["W2"] += r["W2"]; R["W3"] += r["W3"]; R["err0"].append(r["err0"] / r["n0"])
        if r["W5"] is not None: R["W5"] += r["W5"]; R["W5n"] += 1
        R["mixB"] += bool(r["alarm_mixture"] and r["alarm_mixture"]["phase"] == "B")
        if r["W3"]: R["delay"].append(r["alarm_hybrid"]["test"])
    print(f"dep0={dep0}: calib err {np.mean(R['err0']):.3f}; W1 {R['W1']}/60, W2 {R['W2']}/60, W3 (hybrid alarm in B) {R['W3']}/60 "
          f"[mixture {R['mixB']}/60], median alarm at B-test {np.median(R['delay']) if R['delay'] else None}, W5 {R['W5']}/{R['W5n']}", flush=True)
