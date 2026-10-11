# REVIEW_28: adversarial pre-pilot review of Study 28 (mcheck.py, lb.py, study28.py)

Reviewer: Claude (referee role), 2026-10-11. No source files were edited. Scratch experiments were run in the session scratchpad (they are described below so they can be re-run).

## Verdict

- **No BLOCKER.** I found no bug that makes the pilot's numbers wrong:
  - The model-check e-process is valid as implemented.
  - The kgN level change takes effect.
  - The NEPOCH = 90 override reaches every array.
  - lb.py's numbers are right.
- **Seven MAJOR findings.** Two of them change what the study can show:
  - **M1 (power):** on siv and nv2, and in the fault scenario on every hardware, the check cannot detect anything within the 90-epoch horizon. Those kgM/kg comparisons are null by design, and the pre-registration has to say so up front.
  - **M2 (margin update):** the update rule has no upper bound. Three test errors in a row at the start of a segment raise `s.dec` by about 1.45, which turns delivery off for the rest of the run.
- **Proposition LB:** the conclusion is right, but the proof as written has a false step (the "same law" claim, M5). The statement also needs an extra hypothesis (certify with probability 1, M6); without it the bound becomes vacuous.

---

## What I verified (no action needed)

| Check | Result |
|---|---|
| Lemma F in the simulator | `ptm_corr.py` self-test: max \|1-(eX+eY+eZ)/2-F\| = 2.2e-16. Truth `Ft` and guard `Fg` use the same `ptm.delivered_F`, so under '-' a violation can only come from CS miscoverage (or non-monotonicity of F in lambda, already covered in earlier studies). |
| Predictability of q_i | `Fg(i)` is computed from `lamlo` (previous epoch's counts), the pair's own waits `w1,w2,hold` (from `s.rng`), and `s.dec` (past test outcomes only). The test coin, basis and outcome come from `s.trng`, which nothing else in the network reads. Take the filtration G_i = everything up to and including pair i's generation, which includes the unobservable `Ft_i`. Then q_i is G_i-measurable and P(E_i=1 \| G_i) = mean_b eB_b = (2/3)(1-Ft_i). Ville holds for any filtration, so the unobservable `Ft` in G_i is fine. |
| Bets and cap | Fixed `LAMS >= 0`, with `lam <= 0.9/q`, so each factor is at least 0.1 > 0. Clipping q up to 1e-6 is conservative: if the true P(E) is below 1e-6, clipping only helps. If `Fg > 1` (possible with off = 0.044), the pair necessarily violates the null and lies after the stopping point. |
| Stopping at the first violation | "Pair i violates" (`Ft_i < Fg_i`) is G_i-measurable, so the process stopped just before the first violation is a nonnegative supermartingale, and Ville gives P(alarm before first violation) <= level_1 = 0.0304. An alarm on the violating pair itself is not covered, and the code agrees: the violation time is set before the test at the same `t`, and `first_alarm < first_null_viol` is strict (study28.py:95, :123). |
| Null over ALL delivered pairs | Valid but weak. The same argument holds with "first **tested** violating pair": the freeze decision uses `T_i`, which is known before `E_i`. That version is strictly sharper. See M3. |
| Tests during warm-up | Coins are drawn for every delivered pair, `mc.update` runs whether or not `meas` is set, and `first_null_viol` is set whether or not `meas` is set. These are consistent with each other and with the theorem. |
| Synthetic false-alarm MC (`mcheck_out.json`) | 0.021-0.023 against level 0.0304, including an adaptive q that depends on the previous E. Delay means sit below `delay_bound` in all four cases. |
| C1 under kgM feedback | The network now adapts to past `E` and `T`, but `T_i` is fresh and drawn after delivery, so C1's supermartingale (predictable states) still holds. |
| kgN | Ran `Net28(...,'kgN',...)` on all 4 hardware types: `lvl = 0.00125 = 0.05/40` vs 0.0125 (Umax 4) or 0.00714 (ionproj, Umax 7). `st(10)` lower bounds are elementwise <= kg's and all <= true lambda. Nothing in `g1.Net / Net24 / Net25 / Net26.__init__` calls `st()` or reads `s.lvl` (the only cached state is `s.cache`, built lazily in `st`), so overwriting `lvl` after `super().__init__` and clearing `cache` is enough. Network-wide claim: if every link's CS covers its lambda (probability >= 1 - 40 * alpha/40), then every delivered pair has Ft >= F(lamlo) >= tau + dec >= tau. So P(any user ever gets a bad pair) <= alpha under a correct model (no off, binomial counts, monotone F), and raising `dec` keeps the implication. **Correct.** |
| NEPOCH = 90 | Every reader uses the attribute at run time (`g1.NEPOCH`); none does `from ... import NEPOCH` or uses it as a default argument (grep over s18c/s25/s26/s27/s28). `Net25` gives `NE = 102` (checked), the Block R `draw(er, s.NE)` is sized from it, `E0 = -1`, the maximum epoch used is about 89 (well below the clamp at 100), `FAULT_EP = 45` is inside the horizon, `WARM_EPOCH = 3` is unchanged, and g6's NEPOCH use is not imported. Module copies actually loaded: study23/24/25/corr_net24/hw24 from **s26** (identical to s25's), cert/ptm_corr from s27, g1/ptm_model from s18c. |
| Margin-update predictability | `s.dec` changes only after `E_i` and affects pairs j > i, so q_j stays predictable. `s.dec` is used only in `Fg` (study28.py:89). `Net26.st`'s cache does not depend on it, and neither does the controller (`Fs`, `pbad`, `choose_t`). Raising it does not break anything else. |
| lb.py numerics | Extending the f-grid to [1-tau, 1] (4000 points) gives the same K_LB in all three cases checked. No K in [K_LB, K_LB+200] has lhs > alpha, so the non-monotonicity does not bite. The `floor(.+1e-9)` handles (1-tau)K in floating point correctly. |

---

## MAJOR

### M1. The model check has essentially no power on siv and nv2, or for the fault scenario on any hardware. Pre-register this or change the design.
`study28.py:30-31`, `mcheck.py:44-51`.

I instrumented `Net28` with the check running in shadow mode on arm kg (DEV seeds, idx 0-1):

| hw / scen | tests per run (p=0.1) | mean P(E)-q while violated | delay_bound (tests) |
|---|---|---|---|
| siv '-' / fault / o0.044 | **3-14** | -0.008 to +0.006 | inf |
| nv2 o0.044 | 76-99 | +0.011 to +0.013 | 5,700-21,600 |
| nv2 fault | 33-45 | +0.007 to +0.009 | > 20,000 |
| ion2020 fault (post-fault: 564 tests) | 1,089 total | +0.0007 | inf |
| ionproj fault (post-fault: 1,122 tests) | 2,094 total | **+0.0058** | 25,900 |

ionproj fault is not sparse harm: **22.6% of post-fault delivered pairs are bad** (2,446 bad), yet the mean excess Ft-Fg is only -0.0087. The guard approves pairs with Fg just above tau, so a small model error causes a lot of threshold-crossing harm, while the e-process sees only a mean shift of 0.006 in error probability. A synthetic replay with the measured pre-fault deficit (525 tests at -0.0023) and +0.006 afterwards detects within 1,100 post-fault tests in **0.9%** of runs. At +0.02 it detects in 31%.

**Fixes:**
- Use the pilot to measure tests per run, and the mean excess while violated, for each (hw, scenario, p). Pre-register the predicted detection probability from `delay_bound` or a replay.
- State up front that the kgM hypotheses are tested only where power is at least 0.8, which is probably ion2020/ionproj o0.044 only. Elsewhere, label the comparison as a pre-registered null or "not testable".
- If detecting the fault scenario matters, add more power in ways that keep validity:
  - covariate-weighted predictable bets, for example lambda_i proportional to the pair's sensitivity to T2 (hold time). Any G_i-measurable lambda_i in [0, 0.9/q_i) is allowed.
  - a higher test fraction.
  - a longer horizon.

### M2. The margin update has no upper bound and is very noisy on short segments.
`study28.py:109`.

The update is `s.dec += max(STEP, 1.5*mean(excess))`. With q = 0.04, three consecutive errors at the start of a segment trigger an alarm at k = 1 and at k = 2 (checked with `ModelCheck`), giving `mean(excess) ≈ 0.96`, so **dec jumps by 1.44** and the guard blocks everything for the rest of the run.

This is rare under the null (about q^3 per segment start), but much less rare under faults with P(E) around 0.1-0.2. A single occurrence hands kgM a "0 bad after alarm" record by shutting delivery down, and pilot bars set from it would be contaminated. Separately, the update is biased upward: alarms fire when the running excess is high by chance, and the 1.5 factor converts error probability to fidelity (correct units), not a safety factor.

**Fixes:**
- Cap each increment, e.g. `min(max(STEP, 1.5*m), DMAX)` with DMAX = 0.05.
- Better: set the increment from a one-sided upper confidence bound on the mean gap, and require at least N_MIN tests per segment before it is used. Otherwise step by STEP only.
- Log the number of tests in each segment and each increment, so the pilot shows the update dynamics.

### M3. The `false_alarm` metric checks only the first alarm, against the weakest null, and in stressed scenarios it is close to unable to fail.
`study28.py:95, 123`, `pilot_summary_28.py:40`.

- **(a) Later alarms are never checked.** The restart spending `beta*6/(pi^2 k^2)` exists to cover alarms k >= 2 under the null as it stands after the margin is raised: no pair in segment k violates `Ft >= Fg` with the current `dec`. The metric never checks those alarms, yet they are what drives over-correction (throughput cost) in '-' and after a true alarm.
  **Fix:** add `seg_false_alarms` = the number of alarms k with no delivered (or tested) violation since the previous reset. The bar is sum_k level_k <= 0.05 per run.
- **(b) The null is the weakest valid one.** One untested pair with Ft < Fg - 1e-12, at any time including warm-up, makes every later alarm "true". Under o0.044 the first violation comes at epoch 2-18, so `false_alarm` cannot fire there. Pooling it across scenarios (pilot_summary_28.py:40) dilutes the '-' signal.
  **Fixes:**
  - Also report the sharper, equally valid version: alarm before the first **tested** violating pair.
  - Report false alarms by scenario: '-' and fault-pre-epoch-45 only.
  - Use the per-network bar 0.0304, not 0.05.
- **(c) The violation flag ignores magnitude.** To show alarms are caused by material model error, record the mean (Fg-Ft) over each alarmed segment.

### M4. Readout (SPAM) error is not modelled, and q_i does not allow for it. In practice the check would alarm on readout noise and ratchet the margin.
`study28.py:105`, `mcheck.py:1-11`.

With independent readout flips r per qubit, a perfect pair errs with probability s = 2r(1-r) ≈ 0.02 at r = 1%. That is about half of a typical q (0.04 on ion2020), so the "model check" fails with certainty given enough tests, even when F_true >= Fg. cert.py already carries `rmax`; mcheck does not.

**Fixes:**
- Use q_i = s_max + (1 - 2 s_max)(2/3)(1-Fg) with a declared readout bound.
- Add a readout-error scenario (e.g. r = 0.5%, 1%) that the check must survive in '-'. A referee will ask for this, because the "model-free" framing invites the question.

### M5. lb.py's "same law" step is false as written.
`lb.py:5-7`.

"Conditional on all tests passing, the observed record has the same law as under the perfect source." This fails in two ways:
- **(i) Bases.** For an orthogonal state such as Psi+ (eX=0, eY=eZ=1), a test passes only in basis X. Conditional on all tests passing, the test bases are skewed towards X.
- **(ii) Pattern.** P(all pass \| pattern) = (1-nu f)^{n_K}, so conditional on all passing, the test/keep pattern is tilted towards fewer tests.

The displayed inequality is still correct, but by a different argument. If the rule certifies on every all-pass record, then P_f(violation) >= sum over patterns of P(pattern) * prod_tests E_b[1 - f e_b] * P(Bin(K,f) > (1-tau)K) = E[(1-nu f)^{n_K}] * P(Bin...). This uses E_b[e_b] = 2/3 for **every** orthogonal state (Lemma F: e_X+e_Y+e_Z = 2 when F = 0; the per-basis rates need not be equal) and the fact that kept and tested pairs are disjoint and iid.

**Fix:** replace the "same law" sentence with this product computation, or use the symmetric orthogonal state (I - Phi+)/3 (e_b = 2/3 in each basis), which makes the bases uninformative.

### M6. Proposition LB needs the hypothesis "certifies with probability 1 on the perfect source". With probability gamma < 1 it changes a lot.
`lb.py:6-11`.

A record-measurable rule may use the number of tests n. A rule that certifies only when n_K is unusually large escapes the bound. The best evasion is to certify on the top-gamma tail of n_K. I recomputed the bound under that evasion at tau = 0.9, p = 0.1:

| gamma | K_LB (step 10) |
|---|---|
| 1 | 331 (matches 330) |
| 0.5 | 191 |
| 0.1 | **1**, vacuous: certifying only when n_1 >= 1 gives max_f 0.1(1-2f/3)f < 0.05 |

**Fixes:**
- State LB for rules that certify tau on **every** all-pass record (equivalently with probability 1). This is the regime C1 is in at err = 0, since `Certifier.lower(0, K)` is deterministic, so the K_C1 comparison is fair at gamma = 1.
- Optionally give the gamma-curve, or the gamma = 1/2 ("median") version.
- Also say when a certificate "after K kept pairs" is issued. If it may be issued any time before the (K+1)-th kept pair, the record includes NegBin(K+1) tests and the exponent becomes K+1. This is a small effect, but it should be stated.

### M7. Baselines a referee will ask for are missing.
`study28.py:32`.

kgM is compared only with kg, which carries the full undeclared offset. Baselines to add:
- **Study 26's recipe arms on o0.044:** tomography margins m16/m64 and the oracle margin orc. Does an e-process on free test data beat a dedicated tomography budget, and how close does it get to orc?
- **A naive detector:** per-epoch binomial test, Bonferroni over 90 epochs. This shows what anytime validity buys.
- **Optionally, an e-detector:** SR/CUSUM-type, calibrated for average run length. My quick per-component CUSUM reset with the Ville threshold had a 36% pre-change false-alarm rate, so it must be calibrated before use; do not swap it in blindly.

**Fix:** add at least kg_m16 and kg_orc on o0.044, from the same networks.

---

## MINOR

- **m1. Pre-change deficit (Ville vs change detection).** `mcheck.py:30`. Before epoch 45 the log-wealth drifts to about -2.2 to -2.9 nats (ion2020, ionproj), so a post-fault alarm needs about 6.3 nats instead of 3.5. This is about 1.8x the delay that `delay_bound` assumes, and the bound assumes the alternative holds from test 1. State this in Proposition MC, or reset the wealth at known change points. The effect is moderate here because the guard's slack before the fault is only 0.003-0.005 in fidelity.
- **m2. delay_bound assumptions.** `mcheck.py:44-51`. The bound assumes a fixed q and P(E) >= q+delta on **every** tested pair. In the network both vary and violations are sparse. Restate it in terms of per-pair q_i and the minimum (or average) growth rate, or label it as a constant-q benchmark only. The Wald/optional-stopping argument itself is fine: positive drift, increments bounded above by ln(1+lam(1-q)), and a truncation argument for E[tau] < inf.
- **m3. Safety metrics count only measured pairs.** `study28.py:97, 120`. `any_bad` and `users_bad` count only pairs with `meas` set (after warm-up), while the kgN and per-user guarantees cover the whole run. Few pairs are delivered in warm-up, but count all delivered pairs for the safety bars, or say that the bars cover post-warm-up pairs only.
- **m4. Harm and throughput include tested pairs.** `study28.py:97-98`. Tested pairs are destroyed by measurement, so `bad` and `qual` count pairs the user never gets. Paired kg/kgM ratios at the same p are fair, but absolute harm and fq are overstated by a factor of about 1/(1-p). Add `bad_kept` and `qual_kept`.
- **m5. Memory.** `s26/study26.py:193`. The `st` cache holds a 3.84 MB `cdf` per epoch, about 350-390 MB per network at 90 epochs (about 3x Study 27). Check the cluster's per-worker memory. Service is serial and epochs only increase, so keeping only the last two cache entries would be safe.
- **m6. Wasted compute on kg and kgN.** `study28.py:37`. kg and kgN deliver the same stream at p10 and p20, because the network never reads `trng`. Only the certificate differs, so 25% of tasks repeat deliveries. This is acceptable for pairing; alternatively, compute both p certificates in one run, as Study 27 did.
- **m7. The `fault` label is reused.** `study28.py:30`. FAULT_EP = 45 differs from Study 27's 15. Record it in the output row, because the pilot summary pools by label.
- **m8. Global side effect of the NEPOCH override.** `study28.py:22`. Setting NEPOCH = 90 at import changes the module globally. A worker process that imports study28 and then runs a study26 or study27 task would silently get 90 epochs. Assert `g1.NEPOCH == 90` in `Net28.__init__`, and keep runners per study.
- **m9. LB vs C1 comparison wording.** lb_out.json. K_C1/K_LB ≈ 1.9-2.3 compares an anytime certificate, valid against adaptive sources, with a fixed-K converse against iid sources. Say that the factor of about 2 includes the anytime price and any slack in the LB. To split the two, compute the best fixed-K certifier for this iid family as an achievability point.
- **m10. Synthetic false-alarm MC covers only k = 1.** `mcheck.py:54-67`. The MC never exercises restarts. Add a run with forced restarts that checks the total per-segment false-alarm rate against 0.05 (pairs with M3a).

---

## Hypotheses a referee will want pre-registered

1. **H-FA:** in '-' (and fault before epoch 45), per-network P(first alarm before first violation) <= 0.0304, and per-segment false alarms <= 0.05 per run. Use a one-sided binomial test over the stated number of runs.
2. **H-DET (powered cells only):** detection probability and median epoch of first alarm under o0.044 on ion2020 and ionproj, predicted from the pilot via `delay_bound` or a replay.
3. **H-HARM:** paired ratio of bad kept pairs, kgM/kg, in the powered cells. Same comparison against kg_m16 and kg_orc (M7).
4. **H-COST:** throughput loss fq(kg) - fq(kgM) in '-', and the distribution of `dec_final`. Pre-register a bound, e.g. <= 1 point.
5. **H-NET:** kgN P(any_bad) <= 0.05 in '-', and its throughput cost against kg.
6. **H-SPAM (if M4 is adopted):** no alarm inflation under declared readout error r <= rmax.
7. **Explicit nulls:** siv, nv2 and fault for kgM, declared as not testable or predicted null from the power analysis (M1).

---

## How the scratch experiments were run

- **Shadow-mode instrumentation.** Subclass `Net28` and wrap `mc.update` and `true_state` to log (t, q, Ft, E, log-wealth) per tested pair. Arm kg runs the check without feedback. Networks: DEV seeds, idx 0-1, on siv and nv2 ('-', fault, o0.044) and ion2020/ionproj (fault). The ion2020 and ionproj fault runs are identical to '-' before epoch 45.
- **Power replay.** `mcheck`'s vectorised betting, 2,000 replications: 525 tests at excess -0.0023, then 1,100 tests at excess +0.006 or +0.02.
- **Margin jump.** `ModelCheck` fed consecutive errors at q in {0.005, 0.02, 0.04} with k in {1, 2}. An alarm fires after 3 errors and the increment is 1.44-1.49.
- **LB checks.** A full f-grid; a scan of K_LB+200 for non-monotonicity; and the gamma-evasion bound computed from the NegBin(K, 1-p) top-gamma tail.
