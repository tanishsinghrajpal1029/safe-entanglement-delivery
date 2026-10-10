# Study 18C v6: confidence-bound delivery controller (pre-registered 4 Oct 2026, before any v6 run)

This is a development run, **not** the final run. The script is `drift_queue_des_v6.py`. It imports v5 and v4 unchanged.

## What v5 showed (`des_v5_mac/SUMMARY.csv`, sha `0ee68bf7…`; ledger E21)

| Prediction | Result | Detail |
|---|---|---|
| P1 | **PASS** | At fast drift (g = 1e-4) the best rule reaches 0.146 (ion_2020) and 0.012 (ion_proj) of the oracle, both below 0.5. Caveat: the best rho sat at the grid edge (0.3). |
| P2 | **FAIL** | `reset` and `ols_reset` were infeasible at g = 1e-4 (diagnosis below) |
| P3 | **PASS for `ucb`** | 0 of 21 eval rows above 1% |
| P3, 2nd part | **FAIL** | "The point rule violates" did not happen: with ≥ 50 deliveries required, it was safe too |
| P4 | **PASS** | Moving the deadline from 0.25 to 1.0 s changed results by at most 0.011 |

**Diagnosis of P2.** Right after a re-alignment, the post-reset window holds very few pairs. With a fixed margin, the controller trusts them anyway. For example, P(all 10 parities even | λ = 0.93) = 0.70, which gives λ̂ = 1, and the pair is delivered whatever the margin. Dev r_cond for `reset` even *rises* with the margin (0.14 → 0.65). **A fixed margin is unsafe for estimators whose precision varies.**

**Second issue.** Dev and eval path populations differ strongly (best dev qualified rate 0.37/s against 4.26/s on eval). Path-to-path heterogeneity near threshold dominates the aggregates.

## v6 design

| | |
|---|---|
| Controller | Deliver iff F(λ̂ − z·SE) ≥ 0.9 + m, with SE per link from the parity variance, or from the weighted-LS intercept covariance for `ols_reset`. Unit check (2,000 repeats): reported SE matches the empirical SD within 5% for all three estimators. One-sided 2-SE coverage is 0.96 for `ols_reset`; it is lower for `static`/`reset` exactly where their known drift bias applies. |
| Grid | est {static, reset, ols_reset} × z {1, 2, 3} × rho {0.1, 0.3, 0.5} × T {10, 30, 100, 300} s × m {0, 0.005}. D = 0.25 s. The 4 v5 combos at load 0.9 |
| Selection | Clopper–Pearson 95% upper bound on pooled dev r_cond ≤ 1%, choosing the highest dev qualified count |
| Paths | 32 dev + 32 eval, fresh seeds (18821 / 18822). Oracle run on both. **Per-path rows**, including each path's mean true F over attempts |

## Predictions, fixed before running

- **Q1 (retest of P2 after the diagnosed fix).** With the LCB controller:
  - `reset` or `ols_reset` is feasible in at least 3 of the 4 combos; **and**
  - at g = 1e-4, it beats `static` by ≥ 0.10 of the oracle in at least one cell.
- **Q2 (frontier; repeat of P1).** At g = 1e-4, the best estimator stays below 0.5 of the oracle in both cells.
- **Q3 (safety).** Every feasible eval row has a pooled r_cond ≤ 1%.
- **Q4 (exploratory, no pass/fail).** Per-path delivered fraction of the oracle, plotted against headroom (mean true F − 0.9), falls on a single curve across combos. If it does, it is the target of the scaling-law derivation; if it does not, that gets reported.

All results get reported, pass or fail.
