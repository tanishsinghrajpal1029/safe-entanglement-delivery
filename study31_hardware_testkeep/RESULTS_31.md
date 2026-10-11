# Study 31: test-or-keep on a real quantum processor (results, 11 Oct 2026)

## Run
- **Hardware:** IBM `ibm_fez`, job `db5s7lamb58s738aufbg`, one job of 3,900 shots, physical qubits [0, 1]. 3 s of QPU usage (cap 120 s).
- **Code:** `ibm_testkeep.py` 3b94867c13068e85; schedule sha b8db2032104754d0 (seed 31031).
- **Dry run:** a local Aer simulation of the fake Brisbane device was run first (`aer_result.json`).
- **Timing:** pre-registration commit `b51306a` at 16:58:36 UTC; the result files were written at about 17:13–17:14 UTC, so the commit came about 15 min before the job. The push time is still for the user to confirm on GitHub.

## Verdicts (pre-registered, single run): 2 of 3 PASS, W3 FAIL

| | Hypothesis | Result | Numbers |
|---|---|---|---|
| **W1** | The certificate stays valid | **PASS** | The certificate was never above the Bell-measured pass fraction of the kept pairs. Final certificate 0.710 against a Bell pass fraction of 0.852 (largest certificate − truth: −0.133) |
| **W2** | No false alarm in phase A | **PASS** | No alarm in 206 phase-A tests |
| **W3** | Alarm in phase B | **FAIL** | No alarm. Peak log-wealth 2.71, below the threshold of 3.49 |
| W4 | Descriptive | — | See below |

**W4 (descriptive)**
- **Calibration:** F̂ = 0.8925 from the 600 calibration tests (43 errors), giving F_decl = 0.8628 and null bound q = 0.0915.
- **Bell pass fraction of kept pairs:** 0.967 in phase A, 0.803 in phase B.
- **Test error rates:**
  - phase 0: 7.2%;
  - phase A: 5.8%;
  - phase B: 15.5%. Injected Ψ⁻ pairs erred in 97% of X and Z tests and 0% of Y tests, as Lemma F predicts for Ψ⁻.
- **Aer dry run:** W1 PASS; the alarm fired in phase B (peak log-wealth 4.98).

## Why W3 failed (exploratory)
- **The e-process lost wealth before the change.** In phase A the good pairs erred less often (5.8%) than in calibration (7.2%). The declared bound F_decl was therefore conservative, so q sat above the true error rate. The log-wealth fell to −3.75 by the end of phase A.
- **The excess in phase B was not enough to recover.** Phase B's excess of about +0.064 over 457 tests lifted the log-wealth by about +6.4, to a peak of 2.71. The alarm needed 3.49.
- **This is the "slack before a change point" effect** that THEORY_28 and the review (m1) warned about: a check that starts from a conservative null pays a detection delay after an unannounced change. The aer dry run, with different noise, crossed the threshold.
- **No re-analysis, re-tuning or re-run changes this verdict.**

## Possible follow-up (not run)
- **What it would test:** a change-detection version of the check (an e-detector: a sum of e-processes restarted at every test, Shiryaev–Roberts style) does not accumulate pre-change debt. Its false-alarm control is in average run length rather than a probability bound.
- **How:** it would need its own pre-registration and a fresh schedule seed. It would use about 3 s of the remaining QPU budget.

## What it means for the paper
- **First hardware test:** this is the first test of the test-or-keep certificate on hardware, and the certificate behaved as the theorem says (W1).
- **The model check missed:** it did not catch a 20% injection of bad pairs within 457 tests on real hardware, because the conservative calibration left a pre-change deficit.
- **Both points are reported.**

## Limits
- One job on one device.
- The "truth" comes from the device's own Bell measurement, which has its own error.
- The pairs are local, not distributed over distance.
