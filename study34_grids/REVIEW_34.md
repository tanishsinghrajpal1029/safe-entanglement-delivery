# Study 34 pre-pilot hostile review (2026-10-11)

Scope: study34.py and the chain it imports (study32, study30, study26/25/24, corr_net/corr_net24, drift_queue_des_g1), pilot_summary_34.py, runner/sbatch. No files were edited.

## Verified OK (measured, not just read)
- **Grid propagation works.** With S34_GRID=30 the modules load from s18c/g1, s26/corr_net, s26/corr_net24, s26/study24/25/26 and s30/study30. g1.GRID_N=30, cn.NL = cn24.NL = 1740, 900 nodes, net.nl = 1740 (the assert at study34.py:23 holds). `corr_net.grid_links(n=g1.GRID_N)` (corr_net.py:16) binds its default at import, which comes after study34.py:20, so the order is right. g1.Net reads GRID_N when it builds the topology (g1:74). The Net25 noise matrix A (study25.py:90) and Net26's `assert s.nl == cn.NL` (study26.py:114) are both sized from cn. Nothing in the 5x5 chain is hard-coded to 40, 25 or 5. The only "5 x 5" text is in docstrings. The 900-node Cholesky (ELL = 1.5, 1e-8 jitter) does not fail. Import takes 2.7 s and Net init about 3 s on 30x30.
- **Umax and the Theorem 1 level do not change with grid size.** Umax is 4 for ion2020 and 7 for ionproj on 5, 10 and 30, so lvl = 0.05/7 on every grid. Every user shape up to distance 3 already fits on the 5x5 grid.
- **m3 is applied consistently.** `rate25 *= 3` (study34.py:44) is set after init. Nothing in the init chain reads rate25, and Net30.run uses it only for arrivals (study30.py:177-179). The oracle serves each request inline, so it scales with the requests. The 'm3' tag passes through Net32's `var` without matching the 'r'/'t' branches. base and m3 use the same nseed, so the network is paired. Serial service keeps up at 9/s: 15,265 measured requests in 17 epochs, which is the expected 9/s.
- **Validity of the per-link levels.** Theorem 1 (per user, α/Umax per link) and B1 (upper ends at ALPHA_HI/nl, a union over every link, study30.py:124) both remain valid at nl = 1740.
- **Memory and time on 30x30 (ionproj, kgMCa, o0.044F, p10, m3).**
  - 6 epochs took 68 s and 20 epochs took 225 s, which is linear at about 11 s per epoch. A full 90-epoch m3 task should take about 17 min.
  - Peak RSS was 1.37 GB, the same at 6 and 20 epochs (the st/hi caches are trimmed to 4 epochs, study30.py:113-127). 16 workers need about 22 GB and 32 workers about 44 GB, which fits RM-shared at 2 GB/core.
  - Rough budget for the g30 file, extrapolated: 704 m3 tasks × ~17 min plus 704 base tasks × ~6 min (the base figure is an estimate, not measured) ≈ 270 core-h. kg arms have no probes and should cost less.

## BLOCKER
**B1. The per-user endpoint over all users is diluted about 60× on 30x30, so it passes regardless.** The total request rate is the same on every grid (study34.py:7-8), but the user count is len(cands) (study30.py:270):

| grid | ion2020 users | ionproj users | requests/user (87 measured epochs, ion2020 / ionproj) |
|---|---|---|---|
| 5 | 204 | 340 | 128 / 77 |
| 10 | 1,004 | 1,860 | 26 / 14 |
| 30 | 10,204 | 19,940 | 2.6 / 1.3 |

"P(a user ever receives a bad pair)" therefore measures per-request risk on 30x30, and roughly a quarter of users are never requested at all. `pu_all = users_bad_all / users_total` (pilot_summary_34.py:13) will sit far below α for every arm, probably including **kg under o0.044 (no check)**. The validity comparison then passes for every arm on 30x30, kg included, and the contrast against kg vanishes.

Fixes, to make before the prereg:
- (a) Make the primary safety endpoints exposure-invariant:
  - the per-delivery bad rate after the alarm (r_after = bad_after_alarm_all / deliv_after_alarm_all, already computed);
  - per-served-user risk (users_bad / users_served, or users_bad_post / users_post);
  - the bad-user rate stratified by requests per user.
- (b) Add a matched-exposure cell on 30x30 (preferred), as config `u`:
  - In Net34.__init__, after super(), replace s.cands with a random subset of the 5x5 user count (204 or 340), drawn with an nseed-derived rng and spread over the whole grid.
  - Keep the base rate, so requests per user match 5x5 while the links, routing and B1 union stay 30x30.
  - Umax and lvl are already computed from the full set, which is fine. users_total becomes the subset size automatically.
- (c) Pre-register that kg + o0.044 must show a nonzero per-served-user failure on every grid (a sensitivity check). If kg does not fail on a grid, that grid is non-diagnostic.

## MAJOR
**M1. The design mostly re-tests mechanisms that do not depend on grid size, so "carries over" holds almost by construction.**
- Calibration counts are per link (Poisson(ρRT), the same on every grid), so each link's guard confidence sequence is identical.
- The offset is the same constant on every pair.
- The check's test count per unit time is set by the total rate, which is the same on every grid.
- The hop mix barely moves. The 3-hop share for ionproj goes 0.40 (5x5) → 0.46 (10x10) → 0.49 (30x30).

The only explicit dependence on nl is hi_at's ALPHA_HI/nl (see m1 below), and it is tiny. Expect alarm epochs, margins and r_after to be statistically indistinguishable across grids. A null result here says little about scaling.

Fix: state this up front as an implementation/scaling sanity check, with per-mechanism predictions that the results do not change except for the hop-mix effect and a margin about 0.001 higher. Then add at least one condition that actually stresses size:
- the matched-exposure `u` cell from B1(b);
- and/or demand that scales with users. This needs parallel service, which Net30 does not have (it is serial only, study30.py:184), so it is out of scope unless ported.

Also consider recording the minimum link quality and the share of blocked users, since tail links grow with nl and with ELL = 1.5 fixed in grid units.

**M2. m3 runs only on g30 (study34.py:31), so the rate effect and the grid effect are confounded.**
The docstring's stated reason ("three times as many tests") applies to any grid, because tests per unit time do not depend on topology. As designed, any g30-m3 vs g5-base difference cannot be attributed to grid size.

Fix: add m3 on g5. It is cheap: 22 configs × 32 networks, each fast on 5x5. Then analyse m3 vs base within each grid, and compare grids only within base.

## MINOR
- **m1. Upper ends at ALPHA_HI/nl add a small cost** (study30.py:124). The mean slack of the model fidelity at the upper link bounds over the true value (Fhi − F_true), at nl = 40 → 180 → 1740:

  | hardware | epoch 5 | epoch 30 | epoch 89 |
  |---|---|---|---|
  | ion2020 | .0093 → .0100 → .0104 | .0047 → .0049 → .0051 | .0028 → .0030 → .0031 |
  | ionproj | .0091 → .0096 → .0107 | .0045 → .0047 → .0052 | .0028 → .0029 → .0032 |

  The test statistics a_i are therefore biased up by about 0.0003 to 0.0016 more on 30x30. U, and so the margin and blocks, end slightly higher. The bound also covers θ slightly more easily. That is valid, but it makes "coverage carries over" a little easier. Pre-register it as a predicted margin about 0.001 higher, not as a finding.
- **m2. The sbatch does not require S34_GRID.** s18c_array.sbatch is missing `: "${S34_GRID:?}"`. Without it, GRID defaults to 5, the run_one assert (study34.py:60) fails on every g10/g30 task, and the shard crashes. That failure is loud, but add the guard and write S34_GRID into the shard meta.
- **m3. Shard meta hashes only study34.py** (psc_array_runner.py: module_sha). The behaviour also depends on study32, study30, core30, study26/25/24, corr_net/24, g1 and hw24. Hash every loaded module from sys.modules whose __file__ sits under the code dirs.
- **m4. Import paths can differ between machines.** study32/30 are found through relative `HERE/../s30` paths (here study30 loaded from `/home/claude/s34/../s30/study30.py`), while s24/s25/s26 copies exist in several directories and resolution depends on sys.path order. Today s26 is ahead of s25 and correct. On PSC, set S26_DIR, S30_DIR and S32_DIR explicitly and log `mod.__file__` for g1, corr_net, study24/25/26/30/32 in meta.
- **m5. The OffsetCS look is O(n) per epoch over the whole window** (core30.py:63-78). kgMCa's window never restarts without an alarm, so m3 on 30x30 reaches about 2×10^5 tests by epoch 90. The timing measured so far is linear and fine, but confirm the 90-epoch wall time in the pilot before setting the time limit. Use the 2 h limit with resumable shards. The ~17 min estimate is extrapolated.
- **m6. The 6-epoch smoke result is expected, not a bug.** kgMCa at m3 delivered 79 of 2,681 requests in 6 epochs and 1,358 of 15,265 in 20. Because the margin starts at THMAX, kgMCa throughput on 30x30 m3 will be dominated by the margin's descent, which is the same on every grid. Do not read it as a topology effect.
