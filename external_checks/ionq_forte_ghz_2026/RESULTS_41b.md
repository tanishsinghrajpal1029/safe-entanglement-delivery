# Study 41b results: the certificate for GHZ-3 and GHZ-4 states on IonQ Forte 1 (15 Nov 2026)

Pre-registration: `PREREG_41b.md` (commit add3dd6, pushed 13 Nov 2026 21:32:25 PST). Confirmatory run of the frozen analysis on all 20 hardware jobs: Stage 1 at 2026-11-15 05:02:56, Stage 2 at 05:03:26 (Mac clock), on Tanish's Mac (NumPy 2.5.1), test switch off. Outputs (sha256/16): `out/analysis_41b_stage1.txt` 772901d613af14f3, `out/analysis_41b_stage2.txt` de05a4d5d9eaae34, `out/stage2_41b.json` ec255917cf5ca912. Code hashes as frozen: analyze_41b.py 5f677757…, job_41b.py bed23a6b…, cert.py 6b84bbdd….

## Run record
- 20 jobs on `ionq_qpu.forte-1` (IonQ record `qpu.forte-1`, 36 qubits per job; compiled 43–48 one-qubit and 24–27 two-qubit gates), 1,000 shots each, debiasing off (IonQ's own record). First job 14 Nov 2026 05:34:24 UTC (21:34 PST on 13 Nov, 2 min after the push), last 15 Nov 12:51:59 UTC (31.3 h). All sent in job-number order; no lost or repeated jobs.
- Platform issue (no effect on data): Qollab's page intermittently reset after the cost confirmation without submitting (as during 41a).

## Stage 1: gates — all PASS
G0 (all five frozen files listed and identical), G1 (all 20 present; size, groups, tests and the submitted OpenQASM circuit equal the frozen table gate by gate; Forte hardware with IonQ metadata, no noise model; no debiasing or other mitigation; 1,000 shots), G2 (every job: each test's error < 0.25, F > 0.5; worst single test 0.080, lowest per-job F 0.940).

## Stage 2: primary hypotheses — 4 of 4 PASS (all as predicted)
| | Prediction | Result |
|---|---|---|
| **H3b** validity (final), GHZ-3 and GHZ-4 | PASS | **PASS**: 0/1000 violations at each p = 0.05, 0.1, 0.2, both sizes |
| **H4b** anytime (10 job checkpoints per size, time order) | PASS | **PASS**: 0/1000 at each p, both sizes |
| **H5b** median certificate at p = 0.2 > 0.90 (GHZ-3), > 0.85 (GHZ-4) | PASS | **PASS**: **0.953** and **0.938** |
| **H6b** GME of the kept ensemble from the first job alone (certificate > 0.5 at the first checkpoint in ≥ 99 % of draws, p = 0.05) | PASS | **PASS**: 100 % of draws, both sizes |

Median certificates (p = 0.05 / 0.1 / 0.2): GHZ-3 0.9482 / 0.9512 / 0.9530; GHZ-4 0.9313 / 0.9352 / 0.9376.

## Descriptives
- **D1 GHZ-3** (120,000 states): error rates Z 2.79 %, XXX 2.44 %, XYY 2.77 %, YXY 2.89 %, YYX 3.01 %; linear F **0.958**; certificate − F = −0.005.
- **D1 GHZ-4** (90,000 states): Z 3.64 %, XY strings 3.43–4.09 %; linear F **0.945**; certificate − F = −0.007. Realised clusters per XY string 6–9 (expected 7.5), as disclosed in advance.
- **D2 (clustering):** excess heterogeneity across (job, group) clusters mainly in the Z test (χ²/df 6.0 for GHZ-3, 2.8 for GHZ-4; cluster range up to 8.8 %) and a few XY strings (YYX 3.8; YYXX 6.5); others ≈ 1. Per-job F 0.952–0.963 (GHZ-3) and 0.940–0.950 (GHZ-4): no drift.
- **D3 (independence):** errors of different GHZ states in the same shot are mildly positively correlated: variance ratio median 1.22 (GHZ-3) and 1.12 (GHZ-4); mean pairwise correlation +0.026 and +0.017 (41a Bell pairs: 1.24, +0.020).
- **D5 (scaling):** 1 − F per CX gate 0.021 (GHZ-3, 2 CX) and 0.018 (GHZ-4, 3 CX), vs 0.022 for 41a's Bell pairs (1 CX): infidelity grows roughly linearly with the number of entangling gates.
- **D6:** median certificate after the first job (12,000 / 9,000 states) 0.943 (GHZ-3) and 0.915 (GHZ-4); 0.953 and 0.938 at the end.

## Meaning (draft, for the paper)
1. The same certificate, with the same constant (P(fail) = (2/3)(1 − F) for the stabiliser test of Li, Han & Zhu), certifies multi-party entanglement on hardware with no new theory: GHZ-3 certified at 0.953 (measured 0.958) and GHZ-4 at 0.938 (measured 0.945).
2. Genuine three- and four-party entanglement of the delivered ensemble is certified from a single 1,000-shot job, and the guarantee held at every checkpoint.
3. As for Bell pairs, validity held although the hardware violates the idealisations measurably (clustered settings with up to 6× excess heterogeneity in some tests, mildly correlated errors across simultaneous states). These are empirical results, not covered by the proof.

## Limits (as pre-registered)
Tests fixed per (job, group), not per state; test-or-keep drawn after the fact; U is a conservative reference (especially loose at early GHZ-4 checkpoints), no planted fault in 41b; readout not corrected (rmax = 0); trusted measurements and compiler; one device over 1.3 days.
