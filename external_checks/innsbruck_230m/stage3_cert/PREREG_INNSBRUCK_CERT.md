# Innsbruck ion–photon: model-free fidelity certificate (Stage 3). Pre-registered 11 Oct 2026, before the statistic is computed.

**Why.** This demonstrates, on real heralded ion–photon data, a fidelity lower bound that uses **no state model and no tomography reconstruction**: only error counts in three Pauli bases (Lemma F). It supports the certified-delivery framing.

**What it is not.**
- It is **not** a validation of Proposition C1. No public dataset randomises the choice to test or keep each pair.
- It is not blind. Stage 1 already printed Φ⁺ fidelity 0.913 (ML), and the per-scan counts in `stage1_counts.csv` were viewed during Stage 1 and again in this session. The bound is a deterministic function of those counts. This pre-registration fixes the **method**, not the outcome.

## Data
The counts come from `innsbruck_230m/stage1/stage1_counts.csv`, produced by the frozen Stage 1 decoder (`reconstruct_ion_photon.py`, sha 587f7352…). There is no re-decoding: threshold, herald rule and window are as in Stage 1.

| Basis | Scans used | Notes |
|---|---|---|
| ZZ | 1651 (H/V), 1655 (V/H) | |
| XX | 1653.02 (D/A), 1659 (A/D) | |
| YY | 1656 (R/L), 1702.02 (L/R) | |

- These six "diagonal" scans are dictated by Lemma F.
- Each pair of detector-swapped scans is pooled by polarisation label (Stage 1 C7).

## Frame and targets
- **Stage 1 C5 frame:** ion ⊗ photon; ion bright = +1 eigenstate of σ_B. Photon H, D, R are the +1 eigenstates of σz, σx, σy.
- **APD mapping M2** (Stage 1 C6): APD3 detects the second-named polarisation of the scan label, APD4 the first.
- **Target:** |Φ⁺⟩ = (|0H⟩ + |1V⟩)/√2, with signs (s_X, s_Y, s_Z) = (+, −, +), at phase 0. No phase optimisation.
- **Error rule:** in basis B, an error is ion outcome × photon outcome ≠ s_B.
- **Fidelity:** F = 1 − (e_X + e_Y + e_Z)/2, exact for any two-qubit state.
- **Honest union bound.** The Bell state and the mapping were chosen after Stage 1, so the bound is made **simultaneous over 8 candidates**: {M1, M2} × {Φ⁺, Φ⁻, Ψ⁺, Ψ⁻}. Each basis error bound uses level α/24, with α = 0.05.
- Only Φ⁺/M2 is the headline. The other seven are computed only to keep the union honest.

## Statistic
- **Per basis:** k_B errors in n_B heralded shots (pooled).
- **Upper bound:** the one-sided Chernoff–KL bound e_B^U solves n_B·KL(k_B/n_B ‖ e_B^U) = ln(24/α).
  - It is valid for adaptively varying conditional error probabilities at fixed n, bounding their average. Proof: the exponential supermartingale, plus concavity of log(1 − p + p·e^{−λ}) in p.
  - Clopper–Pearson is not used.
- **Certificate:** F_L = 1 − (e_X^U + e_Y^U + e_Z^U)/2.
- **Point estimate:** F̂ = 1 − (k_X/n_X + k_Y/n_Y + k_Z/n_Z)/2.

## Assumptions (stated in the paper)
- **(T) Trusted measurements.** Imperfections are charged to the state.
- **(FS) Fair sampling.** Heralding does not depend on polarisation within a basis, after pooling.
- **(H) Heralded population.** The certificate is for the state conditioned on a herald.
- **(S) Stationarity across the six scans.** Settings were measured in separate time blocks.

## Bars
- **R1-A (primary; a demonstration, near-certain to pass):** F_L > 1/2. That is, heralded ion–photon entanglement is certified without a state model at 95%, simultaneously over the 8 candidates.
- **R1-C (diagnostic):** for each basis, the error rates of the two detector-swapped scans agree. The test is an exact two-proportion test at α = 0.01, Bonferroni over 3 bases.
  - A FAIL labels the certificate "assumption (S) and/or (FS) contradicted". It is then reported per scan pair as well; it does not void R1-A.
- **R1-D (descriptive):** compare F_L and F̂ with Stage 1 (0.913 Φ⁺ ML; 0.920 best maximally entangled) and the authors' 0.924.
  - F̂ should agree with the Stage 1 Φ⁺ value within 0.01.
  - F_L above 0.920 flags an error.

No other target, phase, pooling, threshold or scan subset will be reported as primary.
