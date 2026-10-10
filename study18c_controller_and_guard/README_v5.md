# Study 18C v5: artifact check of the v4 queueing result (pre-registered 4 Oct 2026, before any v5 run)

This is a development run, **not** the final run. Its job is to decide whether the v4 result reflects real physics or how v4 was set up. The script is `drift_queue_des_v5.py`; it imports v4 unchanged (sha `cc954805…`).

## What v4 found (`des_v4_mac/ALL.csv`, sha `a966c00f…`)

- **Most of the oracle is lost.** Calibrated delivery reached 5–7% (ion_2020, 2 links) and 24–32% (ion_proj, 3 links) of the oracle at drift g = 1e-5, and about 0% at g = 1e-4.
- **Opportunistic calibration never worked.** It was infeasible in 12 of 12 combos.
- **Safety failed out of sample.** In 6 of 24 feasible rows, the eval-path error rate r_cond exceeded the 1% target (maximum 4.6%, on 65 deliveries).

## Why v4 might be wrong (W1–W4), and the v5 fix for each

| | Possible artifact in v4 | v5 change |
|---|---|---|
| W1 | Grid edges were binding (rho = 0.1 maximum, margin 0.0125 minimum). The window T was only {100, 300} s, though the docstring said {30, 100, 300}, and re-alignment happens every 200 s at g = 1e-4 | rho {0.03, 0.1, 0.3}; T {10, 30, 100, 300} s; margin {0.005, 0.0125, 0.025, 0.04, 0.06} |
| W2 | The estimator ignored the known re-alignment times and the linear drift | Estimators: `static` (v4), `reset`, `ols_reset` (unit-checked: biases g·T/2, g·(t−t_reset)/2 and ≈0 respectively, as derived) |
| W3 | Dev selection used a point estimate on 8 paths (winner's curse), and settings that delivered nothing counted as passing | `point` rule (≥ 50 dev deliveries) and `ucb` rule (Clopper–Pearson 95% upper bound ≤ 1%); 16 fresh dev paths and 16 fresh eval paths |
| W4 | The deadline of 0.25 s is tight: the oracle itself missed 10–58% | D ∈ {0.25, 1.0} s |

Policy is `fixed` only: in v4, hybrid matched fixed within 0.004, and opportunistic was always infeasible. The combos are both cells × g ∈ {1e-5, 1e-4} × load 0.9.

## Predictions, fixed before running

- **P1 (core).** At g = 1e-4 and D = 0.25, the best estimator under the `ucb` rule keeps EVAL qualified delivery **below 0.5 of the oracle in both cells**.
  - If P1 holds, the drift-limited frontier is real and the claim survives go/no-go #1.
  - If it fails, the v4 collapse was an artifact, and the paper becomes a *method* claim (drift- and reset-aware calibration).
- **P2.** At g = 1e-4, `reset` or `ols_reset` beats `static` by ≥ 0.10 of the oracle (absolute) in at least one cell.
- **P3.** Under the `ucb` rule, every feasible row has EVAL r_cond ≤ 1%. The `point` rule violates this in at least one row.
- **P4.** Raising D from 0.25 to 1.0 changes the best oracle-normalized fraction by less than 0.10 in every combo, so the deadline is not the driver.

Every prediction gets reported, pass or fail. A failed prediction is not re-run with new settings without a new, dated pre-registration.

## Outputs

`des_v5_mac/`:

- `dev_cells.csv` (resumable)
- `selection.csv`
- `eval_cells.csv`
- `SUMMARY.csv`
- `run_meta_*.json`
