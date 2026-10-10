# Study 18C G4: the anytime guard under drift and under physics-model error (pre-registered 8 Oct 2026, before any confirmatory run)

**Why.** In G2 and G3 (E69, E73) the guard delivered 0 bad pairs. That was partly by construction: links were stationary and the controller's physics was exact. G4 removes both conditions, and also tests the obvious remedies.

## Scenarios (5 × 5 grid, best routing, otherwise G2)

| Scenario | Truth | Controller belief |
|---|---|---|
| **D** drift | Each link drifts down at g = 1e-5 /s and is re-aligned every 2,000 s (the C2 sawtooth, amplitude 0.02), with a random phase on the epoch grid | Exact physics; knows g and its own re-alignment times |
| **M** model error | Preset T2 and gate error e; no drift | T2 is 1.25× and e is 0.8× the truth (optimistic) |
| **M50** larger error | Same | T2 is 1.5× and e is 0.6× the truth |

## Controllers

| Name | Scenario | What it is |
|---|---|---|
| `cal` | all | Frozen controller, no guard (reference) |
| `gnaive` | D | G2 guard: accumulates all counts since t = 0 and ignores drift |
| `gdrift` | D | **Prop. 6′ guard** (below) |
| `gnom` | M, M50 | G2 guard computed with the controller's own (wrong) nominal physics |
| `grobust` | M, M50 | Guard evaluated at the worst case of a **declared** uncertainty set: T2 ∈ [0.75, 1]·T2_c and e ∈ [e_c, 1.25 e_c]. Under M this covers the truth (0.94 T2, exactly e). Under M50 it does **not** (1.125 T2, 0.75 e). |

**Proposition 6′ (guard under known sawtooth drift).**
- **Construction:**
  - restart each link's confidence sequence at every known re-alignment;
  - bound the current λ by λ(L) − g·(t − t_reset), where L is the Beta-mixture lower bound from the counts since that re-alignment;
  - spend α over a link's cycles c = 1, 2, … as 6α/(π²c²) per path, so the total is ≤ α.
- **Validity:**
  - within a cycle, every event has λ_e ≤ λ_now + g(t − t_reset);
  - so the parity bits are stochastically dominated (bitwise coupling) by iid bits at that value;
  - the lower bound is monotone in the counts, so it covers that value at all times (Ville);
  - subtracting g(t − t_reset) gives a valid lower bound on λ_now.
- **Conclusion:** for every path, P(ever delivering a bad pair) ≤ α.

**Design.** hw {ion2020, ionproj} × (D: 3 controllers + M: 3 + M50: 3) = 18 groups × 64 networks = **1,152 tasks**. Networks are paired across controllers within a scenario. Fresh seeds 19131–19134.

## Dev pilots (disclosed; seeds 20131–20134; 1–2 networks per group; ion2020 unless noted)

| Group | Delivered | Bad | Bad paths / delivering |
|---|---|---|---|
| D cal (2 networks) | 7,200 | 95 | 54 / 180 |
| D gnaive (2) | 6,726 | 9 | 7 / 107 (6.5%) |
| D gdrift (2) | 6,119 | 0 | 0 / 88 |
| M cal (2) | 7,860 | 314 (4.0%) | 76 / 188 |
| M gnom (2) | 7,202 | **0** | 0 / 121 |
| M grobust (2) | 7,190 | 0 | 0 / 108 |
| M50 cal (ion2020 / ionproj) | 3,952 / 7,895 | 302 / 372 | 58 / 101, 92 / 396 |
| M50 gnom | 3,598 / 7,666 | 14 / 49 | 9 / 66, 37 / 369 |
| M50 grobust | 3,516 / 7,369 | 0 / 0 | 0 / 55, 0 / 365 |

The pilot changed one thing in the plan. The nominal guard survived the 25% error (H3 is now an open question rather than a prediction), and **M50** was added to find where it breaks.

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_g4.py` | `3ac4099bb4badc02` |
| `tasks_g4.jsonl` | `24156666586ce1df` |
| `analyze_g4.py` (locked; tested on synthetic data) | `5c432f4a7cac66a4` |

G4 uses `drift_queue_des_g2.py` (`b3f90eaa06042f35`), `drift_queue_des_g1.py` (`4cc0016adedf331d`) and the C2 modules unchanged.

## Hypotheses (groups need ≥ 200 deliveries)

| | Question | Bar |
|---|---|---|
| **H1** (primary) | Prop. 6′ makes the guard safe under drift | `gdrift`, both hw: r ≤ 1%, network-bootstrap upper bound ≤ 1%, bad paths ≤ 5% of delivering paths |
| **H2** (prediction) | Ignoring drift breaks the guard | `gnaive` delivers bad pairs in ≥ 1 hw |
| H3 (open) | Does the nominal guard survive a 25% optimistic model error? | Reported (no guarantee applies) |
| **H4** (primary) | A declared uncertainty set that covers the truth restores safety | `grobust` under M, both hw: r ≤ 1%, upper bound ≤ 1%, bad paths ≤ 5% |
| H5 (descriptive) | Costs | Fraction of oracle and risk for every scenario and controller |
| H6 (open) | What happens when the declared set does **not** cover the truth (M50)? | Reported for `gnom` and `grobust` |

**Commitment.** No re-tuning after the run; every outcome is reported.

**PSC.** 8 shards × 16 cores × 30 min, so the ceiling is 64 SU. Expected about 12–15 SU.
