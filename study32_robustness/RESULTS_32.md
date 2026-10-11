# Study 32 ("re-opening and robustness"): confirmatory results (11 Oct 2026)

## What was run
- **Pre-registration:** `README_32.md` (d38dab2848a06a67) and the locked `analyze_32.py` (e9bbc59b38cf8ac7).
  - Public commit `f647233`, made at 22:45:35 UTC. The first shard started at 22:47:40 UTC, 2 min 5 s later. Confirm the push time on GitHub.
- **Code and tasks:** `study32.py` 3d1462ed528bb311 and `tasks_s32.jsonl` f8dbba7c61d6fe44, both recorded in every shard's metadata. Seeds 19331–19334.
- **Compute:** 32 shards × 16 workers; the longest shard took 1,189 s, about 170 SU.
- **Output:** `runs.csv` sha256 16e67200579969ab, 3,328 rows. No epoch was clamped.
- **Analysis:** run on PSC (`s32_analysis.txt`) and re-run in the cloud (`reanalysis_32_cloud.txt`). The two are identical.

## Verdicts: 6/6 primary PASS, 5/5 secondary PASS

| | Tier | Result | Numbers |
|---|---|---|---|
| **R1** | primary | **PASS** | **The no-intersection bound stays valid in class.** 23 of 11,800 users (upper bound 0.58%) and 661 of 450,432 pairs (upper bound 0.42%) got a bad pair after the alarm |
| **R2** | primary | **PASS** | **No throughput cost.** −0.29 points (lower bound −0.36; bar −2) |
| **R3** | primary | **PASS** | **Recovery limits the damage.** After a forced miscoverage, 9.7% of post-alarm pairs were bad, against 46.3% with the running minimum. Ratio 0.21 (upper bound 0.235; bar 0.5) |
| **R4** | primary | **PASS** | **The bound recovers.** 128 of 128 runs (lower bound 0.977), median 502 tests. The running minimum recovered in 0 of 128, by construction |
| **E1** | primary | **PASS** | **Theorem 2 is robust** at τ 0.85, τ 0.92 and with less calibration data: 0 of 15,606 users and 0 of 810,877 pairs got a bad pair after the alarm |
| **E2** | primary | **PASS** | **Corollary 3 is robust:** the always-on arm gave 0 of 139,264 users a bad pair |
| S1 | secondary (prediction) | PASS | **False alarm before onset:** post-alarm bad-pair rate 0.158 (no intersection) vs 0.333 (running minimum). Per-user risk stays high (0.52–0.56), because (B2) fails |
| S2 | secondary (prediction) | PASS | **Re-alarms after a forced miscoverage:** 0.016 vs 0.883 per run |
| S3 | secondary (prediction) | PASS | **Thin hardware:** no alarm in any run; the always-on arm delivers 1.5% of oracle |
| S4 | secondary | PASS | **Certificate under feedback:** violated in 39 and 50 of 3,328 runs (upper bounds 1.5% and 1.9%) |

### Where R1's bad pairs came from (exploratory)
- **All of them come from one run:** ion2020, L0.044, p = 0.2, network 19.
- **Cause:** a false alarm at epoch 0.21, before the onset at epoch 30. This is the Corollary O case, where (B2) fails and the level paid is β.
- **Comparison:** in the same run, the running minimum delivered 1,236 bad pairs; the no-intersection bound delivered 661.

## Descriptive results
**Throughput** (good pairs ÷ oracle, pooled):

| | No check, ion2020 / ionproj | Always-on, ion2020 / ionproj |
|---|---|---|
| Default (τ 0.9, calibration 0.3) | 0.85 / 0.94 | 0.69 / 0.72 |
| τ 0.85 | 0.995 / 1.00 | 0.87 / 0.985 |
| τ 0.92 | 0.96 / 0.91 | 0.68 / 0.67 |
| Less calibration data | 0.77 / 0.87 | 0.64 / 0.64 |

- **At offset 0.044:**
  - the always-on arm keeps 0.06–0.74 of oracle;
  - the gated hybrid keeps 0.42–0.82, with whole-run per-user risk 0.12–0.55;
  - no check keeps 0.85–0.98, with whole-run per-user risk 0.17–0.64.
- **Thin hardware:** nv2 and SiV produce too few tests for the check to alarm. The always-on margin, which starts at 0.10, delivers almost nothing.

## What it shows
1. **The bound no longer needs to be a running minimum.**
   - Without it, the same guarantee holds at the same cost (−0.3 points).
   - After an unlucky early stretch, the bound comes back within about 500 tests. With the running minimum, it stays stuck until the check alarms again.
   - This removes the failure mode seen in Study 30's network 11. Theorem 2 is reported with the no-intersection bound.
2. **Both guarantees survive changes in the threshold and in the amount of calibration data.**
3. **Thin hardware is outside the closed loop's reach.** This is now measured, not only predicted.

## Limits
- Simulation only, with one 5×5 grid and ion hardware for the closed loop.
- The forced-miscoverage cell breaks the guarantee by construction. It measures recovery, not validity.
