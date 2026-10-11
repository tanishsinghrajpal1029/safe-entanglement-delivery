# Study 28 ("model-checked delivery"): confirmatory results (11 Oct 2026)

## What was run
- **Pre-registration:** `README_28.md`, with the locked `analyze_28.py` (sha 65d4ccf220c2d86e). It was committed as `023faed` at 06:24:48 UTC.
- **Timing:** the first confirmatory shard started at 06:26:51 UTC, so the commit came 2 min 3 s before the first job.
  - The commit time is the local commit time. Confirm the push time from GitHub's activity view.
- **Code:** `study28.py` (70e98b5a) and tasks d469a195 (5,248 tasks), recorded in the job metadata. Seeds 19301–19304 are fresh.
- **Run output:** `runs.csv` sha256 `b1fae5f497cce25c`, 5,248 rows. No epoch was clamped.
- **Analysis:** the locked script was run on PSC on a compute node (`s28_analysis.txt`), and re-run in the cloud (`reanalysis_28_cloud.txt`), which gives identical verdict lines.

## Verdicts

| | Tier | Result | Numbers |
|---|---|---|---|
| **H1** | primary | **PASS** | **Model-check validity.** False first alarms in 3 of 1,024 runs (0.29%), against a level of 3.04%; cluster upper bound 0.68% |
| **H2** | primary | **PASS** | **Detection.** Alarm in 32/32 networks in all 4 powered cells. Median first alarm at epoch 7.9–22.8 |
| **H3** | primary | **PASS** | **Harm.** Bad delivered pairs, kgM ÷ kg: 0.30 / 0.13 (ion2020, p = 0.1 / 0.2) and 0.17 / 0.08 (ionproj). Upper bounds 0.10–0.36 |
| **H4** | primary | **FAIL** | **Delivered-pair risk after the first alarm:** 6,232 / 778,640 = 0.80%, upper bound 2.27% (bar ≤ 1%). See below |
| **H5** | primary | **PASS** | **No cost without a stressor:** 0.00 points in every cell (no false alarms there) |
| **H6** | primary | **PASS** | **Network-wide guarantee:** 0/128 kgN networks delivered any bad pair; Clopper–Pearson upper bound 2.3% |
| **H7** | primary | **PASS** | **Cost of the network-wide guard:** 0.46 (ion2020), 0.55 (ionproj), −0.18 (NV), 2.41 (SiV) points; all upper bounds ≤ 4.24 |
| S1 | secondary | PASS | **Free test data vs tomography** (throughput, fraction of oracle): kgM (p = 0.1) 0.485 vs the 16-point tomography margin's 0.399 on ion2020, and 0.468 vs 0.482 on ionproj. Oracle 0.918 / 0.940 |
| S2 | secondary | PASS | **The e-process beats the naive per-epoch detector** in every cell. It always alarms, against 34–78% for the naive one, with 3–8× fewer bad pairs |
| S3 | secondary (prediction) | PASS | **No power where the theory predicts none:** 2 of 1,792 runs alarmed (0.11%). Both were false alarms on one NV network with readout error at the bound |
| S4 | secondary | PASS | **The network certificate stays valid under feedback:** 1.1% (p = 0.1) and 0.8% (p = 0.2) of runs violated; upper bounds ≤ 1.4% |

**Summary:** 6 of 7 primary hypotheses pass, and 4 of 4 secondary hypotheses pass. **H4 fails.**

## H4 failure (exploratory diagnosis, not pre-registered)
- **Where the bad pairs came from:** all 6,232 post-alarm bad pairs came from **one network** (ion2020, p = 0.1, network 19). The other 127 networks in the powered cells delivered 0 bad pairs after their alarm.
- **Cause:**
  - That network alarmed after only 8 tests (epoch 0.12).
  - With fewer than NMIN = 50 tests, the response rule raises the margin by the fixed step of 0.02, against a true offset of 0.044.
  - The restarted check, now at a stricter level, did not alarm again within the run. About 26% of that network's later pairs were bad.
- **What it means:** the e-process itself is valid (H1) and fast (H2). The weak point is the heuristic margin response after an early alarm, as the pre-registration warned ("the response is a heuristic, not a guarantee").
- **Possible fix (not tested here):** after a low-information alarm, either raise the margin to the declared maximum, or keep estimating the margin from all tests since the first alarm. A future study would have to pre-register and test this. Nothing here is re-tuned.

## Descriptive results (D1–D3)
**Ion hardware, undeclared Δ = 0.044.** The table gives the share of delivered pairs that were bad, and the share of users who ever got a bad pair.

| hw | arm | Bad pairs | Users ever bad | Margin | Throughput |
|---|---|---|---|---|---|
| ion2020 | kg | 43.5% | 53.0% | — | 0.961 |
| ion2020 | kgM p = 0.1 / 0.2 | 31.6% / 20.4% | 48.6% / 45.6% | 0.080 / 0.083 | 0.485 / 0.392 |
| ion2020 | tomography m16 | 3.5% | 1.0% | 0.085 | 0.399 |
| ion2020 | oracle margin | 0 | 0 | 0.044 | 0.918 |
| ionproj | kg | 9.8% | 26.1% | — | 0.961 |
| ionproj | kgM p = 0.1 / 0.2 | 3.6% / 1.8% | 18.5% / 16.0% | 0.088 / 0.087 | 0.468 / 0.451 |
| ionproj | tomography m16 | 0 | 0 | 0.081 | 0.482 |

The throughput column counts good pairs only, so kg's high value includes delivering every pair it could.

## What it shows
1. **Closed loop.** The tests users already run for the model-free certificate also detect systematic model error. Detection was certain in every powered network, typically within 8–23 epochs. False alarms stayed far below their level (0.3%).
2. **Harm is limited, not prevented.**
   - Bad delivered pairs fell by 70–92%.
   - But the users who were harmed before the alarm stay harmed: 46–49% of users on ion2020, against 53% without the check.
   - The per-user guarantee is not restored. This is the fault-exposure no-go again: no data-driven rule can act before the data arrive.
3. **The price is margin precision.**
   - After the alarm, the declared margin was about twice the true offset (0.08–0.09 vs 0.044).
   - Throughput fell to about half of oracle, similar to a dedicated 16-point tomography campaign. The difference is that the check needs no extra measurements, only the test data users already collect.
4. **Blind to sparse failures.** The check is blind to persistent noise and memory faults, which push only a few pairs just below threshold. It is also blind on thin hardware, which gets too few tests. Both were predicted (S3) and are consistent with Proposition N.
5. **The network-wide guarantee is cheap.** "No user anywhere gets a bad pair" (probability at most α) costs 0.5 points of throughput on ions and 2.4 on SiV.
6. **The certificate stays valid** when the network adapts to the test outcomes.

## Limits
- This is simulation, with stylised stressors.
- The margin response is a heuristic, and H4 shows it can fail after a low-information alarm.
- The powered cells are ion hardware only.
- The horizon is 2.5 h.
