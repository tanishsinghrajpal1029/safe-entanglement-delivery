# Study 39 pre-registration: the certificate on an Oxford Sr–Sr link with per-event random bases

**Status:** frozen when this file, `analyze_39.py`, `cert.py` and `HASHES_PREREG_39.txt` are pushed to the public repository, **before the analysis script is run on the data** (written 4 Nov 2026).

## 1. Data
- One Sr⁺–Sr⁺ remote-entanglement characterisation run of the Oxford ion-trap network (ARTIQ RID 565472; 200,000 heralded events), provided by G. Araneda (University of Oxford) with a data guide. Related paper: Main et al., arXiv 2506.14334 (2025). **Private; not redistributed;** kept outside the repository. File sha256 (first 16): `86d0404bf560da1f` (the script prints it).
- Per event: the measurement setting drawn at each node (independent pseudorandom choices, recorded), both fluorescence outcomes, the herald pattern (4 two-detector coincidences), success timestamps and attempts per success. The outcomes are in the authors' common Bell-state frame (herald-dependent corrections applied).

**What we saw before freezing (exposure record):** the authors' email and data guide; the HDF5 structure (names, shapes, types). The guide states, and we therefore know: setting codes (0 +X, 1 +Y, 2 −X, 3 −Y, 4 +Z; ≈1/6, 1/6, 1/6, 1/6, 1/3); in the common frame ⟨XX⟩, ⟨YY⟩ > 0 and ⟨ZZ⟩ < 0 for every pattern; stored per-pattern phase-optimised fidelities ≈ 0.963, 0.959, 0.968, 0.962; stored `fidelity_to_psi_plus` ≈ 0.936; a constant leader–follower timestamp offset. **No per-event value was read or computed by us before the push.** The script was tested only on synthetic data written in the same layout.

## 2. Definitions
- Eigenvalues ±1 per node from bright/dark, with the sign reversed for the negative orientations (codes 2, 3), under the one convention that reproduces the stored fidelities (gate G2).
- **Target Ψ⁺ = (|01⟩ + |10⟩)/√2 in the authors' common frame** (⟨XX⟩ = ⟨YY⟩ = +1, ⟨ZZ⟩ = −1); F(Ψ⁺) = (1 + ⟨XX⟩ + ⟨YY⟩ − ⟨ZZ⟩)/4. A matched-axis event (both nodes on the same axis) is an **error** if its outcome product differs from the target's. The phase-optimised fidelity max_φ F(Ψ(φ)) is reported but **not certified** (choosing φ from the data would select the target after the fact).
- The certificate (Prop. C1, `cert.py`, α = 0.05) uses only matched-axis events (≈ 1/3 of all events; a random, time-interleaved subset because both settings are drawn per event). Every event was measured, so the test-or-keep split is drawn by us after the fact, as in Studies 37–38.

## 3. Stage 1: gates
- **G1 (design):** each node's setting-code frequencies within 5 s.d. of (1/6, 1/6, 1/6, 1/6, 1/3, 0); herald patterns in {0, 1, 2, 3}; timestamps strictly increasing. Reported: share of equal codes at both nodes; events with `protocol_aborts` > 0.
- **G2 (convention):** of the candidate conventions (bright ↦ ±1 at each node; sign reversal for negative orientations or not), exactly one physically distinct convention reproduces the stored per-pattern fidelities **and** the stored `fidelity_to_psi_plus` within 0.01 each (our linear estimates; the global relabelling of both nodes is equivalent).
- If a gate fails, Stage 2 is not run; we report and ask the authors.

## 4. Stage 2: hypotheses
**H2 (primary, drift within the run).** Pearson χ² across 10 equal-event blocks in time order (df = 9; merge/NA rule as in Studies 37–38) for: successes per attempt (`leader_tries_taken`), the XX, YY and ZZ error rates (10 blocks within each), and the share of each herald pattern. Bonferroni over valid tests.
- **Prediction:** successes per attempt **drift detected**; the three error rates **not** detected. (Herald-pattern shares: no prediction; reported.)

**H3 (primary, validity).** Each matched-axis event is labelled "test" with probability p ∈ {0.05, 0.1, 0.2} (1,000 seeded draws per p, seeds 39001–40000). A draw violates if the final certificate exceeds U = 1 − ½ Σ_B CP_lower(e_B) on the kept events (each per-basis bound at level 0.025/3). **FAIL if** in any p the CP95 lower bound on the violation rate exceeds 0.05. **Prediction:** PASS.

**H4 (primary, anytime validity in time order; new).** For the same draws, at 20 equally spaced checkpoints in time order, the running certificate is compared with the running U on the kept events so far (each per-basis bound at level 0.025/3/20). A draw violates if any checkpoint exceeds. **FAIL if** in any p the CP95 lower bound on this rate exceeds 0.05. **Prediction:** PASS. This is the first dataset whose settings are drawn per event, so the certificate's validity at all times can be checked on real data.

**H5 (primary, usefulness predicted in advance).** At p = 0.2 the median final certificate lies inside the 10–90 % band simulated from the **stored** F(Ψ⁺) at the actual number of matched-axis events (tests ~ Binomial(N, p), errors ~ Binomial(tests, 2(1−F)/3); 2,000 draws; seed 3900). p = 0.05 and 0.1 secondary. **Prediction:** PASS. (The stored F(Ψ⁺) was known in advance, so H5 checks the certificate's statistics, not a blind prediction of the fidelity; disclosed.)

**Descriptive (D1–D3).** All nine correlators; F(Ψ⁺) and the phase-optimised fidelity and phase, pooled and per herald pattern (D1) and per time block (D2); a calibrate-then-certify estimate: φ from the first 10 % of events, fidelity of the remaining events to Ψ(φ_cal) (D3); certificate shares above 0.8 and 0.9; first checkpoint at which the certificate exceeds 0.8.

## 5. Code
- `analyze_39.py` (our parser; no author code) and `cert.py` (unchanged from Study 27). Test-only switch `S39_TEST_SMALL` (100 draws) is never set for the real run; the output states if it is.
- Run order: Stage 1 (`--stage 1`), then Stage 2 (`--stage 2`), same machine and Python.

## 6. Limitations (stated in advance)
- One run of one device pair. The test-or-keep split is ours. Pseudorandom settings (NumPy MT19937), recorded; we do not test how or when they were generated relative to the herald.
- The certificate trusts the measurements and the authors' herald-dependent frame correction.
- Only matched-axis events enter the certificate; the other two thirds are used only descriptively.

**Citation:** data provided by G. Araneda, University of Oxford; related work Main et al., arXiv 2506.14334; Stephenson et al., PRL 124, 110501 (2020). Results will be sent to the authors before any submission.
