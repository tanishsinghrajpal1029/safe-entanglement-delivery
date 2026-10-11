# Study 30 ("provable closed loop"): confirmatory results (11 Oct 2026)

## What was run
- **Pre-registration:** `README_30.md` (24968191e1d63a83) and the locked `analyze_30.py` (c8b9914c296b5fcb).
  - Public commit `f5f23f2` at 19:48:04 UTC. The first confirmatory shard started at 19:50:08 UTC, 2 min 4 s later. Confirm the push time on GitHub.
- **Code and tasks:** `study30.py` e796ebb7c05a28cf and `tasks_s30.jsonl` 15e156bc8734488c, recorded in every shard's metadata. Seeds 19321–19324.
- **Compute:** 32 shards × 16 workers; the longest shard took 3,749 s, about 530 SU in total.
- **Output:** `runs.csv` sha256 8e31b20a6ff44006, 8,384 rows. No epoch was clamped.
- **Analysis:** PSC compute node (`s30_analysis.txt`), re-run in the cloud (`reanalysis_30_cloud.txt`). The verdicts and tables are identical; only the formatting of one header line differs.

## Verdicts: 5/5 primary PASS, 6/6 secondary PASS

| | Tier | Result | Numbers |
|---|---|---|---|
| **P1** | primary | **PASS** | **Theorem 2 in class.** 230 of 89,585 users got a bad pair after the alarm (bound 0.60%, bar ≤ 10%). 8,184 of 3,911,876 post-alarm pairs were bad (bound 0.50%, bar ≤ 1%). 2,048 runs |
| **P2** | primary | **PASS** | **Study 28's failure case** (forced early alarm): 0/384 runs had a post-alarm bad pair (CP bound 0.78%). The Study 29 heuristic (kgMT) failed in 1 of 128 runs |
| **P3** | primary | **PASS** | **Always-on arm** in constant-offset cells: 0 of 208,896 users ever got a bad pair |
| **P4** | primary | **PASS** | **New checks are valid.** False segment alarms: plug-in 1/128 runs (bound 0.023); hybrid 0/128 |
| **P5** | primary | **PASS** | **The bound is tight.** Median post-alarm margin minus true offset: +0.011 to +0.013 (hybrid, o0.044); +0.006 to +0.007 (storage class, s0.044) |
| S1 | secondary (prediction) | PASS | **Price of provability** against the Study 29 heuristic at o0.044: 1.3–8.5 points of throughput |
| S2 | secondary (prediction) | PASS | **Debt.** Under late onset, the plug-in alarmed in 82.8% of runs, the mixture in 70.3% |
| S3 | secondary | PASS | **The hybrid is robust.** Its alarm rate is within 0.03 of the better component in L0.044, o0.044, s0.044 and h0.044 |
| S4 | secondary (prediction: unsafe) | PASS | **Outside the theorem the loop fails, as predicted.** Post-alarm per-user risk: L0.044F 0.60; h0.044 0.14; s0.044 with constant shape 0.92; storage shape under constant offset 0.62. kgMCa under late onset, whole run: 0.34 |
| S5 | secondary | PASS | Certificate violated in 149 (p = 0.1) and 260 (p = 0.2) of 8,384 runs; bounds 2.0% and 3.4% (bar ≤ 5%) |
| S6 | secondary (prediction) | PASS | **Static competitor:** a fixed margin of 0.10 delivers 0% of oracle on both hardware types |

### Where P1's bad pairs came from (exploratory diagnosis, not pre-registered)
All 8,184 bad pairs, and all 230 harmed users, come from **2 of 2,048 runs**, both late-onset networks on ionproj at p = 0.2. **The hybrid arm (kgMCh) had none.**

1. **Plug-in arm, network 5: a false alarm at epoch 16, before the onset at 30.**
   - The first window started with no offset, so (B2) failed. This is the Corollary O case, which costs β.
   - Result: 6,109 bad of 12,940 post-alarm pairs.
2. **Mixture arm, network 11: a real alarm at epoch 61.8, inside the class.**
   - At the first look (150 tests), the offset confidence sequence's statistic averaged −0.052, against a truth of at least 0.044. That unlucky start excluded θ, and U fell to 0.028.
   - U is a running minimum, so it stayed there even though the later average (about 0.053) contradicted it.
   - Result: 2,075 bad of 5,027 post-alarm pairs.
   - Re-running the task in the cloud reproduced it exactly.
   - This is the theorem's allowed failure, at most α′ ≈ 1.5% per window. The observed rate is 1 window in about 1,900 alarmed in-class runs.

## Descriptive results (D1–D4)

**D1: detection is the bottleneck once the offset is physical.** The offset is now in the truth, unlike Studies 28–29.
- **o0.044:** alarms in 81–94% of ion2020 runs (median first alarm at epoch 27–55) and 97–100% of ionproj runs (epoch 15–30).
- **o0.02:** detected in only 6–56% of runs.
- **Late onset:** 41–100% of runs alarm, typically 20–50 epochs after the onset.
- Study 28 reported epochs 8–23 at o0.044, with the offset in the model (ledger E134).

**D2: worst-user risk over the whole run** (users ever given a bad pair)

| Scenario | No check | Gated loops | Always-on |
|---|---|---|---|
| o0.02 | 0.26 | 0.25 | 0 |
| o0.044 | 0.53 | 0.47–0.49 | 0 |
| o0.08 | 0.76 | 0.64–0.69 | 0 |
| s0.044 | 0.76 | 0.71–0.74 | 0.21 (out of class) |
| h0.044 | 0.51 | 0.45–0.47 | 0.02 |

Most harm happens before the alarm, as Proposition N says no data-driven rule can prevent.

**D4: throughput** (fraction of oracle)

| | No stressor, no check | Always-on, no stressor | o0.044, gated hybrid | o0.044, always-on | o0.044, exact margin |
|---|---|---|---|---|---|
| ion2020 | 0.895 | 0.757 | 0.536 | 0.112 | 0.779 |
| ionproj | 0.916 | 0.701 | 0.705 | 0.608 | 0.888 |

A fixed margin of 0.10 delivers 0.

## What it shows
1. **The closed loop is now provable, and the proof holds in simulation.** After an alarm, inside the offset class, users are protected at the theorem's level. The margin is only about 0.01 above the true offset, so provability costs 1–9 points against Study 29's heuristic. That heuristic failed once in Study 28's own failure case; the provable rule did not.
2. **The always-on version gives a full guarantee** (0 of 208,896 users) whenever the offset class holds from the start. It pays 14–21 points with no stressor and much more on thin margins (ion2020 at o0.044).
3. **The honest limit is detection, not response.**
   - With physical offsets, the check needs tens of epochs, and small offsets often go undetected. So whole-run worst-user risk falls only from 0.53 to about 0.48 at o0.044.
   - Outside the class (heterogeneous offsets, a wrong shape, or a false alarm before the onset) the guarantee fails badly, as pre-registered.
4. **A running minimum makes one early miscoverage permanent** (network 11). This is within the theorem, but a window-restart or re-check policy could make recovery faster. Future work.

## Limits
- This is simulation of ion hardware only (Study 31b is a single hardware run).
- The offset classes are stylised.
- The per-user bound needs (B1)–(B4).
- The detection-power results replace Study 28's, which were inflated.
