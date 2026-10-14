# Study 36 ("Oxford"): results (14 Oct 2026)

**Reporting permitted** by D. P. Nadlinger (E166), who also confirmed that the export contains every heralded event. The results are sent to the authors before any submission.

## Provenance
- **Pre-registration:** `PREREG_36.md` (sha 216cfed4d2e8be8f), committed and pushed as `d4d4a9d` at 01:32:45 UTC.
- **Run:** the locked `analyze_36.py` (aa8001b58560851d) with `oxford_core.py` (0ab19cc02e82ad96), started at **01:35:26 UTC**, 2 min 41 s after the commit. The run was done once, on `link-quality-events.csv.xz` (sha fae103d8bfdb179b).
- **Output:** `results_36.txt`.
- **Data:** shot-by-shot events of the 1,920,000-round characterisation run of Nadlinger et al., Nature 607, 682 (2022), Fig. 3 / Fig. S4. Shared privately.

## Gates: both PASS
- **G1:** 1,920,000 rows; test fraction 0.5080; every key round has x = 0; time-ordered; test settings 0.2495–0.2506 each.
- **G2:** exactly one of the 8 CHSH conventions reproduces the paper: minus sign on (x, y) = (1, 1) with Alice's outcomes inverted gives **S = 2.6768** (published 2.677(6)). The next-largest candidate is |S| = 0.048. Key-round **QBER 1.439%** (published 1.44(2)%).

## Verdicts: primary 2/2 PASS; secondary S1 PASS, S3 FAIL

| | Tier | Result | Numbers |
|---|---|---|---|
| **O1** | primary | **PASS** | **Anytime certificate on the kept (key) pairs, from real randomised test-or-keep data:** final **F_L = 0.917** (95%, valid at all times; bar > 0.9) over 944,576 kept pairs. It first exceeds 0.9 after 217,893 kept pairs and stays above 0.9 at all times after 219,185 (descriptive, `explore_36_b.py`). A union over all 8 CHSH conventions gives 0.914 (descriptive). Point estimate √2(1−2q) = 0.946. |
| **O2** | primary | **PASS** | **The link fluctuates beyond binomial noise:** χ² = 143.1 (df 95), p = 0.001, dispersion ratio 1.51, **excess relative fluctuation 1.6%** of the CHSH loss rate (mean 0.165; chunks 0.151–0.178) |
| S1 | secondary (prediction) | PASS | **Consistency:** the certificate never exceeded the upper value implied by the kept pairs' own Z errors (0 violations; final 0.993) |
| S2 | descriptive | — | **Device-independent (self-testing) bound on the kept pairs:** F_ext ≥ 0.837 |
| S3 | secondary (prediction) | **FAIL** | **No persistence:** lag-1 autocorrelation of the chunk rates is −0.17 (permutation p = 0.95). The fluctuations do not carry over from one chunk to the next. |
| S4 | descriptive | — | **QBER dispersion:** χ² = 117.6, p = 0.058, ratio 1.24 |

## Deviation found at run time (disclosed; does not change any verdict)
- **The test fraction is not exactly 1/2.**
  - Observed 0.50803 ± 0.00036, which is 22 standard errors above 1/2 and consistent with **130/256 = 0.50781**. That would be an 8-bit random draw, as used for γ = 13/256 in the paper's key run. This is an inference, to be confirmed with the authors.
- **Why the bound stays valid:** the pre-registered p = 1/2 is below the true p. The martingale increment with p = 1/2 then exceeds the one with the true p by (p′ − p)[T_iL_i + (1 − T_i)q_i] ≥ 0. So the pre-registered bound remains **valid but conservative**.
- **Exploratory recomputation** with p = 130/256 (`explore_36_ptrue.py`, not pre-registered):
  - F_L = **0.932**, above 0.9 at all times after 68,129 kept pairs (valid only if every round's test probability is at least 130/256);
  - DI F_ext ≥ 0.867.

## Reading
1. **First real-data run of the anytime certificate under its own assumptions.**
   - The pairs were delivered and the test-or-keep choice was made by a quantum random number generator after the herald.
   - The certificate certified the **kept** pairs above the manuscript's threshold of 0.9 at every moment after about 219,000 kept pairs. That is about 68,000 with p = 130/256.
   - This is consistent with the cost analysis: at p ≈ 1/2 and fidelity about 0.95, certifying 0.9 needs tens of thousands to hundreds of thousands of pairs, because the CHSH test has a loss of 0.146 even on a perfect pair. That is far more than the Pauli test of Prop. C1 needs.
2. **Real link noise is over-dispersed but small and not persistent.**
   - The excess is 1.6% relative on the loss rate.
   - There is no lag-1 persistence; the autocorrelation is negative, consistent with recalibration between chunks.
   - The persistent noise (AR ρ = 0.9) that broke every model-based arm in S26 is **not** seen on this link. The over-dispersion is of the kind a declared dispersion φ handles (S26).
3. **A trusted readout matters, but here it is good.** Readout error is below 10⁻³ (paper). The trusted bound (0.917) and the device-independent bound (0.837) bracket what can be claimed without, and with, trust in the measurements.

## Scoreboard
- **Primary:** +2 (O1 PASS, O2 PASS). Project total **89 primary: 78 PASS, 11 FAIL**.
- **Secondary:** +2 (S1 PASS, S3 FAIL). Total **56: 48 passed or confirmed, 7 failed, 1 unclear**.
