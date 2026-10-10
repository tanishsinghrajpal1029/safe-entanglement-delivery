# Study 18C v8: confirmatory test of the false-discovery risk law (pre-registered 5 Oct 2026, before any v8 run)

**Code.** `drift_queue_des_v8.py` (sha `5e165d38…`) is v7 with only these changes:

- rho 0.3 → 0.1
- T 100 → 30 s
- F0 grid shifted by half a step
- new seed and run tags

**Analysis code, fixed now:**

- `analyze_v7.py` (sha `c9f06b92…`), run as `python3 analyze_v7.py des_v8_mac`
- `analyze_kappa.py` (sha `c1a855e6…`), run as `python3 analyze_kappa.py des_v8_mac`

## Why

v7 (ledger E23) passed R1 and R2, failed R3, and suggested *exploratorily* that a single number κ = p0·s/P(h ≥ 0) orders the whole risk/goodput trade-off. Here:

- p0 is the attempt density at the threshold;
- s is the SD of the estimator error;
- P(h ≥ 0) is the share of attempts above the threshold.

The κ result was found after looking at the data, so it must be confirmed on fresh conditions before it can be a claim.

## Predictions

| | Prediction | Statistic and bar |
|---|---|---|
| S1 | **R2 replicates:** r_cond predicted from each run's own attempt histogram | Runs with ≥ 100 deliveries and z ≥ 1: Spearman ≥ 0.9, and median \|ln(meas/pred)\| ≤ ln 1.5 over runs with bad > 0 (the `R2:` line) |
| S2 | **κ orders the trade-off** | At z ∈ {1, 2}, across κ bins (0, .05], (.05, .1], (.1, .2], (.2, .4], (.4, .8]: median power never rises and median r_cond never falls (the `S2:` line) |
| S3 | **R1 replicates** | g ≤ 1e-5: median of the per-run maximum \|obs − pred\| ≤ 0.05 (the `R1` line) |

These analysis scripts and bars are fixed. Pass or fail, everything gets reported.
