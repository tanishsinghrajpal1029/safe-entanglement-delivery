# Study 26 ("certified delivery, control layer"): confirmatory results (11 Oct 2026)

**Pre-registration:** `README_26.md` (58cccbb6), public in commit `fc22091`. Release v0.2.1: DOI pending.

**Code, run unmodified:**

| File | sha |
|---|---|
| `study26.py` | 56436cc8 |
| `analyze_26.py` | e44895fa |
| `tasks_s26.jsonl` | a693357d (10,848 tasks) |

The job metadata in every shard records these exact hashes.

**Run output:** `runs.csv` sha256 `b31b9c98b934a16e`, 10,848 rows.

**Re-analysis:** the run was re-analysed on the Mac. The output is **byte-identical** to the PSC output (`reanalysis_26_mac.txt`).

**Timing.** The locked files were committed at 2026-10-11 01:41:56 UTC. Every shard started at 01:44:11–01:44:20 UTC, from the job metadata. The commit therefore came 2 min 15 s before the first job; the repo is in sync with GitHub.

## Verdicts

| | Tier | Result | Key numbers |
|---|---|---|---|
| **U1** | primary | **PASS** | Per-user corrected guards (bg, kg, ag2t), every hw: **0 bad in 1,012,881**; 0 of 91,392 users ever got a bad pair |
| U2 | secondary | **FAIL** | Correction cost ≤ 2 points failed on SiV ag2t (+2.43 [+0.76, +4.15]). Every other arm/hw ≤ 1.65 points; ions ≤ 0.75 |
| U3 | secondary, prediction | CONFIRMED | Memory cut-off not SAFE on ion2020, nv2 and siv. It cannot see link-to-link differences |
| U4 | secondary | reported | Matched safety vs the dev-tuned plug-in rule (plugM): see below |
| U5 | descriptive | — | **Plug-in rule without a margin: 17–19% of ion users and 11% of NV users received a bad pair** (r 3.9–15.7%) |
| **R1** | primary | **PASS** | Oracle-declared φ safe in all 48 iid cells (0 bad) |
| **R2** | primary | **PASS** | Recipe-declared φ safe at ICFO noise levels, 64 cells (1 bad pair in total) |
| **R3** | primary | **PASS** | Recipe-declared φ safe at the USTC noise level, 32 cells (91 bad, all within the bar) |
| R4 | secondary, prediction | CONFIRMED | Undeclared guards at the USTC level are not SAFE on ion2020 (ag2t, e and h): 4,625 bad |
| R5 | secondary | **FAIL** | The fleet recipe costs ≤ 3 points on SiV at every level: worst −4.47 |
| R6 | secondary, prediction (informed by the pilot) | CONFIRMED | **Persistent (AR 0.9) noise at the USTC level breaks every model-based arm on ion2020, including oracle φ**. Per-user risk 2.7–12.8% |
| **O1** | primary | **PASS** | Oracle margin d = Δ: 0 bad |
| **O2** | primary | **PASS** | Recipe margin: per-user risk bound ≤ α + β. Max 2.7%; 24 of 512 networks had d < Δ |
| O2b | secondary | PASS | Where d ≥ Δ held: 0 bad |
| O3 | secondary, prediction | CONFIRMED | Undeclared Δ = 0.044 on ion2020: **51% of users received bad pairs** |
| **S1** | primary | **PASS** | Finite memory (Q = 2, 4, ∞) at 4× load: 0 bad in 4,340,857 |

**Summary:** 7 of 7 primary hypotheses PASS. Of the 7 secondary, 5 PASS/CONFIRMED and **2 FAIL (U2, R5)**; these are costs on SiV slightly above the pre-set bars.

## Key results for the paper

**1. The per-user correction is cheap.**
- It costs ≤ 0.75 points on ion hardware and up to 2.4 on SiV.
- With it, the proved per-user guarantee holds and is met empirically: 0 of 91,392 users.

**2. Published model-based rules.**
- **The plug-in fidelity rule (EFiRAP / Q-PATH / Q-GUARD class), as published (no margin),** gave **17–19% of ion users a bad pair**. Its "guarantee" holds only if the model is exactly right.
- **With a margin tuned on dev data (plugM)**, it is safe on these networks.
- Its throughput relative to our guards (points of oracle, 90% CI):

  | hw | kg − plugM | ag2t − plugM |
  |---|---|---|
  | ion2020 | +4.2 [+3.4, +4.8] | +0.4 (CI includes 0) |
  | ionproj | +2.4 | **−3.0** |
  | nv2 | −1.6 (CI includes 0) | **+16.9** [+11.9, +21.5] |
  | siv | +20.5 | +19.4 |

  - **On SiV** the tuned margin (0.10) leaves only 4 deliveries (0.25% of oracle), so the comparison is against an almost-silent baseline.
  - **Honest reading:** on data-rich ions, a well-tuned plug-in margin is competitive. On thin hardware our guards deliver far more at the same safety.
  - **The difference that matters:** plugM's margin had to be tuned on ground truth from dev networks, and it carries **no guarantee** off them. Our guards need no tuning and keep a per-user guarantee.
- **The memory cut-off** was infeasible (no safe setting) on 3 of 4 hardware types.

**3. Real-hardware noise levels.**
- At the measured ICFO and USTC levels (iid across epochs), a data-driven declaration recipe (a 30-epoch calibration campaign, upper confidence bound on φ) restores safety, at a cost of ≤ 4.5 points on SiV.
- At the USTC level, undeclared guards on ion2020 fail.

**4. Persistent noise defeats every model-based guard** (R6). With 0.9 epoch-to-epoch persistence at the USTC level, even the oracle per-epoch φ fails (per-user risk 2.7–2.9%; recipe arms 3.3–5.0%; undeclared 11–13%). **This is the main motivation for the model-free certification layer (Study 27).**

**5. Model error measured on real hardware** (Δ up to 0.044; USTC):
- **Undeclared:** 51% of ion2020 users received bad pairs.
- **Declared from tomography with M points:** the certified-safe throughput follows a steep design curve (fraction of oracle):

  | M | ion2020 | ionproj |
  |---|---|---|
  | 4 (USTC-like) | 0.16 | 0.18 |
  | 16 | 0.38 | 0.42 |
  | 64 | 0.67 | 0.67 |
  | 256 | 0.81 | 0.77 |
  | oracle | 0.90 | 0.90 |

  Calibration precision, not link quality, limits certified throughput.

**6. Finite memory:**
- **Safety:** none of the guards (bg, kg, ag2t) delivered a bad pair at any memory size.
- **Effect on throughput and latency:** small at this load. Only nv2 and siv at Q = 2 show it, with latency up 20–60%.

## Limits
- All results are simulation on the 5×5 grid.
- φ deflation is a quasi-likelihood correction, not a theorem.
- Margins and noise levels are anchored to only two real experiments.
- The baselines are class representatives, re-implemented in our model, not the original codes.
