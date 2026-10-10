# Study 18C G6: protecting each user after sudden link faults (pre-registered 9 Oct 2026, before any confirmatory run)

**Why.** On single paths (C1/C2) the average stayed ≤ 1% with faults on 5% of paths, but right after a fault the bad share was 2.2–59% in 5 of 8 cells. On networks, the per-path guard (Prop. 6) assumes links do not change. An unannounced fault makes its accumulated counts stale.

**Not run yet.** The PSC run needs a new compute budget approved by Tanish. The account shows 1,233 SU used against the 1,000 SU he approved.

## Scenario (5 × 5 grid, best routing, exact physics, no drift; otherwise G2/G4)

- Each link is faulted independently with probability **0.05**. This matches the 5% fault rate already declared in the controller's prior.
- The fault happens at the start of a random epoch between 4 and 26 (100-s epochs, 30 per run).
- It lowers the link quality λ by:
  - **F2:** 2 fleet standard deviations, the same size as C1/C2;
  - **F4:** 4 standard deviations, the edge of the declared fault range.
- Faults are paired across controllers.

## Controllers

| Name | What it is |
|---|---|
| `cal` | Frozen Bayesian controller, no guard |
| `gnaive` | G2 guard: one confidence sequence per link over all counts. It assumes no faults. |
| `galarm` | **G2 guard plus a per-link change alarm** (details below). |
| `gwin` | G2 guard, plus the pair must also clear τ at a lower bound computed from the last epoch alone. α is split as α/2 to the long-run sequence and α/(2·30) to each one-epoch window. |

**How the `galarm` change alarm works:**
- After each epoch, it compares that epoch's own upper confidence bound with the guard's current lower bound. The upper bound is one-sided Clopper–Pearson at level 10⁻³.
- If the upper bound falls below the lower bound, the alarm fires.
- The alarm discards the link's counts, including the alarming epoch, and restarts its confidence sequence.
- α is spent over restarts as 6α/(π²c²), as in Prop. 6′.

**Built-in limit.** The controller only sees an epoch's counts after the epoch ends. So no method can react during the first epoch after a fault. Post-fault bad pairs are therefore split into:
- **early:** in the epoch the fault happened;
- **late:** in later epochs. This is what an alarm can prevent.

## Dev pilot (disclosed; seeds 20151–20154; 3 networks per group; 28 faults)

| Group | cal: late / early bad | gnaive: late / early | galarm: late / early | gwin: late / early | Fraction of oracle (cal / gnaive / galarm / gwin) |
|---|---|---|---|---|---|
| ion2020 F2 | 12 / 23 | 2 / 4 | **0** / 6 | 0 / 6 | 0.84 / 0.78 / 0.78 / 0.67 |
| ion2020 F4 | 8 / 11 | 13 / 11 | **0** / 7 | 0 / 12 | 0.90 / 0.86 / 0.85 / 0.77 |
| ionproj F2 | 6 / 16 | 1 / 3 | **0** / 8 | 0 / 0 | 0.94 / 0.83 / 0.84 / 0.64 |
| ionproj F4 | 15 / 49 | 4 / 37 | **0** / 43 | 0 / 0 | 0.95 / 0.87 / 0.86 / 0.66 |

`galarm` detected 27 of 28 faults, with a mean delay of 0.5–1 epoch. There was 1 false alarm.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `drift_queue_des_g6.py` | `70769aae4b66680e` |
| `tasks_g6.jsonl` (1,024) | `1f60786441a8fa9a` |
| `analyze_g6.py` (locked; tested on synthetic data) | `a9fa7a461865bd0a` |

G6 also uses `drift_queue_des_g1.py` (`4cc0016adedf331d`), `drift_queue_des_g2.py` (`b3f90eaa06042f35`) and the C2 modules, all unchanged.

**Design:** 2 hw × 2 scenarios × 4 controllers × 64 networks = 1,024 tasks. Fresh seeds 19151–19154.

## Hypotheses

| | Question | Bar |
|---|---|---|
| **H1** (primary) | After the first post-fault epoch, does the alarm guard stop bad deliveries on faulted paths? | `galarm` late post-fault bad ≤ 0.1% of post-fault deliveries (pooled per hw, both hw) **and** fewer than `cal` in every group |
| **H2** (primary) | Is the alarm guard safe overall? | `galarm` r ≤ 1%, network-bootstrap upper bound ≤ 1%, bad paths ≤ 5%, in all 4 groups |
| H3 (secondary) | Does the alarm work as a detector? | ≥ 90% of faults detected; ≤ 1 false alarm per 10 networks |
| H4 (secondary) | Is the alarm cheap? | `galarm` fraction of oracle ≥ `gnaive` − 0.02 in all groups |
| H5 (descriptive) | What does each method miss and cost? | Early vs late bad pairs, throughput and risk for all controllers |

**Expected limitation, stated now.** First-epoch bad pairs cannot be removed by any data-driven method at this data latency. Reducing them needs faster calibration data (shorter epochs), which is a hardware and protocol question.

**Commitment.** No re-tuning after the run; every outcome is reported.

**PSC.** 8 shards × 16 cores × 30 min, so the ceiling is 64 SU. Expected about 10–15 SU. Needs budget approval.
