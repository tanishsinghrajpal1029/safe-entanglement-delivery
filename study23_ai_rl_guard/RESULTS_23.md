# Study 23 results: a global AI model and an RL router under the safety guard (confirmatory run, 10 Oct 2026)

**Pre-registration:** `README_23.md` (locked before this run; ledger E85).
**Run:** PSC Bridges-2 RM-shared, job 49005581, 16 shards × 16 cores; about 34.6 SU (ceiling 128).

**Verified hashes** (shard metadata and Mac re-check):

| Item | sha (first 16) |
|---|---|
| `study23.py` | 10f75e0ec5711e85 |
| tasks | 0c74b19279fc1662 |
| `analyze_23.py` | 541ca7422406cbed |
| `runs.csv` (3,584 rows) | 7c398c48ef653d8b |

The analysis was reproduced on the Mac with identical output. **RL policy files (hashed on PSC):**

| policy file | sha (first 16) |
|---|---|
| policy_ion2020_dense_arg.json | 6215e9a59f91c715 |
| policy_ion2020_dense_rg.json | 7d769df007610230 |
| policy_ion2020_thin_arg.json | 0aca13f790957d23 |
| policy_ion2020_thin_rg.json | ff96e1dbd5d79054 |
| policy_ionproj_dense_arg.json | 5b228f9895b16085 |
| policy_ionproj_dense_rg.json | 83682b4810b9ea87 |
| policy_ionproj_thin_arg.json | 19ef0e88cffd16a5 |
| policy_ionproj_thin_rg.json | 74814064c3976d43 |

These hashes were taken on PSC after the run. **Timestamp check, settled:** all 8 files were last modified on 2026-10-10 between 00:09:21 and 00:13:09 EDT (04:09–04:13 UTC), which is before the run started (15:26:54 UTC). The files were not changed between training and the confirmatory run.

## Pre-registered tests: all pass

| | Test | Result |
|---|---|---|
| **H1** (primary) | Every guarded arm is safe in all 16 cells | **PASS.** 0 bad pairs in 12.3M guarded deliveries over 470k delivering paths, including the mis-specified AI cells. |
| **H2** (primary) | `arg − bg` ≥ 2 points on correlated cells and lower bound > 0 | **PASS.** +3.05 points, 90% CI [+2.75, +3.36]; cells 1.87 / 2.12 / 2.04 / 6.17. |
| **H3** (primary) | The AI's own value: `ag − fg` on correlated cells, lower bound > 0 | **PASS.** +1.07, [+0.83, +1.33]; cells 0.69 / 1.63 / −0.06 / 2.02. |
| H4 (control) | `ag − fg` on independent links within ±1 point | **PASS.** +0.05, [−0.08, +0.17]. |
| H5 | RL adds value: `arg − ag` over all 8 cells, lower bound > 0 | **PASS.** +0.34, [+0.27, +0.41]; 7 of 8 cells > 0. |

## Where the +3.05 points comes from (correlated cells, means of per-cell differences)

| Component | Gain (points) | Share |
|---|---|---|
| Informed guard prior without AI (`fg − bg`) | +1.59 | about 52% |
| AI learning the correlations (`ag − fg`) | +1.07 | about 35% |
| RL router (`arg − ag`) | +0.39 | about 13% |

## Price of safety
- Guard cost against no guard (`b − bg`): 2.3–11.9 points of fraction of oracle.
- `arg` recovers **35–91% of that cost** on correlated cells while keeping 0 bad pairs.
- Without the guard:
  - `b`: r 0.71–1.11%, with 6.6–20.5% of paths receiving at least one bad pair;
  - `ar` (AI + RL, no guard): r 0.53–0.83%, 5.2–20.7% of paths.
  - **AI + RL alone is not safe.** The guard is what makes the learned components safe to deploy.

## Honest limits
1. **The AI is tested in-distribution.** It was trained on the same correlation generator (Gaussian field, ℓ = 1.5) used for testing. The only mis-specification tested is "no correlation" (H4). A different correlation structure or length is untested.
2. **Effect sizes:**
   - the AI's own effect is about 1 point;
   - RL's effect is about 0.3–0.4 points, statistically clear but small;
   - the largest single gain is ionproj thin (+6.17 for `arg − bg`).
3. **H2 per cell:** one correlated cell (ion2020 dense, +1.87) is below 2 points individually. The pre-registered bar is on the pooled gain.
4. **Simulation only:** the G-series grid simulator with stationary links. No drift or faults are combined with the AI in this study.
5. **H3 measures the AI belief and the AI guard prior together** (found while building Study 24, after this run). The AI arms' belief uses a Gaussian with the fleet's true spread, while `fg` keeps the estimated (empirical-Bayes) fleet belief. So part of `ag − fg` could come from "knowing the fleet spread" rather than from learning correlations.
   - The ρ = 0 cells bound this: `ag − fg` = +0.05 pooled (−0.48 to +0.64), because there the AI has nothing to learn.
   - Study 24 adds a direct control (`kg`: known-law belief, no AI).

## Reading
Learned components (a global AI belief model and an RL router) can be added **on top of** the per-path guard:
- they gain throughput where structure exists;
- they cost nothing measurable where it does not;
- the safety guarantee never moves.

The simplest idea, an informed guard prior, gives half the gain. Report it first.
