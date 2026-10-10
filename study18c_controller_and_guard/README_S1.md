# Study 18C S1: re-checking C2 with realistic overlapping calibration windows (pre-registered 8 Oct 2026, before any S1 run)

**Why.** This was found in G1 (E67). Every single-path run from v16 to C2 and P1 drew **fresh** window counts for each decision. In reality, consecutive decisions share almost all of their 100-s window. Fresh draws are valid for the **mean** risk, but they remove the correlation between decisions on a path. So the path-level clustering of bad deliveries, and hence C2's path-bootstrap upper bounds (≤ 0.55% for non-SiV), may have been understated.

## Change (the data model only)

- Each link gets one pre-generated calibration stream for the whole run. Events arrive as a Poisson process at rate ρR. Each event is a parity bit with P(even) = (1 + rλ_true(t_event))/2, using the true, drifting or faulted λ at that moment.
- A decision at time t uses the events in (t − T, t].
- Everything else is C2's: the controller (`m123`), paths, fleet samples, seeds and oracle. The run differs only through the counts.

## Design (6,144 tasks)

C2 block A (8 cells × g {0, 1e-5} × memory {deph, t1eq, ad}), using the **first 128 of C2's 256 paths** in each group. This is paired with C2 rows idx < 128.

## Smoke test (cloud, 3 tasks; code and timing only)

| Task | S1 delivered / bad | C2 delivered / bad |
|---|---|---|
| ion-future, g 1e-5, ad, idx 0 | 2,800 / 0 | 2,395 / 1 |
| NV, g 0, deph, idx 1 | 12 / 1 | 0 / 0 |
| SiV, g 0, deph, idx 2 | 0 / 0 | 0 / 0 |

S1 runs at the same speed as C2.

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_s1.py` | `42d09f65e55a5d6d` |
| `tasks_s1.jsonl` | `2b05fc1e92d9fef0` |
| `analyze_s1.py` (locked; tested on synthetic data) | `1ece7f04fdddc9f7` |

S1 uses `drift_queue_des_c2.py`, `drift_queue_des_v21.py`, `drift_queue_des_c1.py` and the v4–v20 modules unchanged.

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **S1-a** (primary) | C2's main claim survives realistic windows | Every non-SiV group: r ≤ 1% |
| **S1-b** | Bounds widen | Median ratio (S1 upper bound / C2 upper bound, same paths) over non-SiV groups > 1 |
| S1-c (descriptive) | | Number of non-SiV groups with upper bound ≤ 1% under S1 vs C2 (same paths); SiV reported separately |

**How results will be read:**
- **If S1-a fails:** C2's headline is restated with the realistic data model and the failing groups are named. The earlier simulator choice becomes a stated limitation of the v16–C2 / P1 results.
- **If S1-b is confirmed:** the paper reports S1's upper bounds, not C2's, as the clustering-aware uncertainty.

**PSC.** 16 shards × 16 cores × 60 min, so the ceiling is 256 SU. Expected about 100–130 SU, from C2's timing of about 72 core-seconds per task. G2 (ceiling 64) plus S1 (ceiling 256) plus about 670 already charged gives a worst case of about 990 of the 1,000 approved.
