# Study 28 ("model-checked delivery"): pre-registration (11 Oct 2026)

**Status:** locked. Commit this file publicly, together with `analyze_28.py`, before the first confirmatory job.

**Related files**
- Design and dev history: `README_28_PILOT.md`.
- Theory: `THEORY_28.md`.
- Adversarial review: `REVIEW_28.md`.

## Question
- Can the tests a user already runs for the model-free certificate also detect that the model behind the per-pair guard is wrong, and limit the harm?
- What does a network-wide guarantee cost?

## Design
The simulator is `study28.py`, unchanged since the pilot.

- **Hardware:** 4 types (ion2020, ionproj, NV, SiV).
- **Scenarios:** 5:
  - none;
  - undeclared model optimism Δ = 0.044;
  - USTC-level persistent noise;
  - memory fault at epoch 45;
  - readout error at the declared bound.
- **Arms:**
  - kg and kgN, with no feedback;
  - kgM, kgNM and kgP, each at p = 0.1 and p = 0.2.
- **Baselines on ion hardware, Δ = 0.044:**
  - margin declared from 16 tomography points;
  - oracle margin.
- **Size:** 32 networks per cell, 5,248 tasks.
- **Seeds:** 19301–19304. These are fresh; the pilot used 20301–20304.
- **Horizon:** 90 epochs of 100 s.

## Dev pilot (dev seeds only; disclosed)
The pilot run is `des_p28_psc/runs.csv` (sha `ba9d197c`, 1,312 rows, 8 networks per cell).

- **Detection:**
  - kgM detected the undeclared optimism in every ion network (8/8 in each of the 4 cells). Median first alarm was epoch 6.5–30.
  - Bad delivered pairs fell to 0.07–0.32 of kg's count.
  - After the first alarm, 0 bad pairs in 191,969 deliveries.
- **Cost of the margin response:**
  - Margins 0.078–0.093, against a true offset of 0.044.
  - Throughput 0.25–0.57 of oracle, comparable to a 16-point tomography campaign (0.26 / 0.47). The oracle margin reached 0.90 / 0.94.
- **Per-user risk stays high** (37–45% on ion2020) because the bad pairs come before the alarm. The check limits how long harm lasts; it does not restore the per-user guarantee.
- **No power**, as predicted: no alarms on NV, SiV, persistent noise or fault (0/448 runs).
- **Naive per-epoch detector:** alarmed in 38–88% of networks, with far less harm reduction.
- **False alarms (kgM/kgNM, no stressor or readout at the bound):** 1 of 256 runs.
- **Network-wide guard (kgN):** 0/32 networks with a bad pair. Cost 0.3–0.4 points on ions and 2.1 on SiV.
- **Certificate violations:** 0.3% (p = 0.1) and 0.15% (p = 0.2).
- **No code change after the pilot.**
  - The analysis bars below were set after it.
  - H7's bar was set to 5 points, not the 3 first considered, because SiV's pilot cost was 2.1 points with an upper bound of 4.9 (disclosed).
  - With 8 networks per cell, H6 failed on the pilot (0/32, CP upper bound 8.9%) because the pilot is too small, not because the bar is too tight.

## Hypotheses (`analyze_28.py`, locked)
Bootstrap: 4,000 resamples of networks within each hardware type, one-sided 95%.

| | Tier | What is tested | Pass if |
|---|---|---|---|
| **H1** | primary | Validity of the model check: kgM/kgNM runs in the no-stressor and readout-at-bound scenarios. Measured as the rate of first alarms before any tested violation of the null, and as false segment alarms per run | First-alarm rate ≤ β₁ = 0.0304, and both bootstrap upper bounds ≤ 0.05 |
| **H2** | primary | Detection in the powered cells (ion2020 and ionproj, Δ = 0.044, p = 0.1 and 0.2) | Alarm in ≥ 90% of networks in each of the 4 cells |
| **H3** | primary | Harm: bad delivered pairs under kgM ÷ under kg, same networks, in the 4 powered cells | Bootstrap upper bound ≤ 0.50 in each cell |
| **H4** | primary | Delivered-pair risk after the first alarm, powered cells pooled | Bootstrap upper bound ≤ 1% |
| **H5** | primary | No cost without a stressor: qualified throughput of kg minus that of kgM, ion hardware, each p | Bootstrap upper bound ≤ 1 point in each cell |
| **H6** | primary | Network-wide guarantee: kgN networks with any bad delivered pair, no stressor | Clopper–Pearson 95% upper bound ≤ 5% |
| **H7** | primary | Cost of the network-wide guard: throughput of kg minus that of kgN, no stressor, every hardware type | Bootstrap upper bound ≤ 5 points on each |
| S1 | secondary | Free test data vs dedicated tomography: kgM (p = 0.1) throughput vs the 16-point tomography margin, ion hardware | kgM ≥ m16 − 0.05 on both |
| S2 | secondary | The e-process beats the naive per-epoch detector: bad pairs under kgM < under kgP, powered cells | In each cell |
| S3 | secondary (prediction) | No power where the theory predicts none: NV, SiV, persistent noise, fault (kgM/kgNM) | Alarm rate ≤ 10% |
| S4 | secondary | Network certificate validity under feedback (replicates Study 27), each p | Clopper–Pearson upper bound ≤ 5% |
| D1–D3 | descriptive | Risk, per-user risk, margins, throughput, alarm rates in every cell | — |

**Commitment.** No change after this point, and every outcome is reported.

**What the hypotheses do and do not test:**
- H1 checks a theorem, so a FAIL would mean a bug or a broken assumption.
- H2–H4 test whether the check is useful where it has power.
- S3 records in advance that the check is blind to sparse failures, consistent with Proposition N.
- The margin response is a heuristic, not a guarantee.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `study28.py` | `70e98b5a9fb94599` |
| `mcheck.py` | `a05f0822c0335f3f` |
| `lb.py` | `04e8994ae8ebebef` |
| `analyze_28.py` (locked) | `65d4ccf220c2d86e` |
| `tasks_s28.jsonl` (5,248) | `d469a195f9b955da` |
| `tasks_p28.jsonl` (1,312, pilot) | `c4d8759984aaa408` |
| `cert.py`, `ptm_corr.py`, `study26.py` (unchanged) | `6b84bbdd`, `47d89f15`, `56436cc8` |

**PSC:** 32 shards × 16 cores × 60 min. Ceiling 512 SU; expected about 100–130 SU.
