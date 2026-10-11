# Theory for Study 28: model-checked delivery, a resource converse, and a network-wide guard (11 Oct 2026)

**Status:** draft for review by M. Mattarock. Numerical checks are in `mcheck_out.json` and `lb_out.json`; the adversarial review is in `REVIEW_28.md`.

**Novelty, stated plainly.**
- The tools are standard: e-processes, Ville's inequality, and converse arguments for verification.
- What is new is how they are combined. The tests a user already runs for the model-free certificate (Prop C1) are reused to test the exact condition under which the model-based guard (Theorem 1) is valid. That joins the two layers into one closed loop.
- The converse makes the cost of model-free certification a two-sided statement.

---

## 1. Setting (as in the manuscript)

**Delivery and tests.**
- Pair *i* is delivered only if the guard's conservative fidelity Fg(i) is at least τ.
- Fg(i) is computed from the links' lower confidence bounds, the declared physics model and the declared margin d.
- After delivery the user tests the pair with probability p, using fresh randomness the network does not see. A test is a measurement in a uniformly random basis X, Y or Z.

**Lemma F.** Let e_B be the probability that a test in basis B returns an error. Then

  1 − F = (e_X + e_Y + e_Z)/2,

so a test in a uniformly random basis errs with probability (2/3)(1 − F_true(i)).

**Readout.** Each outcome may be flipped by readout with probability at most s_max = 2r_max(1 − r_max), where r_max is the declared per-qubit readout error.

**Null for pair i.** H0(i): F_true(i) ≥ Fg(i). This is exactly the guard's validity condition: if H0(i) holds for every delivered pair, no delivered pair is below τ.

---

## 2. Proposition MC (validity of the model check)

**Construction.**
- For each tested pair *i*, let q_i = s_max + (1 − 2s_max)(2/3)(1 − Fg(i)), and let E_i ∈ {0, 1} be its observed error.
- For fixed bets λ_g ≥ 0 and weights w_g summing to 1, define

  M_t = Σ_g w_g ∏_{tested i ≤ t} (1 + λ_{g,i}(E_i − q_i)),

  with λ_{g,i} = min(λ_g, 0.9/q_i).
- Raise an alarm when M_t ≥ 1/β₁, where β₁ = 6β/π².

**Statement.** Let ν be the first delivered pair (tested or not) that violates H0. Then

  P(alarm before ν) ≤ β₁ ≤ β,

whatever the network does. The same holds with ν replaced by the first *tested* violating pair, which is a sharper statement.

**Proof.**
- Let G_i contain everything up to and including the generation of pair *i*, including the unobservable F_true(i).
- q_i and λ_{g,i} are G_i-measurable. The test indicator, basis and readout flip are fresh and independent of G_i.
- Under H0(i), P(E_i = 1 | G_i, tested) = s + (1 − 2s)·(2/3)(1 − F_true(i)) ≤ q_i. This expression increases in both s and e, because s ≤ s_max ≤ ½ and e ≤ (2/3)(1 − Fg) ≤ ½.
- So each factor has conditional mean at most 1, and every factor is at least 0.1.
- Hence the process stopped just before ν is a nonnegative supermartingale with initial value 1. Ville's inequality finishes the proof. □

**Corollary (restarts).**
- After the k-th alarm the declared margin d only increases, and the check restarts at level β_k = 6β/(π²k²).
- Under the null as it stands after each restart, the probability of any false alarm over the whole run is at most Σ_k β_k = β.
- A raised margin makes the guard more conservative, so Theorem 1 still applies.

**Numerical checks** (`mcheck_out.json`; errors drawn exactly at the null bound, the worst case):

| Check | Runs | Result | Bound |
|---|---|---|---|
| First-alarm rate, constant / random / adaptive q (10⁴ tests) | 20,000 each | 2.25%, 2.26%, 2.09% | 3.04% |
| Total alarms per run with restarts (10⁴ tests) | 3,000 | 0.021 | 0.05 |

---

## 3. Proposition MC-delay (how fast the check detects)

**Statement.**
- Suppose every tested pair has q_i ≤ q̄ and P(E_i = 1 | G_i) ≥ q_i + δ.
- The expected log-increment of bet g is linear in P(E = 1), so it is at least

  h_g = (q+δ)·ln(1 + λ_g(1−q)) + (1−q−δ)·ln(1 − λ_g q).

- Then, by Wald's identity / optional stopping (increments bounded above, positive drift),

  E[tests to alarm] ≤ min_g [ln(1/(β₁ w_g)) + ln(1 + λ_g(1−q))] / h_g.

**Monte Carlo** (q constant; `mcheck_out.json`):

| q | δ | Mean tests to alarm | Bound |
|---|---|---|---|
| 0.05 | 0.01 | 5,036 | 5,718 |
| 0.05 | 0.03 | 552 | 727 |
| 0.04 | 0.06 | 135 | 195 |
| 0.067 | 0.03 | 710 | 890 |

**Caveats (from the review).**
1. **Constant-q benchmark.** In the network, q_i varies and violations may be sparse. The bound then applies with δ replaced by the average excess over tested pairs.
2. **Slack before the failure.** If the null held with slack before a change point, the log-wealth drifts downward first, and detection takes longer. In the pilot networks this cost about 1.8× before a fault.
3. **Detection needs a mean shift.** The check sees the average excess of the tested pairs' error rate. A failure that pushes only a few pairs just below τ produces a tiny excess. Under a memory fault, 22.6% of ionproj pairs were bad, but the excess was only 0.006, so the check is undetectable within the horizon.
   - This is Proposition N again: sparse per-pair failures are invisible to tests.
   - Only systematic model error is detectable.
   - The expected number of delivered pairs before an alarm is about E[tests]/p.

---

## 4. Proposition LB (converse: the cost floor of model-free certification)

**Statement.**
- Consider any rule that maps the observed record to a lower bound on the fraction of kept pairs that would pass a Φ⁺ test, and that is valid (miscoverage ≤ α) for every source.
- Suppose the rule certifies τ on **every** all-pass record with K kept pairs.
- Then

  max over f > 1−τ of  ((1−p)/(1−p+pνf))^K · P(Bin(K,f) > (1−τ)K)  ≤  α,  with ν = 2/3.

**Proof.**
- Take an i.i.d. source that emits Φ⁺ with probability 1−f and some state orthogonal to Φ⁺ with probability f.
- For any orthogonal state, e_X + e_Y + e_Z = 2 (Lemma F with F = 0). So a random-basis test of a bad pair fails with probability exactly 2/3. The rates per basis may differ; only their average matters.
- Kept and tested pairs are disjoint and independent, and the test/keep pattern does not depend on the states. Hence

  P(all tests pass, bad kept fraction > 1−τ) = E[(1 − νf)^{n_K}] · P(Bin(K, f) > (1−τ)K).

- On that event the rule certifies τ, so this is a violation.
- n_K, the number of tests before the K-th kept pair, is negative binomial, with E[x^{n_K}] = ((1−p)/(1−px))^K. □

**Floor: kept pairs needed to certify τ from perfect pairs** (`lb_out.json`, α = 0.05):

| τ | p | Converse K_LB | Our certificate K_C1 | Ratio |
|---|---|---|---|---|
| 0.9 | 0.05 | 720 | 1,404 | 1.95 |
| 0.9 | 0.1 | 330 | 678 | 2.06 |
| 0.9 | 0.2 | 140 | 315 | 2.25 |
| 0.8 | 0.05–0.2 | 365 / 165 / 70 | 702 / 339 / 158 | 1.9–2.3 |
| 0.95 | 0.05–0.2 | 1,440 / 660 / 280 | 2,808 / 1,355 / 629 | 1.9–2.2 |

**Remarks.**
1. **The "every all-pass record" hypothesis is needed.** A rule that certifies only on the all-pass records with the most tests can partly escape the bound. At τ = 0.9, p = 0.1:
   - certifying on all of them (γ = 1) gives K_LB = 330;
   - on 90% (γ = 0.9), 300;
   - on 50% (γ = 0.5), 205;
   - on 10% (γ = 0.1), the bound is vacuous.

   Our certificate C1 is deterministic at zero errors, so the comparison above is fair.
2. **The bound is tight for i.i.d. sources.** The rule "after exactly K kept pairs, output τ if every test passed" is valid against all i.i.d. sources exactly when the condition holds. So the factor of about 2 is the price of being valid at all times and against adaptive sources, not slack in the converse.
3. **Any test scheme.** Any scheme that rejects every orthogonal state with probability at least ν gives the same bound with that ν. The best local strategy for a Bell state has ν = 2/3 (Pallister et al. 2018). With a Bell measurement (ν = 1) the floor falls by about one third (e.g., 210 instead of 330).
4. **Approximation.** K_LB ≈ (1−p)·ln(1/α) / (pν(1−τ)). So the cost scales as 1/(p(1−τ)), and no model-free scheme can avoid that.

---

## 5. Corollary NW (a network-wide guard)

**Statement.**
- Run every link's confidence sequence at level α/|E| instead of α/U_max (here |E| = 40 links).
- Then, under Theorem 1's assumptions, P(any user ever receives a bad pair) ≤ α.

**Proof.** By the union bound over all links, every link's sequence covers its true value with probability at least 1 − α. On that event every delivered pair has F_true ≥ F(λ^lo) ≥ τ + d ≥ τ. □

**Cost.** The confidence sequences become slightly wider, by a log factor (ln 40 vs ln 4). Study 28 measures the throughput cost.

---

## 6. What the theory predicts for Study 28 (to be checked in the pilot)

- **Systematic model error** (undeclared optimism of 0.044 on ions) gives an excess of roughly 0.01–0.03. That is detectable in roughly 500–2,000 tests, i.e. tens of epochs at p = 0.1–0.2.
- **Persistent noise and memory faults** give sparse threshold failures with an excess of at most about 0.006. They are predicted to be **undetectable** within the horizon.
- **Thin hardware** (NV, SiV) gets 3–100 tests per run: no power.
- **Margin response.** After an alarm the margin rises by an upper estimate of the mean fidelity gap. The mean gap underestimates the constant offset by the guard's average slack, which is why an upper estimate is used. This response is a heuristic; the guarantee comes from the e-process.
- **False alarms:** at most β under the null, including under readout error at the declared bound.
