# USTC 2026 Stage 1 result (10 Oct 2026)

**Pre-registration:** `PREREG_USTC_STAGE1.md` (10dad084; ledger E96). Script 9ae8a9fc, unchanged. Output: `stage1/out_ustc.json`.

## U1 (primary): **PASS**, but a weak test with a consistent bias

Our pure-dephasing memory model, given only the *single-ion* coherence curves, predicts how real remote ion–ion entanglement loses fidelity over 450 ms of storage:

| Storage (ms) | Predicted ΔF | Measured ΔF | Gap (pred − meas) |
|---|---|---|---|
| 100 | −0.048 | −0.077 | +0.029 |
| 200 | −0.121 | −0.147 | +0.026 |
| 300 | −0.162 | −0.205 | +0.044 |
| 450 | −0.218 | −0.238 | +0.020 |

- **Every point is within the bar**, but the bar is wide (0.13–0.15), because the published fidelities carry error bars of about ±0.04–0.06.
- **The model is optimistic at every storage time, by 2–4 fidelity points.** It predicts less decay than measured. The likely cause is that the model omits physics such as readout degradation over storage (recorded in Fig. S3b).

**Why this matters for safety:**
- An optimistic physics model is exactly the failure that our label-free controller cannot catch by itself (v19/v20).
- It is what the guard's **declared physics margin** (G4) is for. On this hardware, that margin would need to be at least about 0.04 in fidelity.

## U2 (secondary): a real ion link drifts over time
- **QBER over 200 data sets** (the file has 200, not the 201 assumed in the pre-registration; n = 4.05×10⁵/200 = 2,025 per set). The mean is 3.6%.
- **Dispersion ratio 3.57** (p ≈ 0): the error rate varies between sets far more than chance allows. Caveat: unequal set sizes, which we cannot check, would also inflate this.
- **The anytime confidence sequence excluded the full-run error rate for 3.5% of the run.** That happens under drift. With an iid link it would happen with probability ≤ 5%, so this one run is consistent with both. Read alongside ICFO (10 of 11 runs fine), it shows that drift exists but the bound mostly survives it.

## Together with ICFO (E92, E95)
Three real-hardware findings support the paper:
1. **Real links drift:** ICFO in 7 of 11 runs, USTC strongly.
2. **The anytime bound mostly holds on real data:** 10 of 11 ICFO runs, plus the USTC run with a brief excursion.
3. **Physics models tend to be optimistic** (USTC: 2–4 points). This motivates the declared-margin guard and the drift-aware guards.
