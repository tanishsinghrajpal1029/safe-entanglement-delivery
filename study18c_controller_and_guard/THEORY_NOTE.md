# Study 18C theory note: what is new, stated precisely (draft, 5 Oct 2026)

**Purpose.** Respond to the critique "establish precisely what is new". This note fixes the notation, an exact risk identity, a no-go proposition for fixed per-decision rules, the controller's assumptions, and a known-vs-new table. It becomes Sec. II–III of the manuscript.

## 1. Setting and notation

Attempt *i* produces a pair with hidden fidelity F_i. The threshold is τ (here 0.9). Define:

- **Headroom:** h_i = F_i − τ.
- **Observed statistic:** d_i = F̂_i − τ, with F̂_i the controller's point estimate.
- **Error bar:** s_i, the controller's F-space standard error.

A **per-decision rule with caution z** delivers iff d_i ≥ z·s_i (written δ_i = 1).

The quantity a user cares about is the **conditional risk**

  r = P(h < 0 | δ = 1),

the fraction of *delivered* pairs that are below threshold.

## 2. Exact risk identity (Bayes; no model assumptions)

Let:

- π₀ = P(h < 0), the base rate of sub-threshold attempts;
- α = P(δ = 1 | h < 0), the false-delivery rate;
- β = P(δ = 1 | h ≥ 0), the power.

Then

  **r = π₀ α / (π₀ α + (1 − π₀) β).**   (1)

Per-decision caution (z) controls α. The user's risk also depends on π₀ and β, which are properties of the **network state**: path mix, drift phase, hardware, load.

## 3. Headroom-histogram law (model-based form; validated)

**Assumption A1 (Gaussian common-mode error).** Within a calibration window, d = h + e with e ~ N(μ, s²), and e independent of h.

Then P(δ = 1 | h) = Φ((h + μ − z s)/s), and

  **r(z) = ∫_{h<0} Φ((h + μ − z s)/s) dP(h) / ∫ Φ((h + μ − z s)/s) dP(h).**   (2)

**Evidence for (2).** Pre-registered in v7, replicated in v8, and confirmed in the final run (ledger E23, E24, E35, F1):

- Spearman 0.961 between predicted and measured r across 609 runs;
- median |ln(meas/pred)| 0.25;
- per-attempt fit of Φ within 0.6 percentage points.

## 4. No-go proposition for fixed per-decision rules

**Proposition 1.** Fix any caution z < ∞ and error scale s > 0, and assume Gaussian errors (A1, μ = 0). For every ε ∈ (0, 1) there is a headroom distribution P, supported on any interval containing [−η, b] with η, b > 0, such that r(z) ≥ ε.

*Proof.* Take P = π₀·δ₋η + (1 − π₀)·δ_b. Then:

- α = Φ((−η − z s)/s) > 0, and β ≤ 1;
- by (1), r ≥ π₀ α / (π₀ α + 1 − π₀) → 1 as π₀ → 1;
- choosing π₀ ≥ ε / (ε + α(1 − ε)) gives r ≥ ε. ∎

**Bounded-error version.** If |e| ≤ E almost surely (any error law), then:

- any z with z s < E still admits α > 0 for η < E − z s, and the same conclusion holds;
- r = 0 for all P requires z s ≥ E, i.e. worst-case caution. Such a rule never delivers an attempt with headroom below z s − E (≥ 0), and it also loses good attempts with small positive headroom whenever their error is negative.

**Corollary 2.** No rule whose caution is fixed independently of the network state can guarantee r ≤ ε across network states, unless it is worst-case conservative. A rule that bounds r must adapt its caution to (an estimate of) the state, i.e. the base rate. This includes:

- Bayesian or belief rules of the form "deliver if P_post(F < τ) ≤ δ" (equivalent, under a flat prior, to a fixed z = Φ⁻¹(1 − δ));
- δ-quantile controllers such as Clayton et al. (arXiv 2608.07163).

These are per-decision rules and fall under Proposition 1.

**Empirical confirmation.** Fixed rules exceeded 1% in development and in the final run:

- final run: fixed z = 2 exceeded 1% in 5 groups, up to 27.8% (F3);
- v11: fixed z = 3 exceeded 1% in 3 groups with honest error bars;
- the next run tests z = 1.28 (Clayton's δ = 0.1) and z = 2.33 (δ = 0.01) explicitly.

## 5. Relation to local false-discovery rate

Write lfdr(d) = P(h < 0 | d). Then r = E[lfdr(d) | δ = 1]: the conditional risk is the mean local fdr among delivered attempts, the tail-area FDR of Efron.

**The label-free controller** (v9/v11) estimates this average by a plug-in over recent attempts,

  r̂(z) = mean_{i in window, d_i ≥ z s_i} Φ(−d_i/s_i),

and chooses the smallest z with r̂(z) ≤ δ. It requires at least 20 supporting attempts; otherwise it does not deliver.

## 6. Assumptions of the controller, and what happens when they fail

| # | Assumption | Status | When it fails (observed) | Planned stress test |
|---|---|---|---|---|
| A1 | Gaussian, common-mode estimator error | Validated (R1/S3: within 0.6 pp) | — | Non-depolarising memory noise; NetSquid end-to-end |
| A2 | Honest SE at small n | Required | Wald collapse after re-alignment: 6–15% risk (E27/E28) | Fixed by Agresti–Coull (E29); keep in sweep |
| A3 | Unbiased estimator (μ = 0) | Required | Static estimator under fast drift: 1.1–4.5% risk (T4, E28/E29) | Drift-rate sweep; bias term |
| A4 | Flat-prior plug-in for lfdr (Φ(−d/s)) | **Approximation**, no proof | Not observed to fail in 150+ groups | Strongly skewed headroom mixes (sweep) |
| A5 | Known re-alignment times | Used by `reset` / `ols_reset` | — | Unknown or jittered re-alignment |
| A6 | Window stationarity (recent attempts represent current state) | Approximation | — | Abrupt path switches; multi-path choice |
| A7 | Depolarising (Pauli) link and swap noise | Model choice | Pauli vs density error ≤ 0.0013 near F ≥ 0.9 (E3) | T1/T2 memory noise in NetSquid |

**Limit stated plainly.** The label-free rule has **no finite-sample guarantee**. Its safety is empirical (F2: 13/13 groups; 0 violations in every PSC run). A finite-sample version would need, for example, a concentration bound on r̂, which is left open or is the optional upgrade.

## 7. Known vs new

| Already known (cited) | New here |
|---|---|
| Base-rate / false-discovery effect; local fdr (Efron); BH; tail-area FDR | Identity (1) and Proposition 1 applied to **fidelity-threshold entanglement delivery**, where routing and purification papers treat "meets F_th" as a planning guarantee |
| Joint rather than conditional soundness in QKD and state verification (Portmann–Renner; Tomamichel–Leverrier; Pallister–Linden–Montanaro; Takeuchi–Morimae) | A **quantitative** prediction of delivered-pair risk from the headroom histogram (2), confirmed pre-registered on fresh data (F1) |
| Labelled risk control: Learn-then-Test, conformal risk control | A **label-free**, self-calibrating delivery controller that holds r ≤ 1% across path populations and three hardware generations (F2), plus its failure modes (A2, A3) |
| Per-estimate fidelity CIs (Oka et al. 2602.18011; 2409.19282); drift-aware δ-quantile control (Clayton et al. 2608.07163) | The demonstration (Prop. 1, F3) that such per-decision guarantees **do not** bound delivered-pair risk |
| Hardware-requirement maps for repeater chains (Avis et al.; Kumar et al.) | Where calibration, drift and readout limit **trustworthy** delivery (frontier at thin headroom) |
| Agresti–Coull vs Wald (textbook) | Identified as a *necessary* engineering condition for safe adaptive delivery after re-alignment (E27–E29) |
