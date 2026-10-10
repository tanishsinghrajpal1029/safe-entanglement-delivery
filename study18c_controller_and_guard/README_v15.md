# Study 18C v15: generality and assumption-stress sweep (pre-registered 6 Oct 2026, before any v15 run)

**Why.** The critique asked us to show the finding survives materially different conditions, and to establish the method's limits. This sweep is **exploratory in scope**: it tests generality and stresses assumptions A3 (bias) and A6 (stationary window). It cannot rescue or replace the confirmed primary claims.

**Code (sha256, first 16):**

| File | Role | sha |
|---|---|---|
| `drift_queue_des_v15.py` | Simulation; RunV11 with a general threshold τ and an optional mis-specified controller model | `8ea82ead5da0b6d9` |
| `tasks_v15.jsonl` | 5,632 tasks | `22ef330b423e2ae6` |
| `analyze_v15.py` | Locked analysis; tested on synthetic data | `8312add006126e10` |

## Variants

Each variant runs × g {0, 1e-5} × est {static, ols_reset} × {adaptive with oracle, fixed z = 2} × 64 fresh paths.

| Variant | What changes |
|---|---|
| `tau085_ion2020`, `tau085_ionproj` | Threshold 0.85 (ion-2020 L2, ion-proj L3) |
| `tau095_ionproj1`, `tau095_ionfut3` | Threshold 0.95 (ion-proj L1, ion-future L3) |
| `nv_tau080` | NV-like: F0 0.82, 9 Hz, T2 1 s, readout 3%; L1; threshold 0.80 |
| `siv_tau080_L1`, `siv_tau080_L2` | SiV-like: F0 0.86, 1 Hz, T2 2 s, readout 1%; L1/L2; threshold 0.80 |
| `uneven` | ion-proj L3 with ×3 per-link quality spread |
| `bestof3` | ion-proj L3; path = best of 3 candidates by a 200-pair pilot estimate |
| `t2_opt`, `t2_pes` | ion-proj L3; the controller assumes memory T2 = 1.3 s (optimistic) or 0.7 s (pessimistic), while the truth is 1.0 s. A model-mismatch (bias) stress. |

**Smoke test (cloud).**
- Runs on NV, SiV, bestof3, t2_opt and ion-future all completed.
- The adaptive controller **abstains entirely** on some marginal paths (fewer than 20 supporting attempts in its window), e.g. an `uneven` ion-proj path where the oracle delivers about 40% of requests. The same behaviour occurs with the unmodified v11 controller, so it is not a v15 artefact. It is a **cost** to report.

## Hypotheses

| | Prediction | Bar |
|---|---|---|
| **G1** | Safety generalises | Adaptive pooled r_cond ≤ 1% in **every** (variant, g, est) group with ≥ 200 deliveries, excluding `t2_opt` |
| **G2** | Expected limitation: a biased model breaks the guarantee | In `t2_opt`, adaptive exceeds 1% in ≥ 1 group with ≥ 200 deliveries. If not seen, we report robustness to a 30% optimistic T2 error. |
| **G3** | Fixed per-decision rules fail across conditions | Fixed z = 2 exceeds 1% (≥ 200 deliveries) in ≥ 1 group in at least 3 distinct variants |
| **G4** | Cost (descriptive) | Fraction of oracle and abstention rate per variant |

**PSC.** 8 × 16 cores × 0.5 h, so the ceiling is 64 SU; expected 8–20 SU. Used so far: about 278 of 400.
