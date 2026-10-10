# ICFO 2021 Stage 1: blind rebuild + real-data checks (pre-registered 10 Oct 2026, before any visibility or concurrence was computed on real data)

**Dataset.** Lago-Rivera, Grandi, Rakonjac, Seri & de Riedmatten, "Telecom-heralded entanglement between multimode solid-state quantum memories", *Nature* 594, 37 (2021). Zenodo 6454536 (CC BY 4.0), raw time tags.

**What was looked at before this pre-registration** (structure only):
- File names; the authors' MATLAB scripts (`CorrLists2_afc.m`, `CorrLists2_in.m`, `heralding_efficiency_calc.m`).
- Singles rates, file durations and monotonicity on three 2 µs files.
- The herald–signal delay histogram of one 2 µs coherence file, to locate the echo near 2.04 µs.
- **No** s1-versus-s2 split per phase setting, visibility, p_ij or concurrence was computed on real data.

**Reported targets** (arXiv 2101.05097):
- At τ = 2 µs: visibility V = 84(2)% and 84(4)% at the two outputs; h_c(2) = 0.036(8); concurrence at detection C = 1.15(5)·10⁻² (both outputs); F_eff = 0.92(1).
- For 7–25 µs the paper gives no numbers, only text: "concurrence decreases with τ" and "positive concurrence at 25 µs with more than 5 standard deviations".

## Analysis (`icfo_stage1.py`, locked; tested on synthetic data with V = 0.80 recovered as 0.78–0.81)

**Coincidence window.**
- 400 ns (as the paper). Its start is chosen per τ by maximising the pooled (s1 + s2) herald–signal coincidences over starts in [τ − 400, τ + 200] ns, in 20 ns steps.
- This uses only total coincidences, not the s1/s2 split that carries the visibility.
- Accidentals come from a noise window [start + 640, start + 960) ns (as the authors' 2 µs script), scaled to 400 ns.

**Visibility (primary estimator).**
- For each coherence file k: net counts m1k, m2k; output-efficiency ratio r = Σm1/Σm2; contrast E_k = (m1k − r·m2k)/(m1k + r·m2k).
- **V = √(2·mean(E_k²) − 2·mean(Var E_k))**. This assumes the recorded phase settings span the fringe evenly, which the data cannot confirm because phases were not recorded. The assumption is stated, and max|E_k| is reported as a phase-free lower check.
- Per-output fringe visibilities are reported as secondary.

**Probabilities** (diagonal folder):
- p10 = net click probability per herald (both outputs summed) in the *tom* runs; p01 the same in the *jerry* runs.
- h_c(2) = N·n12/(n1·n2) on the both-open runs, from raw window clicks.
- p11 = h_c(2)·p10·p01.
- **C = V(p01 + p10) − 2√p11**, **F_eff = ½(p01 + p10)(1 + V)/(p01 + p10 + p11)** (the paper's formulas, with p00 ≈ 1).
- Uncertainties come from a parametric (Poisson) bootstrap.

## Pre-registered tests

| | Test | Bar |
|---|---|---|
| **R1-A** (primary) | 2 µs visibility | V ∈ [0.78, 0.90] (0.84 ± 3σ of the paper's 0.02) |
| **R1-B** (primary) | 2 µs effective fidelity | F_eff ∈ [0.89, 0.95] |
| R1-C (secondary) | 2 µs concurrence at detection | C ∈ [0.80, 1.50]·10⁻² (±30%: p_ij definitions and accidental handling may differ) |
| R1-D (secondary) | The paper's text claims | Spearman ρ(τ, C) ≤ −0.7 over the 5 storage times **and** C(25 µs)/σ ≥ 5 |
| **R3** (real-data check of the guard's key assumption; pre-specified, descriptive) | Each both-open run, 60-s blocks | Over-dispersion of the per-herald echo-click probability against binomial (dispersion ratio, χ² p-value), and whether the running Beta(½,½) mixture confidence sequence (α = 0.05) ever excludes the full-run estimate |

**R3 prediction.** If the echo probability is stationary within a run, the dispersion ratio is ≈ 1 and the CS almost never excludes the final estimate. If real drift is present (laser, phase lock, memory preparation), we expect over-dispersion. That would show on real hardware why the drift-aware guards (Props. 6′, 6″) are needed.

**How results will be read.** As with Innsbruck: a pass means our pipeline reproduces the authors' headline numbers from raw data. A fail is reported as found, and one decoding fix is allowed only if a bug is found and documented. No re-tuning of the bars.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `icfo_stage1.py` | `79a2caad4791f6b8` |
| `synth_icfo.py` | `fa13fb430f39fb49` |
