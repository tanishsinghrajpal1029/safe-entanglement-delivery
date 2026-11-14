# Study 41b: the certificate for GHZ-3 and GHZ-4 states on IonQ Forte 1 (pre-registered)

Extends Study 41a (`../ionq_forte_hw_2026/`) from Bell pairs to three- and four-qubit GHZ states. See `PREREG_41b.md`.

- `job_41b.py`: the script run in the Qollab Playground (one job per run; change only `JOB = k`, k = 0..19).
- `make_design_41b.py`: derives the design table (embedded in `job_41b.py`) from the seeds.
- `analyze_41b.py`: `python analyze_41b.py --raw RAW_DIR --stage 1`, then `--stage 2` (numpy + scipy; no Qiskit).
- `cert.py`: the certificate (unchanged since Study 27; identical to 41a's).
- `HASHES_PREREG_41b.txt`: frozen sha256 of the files above (checked by the analysis, gate G0).
- `tests/`: local simulator helpers used before freezing.

Status: frozen before the first 41b hardware job. Results will be added here whatever they are.
