# Study 18C v18: misspecification stress for the estimated-prior controller (pre-registered 6 Oct 2026, before any confirmatory run)

**Why.** v17 (ledger E43) passed, but its model family matched the simulator: a Normal fleet law and a known drift amplitude. A referee will ask what happens when that model is wrong. In v18 the controller's model stays **fixed** (Normal fit, assumed amplitude), and we break the truth or the assumption.

| Stress | Truth | Controller assumes |
|---|---|---|
| `t3` | Heavy-tailed fleet (Student-t, 3 dof, same sd) | Normal |
| `mixlow` | 85% normal links + 15% bad links (−3 sd) | Normal |
| `mixhigh` | 85% normal links + 15% excellent links (+3 sd) | Normal |
| `amp01` | Drift amplitude 0.02 | 0.01 (optimistic) |
| `amp03` | Drift amplitude 0.02 | 0.03 (pessimistic) |

The evaluation paths and the fleet paths are both drawn from the true law.

**Design.** Variants as v16/v17 × g ∈ {0, 1e-5} × 5 stresses × {eb128, eb32x10} × 128 fresh paths (seeds 18961–18963). That gives **10,240 tasks**.

## Cloud dev pilot (disclosed; seeds 19961–19963; eb128, g 1e-5; no confirmatory-seed runs)

| Stress | NV (32 paths): r | ion-proj L3 (5 paths): r |
|---|---|---|
| t3 | 0.10% (1/976) | **2.25% (13/579)** |
| mixlow | 0 | 0.11% |
| mixhigh | 0.02% | 0.36% |
| amp01 | 0 | 0.34% |
| amp03 | 0 | 0.76% |

**Flagged in advance.** The heavy-tailed fleet may break the Normal empirical-Bayes fit on ion-proj. The fitted Normal under-weights the lower tail, which makes the prior optimistic for bad links.

**Code (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_v18.py` | `0d53da93eb90bf2f` |
| `tasks_v18.jsonl` | `dc2201b4fef76d28` |
| `analyze_v18.py` (locked; tested on synthetic data) | `6aa06ebad379de03` |

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **S1** | Robust to fleet-law shape | r ≤ 1% in every group for t3, mixlow and mixhigh. Each stress is reported separately. **t3 is at risk** (pilot). |
| **S2** | Robust to ±50% drift-amplitude error | r ≤ 1% in every group for amp01 and amp03 |
| **S3** | Descriptive | Path-bootstrap upper bound and fraction of oracle per stress |

**How results will be read:** any violation is reported as a named limitation ("requires a fleet law with approximately Normal tails", for example). No fix will be added to this paper.

**PSC.** 8 × 16 cores × 0.58 h, so the ceiling is 75 SU (worst case ≈ 395 of the 400 approved); expected 30–40 SU. Account balance before the run is 9,549 / 10,000 SU.
