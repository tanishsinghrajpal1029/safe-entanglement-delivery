# Study 41a results: the certificate on IonQ Forte 1 hardware (13 Nov 2026)

Pre-registration: `PREREG_41a.md` (commit 1012b04, pushed 10 Nov 2026 21:58:28 PST). Confirmatory run of the frozen analysis on all 30 hardware jobs: Stage 1 at 2026-11-13 18:59:51 PST, Stage 2 at 19:00:30 PST, on Tanish's Mac (NumPy 2.5.1), test switch off. Outputs (sha256/16): `out/analysis_41a_stage1.txt` 09c4dc6cfab72df8, `out/analysis_41a_stage2.txt` da082837fa26c88a, `out/stage2_41a.json` cdd44b02846f98e3. Code hashes as frozen: analyze_41a.py 9ce04a96…, job_41a.py 2de182a7…, cert.py 6b84bbdd….

## Run record
- 30 jobs on `ionq_qpu.forte-1` (IonQ record `qpu.forte-1`), 18 Bell pairs × 1,000 shots each, debiasing off (IonQ's own job record), first job 11 Nov 06:01:41 UTC, last 13 Nov 21:31:41 UTC (63.5 h).
- **Job 13:** first submission (13 Nov 05:21:55 PST, id 01a1d512-67a3-78f0-b691-4d0c48282484) returned IonQ API error 500 when its results were fetched, so it has no counts. As pre-registered it was set aside and listed (`data/raw/s41a_job_13_lost_ionq500.json`), and job 13 was re-run (id 01a1d5e8-8f49-709a-8ded-0733a2d6a552, 09:15:50 PST). As a result, submission order differs from job-number order; checkpoints follow submission time, as pre-registered.
- Platform issues (no effect on data): an 8 h 10 min queue for job 1; on 12 Nov Qollab's page reset after cost confirmation several times without submitting (reported to Qollab). Cost ≈30 credits per job.

## Stage 1: gates — all PASS
G0 (frozen hashes), G1 (all 30 present; design and the submitted OpenQASM circuit equal the frozen table gate by gate; Forte hardware; no debiasing; 1,000 shots), G2 (every job: each clean-pair basis error < 0.25, F > 0.5; worst basis error 0.0233, lowest F 0.9734).

## Stage 2: primary hypotheses — 5 of 5 PASS (all as predicted)
| | Prediction | Result |
|---|---|---|
| **H3** validity, Block A (final) | PASS | **PASS**: 0/1000 violations at each p = 0.05, 0.1, 0.2 |
| **H4** anytime, Block A (20 job checkpoints, time order) | PASS | **PASS**: 0/1000 at each p |
| **H5** median certificate, Block A, p = 0.2, > 0.9 | PASS | **PASS**: 0.9757 |
| **H6** validity under planted fault, Block B (final + 10 checkpoints) | PASS | **PASS**: 0/1000 at each p |
| **H7** certificate drop matches the planted fault (ratio in [0.5, 1.5]) | PASS | **PASS**: predicted 0.0474, observed 0.0512, ratio **1.08** (expected 1.05–1.1) |

Median certificates: Block A 0.9736 / 0.9749 / 0.9757 (p = 0.05 / 0.1 / 0.2); Block B 0.9195 / 0.9225 / 0.9244.

## Descriptives
- **D1:** Block A error rates X/Y/Z 1.43/1.49/1.49 %, linear F(Φ⁺) **0.978**; certificate − F = −0.0023 (p = 0.2). Block B faulty pairs 15.5/16.1/1.4 % vs predicted 15.7/15.7/unchanged; by sign +θ 16.1/16.3/1.4 %, −θ 15.0/15.9/1.4 %. Block B F 0.9302 vs **predicted 0.9306**; Block B certificate 0.9244 lies 0.0062 below the ground-truth reference F_A − Δ.
- **D2 (clustering):** excess heterogeneity across (job, pair) clusters: χ²/df 2.06 (X), 2.31 (Y), 3.15 (Z); cluster error ranges 0.3–5.1 %. Per-job F 0.974–0.982 (Block A) and 0.973–0.981 (Block B clean pairs): no drift.
- **D3 (independence):** errors on different pairs in the same shot are mildly positively correlated: variance ratio of errors per shot, median 1.24 (range 0.95–2.16); mean pairwise error correlation +0.020.
- **D5:** worst logical qubits q4, q6, q5 (1.75–1.95 %; logical, not physical, labels).
- **D6:** Block A median certificate 0.969 after the first job (18,000 pair outcomes), 0.976 at the end.
- **D7:** hardware F 0.978 vs noise-model simulator ≈0.985.

## Meaning (draft, for the paper)
1. First run of the protocol by us on a real QPU with settings fixed in advance: the certificate was valid at every checkpoint and within 0.003 of the measured fidelity (0.976 vs 0.978).
2. Against a fault of known size the certificate fell by the predicted amount (ratio 1.08) and stayed below the ground-truth fidelity of the damaged batch (0.924 vs 0.931): it detects degradation, not only avoids overclaiming.
3. Validity held although the hardware violates two idealisations measurably: settings were clustered per (job, pair) with 2–3× excess heterogeneity (D2), and errors on simultaneous pairs were mildly correlated (D3). These are empirical results, not covered by the proof.

## Limits (as pre-registered)
Settings per (job, pair), not per pair; test-or-keep drawn after the fact; U is a conservative reference (H3/H4/H6 limited power, H7 adds a ground-truth check); one device over 2.6 days; trusted measurements and compiler; shot order within a job unknown.
