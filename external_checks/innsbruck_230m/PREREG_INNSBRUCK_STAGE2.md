# Innsbruck Stage 2: ion-ion data over 230 m, tests of the controller's calibration assumptions (pre-registered 7 Oct 2026, before any ion-ion statistic is computed)

Ledger: E60–E62 (data, Stage 1 PASS, manuscript). This is E63.
What has been looked at so far: file names, headers, scan reports (time stamps, ion-basis flags X/Y), file sizes. No ion-ion outcome, coincidence or rate statistic.

## Structure (from headers only)
9 runs on 20–21 Jul 2021 (Node A folders 1819, 1856, 1920, 2143, 2203, 2243, 2302, 2349, 0014; Node B 182128 … 001652; BSM station time-tag files 2021_07_20_182031 … 2021_07_21_001507). Node A ion basis Z/Z/Z/X/Y/X/Y/Y/X by run; presumably 9 = 3×3 basis pairs, one run each, ~20 min per run. The paper (PRL 130, 050803) reports, at a 1 µs coincidence window, 491 coincidences, 3.1 per minute, F+(1 µs) = 88.2 (+2.3/−6.0)% and F−(1 µs) = 82.2 (+2.5/−6.4)%.

## Step 1: decoding, with a validation gate (G3)
A decoder (blinded: it may compute run totals and the two tomographic fidelities, but NO within-run time-resolved statistic) builds:
- `stage2/events.csv`: run, t_s (herald time, s since run start on the BSM clock), herald ("psi+"/"psi-"), basisA, basisB, a, b (ion outcomes 0/1);
- `stage2/runs.csv`: run, t_start_s, t_end_s.
All choices (coincidence window 1 µs as in the paper, PMT thresholds from histogram minima, synchronisation, ψ± assignment, basis map) are justified from data / readmes / sequence code, logged in `stage2/CHOICES.md`.
**G3 PASS** if: total heralded events within ±10% of 491, AND F+ within 0.06 of 0.882 AND F− within 0.06 of 0.822 (their lower error bars are ~0.06).
One documented decoding-bug fix is allowed after a fail; never a threshold re-tune toward the paper. If G3 fails, Step 2 is not run and we report "ion-ion data not reproducible by us".

## Step 2: hypotheses (analysis script LOCKED: `stage2/analyze_stage2.py`, sha256 dd68ff9ec7de209b…, tested on synthetic data with `stage2/synth_test_data.py`; seed 20261007)
Controller assumptions under test: (i) calibration data arrive as a stationary Poisson stream within a window, (ii) window counts are binomial at a constant rate (no within-window drift), (iii) the Jeffreys/binomial posterior predicts held-out counts.

| | Hypothesis | Test | "CONSISTENT" if |
|---|---|---|---|
| H-d (within) | Heralds are Poisson at a constant rate within each run | pooled dispersion χ² of 60-s bin counts | p ≥ 0.01 |
| H-d (across) | Same rate in all runs | χ² of run counts vs duration | p ≥ 0.01 |
| **H-a (primary outcome test)** | No loss of correlation within a run | van Elteren stratified Wilcoxon (strata = run × herald; informative strata |success − 0.5| ≥ 0.2; success = majority correlation of the stratum) | two-sided p ≥ 0.05 |
| H-a (secondary) | — | CMH early vs late (median split), Fisher-combined exact tests | reported only |
| H-c | Posterior-predictive calibration | Jeffreys from early half → beta-binomial for late half; randomized PIT KS and 90% interval coverage | KS p ≥ 0.05 and coverage inside the binomial 95% band |
| H-b (descriptive) | Size of real drift | From `Calibrations/Unitaries` (polarisation-unitary fidelity vs time during the session): max and median loss between consecutive re-calibrations, compared with the simulator's drift amplitude A = 0.02 in Werner λ (≈ 0.015 in fidelity) | reported only |

## Power, stated before the data (from the locked script on synthetic data shaped like the paper: ~490 events, 9 runs, 18 strata)
- H-a can only detect a relative loss of correlation of about **60–110% within one ~20-min run** (80% power). A synthetic run with an 80% loss was NOT detected in 2 of 2 tries. So "CONSISTENT" on H-a and H-c is **weak evidence**; only a REJECTED would be informative.
- H-d has more power (thinning-type rate drift of 90% across a run was rejected at p = 0.002 in synthetic data).
- Expected reading in advance: this dataset can at most falsify gross non-stationarity; it cannot validate the controller's ≤ 1% risk claims, and contains no deliver/discard decisions.

## Reporting commitment
All four verdicts, G3, the power numbers and H-b go into the ledger and the manuscript, whatever they are.
