# Study 25 ("realism"): model error, finite characterisation, shared noise, network load, and re-alignment (pre-registered 11 Oct 2026, before the confirmatory run)

**Why.** These are the referee-facing weak spots from the Study 24 review (items 2, 3, 4, 5b, 7). Theory for items 4 and 5b: Props. 9–10 in `THEORY_NOTE_2026-10-11.md`. Ledger E100–E101.

## Design
All blocks use the G-series 5 × 5 grid with greedy best-path routing, exact physics (PTM) and stationary links (except Block D).
- Calibration counts are pre-drawn per epoch. In Studies 23–24 they were drawn when first requested, so absolute numbers are not comparable across studies. Comparisons within a block are paired: the same network for every arm and configuration.
- Arms `bg`, `kg` and `ag2` are as in Study 24.

**Block M (model error).**
- The controller and the guard both use an **undeclared optimistic** physics model: T2 × (1 + κ) and e / (1 + κ), with κ ∈ {0, 0.1, 0.25, 0.5}.
- The guard may **declare** robustness D ∈ {0, 0.1, 0.25, 0.5}: it evaluates fidelity with T2_model/(1 + D) and e_model·(1 + D).
- Arms: `kg` (all κ × D) and `b` (no guard, all κ). Hardware: ion2020, nv2, siv. Pattern: independent links.
- Fidelity is monotone in T2, e and λ (checked: 0 violations in 1,500 random trials). So D ≥ κ makes the guard conservative.

**Block K (finite characterisation campaign).**
- The known fleet law of `kg` is replaced by moment estimates from K ∈ {16, 64, 256, 1024} dedicated windows. Each window is a random fleet link measured at the full pair rate for 1,000 s.
- Arms: `bg`, `kg`, `c16`, `c64`, `c256`, `c1024`.
- **Prop. 3 identifiability**, computed before the run:

  | Hardware | K = 16 | 64 | 256 | 1024 |
  |---|---|---|---|---|
  | SiV | I = 2.11 | 4.23 | 8.45 | 16.9 |
  | NV | 2.70 | 5.39 | 10.8 | 21.6 |
  | ion2020 | 2.49 | 4.99 | 9.98 | 19.9 |

**Block T (shared measurement noise).**
- Each node adds a common-mode shift to the parity probability of every link touching it, independently each epoch. The link-shift sd is c × the per-epoch binomial sd, with c ∈ {0, 0.5, 2}.
- This **also over-disperses each link's own counts**, by a factor of about φ = 1 + c² at the fleet-average link. So it challenges every guard, not only the AI's (Prop. 10).
- Arms:
  - `bg`, `kg`, `ag2`;
  - `ag2t`: time split, so the confidence sequence uses only own data from after the prior was frozen;
  - `kgphi`, `ag2phi`: the guard declares the **fleet-average** φ = 1 + c² and deflates its counts by φ. This is a quasi-likelihood correction, approximate, not a theorem. Links better than average are slightly under-declared.

**Block C (network model).**
- Conditions:
  - `ser0`: one request at a time, no signalling delay (the old model);
  - `ser50`: 50 km per hop, signalling at 5 µs/km;
  - `par1`: requests served in parallel whenever their links are free, 50 km/hop;
  - `par4`: as `par1` with 4× the request rate.
- Delays add to all storage times, the same for truth, controller and guard.
- Arms: `bg`, `kg`, `ag2`. Hardware: ion2020, ionproj, nv2, siv. Pattern: field.

**Block D (re-alignment design curve, `study25b.py`).**
- `gb<B>`: G5's `gexact` plus the declared bound |θ_c − θ_{c−1}| ≤ B (Prop. 9), with B ∈ {0.005, 0.01, 0.02, 0.04, 0.08, 0.16}.
- References: `cal`, `gexact`, `gpersist`.
- Scenarios: D (exact re-alignment), Dj (jump sd 0.0071) and Djb (jump sd 0.028). Hardware: ion2020 and ionproj.

**Sizes and seeds:**
- Blocks M/K/T/C: 180 configurations × 32 networks = **5,760 tasks** (seeds 19261–19264).
- Block D: 54 × 64 = **3,456 tasks** (seeds 19271–19274).

## Code review (before the pilot) and the pilot (disclosed)
An independent review found and we fixed:
1. Block T's noise breaks every guard. The block was redesigned as above.
2. Block D's jump bookkeeping.

A second review of the fixes and of `analyze_25.py` found no bugs. Minor hardening was added: file-name assertion, denominator checks, and φ wording.

**PSC dev pilot:** seeds 20261+/20271+, 8 networks per cell, code 347344dc/1b234c47. Runs sha be7e239c and 2bdce8f1. The analysis ran on it as a functional test; dev data only. Pilot results:
- **M:** D ≥ κ gave 0 bad pairs in all 30 cells. Undeclared κ = 0.5 on ion2020 gave **11.6% of paths with a bad pair** at D = 0 and 3.3% at D = 0.1. NV and SiV stayed safe even at D = 0. Declaring D = 0.5 costs about 5 points on ion2020.
- **K:** SiV campaign arms recovered 87–98% of the known-law gain (kg − bg = 23 points), even at K = 16.
- **T:**
  - c ≤ 0.5: all arms safe.
  - c = 2: every non-declaring arm had bad pairs, with 1.6–4.6% of paths bad. bg, kg, ag2 and ag2t were similar, so the AI did not add failures.
  - Declaring φ gave 0 bad pairs, at a large cost on SiV and NV.
- **C:** 0 bad pairs in all 48 cells. Parallel service cut SiV latency from about 21 s to about 6 s. The ag2 − bg gain on NV/SiV under par4 was +26.7 points.
- **D:**
  - In D, gb0.005 recovered 57–58% of the restart cost.
  - With B ≥ 3 sd, all cells were safe.
  - Broken promises (Djb, B ≤ 0.02) gave 94–551 bad pairs per cell.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `study25.py` | `ecccd63cb64ab392` |
| `study25b.py` | `1b234c47797e3715` |
| `analyze_25.py` (locked) | `47ef235efdaaeab5` |
| `tasks_s25.jsonl` (5,760) | `971aa98122e93ca7` |
| `tasks_s25d.jsonl` (3,456) | `225607483c6e23fd` |
| `study24.py` / `study24b.py` (unchanged) | `7be8c292` / `5d24bef6` |

`study25.py` differs from the pilot code only in output columns (identical columns in every row) and one comment.

## Hypotheses
**Safety bars**, as in all G-series studies: r ≤ 1%, path-bootstrap upper bound ≤ 1%, and ≤ 5% of delivering paths with a bad pair.

| | Question | Bar |
|---|---|---|
| **M1** (primary) | Does declared robustness keep the guard safe? | `kg` safe in all 30 cells with D ≥ κ |
| **M2** (primary, prediction) | Does undeclared optimism break the per-path bound? | ion2020, κ = 0.5, D = 0: bad paths > 5% |
| M3 (descriptive) | | Full κ × D map; cost of D; risk of `b` |
| **K1** (primary) | Are the campaign arms safe? | All 12 cells |
| **K2** (primary, Prop. 3) | Does a campaign with I ≥ 3 suffice? | SiV: each of K = 64, 256 and 1024 recovers ≥ 80% of (kg − bg) |
| K3 (descriptive) | | Estimation error; K = 16; NV and ion2020 |
| **T1** (primary) | Is every arm safe without strong shared noise? | All six arms at c ∈ {0, 0.5}: 36 cells |
| **T2** (primary) | Does declaring φ restore safety? | `kgphi` and `ag2phi` safe in all 18 cells, including c = 2 |
| T3 (secondary, Prop. 10) | Does the AI prior add failures? | At c = 2, the % of bad paths for `ag2` and `ag2t` is ≤ `kg` + 2 points on every hw |
| T4 (descriptive) | | Time-split cost; φ cost |
| **C1** (primary) | Is the guard safe under parallel load and signalling delay? | `bg`, `kg`, `ag2` safe in all 48 cells |
| C2 (secondary) | Does the thin-hardware gain survive load? | `ag2 − bg`, NV + SiV under par4: ≥ 10 points **and** 95% lower bound > 0 |
| C3 (descriptive) | | Throughput and latency by condition |
| **D1** (primary) | Is the declared bound safe when the promise holds? | `gb<B>` safe in the 20 cells with B ≥ 3 sd of the true jump |
| **D2** (primary, design curve) | Does a tight declared bound buy back the restart cost? | Scenario D: gb0.005 recovers ≥ 40% of the gexact → gpersist gap on both hw |
| D3 (secondary, prediction) | Does a broken promise produce bad pairs? | Djb with B = 0.005: bad > 0 on both hw |
| D4 (descriptive) | | Per-network promise check; the full curve |

**Commitment.** No re-tuning; every outcome is reported.

**PSC:**
- A: 32 shards × 16 cores × 30 min (ceiling 256 SU).
- D: 16 × 16 × 30 min (ceiling 128 SU).
- Expected about 95 SU in total. The pilot used 19.3 SU.
