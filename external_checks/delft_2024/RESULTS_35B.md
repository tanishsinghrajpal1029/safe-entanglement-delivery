# Study 35B ("Delft, delivered states"): results (13 Oct 2026)

## Provenance
- **Pre-registration:** `PREREG_35B.md` (sha bddcaafd7f9c7d12), committed publicly as `726549d` at 05:06:41 UTC. The extraction ran at 05:06:53 UTC, **12 s later**. The data were used once.
- **Locked files, unchanged at run time:** `extract_35b.py` de0792d068c056b9, `analyze_35b.py` 5740f8f0ef9e6652, `delft_core.py` 290b837d19ddbba4.
- **Outputs:** `results_35b.txt` 44db158b518ce37e and `results_35b.json` a46e46d822f1a355. The extract (64293fcc99fe78f5) is kept locally.
- **Data:** the paper's Fig. 4: **fully heralded, delivered Ψ− states** (feedback and echo), 15 ns window, main-text file without the PSB correction.
- **Events per basis (combined state):** X 450, Y 452, Z 449. That is fewer than the 750 per state assumed in the synthetic test. G4: the combined counts equal state 0 + state 1.

## Gates: all PASS
- **G1, G2:** basis order Z, X, Y; the parity convention matches exactly.
- **G0:** a Ψ− target reproduces all three fidelity attributes exactly (0.5290, 0.5378, and 0.5340 for the combined state).
- **G3:** the sweep at 15 ns gives 0.5349, against 0.5340 in the h5 file.

## Verdicts: primary 1/2 (D1′ FAIL, predicted; D2′ PASS, underpowered); secondary S1′ PASS (predicted, narrowly)

| | Tier | Result | Numbers |
|---|---|---|---|
| **D1′** | primary | **FAIL (predicted)** | **Raw-count, model-free certificate on the delivered pairs:** F̂ = 0.474, **F_lo = 0.399** (95%; bar > 0.5) |
| **D2′** | primary | **PASS, underpowered** | **Model offset at 15 ns:** F_model 0.5277 (count-rate weights 0.44/0.56) against F_data 0.5349; **Δ = −0.007 ± 0.015**. One-sided 95% interval [−0.032, +0.018]. Bar 0.051, not weak. **Power at Δ = 0.03 only 0.63**, so this is "consistent, underpowered", not evidence that the model is right. |
| S1′ | secondary (prediction) | PASS (narrowly) | **Readout-corrected (model-dependent) bound:** 0.5349 − 1.645 × 0.0151 = **0.510 > 0.5** |
| S2′ | descriptive | — | **Declared margin a guard would need:** Δ upper bound **+0.018** |
| S3′ | descriptive | — | **Sweep:** Δ(w) is negative at every window (the model is pessimistic), from −0.042 at 5 ns to −0.004 at 20 ns. Nested windows, no test. |

## Reading
1. **On the delivered pairs, the "model-free" certificate needs a readout model.**
   - From raw counts, the 95% lower bound is 0.399. With the authors' readout correction it is 0.510.
   - Entanglement of the delivered states is certified only through the readout model. This repeats Study 35 on the object the manuscript is about.
2. **No sign of model optimism for the delivered states.**
   - At 15 ns, Δ = −0.007. At every window the model is at or below the data.
   - A guard would need to declare at most about 0.02.
   - **But with about 450 events per basis, the test cannot rule out an offset of about 0.03** (power 0.63). The honest statement is "no optimism detected; offsets up to about 0.02 are not excluded".
3. **Across the four datasets, model optimism is platform- and setup-dependent:**
   - USTC: 2–4 points optimistic in point estimate;
   - Delft post-selected (Study 35): accurate within ±0.01;
   - Delft delivered (this study): not optimistic, weakly constrained.

## Limits
- Fixed-sample analysis; no per-event time order.
- The basis is not randomised per pair.
- The readout-corrected numbers depend on the authors' readout model.
- Model uncertainties are combined as independent.
- About 450 events per basis, so D2′ is underpowered, as anticipated in the pre-registration.

## Scoreboard
- **Primary:** +2 (D1′ FAIL, D2′ PASS). Project total **87 primary: 76 PASS, 11 FAIL**.
- **Secondary:** +1 (S1′ PASS). Secondary total **54: 47 passed or confirmed, 6 failed, 1 unclear**.
