# Study 18C C1: confirmatory run of the frozen final controller (pre-registered 7 Oct 2026, before any confirmatory run)

**Why.** The final controller was assembled across v16–v20, after seeing failures; each step used fresh seeds. C1 freezes it and tests it **once**, on brand-new seeds, with 4× the paths, across every condition. This answers the forking-paths objection and the fragile cells. Its results are the paper's headline table, **whatever they are**.

**Frozen controller** (`drift_queue_des_c1.py`, sha `070acce42d9a841d`):

- static 100 s parity window;
- fleet prior estimated by hierarchical empirical Bayes from 128 fleet path-windows (Normal law, drift amplitude 0.02);
- posterior draws (M = 256) pushed through the T1/T2-aware Pauli-transfer model with the hardware's T1, T2;
- window-threshold (local-fdr) rule, δ = 1%, ≥ 20 supporting attempts.

**Truth.** The T1/T2 density-matrix model (identical to the NetSquid-validated exact model to 6×10⁻¹⁶).

| Block | Design | Paths | Role |
|---|---|---|---|
| **A** core | 8 cells × g {0, 1e-5} × memory {dephasing-only, T1 = T2, T1 = T2/2} × Normal fleet = 48 groups | 256 | Confirmatory |
| **B** fleet law | 8 cells × g 1e-5 × dephasing × {t3, mixlow, mixhigh} = 24 groups | 128 | Confirmatory |
| **C** fault | 8 cells × g 1e-5 × dephasing; unannounced fault: one link's F0 drops 2 population sd at a random time | 128 | **Exploratory** |

**Cells.** NV L1 τ 0.80; ion-2020 L2 τ 0.90; ion-proj L3 τ 0.90; ion-2020 L2 τ 0.85; ion-proj L3 τ 0.85; ion-proj L1 τ 0.95; ion-future L3 τ 0.95; SiV L1 τ 0.80.

Each task also runs a same-seed oracle, for the fraction-of-oracle cost. In total: **16,384 tasks**, seeds 18991–18994.

## Cloud dev pilot (disclosed; seeds 19991–19994; 1–2 paths per cell; no confirmatory-seed runs)

The pilot was used for runtime and code checks only. Nothing was tuned after it. **Two cells are flagged at risk:**

- **ion-future L3 τ 0.95, amplitude-damping memory:** 1.37% (1,018 / 74,504 on 2 paths).
- **SiV L1, dephasing:** 5 bad of 98 deliveries over 8 paths. The mean predicted risk among those deliveries was 1.2%. SiV is the thinnest-data cell (about 30 parity pairs per window).

Everything else in the pilot was ≤ 0.7%.

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_c1.py` | `070acce42d9a841d` |
| `tasks_c1.jsonl` | `2f93b6523bba24b4` |
| `analyze_c1.py` (locked; tested on synthetic data) | `24241553a68ea25c` |
| `ptm_model.py` | `bf59d252191eefbd` |

C1 also uses v4–v20 modules unchanged; v18 is `0d53da93`, v20 is `d3242555`.

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **C-A1** (primary) | The frozen controller is safe across hardware, drift and memory physics | Block A: r ≤ 1% in **every** group |
| **C-A2** (stricter) | Same, allowing for path clustering | Block A: path-bootstrap 95% upper bound ≤ 1% in every group |
| **C-B** | Robust to fleet-law shape | Block B: r ≤ 1% in every group |
| **C-C** (exploratory) | Unannounced faults | Post-fault r per cell, reported. Expectation: the window lags the fault, so some cells may exceed 1%. |
| **D** | Cost | Fraction of oracle per cell × memory |

**How results will be read:**

- **C-A1 and C-B pass:** these become the paper's main claim.
- **Any failure:** reported in the abstract-level summary as the controller's boundary (e.g. "thin-data hardware such as SiV-like links"). There will be **no re-tuning and no re-run on new seeds** to make it pass.

**PSC.** 16 shards × 32 cores × 1 h, so the ceiling is 512 SU. With ≈ 354 used, the worst case is ≈ 866 of the 1,000 approved. Expected about 180–260 SU.
