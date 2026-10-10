# Safe entanglement delivery: label-free risk control and an anytime-valid per-user guard for quantum networks

[![DOI](https://zenodo.org/badge/1413586519.svg)](https://doi.org/10.5281/zenodo.23287414)

Research code, pre-registrations, results and the audit trail for an independent study at Carnegie Mellon University (Information Networking Institute).

**Authors:** Tanish Singh Rajpal and Michael Mattarock (Carnegie Mellon University).

**Status (October 2026):** a preprint is in preparation.
- The evidence is mainly **simulation**: a discrete-event network simulator whose physics was cross-checked against NetSquid.
- It is backed by **three pre-registered checks on public experimental data** (Innsbruck, ICFO, USTC).
- One further pre-registered study, Study 25 ("realism"), is in progress.

## The question
A quantum network cannot inspect a delivered entangled pair without destroying it. Using only data the network already collects, can it:
- keep the fraction of **delivered** pairs below a fidelity threshold under a target (δ = 1%), and
- promise that **no individual user** ever receives such a pair, except with a small, chosen probability (α = 5%)?

## Main results

| Result | Evidence |
|---|---|
| **No-go.** Rules with a fixed margin or confidence level cannot hold a target rate of bad *delivered* pairs (Prop. 1). | Theory + simulation |
| **Label-free controller.** With a calibrated posterior, network-average delivered risk ≤ 1% (Prop. 2). It held in 63/63 non-SiV hardware groups. | Studies C1–C2, P1, G1–G3 |
| **Per-user guard.** An anytime-valid mixture confidence sequence per path (Prop. 6, drift variants 6′/6″) guarantees P(a user ever receives a bad pair) ≤ α. | **0 bad pairs in 12.3M (Study 23) and 34.8M (Study 24) guarded deliveries** |
| **Learning under the guard.** A learned prior (AI or linear) enters the guard without affecting the guarantee (Props. 7, 10). | Study 24, all pre-registered tests passed |
| …it rescues thin-data hardware | **SiV-like links: from ~4–5% to ~26–32%** of oracle throughput at 0 bad pairs. **+20 points** on NV/SiV over today's guard. |
| …it gains from correlations | **+11.4 points** from the AI's own correlation learning on thin hardware; +4.4 on patterns never seen in training |
| …but has limits | On data-rich ion hardware learning adds < 0.5 points. A linear model captures most of the gain. |
| **Latency.** End-to-end request-to-delivery latency, reported for every arm. | The guard adds no measurable latency on ion hardware |
| **Faults.** Alarms cut post-fault harm by ~97% (24 vs 793 late bad pairs). No data-driven rule can stop exposure before post-fault data arrive (Prop. 8, a no-go). | G6, G7 |
| **Re-alignment drift.** A safe guard pays 12–20% to restart. Re-use is possible only with a declared bound on re-alignment (Prop. 9, a design rule). | G5, Study 24 Block B; Study 25 Block D in progress |

## Real-data checks (pre-registered; data are not redistributed)

| Dataset | What we found |
|---|---|
| **Innsbruck** 230 m trapped ions (Zenodo 7031042) | Stage 1 reproduced: ion–photon fidelity 0.920 ± 0.004 vs 0.924–0.929 reported. Stage 2: event-count mismatch (581 vs 491), reported. |
| **ICFO** 2021 solid-state memories (Zenodo 6454536) | Reproduced the paper's claims: concurrence falls with storage time and stays positive at 25 µs (6.2σ); two-photon suppression 0.033 vs 0.036(8). The primary visibility estimator **failed**, because the phase settings are not in the data (a request was sent to the authors). **Real drift** in 7 of 11 runs, yet the anytime bound held in 10 of 11. |
| **USTC** 2026 remote ion–ion entanglement (Zenodo 18218281, figure data) | Our memory model predicts the real fidelity decay within error, but is **2–4 points optimistic**. **Real drift** in the error rate (dispersion ×3.6). |

**What the real data imply:** real links drift, and physics models tend to be optimistic. A deployed guard therefore needs its drift-aware form and a **declared physics margin**, about 0.04 in fidelity for the USTC device.

## Theory (summary)
Props. 1–7: `study18c_controller_and_guard/THEORY_NOTE.md` and the project theory notes. Props. 8–10 and the contributions list: `docs/THEORY_NOTE_2026-10-11.md`.

| Prop. | Statement |
|---|---|
| 1 | Base-rate no-go for fixed-margin rules |
| 2 | Calibration controls delivered-pair risk |
| 3 | Identifiability index for the fleet spread (I ≥ 3 is safe) |
| 4 | Finite-window deviation of the threshold |
| 5 | Two fault mechanisms |
| 6 | Anytime-valid per-path guard (6′/6″ handle drift) |
| 7 | A prior helps only through the Occam term |
| 8 | Fault-exposure no-go |
| 9 | Declared re-alignment bound |
| 10 | A prior built from neighbours' data adds no independence assumption beyond the guard's own data model |

## Known limitations
- **No live hardware.** The real-data checks re-analyse published data.
- **The guarantee holds only under the guard's stated assumptions.** It needs a correct or declared-pessimistic physics model, counts that are not over-dispersed (or a declared dispersion), and declared drift or re-alignment bounds.
- **Network model:** a 5 × 5 grid (and single paths). It serves one request at a time, and the classical signalling delay is not modelled in Studies ≤ 24. Study 25 adds parallel requests and signalling delay.

## Method
- **Pre-registration.** Every confirmatory study was pre-registered before its run: hypotheses, pass bars, a locked analysis script tested on synthetic data, task lists and code hashes. Failures are kept and reported.
  - See `PREREGISTRATION_TIMELINE.md` and `audit/EVIDENCE_LEDGER.md` (entries E1–E99).
- **Independent timestamps** (`audit/PREREG_TIMESTAMP_CHECK.md`):
  - for **22 of 22** studies run on PSC Bridges-2, the pre-registration file was on the cluster before the first confirmatory job started;
  - each `des_*_psc/` folder holds the job-written metadata (code hash, task hash, start time);
  - from v0.1.0 on, every release is archived on Zenodo.

## Layout

| Folder | Contents |
|---|---|
| `study18c_controller_and_guard/` | Simulators (`drift_queue_des_*.py`), the physics model (`ptm_model.py` + NetSquid cross-checks), pre-registrations (`README_*.md`), locked analyses, confirmatory outputs (`des_*_psc/`) and the theory note. Studies v5–v21, C1–C2, P1, S1, G1–G7. |
| `study23_ai_rl_guard/` | Global AI model + RL router under the guard (Study 23) |
| `study24_ai_v2_hardware/` | AI v2; five hardware types; unseen correlation patterns; latency; drift carry-over (Study 24) |
| `study25_realism/` | Model error, finite calibration, shared noise, parallel load, declared re-alignment bound (Study 25): 9/9 primary PASS, secondary T3 FAIL; see `RESULTS_25.md` |
| `external_checks/` | `innsbruck_230m/`, `icfo_2021/`, `ustc_2026/`: pre-registrations, code and results |
| `audit/` | Evidence ledger, timestamp check, PSC job history, hardware provenance, novelty map, audit scripts |
| `docs/` | Theory note v4 (Props. 8–10, novelty and contributions) |

## Reproducing
- **Requirements:** Python 3.9–3.12 with numpy, scipy and pandas; scikit-learn for the AI models; openpyxl for the USTC check.
- **Cluster runs:** confirmatory runs used PSC Bridges-2 (`psc_array_runner.py`, `s18c_array.sbatch`). Every task is seeded, so results do not depend on how the work is sharded.
- **Example:** to reproduce the Study 24 verdicts from the included outputs:
  ```
  cd study24_ai_v2_hardware
  python3 analyze_24.py A des_s24_psc/runs.csv
  ```

## Data
Third-party datasets are **not** redistributed here; see `DATA_SOURCES.md` for sources and licences.

## AI assistance
Code, simulations and documents were developed with substantial assistance from an AI model (Anthropic's Claude), under the authors' direction. Every result comes from running the code in this repository. The pre-registrations and the ledger record what was decided before each run.

## License and citation
- Code: MIT (`LICENSE`). Documents and results: CC BY 4.0.
- Cite via `CITATION.cff`. Zenodo: **doi:10.5281/zenodo.23287414** (all versions).
