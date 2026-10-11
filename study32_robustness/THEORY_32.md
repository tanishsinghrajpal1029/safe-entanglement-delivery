# Study 32 theory note: a bound that can recover (11 Oct 2026)

**Setting.** Theorem 2 (THEORY_30.md) defines
  U_t = min_{s ≤ t} sup{ m ∈ [0, θ_max] : K_s(m) < 1/α′_k }.
This is the intersection of the confidence sets over all looks so far.

**Remark R (no intersection needed).** Define instead
  U′_t = sup{ m ∈ [0, θ_max] : K_t(m) < 1/α′_k }, using only the current look.

**Claim** (standard for confidence sequences; intersecting is optional, cf. Howard et al. 2021). On the same event as Theorem 2's,
  P( ∃t : θ > U′_t ) ≤ α′_k,
so Theorem 2 holds with U′ in place of U.

**Proof.**
1. Each bet ν_ij ≥ 0 is fixed in advance, and φ_i ≥ 0. So K_t(m) is nondecreasing in m.
2. Hence θ > U′_t implies K_t(θ) ≥ 1/α′_k.
3. The event {∃t : K_t(θ) ≥ 1/α′_k} is exactly the one Ville's inequality bounds in Theorem 2 (Step 3).
4. Steps 1, 2 and 4 of Theorem 2's proof are unchanged. ∎

**Why it matters.**
- With the running minimum, a single unlucky stretch of tests can drive U below θ (the failure Theorem 2 allows with probability ≤ α′). Once there, U can never rise again, so every later pair is exposed. This happened in Study 30's network 11: 2,075 bad pairs.
- With U′, the wealth K_t(θ) falls back once later tests contradict the stretch. U′ then returns above θ, so the exposure lasts only as long as the episode.
- The cost: U′ ≥ U always, so the margin is slightly wider.
- U′ fluctuates, but the check restarts only on new lows: a restart happens when U′ falls DSTEP below the level at the last restart, and that level is lowered only at restarts. So there are at most θ_max/DSTEP restarts per window.
- After U′ recovers, the check is not refreshed. It may alarm again later and throw away a recovered window. Study 32 counts these re-alarms.

**Toy check (not evidence).** In a stream with true offset 0.044, the first 150 tests were forced to be passes, with a look every 150 tests:
- the running minimum stayed at 0 for all 15,000 tests;
- U′ returned above θ after 150–1,350 tests;
- without forcing, U and U′ were within 0.007 of each other.

**A re-opening alternative.** Open a new window at any stopping time, for example when the window's lower confidence bound on the mean of a_i exceeds U. The new window spends 6α′/(π²k²), so it is also valid. But it restarts at θ_max and discards data. U′ needs no extra spending, so Study 32 tests U′.
