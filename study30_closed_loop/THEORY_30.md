# Study 30 theory: a closed loop with a guarantee (11 Oct 2026)

Study 29's response after a model-check alarm worked in simulation (0 post-alarm bad pairs in 512 runs) but was a heuristic.
This note replaces it by a rule with a proof (Theorem 2), and fixes the detection failure seen on IBM hardware (Study 31, W3)
with a check that cannot accumulate "debt" (Proposition D).

## Setting and notation
- Pair i has features w_i (path, link waits, storage time hold_i), known when the pair is made.
- The network's model gives fidelity F_M(λ; w) for link parameters λ. **(M)** F_M is nondecreasing in every link parameter.
- True fidelity: F_i = F_M(λ; w_i) − Δ_i. Δ_i is the model offset (optimism).
- A tested pair is measured in a uniformly random Pauli basis. Its error indicator is E_i, with
  P(E_i = 1 | past, w_i) = s_i + (1 − 2 s_i) · (2/3)(1 − F_i), where s_i ∈ [0, 1/2) is an unknown parity-flip (readout) probability.
- λ^lo_t, λ^hi_t: lower and upper ends of the guard's mixture confidence sequence (CS) for each link, from link data up to the previous epoch.

**Lemma A (one-sided test of fidelity).** If F_i ≥ 1/4 and readout acts as a state-independent parity flip with probability s_i ∈ [0, 1/2), then 1 − F_i ≤ 1.5 · P(E_i = 1 | past, w_i).
(With asymmetric readout, where the flip probability depends on the outcome, Lemma A needs the error rate e ≤ s_c/(s_c + s_e). This is checked for Study 31b.)
*Proof.* P − (2/3)(1 − F) = s (1 − (4/3)(1 − F)) ≥ 0. ∎
With a calibrated lower bound s_lo ≤ s_i, the sharper 1 − F_i ≤ 1.5 (P − s_lo)/(1 − 2 s_lo) holds, because (P − s)/(1 − 2s) decreases in s for P < 1/2.

## Assumptions
- **(B1) Link CS, upper end.** Each link's parameter is constant. The upper end λ^hi uses the guard's own mixture CS at level α_hi/|E|, so all links' upper ends hold at all times with probability ≥ 1 − α_hi (Ville, union over |E| links).
  - The mixture set {λ : mix_t / lik_t(λ) < 1/level} is an interval (the likelihood is concave in λ). Its upper end costs nothing beyond the level.
- **(B2) Offset class after the FIRST alarm.** For every pair made after the first alarm: Δ_i = θ φ_i, with one deterministic θ ∈ [0, θ_max] for all later windows.
  - φ_i ∈ [0, φ_cap] is a declared shape, known when the pair is made.
  - Examples: constant (φ_i = 1); storage-proportional (φ_i = min(hold_i / H̄, φ_cap)).
  - Pairs before the first alarm are unrestricted, **but** (B2) then requires that the first alarm come after any onset of the offset.
  - A false alarm before an onset breaks (B2): the first window starts with Δ = 0, U falls toward the slack, and after the onset θ > U until the check alarms again. Corollary O bounds this case.
- **(B3)** Private randomness for test selection and basis (as Proposition C1).
- **(B4)** A declared maximum offset θ_max per unit φ. The margin starts there after an alarm. Without (B4), set θ_max = 1/φ_cap (Δ ≤ 1 always).
  - Then the first post-alarm pairs are all probe-tested until the CS falls. This is valid but slow.
  - Study 30 uses θ_max = 0.10, about twice the largest measured model gap (0.02–0.044, USTC recipe). Offsets above θ_max are not tested.

## The rule (arms kgMC, kgMCp, kgMCs)
1. **Before the first alarm,** run as Theorem 1 with margin 0, plus a model check (Prop. MC, or Prop. D below).
2. **At an alarm,** restart the offset CS window (the k-th window at level α′_k = 6α′/(π²k²)) and set U = θ_max.
3. **Each tested or probe-tested pair i in the window** contributes
   a_i = F_M(λ^hi_{i−1}; w_i) − 1 + 1.5 E_i,
   together with its shape φ_i and the known bound a_i ≤ â_i := F_M(λ^hi_{i−1}; w_i) + 1/2.
4. **Offset CS (time-uniform).** With the fixed bet grid ν_j = 0.01 · 2^j for j = 0, …, 6 (0.01 to 0.64), capped per pair at ν_ij = min(ν_j, 0.9/â_i):
   K_t(m) = (1/J) Σ_j Π_{i ≤ t} (1 + ν_{ij} (m φ_i − a_i)),
   U_t = min( U_{t−1}, sup{ m ∈ [0, θ_max] : K_t(m) < 1/α′_k } ), with U_t = 0 if even m = 0 is excluded.
   - K_t(0) ≥ 1/α′_k means the tests look *better* than the model at its upper link bounds (a pessimistic model). It is reported as a diagnostic.
5. **Delivery.** A pair j is delivered only if F_M(λ^lo; w_j) − U_t φ_j ≥ τ.
   - A pair blocked only by the margin is probe-tested instead, and joins the window.
   - The model check keeps running against the new guard. A later alarm means (B2) failed, and the rule goes back to step 2.

## Theorem 2 (post-alarm safety)
Under (M), (B1)–(B4) and Theorem 1's assumptions for user u's links, for every user u:

  P( u receives a pair with F < τ at any time after the first alarm ) ≤ α + α_hi + α′.

With Theorem 1's links at α/|E| (Corollary NW), the same bound holds for "any user, anywhere".

**Proof.**
- **The three good events.**
  - G1: the lower ends hold for u's links at all times. P(G1ᶜ) ≤ α (Theorem 1).
  - G2: the upper ends hold for every link at all times. P(G2ᶜ) ≤ α_hi (B1).
  - G3: θ ≤ U_t at all times. Bounded below.
- **Step 1: each a_i over-estimates the offset on average.** For a pair i in a window, let c_i = 1{λ ≤ λ^hi_{i−1}}. Because λ is a fixed constant, c_i is determined by the past (predictable). On c_i = 1:
  E[a_i | past] ≥ F_M(λ; w_i) − 1 + (1 − F_i)   (by (M) and Lemma A)
             = Δ_i = θ φ_i                    (by (B2)).
- **Step 2: a supermartingale at the true θ.** Replace each factor by 1 when c_i = 0: K̃_t(m) = (1/J) Σ_j Π (1 + c_i ν_{ij}(m φ_i − a_i)).
  - Every factor is ≥ 0.1 > 0, because ν_{ij} ≤ 0.9/â_i, a_i ≤ â_i and m φ_i ≥ 0.
  - E[factor | past] ≤ 1 at m = θ, by Step 1.
  - So K̃(θ) is a nonnegative supermartingale, starting at 1 in each window. The window starts at the alarm, which is a stopping time.
- **Step 3: Ville.** P(∃t : K̃_t(θ) ≥ 1/α′_k) ≤ α′_k. On G2, K̃ = K.
  - Each ν_{ij} is fixed in advance and ≥ 0, and φ_i ≥ 0, so K_t(m) is nondecreasing in m. Hence K_t(θ) < 1/α′_k implies U_t ≥ θ.
  - Summing over windows: P(G2 ∩ G3ᶜ) ≤ Σ_k α′_k ≤ α′.
- **Step 4: no bad delivery on the good events.** On G1 ∩ G2 ∩ G3, every pair delivered to u after the alarm satisfies
  F_j = F_M(λ; w_j) − θ φ_j ≥ F_M(λ^lo; w_j) − U_t φ_j ≥ τ.
  So P(a bad delivery to u after the alarm) ≤ P(G1ᶜ) + P(G2ᶜ) + P(G2 ∩ G3ᶜ). ∎

**Corollary O (onset class).** Suppose Δ_i = θ φ_i · 1{t_i ≥ t₀} with unknown onset t₀ (including t₀ = 0 and t₀ = ∞). Before t₀ the model is exact, so the check's null holds on G1. A first alarm before t₀ is therefore a false alarm, which has probability ≤ β on G1 (Prop. MC/D). Hence

  P( u receives a bad pair after the first alarm ) ≤ α + α_hi + α′ + β.

**Remarks.**
1. **What the theorem does not cover: pairs before the alarm.** By Proposition N, no data-driven rule can protect them.
   - The always-on variant (kgMCa: one window from t = 0, margin starting at θ_max) covers every pair **only if (B2) holds from t = 0 with a fixed θ (no onset)**. It replaces (A0) with (B2) plus (B4), and pays for this in throughput.
   - Under a late onset, kgMCa's running minimum U sits near the pre-onset slack. It stays below θ until the check alarms and opens a new window. Study 30 pre-registers kgMCa in L0.044 as an expected failure.
   - A fixed margin θ_max from t = 0 is equally provable under (B2) and (B4) for the constant class, and needs no data. It is the static competitor (baseline '_fix').
2. **How tight the margin is.** U_t − θ → average of [F_M(λ^hi) − F_M(λ)] + 1.5 s̄(1 − (4/3)(1 − F̄)), plus a stochastic term of order sqrt(2 Var(a) ln(J/α′)/n).
   - The first two terms are the price of using only a one-sided, model-free reading of the tests. Lemma A's s_lo version removes the readout part.
   - Unit check (core30.py): with no slack, excess 0.018 after 9,000 tests; with 0.01 of link slack, excess 0.028. Coverage was 0.997–1.000 at level 0.025.
3. **Not covered: changes after an alarm.** A change that breaks (B2) after an alarm is not covered by the theorem. The check is still watching: an increase makes the guard's null false, the check alarms, and a new window starts. Protection resumes after that alarm, as in Proposition N.
4. **(B2) needs exact proportionality.** With heterogeneous offsets the CS estimates a weighted average over the tested and probed pairs, and pairs with above-average offset are not protected. Study 30 tests three cases: the constant class under a storage-proportional offset, the reverse, and per-link heterogeneous offsets (out of class for every arm).
5. **The union bound is conservative.** Both link ends come from the same mixture martingale, so per link G1ᶜ ∪ G2ᶜ is bounded by the larger of the two levels. The α + α_hi union is conservative.

## Proposition D (a model check without pre-change debt)
Null hypothesis H0: P(E_i = 1 | past) ≤ q_i for every tested pair, where q_i is the guard's null bound (Prop. MC).
For any predictable ν_i ∈ [0, 1/q_i), M_t = Π (1 + ν_i (E_i − q_i)) is a nonnegative supermartingale under H0. So
P(alarm under H0) ≤ β₁, and the k-th restart spends 6β/(π²k²), exactly as in Prop. MC.

The false-alarm bound needs H0, which holds on G1 (and on G2 ∩ G3 after an alarm). So P(false alarm) ≤ β + α.

**The plug-in bet (aGRAPA-style).**
ν_i = clip( m̂ / (v̂ + m̂²), 0, 0.5/q_i ), where m̂ and v̂ are the mean and variance of (E − q) over the last 100 tested pairs (ν_i = 0 until there are 10 of them).
- **Debt is limited, not zero.**
  - *When the guard is clearly conservative* (Study 31: q − p ≈ 0.034), m̂ is negative and ν = 0, so wealth stays put. The plug-in debt there was −0.02 nats after phase A.
  - The fixed-bet mixture of Prop. MC instead keeps betting and loses log-wealth at a rate of about Σ_g w_g ν_g (q − p_true). On IBM it was 3.75 nats in debt after phase A, and never alarmed in phase B (peak 2.71 against a threshold of 3.49).
  - *When the guard is nearly exact* (q − p ≈ 0.004, as in the Study 30 simulation before onset), noise in m̂ triggers positive bets, and the plug-in also loses about 1.1–1.3 nats per 1,000 tests (review).
- **Cost.** The plug-in bet needs about 10–100 tests to "notice" an excess. Against a change at t = 0 it is somewhat slower than the best fixed bet.
- **Hybrid default.** The average M = (M_mix + M_plug)/2 is an e-process for the same null, and costs ln 2 nats.
  - It is within a few points of the better component in every regime tried (1,000 tests unless stated; detection rate and median delay in tests):

  | Regime | Mixture | Plug-in | Hybrid |
  |---|---|---|---|
  | Hardware-like (206 tests at −0.034, then +0.064) | 41%, 377 | 85%, 225 | 82%, 258 |
  | Long conservative stretch (2,000 at −0.034) | 0% | 76%, 272 | 70%, 294 |
  | Abrupt, no slack (+0.029 from t = 0) | 79%, 707 | 67%, 727 | 78%, 659 |
  | Null at the bound, 3,000 tests (false alarms) | — | 3.7% | 1.7% |

  - Variants with a lower-confidence plug-in (z = 1–2, window 300) remove the near-exact debt but lose power on hardware-like data (39–52%). They were not adopted.
- **After an alarm**, the provable arms restart the check (with spending) whenever U has fallen by 0.01 since the last restart, so the check watches the current guard with fresh wealth (at most θ_max/0.01 = 10 restarts per window).

**Evidence so far (exploratory, not pre-registered).**
- **Simulation with Study 31-like rates** (q = 0.0915; 206 tests at 0.058, then 457 at 0.155; 1,000 runs):
  - Detection in phase B: mixture 40.5%, plug-in 84.7%.
  - With a 2,000-test conservative stretch: mixture 0%, plug-in 74.3%.
  - Null at the bound: 0/1,000 false alarms within 663 tests for both. Unit check: 14/500 within 20,000 tests at varying q (level 3.04%).
- **Replay of the IBM hardware outcomes** (post hoc; the bet rule was written before the replay, but after seeing Study 31's summary rates):
  - The plug-in check alarms at the 208th phase-B test (of 457), and the hybrid at the 237th. Neither alarms in phase A.
  - On the Aer run: plug-in at the 149th phase-B test, hybrid at the 151st; the mixture alarmed at the 406th.
  - **A confirmatory hardware rerun (Study 31b) must be pre-registered with a fresh seed before any claim.**

## Simulation note (review blocker 4)
In Study 30 the offset is put into the **truth**: extra depolarizing noise lowers F by exactly Δ_i, and the model is unchanged. Studies 28–29 added Δ to the model instead, which let model fidelities exceed 1 for 2.7–63% of attempts, depending on scenario and hardware. Those pairs had q clipped to 10⁻⁶, which inflated the model check's detection power there. Scoring was still correct: bad pairs, false alarms and certificate validity were all judged against the true fidelity. But those cells were less physical. That likely helped detection, and may also have helped Study 29's offset estimate (a central prediction above 1 inflates the estimated offset). It is disclosed as a limitation (ledger E134), and Study 30 re-tests the closed loop with physical scenarios.

## What Study 30 tests
- T: Theorem 2 in simulation, including the forced early alarm that broke Study 28 (H4).
- D: Proposition D against Prop. MC under a late-onset offset (conservative model first).
- Robustness of the shape φ (B2) in both directions.
- Cost against Study 29's heuristic.
- The always-on variant (full guarantee) and its cost.
- Worst-user risk, before and after the alarm.
