# Study 24 results: a better AI under the guard across five hardware types, unseen patterns, latency, and drift restarts (confirmatory, 10 Oct 2026)

**Pre-registration:** `README_24.md` (ledger E88).

**Provenance:**
- Block A: 11,200 / 11,200 tasks, runs.csv sha `71e3cc31467c2efb`, module `7be8c292`, tasks `ea8f322e`; about 60.7 SU.
- Block B: 1,536 / 1,536 tasks, runs.csv sha `9f8633ed3e590f8f`, module `5d24bef6`, tasks `619f6add`; about 14.9 SU.
- Shard metadata hashes match the pre-registration. Both analyses were reproduced on the Mac with identical output.

## Verdicts

| | Test | Result |
|---|---|---|
| **H1** (primary) | Every guarded arm safe, all 25 cells | **PASS.** **0 bad pairs in 34.8M guarded deliveries**, including SiV, NV and the three unseen patterns. Without a guard (`b`), r exceeded 1% in 9 of 25 cells (max 2.2%, SiV), replicating the old SiV failure. |
| **H2** (primary) | Thin hardware rescued: `ag2 − bg` (NV + SiV) ≥ 10 points | **PASS.** **+20.0 points**, 90% CI [+19.2, +20.9]. SiV: +22.5 to +27.5 per cell (from ~4–5% to ~26–32% of oracle). NV: +3.1 to +26.4. |
| **H3** (primary) | The AI's own value: `ag2 − kg`, thin hw, correlated patterns | **PASS.** **+11.4**, [+10.5, +12.3]. NV +10.3 to +25.8; SiV +4.9 to +7.7. |
| **H4** (primary) | Patterns never seen in training: `ag2 − kg`, 15 cells | **PASS.** **+4.4**, [+4.0, +4.8]. Driven by NV and SiV (+4.9 to +25.8); ions −0.2 to +0.7. |
| H5 | No harm on independent links | **PASS.** +1.07, [+0.58, +1.59]; ions −0.24 to +0.12. |
| H6 | AI v2 better than AI v1 | **PASS, barely.** +0.22, lower bound **+0.001**. The pilot predicted FAIL. v2 wins on SiV (+0.4 to +4.6); v1 wins on NV independent links (−8.1). Treat as "about equal, mixed by hardware". |
| H7 | Neural net better than a linear model | **PASS, small.** +0.54, [+0.35, +0.74]. The pilot predicted FAIL. The gain is only on NV and SiV (up to +2.6); ions ≈ 0. |
| **B1** (primary) | `gcarry` safe for any re-alignment jitter | **PASS.** 0 bad pairs in 1.84M. |
| **B2** (primary, Prop. 7) | Carrying the previous cycle buys little | **PASS.** +0.30, [+0.22, +0.38]. The restart cost stays at 12–19 points against no guard. |
| B3 | `gpersist` breaks when re-alignment jitters | **CONFIRMED.** 55 / 204 bad pairs (Dj) and 1,251 / 3,002 (Djb). Under Djb, 7–11% of paths received a bad pair, above the 5% per-path budget. |

## Where the gain on thin hardware comes from (pooled over the 5 patterns)

| Hardware | Informed guard prior (`fg − bg`) | Known fleet law in the belief (`kg − fg`) | AI (`ag2 − kg`) | Total (`ag2 − bg`) |
|---|---|---|---|---|
| **SiV** | +1.8 | **+17.7** | +5.8 | **+25.3** |
| **NV** | +0.8 | +0.4 | **+13.6** | **+14.8** |
| ion2020 | +1.0 | 0.0 | +0.4 | +1.5 |
| ionproj | +2.1 | 0.0 | −0.15 | +1.9 |
| ionfut | +1.0 | 0.0 | −0.08 | +1.0 |

## Reading
1. **The old SiV failure is fixed safely.**
   - Thin-data hardware goes from almost unusable under today's guard (4–5% of oracle) to 26–32%, with 0 bad pairs.
   - Most of the SiV gain comes from **knowing the fleet law** rather than estimating it from thin data (Prop. 3: SiV sits in the I < 1 regime).
   - The AI adds about 6 points on top.
2. **On NV, the AI is the main source of the gain** (+13.6).
3. **On data-rich ion hardware, learning barely matters** (≤ 0.4 points, sometimes −0.15, the hedge's cost). This is Prop. 7: when data are plentiful, the prior's Occam term is small.
4. **Robustness.** The AI's advantage held on three link patterns it never saw. The hedge kept the worst cell at −0.24.
5. **v2 vs v1 and the neural net vs linear:** both differences are small. A simple linear model gets most of the benefit. The paper should say so.
6. **Drift restarts (Block B):** assumption-free carry-over is safe but buys only +0.3 points. Getting more needs an assumption about re-alignment, and `gpersist` shows what happens when that assumption is wrong. This confirms Prop. 7's prediction.

## Latency (advisor's request; descriptive; end-to-end time from request to delivered pair)

| Hardware | Median | 95th percentile | Guard's effect (`bg` vs `b`) | AI's effect (`ag2` vs `bg`) |
|---|---|---|---|---|
| ion2020 | 18 ms | 100 ms | none (same percentiles) | none |
| ionproj | 22 ms | 71–79 ms | 95th 71 → 79 ms; mean 25.5 → 26.5 ms | mean back to 26.3 ms |
| ionfut | 4 ms | 10 ms | none | none |
| NV | 0.9–1.0 s | 4.5 s | none | mean 1.37 → 1.28 s; attempts 1.91 → 1.71 |
| SiV | 14–18 s | 71–89 s | mean 22.0 → 26.2 s (more rejected attempts → more queueing) | mean 26.2 → 25.3 s, while serving 6.5× more requests (1.7% → 10.9%) |

- **Safety costs no measurable latency on ion hardware.** Latency is dominated by entanglement generation and queueing.
- **On SiV, queueing dominates** (about 20 s of the about 25 s).

**Limits of the latency measurement:**
- latencies are for *delivered* requests, so each arm delivers a different set;
- the histogram bins are about 12% wide;
- classical signalling delay is not modelled.

## Limits
- **Simulation only** (G-series grid, stationary links in Block A).
- **The "known fleet law" is an idealisation.** In practice it means a fleet characterised in advance, for example from a separate calibration campaign.
- The AI was trained on the simulator's own physics.
- **Faults are not addressed:** neighbour data cannot reveal a single-link fault (G6/G7 remain the answer).
