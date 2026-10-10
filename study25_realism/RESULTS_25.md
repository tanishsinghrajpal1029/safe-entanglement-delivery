# Study 25 ("realism"): confirmatory results (11 Oct 2026)

**What this study tests:** whether the guard stays safe under model error, finite calibration, shared noise, network load and drift re-alignment (referee weak spots 2, 3, 4, 5b, 7).

**What was run**
- **Pre-registration:** `README_25.md` (b9c1718a), public in commit `370a823`. Release v0.1.4 has DOI 10.5281/zenodo.23289143.
- **Code:** study25.py ecccd63c · study25b.py 1b234c47 · analyze_25.py 47ef235e (run unmodified).
- **PSC jobs:** arrays 49020121 (A) and 49020122 (D).
- **Run outputs (`runs.csv` sha256):**

  | Block | sha256 | Rows |
  |---|---|---|
  | A | `3826490aaf20734b` | 5,760 (expected 5,760) |
  | D | `7bb3996c177a281d` | 3,456 (expected 3,456) |

**Timing** (PSC clock; ledger E102 and its two addenda)

| UTC | Event |
|---|---|
| 22:56:16 | Locked files on the cluster |
| 22:56:52 | Array A submitted |
| 22:57:08 | Array A starts |
| 22:58:56 | Commit `370a823` |
| 23:01:15 | First shard completes |
| 23:01:51 | Array D starts |

## Hypotheses

| | Result | Key numbers |
|---|---|---|
| **M1** declared D ≥ κ keeps `kg` safe (30 cells) | **PASS** | 0 bad in 1,210,048 |
| **M2** undeclared κ = 0.5 breaks the per-path bound (ion2020, D = 0) | **PASS** (prediction confirmed) | 831 bad pairs; r 0.62%; **15.4% of paths with a bad pair** |
| **K1** campaign arms safe (12 cells) | **PASS** | 0 bad in 494,670 |
| **K2** SiV campaigns with I ≥ 3 recover ≥ 80% of kg − bg | **PASS** | K = 64: 0.876 · K = 256: 0.988 · K = 1024: 0.947 (and K = 16: 0.878). kg − bg = 21.9 points |
| **T1** all six arms safe at c ≤ 0.5 (36 cells) | **PASS** | 0 bad |
| **T2** declared φ restores safety (18 cells) | **PASS** | 3 bad in 844,685 (all NV, c = 2); max 0.23% of paths bad; worst bootstrap upper bound 0.33% |
| T3 (secondary) AI prior adds ≤ 2 points of bad paths vs `kg` at c = 2 | **FAIL** | NV: ag2t 5.05% vs kg 2.93% (+2.12). ag2 itself passes on every hw: ion2020 1.73 vs 1.48; NV 2.58 vs 2.93; SiV 0 vs 0.42 |
| **C1** bg, kg, ag2 safe under parallel load and signalling delay (48 cells) | **PASS** | 0 bad in 7,311,518 |
| C2 (secondary) thin-hardware gain under par4 ≥ 10 points with LB > 0 | **PASS** | +26.5 points; 90% two-sided CI [+23.6, +29.5] (its lower end is the pre-registered 95% one-sided LB) |
| **D1** declared bound safe when B ≥ 3 sd (20 cells) | **PASS** | 0 bad in 6,220,215 |
| **D2** gb0.005 recovers ≥ 40% of the restart cost | **PASS** | ion2020 0.611 · ionproj 0.625 |
| D3 (secondary) broken promise (Djb, B = 0.005) gives bad pairs | **CONFIRMED** | 1,425 / 4,065 bad; 11.7% / 8.4% of paths bad |

**Summary:** 9 of 9 primary hypotheses PASS. Of the 3 secondary hypotheses, 2 PASS/CONFIRMED and **1 FAILS (T3)**.

## What it means (for the paper)

**1. Model error (weak spot 2).**
- The guard's guarantee is only as good as its physics model.
- Undeclared optimism breaks the per-path bound on ion2020: 15% of paths at κ = 0.5 and 0.8% at κ = 0.25. The pooled r stays below 1%, which is why the per-path metric matters.
- Declaring D ≥ κ restores 0 bad pairs everywhere.
- Cost of declaring D = 0.5 on ion2020: 81.3% → 74.7% of oracle (about 7 points). On NV and SiV the cost is within noise.
- NV and SiV stayed safe even with no declared margin. Their thresholds already leave margin.
- The unguarded controller (`b`) exceeds r = 1% on NV and SiV even at κ = 0, and on ion2020 already at κ = 0.1. The guard is needed regardless.

**2. Finite calibration (weak spot 3).**
- The "known fleet law" can be replaced by a short campaign:
  - estimates are unbiased;
  - the spread ratio is 1.00 ± 0.03 at K = 1024 and 0.97 ± 0.22 at K = 16;
  - all campaign arms are safe.
- Even K = 16 (I = 2.1) recovered 88% on SiV, so the Prop. 3 rule of I ≥ 3 is conservative.
- On NV, `c16` (22.1%) beat `kg` (18.8%). A noisy prior changes efficiency, never safety (Prop. 7). The NV gain kg − bg is small (2.3 points), so recovery fractions there are not meaningful.

**3. Shared measurement noise (weak spot 4; Prop. 10).**
- Strong common-mode noise (c = 2) over-disperses every link's own counts. It breaks **every** non-declaring guard, AI or not.
- On NV, every non-declaring arm exceeds a safety bar: bootstrap upper bound > 1% for bg, kg and ag2, and r > 1% for kg and ag2t.
- Declaring the fleet-average φ restores safety, with 3 residual bad pairs: the quasi-likelihood correction is approximate, as pre-registered.
- **Cost on thin hardware is severe.** SiV under declared φ drops to about 1.3–1.4% of oracle, from 17–19%. On thin hardware under strong shared noise, safety costs nearly all throughput.

**4. T3 failed, honestly.**
- The time-split arm `ag2t` was worse than `kg` on NV by 2.12 points against a 2-point margin. That is 43 vs 29 bad pairs over 32 networks, a small-count difference.
- The deployed AI arm `ag2` passed on every hardware.
- We do not claim that the time split helps. It cost 2–4 points of throughput at c ≤ 0.5 and did not reduce failures at c = 2.

**5. Network model (weak spot 7).**
- Parallel service at 4× load and 50 km/hop signalling: 0 bad in 7.3M deliveries.
- The AI gain on thin hardware survives load: +26.5 points. On NV, ag2 delivers about 2× kg.
- Latency:
  - parallel service cuts SiV mean end-to-end latency from about 25 s to 5.5–7 s, and NV from about 1.2 s to 0.5–0.6 s;
  - on ions the guard adds no measurable latency: ag2, bg and kg are within 0.0002 s.
- At ion load, parallel and serial service deliver nearly identical counts: requests rarely overlap, and queue wait does not consume qubit memory. Only latency changes.

**6. Re-alignment design curve (weak spot 5b; Prop. 9).**
- Declaring |θ_c − θ_{c−1}| ≤ B buys back 61–63% of the restart cost at B = 0.005.
- It is safe in every cell where the promise holds. The per-network check (D4) gave 0 bad in every network whose realised jump was ≤ B.
- Broken promises give bad pairs, as predicted. So does `gpersist` under jumps (55 / 139 in Dj).
- At B = 0.16 the guard equals `gexact`, so the curve interpolates between the two.

## Limits
- All of this is simulation on the G-series 5 × 5 grid.
- φ is declared as a fleet average and is approximate.
- κ and B are declared by the operator. The guard cannot detect undeclared model error. That is the content of Prop. 8 and of M2.
