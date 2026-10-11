# REVIEW 27: adversarial review of Theorem C1 (certified kept-pair fidelity) and Study 27 code

Reviewer: independent adversarial check, 11 Oct 2026. I did not modify any file under review. My scripts and outputs are in the scratchpad (`rev_mc.py`, `rev_mc_valid.json`, `rev_mc_readout.json`, `rev_valid.log`, `rev_readout.log`).

**Bottom line.**
- The core proof is **correct**. Steps 1–4 of Theorem C1 hold, and the certificate is valid at α = 0.05 when checked after every kept pair, against strong adversaries and non-Bell-diagonal states (my MC below).
- **There is no BLOCKER in the Study 27 code.** It does what the docstring says.
- There are real problems in four places:
  - (A3) is false as stated, with a counterexample at 9–12% failure.
  - (A2) is stated wrongly. It is too weak in one place and unnecessary in another.
  - The novelty claims are not supportable. Theorem C1 is a standard result.
  - Three of the six pre-registered hypotheses (C1, C3, C4) are mis-designed and should be fixed **before** the confirmatory run.

---

## MAJOR findings

### M1. (A3) "readout errors that only add error events make the certificate conservative" is false
**Location:** THEORY_CERTIFIED:20

**Problem.**
- Readout noise does not "only add" error events. With a symmetric per-outcome parity-flip probability r′, the test error probability becomes P(E) = (2/3)δ + r′(1 − (4/3)δ).
- This *lowers* the error rate whenever δ > 3/4, that is, whenever F < 1/4.
- Pairs with F ≈ 0 are realistic. A wrong Pauli-frame correction or a swap-outcome bookkeeping bug delivers Ψ⁻, Φ⁻ or Ψ⁺, all with F = 0.
- For such pairs f(1) > 1. The process is then a **sub**martingale and the violation probability goes to 1 as the stream lengthens.

**Verified.** In `rev_mc.py readout`, the network delivers Ψ⁻ on every pair, each qubit's readout flips with probability r, there are 30,000 pairs and 1,000 runs, and the check runs after every kept pair. Violation rates:

| p | r = 0.01 | r = 0.02 |
|---|---|---|
| 0.05 | **6.3%** | **9.3%** |
| 0.1 | **5.8%** | **9.2%** |
| 0.2 | **6.7%** | **11.8%** |

All six cells are above α = 0.05.

**Fix (pick one).**
- (a) State A3 as "ideal (trusted, noiseless) Pauli measurements".
- (b) Assume a known bound r′ ≤ r_max on each basis's parity-flip probability. Then P(E | δ) ≥ (2/3)(1 − 2r_max)δ, and redefining k(λ) from (1 − p)e^λ + p[1 − (2/3)(1 − 2r_max)(1 − e^{−1.5λk})] = 1 restores validity. The certificate costs a factor of about 1/(1 − 2r_max) on c.
- (c) Restrict the claim to "conservative if every delivered pair has F ≥ 1/4". I do not recommend this: an adversarial or buggy network breaks it.

### M2. (A2) is mis-stated. The theorem holds without it for a cleaner quantity, and "not entangled with one another" is not the right condition
**Location:** THEORY_CERTIFIED:17–19, 110

**What the proof actually certifies.**
- D_t = Σ_kept δ_i, where δ_i is the deficit of pair i's state conditioned on a filtration that includes all past outcomes, and with respect to which (T_i, B_i) and the Born-rule randomness are fresh.
- The proof is correct for *any* such filtration.
- Ville's inequality does not need D_t to be observable. So the filtration may include the network's private classical information. This makes the classical-adaptive case fully rigorous.
- **"The network may correlate pairs classically in any way, adaptively" is therefore correct.**

**What is wrong.**
1. "If different delivered pairs are not entangled with one another, ρ_i is simply pair i's state" is not sufficient. The pair must also not be entangled with any *retained network system* (a reused memory, a non-Markovian bath, or a purification the network keeps) that later couples to delivered pairs or to announced outcomes. The precise condition: given the network's classical record, pair i is in a product state with everything the network keeps.
2. If A2 fails, as the note phrases it (cross-pair entanglement, or purifications held by the network), D_t is a sum of *one-step-ahead predictable* conditional deficits. Outcomes of later tests can steer an earlier kept pair. The "average fidelity of the kept pairs" conditioned on all the data can then differ from D_t/K_t, and the note never says which of the two is certified.

**The stronger version, which needs no A2, no de Finetti and no EAT.**
- XX, YY, ZZ, the test-error parity, and the projector "Φ⁺ vs not" on any pair are all Bell-diagonal. On distinct pairs they commute.
- Neither the network nor the users touch a kept pair after it is kept. So a fictitious measurement of its label b_i ∈ {Φ⁺, not Φ⁺} can be moved to the moment it is kept without changing any joint distribution. This is the Lo–Chau reduction from QKD (Science 283, 2050, 1999).
- Put b_i in the filtration and use Z_i = (1 − T_i)·1[b_i ≠ Φ⁺] − cT_iE_i. The conditional MGF is the *chord* (1 − p)(1 + δ(e^λ − 1)) + p[1 − (2δ/3)(1 − e^{−λc})], which equals 1 at both δ = 0 and δ = 1, so it is ≤ 1. The same k(λ) works.
- **Strongest correct statement:** for any joint quantum strategy of the network, including entanglement across pairs, held purifications and adaptivity on all announced outcomes, P(∃t: N_t^{bad} > D_ub(Err_t)) ≤ α. Here N_t^{bad} is the number of kept pairs that a Φ⁺-projective measurement would reject.
- This is the composable-style statement. It is a joint probability over data and labels, not a posterior given the data.
- It needs only three things: (A1); the network has no access to a kept pair after the keep decision; and each test acts only on its own pair.

**Fix.**
- Replace A2 with this argument and state both forms: the D_t form, and the label-count form for general quantum strategies.
- Delete "Open: whether (A2) can be dropped with de Finetti/EAT". It can, by the elementary argument above.
- Add one caveat. The joint statement does not give a level-α bound *conditional on* the observed data. By Markov's inequality, P(P(N^{bad} > D_ub | data) > β) ≤ α/β.

### M3. Novelty: Theorem C1 is a known result in different notation. Do not call it a "Theorem" contribution
**Location:** THEORY_CERTIFIED:24–36, 38–58, 94–107

**Lemma F is textbook.**
- It is the stabilizer decomposition used in direct fidelity estimation (Flammia–Liu 2011; da Silva–Landon-Cardinal–Poulin 2011).
- It is also exactly the optimal non-adaptive Pauli strategy for a Bell state in quantum-state verification: measure XX, −YY, ZZ, each with probability 1/3, with spectral gap 2/3 and pass probability 1 − (2/3)(1 − F). See Pallister, Linden & Montanaro, PRL 120, 170502 (2018), arXiv:1709.03353.

**"Test a random subset, certify the untested copies, with a non-iid adversarial source" is the adversarial QSV and quantum-sampling literature.**
- Takeuchi & Morimae, PRX 8, 021060 (2018).
- Zhu & Hayashi, "Efficient verification of pure quantum states in the adversarial scenario", PRL 123, 260504 (2019), arXiv:1909.01900; and "General framework…", arXiv:1909.01943.
- Bouman & Fehr, CRYPTO 2010 (quantum sampling).
- Parameter estimation for entanglement-based QKD, where phase plus bit error of the unsampled pairs is exactly 1 − F.
- The Lo–Chau commuting-observable reduction of M2 is also from QKD.

**Anytime-valid inference for the unsampled part of a population is known.**
- Waudby-Smith & Ramdas, confidence sequences for sampling without replacement (NeurIPS 2020).
- The betting confidence sequences of the same authors.
- Test supermartingales against adaptive quantum adversaries are routine: Zhang–Glancy–Knill 2011; Knill et al., PRR 2020.

**What the note lists as new is not new.**
- "An adaptive network" is an adaptive adversary, which is the default setting of the adversarial QSV and test-martingale papers.
- "Per-user" means running the same certificate on a sub-stream.
- "Composed with a guard" and "control-quality vs certification-cost trade-off" are system-integration and empirical points, not theory.

**Honest claim.**
- "We apply a standard (adversarial-QSV / test-supermartingale) certificate as a model-free audit layer on top of a model-based router, and measure what it costs per user."
- Present C1 as a *Proposition* with citations, and keep the proof only because it is short.

**Unverified citations.** "Zhang et al., PR Applied 2025" and "Cumitini et al., arXiv 2601.20761" must be read before they are cited.

**Not read.** I could not read arXiv 2610.10885: arxiv.org returned HTTP 429 (rate limited) to my fetch as well. It is still unread and must be checked by hand.

### M4. "Certified safety" in §5 conflates two different safety notions, and the bad-pair corollary is vacuous in the study's regime
**Location:** THEORY_CERTIFIED:64, 86

**The corollary is correct.** #bad ≤ D_ub/(1 − τ) holds: Σ_bad δ_i > (1 − τ)·#bad, and Σ_bad δ_i ≤ D_t ≤ D_ub.

**But it is vacuous here.**
- τ = 0.9 (I checked: ion2020 `net.tau = 0.9`).
- In my smoke run (ion2020, kg, hot traffic, p = 0.1), the hot user with 1,385 kept pairs has F̄ = 0.934 and L = 0.825. So D_ub ≈ 242, and #bad ≤ 2,420, which is more than K.
- The note says "costs a factor of 10". In fact the bound is above K: it says nothing.

**Consequence for the paper.**
- The guard's safety notion (Studies 18–26) is "P(a user ever receives a pair with F < τ) ≤ α".
- The certificate's notion is average fidelity. These are different and incomparable.
- Sentence §5.1, "A wrong model costs throughput, not certified safety", is an overclaim.

**Fix.**
- State plainly that no testing scheme with a test fraction p < 1 can certify "no kept pair below τ". A network that corrupts one randomly chosen pair escapes detection with probability ≥ 1 − p. This is a one-line no-go and is worth including.
- Rephrase the two layers as "model-based per-pair threshold guard" plus "model-free average-fidelity audit". The second does not certify the first.

### M5. Per-user certificates are vacuous for almost all users. The paper must quantify this floor
**Location:** THEORY_CERTIFIED:63–68; study27.py:28 (`KMIN_TIGHT = 100`)

**The floor.**
- D_ub does not depend on K and has a floor at zero errors (`cert.py`, G = 8): D_ub(0) = 140 (p = 0.05), 68 (p = 0.1) and 31 (p = 0.2).
- So L_t ≤ 1 − D_ub(0)/K. Every user with K ≤ 68 kept pairs at p = 0.1 has L ≤ 0 whatever the data.
- Kept pairs needed for L ≥ 0.9 with *perfect* pairs: 1,471 / 703 / 317 at p = 0.05 / 0.1 / 0.2.
- For F̄ = 0.95 iid pairs: 8,166 / 4,119 / 1,976.

**What the smoke run shows.**
- Uniform traffic: about 3,700 deliveries over 80 served users, roughly 45 pairs per user. Every per-user certificate is vacuous.
- `fault|uni` on nv2: 99 deliveries in the whole network, and even the network-pooled L is negative.

**Fix.** Report the floor (D_ub(0) per p) and "pairs needed per user" in the paper. Frame per-user certification as viable only for heavy users or for pooled streams. Raise KMIN_TIGHT (see M7).

### M6. Analysis C1/C1b/C3 are close to tautological: diluted denominators, ignored clustering, and C3 implied by C1b
**Location:** analyze_27.py:32–35, 40–43, 48–50

**Dilution.**
- `u_cert` counts every user with ≥ 1 kept pair.
- A user whose K never exceeded D_ub(Err) can never violate, because a violation needs L > F̄ ≥ 0.
- Most of the denominator (tens of thousands of users) is in this structurally-cannot-fail class. The pooled rate and its CP bound will pass whatever the code does.

**Clustering.**
- The CP bound treats users as independent Bernoulli trials.
- Users in the same network share δ trajectories (fault, drift, noise) and the same test stream. So the CP bound is anti-conservative.

**C3 is redundant.**
- C3's row-wise and pooled conditions are implied by C1b, which checks every cell. C3 can only pass if C1b passes.
- C3's header says "certificate … is LOW", but nothing about lowness is tested.
- An empty `br` passes vacuously.

**Fixes (before the confirmatory run).**
- (i) Define *eligible* users as those whose certificate was ever > 0, that is, max over time of K_t − D_ub(Err_t) > 0. Record this in study27 as `{tag}_u_elig`. Use it as the C1/C1b denominator, and also report the old one.
- (ii) Use a network-level cluster bound: the mean over networks of each network's violated fraction, with a one-sided t or Hoeffding bound. Or report the CP bound as descriptive only.
- (iii) Make C3 test lowness. Example: in broken-control cells, the median network-pooled L < τ, or L is below the guard's implied bound. Fail C3 if `br` is empty.

### M7. C4 (tightness ≤ 0.10) is calibrated to the wrong regime and will probably FAIL on a correct certificate
**Location:** analyze_27.py:53–56; study27.py:28, 45

**The mismatch.**
- The 0.035 gap in the theory note is for 10⁴ kept pairs.
- Hot users here have about 1,400 kept pairs at p = 0.1.
- Smoke run (ion2020 / kg / −|hot / idx 0): `p10_u_big_F` 0.934, `p10_u_big_L` 0.825, **gap 0.109 > 0.10**. At p = 0.05 the gap is 0.132; at p = 0.2 it is 0.073.

**Half of the hot users are starved.**
- In that network, hot users 143 (2-hop) and 155 received 1,869 and 1,793 requests and **0 deliveries**.
- So HOTN = 4 effectively means 2 users. The wasted serial service budget also slows every other user.

**Fix.**
- Pre-register the C4 threshold from `cert.py`'s expected certificate at the *observed* K and F̄ (gap ≤ 1.2 × predicted). Or compare against a fixed-sample oracle bound, for example the ratio to a Clopper–Pearson bound at the same K.
- Draw hot users only among users whose oracle path can reach τ, for example 1-hop users or users with oracle_qual > 0 on the dev pilot. Do this on dev data, before confirmation.
- Raise KMIN_TIGHT to about 500.

---

## MINOR findings

| # | Location | Problem | Fix | How verified |
|---|---|---|---|---|
| m1 | THEORY:65–68; cert.py:63–71 | The tightness numbers come from **one** binomial draw, not an expectation. Expected-count values are 0.921 / 0.861 / 0.747 vs the reported 0.915 / 0.845 / 0.735. "1.6× wider" does not reproduce: (0.95 − 0.915)/(0.95 − 0.936) = 2.5, and 0.085/0.064 = 1.33. | Use expected or median values over many draws. Define "width". Show the fixed-sample bound computation. | reran with expected counts |
| m2 | THEORY:82–83; mc_cert.py:39 | `mc_cert.py` always writes `mc_cert_results.json`. The G = 8 every-pair background run has now **overwritten** it: max 2.5% (`p0.2_fault`), not the ≤ 1.2% quoted. `mc_cert_results_G16_every.json` still holds the older numbers. Provenance is fragile. | Put the grid and check cadence in the output filename. Update the note's numbers. | diffed the files |
| m3 | THEORY:70–81; mc_cert.py | The MC "adversaries" are weak (≤ 2.5%). The worst case for this supermartingale is δ ∈ {0, 1}, where the product is a *martingale*, so the failure rate approaches α (my all-Ψ⁻ case: 2.8–4.5%). Also, "Ψ⁻ vs Werner" is irrelevant: only the basis-averaged error (2/3)δ enters. | Add all-bad, Bernoulli{0,1} and "lucky" adaptive scenarios with long horizons, so the MC shows near-tightness and not only slack. | my MC below |
| m4 | THEORY:13–16 | A1 in a real network: the pair is only defined after the Pauli-frame / heralding message arrives. If the users reveal T_i or B_i before receiving it, the network can choose the frame after seeing the test choice. | State: "T_i, B_i are revealed only after the pair and its frame correction are fixed at the users". | reasoning |
| m5 | THEORY:51 | The certificate covers fidelity *at delivery*. It does not cover decoherence in the users' memories before use. | Say so. | reasoning |
| m6 | analyze_27.py:61–62 | C6 says "relative to p = 0.05" but prints absolute sums. It averages `net_L` values that are often negative (vacuous), which is meaningless. | Print ratios. Clip L at 0 or report the median. | read |
| m7 | study27.py:48–53 | The fault T2 is evaluated at the attempt end time t and applied to all storage in that attempt, including storage before the fault epoch. That is a small approximation at the boundary. | Document it. | read |
| m8 | THEORY:63 | The per-user statement is fine. But with 204 users per network, "each at α" allows about 10 violated users per network in the worst case. | Say this next to the pooled/union options. | arithmetic |

---

## Checks that PASSED (verified)

**Theory**
- The MGF in step 1 is correct: E[e^{λZ}] = (1 − p)e^{λδ} + p[(1 − q) + q e^{−λc}] with q = 2δ/3.
- f is convex, f(0) = 1, and f(1) = 1 by the choice of k. So f ≤ 1 on [0, 1].
- k exists and is positive exactly for λ ∈ (0, λ_max). This matches `kprime`'s assertion.
- δ ∈ [0, 1] for any 2-qubit state.

**Lemma F**
- It holds for **any** two-qubit state, not just Bell-diagonal ones.
- Checked on 20,000 random full-rank and low-rank complex states, with the error probabilities computed from explicit local projective measurements and not from correlators. Max error 6.7·10⁻¹⁶.
- Named states:

| State | δ | e_X, e_Y, e_Z |
|---|---|---|
| \|00⟩ | 0.5 | (0.5, 0.5, 0) |
| \|01⟩ | 1 | (0.5, 0.5, 1) |
| amplitude-damped Φ⁺, γ = 0.9 | 0.495 | (0.45, 0.45, 0.09) |
| I/4 | 0.75 | (0.5, 0.5, 0.5) |

  In every case the basis-averaged error equals (2/3)δ.
- The two-basis bound F ≥ 1 − e_X − e_Z holds because XX + YY + ZZ ≤ I, with eigenvalues 1 (triplet) and −3 (singlet).

**Ville, mixture, inversion**
- A fixed-weight mixture of nonnegative supermartingales is a nonnegative supermartingale.
- Ville's inequality needs no observability of D_t.
- {sum < 1/α} ⇔ {D_t < D_ub(Err_t)}, by strict monotonicity in D.
- "Simultaneously for all t" holds, so the bound holds at any random time, stopping time or not. Checking only after kept pairs loses nothing, because a violation can only start when D increases.
- `cert._d_ub`: the bracket is valid (one term alone reaches 1/α), and g(0) < 0 always.

**My MC** (3,000 runs × 10,000 pairs; check after every kept pair; α = 0.05). Failure rate (CP 95% upper bound in brackets where shown):

| Scenario | p = 0.05 | p = 0.1 | p = 0.2 |
|---|---|---|---|
| all Ψ⁻ (δ = 1) | 0.028 | 0.035 | 0.045 |
| I/4 | 0.034 | 0.039 | 0.034 |
| Bernoulli 0.3 of Ψ⁻ | 0.028 | 0.033 | 0.037 |
| bad (product \|01⟩) right after an error-free test | 0.013 | 0.020 | 0.030 |
| "lucky" adaptive: bad while errors lag the deficit | 0.039 | **0.046** (ub 0.053) | 0.043 |
| 50/50 mix of amplitude-damped Φ⁺ (γ = 0.9) and \|01⟩ (non-Bell-diagonal) | 0.030 | 0.041 | 0.033 |

All rates are ≤ α. Worst-case adversaries reach 3–4.6%. So the certificate is valid and close to tight in the worst case; the 0–2.5% rates in `mc_cert.py` reflect weak adversaries.

**study27 code**
- **Arm 'b'.** `s26.BASE.setdefault('b', 'b')` leads to `base_of('b') = 'b'`, then Net25 base 'b', then Net24 `ARMS['b'] = ('fleet', None)`. So `s.guard = None` and `s.kind = 'guard'`, and the decision is `ok = pbad <= thr` with no guard. This is exactly Study 24 arm b. study26.py is untouched.
- **Arm 'b' under `o0.044_m0`.** The offset is applied to the controller (`Fs + s.off`), and dec = 0 (tom = 0 is falsy). This is the intended undeclared optimism.
- **Scenario mapping.**
  - `n0.184_a` gives rel = 0.184, ar = True, phi_decl = 1 (undeclared) for kg, b and plug.
  - `fault` passes "-" to Net26 and switches on T2true.
- **True state.**
  - `true_state` F equals `trueF` exactly: max difference 0.0 over a full ion2020 run.
  - The fault T2 is applied to the oracle (time `to`) and to delivered pairs (time t).
  - E is drawn from the *same* true correlators as Ft.
- **Bookkeeping.**
  - Each p has its own test stream (`trng[p]`) on the same delivered stream. Three draws per pair are always consumed.
  - Per-user and network-pooled states are updated with the same T, E.
  - The violation check after every kept pair compares against the true running mean.
  - No division by zero: K is guarded everywhere.
  - Output keys are fixed, so every row has identical columns.
- **Seeds.**
  - nseed and rseed depend only on (hw, idx), which pairs networks across arms and cfgs.
  - Hot users are fixed per network.
  - Pilot and confirmatory runs differ through seed[1] and seed[0] + seed[2] (DEV vs SEEDS). That sum is the seed[3] that `hr` and `trng` use.
- **Counts.** `EXPECT_CELLS = 4·4·2·3 = 96`, with 32 networks each (3,072 tasks), matching `configs()`.

**ptm_corr.** The identity 1 − F = Σe/2 is exact for any state (Lemma F), and the module reproduces `delivered_F` to 2·10⁻¹⁶. Only Σ_B e_B affects certificate validity, so a possible XX↔ZZ labelling swap would not matter.

**Runtime.** About 30 s for an ion2020 hot task and about 5 s for nv2. 3,072 tasks on 2 cores is several hours.
