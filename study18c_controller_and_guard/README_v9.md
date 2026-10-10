# Study 18C v9: self-calibrating, base-rate-aware delivery controller (pre-registered 5 Oct 2026, before any v9 run)

The script is `drift_queue_des_v9.py`. It imports v4, v6 and v7 unchanged. This is a development run.

## Why

E22 showed that risk certified on dev paths did not transfer to fresh paths. E23 and E24 showed that r_cond equals the base-rate integral of a Gaussian per-attempt error model, replicated on fresh conditions.

The controller can therefore **predict its own conditional risk from observables**:

- For each recent attempt on a path, the observables are d = F̂ − 0.9 and the F-space 1-SE s.
- Under the common-mode error model, P(bad | d) = Φ(−d/s).
- So r̂(z) = mean of Φ(−d_i/s_i) over recent attempts with d_i ≥ z·s_i.
- The controller picks, per path and online, the smallest z with r̂(z) ≤ δ = 1%.

It needs no dev set and no oracle.

**Smoke-test fix, made before this pre-registration.** A z is admissible only if at least 20 window attempts pass it; with no admissible z, the controller does not deliver. Treating an empty set as zero risk let a sub-threshold path deliver 9 bad pairs in the smoke test.

## Design

- **Methods** on identical paths and seeds: fixed z ∈ {1, 2, 3}, and adaptive.
- **Adaptive settings:**
  - window of 500 attempts;
  - cold start z = 4 below 100 attempts;
  - z grid 0–6 in steps of 0.25.
- **Populations:**
  - **A:** 32 random paths per cell, drawn as in v6.
  - **B:** 13 fixed-F0 paths per cell, as in v7.
- **Grid:** cells ion_2020 L2 and ion_proj L3 × g {0, 1e-5, 1e-4} × est {static, ols_reset}. rho 0.3, T 100 s, load 0.9, D 0.25 s.

## Predictions

A group is one (population, cell, g, est) combination; r_cond is pooled over the group's paths.

- **T1 (risk transfers).** Adaptive r_cond ≤ 1% in **every** group with g ≤ 1e-5 (16 groups), and in every `ols_reset` group at g = 1e-4 (4 groups).
- **T2 (fixed z does not transfer).** Fixed z = 2 has r_cond > 1% in at least one of those 20 groups.
- **T3 (cost).** Among groups where both adaptive and fixed z = 3 have r_cond ≤ 1%, adaptive delivers at least as many good pairs as fixed z = 3 in ≥ 50% of groups.
- **T4 (expected limitation).** `static` at g = 1e-4: adaptive r_cond > 1% in at least one cell, because the drift bias is not in the error model. The bias needs an unbiased estimator (`ols_reset`) or an explicit bias term.

The Clopper–Pearson 95% upper bound is reported alongside every point estimate. All outcomes get reported.
