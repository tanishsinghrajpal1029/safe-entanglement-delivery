# Study 29 ("margin response"): confirmatory results (11 Oct 2026)

## What was run
- **Pre-registration:** `README_29.md`, with the locked `analyze_29.py` (4a54c1e3). It was committed as `a779735` at 15:34:43 UTC.
- **Timing:** the first confirmatory shard started at 15:39:34 UTC, so the commit came 4 min 51 s before the first job.
- **Code:** `study29.py` (532e612f) and tasks e9c11dcb (4,352 tasks), as recorded by the job metadata. Seeds 19311–19314 are fresh.
- **Run output:** `runs.csv` sha256 `b751d724625ee2ec`, 4,352 rows. No epoch was clamped.
- **Analysis:** run on PSC (`s29_analysis.txt`) and re-run in the cloud (`reanalysis_29_cloud.txt`).
  - The two outputs are identical below the header line.
  - The header differs only in how numpy prints one value (`np.int64(90)` vs `90`).

## Verdicts: 6 of 6 primary PASS; 4 of 4 secondary PASS

**kgMT** is the tracking response.

| | Tier | Result | Numbers |
|---|---|---|---|
| **T1** | primary | **PASS** | kgMT delivered 0 bad pairs in 5,765,233 post-alarm deliveries, across all model-error and forced-alarm cells. Upper bound 0 |
| **T2** | primary | **PASS** | **Study 28's failure case** (an alarm forced after 8 tests, offset 0.044): 0/128 kgMT runs had a post-alarm bad pair, upper bound 2.3%. Study 28's response (kgM) had one in 127/128 runs |
| **T3** | primary | **PASS** | Median post-alarm margin above the true offset: +0.006 to +0.011 in all 8 cells |
| **T4** | primary | **PASS** | Throughput gain over Study 28's response at offset 0.044: +24 to +34 points; lower bounds +17.5 to +25.2 |
| **T5** | primary | **PASS** | False segment alarms when the margin can fall: 0 in 256 runs, with 2.6 restarts per run |
| **T6** | primary | **PASS** | Recovery from a false alarm: the margin returns to 0.008–0.010. Jump (kgMJ) stays at 0.10 |
| U1 | secondary | PASS | The upper bound matters: with the point estimate, 102/512 runs had post-alarm bad pairs; with the bound, 0/512 |
| U2 | secondary | PASS | Tracking beats 16-point tomography: 0.766 vs 0.352 (ion2020) and 0.793 vs 0.529 (ionproj). Oracle: 0.910 / 0.939 |
| U3 | secondary | PASS | The alarm gate matters: always-tracking costs 14.1 / 15.6 points without a stressor |
| U4 | secondary | PASS | The certificate stays valid: 2.3% / 1.6% of runs violated; upper bounds ≤ 2.7% |

## Arms compared (descriptive)
Pooled over hardware and p. Bad pairs are shares of delivered pairs. The margin is the median post-alarm margin. Throughput is the fraction of oracle.

**Offset 0.044**

| Arm | Bad pairs (all) | Bad after the alarm | Margin | Throughput |
|---|---|---|---|---|
| kg (no check) | 42.8% / 11.9% (ion2020 / ionproj) | — | — | 0.96 |
| kgM (Study 28) | 13.4% | **2.65%** | 0.084 | 0.48 |
| kgMJ (jump) | 12.5% | 0 | 0.087 | 0.46 |
| **kgMT (tracking)** | **7.8%** | **0** | **0.053** | **0.78** |
| kgMTp (point estimate) | 7.2% | 0.12% | 0.046 | 0.85 |
| Exact margin (oracle) | 0 | 0 | 0.044 | 0.91 / 0.94 |

**Forced early alarm (offset 0.044)**

| Arm | Bad after the alarm | Throughput |
|---|---|---|
| kgM | 19.6% | 0.87 |
| kgMJ | 0 | 0.15 |
| **kgMT** | **0** | **0.78** |

**Offsets 0.02 and 0.08 (kgMT):** margins 0.028 and 0.089; throughput 0.90 and 0.81; 0 bad pairs after the alarm.

## What it shows
1. **Study 28's failure is fixed.** In the failure case, Study 28's response failed in 127/128 runs. Tracking had 0 post-alarm bad pairs in all 128, and 0 in 5.8 million post-alarm deliveries overall.
2. **The margin price is mostly gone.** Margins sit 0.006–0.011 above the true offset, against about 2× before. Throughput rises from about 0.48 to about 0.78 of oracle, close to the exact-margin baseline (0.91–0.94) and far above 16-point tomography (0.35–0.53).
3. **Each part of the design is needed:**
   - Without the upper bound, 20% of runs leak bad pairs.
   - Without the alarm gate, throughput drops about 15 points with no stressor.
   - Jumping to the maximum margin is safe but wastes almost everything, and never recovers from a false alarm.
   - Probe tests on blocked pairs keep the estimate supplied with data.
4. **What has not changed:**
   - Harm before the first alarm still happens: 27–30% of users get a bad pair under offset 0.044.
   - The margin response is a heuristic. The formal guarantee is on the alarm (Prop. MC).
   - Probe tests need the end nodes to cooperate.
   - Only constant offsets on ion hardware were tested. Pair-varying model error and offsets that change over time are not covered.
