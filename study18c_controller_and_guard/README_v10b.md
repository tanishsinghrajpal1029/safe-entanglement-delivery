# Study 18C v10b: frontier map on PSC (pre-registered 5 Oct 2026, before any v10b run; supersedes v10, which never ran)

**Code.** `drift_queue_des_v10b.py`, run through `psc_array_runner.py` and `s18c_array.sbatch`.

**Controller.** RunV11 (Agresti–Coull SE; ledger E29). Three methods:
- `static:adaptive` (highest goodput; drift-biased at fast g, per E28 T4);
- `ols_reset:adaptive` (unbiased, safe in all 20 v11 groups);
- `static:fixed2` (baseline).

**Grid.** Presets ion_2020, ion_proj, ion_future × L {1, 2, 3, 4} × g {1e-6, 1e-5, 1e-4} × q {0.001, 0.01, 0.03}, with rho 0.3. 32 random paths per cell plus a matched oracle, for 10,368 path-runs (`tasks_v10b.jsonl` sha `d8be3617…`).

**PSC budget.** 20 elements × 16 cores × 0.75 h gives a 240 SU ceiling. Expected 50–110 SU: v11 used 5.7 SU for 2,160 lighter runs, and ion_future (R = 1000 Hz, L up to 4) is about 3× heavier per run.

## Predictions

A cell is one (preset, L, g, q) combination; r_cond is pooled over its 32 paths.

- **M1 (safety at scale).** Pooled r_cond ≤ 1% for `ols_reset:adaptive` in every cell with ≥ 200 deliveries (all g), and for `static:adaptive` in every such cell with g ≤ 1e-5.
- **M2 (readout dominates on good links).** For `static:adaptive`, g = 1e-6, L = 2: the relative drop in fraction-of-oracle from q = 0.001 to q = 0.03 is larger for ion_future than for ion_2020.
- **M3 (monotone frontier).** For `static:adaptive`, fraction-of-oracle is non-increasing in L (fixed preset, g, q) and in g (fixed preset, L, q) in ≥ 80% of adjacent comparable pairs.

All outcomes get reported.
