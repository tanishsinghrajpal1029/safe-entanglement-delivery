# Study 18C final confirmatory protocol (frozen 5 Oct 2026, before any final-run data exist)

**Rules.** The final run is executed **once**, on fresh seeds, with the code and analysis scripts below. No setting, hypothesis or analysis line may change after data exist. Any deviation gets reported as a deviation. Development results (v4–v12, ledger E20–E33) motivate these hypotheses; they are *not* evidence for them.

## Code (sha256, first 16 hex)

| File | Role | sha |
|---|---|---|
| `drift_queue_des_final.py` | Controller and LTT component (26,880 tasks, `tasks_final.jsonl`) | `40ee6079b18ed58c` (tasks `50fe0d1f7339f931`) |
| `analyze_final.py` | Locked analysis for F2–F5 | `2a3487c6bc68dd6b` |
| `drift_queue_des_final_law.py` | Risk-law component: v8 code, new seed tags, rho 0.2, T 60 s | Recorded in the ledger when created; generated mechanically from v8 by `make_final_law.sh` |
| `analyze_v7.py` | Locked analysis for F1 | `c9f06b92ae6bcb91` |
| Imported, unchanged | drift_queue_des.py `cc954805`, v6 `3dac7de5`, v9 `788ec1aa`, v11 `cc2e53c2`, v12 `b982b2b7` | — |

## Design

**Controller component.**
- Cells: ion_2020 L2, ion_proj L3, ion_future L4 (purification on). g ∈ {0, 1e-5, 1e-4}; est ∈ {static, ols_reset}. **Static at g = 1e-4 is excluded**, because its drift-bias failure is pre-declared. That leaves 15 groups.
- **Eval:** 64 fresh random paths per group (seed tag 18901), run under `adaptive` (with matched oracle) and fixed z ∈ {0, 0.5, …, 4}.
- **Dev, for Learn-then-Test:** 64 labelled paths per group. S0 = same distribution (18902); S1 = link F0 + 0.005 (18903). LTT is Bonferroni over the 9-point z grid: δ = 1%, α = 0.05/9, binomial test on pooled dev deliveries; choose the smallest rejected z, else abstain.

**Risk-law component.** The v8 design (single-path controlled-headroom sweep, 1,872 runs), with new seed tags and new conditions (rho 0.2, T 60 s).

**Fixed parameters.** rho 0.3 (controller component), T 100 s, load 0.9, D 0.25 s, horizon 300 s + 300 s warm-up, q 0.001, δ = 1%.

## Hypotheses

**Primary: F1 and F2.**

- **F1 (risk law).** Conditional risk is predicted by integrating the Gaussian per-attempt error model over each run's attempt-headroom histogram. On the risk-law component, using `analyze_v7.py`:
  - the `R2` line gives Spearman ≥ 0.9 **and** median |ln(meas/pred)| ≤ ln 1.5 (runs with ≥ 100 deliveries, z ≥ 1, bad > 0);
  - the `R1` statistic is ≤ 0.05.
- **F2 (label-free safety).** `adaptive` has pooled r_cond ≤ 1% in **every** group with ≥ 200 deliveries, **and** the Clopper–Pearson 95% upper bound on r_cond pooled over all adaptive eval deliveries is ≤ 1%.

**Supporting: F3–F5.**

- **F3 (fixed per-decision confidence does not control conditional risk).** Fixed z = 2 has r_cond > 1% in at least one group with ≥ 200 deliveries.
- **F4 (label-based tuning is valid in-distribution but not under shift).** LTT tuned on S0 has 0 eval violations; LTT tuned on S1 has at least 1 eval violation (r_cond > 1%) among groups where it delivers.
- **F5 (cost; descriptive).** The median ratio of adaptive to LTT-S0 qualified deliveries, over groups where LTT-S0 delivers. Plus the LTT abstention count and adaptive fraction-of-oracle with path-bootstrap 95% CIs.

## Interpretation fixed in advance

| Outcome | What the paper claims |
|---|---|
| F1 **and** F2 pass | Both core claims are confirmed |
| F1 or F2 fails | That claim is dropped or restated as a limitation; no re-run is allowed to rescue it |
| F4 fails | The paper does **not** claim shift-robustness over LTT; it reports the label-free / label-based trade-off only |

## PSC budget

Expected 110–170 SU. Ceiling 220 SU: controller component 24 × 16 cores × 0.5 h = 192, plus the risk-law job 1 × 32 cores × 0.75 h = 24. Used before the final run: about 97 of the 400 approved.
