# Study 38 pre-registration: the delivered-pair certificate on a kilohertz ion–SiV link

**Status:** frozen when this file, `analyze_38.py`, `cert.py` and `HASHES_PREREG_38.txt` are pushed to the public repository, **before any data value is read** (written 1 Nov 2026).

## 1. Data
- Hartung, Barral, … Monroe, … Robens, Levonian, *Quantum Networking at the Speed of Quantum Computation: Kilohertz Entanglement in a Heterogeneous Quantum System*, arXiv 2610.10705 (2026). Published: F = 87.9(7) % to Φ+ (maximum-likelihood tomography), rate 1.032(11) kHz.
- Public data and code: github.com/ionq-publications/khz-heterogeneous-entanglement, Apache-2.0, **commit 8a08f695fca8aff540e85cd8a14b25b25927e82f**. The script stops if the local copy is at another commit or its tracked files were modified.
- Runs: **64563** (Fig. 1, full tomography) and the six Fig. 2 trade-off runs **69967, 69963, 69977, 69969, 69971, 69974** (XY8-1, -2, -3, -4, -8, -16). Each: 9 settings × 1,000 heralded pairs, with per-herald ion and SiV outcomes, attempts until success, and start/readout timestamps.

**What we saw before freezing (exposure record):** the README, `run_ids.py`, the file tree, the authors' analysis code (`src/`, and the fidelity and rate code in `notebooks/figure_1_tomography.py` and `figure_2_rate_fidelity.py`), and HDF5 structure only (dataset names, shapes, data types, setting labels). We did **not** view any data value, anything in `output/`, or any figure. The published fidelity and rate above are from the paper.

## 2. Definitions
- Outcome o = ion bit + 2 × SiV bit (authors' convention; bit 1 = eigenvalue −1). Heralds with a missing outcome are excluded, as in the authors' code, and counted.
- Target Φ+. A tested XX or ZZ pair is an **error** if its parity is odd; a YY pair, if even. F = (1 + ⟨XX⟩ − ⟨YY⟩ + ⟨ZZ⟩)/4 = 1 − (e_XX + e_YY + e_ZZ)/2, exactly (the authors' Fig. 2 formula).
- Only the XX, YY and ZZ heralds (about 3,000 per run) enter the certificate. The six cross settings are not used. Settings were taken in blocks of 1,000 (not interleaved). This does not affect the final certificate, which depends only on counts, but it means the anytime path in time order is not tested; disclosed.

## 3. Stage 1: gates
- **G0 (all 7 runs):** our own HDF5 parser gives exactly the authors' outcome histograms (their `calculate_histogram_population_and_correlator`) for every setting, and our F equals their Fig. 2 formula to 10⁻⁹, with at least one XX/YY/ZZ herald. Stage 2 runs only if G0 passes.
- **G1 (run 64563):** the authors' maximum-likelihood code (`reconstruct_density_matrix`, 1,000 bootstrap samples, their defaults) gives F within 2 s.d. of 0.879(7), and their rate definition (1 / mean(readout − start)) gives a rate within 2 s.d. of 1.032(11) kHz.
- If G1 fails, H3 and H5 are not run for run 64563; the Fig. 2 runs depend on G0 only (the paper's Fig. 2 values were not read and are not used as gates). We report the failure and amend before any further analysis.

## 4. Stage 2: hypotheses
**H2 (primary, drift within a run).** For each run: (i) successes per attempt across 10 equal-herald blocks in time order (Pearson χ², df = 9; needs every attempt count finite and ≥ 1, otherwise NA); (ii) the error rate in each of XX, YY, ZZ across 10 equal blocks in time order. NA rule as in Study 37: merge to 5 blocks if an expected count is below 5; NA if still below 5 or fewer than 20 heralds. Bonferroni over valid tests.
- **Prediction: drift NOT detected** (min p × tests ≥ 0.05). Each run lasts about 9 s at 1 kHz; earlier detections (ICFO, USTC, Oxford, Harvard) were in runs of minutes to hours.

**H3 (primary, certificate validity).** For each run, each herald is labelled "test" with probability p by a seeded draw independent of the data (1,000 draws per p, seeds 38001–39000). The certificate is the paper's anytime bound (Prop. C1, `cert.py`, α = 0.05) on the tested pairs. Reference: U = 1 − ½ Σ_B CP_lower(e_B) on the kept pairs, each per-basis CP bound at level 0.025/3. A draw **violates** if the certificate exceeds U.
- Primary cells: 7 runs × p ∈ {0.1, 0.2}; p = 0.5 is secondary.
- **FAIL (falsified) if** in any primary cell the one-sided CP95 lower bound on the violation rate exceeds 0.05.
- **Prediction:** PASS. (Draws share the same pairs; disclosed.)

**H5 (primary, usefulness predicted in advance).** For run 64563 at p = 0.2, the median final certificate over the 1,000 draws falls inside the 10–90 % band of the certificate simulated from the **published** F = 0.879 at the run's actual number of XX/YY/ZZ heralds N. Simulation: tests ~ Binomial(N, p), errors ~ Binomial(tests, 2(1 − F)/3), 2,000 draws, seed 3800. At N = 3,000 this band is **[0.788, 0.843], median 0.817** (computed 1 Nov 2026 from the S37-D design curve).
- PASS if inside the band. p = 0.1 and 0.5 are secondary (bands [0.746, 0.829] and [0.816, 0.851] at N = 3,000).
- **Prediction:** PASS. A median certificate ≥ 0.8 would be the first time our certificate guarantees the SiV threshold on real data.

**D1 (descriptive).** Per run: F (linear), e_XX, e_YY, e_ZZ, rate, number of heralds; the MLE fidelity for run 64563; share of draws above 0.5 and 0.8 for every cell.

## 5. Analysis code
- `analyze_38.py` imports the authors' functions from their repository (`src/`) for the gates only. Their code is not copied into ours; the data are not redistributed (Apache-2.0 would allow it; we link instead).
- Tested only on **synthetic data written in the real file layout** (`--synthetic`): G0 passed and every Stage 2 path ran. Test-only switches `S38_TEST_SMALL` (100 draws) and `S38_TEST_FORCE_GATES` are never set for the real run; the output states if either is set.
- Run order: Stage 1 (`--stage 1`), then Stage 2 (`--stage 2`, which repeats Stage 1). Both on the same machine and Python.

## 6. Limitations (stated in advance)
- One device pair and one day of data. Runs are short (about 9 s each), so H2 cannot speak to slow drift.
- Settings are blocked, not randomly interleaved, so the test of the anytime property in time order is out of scope.
- H3 has limited power: U is conservative.

**Citation:** Hartung et al., arXiv 2610.10705 (2026); data © IonQ, Inc., Apache-2.0. Results will be sent to the authors (C. Robens) when complete.
