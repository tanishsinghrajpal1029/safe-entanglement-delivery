# ICFO 2021 Stage 1 result (10 Oct 2026)

**Pre-registration:** `PREREG_ICFO_STAGE1.md` (f3ebc014; ledger E90).

**Code:** `stage1/icfo_stage1.py`.
- First run with 79a2caad.
- The single allowed decoding fix (E91): a Hydra time-tag glitch, which the authors' own script trims. Fixed script a4d4124c.
- The scipy shim on the Mac VM was validated to 1e−14.

**Output:** `stage1/out_all_fix1.json`.

## Pre-registered verdicts

| | Test | Result |
|---|---|---|
| **R1-A** (primary) | 2 µs visibility ∈ [0.78, 0.90] | **FAIL.** V(rms) = 1.014 ± 0.011, which is unphysical. |
| **R1-B** (primary) | 2 µs F_eff ∈ [0.89, 0.95] | **FAIL.** 1.007 (follows from R1-A) |
| R1-C (secondary) | 2 µs concurrence ∈ [0.80, 1.50]·10⁻² | **FAIL.** 2.64·10⁻² |
| R1-D (secondary) | Concurrence falls with storage time, and C(25 µs) ≥ 5σ (the paper's text claims) | **PASS.** Spearman ρ = −0.90; C = 2.64, 1.06, 1.18, 0.50, 0.35 (·10⁻²) at 2–25 µs; C(25 µs) = 6.2σ |
| R3 (descriptive) | Real-data drift and validity of the anytime bound | Over-dispersion is present in most runs: dispersion ratio 0.73–5.6, and **9 of 12 runs show significant over-dispersion** (p < 0.05). Yet the anytime-valid confidence sequence **never excluded the full-run estimate in 11 of 12 runs** (once, for 1.7% of a 7 µs run). |

## Why R1-A failed (diagnosis, stated as such)
- The primary visibility estimator assumed that the recorded phase settings span the fringe evenly. The pre-registration flagged this as untestable, because phases were not recorded.
- At 2 µs, 5 of the 7 settings sit near the fringe extremes (|E| = 0.72–0.88), so the rms estimator over-shoots.
- It is our estimator's assumption that failed, not the data. The fail stands as pre-registered.

## Matches that were not primary tests

| Quantity | Ours | Paper |
|---|---|---|
| h_c(2) at 2 µs | **0.033** | 0.036(8) |
| p01/p10 ratio (Jerry/Tom) | 2.04 | 2.18, the authors' own heralding efficiencies in `heralding_efficiency_calc.m` |
| Phase-free visibility max\|E\| at 2 µs (exploratory, post hoc) | 0.884 | 84(2)% |
| Per-output concurrence with that visibility (exploratory, post hoc; the paper reports C at one beam-splitter output) | 1.12·10⁻² | **1.15(5)·10⁻²** |

## What this means for our paper
1. **Real hardware drifts.** Echo probability is over-dispersed against an iid model in most long runs. This supports the drift-aware guards (Props. 6′, 6″) as necessary rather than optional.
2. **The anytime-valid bound behaved as designed on real data** (11/12 runs never excluded the estimate). This is the first real-data check of the guard's statistics. It checks the confidence sequence on real counts; it is not a full delivery experiment.
3. **We reproduce the authors' qualitative claims and their two-photon suppression.** The headline visibility could not be pinned down, because the phase settings were not recorded.
4. **Next step, Stage 2** (needs its own pre-registration): ask the authors for the phase settings, or pre-register a phase-free estimator.
