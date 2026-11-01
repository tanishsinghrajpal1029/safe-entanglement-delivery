# Study 37 pre-registration: SiV–SiV and 29Si–29Si entanglement records, Harvard (Knaut et al., Nature 2024)

**Status:** frozen when this file, `analyze_37.py`, `cert.py` and `HASHES_PREREG_37.txt` are pushed to the public repository, **before any data value is read** (draft 1 Nov 2026).
**Data:** provided by Y.-C. Wei (Lukin group, Harvard) on 31 Oct 2026; private; not redistributed; results shared with the authors before any submission. Cite Knaut et al., Nature 629, 573 (2024) and "data provided by Y.-C. Wei and M. D. Lukin".

## 0. Exposure before this pre-registration (complete list)
- File names, sizes, extensions and `.npy` headers (shape, dtype) of the shared folder.
- Code and markdown cells of the six shared notebooks; all saved outputs stripped unread.
- The public paper and supplement (published fidelities, error budgets, T2 values, rates).
- **Not opened:** any data value, `.txt` log, `.png` plot, `.json` metadata value, pickled cache or the authors' `analysis results/*.pkl`.

## 1. Datasets
| Key | Folder | Settings | Use |
|---|---|---|---|
| EE | `electron-electron entanglement/mu-sweep` | 5 runs, AOM voltage 1.20–1.41 (μ sweep) | Stage 1; certificate coverage; over-dispersion |
| NH | `nucleus-nucleus entanglement/hold` | hold 10 ms (XY8-1), 250/500/750/1000 ms (XY8-128) | Stage 1; memory-model offset |
| NT | `nucleus-nucleus entanglement/telecom` | 0, 10, 20, 30, 40 km spools | descriptive |
| NL | `nucleus-nucleus entanglement/link` | deployed 35 km loop | not analysed (the shared N–N notebook has no configuration for it; see §4) |

Run ids, thresholds, contrast cuts, error-detection flags and file groupings are **exactly those in the authors' notebooks** (`YC_2026_E-E_musweep_analysis_new_new_dyn.ipynb`, `N-N_hold_telecom_analysis_new_eff_dyn.ipynb`): dynamic readout threshold, contrast post-selection on, chunk 1000 (EE) / 500 (NN). We change none of them.

## 2. Stage 1: reproduce the published numbers (gate; fixes conventions)
Using the authors' own functions and settings, compute F for each herald sign. Their code counts a herald when the APD count is odd (a bitwise AND with a Boolean mask); we replicate this exactly and report it.
- **G1 (EE):** at least one EE run gives F(Φ−) within 2 s.d. of **0.86(3)** and F(Φ+) within 2 s.d. of **0.74(3)** (Fig. 2b, μ = 0.017). The run(s) that match define "the published EE run"; all five runs are reported.
- **G2 (NH, 10 ms, XY8-1, Φ−):** F^ED within 2 s.d. of **0.77(5)** and F^raw within 2 s.d. of **0.64(5)** (Fig. 3b). This fixes the herald-sign mapping and the error-detection convention for NH.
- **G0 (our bookkeeping):** our per-herald records, built from the readout thresholds and contrasts that the authors' own functions compute (recorded in call order), must reproduce the authors' Bell-count tables **exactly**, for every EE run and the NH 10 ms setting, with at least one herald each. Stage 2 runs only if G0 passes.
- The herald sign is taken as the code labels it: APD2 → Φ− ("minus"), APD1 → Φ+ ("plus"). We do not swap labels after seeing results.
- (s.d. = the published one, combined in quadrature with our binomial s.d.)

**If a gate fails, the tests H1–H4 are not run for that dataset** (G1 → EE parts of H2, H3, H4; G2 → H1 and the NH part of H2; G0 → all of Stage 2). The descriptives D1–D3 are still reported, labelled as such. We report the failure, ask the authors one specific question, and add a dated amendment before any Stage 2 analysis.

## 3. Stage 2 hypotheses
Levels: α = 0.05; one-sided Clopper–Pearson (CP) unless stated; bootstrap B = 20,000, seed 3037; resampling unit = herald event within a run (pairs are not independent of the link state; reported as a limitation).

**H1 (primary, memory-model offset, NH).** Model fixed now from the paper (Table S4): pure dephasing with exponential (Markovian) decay, XY8-128 T2 = 2.11 s (node A) and 2.10 s (node B). Anchored at the 250 ms point, the prediction for t = 500, 750, 1000 ms is
F_pred(t) = ½·P_ZZ(250) + [F(250) − ½·P_ZZ(250)]·exp(−(t − 250 ms)·(1/T2A + 1/T2B)),
using the error-detected Φ− data. Offset Δ(t) = F_pred(t) − F_meas(t). Report Δ(t) with 95% bootstrap intervals (heralds resampled independently at the anchor and at each t) and a pooled offset (inverse-variance weights from the bootstrap variances).
- **Prediction (registered):** the pooled 95% interval contains 0 (the published model is not detectably optimistic). Pass/fail is reported; the upper bound on Δ is what a guard would declare.

**H2 (primary, calibration noise beyond chance, EE and NH).** For each EE run and each NH setting (error-detected heralds): (i) ZZ error rate across 10 equal-count blocks of Z-basis heralds in time order; (ii) heralds per shot across 10 equal-shot blocks. Pearson χ² (df = blocks − 1). With fewer than 20 Z-basis heralds, or if any expected cell count is still below 5 after merging adjacent blocks (10 → 5), the test is reported as NA and not counted.
- **PASS (over-dispersion detected) if** min p × (number of valid tests) < 0.05 (Bonferroni).
- **Prediction:** PASS (as ICFO, USTC, Oxford).

**H3 (primary, certificate validity, EE published run and pooled EE).** Test-or-keep is simulated: each herald is labelled "test" with probability p ∈ {0.1, 0.2} by a seeded random draw independent of all data (1,000 draws per p; seeds 37001–38000). The basis is the experiment's own (X, Y, Z cycled by shot index; not hidden; disclosed). On the tested pairs we run the paper's anytime certificate (Prop. C1, mixture over ν, level α) for the target Bell state of each herald sign. Reference: the kept pairs' own measured outcomes. Their fidelity is bounded above, conservatively, by U = 1 − ½ Σ_B CP_lower(e_B) with each per-basis CP bound at level 0.025/3.
- A draw **violates** if the certificate's final lower bound exceeds U.
- **FAIL (certificate falsified) if** the one-sided CP95 lower bound on the violating-draw rate exceeds 0.05.
- **Prediction:** PASS. (Draws share the same pairs, so the violation rate across draws is descriptive of one dataset, not 1,000 independent tests; disclosed.)

**H4 (secondary, usefulness).** At p = 0.1 and 0.2, report the median final certificate and the share of draws in which it exceeds 0.5 (entanglement) and 0.8 (the paper's SiV threshold). The certificate can be below 0 when kept pairs are few; values are reported unclipped. **Prediction:** above 0.5 in most draws for Φ−; rarely above 0.8.

**D1–D3 (descriptive).** F and heralds per EE run (μ sweep); raw and error-detected F at every hold time; raw and error-detected F at every fibre length (NT). If the telecom analysis fails, the failure is reported.

## 4. Assumptions and limits (stated now)
- Measurements are trusted; readout is not corrected (raw thresholded counts, as in the authors' notebooks).
- The test/keep split is ours and post hoc; the basis cycle is deterministic and known; every pair was measured, so "kept" pairs are a random subset of measured pairs.
- Post-selection on local contrast uses neighbouring shots; it is part of the authors' pipeline and is kept.
- Herald events within a run share link conditions, so bootstrap and χ² treat heralds as exchangeable within blocks.
- One device pair; data from 2023.
- The deployed-link data (NL) are not analysed: the shared N–N notebook contains no configuration for them, and choosing one ourselves would be a free choice after seeing the folder.

## 5. Analysis code
- `analyze_37.py` executes the authors' functions directly from their two notebooks (EE cells 0, 1, 3–15 and configuration cell 17; N–N cells 0, 1, 3–16 and configuration cells 18 (hold) and 22 (telecom)). The notebooks are not redistributed; their sha256 values are frozen in `HASHES_PREREG_37.txt` and printed by every run.
- The certificate is `cert.py`, unchanged from `study27_certification/cert.py`.
- Tested only on **synthetic data written in the real file layout** (`--synthetic`): G0 passed (our per-herald records reproduce the authors' counts exactly) and every Stage 2 path ran. Two switches exist for that testing only and are never set for the real run: `S37_TEST_SMALL` (500 resamples, 100 draws) and `S37_TEST_FORCE_GATES`. The output states if either is set.
- Seeds: bootstrap 3037; test-or-keep draws 37001–38000. Bootstrap B = 20,000.

## 6. Order
1. Tanish reviews this draft. 2. Script written and tested on synthetic data. 3. Pre-registration + script hash pushed publicly. 4. Stage 1, then Stage 2, on the Mac. 5. Results to Y.-C. Wei before any submission.
