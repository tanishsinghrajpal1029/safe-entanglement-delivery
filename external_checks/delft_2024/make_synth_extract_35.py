"""Build a synthetic delft_extract JSON with known truth, in the authors' layout, to test analyze_35.py end to end.
Usage: python3 make_synth_extract_35.py OUT.json [F_true] [model_offset] [n_per_basis] [variant]
variant: ok | flipconv (parity convention flipped in 'correlation' attr) | badlabel (unparseable state label)"""
import json, sys
import numpy as np
from delft_core import BELL

rng = np.random.default_rng(3535)
out, F, off, n = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
variant = sys.argv[5] if len(sys.argv) > 5 else "ok"
labs = ["00", "01", "10", "11"]; par = np.array([1, -1, -1, 1])
order = ["Z", "X", "Y"]                                   # saved order in the authors' file ("ZZ XX YY")
tl = ["$\\Psi^+$", "$\\Psi^-$", "combined"] if variant != "badlabel" else ["state A", "state B", "c"]
names = ["Psi+", "Psi-"]
ro = 0.93                                                # per-node readout fidelity (symmetric) -> correlator shrink ro_c
ro_c = (2 * ro - 1) ** 2
d = {"ssro_outcome_tick_labels": labs, "state_generated_tick_labels": tl, "states": {}}
v = (4 * F - 1) / 3
cres = np.zeros((2, 3, 3)); sweep = np.zeros((16, 3, 3, 3))
for j in range(3):
    s = BELL[names[min(j, 1)]]; st = {"datasets": {}}; Fs = []
    for i, b in enumerate(order):
        c_true = s[b] * v
        q = np.array([(1 + c_true * ro_c) / 4] * 4) * 0 + 0
        # true outcome probabilities (unbiased marginals), then readout noise shrinks the correlator
        p_true = (1 + par * c_true) / 4; p_raw = (1 + par * c_true * ro_c) / 4
        N = rng.multinomial(n, p_raw)
        c_raw = float((N * par).sum() / n); c_corr = c_raw / ro_c
        p_corr = (1 + par * c_corr) / 4
        u_c = float(np.sqrt(max(1 - c_raw ** 2, 1e-9) / n) / ro_c)
        corr_attr = -c_corr if variant == "flipconv" else c_corr
        st["datasets"][f"{i:03d}"] = {"N": N.tolist(), "p": p_corr.tolist(), "u_p": [0.01] * 4, "correlation": corr_attr,
                                      "u_correlation": u_c, "node1_readout_basis": b, "node2_readout_basis": b, "combined_readout": b + b}
        Fs.append(s[b] * c_corr)
        vm = (4 * (F + off) - 1) / 3
        cres[0, j, i] = s[b] * vm; cres[1, j, i] = 0.005
        for w in range(16):
            sweep[w, j, 0, i] = c_corr; sweep[w, j, 1, i] = u_c; sweep[w, j, 2, i] = s[b] * vm
    st["fidelity"] = (1 + sum(Fs)) / 4; st["u_fidelity"] = 0.01
    d["states"][f"state_{j}"] = st
d["correlation_results"] = cres[:, :3, :].tolist(); d["total_result_sweep"] = sweep.tolist()
json.dump(d, open(out, "w"))
print(f"synthetic: F_true {F}, model offset {off}, n {n} per basis per state, readout correlator factor {ro_c:.3f}, variant {variant}")
