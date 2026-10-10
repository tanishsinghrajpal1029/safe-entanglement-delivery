"""Scan: true delivered fidelity with T1/T2 memories minus the controller's depolarizing-model prediction,
over the operating distribution of the v16-v18 cells (link quality from the fleet law, waits from the DES link process)."""
import sys, json, numpy as np, drift_queue_des as v4, drift_queue_des_v15 as v15, memory_t1t2_exact as mx
CELLS = {"nv_tau080": (v15.NV, 1, 0.80), "ion2020_tau090": (v15.ION2020, 2, 0.90), "ionproj_tau090": (v15.IONPROJ, 3, 0.90), "tau085_ion2020": (v15.ION2020, 2, 0.85)}
MEM = {"dephasing_T1inf": np.inf, "T1_eq_T2": 1.0, "T1_half_T2_AD_limit": 0.5}     # T1 in units of T2 (T2 = model T2)
N = int(sys.argv[1]) if len(sys.argv) > 1 else 600; rng = np.random.default_rng(22101); out = {}
for c, (P, L, tau) in CELLS.items():
    Ru = P["R"] * 0.7; T2 = P["T2"]; e = P["e"]
    F0 = np.clip(P["F0"] + rng.normal(0, (1 - P["F0"]) * 0.2, (N, L)), 0.3, 0.9999); LAM = (4 * F0 - 1) / 3 - 0.02 * rng.uniform(size=(N, 1))
    rows = []
    for i in range(N):
        lam = np.clip(LAM[i], 0, 1); t1 = rng.exponential(1 / Ru, L); t2 = rng.exponential(1 / Ru, L)
        w1 = t1.max() - t1; w2 = t2.max() - t2; hold = t2.max()
        Fm = v4.dej(v4.chainF(lam, P, L, w1.sum() + hold), v4.chainF(lam, P, L, w2.sum()), e)
        r = [Fm]
        for k, T1 in MEM.items(): r.append(mx.delivered_F(lam, w1, w2, hold, e, ("t1t2", T1 * T2, T2)))
        rows.append(r)
    A = np.array(rows); Fm = A[:, 0]; near = np.abs(Fm - tau) < 0.01; out[c] = {"samples": N, "near_threshold": int(near.sum())}
    for j, k in enumerate(MEM, 1):
        d = A[:, j] - Fm
        out[c][k] = dict(min=float(d.min()), q01=float(np.quantile(d, .01)), median=float(np.median(d)), frac_negative=float((d < -1e-6).mean()),
                         near_min=float(d[near].min()) if near.any() else None, near_median=float(np.median(d[near])) if near.any() else None,
                         label_flips_true_bad_model_good=int(((A[:, j] < tau) & (Fm >= tau)).sum()))
print(json.dumps(out, indent=1)); json.dump(out, open("memory_bias_scan.json", "w"), indent=1)
