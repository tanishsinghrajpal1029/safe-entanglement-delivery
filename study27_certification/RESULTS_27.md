# Study 27 ("certified delivery, certification layer"): confirmatory results (11 Oct 2026)

**What was run**
- **Pre-registration:** `README_27.md` (dd6335aa), public in commit `63d20c6` at 02:38:49 UTC. Shards started 02:40:40–02:42:42 UTC, so the commit came 1 min 51 s before the first job.
- **Code** (run unmodified; the job metadata records these hashes):
  - `study27.py` 1281b710;
  - `cert.py` 6b84bbdd;
  - `ptm_corr.py` 47d89f15;
  - `analyze_27.py` 8d455051;
  - tasks 452a078e (3,072).
- **Run output:** `runs.csv` sha256 `53443c34b17cde71`, 3,072 rows.
- **Re-analysis:** re-run in the cloud; the output is **byte-identical** to the PSC output.

## Verdicts

| | Tier | Result | Numbers |
|---|---|---|---|
| **C1** | primary | **PASS** | Per-user certificate wrong (ever above the true kept-pair average), as violated / eligible users. p = 0.05: **0/3,283**. p = 0.1: **12/3,584** (0.33%; 95% upper bound 0.50%). p = 0.2: **11/21,358** (0.05%). The bar is ≤ 5% |
| C1b | secondary | PASS | Worst cell 2.3%, against a 10% allowance (120 cells checked) |
| **C2** | primary | **PASS** | Network-pooled certificate wrong. p = 0.05: 17/1,931 (0.9%). p = 0.1: 29/2,115 (1.4%; upper bound 1.9%). p = 0.2: 6/2,313 (0.3%) |
| C3 | descriptive | — | In the **80 cells where the model-based control layer was NOT safe**, the certificate was wrong for ≤ 0.34% of users and ≤ 1.2% of networks |
| C4 | descriptive | — | Tightness for users with ≥ 500 kept pairs on ions (arm kg, no stressor): see below |
| C5 | descriptive | — | Network certificate vs truth: see below |
| C6 | descriptive | — | Cost of testing: kept qualified pairs fall to 0.948× at p = 0.1 and 0.842× at p = 0.2, relative to p = 0.05 |

**Summary:** both primary hypotheses PASS (2 of 2), and the secondary C1b PASS.

## What it shows

**1. The certificate stays correct when the control layer breaks.**
- Undeclared model error, persistent noise at the USTC level, and memory faults the models cannot see all break the per-pair guarantee: up to 26% of delivered pairs fell below threshold.
- Throughout, the model-free certificate of the kept-pair **average** fidelity was wrong for only 0–1.4% of users or networks, against α = 5%.

**2. Proposition N, shown in the network.**
- On ion2020 with undeclared Δ = 0.044, the guarded network delivered **126,446 bad pairs out of 506,494 (25%)**.
- Yet the kept-pair average fidelity was 0.926, and the certificate (0.888) was correct about that average.
- An average-fidelity certificate cannot reveal per-pair threshold failures. Per-pair guarantees need a model.

**3. Tightness and cost.**
- Gap between the true kept-pair average and the certificate, for heavy ion users:

  | p | ion2020 | ionproj |
  |---|---|---|
  | 0.05 | 0.16 | 0.14 |
  | 0.1 | 0.10 | 0.08 |
  | 0.2 | 0.07 | 0.05 |

- Network-pooled certificates on ions: 0.89–0.92, against a truth of 0.92–0.95.
- **Thin hardware cannot be certified at this horizon.** NV network certificates were 0.09–0.44, SiV ≈ 0, with only 4,800–33,000 (NV) and 740–5,500 (SiV) delivered pairs per cell.
- The floor: even perfect pairs need 1,404 / 678 / 315 kept pairs at p = 0.05 / 0.1 / 0.2 to certify ≥ 0.9.

**4. Control quality and certification.**
- Where the guard works (no stressor), the certificate is higher and the per-pair failures are zero.
- A better control layer raises the certified average. The model-free layer catches what remains only on average.

## Limits
- This is simulation. Test outcomes are drawn from the model's true correlators.
- Measurements are ideal: the A3′ readout bound is not exercised.
- Proposition C1 is a known-type result; this study shows its behaviour in an adaptive network, not a new theorem.
