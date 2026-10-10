# Study 18C v14: statistically appropriate baselines (pre-registered 5 Oct 2026, before any v14 run)

**Why.** The external critique asked for a statistically appropriate baseline. In the final run, Learn-then-Test pooled every dev delivery as if independent. Deliveries cluster by path, which plausibly explains its in-distribution failure (F4).

**What v14 adds:**

- **Cluster-aware LTT.** Paths are the resampling unit; path-bootstrap upper bound, B = 2000, Bonferroni over the z grid.
- **Two per-decision belief rules**, which Proposition 1 (`THEORY_NOTE.md`) predicts cannot bound conditional risk:
  - δ-quantile / belief controller at δ = 0.10 (z = 1.2816), as in Clayton et al. 2608.07163;
  - Bayesian flat-prior rule "deliver iff P_post(F < 0.9) ≤ 1%" (z = 2.3263).

**Code (sha256, first 16):**

| File | Role | sha |
|---|---|---|
| `drift_queue_des_v14.py` | Simulation; imports the frozen final-run modules unchanged | `0bfa4d38e8cebbe4` |
| `tasks_v14.jsonl` | 21,760 tasks | `3447f4626c35c637` |
| `analyze_v14.py` | Locked analysis; tested on synthetic data | `7d42f5ef70c8dc43` |

**Design:**

- Cells: ion_2020 L2 and ion_proj L3; g ∈ {0, 1e-5, 1e-4}; est ∈ {static, ols_reset}. Static at g = 1e-4 is excluded, as before. That gives 10 groups.
- 64 fresh eval paths per group (seed 18911).
- Dev paths: S0 = same distribution (18912); S1 = link F0 + 0.005 (18913).
- Eval methods: label-free adaptive (with oracle) and fixed z ∈ {0, 0.5, 1, 1.2816, 1.5, 2, 2.3263, 2.5, 3, 3.5, 4}.

## Hypotheses

| | Prediction | Bar |
|---|---|---|
| **B1** | Cluster-aware LTT is valid in-distribution | Tuned on S0: 0 eval violations (r > 1%) among groups where it delivers |
| **B2** | Under shift it can fail; the label-free rule does not | Tuned on S1: ≥ 1 violation, **and** adaptive has 0 violations among groups with ≥ 200 deliveries |
| **B3** | Per-decision belief rules do not control conditional risk (Proposition 1) | z = 1.2816 **and** z = 2.3263 each exceed 1% in ≥ 1 group with ≥ 200 deliveries |
| **B4** | Cost (descriptive) | Median adaptive / cluster-LTT-S0 qualified ratio, and the LTT abstention count |

**How results will be read:**

- **If B1 passes:** the final-run F4 failure is attributed to the inappropriate pooled test, and cluster-aware LTT becomes the paper's reference baseline.
- **If B2 fails because cluster-aware LTT does not break under this shift:** the paper states only that the label-free rule matches a properly clustered labelled method without needing labels. It claims no robustness advantage.

**PSC.** 12 elements × 16 cores × 0.5 h, so the ceiling is 96 SU; expected 40–60 SU. Used so far: 235 of 400.
