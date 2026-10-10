# Study 18C v16: calibrated-posterior controllers (pre-registered 6 Oct 2026, before any confirmatory run)

**Status: post-hoc improvement.** v15 G1 failed on NV-like hardware (ledger E39). v16 is designed *after* seeing that failure. Whatever v16 shows, G1 stays a recorded FAIL. v16 can only add a new, separately labelled claim.

## Why

The theory note says r_cond = E[lfdr | delivered]. That identity needs the per-decision risk to be the posterior under the **true population prior**. The Gaussian plug-in Φ(−d/s) is a flat-prior, Gaussian approximation. That raises two possible failure sources:

1. **Tail shape.** The Gaussian approximation misses heavy tails (E39 diagnosis).
2. **Prior.** A flat prior gives no shrinkage. At low signal-to-noise the controller then delivers on lucky-high estimates (winner's curse).

## Cloud dev pilot (disclosed; seeds 19931/19932, never reused)

| Variant (g = 1e-5 unless noted) | Method | Deliveries | Bad | r |
|---|---|---|---|---|
| NV, static (g 0 / 1e-5) | Gaussian adaptive | 1101 / 1118 | 18 / 28 | 1.63 / 2.50% |
| NV, static | Jeffreys exact | 873 / 884 | 11 / 8 | 1.26 / 0.91% |
| NV, ols_reset | Gaussian adaptive | 632 / 677 | 61 / 71 | 9.7 / 10.5% |
| NV, ols_reset | Jeffreys exact | 181 / 236 | 4 / 11 | 2.2 / 4.7% |
| NV, static | fleet prior **without** drift offset | 840 / 852 | 0 / 0 | 0 |
| ion-proj L3 τ 0.9, static | fleet prior **without** drift offset | 14,925 | 285 | **1.91%** |
| ion-proj L3 τ 0.9, static | fleet prior **with** drift offset (`pop`) | 11,412 | 47 | 0.41% |
| ion-proj L3 τ 0.9, static | Gaussian adaptive / Jeffreys exact | 5,770 / 11,921 | 1 / 102 | 0.02 / 0.86% |
| NV, static | `pop` / `popwide` / `popopt` | 644 / 700 / 2132 | 0 / 2 / 78 | 0 / 0.29 / 3.66% |

**What the pilot taught us:**

- An exact likelihood helps but does not suffice.
- The correctly specified prior is what restores safety.
- A prior that ignores drift is optimistic and fails.

**Peeking disclosure.** Smoke tests ran 9 confirmatory-seed tasks (paths 0–3) to check runtime only. Their outcomes are not used.

## Methods (all label-free; same paths, seeds and queue)

| Method | Per-decision risk | Estimators |
|---|---|---|
| `adaptive` | Gaussian plug-in Φ(−d/s), z-window rule (v11, unchanged) | static, ols_reset |
| `exact` | Monte-Carlo posterior P(F < τ), Jeffreys Beta per link or bin | static, ols_reset |
| `pop` | Posterior under the true fleet prior: link law, minus a uniform sawtooth offset (amplitude 0.02) common to the path | static |
| `popwide` | As `pop`, prior sd × 2 (conservative mis-specification) | static |
| `popopt` | As `pop`, prior mean + 1 sd (optimistic mis-specification) | static |

**Decision rule for the posterior methods.** Deliver iff pbad ≤ t, where t is the largest grid value at which the window mean of pbad (over pbad ≤ t) is ≤ 1%, with ≥ 20 supporting attempts. This is a local-fdr / Bayesian-FDR threshold.

**Grid.** Variants nv_tau080, ion2020_tau090 (L2), ionproj_tau090 (L3), tau085_ion2020 (L2) × g ∈ {0, 1e-5} × 64 fresh paths (seeds 18931/18932). That gives **3,584 tasks**.

**Code (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_v16.py` | `bf7882e7948b5749` |
| `tasks_v16.jsonl` | `d8217837d7566ed3` |
| `analyze_v16.py` (locked; tested on synthetic data) | `4d50170ec09ee715` |

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **H1** (primary) | A calibrated posterior restores the guarantee | `pop`: r ≤ 1% in **every** (variant, g) group |
| **H2** | Exact likelihood alone is insufficient at low SNR | `exact` exceeds 1% in ≥ 1 NV group |
| **H3** | Replication of the E39 failure | Gaussian `adaptive` exceeds 1% in ≥ 1 NV group on fresh seeds |
| **H4** | No efficiency cost at high SNR | `pop` qualified deliveries ≥ 0.8 × `adaptive` (static) in every ion group |
| **H5** | Limitation: prior optimism breaks it | `popopt` exceeds 1% in ≥ 1 group; `popwide` descriptive |

**How results will be read:**

- **If H1 passes:** the paper's assumption A1 is restated as *posterior calibration*. The Gaussian rule becomes a high-SNR approximation, and `pop` is the general controller, honestly scoped:
  - in the simulation, the prior equals the generating law, which is the best case;
  - `popwide` and `popopt` show sensitivity to the prior.
- **If H1 fails:** the paper reports the low-SNR regime as an open limitation, with no fix claimed.

**PSC.** 8 × 16 cores × 0.5 h, so the ceiling is 64 SU; expected 6–15 SU. Used so far: about 292 of 400.
