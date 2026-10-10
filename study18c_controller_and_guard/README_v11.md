# Study 18C v11: v9 with small-sample-honest error bars (pre-registered 5 Oct 2026, before any v11 run)

**Code.** `drift_queue_des_v11.py`: the same tasks, seeds and paths as v9, with **Agresti–Coull** variances in place of the Wald variances. Run on PSC through `psc_array_runner.py`.

## Why

v9's partial results (ledger E27) show r_cond of 6.2% (adaptive) and 37.8% (fixed z = 3) for ion_2020, g = 1e-5, `ols_reset`. Diagnosis: right after a re-alignment the window holds few parities. When they are all even, the Wald variance collapses (P(all 20 even | λ = 0.92) = 0.44), so the controller is "very sure" exactly when it knows least.

**Unit check, cloud, 4,000 repeats per row.** Share of draws where the 1-sided bound λ̂ − z·SE stays at or below the true λ (ion_2020 link λ = 0.92, just after a re-alignment):

| Estimator | Window | Wald, z = 2 | Wald, z = 3 | Agresti–Coull, z = 2 | Agresti–Coull, z = 3 |
|---|---|---|---|---|---|
| reset | 0.5 s | 0.786 | 0.989 | 1.000 | 1.000 |
| ols_reset | 5 s | 0.841 | 0.921 | 0.972 | 1.000 |

## Predictions

- **U1 (T1 retest).** Adaptive pooled r_cond ≤ 1% in every group with g ≤ 1e-5 (16 groups) and in every `ols_reset` group at g = 1e-4 (4 groups).
- **U2.** Fixed z = 3 pooled r_cond ≤ 1% in the same 20 groups. v9 had 37.8% in at least one of them.
- **U3 (cost, descriptive).** The qualified-delivery fraction compared with v9, path by path. Expected to fall: in a smoke test, adaptive on ion_proj F0 0.98 delivered 16 pairs against 136 in v9.

All outcomes get reported.
