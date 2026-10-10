# Study 18C v17: estimated (empirical-Bayes) fleet prior (pre-registered 6 Oct 2026, before any confirmatory run)

**Why.** v16 (ledger E41) showed the controller is safe when its per-decision risk is the posterior under the true fleet prior. In simulation, though, that prior was *given* to it, which is an oracle. v17 removes the oracle: the prior is **estimated from parity counts of other fleet paths**. No fidelity labels are used.

**Method.**

- Each fleet path reports parity counts per link, taken at an unknown sawtooth phase.
- Model: link F0 ~ Normal(m, s); current λ = λ0 − 0.02·U. The drift amplitude is assumed known as operator knowledge, the same assumption as v16.
- Hyperprior: flat on a grid (m 0.70–0.9995, s 0.001–0.08). The marginal likelihood is computed exactly by quadrature.
- The controller uses the **posterior-predictive** prior, so uncertainty in the hyperparameters is carried through.
- Each evaluation path gets its **own** fleet sample, so pooled risk averages over fleet draws.

## Cloud dev pilot (disclosed; seeds 19951–19953, never reused; no confirmatory-seed runs at all)

| NV, static (g 0 / 1e-5) | Deliveries | Bad | r |
|---|---|---|---|
| `pop` (oracle prior) | 942 / 1023 | 0 / 0 | 0 |
| `eb8` (8 fleet paths × 1 window) | 1679 / 1783 | 63 / 42 | **3.75 / 2.36%** |
| `eb32` (32 × 1 window) | 1510 / 1710 | 46 / 25 | **3.05 / 1.46%** |
| `eb128` (128 × 1 window) | 1058 / 1036 | 0 / 0 | 0 |
| `eb32x10` (32 × 10 windows) | 1065 / 1075 | 0 / 0 | 0 |

**Ion cells (eb32, 4 paths, g 1e-5):** ion-proj 0.67%; τ 0.85 at 0.24%.

**What the pilot showed:** estimating the prior works only with enough fleet data. With too little data, the estimated prior is sometimes optimistic, and the low-SNR cell fails. So v17 is designed as a **dose-response in fleet data**.

## Design

- Variants: as v16 (nv_tau080, ion2020_tau090, ionproj_tau090, tau085_ion2020) × g ∈ {0, 1e-5} × **128 fresh paths** (seeds 18951–18953).
- Static window. Methods: `adaptive` (Gaussian), `pop` (oracle prior), `eb8`, `eb32`, `eb128`, `eb32x10`.
- That gives **6,144 tasks**.

**Code (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_v17.py` | `604f743db935a327` |
| `tasks_v17.jsonl` | `a8993752fa82df12` |
| `analyze_v17.py` (locked; tested on synthetic data) | `f3240a28624e589a` |

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **V1** (primary) | An estimated prior with enough fleet data is safe | `eb128` **and** `eb32x10`: r ≤ 1% in every (variant, g) group |
| **V2** (stricter) | Same, allowing for path clustering | Path-bootstrap (B = 4000) 95% upper bound ≤ 1% for both, in every group |
| **V3** | Too little fleet data breaks it | `eb8` or `eb32` exceeds 1% in ≥ 1 NV group |
| **V4** | v16 replicates | `pop` ≤ 1% in every group on fresh seeds |
| **V5** | Cost of estimating the prior | `eb128` qualified ≥ 0.8 × `pop` wherever `pop` qualified ≥ 200 |

**How results will be read:**

- **If V1 passes:** the paper claims a fully label-free, data-estimated controller, with a stated fleet-data requirement.
- **If V1 fails:** the paper scopes the guarantee to a known or well-characterised fleet prior, and reports the data requirement as open.
- **V2 failing alone** is reported as a thin-cell uncertainty, not as a violation.

**PSC.** 8 × 16 cores × 0.67 h, so the ceiling is 85 SU (worst case 387 of 400); expected 15–25 SU. Used so far: about 302.
