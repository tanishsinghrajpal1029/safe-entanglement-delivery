# Study 31b: hardware rerun with the hybrid model check, results (11 Oct 2026)

## What was run
- **Pre-registration:** `README_31b.md`, `ibm_testkeep_31b.py` 29c96b3f259a9e24 (seed 31032; schedule sha 3bfbc93611f01b96).
  - Commit `3520391`, committed at 19:37:59 UTC and pushed (origin/main = 3520391). Confirm the push time from GitHub's activity view.
- **Aer dry run** (local, fake_brisbane): result file written at 19:38:26 UTC.
- **Hardware:** ibm_fez, job db5ubf04qg6s73c40k20, **3 s QPU**, wall time 15.9 s, layout [0, 1]. Result file written at 19:38:50 UTC, 51 s after the commit.
- **Reproduced:** re-running the locked `analyse()` on the saved outcomes in the cloud gives identical values (hardware and Aer).

## Verdicts (hardware)

| | Tier | Result | Numbers |
|---|---|---|---|
| W1 | primary | **PASS** | The certificate was never above the Bell pass fraction. Final 0.6526 against 0.8403; max(cert − truth) = −0.139 |
| W2 | primary | **PASS** | No hybrid alarm in phase A (205 tests) |
| W3 | primary | **PASS** | Hybrid alarm in phase B, at test 170 of 472 |
| W5 | secondary | **PASS** | After the alarm, the offset bound U = 0.312 (302 tests) is ≥ the Bell-measured offset 0.099 of the 1,118 kept pairs after the alarm |

**W6 (descriptive)**
- Calibration: F_decl = 0.8851 (35 errors in 600 tests); q = 0.0766.
- Test error rates in phases 0 / A / B: 5.8% / 4.9% / 19.5%.
- Bell pass fraction: 0.972 in A, 0.783 in B.
- Paired mixture check (Study 31's): it also fell into deficit in phase A (log-wealth −3.37 at the end of A, minimum −3.60), and **alarmed at phase-B test 214**.
- The plug-in alone (exploratory, not pre-registered) would have alarmed at test 166.

**Aer dry run (fake_brisbane):** W1–W3 and W5 all pass. Hybrid alarm at B-test 188, mixture at 261; U = 0.310 against an offset of 0.100.

## What it shows
1. **The hybrid check detects on real hardware.** Taken with Study 31's W3 failure, the pre-registered fix now works on the device where the original failed.
2. **This run shows earlier detection, not a rescue.** The mixture also recovered and alarmed, 44 tests later. The phase-B excess was larger than in Study 31 (error 19.5% against 15.5%) and the debt was similar (−3.37 against −3.75).
   - The pre-registered power at Study 31's rates was 79% for the hybrid and 45% for the mixture, so a single run cannot separate them.
3. **The post-alarm offset bound is valid on hardware but loose:** about 3× the offset, after 302 tests. This is the price of a model-free, time-uniform bound at small samples.
4. **The certificate is valid in a second independent hardware run.**

## Limits
- This is one job on one device; the pairs are not distributed over distance.
- The Bell-basis truth has its own error.
- Lemma A assumes symmetric readout.
- 31b is n = 1 per check: it is evidence of feasibility, not of a power difference.
