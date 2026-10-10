# Study 23: a global AI model and an RL router under the safety guard (pre-registered 10 Oct 2026, before the confirmatory run)

**Plan and stop rules:** `PLAN.md`.
- **Go/no-go #1 (AI model accuracy): PASS** (E84).
- **Go/no-go #2 (pilot): PASS.** `ag` or `arg` beat `bg` by ≥ 2 points on correlated networks in 3 of 4 correlated cells (details below).

## Setup

**Network.** The G-series 5 × 5 grid: best route among the shortest paths, exact physics, stationary links.
- Link qualities are spatially correlated (`corr_net.py`), with ρ = 0.7 (correlated) or 0 (independent control).
- Calibration data are either **dense** (ρ_cal = 0.3, ~5,500 parity checks per link per 100-s epoch) or **thin** (ρ_cal = 0.03).
- Hardware: ion2020 and ionproj.

**Global AI model** (`ai_weights_<hw>.npz`):
- An MLP (32-32) that predicts a link's quality from its **neighbours'** latest calibration window only.
- Trained offline on separate simulated networks (seeds 100000–121499).
- It always assumes ρ = 0.7, so in the ρ = 0 cells it is deliberately mis-specified.

**AI-informed guard** (Prop. 6 with an informative mixing prior):
- Mixing prior: a Gaussian around the AI's prediction, frozen at the end of warm-up from neighbours' data only. That makes it independent of the link's own counts given the link qualities.
- The per-path guarantee P(ever deliver a bad pair) ≤ α is unchanged.

**RL router:**
- A linear scoring policy over the candidate paths.
- Learned by the cross-entropy method on separate training networks (seeds 50000+) on PSC (`train_rl.py`; 8 configurations; theta frozen in `policy_<hw>_<data>_<rg|arg>.json`).
- On fresh training networks, the learned policies beat greedy routing by −0.1 to +1.4 points.

## Arms

| Arm | Belief | Router | Guard |
|---|---|---|---|
| `b` | fleet prior | greedy | none |
| `bg` | fleet prior | greedy | Beta(½, ½) mixture (G2) |
| **`fg`** | fleet prior | greedy | **fleet-informed Gaussian mixture** (new control: an informed guard prior *without* AI) |
| `ag` | AI prior | greedy | AI-informed mixture |
| `rg` | fleet prior | RL | Beta mixture |
| `arg` | AI prior | RL | AI-informed mixture |
| `ar` | AI prior | RL | none |

**Design:** 2 hw × 2 ρ × 2 data regimes × 7 arms × 64 networks = **3,584 tasks**. Networks are paired across arms. Fresh seeds 19231–19234.

## Pilots (disclosed)

**PSC dev pilot** (seeds 20231–20234, 8 networks per cell, all arms except `fg`). Gain in fraction of oracle over `bg`, in points:

| Cell | ag | rg | arg |
|---|---|---|---|
| ion2020 ρ0.7 dense | +1.30 | +0.42 | +1.73 |
| ion2020 ρ0.7 thin | +3.33 | +0.01 | +2.67 |
| ionproj ρ0.7 dense | +2.53 | +0.21 | +2.99 |
| ionproj ρ0.7 thin | +5.38 | +0.56 | +6.26 |
| ρ = 0 cells (AI mis-specified) | −0.05 to +2.99 | −0.08 to +1.01 | +0.18 to +4.19 |

Guarded arms had **0 bad pairs** in every cell. The no-guard arms (`b`, `ar`) had 0.43–1.07% bad pairs, with 4–24% of paths receiving at least one.

**Cloud check of the new `fg` control** (same dev networks, 3 per cell, 6 cells completed):
- `fg − bg` = −0.6 to +2.3 points;
- `ag − fg` = **+0.25 to +0.77** on correlated cells and **−0.5 to −0.7** on independent ones.

**What the pilots suggest, stated before the run:** much of the AI arms' gain over `bg` comes from giving the guard *any* informed prior. The AI's own contribution (learning correlations) is smaller, about +0.5 points. That is why H3 compares `ag` with `fg`, not with `bg`.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `study23.py` | `10f75e0ec5711e85` |
| `analyze_23.py` (locked; tested on synthetic data) | `541ca7422406cbed` |
| `tasks_s23.jsonl` (3,584) | `0c74b19279fc1662` |
| `train_rl.py` | `13f8e0e4e367fb33` |
| `corr_net.py` | `3f6df6215f05861c` |
| `ai_weights_ion2020.npz` | `e3ba6ca7ad0d84d8` |
| `ai_weights_ionproj.npz` | `f7e38bcc687d2498` |

The 8 policy files on PSC are hashed by the run command and recorded in the results.

## Hypotheses

Gains are pooled as the mean over cells of the ratio-of-sums difference in fraction of oracle, with a paired network bootstrap.

| | Question | Bar |
|---|---|---|
| **H1** (primary, safety) | Is every guarded arm safe, including the mis-specified AI? | Every guarded arm (`bg`, `fg`, `ag`, `rg`, `arg`) in all 16 cells: r ≤ 1%, upper bound ≤ 1%, bad paths ≤ 5% |
| **H2** (primary) | Does the full proposal beat today's guarded controller on correlated networks? | `arg` − `bg` ≥ 2 points **and** one-sided 95% lower bound > 0 |
| **H3** (primary) | Does the AI add value beyond an informed prior? | `ag` − `fg` on correlated cells: 95% lower bound > 0 |
| H4 (secondary, control) | Does the AI's advantage vanish when links are independent? | `ag` − `fg` on independent cells within ±1 point |
| H5 (secondary) | Does the RL router add value? | `arg` − `ag` over all 8 cells: 95% lower bound > 0 |
| H6 (descriptive) | What do the other comparisons show? | `fg` − `bg`; risk and bad paths without a guard (`b`, `ar`); fraction of oracle for all arms |

**Commitment.** No re-tuning after the run; every outcome is reported.

**PSC.** 16 shards × 16 cores × 30 min, so the ceiling is 128 SU. Expected about 35 SU.
