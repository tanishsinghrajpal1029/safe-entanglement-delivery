# Study 18C P1: safety phase diagram versus fleet identifiability (pre-registered 7 Oct 2026, before any confirmatory run)

**Purpose: characterization, not rescue.** P1 maps *where* the frozen C2 controller (v21 'm123') is safe, as a function of how much calibration information it has. It turns the SiV boundary into a quantitative, theory-predicted law.

## Theory (Proposition 3, THEORY_NOTE v3)

The fleet prior is calibrated only if the fleet spread s is identifiable. Take K fleet windows per link (K·L observations), each a noisy look at λ:

- window noise σ_w² = 4p(1 − p)/(n r²), with n = ρRT pairs per window;
- plus the unknown drift phase, A²/12.

The method-of-moments relative precision of s² then defines the **identifiability index**

  **I = √(KL/2) / (1 + (σ_w² + A²/12)/s²).**

**Already observed** (not a prediction): SiV I = 0.72 (C1 failed, C2 abstained); NV 3.73; ion cells 2.37–9.08 (all pass in C2).

## Design

| | |
|---|---|
| Hardware | SiV-like L1 τ 0.80, and NV-like L1 τ 0.80 |
| Fixed | g ≈ 0 (no drift), dephasing-only memory |
| Window T | {50, 100, 200, 400} s (controller window = fleet window length) |
| Fleet windows K | {16, 64, 256, 512} |
| Paths | 256 fresh per group (seeds 19021–19023) |
| Size | 32 groups, **8,192 tasks**; I spans 0.13–12.3 |

**Dev smoke test** (seeds 20011–20013, 3 tasks): runtime only.

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_p1.py` | `c7a3b36db75e490d` |
| `tasks_p1.jsonl` | `fd18cd8c127600f4` |
| `analyze_p1.py` (locked; tested on synthetic data) | `f36f97895daafda0` |

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **P-1** | Identifiable fleets are safe | Every tested group with I ≥ 3 has r ≤ 1% |
| **P-2** | No free lunch below identifiability | No group with I < 1 is *both* safe (r ≤ 1%, ≥ 200 deliveries) *and* useful (≥ 5% of oracle) |
| **P-3** | Descriptive | Violation rate, max r and ŝ/s by I band, which locates the empirical threshold I* |
| **P-4** | Descriptive | Fraction of oracle versus T and K |

**PSC.** 8 shards × 16 cores × 20 min, so the ceiling is 43 SU; expected about 5–15 SU. About 642 SU charged so far, of the 1,000 approved.
