# Study 41b pre-registration: the certificate for GHZ states on IonQ Forte 1 hardware

**Status:** FROZEN (14 Nov 2026) when this file, `job_41b.py`, `make_design_41b.py`, `analyze_41b.py`, `cert.py` and `HASHES_PREREG_41b.txt` are pushed to the public repository, **before the first 41b hardware job**.

## 1. What is new
- Study 41a certified Bell pairs on hardware. 41b extends the certificate to **multi-party entanglement**: three- and four-qubit GHZ states, (|0…0⟩ + |1…1⟩)/√2.
- **The test.** Each state gets one test, chosen in advance:
  - **"Z"** with probability 1/3: all qubits measured in Z; the state passes if all outcomes agree.
  - **An even-#Y string s in {X,Y}ⁿ** with probability (2/3)/2ⁿ⁻¹: the state passes if the outcome parity equals the stabiliser sign (−1)^(#Y/2).
- **Why it works.** Averaged over the test choice, the pass operator is Ω = P_Z/3 + (1/3)(I + |0…0⟩⟨1…1| + h.c.) = I/3 + (2/3)|GHZ⟩⟨GHZ|, because the 2ⁿ⁻¹ signed XY stabilisers average to |0…0⟩⟨1…1| + h.c. So P(fail) = 1 − tr(Ωρ) = (2/3)(1 − F_GHZ) **exactly, for every state ρ, when the test is drawn independently of the state**. This follows from the optimal Pauli-measurement GHZ verification strategy of Li, Han & Zhu, Phys. Rev. Applied 13, 054002 (2020). An independent numerical check (random mixed states, n = 2, 3, 4) agreed to 10⁻¹⁵. It is the same constant as the Bell test, so the frozen `cert.py` (unchanged since Study 27) **certifies GHZ fidelity with no new theory**.
- **Linear estimate:** F = 1 − e_Z/2 − mean over the 2ⁿ⁻¹ XY strings of e_s.
- A certified average fidelity F > 0.5 certifies that the **ensemble of kept states is genuinely multipartite entangled** (the biseparable states form a convex set with GHZ fidelity ≤ 0.5, so not all kept states can be biseparable), assuming trusted measurements.

## 2. Exposure record (before freezing)
- **Study 41a hardware results are known** (Bell pairs: linear F 0.978 on this device). The GHZ thresholds in H5b were set from them together with a local noise model calibrated to that Bell fidelity, which gave GHZ-3 ≈ 0.955 and GHZ-4 ≈ 0.937.
- **Free rehearsals of the frozen `job_41b.py`** on IonQ's Forte-1 noise-model simulator (14 Nov), with outputs verified complete by SHA, design and submitted circuit matching the table, and debiasing off per IonQ's record:
  - Job 0, GHZ-4 (7 groups; id 01a1d82e-467d-7bbf-a9bd-65c8fe361655): Z errors 3.3–4.3 %, XY 2.2–3.9 %.
  - Job 1, GHZ-3 (9 groups; id 01a1d83c-9198-7557-8ba4-31a06e7b3944): Z 1.4–2.6 %, XY 0.9–2.1 %.
- **No GHZ circuit has been run on hardware.** One hardware cost estimate was seen and declined (job 0, GHZ-4: 48.95 credits).
- **Not used:** the Study 40 GHZ code (`study40_ghz/`, written for Oxford's per-qubit random settings, which need thinning). It is not needed here because the test is chosen per state.

## 3. Design (fixed by the design table embedded in `job_41b.py`, derived from seeds by `make_design_41b.py`)
- **20 jobs**, numbered 0–19 and run in number order. The GHZ size per job comes from a seeded random order (seed 41199): sizes 4,3,3,4,3,3,3,4,3,3,4,4,4,4,3,4,3,4,3,4. That makes 10 jobs of GHZ-3 (12 states per shot) and 10 of GHZ-4 (9 states per shot).
- **Per job** (seed 41100 + job):
  - The 36 qubits are randomly partitioned into groups. Each group is prepared as H on its first qubit, then a CX chain.
  - Tests are stratified so every state's test has exactly the marginals of §1:
    - GHZ-3: 4 "Z" tests plus each of the 4 XY strings twice.
    - GHZ-4: 3 "Z" tests plus 6 of the 8 XY strings, drawn without replacement.
  - The tests are then randomly permuted over the groups.
- **1,000 shots per job**, with `error_mitigation = NO_DEBIASING`.

## 4. Running (Tanish, in Qollab)
The same procedure and rules as Study 41a §4:
- **Setup.** Paste `job_41b.py` unchanged and change only `JOB = k`. Keep Qollab's allowance at 1 credit and click OK only if the estimate is ≤ 60 credits (GHZ circuits have more gates; the GHZ-4 estimate seen was 48.95, and in 41a the charge was about 80 % of the estimate). Budget about 800 credits. Keep the tab open until the file is downloaded, and save files to `prx_work/study41b_ionq_forte/raw/`.
- **Duplicates.** If a job number is run twice, the earliest hardware submission with counts is the one used.
- **Lost outputs.** A job whose output is lost (no counts) is kept in `raw/`, set aside and reported with its id; that job number is then re-run.
- **When the analysis runs.** Only once all 20 job numbers are present.
- **Time order** comes from the UUIDv7 submission times.

## 5. Stage 1: gates
- **G0:** frozen hashes; the hash file must list all five frozen files.
- **G1:**
  - The design table equals its seed derivation.
  - All 20 jobs are present, and no job id is shared between different job numbers.
  - Each file's size, groups and tests equal the table.
  - The submitted OpenQASM circuit matches the table gate by gate.
  - 1,000 shots, with positive integer counts.
  - The backend is Forte hardware: IonQ's metadata is present, neither the name nor the metadata says simulator, and no noise model is reported.
  - No debiasing was requested, and IonQ reports no debiasing or other applied mitigation.
  - IonQ's compiled statistics (qubits, gate counts) are logged, not gated.
- **G2:** in every job, each test's error rate is < 0.25 and the linear F is > 0.5.
- If a gate fails, Stage 2 is not run, and any change is made by a dated amendment pushed before re-running.

## 6. Stage 2: hypotheses (each GHZ size analysed separately)
**Method.**
- **Test-or-keep:** each state is labelled "test" with probability p ∈ {0.05, 0.1, 0.2}. Labels are drawn independently as binomial counts per (job, group, fail/pass), with 1,000 seeded draws per p (seeds 61001–62000).
- **Certificate:** Prop. C1 (`cert.py`, α = 0.05).
- **Reference U:** 1 − e_Z,lo/2 − mean_s e_s,lo. Each e is the Clopper–Pearson lower bound on the kept states of that test type, at level 0.025/(1 + 2ⁿ⁻¹) for the final check and 0.025/(1 + 2ⁿ⁻¹)/J at each of the J = 10 job checkpoints.

**Hypotheses.**
- **H3b (primary, validity, final):** a draw violates if the certificate > U. **FAIL if** the CP95 lower bound on the violation rate exceeds 0.05 for any p or size. Prediction: PASS.
- **H4b (primary, anytime):** the same check at each of the 10 job checkpoints per size, in time order. FAIL rule as for H3b. Prediction: PASS.
- **H5b (primary, usefulness):** at p = 0.2, the median certificate is **> 0.90 for GHZ-3** and **> 0.85 for GHZ-4**. Prediction: PASS.
- **H6b (primary, GME of the kept ensemble from one job):** at p = 0.05, the certificate at the first checkpoint (after one job: 12,000 GHZ-3 or 9,000 GHZ-4 states) exceeds 0.5 in **≥ 99 % of draws**, for both sizes. Prediction: PASS.

**Descriptive.**
- **D1:** error rate per test type, the realised number of clusters per test type (GHZ-4: each XY string appears 6–9 times over the 10 jobs, expected 7.5; the pooled test error weights strings by these counts, a bias of order 10⁻⁴ in the implied F), linear F and certificate − F.
- **D2:** clustering (χ²/df per test type) and per-job F.
- **D3:** within-shot independence.
- **D4:** timeline.
- **D5:** 1 − F per CX, compared with 41a's Bell pairs.
- **D6:** certificate path over the checkpoints.

## 7. Limitations (stated in advance)
- **Clustered tests.** Each test is fixed per (job, group), not per state, because Qollab runs one circuit per job. Validity under this clustering is therefore an empirical check, as in 41a.
- **Test-or-keep is drawn after the fact,** and U is a conservative reference. There is no planted fault in 41b. At early GHZ-4 checkpoints U is especially loose, because each job contains only 6 of the 8 XY strings and an absent string enters with lower bound 0, so H4b has little power early on. As in 41a, the FAIL rule (CP95 lower bound > 0.05) tolerates a violation rate up to about 0.075 if both the certificate and U were exactly at their nominal levels; in practice both are conservative.
- **Trusted measurements and compiler.** Readout error is not corrected (`cert.py` with rmax = 0). It counts as state error, which is conservative in aggregate for high-fidelity states but not strictly for every state (a flip can turn a failing outcome into a passing one).
- **Fixed preparation.** The GHZ states are prepared with a CX chain whose qubit order is fixed by the table.
- One device.

## 8. Code
- **Files:**
  - `job_41b.py`: runs in Qollab, with the design table embedded.
  - `make_design_41b.py`: derives the design table from the seeds.
  - `analyze_41b.py`: numpy and scipy only.
  - `cert.py`: identical to Study 41a, sha256/16 6b84bbdd3c10fd36.
- **Before freezing:**
  - The job script was run, as Qollab runs it, against a noiseless Aer simulator: every test had 0 errors, which confirms the stabiliser signs and bit order.
  - The full pipeline was run on 20 noisy Aer jobs (GHZ-3 F 0.955, GHZ-4 F 0.937; all hypotheses as predicted).
  - Gate tests fail as they should for a missing job, a simulator file, an altered circuit, and swapped tests.
  - An independent AI code review (14 Nov) found no critical issues. Its two important findings, both fixed, were the GME wording and the G0 check, which now requires all frozen files to be listed. Its minor findings were also applied: lost jobs reported with their id, the metadata required, realised test counts disclosed, readout wording, and versions logged.
