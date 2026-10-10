# Study 18C v7: does threshold delivery behave like a false-discovery problem? (pre-registered 5 Oct 2026, before any v7 run)

The script is `drift_queue_des_v7.py`; it imports v6 and v4 unchanged. This is a development run.

## What v6 showed (`des_v6_mac/SUMMARY.csv`, sha `0578583b…`; ledger E22)

| Prediction | Result | Detail |
|---|---|---|
| Q1 | **FAIL** | At g = 1e-4, `reset` beats `static` by only 0.010 (ion_2020) and 0.012 (ion_proj). The bar was 0.10. |
| Q2 | **PASS** | At g = 1e-4, the best estimator reaches 0.018 and 0.065 of the oracle, both below 0.5 |
| Q3 | **FAIL** | 6 of 11 feasible eval rows have r_cond > 1% (up to 6.0%), although every one met CP-UCB ≤ 1% on dev paths |
| Q4 | **Partial** | Per-path fraction rises monotonically with headroom, but there is no collapse across combos without a normalisation |

**Mechanism found.** Bad deliveries sit on paths whose mean true F is below 0.9. In combo 0, 198 of 539 deliveries on paths with h < −0.01 were bad, against 11 of 11,512 on paths with h > 0.003. Eval path sets had more sub-threshold paths than dev:

| Combo | Dev | Eval |
|---|---|---|
| 0 | 84% | 91% |
| 1 | 91% | 97% |

**Hypothesis H-FDR.** Per-decision confidence (z) fixes the false-delivery probability α(h) of each sub-threshold attempt. r_cond = P(bad | delivered), however, also depends on the base rate of sub-threshold attempts, which moves with path population, drift phase and hardware. Risk calibrated on one population does not transfer.

## v7 design

- **One path per run.** All links share a fixed F0, swept across the threshold (13 values per cell).
- **Grid.** g {0, 1e-5, 1e-4} × est {static, ols_reset} × z {0, 1, 2, 3} × 3 replicates. rho 0.3, T 100 s, m 0, load 0.9, D 0.25 s.
- **Per-attempt logging.**
  - Attempts and deliveries in h-bins of width 0.0025.
  - Per-run moments of the estimator error e = F̂ − F_true.
  - Per-run mean of the confidence offset F̂ − F̂_low.

## Predictions, fixed before running

- **R1 (Gaussian error model).** Delivery happens iff e ≥ off − h. With e ~ N(μ, s) and off its per-run mean, the predicted delivery probability is P(h) = Φ((h + μ − off)/s).
  - For runs at g ≤ 1e-5 with z ≥ 1, the median over runs of the maximum |observed − predicted| in bins with ≥ 200 attempts is ≤ 0.05.
  - At g = 1e-4 with `static`, e and h are correlated through the drift phase, so R1 may fail there. That case is reported, not tuned.
- **R2 (risk predicted from the base rate).** Integrating P(h) over each run's own attempt histogram predicts its r_cond.
  - Over runs with ≥ 100 deliveries and z ≥ 1: Spearman ρ(predicted, measured) ≥ 0.9, and the median |ln(measured / predicted)| ≤ ln 1.5.
- **R3 (base-rate dependence).** At fixed (cell, g, est, z ≥ 1), r_cond rises as F0 falls: Kendall τ(F0, r_cond) ≤ −0.6 in at least 75% of the series.

**If R1–R3 hold:** the paper's core becomes a closed-form, base-rate-aware risk law. That covers the dimensionless frontier number κ = (attempt density at threshold × estimator error) / (attempt mass above threshold), and the drift floor on estimator error, s_min ∝ (g·σ²/(ρR))^{1/3}.

**If they fail:** the risk is not governed by this mechanism, and that gets reported.
