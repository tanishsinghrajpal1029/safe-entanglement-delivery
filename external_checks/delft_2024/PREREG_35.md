# Study 35, "Delft": pre-registration (13 Oct 2026)

**Written before any data value was read.** What had been seen is listed in §2. Commit this file and the locked scripts publicly **before** running `extract_35.py` without `--check`.

## 1. Dataset and question
- **Data:** Stolk et al., *Data and software supporting the publication: Metropolitan-scale heralded entanglement of solid-state qubits*, 4TU.ResearchData, doi:10.4121/983e4771-1d12-457f-a98e-fab3a2959288.v1 (CC BY 4.0).
- **Paper:** doi:10.1126/sciadv.adp6442. Two diamond-spin nodes 10 km apart, linked over 25 km of deployed fibre.
- **The data are not redistributed.** The extract JSON stays on the Mac, outside the repository.
- **Why this dataset:** it is the project's first colour-centre entanglement data. It tests two claims of the manuscript on a new platform:
  - (a) the model-free certificate (Prop. C1) needs **trusted measurements**, and real readout errors are a model of their own;
  - (b) physics models can be **optimistic**, so a guard must declare an *upper bound* on the offset, not a point estimate (USTC, E97).

## 2. What was seen before this pre-registration (E153)
- The README, the file list and sizes, and the **source cells** (not the outputs) of the Figure 2/S7 and Figure 3 notebooks.
- `structure_35.txt`: names, shapes, dtypes and attribute names only. No data value was read and nothing was computed.
- **Disclosed:** the Figure 3 notebook source draws a circle at (10 ns, 0.57) labelled "Circle data used in B". This identifies the main-text window as 10 ns and hints that the data fidelity there is about 0.57. It informs the prediction for S1 below.
- **From the notebook source:**
  - the bases are stored in the order ZZ, XX, YY;
  - `correlation_results[0, state, k]` holds the authors' simulated (model) correlators;
  - `total_result_sweep[window, state, (data, uncertainty, model), k]` holds the sweep over 16 windows from 5 to 20 ns.

## 3. Scope
- **Included:**
  - the Figure 3 main dataset (`dataset_processed_RO_corrected.h5`, the 10 ns window) and its model (`correlation_results.npy`);
  - the two heralded states `state_0` and `state_1`;
  - the window sweep (`total_result_sweep.npy`), descriptive only.
- **Excluded:**
  - `state_2`, which is not plotted in Fig. 3 (its label is logged);
  - Figure 4/S6, a variant with a different correction;
  - the Figure 2/S7 stabilisation time series. Those may become Stage 1b, with its own pre-registration after their column labels are read.

## 4. Gates (in order; a failure stops the run and no hypothesis is scored)
| Gate | Check | Bar |
|---|---|---|
| **G1** | Outcome labels are 00/01/10/11. The labels of `state_0` and `state_1` parse to Bell states. Each state has X, Y, Z data with the same basis at both nodes | All true |
| **G2** | Parity convention: our correlator P(00)+P(11)−P(01)−P(10) from `p` matches the authors' `correlation` attribute | max diff ≤ 0.002 |
| **G0** | Target mapping: F = (1 + Σ s_b c_b)/4, with signs from the parsed labels (Φ+ (+,−,+), Φ− (−,+,+), Ψ+ (+,+,−), Ψ− (−,−,−) in X,Y,Z), matches the authors' `fidelity` attribute | max diff ≤ 0.005 |
| G3 (sweep only) | The sweep at 10 ns reproduces the main-window data fidelity | diff ≤ 0.005; if it fails, S3 is flagged, not dropped |

## 5. Primary hypotheses (2)
**D1: model-free certificate from raw counts.**
- **Method:** pool the raw outcome counts `N` of both heralded states, each scored against its own target. Count the errors per basis (parity ≠ target sign). Take one-sided Clopper–Pearson upper bounds at α/3 per basis (Bonferroni). Then F_lo = 1 − Σ_b e_b^ub / 2, at 95%.
- **PASS** if F_lo > 0.5, which certifies entanglement with no readout or physics model.
- **Assumptions:** within each basis, events are i.i.d. and the readout is trusted as recorded (no correction).
- **Prediction: FAIL.** Raw readout errors shrink the correlators. At a corrected fidelity of about 0.57, the raw fidelity is expected near or below 0.5.

**D2: model offset at the main window.**
- **Definitions:**
  - Δ = F_model − F_data, each averaged over the two states with equal weights (as the authors do);
  - F_data comes from the authors' readout-corrected correlators, F_model from `correlation_results`;
  - u = √(u_data² + u_model²), treating the bases, states, data and model as independent (stated).
- **PASS (model adequate)** if |Δ| ≤ 2u + 0.02 (the USTC bar, E97) **and** optimism is not detected (Δ − 1.645u ≤ 0).
- **Labels:**
  - **"weak test"** if 2u + 0.02 > 0.06;
  - **"underpowered"** if the power to detect Δ = 0.03 is below 0.8; a PASS is then reported as "consistent, underpowered", not as evidence that the model is right.
- If the model uncertainties are not usable (outside [0, 0.2)), u_model is set to 0 and this is flagged.
- **Prediction:** none on the direction.

## 6. Secondary
- **S1:** readout-corrected (model-dependent) bound F_data − 1.645·u_data > 0.5. **Prediction: PASS** (see §2).
- **S2 (descriptive):** the declared margin a safe guard would need, i.e. the one-sided 95% upper bound on Δ.
- **S3 (descriptive):** Δ(w) over the 16 windows from 5 to 20 ns, with pointwise uncertainties. The windows are nested, so their data overlap; **no test, no selection of a "best" window.**

## 7. Controls against false positives
1. **No shopping:** two primary tests, the window fixed in advance (10 ns), the states fixed (0 and 1), Fig. 4 excluded, and the sweep descriptive only.
2. **The data are used once.** There is no pilot on real data. The pre-run is on synthetic data (below).
3. **Gates** catch label, basis-order and sign-convention errors before any test is scored. Tested: a flipped convention stops at G2 and unreadable labels stop at G1.
4. **Calibration on synthetic data** with the same tests (`synth_35.py`, seed 35, 10,000 replicates per cell; output `synth_35.txt`):

| Check | n = 200 | 500 | 1,000 | 3,000 (events per basis per state) |
|---|---|---|---|---|
| D1 false certification at F = 0.5 (worst of three error splits; bar ≤ 0.05) | 0.0001 | 0.0005 | 0.0006 | 0.0008 |
| D1 coverage at F = 0.55–0.70 (bar ≥ 0.95) | 1.000 | ≥ 0.9999 | ≥ 0.9999 | ≥ 0.9999 |
| D1 mean margin F − F_lo | 0.10–0.11 | 0.06–0.07 | 0.04–0.05 | 0.02–0.03 |
| D2 false FAIL with an exact model (≈ α) | 0.049 | 0.046 | 0.046 | 0.050 |
| D2 power at Δ = 0.02 / 0.03 / 0.05 | 0.24 / 0.44 / 0.79 | 0.47 / 0.77 / 0.99 | 0.74 / 0.96 / 1.00 | 0.99 / 1.00 / 1.00 |

**Reading of the calibration:**
- **D1 is conservative,** so a D1 PASS is not a false positive. The price is a margin of about 0.05 at n = 1,000.
- **D2 has a false-FAIL rate of about 5%.** Small offsets (0.02) are often missed below n = 1,000. That is why "underpowered" is a pre-registered label.

5. **End-to-end test** (`make_synth_extract_35.py`): synthetic files in the authors' layout, with F = 0.57, readout fidelity 0.93 per node and a model offset of 0.03.
   - The analysis recovered Δ = +0.029 ± 0.010 and detected the optimism (D2 FAIL).
   - With no offset: Δ = −0.001 (D2 PASS).
   - D1 failed at F = 0.57 and passed at F = 0.62 with n = 3,000, as designed.

## 8. Known limits (stated now)
- **No time-ordered per-event records,** so no anytime certificate, model check or closed-loop test is possible. This is a fixed-sample analysis.
- **The basis is not randomised per pair.** The certificate assumes i.i.d. events within each basis.
- **Readout-corrected numbers depend on the authors' readout model.** That is why D1 uses raw counts.
- **Independence:** treating the model uncertainty as independent across bases may understate u_model.

## 9. Procedure (Mac terminal, in the `labs` environment)
1. Dry run (field names and shapes only): `python3 extract_35.py DATA_DIR --check`
2. Commit and push this file and the locked scripts.
3. `python3 extract_35.py DATA_DIR delft_extract_35.json && python3 analyze_35.py delft_extract_35.json > results_35.txt`
4. Results go to the ledger as reported. Any deviation is labelled exploratory.

## 10. Locked files (sha256, first 16)
| File | sha |
|---|---|
| `delft_core.py` | 290b837d19ddbba4 |
| `extract_35.py` | 61e266e4c795728e |
| `analyze_35.py` | d41418d4e4b6acda |
| `synth_35.py` | d8c1221abf46a875 |
| `make_synth_extract_35.py` | 57544847a6856679 |
| `synth_35.txt` | 7dc15246d46a878d |
