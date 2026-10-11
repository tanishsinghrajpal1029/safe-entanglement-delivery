# Weakness review after Study 25 (11 Oct 2026)

This is a skeptical referee-style pass over the paper as it stands after Studies 23–25, the ICFO/USTC checks and theory note v4. Items are ranked by how likely each is to sink a PRX Quantum submission.

## Critical

### 1. Our own real data sits in the regime where Study 25 shows the guard breaks
- USTC shows error-rate dispersion of about 3.6 (φ ≈ 3.6, i.e. c ≈ 1.6), and the USTC model is 2–4 fidelity points optimistic.
- ICFO: 7 of 11 runs are over-dispersed.
- Study 25 shows that undeclared optimism (M2) and strong shared noise (c = 2) break every undeclared guard. Declaring φ restores safety, but SiV falls to about 1% of oracle.
- c ≈ 1.6 was never tested; Study 25 tested c = 0, 0.5 and 2.
- **Caveat:** the USTC set sizes are unknown, which could inflate the dispersion, and the mapping from per-set dispersion to our per-epoch c is approximate.
- **Fix:** Study 26, "data-calibrated realism". Set D and φ from the ICFO/USTC estimates, with uncertainty, and run c ∈ {1, 1.6} plus per-link φ.

### 2. The guarantee rests on operator declarations (D, φ, B) that cannot be checked online
- The fault-exposure no-go (Prop. 8) also cuts against us.
- The earlier novelty framing said rivals' fidelity guarantees are "tautological under model mismatch". M2 shows ours also fails under undeclared mismatch.
- **Fix:** narrow the claim. The guard controls *statistical* uncertainty from heralded counts, given a declared-pessimistic model. Add a recipe that estimates D, φ and B from calibration data with confidence, demonstrated on ICFO/USTC.

### 3. Venue fit and novelty for PRX Quantum
- The mathematical tools are known: Ville, mixture confidence sequences, quasi-likelihood.
- Most of the routing literature sits at IEEE QCE/TQE.
- PRX Quantum referees may call the work an applied-statistics engineering contribution.
- **Fix:**
  - lead with the physics-facing content: a per-user delivered-pair guarantee, real-hardware drift evidence, and the no-go;
  - cut the scope;
  - pick a backup venue now: npj QI, Quantum or IEEE TQE.

## Major

### 4. Baselines from the literature
- The guard-era studies (G1–G7, 23–25) compare against our own variants: cal, bg, kg, gexact and gpersist.
- Comparisons with Q-GUARD/EFiRAP-style or DeltaPurify-style rules at matched realised risk were planned (NOVELTY_MATRIX, PROTOCOL_DRAFT). They appear only in the older oracle-decision studies.
- **To verify, then fix:** add a matched-risk comparison with at least one published rule.

### 5. The AI/RL contribution is modest
- Learning adds less than 0.5 points on ions.
- A linear model captures most of the gain; RL adds +0.34.
- T3 failed, through the time-split variant.
- The big thin-hardware gain comes mostly from pooling a prior, not from the "AI".
- **Fix:** frame the learned prior as an optional, safe add-on. Present the linear prior as a strong baseline. Keep RL out of the abstract.

### 6. Simulation scope
- A 5 × 5 grid with greedy routing.
- PTM/Werner-type physics.
- No memory-slot limits, multiplexing or cutoff policies.
- Parallel service arrived only in Study 25.
- **Fix:** state these limits plainly. An optional NetSquid cross-check already exists for the physics.

### 7. The real-data checks are partial and offline
- ICFO: the primary visibility estimator failed.
- Innsbruck Stage 2: event-count mismatch (581 vs 491).
- No Delft data; no closed-loop or live test.
- **Fix:** report the checks as falsification tests of the model and assumptions, not as validation; this ties to item 1.

## Moderate

### 8. Multiplicity across the whole programme
- The programme has about 25 studies, plus pilots and many hypotheses.
- Each study was pre-registered, but the paper's narrative selects among them.
- **Fix:** add an appendix scoreboard of every confirmatory hypothesis ever tested and its pass/fail, generated from the ledger.

### 9. The proofs have not been checked by an outside expert
- Props. 9–10 are close to design rules or elementary.
- **Fix:** label each proposition honestly (theorem / lemma / design rule), and give the theory note to a statistician or Prof. Mike for checking.

### 10. Provenance optics
- Heavy AI assistance, a single developer, and a thin timing margin on Study 25 Block A: public at most 28 s before the first output.
- **Fix:** keep the disclosure, deposit the full audit trail (done), and state the timing exactly.

### 11. The manuscript is not written, and the story sprawls
- 10 propositions and 25 studies.
- **Fix:** 3 claims, 4 figures, everything else in the supplement.
