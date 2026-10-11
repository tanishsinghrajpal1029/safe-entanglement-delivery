# Pre-registered hypothesis scoreboard (quantum-network delivery programme)

Built 2026-10-10/11 for the paper *Safe entanglement delivery: label-free risk control and an anytime-valid per-user guard for quantum networks*. Machine-readable copy: `scoreboard.csv`.

## How this was built

- **Source of truth:** `prx_work/18_audit_independent/EVIDENCE_LEDGER.md`, entries E1–E105 (1,802 lines), read in full. Every row cites the ledger entries where the hypothesis was registered and where its verdict was recorded.
- **Gap filling (secondary sources):** where the ledger names a hypothesis but not its tier or bar, the project's pre-registration notes (`claude/*_PREREG_*.md`, `claude/*_RESULTS_*.md`) were used. This is said in the `notes` column. Studies 13 and 14 do **not** appear in the ledger. Their rows come from `VERDICT_15b_2026-10-02.md`, `CORRECTIONS_15b_2026-10-02.md` and `AUDIT_REPORT_2026-10-03.md`, and are marked `not in ledger`.
- **Outcomes** are the ledger's own words (PASS, FAIL, CONFIRMED, NOT CONFIRMED, REPLICATED, YES, NOT MET, …). No outcome was upgraded. Qualifiers such as "narrowly", "barely" or "as specified" are kept in `notes`. Where the ledger gives no verdict word, or two verdicts for one ID, the row is `UNCLEAR` or split, and the reason is quoted.
- **Tiers:** `primary` / `secondary` only when a pre-registration labels them that way ("supporting" counts as secondary). `unlabelled` = registered with a pass bar but no tier label; the pre-registration's own label ("stricter", "prediction", "mechanism") is kept in `notes`. `validation` = a check with criteria fixed before running. `gate` = a pre-set analysis or stop gate. `descriptive`, `exploratory` and `open` (a registered question with no bar) are listed but **not counted** as confirmatory tests.
- **Excluded:** exploratory model studies (E5, E10, E11, E15, E17), the v4 DES (E20, labelled PROVISIONAL, with no pre-registration), the E19 pilot, the E46 parity-calibration check (no bar was set in advance), and all dev pilots. The pilots are listed at the end.
- **Not found anywhere:** pre-registered hypotheses for Studies 15b (an audit of 08–14, not a study with its own hypotheses), 16, 18 and 19 (the other agent's line; PRX_READINESS_2026-10-04 says it has "no pre-registration"), 20 and 21. If the request's "16–20" meant v16–v20, those are included.

## Summary counts


**All registered tests with a bar (confirmatory + validation + gates), ledger and pre-ledger together**

| Tier | PASS | CONFIRMED | REPLICATED | YES | FAIL | NOT MET | NOT CONFIRMED | NOT RUN | NOT COUNTED | UNCLEAR | Total |
|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | 33 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 | 0 | 40 |
| secondary | 13 | 2 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 1 | 20 |
| unlabelled | 37 | 10 | 3 | 1 | 19 | 1 | 2 | 1 | 0 | 3 | 77 |
| UNCLEAR | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 3 |
| validation | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| gate | 3 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 5 |
| **all** | **92** | **13** | **3** | **1** | **31** | **1** | **2** | **1** | **1** | **5** | **150** |


**Confirmatory hypotheses, ledger only (excludes Studies 13/14, validation checks and gates)**

| Tier | PASS | CONFIRMED | REPLICATED | YES | FAIL | NOT CONFIRMED | NOT RUN | UNCLEAR | Total |
|---|---|---|---|---|---|---|---|---|---|
| primary | 33 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 40 |
| secondary | 13 | 2 | 0 | 0 | 4 | 0 | 0 | 1 | 20 |
| unlabelled | 36 | 10 | 3 | 1 | 19 | 2 | 1 | 1 | 73 |
| UNCLEAR | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 3 |
| **all** | **83** | **13** | **3** | **1** | **30** | **2** | **1** | **3** | **136** |


Other items listed but not counted as tests: descriptive 23, exploratory 2, open (no bar) 2.

**Primary hypotheses only (ledger):** PASS 33, FAIL 7 (total 40).


**Per study** (confirmatory rows: primary + secondary + unlabelled + UNCLEAR-tier; validation and gate rows in brackets)

| Study | Tests | PASS-type (PASS/CONFIRMED/REPLICATED/YES) | FAIL / NOT MET / NOT CONFIRMED | Other (UNCLEAR, NOT RUN, NOT COUNTED) | Ledger |
|---|---|---|---|---|---|
| 13 | 2 | 1 | 1 | 0 | not in ledger |
| 14 | 2 | 0 | 0 | 2 | not in ledger |
| 17 | 4 | 3 | 1 | 0 | E1 |
| NetSquid surrogate check (18c) | 0 [+3] | 3 | 0 | 0 | E13, E14 |
| NetSquid T1/T2 check (A) | 0 [+2] | 2 | 0 | 0 | E48 |
| v5 | 5 | 3 | 2 | 0 | E20, E21 |
| v6 | 4 | 1 | 2 | 1 | E21, E22 |
| v7 | 3 | 2 | 1 | 0 | E22, E23 |
| v8 | 3 | 3 | 0 | 0 | E24 |
| v9 | 4 | 3 | 1 | 0 | E25, E27, E28 |
| v11 | 5 | 3 | 1 | 1 | E27, E29 |
| v10b | 3 | 1 | 2 | 0 | E26, E29, E30 |
| v12 | 3 | 2 | 1 | 0 | E32, E33 |
| FINAL (18C) | 4 | 3 | 1 | 0 | E34, E35 |
| v14 | 3 | 2 | 1 | 0 | E36, E37, E62 |
| v15 | 3 | 2 | 1 | 0 | E38, E39 |
| v16 | 5 | 5 | 0 | 0 | E40, E41 |
| v17 | 5 | 5 | 0 | 0 | E42, E43 |
| v18 | 2 | 2 | 0 | 0 | E44, E45 |
| v19 | 4 | 4 | 0 | 0 | E47, E49 |
| v20 | 4 | 4 | 0 | 0 | E50, E51 |
| C1 | 3 | 0 | 3 | 0 | E53, E54 |
| C2 | 4 | 1 | 3 | 0 | E55, E56, E62 |
| P1 | 2 | 1 | 1 | 0 | E58, E59, E62 |
| Innsbruck Stage 1 | 0 [+2] | 1 | 0 | 1 | E61, E62 |
| Innsbruck Stage 2 | 1 [+1] | 0 | 1 | 1 | E63 |
| G1 | 4 | 0 | 4 | 0 | E65, E66, E67 |
| G2 | 3 | 3 | 0 | 0 | E68, E69 |
| S1 | 2 | 2 | 0 | 0 | E68, E70 |
| G3 | 4 | 4 | 0 | 0 | E72, E73 |
| G4 | 3 | 3 | 0 | 0 | E75, E76 |
| G5 | 4 | 4 | 0 | 0 | E77, E78 |
| G6 | 4 | 2 | 2 | 0 | E80, E81 |
| G7 | 5 | 4 | 1 | 0 | E82, E83 |
| 23 | 5 [+2] | 7 | 0 | 0 | E84, E85, E86 |
| 24 | 10 | 10 | 0 | 0 | E88, E89 |
| ICFO Stage 1 | 4 | 1 | 3 | 0 | E90, E91, E92, E95 |
| USTC Stage 1 | 2 | 1 | 0 | 1 | E96, E97 |
| 25 | 12 | 11 | 1 | 0 | E101, E103 |

## Full table

| Study | ID | Tier | Question | Outcome | Key number | Ledger | Notes |
|---|---|---|---|---|---|---|---|
| 13 | E1 | unlabelled | adaptive_4 beats retry_4 on acceptance (30x30 cal20)? | PASS | +4.12 [3.76, 4.48] | not in ledger | Source: project docs VERDICT_15b_2026-10-02 / CORRECTIONS_15b / AUDIT_REPORT_2026-10-03 (study attribution from AUDIT_REPORT table). Outside the ledger. |
| 13 | E2 | unlabelled | Registered E2 comparison (acceptance lower bound > -1.0) | **NOT MET** | acceptance -1.18 [-1.64, -0.72]; pairs -1.084 | not in ledger | Source: VERDICT_15b / CORRECTIONS_15b ('lower bound < -1.0, so NOT MET as registered'). Exact wording of the E2 hypothesis not in available docs. |
| 14 | R1 | unlabelled | Registered robustness check R1 (per condition) | UNCLEAR | 6/6 conditions | not in ledger | Source: VERDICT_15b item 2 ('R1: 6/6') and AUDIT_REPORT ('14 \| R1 / R2 per condition'). No verdict word recorded; hypothesis text not available. |
| 14 | R2 | unlabelled | Registered robustness check R2 (per condition) | UNCLEAR | 7/7 conditions | not in ledger | Source: VERDICT_15b item 2 ('R2: 7/7'). No verdict word recorded; hypothesis text not available. |
| 17 | F1 | unlabelled | adaptive_4 - retry_4 acceptance gain > 0 (30x30 cal20, 5 fresh topologies) | PASS | +4.38 [3.63, 5.13] | E1 | Verdict word from E1 header region and STUDY17_VERIFIED_RESULTS ('Registered verdict'). |
| 17 | F2 | unlabelled | adaptive_4 - verified single acceptance gain > 0 | PASS | +12.58 [10.95, 14.21] | E1 |  |
| 17 | F3 | unlabelled | r_cond upper bound <= 2% for adaptive_4 and verified single | PASS | upper bounds 0.988% and 0.955% | E1 | Bar (<=2%) from STUDY17_VERIFIED_RESULTS. |
| 17 | F4 | unlabelled | stop vs adaptive_4 (acceptance bound) | **FAIL** | -1.04 [-1.27, -0.81] | E1 | FAIL on acceptance bound. Descriptive: cal30 6.25% bad. |
| NetSquid surrogate check (18c) | swap-chains | validation | Swap chains vs closed form, max error < 1e-9 | PASS | max error 4.4e-16 (60 cases) | E13, E14 | Criteria fixed in README before running (E13). |
| NetSquid surrogate check (18c) | DEJMPS-prob | validation | DEJMPS success probability within 4 SE | PASS | max \|z\| = 2.55 | E14 |  |
| NetSquid surrogate check (18c) | DEJMPS-fid | validation | DEJMPS fidelity vs exact NumPy circuit < 0.003 | PASS | max error 4.4e-14 | E14 | Also confirmed E13: old gate shortcut optimistic by 0.0037-0.0078. |
| NetSquid T1/T2 check (A) | Part1-channel | validation | Exact T1/T2 channel vs NetSquid, max \|DM diff\| < 1e-9 | PASS | 2.2e-16 over 8 cases | E48 | 'pre-set < 1e-9'. v1 crashed before physics (T1=0 rejected); v2 used. |
| NetSquid T1/T2 check (A) | Part2-e2e | validation | End-to-end delivered-pair protocol within 4 SE + 1e-4 | PASS | 24/24 cases; max \|diff\| 8e-5 | E48 | Ledger does not state explicitly that the Part 2 tolerance was pre-set (Part 1 is stated as pre-set). |
| v5 | P1 | unlabelled | At g=1e-4 best ucb rule < 0.5 of oracle (frontier survives) | PASS | 0.146 (ion_2020), 0.012 (ion_proj) | E20, E21 | Caveat: best rho at grid edge (0.3). |
| v5 | P2 | unlabelled | reset/ols_reset beat static by >= 0.10 | **FAIL** | infeasible at g=1e-4; reset +0.066 at g=1e-5 (ion_proj) | E21 |  |
| v5 | P3a | unlabelled | Under ucb, no eval row exceeds 1% | PASS | 0 of 21 eval rows > 1% | E21 | Ledger gives P3 two verdicts without a single header verdict; split here into P3a/P3b. |
| v5 | P3b | unlabelled | The point rule violates 1% on eval | **FAIL** | point rule (>= 50 deliveries) was also safe | E21 | See P3a. |
| v5 | P4 | unlabelled | Deadline D 0.25 -> 1.0 s changes results little | PASS | max change 0.011 | E21 |  |
| v6 | Q1 | unlabelled | Smarter estimators gain over static at g=1e-4 (wording inferred) | **FAIL** | gain <= 0.012 | E21, E22 |  |
| v6 | Q2 | unlabelled | Best fraction of oracle at g=1e-4 is low (wording inferred) | PASS | 0.018 (ion_2020), 0.065 (ion_proj) | E22 |  |
| v6 | Q3 | unlabelled | Dev-certified (CP-UCB <= 1%) risk transfers to fresh eval paths | **FAIL** | 6 of 11 feasible eval rows > 1% (max 6.0%) | E22 |  |
| v6 | Q4 | unlabelled | Fraction monotone in headroom; collapse without normalisation | UNCLEAR | monotone in headroom; no collapse without normalisation | E22 | Ledger records 'Q4 partial' - not a pass/fail word. |
| v7 | R1 | unlabelled | Gaussian per-attempt model P(deliver\|h) fits | PASS | median per-run max deviation 0.0026 (g<=1e-5); 0.176 static at g=1e-4 | E22, E23 |  |
| v7 | R2 | unlabelled | r_cond predicted from headroom histogram (Spearman >= 0.9; median \|ln ratio\| <= 0.405) | PASS | Spearman 0.916; median \|ln ratio\| 0.374 (534 runs) | E23 | Ledger: 'PASS (narrowly)'. 0.5-corrected all-runs value 0.638 reported as sensitivity (not pre-specified). |
| v7 | R3 | unlabelled | F0 is a monotone proxy for base rate (series tau <= -0.6) | **FAIL** | 28% of 36 series have tau <= -0.6 | E23 | kappa found exploratorily afterwards. |
| v8 | S1 | unlabelled | Risk law replicates on fresh conditions | PASS | 745 runs, Spearman 0.987, median \|ln ratio\| 0.228 | E24 |  |
| v8 | S2 | unlabelled | kappa orders power/risk (monotone across 5 bins) | PASS | median power never rises, r_cond never falls (z=1,2) | E24 | Limit: kappa is ordering only; closed-form kappa*G(a) fails (Spearman 0.36). |
| v8 | S3 | unlabelled | Gaussian per-attempt model fits (max dev <= 0.05) | PASS | median per-run max deviation 0.017 | E24 |  |
| v9 | T1 | unlabelled | Self-calibrating adaptive r_cond <= 1% in all 20 target groups | **FAIL** | 3 of 20 groups > 1% (6.2%, 14.6%, 1.5%; ion_2020 ols_reset) | E25, E27, E28 | Wald-SE collapse; fix (v11) pre-registered after seeing v9 partial results (E27). |
| v9 | T2 | unlabelled | Fixed z=2 violates 1% | PASS | violates in 7 of 20 groups | E28 |  |
| v9 | T3 | unlabelled | Adaptive delivers >= fixed z=3 where both safe | PASS | 15 of 15 groups | E28 |  |
| v9 | T4 | unlabelled | Expected limitation: static at g=1e-4 exceeds 1% | CONFIRMED | 1.1-4.3% in 4 of 4 groups | E28 |  |
| v11 | U1 | unlabelled | Agresti-Coull adaptive r_cond <= 1% in all 20 groups | PASS | 20/20; max 0.725% | E27, E29 |  |
| v11 | U2 | unlabelled | Fixed z=3 safe with honest SE | **FAIL** | violates in 3 groups (5.6%, 20%, 1.66%; small counts) | E29 | Exact U2 wording not in ledger; inferred from E29 text. |
| v11 | U3 | UNCLEAR | Pre-registered (E27: 'predictions U1-U3') but not reported by name | UNCLEAR | - | E27, E29 | E29 reports U1, U2, T3, T4 but no U3. Possibly T3 below; cannot be determined from ledger. |
| v11 | T3 (v11) | UNCLEAR | Adaptive >= fixed z=3 where both safe (re-test) | PASS | 17 of 17 groups | E29 | Reported in E29 header; whether pre-registered for v11 is UNCLEAR. |
| v11 | T4 (v11) | UNCLEAR | Static at g=1e-4 exceeds 1% (expected) | CONFIRMED | 1.2-4.5% | E29 | Ledger: 'T4 (expected) CONFIRMED again'; v11 pre-registration status UNCLEAR. |
| v10b | M1 | unlabelled | Adaptive pooled r_cond <= 1% in all checked cells | PASS | 118/118 cells | E26, E29, E30 | v10 (Wald) cancelled after a ~0.3 SU test shard; re-specified as v10b. |
| v10b | M2 | unlabelled | Readout error q matters most where links are best | **FAIL** | opposite direction: ion_future 0.578 -> 0.578; ion_2020 L2 -97% | E30 |  |
| v10b | M3 | unlabelled | UNCLEAR: M3 definition not in ledger (a 0.80 bar; failures are 'noise-level rises in flat regions') | **FAIL** | 0.78 vs 0.80 bar | E30 | Ledger: 'FAIL (narrowly)'. Exact M3 definition not in ledger. |
| v12 | L1 | unlabelled | LTT (S0, iid labels) eval r_cond <= 1% | PASS | 10 of 10 groups (LTT abstained in 8 of 10) | E32, E33 |  |
| v12 | L2 | unlabelled | Under S1 shift LTT violates while adaptive does not | PASS | LTT violates 1 group (1.51%); adaptive 10/10 <= 1% | E33 |  |
| v12 | L3 | unlabelled | Adaptive goodput >= LTT where both deliver | **FAIL** | 0.59x and 0.70x of LTT (2 groups) | E33 |  |
| FINAL (18C) | F1 | primary | Risk law (histogram integral) predicts r_cond | PASS | Spearman 0.961; median \|ln ratio\| 0.252; R1 stat 0.0059 | E34, E35 |  |
| FINAL (18C) | F2 | primary | Label-free adaptive r_cond <= 1% in every group (>= 200 deliveries) | PASS | 13/13 groups; pooled 0.0081% | E34, E35 | Two ion_2020 groups near bar: 2/512 (CP upper 1.22%), 2/208 (CP upper 3.0%). |
| FINAL (18C) | F3 | secondary | Fixed z rule fails | PASS | z=2 > 1% in 5 groups (up to 27.8%) | E34, E35 | Ledger label: 'supporting'. |
| FINAL (18C) | F4 | secondary | LTT valid iid (0 S0 violations), breaks under shift | **FAIL** | LTT-S0 violated 1 group (5.85%); LTT-S1 4 | E34, E35 | Ledger: 'FAIL (as specified)'; per protocol no shift-robustness claim over LTT. Ledger label: 'supporting'. |
| FINAL (18C) | F5 | descriptive | Cost vs LTT | DESCRIPTIVE | median adaptive/LTT-S0 0.723 (11 groups) | E35 |  |
| v14 | B1 | unlabelled | Cluster-aware LTT (S0) <= 1% in every delivering group | **FAIL** | 1 of 8 groups: 9 pairs, 1 bad (11%) | E36, E37 | No minimum-delivery clause, so counts as fail. |
| v14 | B2 | unlabelled | Under S1 shift cluster-LTT violates, label-free adaptive does not | PASS | cluster-LTT 4 violations; adaptive 0 of 9 (max 0.142%) | E37, E62 | E62 correction: the 0/9 label-free result was the earlier Gaussian controller, not the EB controller. |
| v14 | B3 | unlabelled | Per-decision belief rules (delta-quantile, Bayesian flat) violate (Prop. 1) | PASS | delta=0.10 rule > 1% in 8 groups; Bayesian flat in 3 | E37 |  |
| v14 | B4 | descriptive | Cost vs cluster-LTT | DESCRIPTIVE | median ratio 0.663 (8 groups) | E37 |  |
| v15 | G1 | unlabelled | Adaptive <= 1% across generality/stress variants | **FAIL** | 4 of 32 groups > 1%, all NV-like (1.40-8.3%) | E38, E39 | v16 designed post hoc; E40 states G1 stays FAIL. |
| v15 | G2 | unlabelled | Expected limitation: optimistic memory model exceeds 1% | CONFIRMED | static adaptive 1.68%, 2.01% | E39 |  |
| v15 | G3 | unlabelled | Fixed z=2 exceeds 1% | PASS | 3 variants (up to 14.8%) | E39 |  |
| v15 | G4 | descriptive | Throughput by variant | DESCRIPTIVE | tau 0.85: 0.80 / 0.65 of oracle | E39 |  |
| v16 | H1 | primary | pop (calibrated posterior) r <= 1% in every group | PASS | 8/8; max 0.80% (8/1001) | E40, E41 | Fragile: path-bootstrap upper bound 2.04% in ion-2020 tau0.9 cell; v17 V4 re-test 0.10%/0.13% (E43). |
| v16 | H2 | unlabelled | Jeffreys exact alone exceeds 1% in >= 1 NV group | CONFIRMED | 1.89%, 1.49% | E41 |  |
| v16 | H3 | unlabelled | Gaussian adaptive replicates NV failure | REPLICATED | ols 5.63%, 5.78% | E41 |  |
| v16 | H4 | unlabelled | pop >= 0.8x Gaussian qualified in ion cells | PASS | 1.05x-1.81x | E41 |  |
| v16 | H5 | unlabelled | popopt exceeds 1% in >= 1 group | CONFIRMED | 3 of 8 groups | E41 | popwide (descriptive) also violated 1 group (1.22%). |
| v17 | V1 | primary | eb128 and eb32x10 r <= 1% in every group | PASS | 16/16; max 0.40% | E42, E43 |  |
| v17 | V2 | unlabelled | Path-bootstrap 95% upper bound <= 1% | PASS | <= 0.49% all 16 | E43 | Prereg label 'stricter'. |
| v17 | V3 | unlabelled | Small fleets (eb8/eb32) break on NV | CONFIRMED | eb8 1.39%, 1.32%; eb32 1.01% | E43 |  |
| v17 | V4 | unlabelled | pop replicates (<= 1% every group) | REPLICATED | 8/8 | E43 |  |
| v17 | V5 | unlabelled | eb128 >= 0.8x pop qualified | PASS | 0.976-1.115 | E43 |  |
| v18 | S1 | unlabelled | Robust to fleet-law shape (t3, mixlow, mixhigh) | PASS | 0 violations in 48 groups; t3 max 0.745% | E44, E45 | Fragile: t3 NV cell bootstrap UB 2.09% (one outlier path). |
| v18 | S2 | unlabelled | Robust to +/-50% drift-amplitude error | PASS | 0 violations in 32 groups; amp03 max 0.94% (UB 1.12%) | E45 | Header: 'two near-limit cells'. |
| v18 | S3 | descriptive | Bootstrap UB and cost per stress | DESCRIPTIVE | fraction of oracle similar to v17 | E45 |  |
| v19 | N1 | unlabelled | Dephasing-only memories safe in 4/4 cells | PASS | 0 bad in 438,764 | E47, E49 | Cloud run, 0 SU. |
| v19 | N2 | unlabelled | T1=T2 safe in 4/4 | PASS | r <= 0.51% (UB 1.07%) | E49 |  |
| v19 | N3 | unlabelled | Amplitude-damping limit breaks (expected limitation) | CONFIRMED | 38.6% / 16.2% / 10.0% (ion cells) | E49 |  |
| v19 | N4 | unlabelled | Paired: dephasing never adds bad deliveries | YES | never adds bad deliveries vs Werner truth | E49 |  |
| v20 | Q1 | primary | T1-aware controller (correct T1) r <= 1% in every cell | PASS | 12/12; max 0.52% | E50, E51 |  |
| v20 | Q2 | unlabelled | Depolarising controller under ad exceeds 1% (replication) | REPLICATED | 15.0% / 37.3% / 8.7% | E51 |  |
| v20 | Q3 | unlabelled | T1 over-estimated by 25% exceeds 1% in >= 1 cell | CONFIRMED | 2.2% / 6.2% / 3.1% | E51 |  |
| v20 | Q4 | unlabelled | Under deph, T1-aware qualified >= depolarising | PASS | 1.02x-5.1x | E51 |  |
| C1 | C-A1 | primary | Frozen controller: Block A r <= 1% in every group | **FAIL** | 7 of 48 groups > 1% (6 SiV 1.97-5.79%; ion-future AD 1.43%) | E53, E54 | Both failing cells flagged at risk before run. No re-tuning (commitment honoured). |
| C1 | C-A2 | unlabelled | Block A path-bootstrap UB <= 1% | **FAIL** | same 7 groups | E54 | Prereg label 'stricter'. |
| C1 | C-B | unlabelled | Block B (fleet law) r <= 1% | **FAIL** | 3 of 24 groups, all SiV (1.1%, 8.0%, 3.7%) | E54 |  |
| C1 | C-C | exploratory | Unannounced 2-sd fault | EXPLORATORY | unsafe in 7 of 8 cells (post-fault r up to 100%) | E54 | Ledger: 'C-C unsafe'. |
| C1 | D | descriptive | Cost (fraction of oracle) | DESCRIPTIVE | SiV 0.04-0.15 ... tau0.85 0.62-0.91 | E54 |  |
| C2 | C2-A1 | primary | v21 robust prior: Block A r <= 1% every group | **FAIL** | 1 of 44 tested: SiV deph g0 1.42% (11/776) | E55, E56, E62 | Post-hoc fix after C1. 42/42 non-SiV pass (non-SiV restriction is post hoc, E62). 4 SiV groups untested (< 200 deliveries). |
| C2 | C2-A2 | unlabelled | Block A path-bootstrap UB <= 1% | **FAIL** | SiV deph both g (UB 3.1%, 1.2%) | E56 | Non-SiV UBs <= 0.55% later judged likely optimistic (E67) and superseded by S1 bounds (E70). |
| C2 | C2-B | unlabelled | Block B r <= 1% every group | **FAIL** | 1 of 23 tested: SiV mixhigh 2.08% (5/240) | E56 |  |
| C2 | C2-R | unlabelled | Rare declared faults: r <= 1% every cell | PASS | 8/8 cells; max 0.31% (E56) corrected to 0.32% incl. SiV (E62) | E56, E62 | Per-episode post-fault r 2.2-59% (aggregate protection only). |
| C2 | C2-C | exploratory | Always-fault | EXPLORATORY | still unsafe ion-2020 87%, NV 37%, SiV 15%, ion-proj 6.2% | E56 |  |
| C2 | D | descriptive | Throughput cost vs C1 | DESCRIPTIVE | non-SiV within +/-0.05; SiV near zero | E56 |  |
| P1 | P-1 | unlabelled | Identifiability I >= 3 -> r <= 1% | PASS | 12/12; max 0.53% | E58, E59 |  |
| P1 | P-2 | unlabelled | No group with I < 1 is both safe and useful | **FAIL** | 3 groups safe and useful (I 0.80-0.93) | E59, E62 | Corollary 3a withdrawn. E62 corrects the explanation (s_hat/s 1.007, 1.118, 0.938). |
| P1 | P-3 | descriptive | Where violations occur | DESCRIPTIVE | only at 1 < I <= 2 (3 of 7 groups) | E59, E62 | E62 limits this to P1 (C2 SiV failures at I = 0.72). |
| P1 | P-4 | descriptive | Throughput drivers | DESCRIPTIVE | throughput driven by T; K drives safety | E59 |  |
| Innsbruck Stage 1 | G1 | gate | Blind reproduction of authors' ion-photon fidelity within 0.02 | PASS | 0.920 +/- 0.004 vs authors 0.914-0.924 | E61, E62 | E62: PRL quotes 0.929; ours is 0.009 below, still inside the gate set against the repository figure (0.924). |
| Innsbruck Stage 1 | G2 | gate | Density-matrix elements agree | NOT COUNTED | magnitudes within ~0.02; phase -2 deg vs -87 deg | E61 | Ledger: 'Not counted as pass or fail' (frame convention). |
| Innsbruck Stage 2 | G3 | gate | Decoder reproduces paper's event count (+/-10%) and fidelities | **FAIL** | 581 vs 491 events (+18%); F+ / F- pass | E63 | Single allowed fix unused. |
| Innsbruck Stage 2 | H-a (Step 2) | unlabelled | Ion-ion assumption test | NOT RUN | - | E63 | Not run because gate G3 failed, as pre-registered. |
| G1 | H1 | primary | cal pooled r <= 1% in every group (route choice) | **FAIL** | 9/10; K ion2020 k=1: 1.173% (254/21,659) | E65, E66, E67 | Failing group has no route choice; 190 of 254 bad in one network (E67, post hoc). |
| G1 | H1b | unlabelled | cal network-bootstrap UB <= 1% | **FAIL** | UB > 1% in 4 groups (max 4.14%) | E66 | Prereg label 'stricter'. |
| G1 | H2 | unlabelled | Winner's curse for flat, not for cal (cal bias at k=8 <= 0) | **NOT CONFIRMED** | cal bias +0.0006 (NV), +0.0001 (ion2020) | E66 | Prereg label 'mechanism'. Qualitatively as predicted but bar missed. |
| G1 | H3 | unlabelled | flat r rises from k=1 to k=8 on both hw | **NOT CONFIRMED** | NV 1.23 -> 1.93%; ion2020 4.39 -> 1.04% | E66 | Prereg label 'consequence'. |
| G1 | H4 | descriptive | Cost/benefit of route choice | DESCRIPTIVE | best routing 0.86 -> 0.95 (ionproj) | E66 |  |
| G2 | H1 | primary | Guarded calg pooled r <= 1% every group | PASS | 10/10; 0 bad in ~1.67M | E68, E69 | Post-hoc remedy after G1 FAIL (G1 verdict stands). |
| G2 | H1b | unlabelled | calg network-bootstrap UB <= 1% | PASS | all UB 0.000% | E69 |  |
| G2 | H2 | unlabelled | Bad paths / delivering paths <= 5% (Prop. 6) | PASS | 0 of 56,959 | E69 |  |
| G2 | H3 | descriptive | Cost of guard | DESCRIPTIVE | 2-15% relative throughput loss | E69 |  |
| G2 | H4 | descriptive | G1 replication on fresh seeds (cal) | DESCRIPTIVE | 0 of 10 groups > 1% (max 0.943%); UB up to 1.40% | E69 |  |
| S1 | S1-a | primary | C2 non-SiV r <= 1% with realistic overlapping windows | PASS | 42/42; max 0.834% | E68, E70 | Point risk also rose in 37 of 42 groups (not predicted). |
| S1 | S1-b | unlabelled | Upper bounds widen (median ratio > 1) | CONFIRMED | median UB ratio 2.01; 33 of 42 groups UB <= 1% | E70 |  |
| S1 | S1-c | descriptive | Groups with UB <= 1%, SiV | DESCRIPTIVE | 33/42 vs 42/42; SiV 1.28%, 3.01% | E70 |  |
| G3 | H1 | primary | calg r <= 1% in all 4 groups (30x30) | PASS | 0 bad in ~2.11M | E72, E73 |  |
| G3 | H1b | unlabelled | calg network-bootstrap UB <= 1% | PASS | all 0.000% | E73 |  |
| G3 | H2 | unlabelled | calg bad paths <= 5% | PASS | 0 of 930,435 | E73 |  |
| G3 | H3 | unlabelled | Frozen cal r <= 1% in all 4 groups | PASS | 0.69-0.83%; max UB 0.87% | E73 | Per path still exposed: 1.2-3.0% of paths bad. |
| G3 | H4 | descriptive | Own-link vs external prior | DESCRIPTIVE | r 0.80 vs 0.83%; 0.69 vs 0.74% | E73 |  |
| G3 | H5 | descriptive | Cost of guard | DESCRIPTIVE | -6% / -9% | E73 |  |
| G4 | H1 | primary | gdrift (Prop. 6') safe under drift | PASS | 0 bad in ~514k; 0 of 21,434 paths | E75, E76 | Cost: 0.68 vs 0.85; 0.63 vs 0.95 of oracle. |
| G4 | H2 | unlabelled | gnaive (ignores drift) delivers bad pairs | CONFIRMED | 69 and 463 bad | E76 | Prereg label 'prediction'. |
| G4 | H3 | open | Does nominal guard survive 25% model error? | ANSWERED | yes, slightly: 5 and 16 bad | E75, E76 | Was a prediction; converted to open question after the dev pilot, before the confirmatory run (E75). |
| G4 | H4 | primary | grobust (declared set covers truth) safe under M | PASS | 0 bad; 0 of 26,174 paths | E76 |  |
| G4 | H5 | descriptive | Costs; unguarded fragility | DESCRIPTIVE | cal r 1.18-1.26% (drift), 2.6-2.7% (25% error) | E76 | cal under D uses simplified grid controller (caveat in E76). |
| G4 | H6 | open | M50: declared set does not cover truth | ANSWERED | gnom 15.3% / 5.9% of paths bad; grobust 16 and 2 bad | E75, E76 | M50 added after dev pilot, before confirmatory run. |
| G5 | H1 | primary | gexact safe in all 4 groups | PASS | 0 bad in 1,183,827 | E77, E78 |  |
| G5 | H2 | primary | gexact > gdrift throughput (paired LB > 0, all 4 cells) | PASS | +0.038/+0.046 (ion2020), +0.129/+0.126 (ionproj) | E77, E78 |  |
| G5 | H3 | secondary | gpersist under D safe and >= gexact | PASS | 0 bad; 0.816 / 0.896 of oracle | E78 |  |
| G5 | H4 | unlabelled | gpersist under Dj delivers bad pairs (pilot-informed prediction) | CONFIRMED | 43 / 211 bad | E77, E78 | Prereg label 'prediction, pilot-informed'. |
| G5 | H5 | descriptive | Costs | DESCRIPTIVE | cal r 1.21-1.36% | E78 |  |
| G6 | H1 | primary | galarm late post-fault bad <= 0.1% (per hw) and < cal in every group | **FAIL** | ion2020 0.14% (> 0.1%); ionproj 0.07% | E80, E81 | Ledger: 'FAIL (narrowly)'. Fewer than cal in every group. |
| G6 | H2 | primary | galarm r <= 1%, UB <= 1%, bad paths <= 5% | PASS | r <= 0.12%; UB <= 0.15%; bad paths 0.5-2.8% | E81 |  |
| G6 | H3 | secondary | Detects >= 90% of faults; <= 1 false alarm / 10 networks | **FAIL** | 414/475 = 87% detected | E81 |  |
| G6 | H4 | secondary | galarm fraction of oracle >= gnaive - 0.02 | PASS | cost 0.4-0.7 points | E81 |  |
| G6 | H5 | descriptive | Early vs late bad, cost | DESCRIPTIVE | late bad: cal 793, gnaive 286, galarm 24, gwin 5 | E81 |  |
| G7 | H1 | primary | gglr late bad <= 0.1% and <= galarm's, per hw | **FAIL** | 0.068% / 0.065% but ion2020 8 vs galarm 4 | E82, E83 | Fails on the '<= galarm' clause. |
| G7 | H2 | primary | gglr detects >= 90% of 2-SD faults | PASS | 252/255 (98.8%) | E83 |  |
| G7 | H3 | secondary | <= 1 false alarm per 10 networks | PASS | 6 in 256 networks | E83 |  |
| G7 | H4 | secondary | gglr r <= 1%, UB <= 1%, bad paths <= 5% | PASS | (no number given in ledger) | E83 |  |
| G7 | H5 | secondary | gglr fraction of oracle >= galarm - 0.02 | PASS | (no number given in ledger) | E83 |  |
| G7 | H6 | descriptive | Misses and costs | DESCRIPTIVE | late bad: cal 769, galarm 28, gglr 28, gglr_s 14 | E83 |  |
| 23 | Go/no-go #1 | gate | AI prior error reduction >= 20% (held-out, offline) | PASS | -30.6% dense, -25.0% thin | E84 | Stop rule fixed in PLAN.md before any result. Offline held-out check, not a confirmatory run. |
| 23 | Go/no-go #2 | gate | ag or arg beat bg by >= 2 points in correlated cells (dev pilot) | PASS | 3 of 4 cells (arg +1.73/+2.67/+2.99/+6.26) | E85 | Evaluated on the dev pilot (seeds 20231-20234). |
| 23 | H1 | primary | Every guarded arm safe in all 16 cells | PASS | 0 guarded bad pairs | E85, E86 |  |
| 23 | H2 | primary | arg - bg >= 2 points on correlated cells, LB > 0 | PASS | +3.05 [2.75, 3.36] | E86 |  |
| 23 | H3 | primary | ag - fg > 0 on correlated cells (AI beyond informed prior) | PASS | +1.07 [0.83, 1.33] | E86 | E86 addendum (post hoc): H3 mixes correlation learning with use of known fleet spread; rho=0 cells bound the latter (+0.05). |
| 23 | H4 | secondary | ag - fg within +/-1 point on independent cells | PASS | +0.05 | E86 | Tier and bar from STUDY23_PREREG doc. |
| 23 | H5 | secondary | arg - ag over 8 cells, LB > 0 (RL adds value) | PASS | +0.34 [0.27, 0.41] | E86 | Tier and bar from STUDY23_PREREG doc. |
| 23 | H6 | descriptive | Other comparisons | DESCRIPTIVE | no-guard r 0.53-1.11%; 5-21% paths bad | E86 |  |
| 24 | H1 | primary | Every guarded arm safe in all 25 cells | PASS | 0 bad in 34.8M | E88, E89 |  |
| 24 | H2 | primary | ag2 - bg on NV+SiV >= 10 points, LB > 0 | PASS | +20.0 [19.2, 20.9] | E89 |  |
| 24 | H3 | primary | ag2 - kg on thin hw correlated patterns, LB > 0 | PASS | +11.4 [10.5, 12.3] | E89 |  |
| 24 | H4 | primary | ag2 - kg on unseen patterns, LB > 0 | PASS | +4.4 [4.0, 4.8] | E89 |  |
| 24 | H5 | secondary | No harm on independent links (LB > -1) | PASS | +1.07 | E89 |  |
| 24 | H6 | secondary | AI v2 better than v1 (LB > 0) | PASS | +0.22, LB +0.001 | E89 | Ledger: 'PASS, barely'; pilot predicted FAIL. |
| 24 | H7 | secondary | Neural net beats linear (LB > 0) | PASS | +0.54 [0.35, 0.74] | E89 | Pilot predicted FAIL. |
| 24 | H8 | descriptive | Per-hw decomposition; latency | DESCRIPTIVE | SiV known law +17.7, AI +5.8; NV AI +13.6 | E89 |  |
| 24 | B1 | primary | gcarry safe | PASS | 0 bad | E88, E89 |  |
| 24 | B2 | primary | gcarry - gexact 90% CI inside [-2, +2] (Prop. 7) | PASS | +0.30 [0.22, 0.38] | E89 |  |
| 24 | B3 | secondary | gpersist fails under jitter | CONFIRMED | 55/204 (Dj), 1,251/3,002 (Djb) | E89 |  |
| 24 | B4 | descriptive | gexact safety and cost vs cal | DESCRIPTIVE | (not reported in ledger) | E88 | Listed in prereg doc; no B4 line in E89. |
| ICFO Stage 1 | R1-A | primary | 2 us visibility in [0.78, 0.90] | **FAIL** | V(rms) = 1.014 | E90, E91, E92 | Estimator assumption (evenly spread phases) violated. |
| ICFO Stage 1 | R1-B | primary | 2 us F_eff in [0.89, 0.95] | **FAIL** | 1.007 | E90, E92 |  |
| ICFO Stage 1 | R1-C | secondary | 2 us concurrence in [0.80, 1.50]e-2 | **FAIL** | 2.64e-2 | E90, E92 |  |
| ICFO Stage 1 | R1-D | secondary | rho(tau, C) <= -0.7 and C(25 us) z >= 5 | PASS | rho -0.90; 6.2 sigma | E90, E92 |  |
| ICFO Stage 1 | R3 | descriptive | Over-dispersion and anytime CS coverage on real data | DESCRIPTIVE (CORRECTED) | 7 of 11 runs over-dispersed; CS never excluded estimate in 10 of 11 | E92, E95 | E92 said 9 of 12 and 11 of 12; superseded by E95 (11 both-open runs). |
| USTC Stage 1 | U1 | primary | Dephasing model from single-ion coherence predicts remote fidelity decay within 2 sigma + 0.02 | PASS | all 4 storage times; model optimistic by 0.020-0.044 | E96, E97 | Ledger: 'PASS, but a weak test'. |
| USTC Stage 1 | U2 | secondary | Per-set QBER over-dispersion and anytime CS coverage | UNCLEAR | dispersion 3.57; CS excluded full-run rate for 3.5% of run | E96, E97 | No pass bar or verdict recorded in ledger; reported descriptively. 200 sets, not 201. |
| 25 | M1 | primary | Declared D >= kappa keeps kg safe (30 cells) | PASS | 0 bad in 1.21M | E101, E103 |  |
| 25 | M2 | primary | Undeclared kappa=0.5 breaks per-path bound (ion2020, D=0) | PASS | 15.4% of paths bad | E103 | Prediction confirmed. |
| 25 | K1 | primary | Campaign arms safe (12 cells) | PASS | 0 bad in 495k | E103 |  |
| 25 | K2 | primary | SiV campaigns K=64/256/1024 recover >= 80% of kg - bg | PASS | 0.876 / 0.988 / 0.947 | E103 |  |
| 25 | T1 | primary | All six arms safe at c in {0, 0.5} | PASS | 0 bad | E103 |  |
| 25 | T2 | primary | Declared phi restores safety (18 cells) | PASS | 3 bad in 845k; max 0.23% paths bad | E103 |  |
| 25 | C1 | primary | bg, kg, ag2 safe under load and signalling delay (48 cells) | PASS | 0 bad in 7.31M | E103 |  |
| 25 | D1 | primary | Declared bound safe when B >= 3 sd (20 cells) | PASS | 0 bad in 6.22M | E103 |  |
| 25 | D2 | primary | gb0.005 recovers >= 40% of restart cost (both hw) | PASS | 0.611 / 0.625 | E103 |  |
| 25 | C2 | secondary | Thin-hw gain under par4 >= 10 points, LB > 0 | PASS | +26.5, 90% CI [23.6, 29.5] | E103 |  |
| 25 | D3 | secondary | Broken promise (Djb, B=0.005) gives bad pairs | CONFIRMED | 1,425 / 4,065 bad | E103 |  |
| 25 | T3 | secondary | At c=2 AI prior adds <= 2 points of bad paths vs kg | **FAIL** | NV ag2t 5.05% vs kg 2.93% (+2.12) | E103 | Not re-tuned. ag2 itself passes on all hw. |
| 25 | M3/K3/T4/C3/D4 | descriptive | Maps, estimation error, costs, latency, promise check | DESCRIPTIVE | - | E101, E103 | Listed in STUDY25_PREREG; not itemised in ledger. |

## Failures and corrections

### Every non-PASS primary/secondary/unlabelled result

Includes FAIL, NOT MET, NOT CONFIRMED, NOT RUN and UNCLEAR rows of every tier that has a bar, including gates. CONFIRMED, REPLICATED and YES are pass-type outcomes for registered predictions, so they are not listed here.

| Study | ID | Tier | Outcome | Key number | Ledger |
|---|---|---|---|---|---|
| 13 | E2 | unlabelled | NOT MET | acceptance -1.18 [-1.64, -0.72]; pairs -1.084 | not in ledger |
| 14 | R1 | unlabelled | UNCLEAR | 6/6 conditions | not in ledger |
| 14 | R2 | unlabelled | UNCLEAR | 7/7 conditions | not in ledger |
| 17 | F4 | unlabelled | FAIL | -1.04 [-1.27, -0.81] | E1 |
| v5 | P2 | unlabelled | FAIL | infeasible at g=1e-4; reset +0.066 at g=1e-5 (ion_proj) | E21 |
| v5 | P3b | unlabelled | FAIL | point rule (>= 50 deliveries) was also safe | E21 |
| v6 | Q1 | unlabelled | FAIL | gain <= 0.012 | E21, E22 |
| v6 | Q3 | unlabelled | FAIL | 6 of 11 feasible eval rows > 1% (max 6.0%) | E22 |
| v6 | Q4 | unlabelled | UNCLEAR | monotone in headroom; no collapse without normalisation | E22 |
| v7 | R3 | unlabelled | FAIL | 28% of 36 series have tau <= -0.6 | E23 |
| v9 | T1 | unlabelled | FAIL | 3 of 20 groups > 1% (6.2%, 14.6%, 1.5%; ion_2020 ols_reset) | E25, E27, E28 |
| v11 | U2 | unlabelled | FAIL | violates in 3 groups (5.6%, 20%, 1.66%; small counts) | E29 |
| v11 | U3 | UNCLEAR | UNCLEAR | - | E27, E29 |
| v10b | M2 | unlabelled | FAIL | opposite direction: ion_future 0.578 -> 0.578; ion_2020 L2 -97% | E30 |
| v10b | M3 | unlabelled | FAIL | 0.78 vs 0.80 bar | E30 |
| v12 | L3 | unlabelled | FAIL | 0.59x and 0.70x of LTT (2 groups) | E33 |
| FINAL (18C) | F4 | secondary | FAIL | LTT-S0 violated 1 group (5.85%); LTT-S1 4 | E34, E35 |
| v14 | B1 | unlabelled | FAIL | 1 of 8 groups: 9 pairs, 1 bad (11%) | E36, E37 |
| v15 | G1 | unlabelled | FAIL | 4 of 32 groups > 1%, all NV-like (1.40-8.3%) | E38, E39 |
| C1 | C-A1 | primary | FAIL | 7 of 48 groups > 1% (6 SiV 1.97-5.79%; ion-future AD 1.43%) | E53, E54 |
| C1 | C-A2 | unlabelled | FAIL | same 7 groups | E54 |
| C1 | C-B | unlabelled | FAIL | 3 of 24 groups, all SiV (1.1%, 8.0%, 3.7%) | E54 |
| C2 | C2-A1 | primary | FAIL | 1 of 44 tested: SiV deph g0 1.42% (11/776) | E55, E56, E62 |
| C2 | C2-A2 | unlabelled | FAIL | SiV deph both g (UB 3.1%, 1.2%) | E56 |
| C2 | C2-B | unlabelled | FAIL | 1 of 23 tested: SiV mixhigh 2.08% (5/240) | E56 |
| P1 | P-2 | unlabelled | FAIL | 3 groups safe and useful (I 0.80-0.93) | E59, E62 |
| Innsbruck Stage 1 | G2 | gate | NOT COUNTED | magnitudes within ~0.02; phase -2 deg vs -87 deg | E61 |
| Innsbruck Stage 2 | G3 | gate | FAIL | 581 vs 491 events (+18%); F+ / F- pass | E63 |
| Innsbruck Stage 2 | H-a (Step 2) | unlabelled | NOT RUN | - | E63 |
| G1 | H1 | primary | FAIL | 9/10; K ion2020 k=1: 1.173% (254/21,659) | E65, E66, E67 |
| G1 | H1b | unlabelled | FAIL | UB > 1% in 4 groups (max 4.14%) | E66 |
| G1 | H2 | unlabelled | NOT CONFIRMED | cal bias +0.0006 (NV), +0.0001 (ion2020) | E66 |
| G1 | H3 | unlabelled | NOT CONFIRMED | NV 1.23 -> 1.93%; ion2020 4.39 -> 1.04% | E66 |
| G6 | H1 | primary | FAIL | ion2020 0.14% (> 0.1%); ionproj 0.07% | E80, E81 |
| G6 | H3 | secondary | FAIL | 414/475 = 87% detected | E81 |
| G7 | H1 | primary | FAIL | 0.068% / 0.065% but ion2020 8 vs galarm 4 | E82, E83 |
| ICFO Stage 1 | R1-A | primary | FAIL | V(rms) = 1.014 | E90, E91, E92 |
| ICFO Stage 1 | R1-B | primary | FAIL | 1.007 | E90, E92 |
| ICFO Stage 1 | R1-C | secondary | FAIL | 2.64e-2 | E90, E92 |
| USTC Stage 1 | U2 | secondary | UNCLEAR | dispersion 3.57; CS excluded full-run rate for 3.5% of run | E96, E97 |
| 25 | T3 | secondary | FAIL | NV ag2t 5.05% vs kg 2.93% (+2.12) | E103 |

### Corrections recorded in the ledger (cite both entries)

| What was corrected | Original | Correction | Effect on scoreboard |
|---|---|---|---|
| ICFO R3 counts | E92: over-dispersion 9 of 12 runs; CS never excluded in 11 of 12 | E95: 11 both-open runs, so 7 of 11 and 10 of 11 | R3 row shows the E95 numbers (descriptive) |
| C2-R maximum | E56: max 0.31% | E62: 0.32% with SiV included | Still PASS; both values given |
| C2 framing | E56 header: "FAIL (SiV only)" | E62: C2 *failed its primary test*; the non-SiV restriction is post hoc; SiV exceeded 1% in 2 groups (1.42% A, 2.08% B) | C2-A1, C2-A2 and C2-B stay FAIL |
| P-2 explanation | E59: "ŝ/s = 1.1–1.6, over-estimated" | E62: ŝ/s 1.007, 1.118, 0.938, so over-estimation does not explain all three | P-2 stays FAIL; the mechanism text is corrected |
| P-3 scope | E59: violations only at 1 < I ≤ 2 | E62: holds within P1 only (C2's SiV failures are at I = 0.72) | Descriptive row annotated |
| v14 B2 attribution | E37: label-free 0/9 | E62: that was the earlier Gaussian controller, not the EB controller | B2 stays PASS, with the attribution noted |
| "Fresh draws are valid for the mean" | E67 | E70: wrong; the mean risk shifts too (point risk rose in 37 of 42 groups) | C2/P1 bootstrap UBs superseded by the S1 bounds (E70) |
| Innsbruck Stage 1 reference value | E61: gate set against the repository figure 0.924 | E62: the PRL quotes 0.929; ours is 0.009 below it, still inside 0.02 | G1 stays PASS |
| Study 25 "public before the run" | E102 | E102 addenda 1–3: Block A started 22:57:08 UTC, before the commit (22:58:56) and push (by 23:00:47); first output at 23:01:15 | Timing claim narrowed; no outcome changes |
| T1 requirement wording | — | E62: "better than 25%; under-estimates untested" | Q3 (v20) note |

### Post-hoc remedies (each designed after seeing a failure; the earlier verdict stands)
- v9 T1 FAIL → v11 (E27, designed after seeing v9 partial results, 658 of 2,160 runs).
- v15 G1 FAIL → v16 (E40: "E39 G1 stays FAIL").
- v19 N3 (AD limit unsafe) → v20.
- C1 C-A1/C-A2/C-B FAIL → v21 + C2 (E55: "E54 stands").
- G1 H1/H1b FAIL → G2 (E68: "G1's verdict stands").
- G4 cost → G5. G6 H1/H3 FAIL → G7. Study 23 H3 confound → `kg` control in Study 24 (E86 addendum).

## Pilots and dev runs viewed before the lock

Not counted above. Each was disclosed in the ledger before the corresponding confirmatory run.

| Study | What was seen before locking | Ledger |
|---|---|---|
| v4/DES | Cloud pilot of combos 1 and 4 (ion_2020 L2, load 0.9) | E19 |
| v5 | Unit checks of new estimators; spawn-start smoke run | E20 |
| v6 | SE check against empirical SD | E21 |
| v9 | Cloud smoke test (found and fixed the empty-passing-set bug) | E25 |
| v11 | **v9 partial confirmatory results (658 of 2,160) seen before v11 was pre-registered**; smoke tests | E27 |
| v10 | PSC test shard 47438275 (~0.3 SU), cancelled | E29 |
| v12 | Cloud smoke of the eval z = 2 path (reproduced v11) | E32 |
| FINAL | Cloud smoke (ion_future L4 adaptive path); S2 dev arm dropped before data | E34 |
| v15 | Smoke finding: adaptive abstains on marginal paths | E38 |
| v16 | Cloud dev pilot seeds 19931/19932; **9 confirmatory-seed tasks (paths 0–3) run for runtime only** | E40 |
| v17 | Cloud dev pilot seeds 19951–19953 | E42 |
| v18 | Cloud dev pilot seeds 19961–19963 (t3 ion-proj 2.25% flagged) | E44 |
| v19 | Disclosed bias scan (true F − model F) | E47 |
| v20 | Cloud dev pilot seeds 19981–19983 | E50 |
| C1 | Cloud dev pilot seeds 19991–19994 (two at-risk cells flagged) | E53 |
| C2/v21 | Dev pilots seeds 20001–20004 | E55 |
| G1 | Cloud dev pilot seeds 20101–20104 | E65 |
| G2 | Dev pilot seeds 20111–20114 | E68 |
| S1 | Cloud smoke, 3 tasks (from S1_PREREG doc; not itemised in the ledger) | — |
| G3 | Cloud smoke seeds 20121–20124 | E72 |
| G4 | Dev pilots seeds 20131–20134; **the pilot changed the plan (H3 made open, M50 added)** | E75 |
| G5 | Dev pilot seeds 20141–20144; **H4 is pilot-informed** | E77 |
| G6 | Dev pilot seeds 20151–20154 (28 faults) | E80 |
| G7 | Dev pilot, 24 faults (seeds 20161–20164 per prereg doc) | E82 |
| 23 | Offline AI check (go/no-go #1); RL training (CEM, seeds 50000+); PSC dev pilot 384 tasks, seeds 20231–20234 (go/no-go #2); cloud check of the new `fg` control | E84, E85 |
| 24 | Cloud dev runs and the guard design chosen on dev (E87); Block B smoke; PSC dev pilots P24 (1,400) and P24B (192); latency-recording equivalence check on 4 dev tasks | E87, E88 |
| 25 | Two independent code reviews; PSC dev pilots P25 (1,440) and P25D (432), 19.3 SU | E100, E101 |
| Innsbruck | File structure and headers only (E60); Stage 1 sensitivity after choices fixed | E60, E61 |
| ICFO | File names, authors' scripts, singles rates, one herald–signal delay histogram; **first run (79a2caad) results seen before the single allowed decoding fix** (R1-A input unaffected) | E90, E91 |
| USTC | Workbook headers only | E96 |

**Count:** 30 studies or stages (rows above) had pilot, dev or smoke exposure before their lock. Two had confirmatory-seed or confirmatory-data exposure: v16 (9 tasks, runtime only) and v11 (designed after partial v9 confirmatory data). Two pilots changed a hypothesis before the lock: G4 H3 (made open) and G5 H4 (pilot-informed).


## Ledger inconsistencies and open points noticed while building this

1. **E92 vs E95 (ICFO R3):** run counts 12 → 11. Corrected in E95; E92's text was left as written.
2. **E56 vs E62 (C2-R maximum):** 0.31% vs 0.32%. E62 includes SiV.
3. **E59 vs E62 (P-2 mechanism):** E59 says ŝ/s = 1.1–1.6 for the safe low-I groups, while E62 gives 1.007 / 1.118 / 0.938. The project note P1_RESULTS still says "ŝ/s 1.0–1.6" for the I ≤ 1 band.
4. **E67 vs E70:** "fresh draws are valid for the mean" was retracted. So the C2 and P1 path-bootstrap upper bounds (e.g. ≤ 0.55%) are likely optimistic, and the E54/E56 uncertainty statements should not be quoted alone.
5. **E99:** says "22 of 22" PSC-run studies had their pre-registration on the cluster first. Counting distinct PSC confirmatory runs before E99 (v10b, v11, v12, FINAL, v14–v18, v20, C1, C2, P1, G1, G2, S1, G3–G7, 23, 24) gives 23. They agree if G2 and S1 (one pre-registration entry, E68) count as one. UNCLEAR. E99 also says "v5–v10 ran on the Mac", but v10 had only a cancelled PSC test shard and v10b ran on PSC.
6. **E102 vs addenda:** "public before the confirmatory run" was false for Study 25 Block A, which started about 2 min before the commit. The addenda narrow the claim; no outcome depends on it.
7. **PSC accounting:** account-based and timing-based totals disagree repeatedly: E52 354 vs 366; E57 642 vs 931; E79 1,233 SU charged against a 1,000 SU cap, where the earlier estimate was ~850. This does not affect any outcome, but the cap was exceeded before G6 (E79/E80).
8. **v11 U3:** registered (E27, "U1–U3") but never reported by name (E29). E29 reports T3 and T4 instead.
9. **v18 header:** "S2 PASS (two near-limit cells)", but the S2 text names only one near-limit S2 cell (amp03, 0.94%). The other near-limit cell (t3 NV, 0.745%) belongs to S1.
10. **Study 24 B4 and Study 25 M3/K3/T4/C3/D4:** registered as descriptive, but no result line appears in the ledger.
11. **Studies 13 and 14** (E1/E2, R1/R2) are cited as "registered results" in project docs but have no ledger entry. R1/R2 have no verdict word.
