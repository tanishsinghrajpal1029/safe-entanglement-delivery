# Study 18C v12: Learn-then-Test baseline vs the label-free controller (pre-registered 5 Oct 2026, before any v12 run)

**Why.** The novelty check (ledger E31) found that the controller claim (C2) stands only against a strong label-based baseline. The closest one is Learn-then-Test (LTT; arXiv 2110.01052).

**Code.**
- Simulation: `drift_queue_des_v12.py`, 12,672 tasks (`tasks_v12.jsonl` sha `ddcefe9d…`).
- Analysis, fixed now: `analyze_v12.py`, run as `python3 analyze_v12.py des_v12_psc des_v11_psc`.

**The baseline is deliberately generous.**
- It gets the true F of every delivered *dev* pair, i.e. free labels.
- It tunes a fixed-z rule by fixed-sequence testing: from z = 5 downward in steps of 0.5, H0: r_cond > 1%, binomial p-value, α = 0.05.

**Dev scenarios:**

| | Dev paths |
|---|---|
| S0 | Fresh draws from the same distribution as eval |
| S1 | Drawn with link F0 + 0.005: better paths and fewer near-misses (the shift that broke v6) |

**Eval.** v11's population A paths and seeds, unchanged, so v11's `adaptive` rows are the label-free comparator. Built-in reproducibility check: v12 eval at z = 2 must equal v11 `fixed2` path by path.

**Groups.** 10: two cells × (g ∈ {0, 1e-5} × est {static, ols_reset}, plus g = 1e-4 with ols_reset). Static at g = 1e-4 is excluded as a known bias failure.

## Predictions

- **L1 (LTT is valid without shift).** In S0, LTT eval r_cond ≤ 1% in all 10 groups.
- **L2 (LTT breaks under shift; adaptive does not).** In S1, LTT eval r_cond > 1% in at least one group, while adaptive (v11) is ≤ 1% in all 10.
- **L3 (cost of being label-free).** Where both S0-LTT and adaptive are safe, adaptive's qualified count is ≥ 0.8 × LTT's in ≥ 50% of groups.

**What it means.** If L2 passes, the paper can say the label-free controller is robust to population shift where the label-based gold standard is not. If L2 fails, LTT is a safe alternative, and the claim weakens to "label-free at a cost of X".

**PSC budget.** About 30–40 SU (v11-like runs cost about 9.5 core-seconds each). Ceiling 12 × 16 cores × 0.5 h = 96 SU.
