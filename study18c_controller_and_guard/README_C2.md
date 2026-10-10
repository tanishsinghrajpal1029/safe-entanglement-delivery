# Study 18C C2: confirmatory run of the robust-prior controller v21 (pre-registered 7 Oct 2026, before any confirmatory run)

**Status: post-hoc fix.** C1 (E54) failed its pre-registered test, and that verdict stands. v21 was designed *after* seeing it. C2 tests v21 once, on fresh seeds (19011–19014), on the same grid as C1. The paper reports C1 and C2 side by side.

## What v21 changes (prior only; the C1 controller is otherwise frozen)

| | Change | Targets |
|---|---|---|
| M1 | Hyperprior on the fleet spread s: uniform in s (weakly informative), instead of log-uniform | SiV: over-confident prior from thin fleet data |
| M3 | Drift-aware window likelihood. Counts measure the window-average λ; the offset to the current λ is computed exactly per phase of the known sawtooth (verified to 5×10⁻⁸). | ion-future amplitude-damping cell: optimistic bias ≈ gT/2 per link |
| M2 | Declared fault component: each link's prior is 5% "degraded by D ~ U(0, 4 ŝ)" | Faults, *if* faults are rare and declared |

## Dev pilots (disclosed; seeds 20001–20004; no confirmatory-seed runs)

| Cell | C1 controller | v21 |
|---|---|---|
| ion-future L3 τ 0.95, amplitude damping, g 1e-5 (3 paths) | 1.63% | **0.37%** (throughput 0.46 → 0.43 of oracle) |
| SiV, dephasing (24 paths) | 7.4% | **1.5–1.6%** (2/137 and 1/63) — **still at risk**; throughput falls from 0.16 to 0.03–0.07 |
| NV always-fault (16 paths) | post-fault 40% | 36–53% — **M2 does not fix frequent faults** |
| Regressions (ion-proj, τ 0.85 ion-proj) | | None (0.07%, 0.37%) |

## Theory point (stated before the run)

A fault smaller than one window's estimation noise is not identifiable from that window. By Proposition 2, a label-free controller is then calibrated only if its prior fault rate matches reality. So:

- block **R** (faults on 5% of paths, matching the declared ε = 0.05) is a confirmatory test;
- block **C** (every path faulted) is a worst case, expected to fail.

## Design: 16,640 tasks

| Block | Design | Paths |
|---|---|---|
| A core | 8 cells × g {0, 1e-5} × memory {dephasing-only, T1 = T2, T1 = T2/2} | 256 |
| B fleet law | 8 cells × {t3, mixlow, mixhigh}, dephasing, g 1e-5 | 96 |
| R rare faults | 8 cells, each path faulted with probability 0.05 (2-sd drop at a random time) | 192 |
| C always-fault | 8 cells | 64, **exploratory** |

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_v21.py` | `3cbf3be8649677da` |
| `drift_queue_des_c2.py` | `0832684b21aebdb9` |
| `tasks_c2.jsonl` | `7b176bfbe7bebda8` |
| `analyze_c2.py` (locked; tested on synthetic data) | `cbab5fff127a1004` |

C2 also uses `drift_queue_des_c1.py` (070acce4) and the v4–v20 modules unchanged.

## Hypotheses (groups need ≥ 200 deliveries)

| | Bar |
|---|---|
| **C2-A1** (primary) | Block A: r ≤ 1% in every group. **At risk: SiV.** |
| **C2-A2** | Block A: path-bootstrap 95% upper bound ≤ 1% |
| **C2-B** | Block B: r ≤ 1% in every group |
| **C2-R** | Block R: r ≤ 1% in every cell |
| **C2-C** (exploratory) | Post-fault r reported. Expected unsafe in several cells. |
| **D** | Fraction of oracle (the throughput cost of v21 vs C1) |

**Commitment.** No further re-tuning. Whatever C2 shows, the paper reports both C1 and C2, and both failures and passes go in the abstract-level summary.

**PSC.** 16 shards × 32 cores × 50 min, so the ceiling is 427 SU; expected about 260–300 SU.
