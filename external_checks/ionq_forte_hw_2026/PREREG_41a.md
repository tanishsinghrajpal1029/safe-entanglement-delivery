# Study 41a pre-registration: the certificate on IonQ Forte 1 hardware, settings fixed in advance

**Status:** FROZEN (11 Nov 2026) when this file, `job_41a.py`, `make_design_41a.py`, `analyze_41a.py`, `cert.py` and `HASHES_PREREG_41a.txt` are pushed to the public repository, **before the first hardware job**.

## 1. What is new
Studies 36–39 re-analysed other groups' data. Here the protocol is run by us on a cloud QPU: IonQ Forte 1, 36 qubits, using Qollab credits.
- Every measurement setting is in a design table pushed before the run.
- A planted fault of known size (Block B) checks that the certificate **drops** when the delivered pairs are worse, not only that it stays valid.

## 2. Exposure record (before freezing)
- **Free tests on the IonQ Forte 1 noise-model simulator (10 Nov):**
  - Qollab returns counts only, with no shot order.
  - One circuit per job and one job per run; Qollab calls `main()` itself.
  - Job IDs are UUIDv7, with the submission time in ms.
  - One 14-pair circuit gave linear F(Φ⁺) ≈ 0.985 under the noise model.
- **Free rehearsal of an earlier version of `job_41a.py`** (11 Nov, job 01a1c80a-e2e7-…, 12 pairs):
  - `NO_DEBIASING` was accepted and the download was offered.
  - The design was reproduced exactly by our local code (Qollab NumPy 2.4.6 vs local 2.5.3).
  - Faulty X/Y pairs had 0.14–0.15 error; all others ≤ 0.012.
  - Qollab cannot read its own `main.py`.
- **Free rehearsal of the frozen `job_41a.py`** (11 Nov, job 01a1c91c-ee67-7de4-9c01-9805fd523f31, 12 pairs):
  - The downloaded file was byte-identical to the console output (SHA ff536560020350f6).
  - IonQ's own job record shows `debiasing: false`, backend `simulator`, noise model `forte-1`.
  - Faulty X/Y pairs had 0.14–0.15 error; faulty Z pairs and clean pairs about 0.01.
  - **Recovery by job id is not possible through Qollab**: `retrieve_job` returned 404 "Job not found" for this simulator job, and nothing was submitted.
- **Cost:** Qollab estimates for an 18-pair circuit (declined) were 33.53 credits at 100 shots and 36.90 at 1,000.
- **No hardware job has been run.**

## 3. Design (fixed by the design table embedded in `job_41a.py`, derived from seeds by `make_design_41a.py`)
- **Jobs:** 30, numbered 0–29 and run in number order.
  - **Block B** = jobs {0, 1, 2, 7, 8, 9, 18, 21, 23, 29} (seed 41999).
  - **Block A** = the other 20.
- **Each job:** one circuit of **18 Bell pairs Φ⁺ = (|00⟩+|11⟩)/√2** (H, CX) on 36 qubits.
  - 1,000 shots.
  - `error_mitigation = NO_DEBIASING`: raw device, no symmetrisation.
- **Settings per job** (seed 41000 + job):
  - A random pairing of the 36 qubits.
  - 18 measurement axes, randomly arranged as 6 X, 6 Y, 6 Z.
  - X is measured via H and Y via S†H, on both qubits.
- **Block B fault:** in each axis group, 2 of the 6 pairs get Rz(+π/4) or Rz(−π/4) (one of each sign) on the pair's first qubit after the CX.
  - For Bell-diagonal native noise (readout flips included), X and Y errors rise by exactly (1 − 2e)·sin²(π/8), where e is the native error; Z is unchanged.
  - A native coherent phase shared by the two pairs of opposite sign cancels at first order.
  - Phases that differ between pairs cancel only on average, so H7's tolerance is wide.
- **Error convention (Φ⁺):** XX and ZZ outcomes that differ, and YY outcomes that agree, are errors.
- **Bit order:** a key's rightmost character is qubit 0.

## 4. Running (Tanish, in Qollab)
- **Allowance:** Qollab's confirmation allowance is set to **40 credits**, i.e. one job. If a hardware estimate exceeds 45 credits, stop and report; do not run.
- **Procedure:**
  - Paste `job_41a.py` unchanged as `main.py`.
  - Change only `JOB = k`, run once per k, and keep the downloaded `s41a_job_kk.json`. The same JSON is also printed in the console.
  - The script refuses any backend whose name contains neither "simulator" nor "forte", and submits nothing.
- **Rules fixed in advance:**
  - The job ID is printed right after submission.
  - The Qollab tab stays open until the job's file is downloaded.
  - If the output is lost, recovery is attempted with the same script (`RECOVER = "<job id>"`, same `JOB`, nothing new submitted); a recovered output counts as that job. Recovery failed in testing (§2), so in practice a lost output means the number is **re-run**, and the lost job is reported with its id.
  - Per job number, the analysis uses the **earliest hardware submission (UUIDv7 time) that has counts**.
  - Simulator rehearsals, failed and malformed files are set aside and listed.
  - The analysis runs only when all 30 numbers are present.
  - Time order of checkpoints = UUIDv7 submission time.

## 5. Stage 1: gates (`--stage 1`)
- **G0:** `job_41a.py`, `make_design_41a.py`, `analyze_41a.py` and `cert.py` are identical to the frozen hashes.
- **G1 (integrity):**
  - The design table equals its seed derivation.
  - All 30 jobs are present.
  - No job id is shared by different job numbers.
  - Each file's block, axes, pairing and faulty positions/signs equal the table.
  - The **circuit actually submitted** (OpenQASM 2, recorded in the job file) equals the prescribed circuit gate by gate.
  - Shots = 1,000, with positive integer counts summing to 1,000.
  - Keys fit 36 bits.
  - The backend name contains "forte" and neither the name nor IonQ's target says simulator.
  - No debiasing was requested, and IonQ's metadata, where reported, does not show debiasing on.
- **G2 (conventions, per job):** in every job, the clean pairs' error rate in each basis is < 0.25 and the linear F > 0.5.
- **If a gate fails,** Stage 2 is not run. We report and diagnose, and any change is a dated amendment pushed before re-running.

## 6. Stage 2: hypotheses (`--stage 2`)
**Test-or-keep:**
- Each pair outcome is labelled "test" with probability p ∈ {0.05, 0.1, 0.2}, independently. This is drawn as binomial counts per (job, pair, error/no error), which is equivalent because every statistic depends only on those counts.
- 1,000 seeded draws per p (seeds 51001–52000).
- **Certificate:** Prop. C1 (`cert.py`, α = 0.05) on cumulative test errors and kept pairs.
- **Reference:** U = 1 − ½ Σ_B CP_lower(e_B of kept pairs), at level 0.025/3 (final) and 0.025/3/J at each of the J job checkpoints.

**Hypotheses:**
- **H3 (primary, validity, Block A):** a draw violates if the final certificate > U. **FAIL if** in any p the CP95 lower bound on the violation rate > 0.05. Prediction: PASS.
- **H4 (primary, anytime, Block A):** the running certificate vs running U after each of the 20 jobs, in time order. A draw violates if any checkpoint exceeds. FAIL rule as in H3. Prediction: PASS.
- **H5 (primary, usefulness, Block A):** median final certificate at p = 0.2 **> 0.9**. Prediction: PASS.
- **H6 (primary, validity under a planted fault, Block B):** H3 and H4 applied to Block B (10 checkpoints). Prediction: PASS.
- **H7 (primary, power against a known fault):**
  - Predicted drop Δ = ½·f·sin²(π/8)·[(1 − 2e_X) + (1 − 2e_Y)], with f = 1/3 faulty pairs and e from Block A.
  - Observed: median certificate (p = 0.2) of Block A minus that of Block B.
  - **PASS if the ratio observed/predicted is in [0.5, 1.5].** Prediction: PASS.
  - Expected ≈ 1.05–1.1 when phases are uniform, because Block B has half the pairs and so a wider finite-sample gap. Pair-to-pair differences in native phase can move the ratio by about ±0.3 (synthetic tests).

**Descriptive (D1–D7):**
- **D1:** error rates by basis for A, B-clean, B-faulty (vs predicted) and B-faulty split by the sign of the planted phase; F for A and B; certificate minus F; the Block B certificate vs F_A − Δ.
- **D2:** extra heterogeneity across (job, pair) clusters (χ²/df per basis); per-job F for Block A and for Block B's clean pairs (drift check, since Block B includes the first three jobs).
- **D3:** within-shot independence (variance ratio of errors per shot; mean pairwise error correlation).
- **D4:** timeline, backend, versions.
- **D5:** per logical qubit (the compiler may map logical qubits to different ions per job).
- **D6:** certificate path over the 20 checkpoints.
- **D7:** hardware vs simulator F.

## 7. Limitations (stated in advance)
- **One basis per (job, pair), not per pair.** Qollab runs one circuit per job, so all 1,000 shots of a pair in a job share its axis. The axis is drawn independently of the fixed circuit, so the mean test error is unbiased over the design. But the clustering is **not covered by the proof**, which assumes a fresh, independent basis for every pair. The effective randomisation is over 360 (Block A) and 180 (Block B) clusters. H3/H4/H6 are therefore empirical checks of validity under this clustering, and D2 reports its size. Clustering also weakens the Clopper–Pearson coverage of U.
- **Test-or-keep is drawn after the fact:** every pair is measured, as in Studies 37–39. U is a reference, not the true fidelity, so H3/H4/H6 have limited power. H7 adds a check against a known planted fault.
- **Shot order within a job is unknown;** the anytime check has job resolution (18,000 pair outcomes per checkpoint).
- **Trusted measurements:** readout error counts as pair error, which makes the certificate conservative. The IonQ compiler is trusted.
- One device and one session; IonQ's queue decides the timing.

## 8. Code
- **Files:**
  - `job_41a.py`: runs in Qollab, with the design table embedded.
  - `make_design_41a.py`: derives the table from the seeds.
  - `analyze_41a.py`: our code; numpy and scipy, no Qiskit needed.
  - `cert.py`: unchanged since Study 27, sha256/16 6b84bbdd3c10fd36.
- The test switch `S41A_TEST_SMALL` (100 draws) is never set for the real run, and the output states whether it is.
- **Tests before freezing:**
  - The job script was run, as Qollab runs it, against noiseless and noisy local Aer simulators. Clean pairs had zero errors; faulty X/Y pairs were 0.12–0.16 vs 0.146 expected. The full pipeline gave H7 ≈ 1.07.
  - Fake-backend safety tests:
    - A generic backend name submits nothing.
    - A wrong qubit count no longer changes the circuit.
    - A failed result still prints the job id and the output.
    - Recovery works without submitting.
  - Gate tests that fail as they should: a missing job, a simulator file, an altered submitted circuit.
  - An independent AI code review (11 Nov) found two critical issues: the circuit size could change if IonQ misreported the qubit count, and nothing was printed between submission and the end. Both are fixed, along with six important issues (frozen design table, set-aside rules, metadata checks, per-job G2, reworded limitations) and minor ones.

**Results** will be reported in full whatever they are, with the first output preserved verbatim.
