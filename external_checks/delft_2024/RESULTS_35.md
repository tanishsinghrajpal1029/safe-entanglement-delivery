# Study 35 ("Delft"): results (13 Oct 2026)

## Provenance
- **Pre-registration:** `PREREG_35.md` (sha b5765393a6c657aa), committed publicly as `f9db617` at 04:51:17 UTC. The extraction ran at 04:51:31 UTC, **14 s later**. The data were used once.
- **Locked files, unchanged at run time:** `delft_core.py` 290b837d19ddbba4, `extract_35.py` 61e266e4c795728e, `analyze_35.py` d41418d4e4b6acda.
- **Outputs:** `results_35.txt` 93d8ca6c6fe5b8fc and `results_35.json` 6d8df4aff00e06d4. The extract JSON (c90a6269f7ebc9a0) is kept locally and not redistributed.
- **Data:** Stolk et al., doi:10.4121/983e4771-1d12-457f-a98e-fab3a2959288.v1 (CC BY 4.0). Figure 3 main dataset, 10 ns herald window, heralded states Ψ+ and Ψ−. Events per basis, both states: X 1,436, Y 1,535, Z 1,415.

## Gates: all PASS
- **G1:** the labels parse to Ψ+ and Ψ−; the stored basis order is Z, X, Y; the third state, labelled "Avg", is excluded as pre-registered.
- **G2:** the parity convention matches the authors' correlators exactly.
- **G0:** our fidelities equal the authors' attributes (0.5672 for Ψ+, 0.5759 for Ψ−).
- **G3:** the sweep at 10 ns reproduces the main-window fidelity.
- The stored probabilities are readout-corrected: they differ from the raw frequencies by up to 0.050.

## Verdicts: primary 1/2 (D1 FAIL, as predicted; D2 PASS); secondary S1 PASS

| | Tier | Result | Numbers |
|---|---|---|---|
| **D1** | primary | **FAIL (predicted)** | **Raw-count, model-free certificate:** F̂ = 0.505, **F_lo = 0.464** (95%; bar > 0.5). Per state, F_lo is 0.443 and 0.451. Without a readout model, entanglement cannot be certified from these data. |
| **D2** | primary | **PASS** (adequately powered) | **Model offset at 10 ns:** F_model 0.5672 against F_data 0.5716; Δ = −0.004 ± 0.008. One-sided 95% interval [−0.018, +0.009]. Bar 0.037, not weak; power at Δ = 0.03 is 0.97. |
| S1 | secondary (prediction) | PASS | **Readout-corrected (model-dependent) bound:** 0.5716 − 1.645 × 0.0081 = **0.558 > 0.5** |
| S2 | descriptive | — | **Declared margin a safe guard would need here:** Δ upper bound **+0.009** |
| S3 | descriptive | — | **Sweep:** Δ(w) rises from −0.004 at 5 ns to +0.016 at 20 ns. No test, because the windows are nested. |

## Reading
1. **The trusted-measurement assumption matters on real hardware.**
   - The same events give a fidelity of 0.505 from raw counts and 0.572 after readout correction. The correction is worth about 0.07.
   - Entanglement is certified only with the readout model (S1), not without it (D1).
   - So a "model-free" certificate on real devices still rests on a readout model, unless readout is characterised separately and trusted. This supports the manuscript's stated assumption for Prop. C1.
2. **This model is accurate, unlike USTC's.**
   - At the authors' operating window, their model matches the data within ±0.01: Δ = −0.004, with an upper bound of 0.009.
   - The margin a guard would need to declare is about 0.01. For comparison, USTC needed 0.10, and that model was 2–4 points optimistic (E97).
   - Model optimism is therefore platform- and setup-dependent. It is not universal.
3. **Exploratory, not tested:** the model becomes more optimistic as the acceptance window widens, reaching +0.016 at 20 ns. That is about 2.5 standard errors of the data alone at that point. A wider window admits more noise than the model accounts for. Because the windows are nested and no test was pre-registered, this is a hypothesis for future work, not a finding.

## Disclosures and limits
- **Two model files disagree slightly.** At 10 ns, the main-figure model file (`correlation_results`, used for D2 as pre-registered) gives F_model 0.5672. The sweep's model gives 0.5753, about 0.008 higher. With the sweep model, Δ at 10 ns would be +0.004, still within the bar. Both are reported.
- **Fixed-sample analysis.** There are no time-ordered per-event records, so no anytime certificate or closed-loop test was possible. The basis was not randomised per pair, so i.i.d. events within each basis are assumed.
- **Model uncertainty treated as independent across bases** (stated in advance).

## Scoreboard
- **Primary:** +2 (D1 FAIL, D2 PASS). Project total **85 primary: 75 PASS, 10 FAIL**.
- **Secondary:** +1 (S1 PASS).
