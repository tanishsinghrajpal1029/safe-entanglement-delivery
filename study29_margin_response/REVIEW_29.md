# Study 29: adversarial pre-pilot review of `study29.py` (11 Oct 2026)

**Scope.** `study29.py` (sha256 `fb5c6c71a3d21fcf`) compared against `../s28/study28.py`. I also checked `mcheck.py` (unchanged, `a05f0822`) and the task files. No code was edited.

**Experiments.** Every experiment used dev seeds only, or Study 28's confirmatory seeds for a replay of its failure. I touched none of Study 29's confirmatory seeds. The scripts and pickled logs are in the session scratchpad (`.../scratchpad/exp/`):
- `study29_log.py` is an instrumented copy that logs every delivered pair.
- `sim2.py` is a pair-level replay of the response rules.
- `replay.py` replays Study 28's network 19.

**Verdict.**
- The **code is correct** in the sense you asked about:
  - kgM is bit-identical to Study 28.
  - The e-process still uses the conservative q.
  - The margin updates are predictable.
- There is **one design blocker.** kgMT locks in at DMAX for the whole run on exactly the case Study 29 was built for: Study 28's 8-test alarm.
- There are **seven major issues**, mostly about what the tracking margin estimates and how it is bounded.

Fix B1 and M1, and add the instrumentation (M6) and the forced-alarm configurations (M5), before the pilot.

---

## What I verified (no action needed)

| Check | Result |
|---|---|
| kgM in Study 29 is the same as kgM in Study 28 | I ran Net28 and Net29 on the same seeds, with Study 29's `trng` reseeded to Study 28's tag 281 (dev network 0, ion2020, o0.044, p = 0.2). All **40 shared output columns are identical**, so nothing was dropped or changed unintentionally in the shared path. Removing kgP, kgN and the naive detector only removed code. |
| Pairing across arms | kgM, kgMJ and kgMT follow the **same trajectory until the first alarm**: dev network 0, ion2020, o0.044, p = 0.1 alarms at epoch 22.68 after 644 tests in all three. kgMJ is the same as kgM whenever n ≥ NMIN (all of its outputs were identical in that run). |
| e-process q | `study29.py:159` `q = null_bound(Fg, s.smax)`, with Fg including the current margin. It is the conservative q, and `mcheck.py` is unchanged. Prop. MC validity only needs q to be predictable, and it is, even when the margin falls. |
| d_i predictability | The margin changes only at `alarm()` (`:102-116`) or at the epoch-boundary update (`:135-138`). Both read completed tests only. The update runs before `Fg` (`:145`) for the same attempt, so that pair uses the new margin. That is predictable. |
| a_i does not depend on d_i | `Fc` includes `-d_now`, and `a_i` adds `+d_now` back, so a_i = R_a·(E − null_bound(F(est)+off)) **exactly**. The margin enters a_i only through which pairs get delivered. |
| `trk['a']` appends | Only while tracking is on (`:172`). It is appended before `mc.update`, and on an alarm `trk['a'] = list(seg['a'])` already contains the current test, so nothing is counted twice. `seg['a']` also fills for kgM and kgMJ but is unused there. That is harmless. |
| Lemma F in the simulator | max \|mean(eB) − (2/3)(1 − F_true)\| = 2e-16 over every logged pair. |
| Bias from routing on est (winner's curse), est shrinkage, DEJMPS non-linearity | Mean F(est) − F_true on delivered pairs ranged from −0.0005 to +0.0007 (sd 0.003) across 6 dev runs. Multi-path users ranged from −0.0012 to +0.0011. This is **negligible** on ions. |
| Correlation between tests | Design effect over epoch clusters was 0.74–1.13. The estimation-error variance (~1e-5) is about 1e-4 of the Bernoulli variance of a_i (sd about 0.30), so correlation is not an issue. a_i is bounded, so there are no heavy tails. **Skew** is the issue (M2). |
| Task files | `tasks_s29.jsonl` (2,432 tasks, `01529e959e9a2e05`) and `tasks_p29.jsonl` (608 tasks, `b7cdae18cc911eb6`) equal `tasks()` and `tasks('P29', 8)`. Output columns are identical for every arm, which the runner's append-under-first-header needs. |

---

## BLOCKER

### B1. kgMT keeps the alarm segment in its window, which pins the margin at DMAX for the whole run after an early alarm (`study29.py:106`, `:97-99`)

**Mechanism.**
- At the first alarm, `trk['a'] = list(seg['a'])`, so the window starts with the segment that ended in the alarm.
- That segment is selected by a stopping time: it ends exactly when the e-process got lucky, so it is biased upward.
- In the dev runs the alarm segment's mean a_i exceeded the pair-level prediction by 0.0035 (ion2020, 0.044, p = 0.1), 0.009 (ionproj, 0.02) and 0.012 (ionproj, 0.044, p = 0.2).
- With 8 tests the bias is huge.

**Replay of Study 28's failing network** (ion2020, p = 0.1, network 19, Study 28 seeding; exact, because Net29's kgM equals Net28's):

| Arm | First alarm | Bad after alarm | Delivered / good pairs (oracle about 18,400) | Final margin |
|---|---|---|---|---|
| kgM (Study 28) | 8 tests, epoch 0.12 | 6,232 / 24,134 | 24,134 / 17,902 | 0.02 |
| **kgMJ** | same | **0** | 1,462 / 1,462 | 0.10 |
| **kgMT** | same | **0** | **1,471 / 1,471** | **0.10 for all 90 epochs** |

**Why kgMT is stuck at 0.10.**
- The 8-test segment (3 errors) has mean a = 0.52.
- The window's mean is 0.061 with it and 0.033 without it, so the upper bound is 0.101 (clipped to DMAX) instead of 0.065.
- A margin of 0.10 delivers only about 8% of oracle, so the network gets about 1.5 tests per epoch, and the poisoned window never gets diluted. Only 144 tests arrived in 90 epochs.

**Consequences.**
- Both new arms fix the safety failure.
- But kgMT is then **no better than kgMJ on the case it was designed for**, and its throughput hypothesis is decided by the window rule, not by tracking.

**Fix (pick one and pre-register it).**
- (a) Start the window **after** the alarm, using post-alarm tests only, with DMAX until NMIN post-alarm tests. In the replay that gives 0.080 at epoch 36 and 0.065 at the end.
- (b) Drop the alarm segment only when it has fewer than NMIN tests, and keep it otherwise. Then disclose its upward bias of about 0.003–0.012, which is conservative.

**Either way, the margin starves itself.**
- At DMAX the network delivers about 10× fewer pairs. Reaching 50 post-alarm tests took 36 epochs in the replay. On dev network 0 (ion2020, p = 0.2), kgM at 0.10 delivered 1,513 pairs in the whole run.
- This is inherent, because the margin learns only from pairs it lets through. State it.
- Optional design change: test some guard-blocked pairs on the network side during the interim.

---

## MAJOR

### M1. The central prediction assumes readout error is at its declared bound, which biases a_i low by about 0.0026 on ions (`:161`, `:170`)

**Exact conditional mean.** With true readout s:

E[a_i | G_i] = off + (F(est_i) − F_true,i) − 1.5·(s_max − s)·(1 − (4/3)(1 − F_true,i)) / (1 − 2 s_max).

**What this means in the study.**
- In every scenario except `ro`, s = 0. The bias is then −0.0026 to −0.0028 on ions.
- Measured on dev network 0: the pair-level prediction of E[a] was 0.0416 against off = 0.044. In the `ro` run the measured mean of a was −0.0004 against off = 0.
- That is about the **same size as the guard's lower-bound slack**. Measured on delivered pairs, F_true − F(λ_lo) has median 0.0024 and 5th percentile 0.0010.
- So the tracked margin converges to a value below the one that makes the guard valid.
- On NV the same rule would be biased by −0.08 (s_max = 0.058). Do not carry it beyond ions in this form.

**Fix.** Use q_c with s = 0, i.e. q_c,0 = (2/3)(1 − F_c), and a_i = 1.5(E_i − q_c,0) + d_i.
- Then E[a_i | G_i] = off + b_i + 1.5·s·(1 − (4/3)(1 − F)), which is ≥ off + b_i for every s ≤ ½.
- Readout error is charged to the offset. That costs at most about 0.003 on ions and is conservative.
- Correct the docstring claim "E[a_i] ~ offset" (`:85`).

### M2. The "95% normal bound" under-covers, and it is re-applied at every epoch (`:97-99`)

**Fixed-n coverage.** I resampled tests from dev network 0's delivered pairs, with 20,000 replicates per n.

| n | Normal bound misses E[a] | Normal bound misses off | Clopper–Pearson (CP) misses E[a] | CP misses off |
|---|---|---|---|---|
| 50 | 8.9% | 10.1% | 0.0% | 0.0% |
| 100 | 13.8% | 13.8% | 3.9% | 4.5% |
| 200 | 8.0% | 10.4% | 3.4% | 3.5% |
| 500 | 7.6% | 9.8% | 4.1% | 5.6% |
| 1,000 | 6.7% | 10.1% | 4.1% | 6.7% |

- The cause is skew: the error rate is about 4.8%, so E_i ∈ {0,1} is rare-event data.
- The "misses off" column also includes M1's bias.

**Repeated looks.**
- kgMT recomputes the bound at every epoch: 68 updates on dev network 0, and 30–160 in the replays.
- Nothing makes the bound hold uniformly over time.

**Pair-level replay** (`sim2.py`; pairs resampled from dev network 0 and re-filtered by the current margin; e-process with restarts; true readout 0):

| Rule | Horizon | Bad after alarm (pooled) | Runs with any bad pair | Post-alarm deliveries with d < off | Final d (5th pct / median) |
|---|---|---|---|---|---|
| kgM (Study 28) | 90 epochs | **6.4%**; **3.0% of runs > 1%** (reproduces Study 28's H4 failure) | 3.0% | 16.3% | 0.058 / 0.100 |
| kgMJ | 90 epochs | 0 | 0 | 0 | 0.061 / 0.100 |
| kgMT, normal | 90 epochs | 0 | 0.8% | 0.6% | 0.047 / 0.059 |
| kgMT, CP | 90 epochs | 0 | 0 | 0 | 0.049 / 0.061 |
| kgMT, normal | 360 epochs | 0.024% | **12.5%** | **8.2%** | 0.042 / 0.049 |
| kgMT, CP | 360 epochs | 0.014% | 10% | 6.3% | 0.043 / 0.050 |

**Reading.**
- Within the 2.5 h horizon the drift is harmless.
- It does not converge to a safe margin: the drift is M1's bias plus the repeated looks.
- The study must not describe the rule as a "95% upper bound".

**Fix, in order of rigour.**
1. A **time-uniform upper confidence sequence** on the running mean of a_i. A betting or hedged-capital CS for bounded martingale differences (Waudby-Smith & Ramdas) is valid under the adaptive selection, because E[a_i | G_i] is defined pair by pair. Expect about 1.5–2× the width.
2. At least use CP on ΣE (`R_a·(CP_ub(ΣE, n) − mean q_c)`) together with M1's fix.

**Pre-register a margin-coverage metric either way** (see M6).

**A tempting route that does not work.** Inverting the model-check e-process over a grid of margins gives a *lower* confidence bound on the needed margin, because it rejects margins that are too small. It cannot set a safe margin: in the replay it under-declared in 99% of runs. An upper bound needs a test in the opposite direction.

### M3. The "e-process keeps running" backstop is blind after a period of over-declaration (`:86`, mcheck restarts)

**What happens after tracking starts.**
- The margin sits above the needed one, and q is conservative (lower-bound slack plus s_max), so the restarted e-process drifts strongly downward.
- In the dev runs, mean(E − q) after the alarm was −0.009 to −0.018.
- The final mixture log-wealth was −5.9, −10.5 and −14.2. The k = 2 threshold is +4.88.

**Consequences.**
- A later under-declaration would need 11–19 nats of evidence before any re-alarm. In practice the backstop does not exist within the horizon.
- The shrinking restart levels, ln(π²k²/(6β)), add only about 1.4 nats per doubling of k. The deficit is the problem.
- In the replay (`sim2.py`), 0 second alarms occurred even in the 12.5% of runs that delivered bad pairs.

**Fix.** Either:
- (a) use a CUSUM-type e-detector, S_t = max(0, S_{t−1} + log factor_t) on the same bets, and pre-register its average run length to a false alarm. This changes the guarantee from P(any false alarm) ≤ β to an average-run-length (ARL) bound. Or
- (b) restart the e-process whenever the margin falls by more than a fixed step, and spend level for each restart.

Remove the backstop claim from the docstring otherwise.

### M4. Theory: a margin that falls breaks the restart corollary's premise (`mcheck.py:10-11`; `THEORY_28.md` §2 Corollary)

- The corollary states that "after the k-th alarm the declared margin d only increases … so Theorem 1 still applies." kgMT's margin falls (by design).
- Prop. MC itself remains valid, because q is predictable.
- But **Theorem 1's delivery guarantee does not cover kgMT after a decrease.** Its post-alarm safety is heuristic only, unless M2 option 1 is adopted. Even then the guarantee is only for the *mean* offset (see M7).
- Say this in the paper and in THEORY_29. Do not inherit Theorem 1's wording.

### M5. The motivating case is too rare to test, and these configurations are mostly duplicates (`:32-43`)

**Rarity.**
- In Study 28's confirmatory data, 3 of 259 alarmed feedback runs alarmed after fewer than 50 tests. Only **1 of 256** was in a powered ion cell, and that was network 19.
- Here kgMJ equals kgM unless n < NMIN (verified). kgMT's early path is likewise exercised only then.
- The 384 kgMJ runs in offset cells will probably contain 0–3 such networks.
- My o0.08 dev run alarmed after 242 tests, so a larger offset does not make early alarms common.

**Duplicates.** The 512 kgMJ and kgMT runs in `-` and `ro` repeat kgM exactly unless a false alarm occurs (about 0.3%).

**Fix.** Use that compute for:
- **(a) Forced-alarm configurations.** Inject an alarm at the 8th feedback test (`alarm(t)`, `mc.k += 1`, `mc.logm[:] = 0`), in o0.044 (and o0.08). This tests the early-alarm response directly.
- **(b) The same in `-`.** This tests **recovery from a false alarm**, where kgMT should fall back toward 0 and kgM or kgMJ should not.
- **(c) A `replay28` seed option** in `run_one`. `:212-214` hashes "s29net"/"s29run", and `:62` uses tag 291, so Study 28's network 19 cannot be reached through `run_one` today. My replay patched `trng` by hand. Make it a positive control in the pilot.

### M6. Outputs missing that the post-alarm hypotheses need (`:182-190`)

Add the following:
- `viol_after_alarm`: deliveries after the alarm with F_true < Fg.
- `under_after_alarm`: deliveries after the alarm with s.dec < s.off. The analysis cannot reconstruct this from run totals.
- `dec_min_after`.
- `n_dec_decreases`.
- `seg_n_min`: whether *any* alarm fired with n < NMIN, which is kgMJ's trigger. Study 28 had this column; `seg_n_first` replaces it.
- `tests_after_alarm`.
- `deliv_at_dmax`.
- `qual_after_alarm`.

Also define `dec_mean_after` in the analysis. It is weighted by deliveries, so low-margin periods count more.

### M7. Missing baselines and scenarios that a referee will ask for (`:32-33`)

1. **Always track (kgT):** track from epoch 0 with no alarm gate. This shows what the gate buys. It gives no cost under the null (H5), but per-user harm before the alarm stays at about 46–49% (Study 28).
2. **The 16-point tomography baseline (`o*_m16`).** Study 28's S1 comparator was dropped. Without it, a throughput claim has no non-oracle reference.
3. **Plug-in ablation:** margin = mean(a) with no upper bound. This shows why the bound is needed.
4. **Model error that depends on the pair.** The additive constant offset is the *easiest* case for mean tracking. With T2 or gate optimism (Study 25's κ), the offset grows with hold time, so pairs admitted near τ (long holds) have a larger offset than the mean. A mean-based margin then under-protects exactly the marginal pairs.
5. **An offset that changes during the run:** it appears at epoch 45, or disappears after a recalibration. The window logic exists for this but is never exercised.

---

## MINOR

- **m1 (`:106`).** At a later alarm, kgMT resets the window to the latest segment, and the new bound can be *lower* than the current margin when the margin rose during that segment. An alarm is evidence that the margin is too small, so use `s.dec = max(s.dec, new)` at alarms.
- **m2.** Dead code: `eb_ub` (`:47-50`, and its form differs from the inline EB at `:110`), the `binom` import (`:23`), and the `s.fault` and `T2true` fault branch (no fault scenario).
- **m3 (`:160-161`).** `Fc` (an extra `delivered_F` call) is computed for every delivered pair in every arm, including kg. Gate it on `s.arm28 == "kgMT"`.
- **m4.** The additive offset pushes F(est) + off above 1.003 for 1.6% of delivered pairs, so q_c < 0 for 0.6% of tests. a_i stays unbiased because null_bound is linear, but the model is unphysical there. Note it.
- **m5.** `inc_max` can be negative for kgMT, which changes its meaning.
- **m6.** `oracle_qual` depends on the arm through service-time coupling: 13,338 for kgM against 13,256 for kgMT on the same network. Compare arms by **paired `qual` difference**, which is purely post-alarm thanks to the identical pre-alarm paths, not by the fq ratio.
- **m7.** Docstrings `:9-10` and `:81-87`: give the exact E[a | G] formula (M1) and drop "95%" (M2) and the backstop claim (M3).

---

## What to pre-register (bars set after the pilot, disclosed)

**Integrity checks** (not hypotheses):
- Pre-alarm trajectories are identical across kgM, kgMJ and kgMT for each network and cell (`first_alarm_ep`, `seg_n_first`).
- kgMJ equals kgM in every run with `seg_n_min` ≥ NMIN.
- No new alarms in `-` and `ro` beyond Study 28's H1 rate.

| | What | Suggested bar |
|---|---|---|
| P1 (primary) | Safety of the fix. Risk of a bad delivered pair after the first alarm, for kgMT and kgMJ separately, in powered cells (ion × {0.044, 0.08} × p) **plus the forced-alarm cells** | Pooled bootstrap upper bound ≤ 1% **and** per-network: CP upper bound on the share of networks with post-alarm risk > 1% ≤ 5%. Study 28 failed because one network dominated a pooled ratio. |
| P2 (primary) | Throughput. Paired post-alarm `qual`, kgMT vs kgM (and vs kgMJ), in each powered and forced-alarm cell; gap to `orc` | Ratio lower bound ≥ pilot-set value; gap to orc ≤ X points |
| P3 (primary) | Margin calibration. Share of post-alarm deliveries with d < off, and final d − off | Share upper bound ≤ 5%; median final d − off ∈ [0, 0.02] |
| P4 (secondary) | Recovery from a false alarm (forced alarm in `-`) | kgMT final d ≤ 0.02 and throughput within 2 points of kg; kgM and kgMJ do not recover |
| S (prediction) | o0.02 detection on ion2020 | Prediction from `delay_bound`. Dev network 2 did not alarm within 1,446 tests, so this cell may be unpowered. Say so in advance. |
| D | Margin paths, number of decreases, under-declared share, post-alarm e-process log-wealth (M3), kgT, m16, plug-in | Descriptive |

**Questions a referee will ask.**
- Why use a fixed-n normal bound when a time-uniform CS for bounded means exists?
- What does the alarm gate buy over always tracking?
- Does tracking the mean offset survive model error that depends on the pair?
- What happens when the offset changes?
- Is the 1-in-256 early-alarm event actually tested, or only the common path?
- What is the guarantee after the margin falls? Theorem 1 no longer applies.
- How sensitive is the method to true readout below the declared bound (M1)?
- Present results per network, not as pooled ratios.

**Compute.** About 3–6 min per ion task, so the 2,432 tasks need about 150–200 CPU-h. The forced-alarm and replay cells fit if the duplicate `-`/`ro` kgMJ and kgMT cells are dropped (M5).
