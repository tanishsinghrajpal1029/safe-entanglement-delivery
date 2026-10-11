# Study 31: test-or-keep on a real quantum processor (pre-registration, 11 Oct 2026)

**Status:** locked. Commit this folder publicly before the hardware run.

## Why
The manuscript's certificate (Prop. C1) and model check (Prop. MC) have only been tested in simulation, and no public dataset randomises test-or-keep per pair. On a quantum processor both qubits of a pair are local. So a kept pair can be measured in the Bell basis, which gives an approximate ground-truth label to check the certificate against.

## Design (`ibm_testkeep.py`; one job; seeded schedule, sha recorded in the output)
- **Delivered pairs:** each pair is one shot of a two-qubit circuit that prepares Φ⁺ (good) or Ψ⁻ (bad, injected).
- **Pre-drawn schedule** (seed 31031):
  - **Phase 0:** 600 pairs, all tested in a random X/Y/Z basis. This gives the declared fidelity F_decl, a one-sided 95% Clopper–Pearson lower bound via Lemma F.
  - **Phase A:** 1,000 pairs, test fraction p = 0.2, no injection.
  - **Phase B:** 2,300 pairs, p = 0.2, with Ψ⁻ injected with probability 0.20. This is an unannounced source degradation, i.e. a "model error".
- **Kept pairs:** measured in the Bell basis (CX, H, measure; "00" means Φ⁺). The Bell-measured pass fraction is the approximate truth. Its own error biases it low, which makes the validity check stricter.
- **Certificate:** Prop. C1 (`cert.py`, 8-λ grid) at p = 0.2, α = 0.05, with a declared parity-flip bound of 0.05. It is updated after every kept pair in A and B.
- **Model check:** Prop. MC (`mcheck.py`), β = 0.05, null q = (2/3)(1 − F_decl), on the tests in A and B.
- **Budget:** 3,900 shots in one job, under a hard cap of 4,000 shots; `max_execution_time` = 120 s.

## Hypotheses (single run; binary)

| | Hypothesis | Passes if | Expected |
|---|---|---|---|
| W1 | The certificate stays valid | The certificate is never above the Bell-measured pass fraction of the kept pairs, at any kept pair | Yes |
| W2 | No false alarm | No model-check alarm in phase A | Yes |
| W3 | Detection | A model-check alarm occurs in phase B | Yes |
| W4 | Descriptive | Report F̂ and F_decl, the final certificate, Bell pass fractions in A and B, QPU usage, backend and layout | — |

**Simulation power check** (numpy model with 6% depolarising and 1.5% readout; 60 seeded runs; not evidence):
- W1 held in 60/60 runs.
- Alarm in phase A: 0/60.
- Alarm in phase B: 59/60.

The design (phase sizes, injection rate 0.20, readout bound 0.05) was chosen with these simulations before any hardware data.

## Commitment and limits
- **Run order:** the `--aer` dry run (local, free) comes first, then one hardware job. The hardware output is reported whatever it shows.
- **Approximate truth:** the Bell measurement on hardware has its own error.
- **Small scale:** this is one job on one device, with an injected degradation. It tests the protocol and the statistics, not a network.
- **Not tested:** the "pairs" are not distributed over distance, so this does not test the network's own physics.

## Files
- `ibm_testkeep.py`, `cert.py` (6b84bbdd, unchanged), `mcheck.py` (a05f0822, unchanged).
- Simulation dry run: `sim_result.json`, `sim_summary.txt`.
