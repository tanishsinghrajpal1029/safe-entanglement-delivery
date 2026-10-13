"""Synthetic extract in the Fig. 4 layout (Psi- targets, combined state_2 = state_0 + state_1, sweep with count-rate
weights) with known truth, to test analyze_35b.py end to end.
Usage: python3 make_synth_extract_35b.py OUT.json F_true model_offset n_per_basis_per_state [variant: ok|flipconv]"""
import json, sys
import numpy as np
from delft_core import BELL

rng = np.random.default_rng(353535)
out, F, off, n = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
variant = sys.argv[5] if len(sys.argv) > 5 else "ok"
labs = ["00", "01", "10", "11"]; par = np.array([1, -1, -1, 1]); order = ["Z", "X", "Y"]; s = BELL["Psi-"]
ro_c = (2 * 0.93 - 1) ** 2; v = (4 * F - 1) / 3; vm = (4 * (F + off) - 1) / 3
d = {"ssro_outcome_tick_labels": labs, "state_generated_tick_labels": ["$\\Psi^-$", "$\\Psi^-$", "Combined"], "states": {}}
Ns = {}
for j in (0, 1):
    for i, b in enumerate(order):
        Ns[(j, b)] = rng.multinomial(n, (1 + par * s[b] * v * ro_c) / 4)
for b in order: Ns[(2, b)] = Ns[(0, b)] + Ns[(1, b)]
sweep = np.zeros((16, 3, 3, 3)); cps = np.zeros((16, 2, 2)); cps[:, 0, 1] = 0.6; cps[:, 1, 1] = 0.4
cres = np.zeros((2, 3, 3))
for j in (0, 1, 2):
    st = {"datasets": {}}; cs = []
    for i, b in enumerate(order):
        N = Ns[(j, b)]; m = N.sum(); c_raw = float((N * par).sum() / m); c_cor = c_raw / ro_c
        u_c = float(np.sqrt(max(1 - c_raw ** 2, 1e-9) / m) / ro_c)
        st["datasets"][f"{i:03d}"] = {"N": N.tolist(), "p": ((1 + par * c_cor) / 4).tolist(), "u_p": [0.01] * 4,
                                      "correlation": (-c_cor if variant == "flipconv" else c_cor), "u_correlation": u_c,
                                      "node1_readout_basis": b, "node2_readout_basis": b, "combined_readout": b + b}
        cs.append(s[b] * c_cor)
        sweep[:, j, 0, i] = c_cor; sweep[:, j, 1, i] = u_c; sweep[:, j, 2, i] = s[b] * vm
        if j < 2: cres[0, j, i] = s[b] * vm; cres[1, j, i] = 0.005
    st["fidelity"] = (1 + sum(cs)) / 4; st["u_fidelity"] = 0.01; d["states"][f"state_{j}"] = st
d["correlation_results"] = cres.tolist(); d["total_result_sweep"] = sweep.tolist(); d["total_cps_sweep"] = cps.tolist()
json.dump(d, open(out, "w")); print(f"synthetic 35B: F_true {F}, offset {off}, n {n}/basis/state, variant {variant}")
