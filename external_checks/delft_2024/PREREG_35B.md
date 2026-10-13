# Study 35B, "Delft, delivered states": pre-registration (13 Oct 2026)

**Written before any Figure 4 data value was read.** Commit this file and the locked scripts publicly **before** running `extract_35b.py` without `--check`.

## 1. Why
- Study 35 analysed the paper's **Figure 3**, which is post-selected entanglement (E157).
- The object the manuscript is about is **delivered** pairs. Those are the paper's **Figure 4**:
  - fully heralded Ψ− states, with real-time feedback and an echo;
  - a 15 ns herald window;
  - a published fidelity of **0.534 ± 0.015**.
- This stage applies the same two tests to those delivered states.

## 2. What was seen before this pre-registration
- **Paper text:** the 15 ns window and F = 0.534(15) for the delivered states (arXiv:2404.03723).
- **The source cells (not the outputs) of `Figure4.ipynb`:**
  - main-text Fig. 4C uses `dataset_processed_RO_corrected_NoPSBcorrection.h5` and `correlation_results.npy`;
  - the target signs are (−1,−1,−1), i.e. Ψ−, for all three states, and state 2 is labelled "Combined";
  - the Fig. 4D sweep uses `total_result_sweep[:, 2, 0]` as the data (the combined state);
  - the model is the count-rate-weighted average of the state-0 and state-1 models, with weights `total_cps_sweep[:, j, 1]` normalised;
  - the windows are `np.linspace(5, 20, 16)` ns;
  - a circle is drawn at (15 ns, 0.533).
- **`structure_35.txt`:** names and shapes only.
- **Study 35 results (Figure 3, post-selected data),** which come from the same experiment and are disclosed here.
- **Not seen:** no Figure 4 data value.

## 3. Scope
- **Included:**
  - Fig. 4 main-text data without the PSB correction: the h5 file above, `correlation_results.npy`, `total_result_sweep.npy` and `total_cps_sweep.npy`;
  - the combined state (state 2) as "the delivered states".
- **Excluded:**
  - the PSB-corrected supplementary variant (Fig. S6);
  - Figure 2/S7.

## 4. Gates (G1, G2 and G0 stop the run; G3 is a flag)
| Gate | Check | Bar |
|---|---|---|
| **G1** | Outcomes are 00/01/10/11; every state has X, Y, Z with the same basis at both nodes | All true |
| **G2** | Parity convention: our correlator from `p` equals the authors' `correlation` | ≤ 0.002 |
| **G0** | A Ψ− target for all three states reproduces the authors' `fidelity` attributes | ≤ 0.005 |
| G3 | The sweep at 15 ns reproduces the h5 combined fidelity | ≤ 0.005; flagged if not |
| G4 (info) | Combined counts = state 0 + state 1 in every basis | Reported |

## 5. Primary hypotheses (2)
**D1′: model-free certificate from the raw counts of the delivered (combined) states.**
- **Method:** the same method as Study 35 (Bonferroni Clopper–Pearson; `delft_core.certificate`), with a Ψ− target.
- **PASS** if F_lo > 0.5.
- **Prediction: FAIL.** The readout-corrected fidelity is already only 0.534.

**D2′: model offset for the delivered states at 15 ns, as the authors compare them in Fig. 4D.**
- **Definitions:**
  - F_data is the combined-state data at the 15 ns sweep point;
  - F_model is the count-rate-weighted model at the same point;
  - u = √(u_data² + u_model²). Here u_data comes from the sweep, and u_model from `correlation_results[1]` for states 0 and 1, combined with the same weights. If those values are outside [0, 0.2), u_model is set to 0 and flagged.
- **PASS** if |Δ| ≤ 2u + 0.02 **and** Δ − 1.645u ≤ 0.
- **Labels,** the same as Study 35:
  - "weak" if 2u + 0.02 > 0.06;
  - "underpowered" if the power at Δ = 0.03 is below 0.8. A PASS is then "consistent, underpowered".
- **Prediction:** none on the direction.
- **Power, stated now:** with u ≈ 0.015, which the published ±0.015 implies, the power at Δ = 0.03 is about 0.65. **D2′ is expected to be underpowered.**

## 6. Secondary
- **S1′:** readout-corrected bound F_data − 1.645·u_data > 0.5. **Prediction: PASS, narrowly**, from the published 0.534 ± 0.015, which gives about 0.509.
- **S2′ (descriptive):** the declared margin a guard would need, i.e. the Δ upper bound.
- **S3′ (descriptive):** Δ(w) over the 16 windows. Nested windows; no test.

## 7. Controls against false positives
- **The calibration of Study 35 applies unchanged,** because the same `certificate` and `offset_test` functions are used (`synth_35.txt`):
  - D1 false certification ≤ 0.0008;
  - D2 false FAIL about 0.05.
- **End-to-end test** (`make_synth_extract_35b.py`, Fig. 4 layout, 750 events per basis per state, readout 0.93 per node):
  - a planted offset of 0.03 was detected;
  - with no offset, D2′ passed and was labelled "underpowered";
  - D1′ failed at F = 0.534;
  - a flipped convention stopped at G2.
- **The data are used once.** One window (15 ns), one dataset, no selection.

## 8. Limits
- The same limits as Study 35:
  - fixed-sample analysis, with no per-event time order;
  - the basis is not randomised per pair;
  - the readout-corrected numbers depend on the authors' readout model;
  - model uncertainties are combined as independent.

## 9. Procedure (Mac, `labs` environment, in `prx_work/35_delft`)
1. `python3 extract_35b.py DATA_DIR --check`
2. Commit and push this file and the scripts.
3. `python3 extract_35b.py DATA_DIR delft_extract_35b.json && python3 analyze_35b.py delft_extract_35b.json > results_35b.txt`

## 10. Locked files (sha256, first 16)
| File | sha |
|---|---|
| `extract_35b.py` | de0792d068c056b9 |
| `analyze_35b.py` | 5740f8f0ef9e6652 |
| `make_synth_extract_35b.py` | 968fe4852852d57b |
| `delft_core.py` (unchanged from Study 35) | 290b837d19ddbba4 |
| `extract_35.py` (helpers; unchanged) | 61e266e4c795728e |
