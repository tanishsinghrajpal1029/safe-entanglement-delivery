# Study 31b: hardware rerun with the hybrid model check (pre-registration, 11 Oct 2026)

**Status:** locked. Commit and push this folder publicly **before** the hardware job.

## Why
Study 31 ran on IBM hardware (ibm_fez) and found:
- the certificate was valid (W1 PASS);
- there was no false alarm (W2 PASS);
- **the fixed-bet model check missed the injected degradation (W3 FAIL).**

The cause was a deficit: the conservative declared fidelity let log-wealth fall to −3.75 before the change. Study 30's theory (THEORY_30.md, Prop. D) adds a plug-in e-process with limited debt and a hybrid check (the average of the mixture and the plug-in).

A post hoc replay of Study 31's outcomes with the hybrid check alarmed in phase B. That replay is not evidence, because the bet rule was written after Study 31's summary rates had been seen. Study 31b tests the frozen rule on fresh hardware data.

## Design (`ibm_testkeep_31b.py`)
Same as Study 31 except:
1. **Fresh schedule seed:** 31032 (schedule sha 3bfbc93611f01b96; 3,900 shots; 467 Ψ⁻ pairs in phase B).
2. **Primary check:** `core30.HybridCheck` (frozen in core30.py, sha 9091e3364b19fe56), β = 0.05, same null q = (2/3)(1 − F_decl).
   - Study 31's mixture check runs on the same outcomes as a paired comparison.
3. **Offset bound after the alarm (Theorem 2 machinery).** After the first hybrid alarm, `core30.OffsetCS` runs on the post-alarm tests.
   - Settings: level 0.025, constant class, no declared maximum (U starts at 1).
   - a_i = F_decl − 1 + 1.5 E_i.

Unchanged from Study 31 (`ibm_testkeep.py` 3b94867c13068e85 is imported, not edited):
- phases: 600 calibration pairs; A with 1,000 pairs at p = 0.2; B with 2,300 pairs and Ψ⁻ at 0.20;
- certificate C1 (`cert.py` 6b84bbdd), with α = 0.05 and readout bound 0.05;
- Bell-basis truth for kept pairs;
- one job, ≤ 4,000 shots, `max_execution_time` 120 s (Study 31 used 3 s of QPU).

## Hypotheses (single run)

| | Tier | Hypothesis | Passes if |
|---|---|---|---|
| W1 | primary | The certificate stays valid | The certificate is never above the Bell-measured pass fraction of kept pairs |
| W2 | primary | No false alarm | No hybrid alarm in phase A |
| W3 | primary | Detection | A hybrid alarm in phase B |
| W5 | secondary | The post-alarm offset bound covers | U_final ≥ F_decl − (Bell pass fraction of kept pairs after the alarm). Not scored if there is no alarm |
| W6 | descriptive | — | Paired mixture alarm; alarm positions; U trace; F_decl; Bell pass fractions; QPU usage; backend and layout |

## Power (simulation; not evidence)
- **numpy model** (6% depolarising, 1.5% readout; 60 runs each):
  - W1, W2, W3 and W5: 60/60 at each calibration noise level tried.
  - Calibration error 5.7% / 7.2% / 8.5%: the mixture alarmed in B in 59 / 56 / 36 of 60 runs.
- **At Study 31's observed hardware rates** (q = 0.0915; 205 A-tests at 5.8%, 472 B-tests at 15.5%; 1,000 runs):
  - P(alarm in A): 0.2% for both checks.
  - **P(alarm in B): hybrid 78.9%, mixture 44.7%.**
  - So even if the hybrid behaves exactly as designed, **W3 can fail with probability about 21%**. This is stated before the run.

The design is kept identical to Study 31 so that the only change is the check (a paired comparison). Raising phase B for more power was considered and rejected for that reason.

## Commitment and limits
- **Run order:** the `--aer` dry run (local, free) first, then one hardware job. The output is reported whatever it shows.
- **Limits:**
  - Lemma A (W5) assumes symmetric, state-independent readout.
  - The Bell-basis truth has its own error, which biases the "true offset" up, making W5 stricter.
  - This is one job on one device.

## Files
- `ibm_testkeep_31b.py`
- `ibm_testkeep.py`, `cert.py`, `mcheck.py`: unchanged from Study 31
- `core30.py`: frozen, Study 30
- `power31b.py`, `power31b.txt`, `sim_default.json`
- `HASHES.txt`
