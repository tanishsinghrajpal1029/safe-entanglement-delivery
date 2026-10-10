# Innsbruck Stage 1 result (7 Oct 2026): G1 PASS; G2 consistent in magnitude, phase convention differs

Pre-registration: PREREG_INNSBRUCK_STAGE1.md (sha 568c7b973f8e94f4), written before any reconstruction.
Reconstruction done blind to the authors' result (Analysis_fidelity_and_matrices.png not opened until stage1_result.json was frozen).
Script stage1/reconstruct_ion_photon.py (sha 587f735216996b81); result stage1/stage1_result.json (sha 3db7c287e82de9e3); choices stage1/CHOICES.md.

| Quantity | Ours (blind) | Authors (their figure) | Diff |
|---|---|---|---|
| Fidelity to closest maximally entangled state | 0.920 ± 0.004 (ML), 0.920 (linear inversion) | Fid_arb_max 0.924 | −0.004 |
| Fidelity, best local phase | 0.9135 ± 0.004 | Fid_theta 0.914 ± 0.004 | −0.0005 |
| Other authors' variants | | Fid_alpha 0.919, Fid_alpha_theta 0.919, upper bound 0.926 | |
| Populations of the two dominant terms | 0.479 / 0.480 | "0.50 to 0.50" | |
| Coherence magnitude | 0.434 | ≈ 0.45 (read from 3-D bar plot) | ≈ 0.02 |
| Phase of the coherence | −2.4° | −86.9° | convention |

- **G1 PASS:** every pairing of our fidelity with the authors' corresponding quantity differs by ≤ 0.006, inside the pre-set tolerance max(2 × 0.004, 0.02) = 0.02.
- **G2: consistent in magnitude, not checkable in phase.** Diagonal and coherence magnitudes agree within ≈ 0.02. The authors' frame (|DH>, |DV>, |D'H>, |D'V>, phase −87°) differs from ours by a local z-rotation of the ion, a convention the raw data cannot fix (see subagent note: APD assignment, R/L handedness, rotation sign and |0> level are only fixed jointly). The element-wise phase comparison is therefore not possible without the authors' convention.
- One data-driven choice decided the APD↔polarisation mapping: the alternative gives an unphysical state (min eigenvalue −0.42). Recorded before comparison.
- **Consequence:** our decoding of this group's raw format (ion readout threshold, herald rule, cycle alignment) is validated on a result they computed. Stage 2 (ion-ion, 230 m) needs additional decoding: Node B format, Bell-state-station time tags and cross-node synchronisation. Stage 2 is pre-registered separately before any ion-ion statistic is computed.
