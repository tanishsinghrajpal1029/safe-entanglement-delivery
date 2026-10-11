# Certified entanglement delivery: theory note (v2, 11 Oct 2026; revised after adversarial review REVIEW_27.md)

**Status.** This is not yet in the paper.
- Code: `cert.py`.
- Our Monte Carlo: `mc_cert.py`, with results in `mc_cert_log_G8_every.txt`.
- The reviewer's Monte Carlo: `REVIEW_27.md`.

**What changed from v1.**
- A2 is replaced by an argument that needs **no** per-pair assumption.
- A3 is corrected. It was false: see the readout counterexample in REVIEW_27 M1.
- The novelty claims are withdrawn. The certificate is a **known-type result**, and we use it as a component.
- Proposition N is added: a no-go for certifying per-pair thresholds model-free.

## 1. Protocol and assumptions
- A user (Alice, Bob) receives delivered two-qubit pairs i = 1, 2, …. The network may act in any way, quantum or classical, adaptive or adversarial. It may hold purifications and may entangle pairs with each other or with its own systems.
- After pair i is delivered **and after its Pauli-frame correction has arrived**, the users draw fresh shared randomness hidden from the network. They test the pair with probability p (Tᵢ = 1), in a basis Bᵢ uniform on {X, Y, Z}. Otherwise they keep it.
- A test error is Eᵢ = 1 if the outcomes differ in X or in Z, or agree in Y. These are the events |Φ⁺⟩ never produces.

**Assumptions**
- **(A1) Hidden, fresh test choice.** (Tᵢ, Bᵢ) is independent of everything the network holds and of everything before it.
- **(A3′) Trusted measurements.** The users' Pauli measurements are ideal, **or** each basis's parity-flip probability is at most a known r_max. In the second case, replace 2/3 by a = (2/3)(1 − 2r_max) below (implemented in `cert.py`).
  - Readout noise does **not** in general make the certificate conservative: it lowers the error rate of pairs with F < 1/4.

## 2. Virtual Bell-basis labels (removes the per-pair assumption)
- The test observables XX, YY, ZZ and the projector |Φ⁺⟩⟨Φ⁺| = (I + XX − YY + ZZ)/4 all commute; they are diagonal in the Bell basis.
- So the outcome statistics are unchanged if every pair is first measured in the Bell basis by a virtual measurement. This is the Lo–Chau reduction familiar from QKD.
- Give each pair the label Λᵢ ∈ {Φ⁺, Φ⁻, Ψ⁺, Ψ⁻}, and let φᵢ = 1[Λᵢ ≠ Φ⁺] ("would fail a Φ⁺ check").
- Given φᵢ = 1, a uniformly random basis gives E = 1 with probability exactly 2/3. Each wrong Bell state errs in two of the three bases. Given φᵢ = 0, E = 0.
- **The kept-pair fidelity is the average of the labels.** For each kept pair, the conditional expectation of 1 − φᵢ given the past is the fidelity of that pair's conditional state to Φ⁺ (Lemma F: 1 − F = (e_X + e_Y + e_Z)/2 for any two-qubit state). So bounding the number of failed kept labels bounds the kept pairs' average fidelity, with the usual martingale correction.

## 3. Proposition C1 (anytime-valid kept-pair certificate; a known-type result)
**Definitions.**
- For λ ∈ (0, λ_max), with λ_max = ln[(1 − p(1 − a))/(1 − p)], let k(λ) solve
  (1 − p)e^{λ} + p[1 − a(1 − e^{−1.5λk})] = 1.
- Let c_g = 1.5·k(λ_g), with mixture weights w_g over a grid of 8 values of λ.
- Let N_t be the number of kept pairs up to t whose virtual label fails, and Err_t the number of test errors.

**Statement.** Under A1 and A3′,

  P( ∃ t : Σ_g w_g exp(λ_g (N_t − c_g Err_t)) ≥ 1/α ) ≤ α.

**Proof.**
1. Fix λ. Conditioned on the past, the increment exp(λ[(1 − Tᵢ)φᵢ − c Tᵢ Eᵢ]) has expectation 1 if φᵢ = 0, and f(1) ≤ 1 if φᵢ = 1, by the choice of k.
2. So the product is a nonnegative supermartingale for **any** joint strategy of the network.
3. A mixture over λ is again one. Ville's inequality applies, and we invert in N_t, which is monotone. ∎

**Certificates, valid simultaneously for all t and under any stopping rule, with probability ≥ 1 − α:**
- **(i) Kept-pair Bell check:** N_t ≤ N_ub(Err_t).
- **(ii) Kept-pair average fidelity:** L_t = 1 − N_ub(Err_t)/K_t.
  - This statement is about the failed-label *fraction*.
  - When the pairs are not entangled with each other or with the network's systems, it is also the kept pairs' average fidelity; the earlier version (v1) proves that case directly.

**Verified numerically:**
- Ours, with the check after every kept pair, 1,000 runs per cell, the 8-value λ grid, at p = 0.05 and p = 0.2: the worst cell failed at 2.5%.
- The reviewer's, with 3,000 runs × 10,000 pairs, adaptive adversaries and states that are not Bell-diagonal: at most 4.6%.

**Prior art: this is not new.**
- Direct fidelity estimation with Pauli tests; Pallister–Linden–Montanaro 2018.
- "Test some, certify the rest" against adversarial sources: Takeuchi–Morimae 2018; Zhu–Hayashi 2019; Gočanin–Šupić–Dakić, PRX Quantum 2022 (device-independent); Bouman–Fehr sampling; QKD parameter estimation.
- Test supermartingales: Zhang–Glancy–Knill; Knill et al. 2020.
- Anytime-valid tomography: Cumitini et al. 2026.

We cite Proposition C1 as a component.

## 4. Proposition N (no model-free certificate of per-pair thresholds)
**Setting.** Fix a target "no kept pair has F < τ", and any certification rule that sees only the outcomes of a fraction p < 1 of pairs.

**Construction.** Compare two delivery strategies:
- **S₀:** every pair is Φ⁺.
- **S₁:** each pair is independently replaced by Ψ⁻ with probability η = c/N, out of N pairs.

**What the rule sees.** The test-outcome distributions under S₀ and S₁ differ in total variation by at most (2/3)·p·c. So any rule that certifies under S₀ with probability ≥ 1 − α also certifies under S₁ with probability ≥ 1 − α − (2/3)pc.

**What actually happens under S₁.** A kept pair is bad with probability 1 − (1 − (1 − p)c/N)^N → 1 − e^{−(1−p)c}.

**Example.** With c = 1 and p = 0.1:
- the rule wrongly certifies with probability ≥ 0.93 − α (total variation ≤ 0.067);
- at least one bad pair is kept with probability ≈ 0.59.

**Consequence.** Only averages and counts can be certified model-free. "No pair below τ" needs a model, which is the job of the guard (Prop. 6) and its declared margins. That guard can be broken by undeclared optimism and persistent noise, as Studies 25 and 26 show at measured real-hardware levels. This is the central tension the paper reports.

## 5. Resource floor (`cert.py`, α = 0.05)
- **Perfect pairs:** reaching L ≥ 0.9 needs about 1,404 / 678 / 315 kept pairs at p = 0.05 / 0.1 / 0.2. For F = 0.95 pairs it needs several thousand.
- **What users actually get.** In the 5×5 network a uniformly chosen user receives tens of pairs per 2,700 s. Per-user certification is therefore vacuous except for heavy users. The network-pooled (operator) certificate is informative.
- **This is a physical cost the paper must state.**

## 6. What the paper can claim (honest positioning)
**Not claimed as new:** Proposition C1, Lemma F, and the statistical tools.

**Candidate contributions, to be argued, not assumed:**
- **(a) The two-layer analysis.** A model-based per-user guard (Prop. 6, corrected per user) plus a model-free average certificate (C1). The no-go (Prop. N) shows why both are needed.
- **(b) Evidence from real data.** Measured non-stationarity and model optimism on three public experiments put deployed-like links in the regime where the per-pair layer breaks (Studies 25–26), while the model-free layer stays valid (Study 27).
- **(c) The network-level cost of certification.** How it scales with p, traffic and control quality, and the per-user floor.
- **(d) A model-free fidelity lower bound on real ion–photon data (Innsbruck),** pre-registered. It is a demonstration under stated assumptions, not a validation of C1.

**Still unread:** arXiv 2610.10885. Two fetches were rate-limited. It must be read by hand.
