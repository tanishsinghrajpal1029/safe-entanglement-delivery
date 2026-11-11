# Study 41a: the certificate run end to end on IonQ Forte 1 (pre-registered)

Bell pairs on a cloud QPU with settings fixed in advance, plus a planted fault of known size. See `PREREG_41a.md`.

- `job_41a.py`: the script run in the Qollab Playground (one job per run; change only `JOB = k`, k = 0..29).
- `make_design_41a.py`: derives the design table (embedded in `job_41a.py`) from the seeds.
- `analyze_41a.py`: `python analyze_41a.py --raw RAW_DIR --stage 1`, then `--stage 2` (numpy + scipy; no Qiskit).
- `cert.py`: the certificate (unchanged since Study 27).
- `HASHES_PREREG_41a.txt`: frozen sha256 of the files above (checked by the analysis, gate G0).
- `tests/`: synthetic and simulator tests used before freezing.

Status: frozen before the first hardware job. Results will be added here whatever they are.
