# Adversarial proof review: Props 1–10 (theory notes of 5, 6, 7, 8 and 11 Oct 2026)

**Reviewer stance.** Probability and statistics referee. I hunted for errors on purpose, and I report findings without softening them.
**Sources read.**
- Project docs `claude/THEORY_NOTE_2026-10-05/06/07/08/11.md`. The local copy of the 11 Oct note is identical to the project copy.
- `G4_PREREG`/`G4_RESULTS` (Prop 6′), `G5_RESULTS` (Prop 6″), `G6_PREREG` (alarm restart), `STUDY24_PREREG`/`PLAN` (Prop 7), `STUDY25_PREREG` (Block D/T).
- `EVIDENCE_LEDGER.md` E65–E101.
- `24_ai_v2_hardware/study24.py`, the only guard code available locally.

**Monte Carlo.** Scripts are in this folder. `python3 run_all.py` reproduces every number below in 142 s on 2 cores (numpy/scipy only, fixed seeds). Every miss rate carries a 95% Clopper–Pearson CI.

---

## 0. Bottom line

1. **The core per-path guard (Prop 6) is correct.** It is a textbook application of Ville's inequality to Robbins' Beta mixture, plus a union bound over at most L_max links and a monotonicity step. It holds under adaptive sampling and data-dependent routing. MC: ever-miss stayed below the nominal level in every configuration tried, typically 5–20× below.
2. **Contribution 2 as written is false.** It claims "P(a *user* ever receives a below-threshold pair) ≤ α". Prop 6 proves this **per fixed path**. The router picks among candidate paths using data. For a request whose candidate paths use the link set U, the valid bound is |U|·α/L_max, not α. In a 5×5 corner-to-corner request, |U| = 40 and L_max = 8, giving 5α = 0.25. MC with a Ville-tight per-link sequence: 0.21 [0.19, 0.22] per user at k = 40 candidate links, against the claimed 0.05. With the paper's own Beta mixture, the slack hides the failure until about k = 70 (0.048 [0.038, 0.059]). The proof does not cover the user claim.
3. **Prop 10 is false as stated, and its conclusion is mis-framed.**
   - (a) ⇒ (b) fails: own counts can be exactly binomial while p depends on a per-trial shared environment.
   - "Over-dispersion of own counts" is neither necessary nor sufficient for the AI prior to be invalid.
   - MC: own-count dispersion 1.000, corr(own, neighbour) = 0.49–1.0. The AI-prior guard's miss rises to about 2.8× the independent control, and an epoch-refit prior reaches 0.053 [0.048, 0.058] at nominal 0.05.
4. **Prop 7 is a correct identity but is used for a claim it does not support.** Contribution 3 says "any learned prior enters the guard safely". Validity needs the prior to be conditionally independent of the link's own data given the parameters. Prop 7 is silent on this.
   - Counterexample: a prior fit on the link's own data (Occam term 0) gives an ever-miss of 0.14 [0.135, 0.145] at nominal 0.05 after 2,000 looks, and 0.024 at nominal 0.00625 (3.8×).
5. **Prop 9 needs two corrections.**
   - Its guarantee holds only if the jump bound is **deterministic**. Study 25 uses Gaussian jumps with B = 3 sd, so the honest per-path bound is α + P(any declared bound is violated on the path). MC: 1.6% of links violate B = 3 sd over 11 re-alignments, which is 2.5× the per-link level.
   - "Optimistic by up to δ" is wrong: violations **accumulate** along the carry chain. MC: the overshoot exceeds the largest single violation in 412/20,000 links (random walk) and in 4,409/20,000 (Djb).
6. **The G-series safety bar "bad paths / delivering paths ≤ 5%" is not implied by Prop 6.** It is a conditional (selected) rate, the same base-rate trap Prop 1 describes. If every candidate path is truly bad, every path that delivers is bad: the ratio is 100% while P(path ever bad) ≤ α holds.
7. **Most other "propositions" are known results or elementary.**
   - Identity (1) is Storey's pFDR identity.
   - Prop 2 is the Efron/Storey/Sun–Cai lfdr relation.
   - Prop 4 is Hoeffding plus a union bound.
   - Prop 7 is algebra.
   - Prop 8 is a measurability remark.
   - Only Prop 6 (with 6′, 6″ and 9 as corollaries) deserves "Theorem", and it is an application of classical tools, not new probability.

---

## 1. Per-proposition table

Verdict key: **C** = correct; **CG** = correct with gaps; **X** = incorrect (counterexample); **NP** = no proof given; **H** = heuristic presented as a proposition.

| # | Statement (as given, condensed) | Proposed class | Verdict | Main gaps |
|---|---|---|---|---|
| (1) | r = π₀α / (π₀α + (1−π₀)β) | Known: Bayes; Storey 2003 pFDR identity | C | Needs P(δ = 1) > 0. Not new. |
| (2) | Headroom-histogram law r(z) = ∫Φ·dP / ∫Φ·dP under A1 | Known (plug-in of (1) with Gaussian error) | C | Requires e ⟂ h, which a controller using the same window for d and s violates. Validated empirically, not proved. |
| 1 | Any finite z, Gaussian errors: for every ε there is P with r(z) ≥ ε | Lemma (base-rate no-go); cite Storey 2003, Ioannidis 2005 | C | Bounded-error version: "|e| ≤ E, any law" must read E = ess sup e, otherwise α can be 0. Elementary. |
| Cor 2 | No fixed-caution rule bounds r across states; P_post(F<τ) ≤ δ under a flat prior is a fixed z | Corollary of 1 | C | "Unless worst-case conservative" applies only to bounded errors; under Gaussian errors no finite z works. |
| 2 | δ = 1{p ≤ t}, p = P(h<0 \| D) under the true law ⇒ r(t) = E[p \| p ≤ t] | Known: Efron 2008; Sun & Cai 2007 | C | t must be fixed (or D-measurable with p conditioning on all of t's information); the 8 Oct note says so. Marginal, not per path. |
| 3 | SE(ŝ²)/s² ≈ √(2/N)(1 + (σ_w² + A²/12)/s²) ≡ 1/I | Definition + heuristic | CG/H | Valid only if the N windows come from N **distinct** links (iid λ). With K windows per link (the 7 Oct definition, N = KL), it is optimistic by 2–3.4× and ŝ² is biased (MC 7d). Also treats σ_w² as known and uses a Gaussian 4th moment. The I-regime thresholds (3, 1–2) are empirical. |
| 4 | r(t̂) ≤ δ + t̂√(ln(\|𝒯\|/η)/(2C)) w.p. ≥ 1−η | Lemma (Hoeffding 1963 + Bonferroni) | CG | Needs iid p_i drawn from the same law as the future attempt, and the future attempt independent of the window (stated as violated in practice: S1). MC 7e: 0/4000 bound failures under iid, but the plug-in r(t̂) > δ in 31%. Not a guarantee for the deployed controller. |
| 5 | (a) window lag Δ(1−(t−t_f)/T); (b) KL ≈ Δ²/(2σ_w²), shrinkage if Δ ≲ σ_w√(2 ln((1−ε)/ε)); detection k ≳ 2 ln(1/α)σ_w²/Δ² | Remark (heuristics) | H / NP | (a) is exact for a uniform window. (b) and k are order-of-magnitude (Wald SPRT sample size). No proof; should not be a "Proposition". |
| 6 | Per-link Beta(½,½) mixture CS at α/L, lower end → λ_lo; deliver iff F(λ_lo; w) ≥ τ ⇒ for every path, P(ever deliver F < τ) ≤ α | **Theorem** (application of Ville 1939, Robbins 1970; cf. Howard et al. 2021, Waudby-Smith & Ramdas 2024) | CG (per path); **X for the per-user claim** | See §2.1–2.3. Unstated assumptions: readout factor r known exactly; calibration bits drawn from the same λ as delivered pairs, with parity-measurement selection independent of outcome; every path has ≤ L_max links (check the best-of-k disjoint-path block); F coordinatewise nondecreasing (only numerically checked, 1,500 trials); in code, the CS grid must contain the true λ. |
| 6′ | Restart at re-alignment, Beta lower bound L on p_reset from drifting bits, λ_now ≥ λ(L) − g(t − t_reset), α spent 6α/(π²c²) | Corollary | CG | Needs (i) the lower end nondecreasing in K at fixed N (asserted, not proved; proved in the appendix; MC 4a 0/446,175 violations); (ii) g an upper bound on the decay rate; (iii) "6α/(π²c²) per path" (G4) vs "/L_max per link" (Prop 9): the per-link version is the correct one; (iv) pairs stored across a re-alignment must be checked against their generation cycle's bound. |
| 6″ | Exact-drift mixture M_t(θ) with Bin(k_j \| n_j, p_j(θ)), CS = {M < L_max/α_c} | Corollary | CG | (i) Epoch counts are Poisson-binomial, not binomial: M is a **super**martingale, not a martingale (still fine via AM–GM; proved in the appendix). (ii) g must be known exactly; MC with g 50% under-declared doubles the miss (0.0006 → 0.0014, still under nominal only because of slack). (iii) Alternatives with p ∉ [0,1] must be clipped or excluded. |
| α-spend | Σ_c 6α/(π²c²)/L_max = α/L_max | Known (weighted Bonferroni, Basel sum) | C | Data-dependent restarts (G6 alarm) are also valid, but need a sentence: the new CS uses only post-stopping-time data (strong Markov for conditionally iid bits). MC 4d: 0.0049 and 0.0063 vs 0.05 with spending; 0.19–0.55 without. |
| 7 | CS_t(π) = {θ : ℓ(θ̂) − ℓ(θ) < log(1/level) + O_t(π)}, O_t ≥ 0; the prior acts only via O_t; gain ≤ O_t(π₀); Gaussian O_t formula; hedge cost ≤ −log w | Remark (algebraic identity) | C (identity) / **X as used** | It is a rewriting of M_t = ∫e^ℓ dπ / e^{ℓ(θ)}. It says nothing about **validity**, which needs π ⟂ own data \| parameters. Contribution 3's "any learned prior enters the guard safely" is unsupported (MC 6, 7a). |
| 8 | Unannounced fault: decisions in [τ_f, τ_f+Δ) have the no-fault law; E[bad] = E[N_Δ]; no past-data rule can do better; exposure decomposition | Remark / no-go lemma | CG | "τ_f independent of F_{τ_f}" is ill-posed (τ_f is F_{τ_f}-measurable); it must be independent of the whole no-fault process. "Every pair delivered in the window is bad" needs the pair generated after τ_f. Claim 3 is overstated; the correct necessary condition is sup_t P(deliver through e in [t, t+Δ)) ≤ α, which is not "never deliver". Claim 4 is a definition. Assumes the fault leaves heralding and waits unchanged until τ_f + Δ. |
| 9 | comb_c = max(CS_c, comb_{c−1} − B); if \|θ_c − θ_{c−1}\| ≤ B always, P(∀c,t: comb_c ≤ θ_c) ≥ 1 − α/L_max | Corollary of 6/6″ | CG; one claim **X** | (i) Only the one-sided θ_c ≥ θ_{c−1} − B is needed. (ii) With random jumps the guarantee is α/L_max + P(∃ violation), not "unchanged" (MC S2: violations 1.6% vs level 0.6%). (iii) "Optimistic by up to δ" is false; overshoot ≤ the sum of violation excesses along the carry chain (MC S4, S6). (iv) "B → 0 recovers gpersist" is false: gpersist pools counts; comb with B = 0 takes a running max of separate bounds. |
| 10 | (a) own counts exactly Bin(n, p(λ)) ⇔ (b) p independent of E; under (b) any prior from other links is a valid mixing prior | — (withdraw; replace with Lemma B below) | **X** | (a) ⇒ (b) fails when E varies per trial (counterexample in §2.6, MC 6: dispersion 1.000, correlation up to 1.0). (b) ⇒ independence is correct. The consequence "coupling ⇒ over-dispersion ⇒ breaks the baseline too" is false in both directions (§2.6). |

---

## 2. Detailed issues

### 2.1 Union bounds: links, paths, users, network (Prop 6, contribution 2)

- **Per fixed path: correct.** Each link's CS runs at α/L_max. A fixed path P with |P| ≤ L_max has
  P(∃ e ∈ P, ∃ t: CS_e misses) ≤ |P|·α/L_max ≤ α.

  On the complement, F(λ_lo; w) ≤ F(λ; w) for every attempt, so no bad pair passes. The link's CS is shared by all paths through it, which is fine.
- **Per user/request with route choice: NOT proved, and false in the worst case.** `study24.py` picks `path = argmax_c Σ log est[c]` among all candidate paths (shortest paths, or k disjoint paths). The user's bad event is contained in ∪_{e ∈ U} {CS_e misses}, where U is the union of the candidates' links. The only valid bound is |U|·α/L_max. Data-dependent routing can steer onto a miscovering link: a "best-looking" path is exactly one whose lower bounds are high. In a d_x × d_y Manhattan box, |U| = 2 d_x d_y + d_x + d_y. For d_x = d_y = 4 (corner to corner, L = 8), |U| = 40, so the per-user bound is 5α.
- **MC3** (k candidate paths, each with one marginal link sitting at the threshold; per-link level 0.05/8):

  | k (links in U) | Beta mixture (paper's guard) | Ville-tight tilted LR | valid bound k·α/L_max |
  |---|---|---|---|
  | 1 | 0.0007 [0.0006, 0.0009] | 0.0057 [0.0053, 0.0062] | 0.006 |
  | 8 | 0.0056 [0.0045, 0.0069] | 0.045 [0.042, 0.048] | 0.05 |
  | 40 | 0.028 [0.022, 0.034] | **0.207 [0.192, 0.222]** | 0.25 |
  | 70 | 0.048 [0.038, 0.059] | **0.327 [0.305, 0.350]** | 0.44 |

  The theorem must be stated for any valid CS. The tilted-LR column shows that the proof structure permits per-user risk of 4–6× α. The paper's Beta mixture survives empirically only because it is about 8× conservative.
- **Fixes**, any one of:
  - (a) state the guarantee per path and drop "per user";
  - (b) run each link at α/U_max, where U_max is the largest candidate-link union over requests;
  - (c) commit each request to a path chosen from data independent of the guard's data;
  - (d) state per request: P ≤ |U_req|·α/L_max.
- **Network-wide:** P(any bad pair anywhere) ≤ |E|·α/L_max. That is 0.25 for the 5×5 grid and vacuous (10.9) for the 30×30 grid. The paper must not imply a network-level guarantee.
- **Path length:** the best-of-k block uses k = 3 and 8 *disjoint* paths. Disjoint paths are generally longer than the shortest path. If any has more than L_max links, its per-path bound is |P|·α/L_max > α. Check `drift_queue_des_g1.py`.

### 2.2 Adaptive sampling and data-dependent routing (filtration)

- The mixture is a test martingale in the bit-level filtration whenever each new bit is conditionally Bern(p) given the past. Sample sizes may be any predictable function of the past, and optional stopping and continuation are free (Ville covers all times).
- In `study24.py` the calibration sizes are Poisson(ρ_cal·R·T), independent of routing. Sampling there is not even adaptive.
- **MC2** (p = 0.9): an adversarial rule sampled 400 bits when the running estimate was optimistic and 2 otherwise. An LCB-driven "routing" rule sampled 200 when the LCB cleared the threshold and 10 otherwise. Neither increased the miss rate:
  - adversarial: lower miss 0.00085 at level 0.05, and 0.00025 at 0.00625;
  - LCB-driven: 0.0022 and 0.00025.
- **Hidden assumption:** whether a pair is parity-measured (calibration) or delivered must not depend on its own outcome. Calibrating only heralds that pass a quality flag correlated with parity would break it.
- **Conclusion:** routing adaptivity does not break per-link coverage. It breaks only the per-user union (§2.1).

### 2.3 "P(a user ever receives a bad pair) ≤ α": the monotonicity step

The chain coverage of p ⇒ λ_lo ≤ λ ⇒ F(λ_lo; w) ≤ F(λ; w) needs:
- (i) p = (1 + rλ)/2 with r > 0 **known exactly**. A wrong readout q shifts λ_lo; this assumption is unstated.
- (ii) the delivered pair's fidelity is the deterministic function F(λ(t_gen); w) of the same λ the calibration bits measure;
- (iii) F nondecreasing in each λ_i at every wait vector.

(iii) is provable for Bell-diagonal/Werner compositions (fidelity is multilinear with nonnegative coefficients in the λ's under depolarising swaps). For the PTM/T1/T2 model it rests on a 1,500-sample numerical check (Study 25 Block M). Either prove it for the PTM model used or state it as an assumption.

Even granting (i)–(iii), this yields **per path**, not per user (§2.1). It also bounds the **ever** event, not the delivered-pair rate r. Moreover:
- **"bad paths / delivering paths ≤ 5%" is not implied.** It conditions on delivering, which selects. If all candidates are truly bad, the ratio is 1 (MC3) while P(path ever bad) ≤ α. The correct reported quantity is (#paths ever bad)/(#paths eligible), or per request.

### 2.4 Prop 7 when the prior sees the link's own data

- **The identity is correct.** log M_t(θ) = log ∫e^{ℓ} dπ − ℓ(θ) = [ℓ(θ̂) − ℓ(θ)] − O_t(π), with O_t ≥ 0 because ∫e^ℓ dπ ≤ e^{ℓ(θ̂)}. Also correct:
  - the Gaussian Occam formula (conjugate normal);
  - the hedge bound O_t(Σ w_i π_i) ≤ O_t(π_k) − log w_k.
- **Validity is a separate condition the note never states.** Ville needs M_t(θ*) to be a (super)martingale under the truth. That holds if π is fixed, or is measurable with respect to a σ-field 𝒢 such that the own bit stream is conditionally iid Bern(p*) given 𝒢 and the parameters. If π uses the link's own data, the CS is the likelihood-ratio region of radius log(1/level) + O_t with O_t ↓ 0. That is the fixed-radius GLR, which by the law of the iterated logarithm misses eventually with probability 1.
- **MC 7a**, prior = point mass at the own running MLE (n = 20 per look):

  | level | after 10 looks | after 100 looks | after 2,000 looks |
  |---|---|---|---|
  | 0.05 | 0.040 | 0.083 | **0.140 [0.135, 0.145]** |
  | 0.00625 | 0.0067 | 0.013 | **0.024 [0.022, 0.026]** |
- **Practical leak points** to audit in code:
  - `ag1` (Study 23/24): the prior comes from `ai1_z(s.n, s.kc)` over all links' latest window. Verify that `cn1.features` excludes the link's own window.
  - EB fleet priors for `gexact`/`fg` estimated from fleet data that include this link's counts (the G3 `own` prior used 512 of the network's own links for the *belief*). Check that it never enters a guard prior.
  - The `gcarry` previous-cycle prior is valid: the previous cycle's counts are conditionally independent of the current cycle's given the levels.

### 2.5 Prop 9 when B is violated, or random

- **Deterministic B: proof correct.** It is induction on the coverage event, plus Ville and a union over cycles.
- **Random jumps (Study 25: Gaussian, jump sd 0.0071, B = 3 sd).** No deterministic bound holds. The rigorous statement is
  P(∃ c, t: comb_c > θ_c) ≤ α/L_max + P(∃ c: θ_c < θ_{c−1} − B).
- **MC5** (12 cycles; per-link level 0.00625):

  | Scenario | P(miss per link) | P(promise violated) | miss \| no violation |
  |---|---|---|---|
  | S0 exact re-alignment | 0/20,000 | 0 | 0 |
  | S1 random walk, \|jump\| ≤ B | 0.00005 | 0 | 0.00005 |
  | S2 iid jitter 0.005, B = 3 sd (D1 cell) | 0.0001 | **0.0156** | 0.00005 |
  | S3 iid jitter 0.005, B = 0.005 | **0.148** | 0.98 | 0 |
  | S4 Djb jitter 0.02, B = 0.005 | **0.997** | 1.0 | — |
  | S5 random-walk steps, B = 3 sd | 0.0001 | 0.0139 | 0.00005 |
  | S6 random-walk steps, B = 0.005 | **0.234** | 0.95 | 0 |

- In S2/S5 the violation probability (1.4–1.6%) exceeds the per-link level (0.6%). Per path (8 links) the rigorous bound becomes about α + 12%. Empirically the small overshoots (≤ 0.0006) are absorbed by the Beta slack, but that is luck, not proof.
- **Accumulation.** The note says a violation of size δ makes the bound "optimistic by up to δ". On the coverage event the overshoot obeys e_c ≤ max(0, e_{c−1} + δ_c), so it is bounded by the **sum** of excesses along a carry chain. Overshoot exceeded the largest single violation in 2 (S3), 4,409 (S4) and 412 (S6) of 20,000 links. Max overshoot in S6 was 0.032 with B = 0.005.

### 2.6 Prop 10: direction of implication, and what actually matters

- **(b) ⇒ (a) and (b) ⇒ cross-link independence given λ: correct.**
- **(a) ⇒ (b) is false.** Take a per-trial environment E_i ~ Bern(p̄). Let own_i = E_i with probability ρ, otherwise an independent Bern(p̄), and let the neighbour bit be built the same way. Then:
  - own bits are exactly iid Bern(p̄), so own counts are exactly Bin(n, p̄) and (a) holds;
  - p(E_i) = ρE_i + (1−ρ)p̄ depends on E, so (b) fails;
  - corr(own_i, nb_i) = ρ².

  The variance argument assumed E is constant within the epoch's n trials. Nothing in the stated setting ("any shared environment E") requires that.
- **MC 6** (p̄ = 0.9, 50 bits/epoch, prior frozen after 3 warm-up epochs, CS on own data from t = 0, one-sided ever-miss over 37 epochs, 8,000 reps):

  | ρ (corr) | own dispersion | Beta guard @0.05 | AI prior (sd 0.3 SE) @0.05 | AI hedged | AI time-split | per-epoch refit @0.05 | @0.00625: beta / AI / refit |
  |---|---|---|---|---|---|---|---|
  | 0 (0.00) | 1.001 | 0.0071 | 0.0093 | 0.0089 | 0.0098 | 0.0046 | 0.0013 / 0.0015 / 0.0001 |
  | 0.7 (0.49) | 1.000 | 0.0050 | 0.0150 | 0.0110 | 0.0095 | 0.0208 | 0.0009 / 0.0018 / 0.0019 |
  | 1 (1.00) | 1.001 | 0.0060 | **0.0265** | 0.0158 | 0.0089 | **0.053 [0.048, 0.058]** | 0.0005 / 0.0028 / **0.0068** |

  With own counts *exactly* binomial, the AI guard's miss rate rises with correlation: 2.8× at ρ = 1, frozen prior. A prior re-fit on concurrent neighbour data reaches the nominal level, and with more looks it exceeds it (cf. 7a). The time-split arm (`ag2t`) removes the effect, as theory predicts.
- **The consequence paragraph is wrong in both directions.**
  - Over-dispersion across epochs from a **slow** shared environment (constant over the run) does *not* break any guard. Conditional on E the own bits are iid Bern(p(λ, E)), and that conditional parameter is what the delivered pair's fidelity depends on.
  - Conversely, a **fast** shared environment can couple the prior to the own data with zero over-dispersion.
  - What matters for the baseline guard is stationarity of the own p on the CS's accumulation time-scale; epoch-to-epoch varying E is drift. What matters additionally for informed priors is conditional independence of π from the own stream given the run's realised parameters (Lemma B in the appendix draft).

### 2.7 Prop 8

- Fix the independence hypothesis: τ_f must be independent of the entire no-fault process and of the controller's randomisation.
- Claim 1 also needs the fault to leave all observables (heralding rates, waits) unchanged until τ_f + Δ.
- Claim 2 needs "pairs generated after τ_f".
- **Claim 3, stated correctly:**
  - against an oblivious adversarial fault time, a per-user guarantee P(bad) ≤ α forces sup_t P_nofault(a pair generated in [t, t+Δ) is delivered through e) ≤ α;
  - against a random fault time with a known law, it forces E_{τ_f}[that probability] ≤ α / P(fault).

  This is a throughput cap, not "not delivering at all".
- The "k ≳ 2 ln(1/α)σ_w²/Δλ²" detection delay is a heuristic (Prop 5), not a bound.

### 2.8 Smaller points

- **Prop 6 (two-sided vs one-sided).** The Beta-mixture CS is two-sided, but only its lower end is used. MC1: the realised one-sided miss is 10–40× below level, e.g. 0.00015–0.00065 at level 0.00625 with 50-bit epochs. A one-sided mixture (prior on q ≥ p), or a stitched/LIL boundary (Howard et al. 2021), would buy back throughput legitimately.
- **Evidence.** "0 miscoverage in 2,000 simulated repetitions" (E68) cannot distinguish level 0.00625 from 0.0007. Likewise "0 bad pairs in tens of millions" is expected given an ~8× conservative bound plus exact physics by construction. It is not evidence about the theorem.
- **Prop 6′ wording.** G4 says "6α/(π²c²) per path". The correct per-link allocation is 6α/(π²c²L_max), with c the link's own cycle index (links have different phases).
- **Prop 6″, uncertain g.** Take the CS for θ under each g in a declared set and use the minimum λ_now bound across the set. This is valid with no extra α if the true g lies in the set, and replaces "g known exactly".
- **Code-level check** (not verifiable here: `s23.cs_lower_mix` not provided). The λ grid is truncated to [μ − 8sd, μ + 6sd]. If a true λ lies below the grid (e.g. the `outlier` pattern), the reported lower end can exceed the truth. The CS lower end must also be rounded *down* to the grid.

---

## 3. Monte Carlo summary (all reproducible: `run_all.py`, 142 s)

| Check | Result | Verdict |
|---|---|---|
| MC1: Beta(½,½) CS, optional stopping, 50-bit epochs × 400, p ∈ {0.55, 0.8, 0.95, 0.995} | Two-sided ever-miss 0.0029–0.0075 at level 0.05; 0.00035–0.0013 at 0.00625. One-sided lower miss about half of that. | Valid; ≈7–20× conservative |
| MC1: single bits × 3,000 | 0.039 (p = 0.55), 0.024 (p = 0.95) at 0.05 | Valid; closer to level |
| MC2: adaptive sample sizes (adversarial; LCB-routing) | ≤ 0.017 two-sided, ≤ 0.0022 one-sided at 0.05 | Valid |
| MC3: per-user union | Ville-tight CS: 0.207 at k = 40, 0.327 at k = 70 vs claimed 0.05. Beta: 0.028 / 0.048. | **Per-user claim not supported** |
| MC4a: monotonicity of the Beta lower end in K | 0 violations in 446,175 pairs | Holds (proved in the appendix) |
| MC4b: Prop 6′ under drift | 0.00005 [0, 0.00028] at 0.00625; naive guard 0.108 | Valid; naive breaks |
| MC4c: Prop 6″ exact drift, Poisson-binomial epochs | 0.0006 (g exact), 0.0014 (g under-declared 1.5×) at 0.00625 | Valid; mis-specification doubles the miss |
| MC4d: α-spending over 50 restarts | Spend: 0.0049 (Beta), 0.0063 (tilted) vs 0.05. No spend: 0.19, 0.55. | Valid; spending necessary |
| MC5: Prop 9 | See §2.5 | Valid if deterministic B; random B and accumulation need restating |
| MC6: Prop 10 counterexample | Exact binomial own counts; AI-guard miss up to 2.8× control; refit 0.053 at nominal 0.05 | **Prop 10 false; validity condition is conditional independence** |
| MC7a: Prop 7 own-data prior | 0.14 at nominal 0.05 (2,000 looks); 0.024 at 0.00625 | **Data reuse breaks the guard** |
| MC7b: Prop 1 | z = 3, s = 0.01, η = 0.005 ⇒ π₀ = 0.99977 gives r = 0.506 ≥ 0.5 | Correct |
| MC7c: Prop 2 | r_emp vs E[p \| p≤t]: 0.00258/0.00264, 0.0133/0.0136, 0.0430/0.0434 | Correct |
| MC7d: Prop 3 | iid windows: 0.186 vs formula 0.188. 16 links × 8 windows: **0.369** vs 0.188; 4 × 32: **0.635** vs 0.188. | Correct only for distinct-link windows |
| MC7e: Prop 4 (iid) | Bound failures 0/4,000; plug-in r(t̂) > δ in 31% | Bound holds under iid |

---

## 4. Proposed honest labelling for the paper

| Current | Proposed label | Action |
|---|---|---|
| Identity (1) | Eq. (1), cited (Bayes; Storey 2003) | Keep as an equation, not a result. |
| Law (2) | Model equation | Keep with "under A1"; empirical validation is the content. |
| Prop 1 + Cor 2 | **Lemma 1** (base-rate no-go) | Keep; say "elementary, cf. Storey 2003; Ioannidis 2005". Fix the bounded-error wording. |
| Prop 2 | **Lemma 2** (known; Efron 2008, Sun & Cai 2007) | One line plus citation; keep the scope correction (marginal; threshold information). |
| Prop 3 | **Definition** (identifiability index) + heuristic remark | Demote. Define N as the number of distinct links (or the effective sample size); state the iid assumption; regime cut-offs are empirical. |
| Prop 4 | Remark, or cut | Not a guarantee for the deployed controller (dependence). Cut or move to the SM. |
| Prop 5 | Remark (fault mechanisms) | Merge with Prop 8. |
| Prop 6 | **Theorem 1** (per-path anytime guard) | Keep; state per path; list assumptions A1–A6 (appendix); per-request corollary with the |U|·α/L_max factor or α reallocated. |
| Prop 6′, 6″, α-spending | **Corollaries 1–2** of Theorem 1 | Keep; add the monotonicity lemma and the Poisson-binomial supermartingale lemma; fix the "per path" spending wording. |
| Prop 7 | Remark (Occam identity) + **Lemma B** (validity of informed priors) | Demote the identity to a remark; add the missing validity lemma; drop "any learned prior enters safely" unless the conditional-independence condition is stated and the code is shown to satisfy it. |
| Prop 8 | **Proposition** (no-go), with corrected claim 3 | Keep as a short, honestly elementary no-go; claim 4 is a definition. |
| Prop 9 | **Corollary 3** | Keep with: one-sided bound; random-B version α/L_max + P(violation); accumulation statement; drop "B → 0 = gpersist". |
| Prop 10 | **Withdraw** | Replace with Lemma B plus a remark on time-scales (slow shared noise is harmless; fast shared noise couples priors without over-dispersion; epoch-scale noise is drift). Block T's φ-deflation stays "quasi-likelihood heuristic". |
| Contribution 2 | Rewrite | "per-path" (or per request with the union factor). Report bad paths / eligible paths, not / delivering paths. |
| Contribution 3 | Rewrite | "Any prior that is conditionally independent of the link's own calibration stream given the link parameters (e.g. built only from other links' data, with no per-trial shared noise, or from time-disjoint data) preserves Theorem 1." |

Net: **one theorem with three corollaries, two lemmas (one known, one elementary), one no-go proposition, one definition, and remarks.** The probabilistic content is classical (Ville, Robbins mixtures, Bonferroni). The paper's novelty should be presented as the *application* and the system-level design, not as new probability.

The companion `PROOFS_APPENDIX_DRAFT.md` gives clean statements and proofs for the surviving results.
