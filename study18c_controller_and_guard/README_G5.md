# Study 18C G5: a cheaper drift-valid guard (pre-registered 9 Oct 2026, before any confirmatory run)

**Why.** In G4 (E76) the drift-valid guard `gdrift` (Prop. 6′) delivered 0 bad pairs but kept only 0.68 (ion2020) and 0.63 (ionproj) of oracle throughput, against 0.85 and 0.95 without a guard. G5 tests whether a tighter, still-valid drift bound recovers part of that cost.

**Where the G4 cost comes from.**
1. `gdrift` treats the counts since the last re-alignment as iid at the *worst* level in the cycle, then subtracts the *worst-case* drift g·(t − t_reset). This is double-counted conservatism.
2. It restarts at every re-alignment and spends α across cycles.

## Two new guards

**`gexact` (Prop. 6″, exact drift likelihood).**
- The drift is a known deterministic offset. Epoch j of the current cycle has parity probability p_j(θ) = (1 + r(θ − g·φ̄_j))/2, where:
  - θ is the link's level just after its last re-alignment;
  - φ̄_j is the epoch-average time since that re-alignment.
- The mixture likelihood ratio M_t(θ) = ∫ Π_j Bin(k_j | n_j, p_j(θ′)) π(dθ′) / Π_j Bin(k_j | n_j, p_j(θ)):
  - is a nonnegative mean-1 martingale under the true θ for any fixed mixing prior π (we use the fleet prior);
  - so CS_t = {θ : M_t(θ) < Lmax/α_c} covers θ at all times (Ville's inequality).
- The bound is λ_now ≥ θ_lo − g·(t − t_reset), which is exact, with no worst-case margin.
- It still restarts each cycle, with α_c = 6α/(π²c²). The guarantee is unchanged: per path, P(ever delivering a bad pair) ≤ α.

**`gpersist` (one confidence sequence for the whole run).**
- The same likelihood, but it assumes every re-alignment restores **exactly the same** level θ.
- It uses no restart and no α spending.
- It is valid only if that assumption holds.

## Scenarios (5 × 5 grid, best routing, otherwise G4)

| Scenario | Truth |
|---|---|
| **D** | G4's sawtooth: g = 1e-5/s, re-aligned every 2,000 s to the same level |
| **Dj** | Same, but each re-alignment restores the level plus an independent jitter N(0, 0.005) per link per cycle (a quarter of the drift amplitude). `gpersist`'s assumption is false here. |

**Controllers:** `cal` (no guard), `gdrift` (G4 reference), `gexact`, `gpersist`.

**Design:** 2 hw (ion2020, ionproj) × 2 scenarios × 4 controllers × 64 networks = **1,024 tasks**. Networks and jitter are paired across controllers. Fresh seeds 19141–19144.

## Dev pilot (disclosed; seeds 20141–20144)

Two networks per cell, except ion2020 D, which had one.

| Cell | cal | gdrift | gexact | gpersist |
|---|---|---|---|---|
| ion2020 D, fraction of oracle | 0.86 | 0.68 | 0.74 | 0.84 |
| ion2020 Dj | 0.85 | 0.65 | 0.72 | 0.80 |
| ionproj D | 0.94 | 0.62 | 0.74 | 0.89 |
| ionproj Dj | 0.96 | 0.63 | 0.78 | 0.91 |

**Pilot safety:**
- `gdrift` and `gexact` had 0 bad pairs in every cell.
- `gpersist` had 0 bad pairs under D.
- Under **Dj**, `gpersist` (ionproj) delivered **10 bad pairs in 14,171**, with 9 of 910 paths bad. ion2020 Dj had 0.

The pilot therefore informs H4. It is stated as a prediction and disclosed as pilot-informed.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `drift_queue_des_g5.py` | `6a3760751656f798` |
| `tasks_g5.jsonl` (1,024) | `084506ae9237a184` |
| `analyze_g5.py` (locked; tested on synthetic data) | `a28effcdded14d6e` |

G5 also uses, unchanged:
- `drift_queue_des_g4.py` `3ac4099bb4badc02`
- `drift_queue_des_g2.py` `b3f90eaa06042f35`
- `drift_queue_des_g1.py` `4cc0016adedf331d`
- the C2 modules.

## Hypotheses (groups need ≥ 200 deliveries; bad paths ≤ 5% means ≤ α of delivering paths)

| | Question | Bar |
|---|---|---|
| **H1** (primary, safety) | `gexact` stays safe | In each of 4 groups (D, Dj × 2 hw): r ≤ 1%, network-bootstrap upper bound ≤ 1%, bad paths ≤ 5% |
| **H2** (primary, cost) | `gexact` is cheaper than `gdrift` | In all 4 hw × scenario cells, paired network-bootstrap 95% lower bound of (fraction of oracle `gexact` − `gdrift`) > 0 |
| H3 (secondary) | Under D, `gpersist` is safe and cheaper still | Safe as in H1 (both hw); point gain over `gexact` ≥ 0 (both hw) |
| H4 (prediction, pilot-informed) | Dropping the restart is unsafe when re-alignment is imperfect | `gpersist` under Dj delivers bad pairs in ≥ 1 hw (no guarantee applies) |
| H5 (descriptive) | Costs | Fraction of oracle, risk and bad-path share for every cell |

**Commitment.** No re-tuning after the run; every outcome is reported.

**PSC.** 8 shards × 16 cores × 30 min, so the ceiling is 64 SU. Expected about 20 SU, since pilot tasks took 45–65 s on one cloud core.
