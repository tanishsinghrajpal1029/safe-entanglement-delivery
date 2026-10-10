# Safe entanglement delivery: label-free risk control and an anytime-valid per-user guard for quantum networks

[![DOI](https://zenodo.org/badge/1413586519.svg)](https://doi.org/10.5281/zenodo.23287414)

Research code, pre-registrations, results and the audit ledger for an independent study at Carnegie Mellon University (Information Networking Institute).

**Author:** Tanish Singh Rajpal.

**Status:** working research repository; a preprint is in preparation. Everything here is **simulation-based** unless stated otherwise. Real-data checks are in `external_checks/`.

## The question
A quantum network cannot measure a delivered entangled pair without destroying it. So how can it promise that at most δ = 1% of the pairs it **delivers** are bad, and that no individual user is left with bad pairs?

## Main components
- **Label-free delivery controller** (`study18c_controller_and_guard/`).
  - It uses only data the network already collects: parity checks on sacrificed pairs, memory waiting times, and a physics model.
  - With a calibrated posterior it holds network-average delivered risk ≤ 1% (Props. 1–2).
- **Per-path guard** (Prop. 6 and its variants): an anytime-valid mixture confidence sequence (Ville's inequality).
  - It guarantees P(a path ever receives a bad pair) ≤ α, including under drift (Props. 6′, 6″) and with declared physics uncertainty.
  - Fault alarms (G6, G7) cut post-fault harm by ~97%, but give no formal guarantee.
- **Learning under the guard** (`study23_ai_rl_guard/`, `study24_ai_v2_hardware/`): a global model learns link quality from neighbours' data and sets the guard's prior.
  - The guarantee holds whatever the model predicts.
  - Thin-data hardware (SiV-like, NV-like) goes from nearly unusable to usable with 0 bad pairs.

## Method: pre-registration
Every confirmatory study was pre-registered before its run: hypotheses, pass bars, a locked analysis script tested on synthetic data, task lists, and code hashes. Failures are kept and reported.
- See `PREREGISTRATION_TIMELINE.md` and `audit/EVIDENCE_LEDGER.md`.
- Each confirmatory output folder (`des_*_psc/`) contains the cluster's own shard metadata, with code and task hashes and start times.

## Layout

| Folder | Contents |
|---|---|
| `study18c_controller_and_guard/` | Discrete-event simulators (`drift_queue_des_*.py`), physics model (`ptm_model.py`, NetSquid cross-checks), pre-registrations (`README_*.md`), locked analyses (`analyze_*.py`), confirmatory outputs (`des_*_psc/`), theory note |
| `study23_ai_rl_guard/` | Global AI model + RL router under the guard (Study 23) |
| `study24_ai_v2_hardware/` | AI v2, five hardware types, unseen correlation patterns, latency, drift carry-over (Study 24) |
| `external_checks/` | Pre-registered reproduction of the Innsbruck 230 m trapped-ion experiment (Zenodo 7031042): Stage 1 (pass) and Stage 2 (count mismatch, reported) |
| `audit/` | Evidence ledger (E1–E89), hardware provenance, novelty map, independent audit scripts |

## Reproducing
- Python 3.9–3.12 with numpy, scipy and pandas; scikit-learn for the AI models.
- Confirmatory runs used PSC Bridges-2 (`psc_array_runner.py`, `s18c_array.sbatch`). Every task is seeded, so results do not depend on how the work is sharded.
- Example:
  ```
  cd study24_ai_v2_hardware
  python3 analyze_24.py A des_s24_psc/runs.csv
  ```
  This reproduces the Study 24 verdicts from the included outputs.

## Data
Third-party datasets are **not** redistributed here; see `DATA_SOURCES.md`.

## AI assistance
Analysis code, simulations and documents were developed with substantial assistance from an AI model (Anthropic's Claude), under the author's direction. Every result was produced by running the code in this repository, and the pre-registration and ledger record what was decided before each run.

## License
- Code: MIT (`LICENSE`).
- Documents and results: CC BY 4.0.

How to cite: `CITATION.cff`. Archived on Zenodo: **doi:10.5281/zenodo.23287414** (all versions; v0.1.0 is doi:10.5281/zenodo.23287415).
