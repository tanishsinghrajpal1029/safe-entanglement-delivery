# Study 32 hostile pre-pilot review (11 Oct 2026, ~25 min)

Scope: study32.py, THEORY_32.md, README_32_PILOT.md, with study30.py / core30.py / THEORY_30.md underneath. No files were edited.

Runs made:
- **One full run:** nv2, kgMCh, o0.044, p = 0.2, dev network 0.
- **Three cheap full SiV runs**, about 5–10 s each.
- **Eight 15-epoch short checks**, run with g1.NEPOCH and NEPOCH30 patched in memory only.
- Scratch outputs are in the session scratchpad.

## BLOCKER

**B1. Block T is degenerate: the closed loop never engages on thin hardware.** (study32.py:71-75)
- **nv2, kgMCh, o0.044, p = 0.2, full 90 epochs:**
  - 196 delivered, 30 bad.
  - **0 alarms, cs_n = 0.**
  - The output is identical in structure to kg.
- **siv, kgMCh, o0.044, p = 0.2, full run:**
  - 35 delivered, 6 bad, 0 alarms, cs_n = 0.
  - The output is byte-identical to siv kg (p00) on the same network.
- **siv, kgMCa, o0.044, p = 0.2:**
  - 0 delivered against oracle_qual = 75.
  - Only 66 CS tests, and U stays at θ_max = 0.10.
- **Why:** thin hardware gives about 20–40 feedback tests in 90 epochs. The hybrid check needs hundreds of tests to detect a 0.044 offset. On top of that, τ = 0.8 leaves no headroom for a 0.10 margin (F0 is 0.82 for NV and 0.86 for SiV).
- **Effect on the hypotheses:**
  - kgMCh ≡ kg, so anything that compares them is decided by construction.
  - kgMCa "safe with zero throughput" passes trivially.
  - Block T cannot answer "the closed loop on thin hardware".
- **Fix (choose one, before the pilot):**
  - (a) Give thin hardware an affordable test budget: a higher request rate for T (for example ×10 via the existing `ratemult`, s.o["ratemult"]), or p up to 0.5, or a longer horizon. Then confirm with one full run per hardware that kgMCh alarms in o0.044.
  - (b) Use an offset scaled to the headroom, for example o0.02. Also scale θ_max per hardware: the post-alarm margin of 0.10 against τ = 0.8 with F0 = 0.82 is unreachable.
  - (c) Drop SiV. Pre-register nv2 explicitly as a "power floor" cell, where the expected outcome is no alarm and kgMCh = kg, so that no hypothesis can pass because the loop did nothing.
- **At minimum:** add a pre-registered non-degeneracy gate (e.g. cs_n ≥ 200 and alarm rate ≥ 50% in o0.044 for kgMCh). Any cell that fails the gate is report-only.

## MAJOR

**M1. Block E, τ = 0.92 × o0.044 on ion2020 is degenerate.** (study32.py:67-70)
- Short check (15 epochs, kg p00): oracle_qual = 0. kg delivered 1,402 pairs, and every one was bad.
- No truly good pair exists in this cell, so every post-alarm arm will "pass" safety by delivering nothing. fq = qual / max(oracle, 1) = 0 carries no information.
- The same cell on ionproj is fine: oracle 588, kg 1,425 bad of 2,012.
- '-' at τ = 0.92 on ion2020 is near the ceiling: delivered = oracle = 1,402 with only 7 guard blocks. Any post-alarm margin will zero it.
- **Fix:**
  - Drop ion2020 × τ 0.92 × o0.044, or use o0.02 there.
  - Alternatively, pre-register it as a "correct answer is deliver nothing" cell and exclude it from throughput and cost hypotheses.
  - Add the oracle_qual > 0 gate to analyze_32.

**M2. Block R records no direct measure of recovery or poison dose.** (study32.py:41-46, 97-100)
- The question is "does U′ recover, and how fast". The outputs (via study30.run) give only pair counts: bad_after_alarm, below_after_alarm, dec_mean_after.
- Those counts mix two things: U′ recovering, and the hybrid check re-alarming. Both arms recover through the check's re-alarm. The README smoke says kgMCh was bad "until the check alarmed again".
- The poison dose (the number of tests forced to E = 0) is not recorded. It varies with hw and p, because the first look comes after about 480 tests and depends on the probe rate.
- If the check alarms during the poison stretch, k becomes 2 and no miscoverage happens. That case would go unnoticed.
- **Fix:** add these to OffsetCS32 and the output:
  - `npois`: tests poisoned.
  - `cov_fail_looks`: looks with U < θ.
  - `first_look_below_ep` and `recover_ep`: the first look with U < θ, and the first look after it with U ≥ θ.
  - `realarm_ep`: the next alarm after the forced one.
- Pre-register:
  - recovery time and bad pairs **during the episode**;
  - a per-run indicator that the poisoning actually produced U < θ, conditioning on it.

**M3. The forced-miscoverage cell answers its own question by construction. Add a natural miscoverage cell.**
- **The comparison is decided in advance:** the running minimum cannot rise. "kgMChN recovers faster than kgMCh in o0.044FM" is guaranteed by construction, and the margin of the win scales with the poison dose (all E = 0 for at least 480 tests). That is a stress test, not the S30 network-11 mechanism (an unlucky stretch of about 1e-5 probability).
- **The informative R-block questions are:**
  - (i) the cost of U′ in the unpoisoned cells: margin, throughput, extra alarms or false alarms;
  - (ii) validity of U′ in '-', o and L, i.e. below_after_alarm = 0;
  - (iii) absolute recovery time (M2).
- **Natural case to add:** `L0.044F` (from S30: a forced false alarm before onset, so (B2) fails in window 1).
  - There U sits at the pre-onset slack. U′ can rise once the post-onset data dominate the window, with no poisoning at all.
  - S30 pre-registered kgMCh as an expected failure in this cell, so it is the realistic recovery test.
  - Cost: 8 configs (2 hw × 2 p × 2 arms).
- **Optional:** a milder poison, e.g. only the first NPOIS tests poisoned and the look forced at NPOIS. This makes the result less dose-driven.

**M4. Block E has no paired base controls for kg and kgMCa.**
- kgMCh base cells ('-' and o0.044, p10, both ion types) exist in Block R. Seeds depend only on (hw, idx), so those cells are paired with Block E. That pairing works.
- **The gap:** there are no kg-p00-base or kgMCa-p10-base cells in Study 32. Any E-block comparison of cost or bad pairs against the default τ and ρ for those arms would have to borrow S30 cells, which use different networks (s30net vs s32net seeds) and are unpaired.
- **Fix:** add 8 configs: {ion2020, ionproj} × {'-', o0.044} × {kg p00, kgMCa p10} with base τ and ρ.
- Alternatively, state that all E hypotheses are absolute bars, with no comparison to the default.

## MINOR

**m1. "Calibration fraction 0.1" is mislabelled.** (study32.py:12, 84-90; README table)
- hw24.RHO_CAL only scales the calibration **count rate**. In Net25.__init__, nbar = s.rho_cal·R·T.
- The service rate stays at (1 − g1.RHO)·R with g1.RHO = 0.3 (g1.chains).
- So r0.1 is "a third of the calibration data at the same throughput", not a calibration-fraction trade-off.
- Rename it, or also scale g1.RHO. As it stands, the cell is purely harder and nothing is gained.
- The mechanics are correct:
  - hw24 is the same module object as study24's (/home/claude/s26/hw24.py; checked via sys.modules).
  - It is read only in Net24.__init__ (s.rho_cal) and used in Net25.__init__, both inside the try block. It is restored in finally.
  - It is not read at run time for the kg belief (ai_model24 uses it only for AI training).

**m2. The τ override after init is safe; noted as verified.**
- s.tau is not read anywhere in g1.Net, Net24, Net25, Net26 or Net30 __init__ (candidate sets come from topology and Lmax only).
- At run time, the oracle, pbad / choose_t, the guard and the bad-pair count all read s.tau. They are consistent.
- null_bound(Fg, smax) and the certifiers do not depend on τ.
- **One residual:** θ_max = 0.10 was set relative to τ = 0.9. At τ = 0.85 the post-alarm margin blocks less; at τ = 0.92, more. Disclose this.

**m3. kgMChN → arm30 "kgMCh" swaps in the new CS with no stale state.** (study32.py:83, 93-95)
- Net30.__init__ uses s.cs only to restart it for kgMCa. reset_dec, mc and trk do not reference the object.
- kgMCa: the old CS is restarted, then replaced, then the new one is restarted, so k = 1. This is correct.
- Thin hardware is compatible with Net30's assumptions:
  - The guard is fleetmix for kg.
  - HBAR is used only by 's' / kgMCs, which are absent from S32.
  - s.nl == cn.NL holds (5×5 grid, Lmax = 2).
  - The g1.HW entries for nv2 and siv come from the hw24 import.

**m4. OffsetCS32 logic checks out.**
- The poison gives a = amax − 1.5 = Fhi − 1, which is exactly E = 0.
- The `looked` flag is set before the U computation, so the look that ends the poisoning already uses only poisoned data. This is intended.
- restart() resets looked, but poison is gated on k == 1, so the reset is irrelevant.
- The non-monotone branch is correct: m_hi when nothing is excluded, 0 when m = 0 is excluded, and the bisection returns `hi`, which is conservative.
- **Small item:** a real check alarm during the poison stretch silently cancels the forcing (see M2's `npois`).

**m5. Remark R is correct, but word it carefully.**
- K_t is nondecreasing in m, so θ > U′_t ⇒ K_t(θ) ≥ 1/α′_k. This is the same Ville event.
- Coverage holds for each window, so the cross-window spending is unchanged.
- **Wording:**
  - State it as P(G2 ∩ {∃t: θ > U′_t}) ≤ α′_k, since Ville applies to K̃, and K̃ = K only on G2.
  - Cite that intersecting a CS is optional (standard; e.g. Howard et al. 2021). Do not present it as a new result.
  - Note that between looks the delivery uses the U′ from the last look. This is valid because θ is constant under (B2).
- **Check-restart interaction (study30.py:202-204):**
  - reset_dec is updated only downward (it is the running minimum of restart levels), and it is reset to θ_max only at an alarm.
  - So restarts are at most θ_max/DSTEP = 10 per window, whatever U′ does. Oscillation cannot cause unbounded restarts.
- **Correct THEORY_32 line 23 ("U′ also fluctuates, which can trigger more restarts"):**
  - Restarts fire only on new lows of U′.
  - After U′ recovers upward, the check is **not** refreshed. It keeps betting against the looser q = null_bound(F0 − U′) with whatever wealth it built during the episode. Its validity is unaffected, because H0 was false during the episode.
  - The likely result: a re-alarm after recovery that throws the recovered window away (k = 2, U back to θ_max). The pilot should count these "late re-alarms" in kgMChN FM (M2's realarm_ep).

**m6. pilot_summary_32.py omits the direct coverage measures.**
- Missing: below_after_alarm, viol_after_alarm, and the M2 fields.
- fq is averaged over runs with oracle_qual clipped to ≥ 1, which hides M1.
- **Fix:** add these columns and report oracle_qual per cell.

**m7. Compute and reproducibility.**
- **Cores:** the pilot puts 352 tasks over 32 shards, i.e. 11 tasks per shard on 16 workers. Five cores per shard are billed and idle. Use --cpus-per-task=11 or 12, or 16 shards.
- **Cost:** thin tasks take seconds; ion tasks take about 3–4 min. The 50 SU estimate is plausible (roughly 32 × 16 × 0.1–0.15 h).
- **Hashes:** the runner's meta hashes only study32.py. Put sha256 of ../s30/{study30,core30,mcheck}.py and of hw24.py in the prereg hash file, since the PSC copy of s30 must be unchanged.

**m8. README "All-paths check: 38 distinct configs ran for 8 epochs".**
- 8 epochs is below where thin hardware or τ = 0.92 show their problems.
- Before the pilot, at least one full-length run per new axis would have caught B1 and M1. Recommend one full run per (thin hw, kgMCh, o0.044) and (ion2020, τ 0.92, kgMCh, o0.044) after the fixes.

## Short-check numbers (dev network 0; 15 epochs unless marked full)

| cell | delivered | bad | oracle_qual | alarms | cs_n |
|---|---|---|---|---|---|
| nv2 kgMCh o0.044 p20 (full 90) | 196 | 30 | 527 | 0 | 0 |
| siv kgMCh o0.044 p20 (full) | 35 | 6 | 71 | 0 | 0 |
| siv kg o0.044 p00 (full) | 35 | 6 | 71 | – | – |
| siv kgMCa o0.044 p20 (full) | 0 | 0 | 75 | 0 | 66 |
| siv kgMCh '-' p20 (full, net 1) | 78 | 0 | 167 | 0 | 0 |
| ion2020 kg o0.044 base | 1,571 | 886 | 707 | – | – |
| ion2020 kg o0.044 τ 0.92 | 1,402 | 1,402 | **0** | – | – |
| ion2020 kg '-' τ 0.92 | 1,402 | 0 | 1,402 | – | – |
| ionproj kg o0.044 τ 0.92 | 2,012 | 1,425 | 588 | – | – |
| ion2020 kg o0.044 τ 0.85 | 3,598 | 1,606 | 2,141 | – | – |
| ion2020 kg '-' ρ 0.1 | 1,472 | 0 | 1,839 | – | – |
| nv2 kg o0.044 p00 | 34 | 5 | 67 | – | – |
