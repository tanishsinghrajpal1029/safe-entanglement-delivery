# Study 18C v10: frontier map on PSC (pre-registered 5 Oct 2026, before any v10 run)

**Code and runner.** `drift_queue_des_v10.py`, run through `psc_array_runner.py` and `s18c_array.sbatch`.

**What it is.** A descriptive map across 3 presets × L {1, 2, 3, 4} × g {1e-6, 1e-5, 1e-4} × rho {0.1, 0.3} × q {0.001, 0.01, 0.03} × method {fixed3, adaptive}, with 32 random paths per cell. That is 13,824 path-runs, each paired with an oracle run on the same path and seed. The estimator is `ols_reset`, which has no drift bias.

**PSC budget** (approved total: 400 SU):

| | SU |
|---|---|
| Hard ceiling: 20 elements × 32 cores × 0.5 h | 320 |
| Expected, from a cloud timing of ~30 core-seconds per path-run | 110–180 |

The runner is resumable, so any element killed by the time limit can be resubmitted without redoing finished runs.

## Predictions

A cell is one (preset, L, g, rho, q) combination; r_cond is pooled over its 32 paths.

- **M1 (safety at scale).** In every cell with g ≤ 1e-5 and at least 200 adaptive deliveries, adaptive pooled r_cond ≤ 1%. Fixed3 is reported alongside it.
- **M2 (readout dominates when links are good; E5 mechanism).** Going from q = 0.001 to q = 0.03 (g = 1e-6, rho 0.3, fixed3, L = 2), the relative loss of fraction-of-oracle is larger for ion_future (link p ≈ 0.013) than for ion_2020 (p ≈ 0.08).
- **M3 (monotone frontier).** In at least 80% of comparable cell pairs, fixed3's fraction-of-oracle is non-increasing in L and non-increasing in g.

**Outputs.** `des_v10_psc/shard_*.csv`, merged into `runs.csv` with `python3 psc_array_runner.py --merge des_v10_psc`.
