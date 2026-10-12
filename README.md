# Certifying delivered entanglement: per-pair guarantees need a model, averages do not

[![DOI](https://zenodo.org/badge/1413586519.svg)](https://doi.org/10.5281/zenodo.23287414)

Code, pre-registrations, results and the audit trail for the manuscript of the same title. The work is an independent study at Carnegie Mellon University (Information Networking Institute). The repository was formerly titled "Safe entanglement delivery".

**Authors:** Tanish Singh Rajpal and Michael Mattarock (Carnegie Mellon University).

**Status (October 2026):** the manuscript is in preparation.
- The evidence is mainly **simulation**: a discrete-event network simulator whose physics was cross-checked against NetSquid.
- **Three pre-registered re-analyses of public experimental data** back it up: Innsbruck, ICFO and USTC.
- **Two pre-registered hardware runs on an IBM quantum processor** (Studies 31 and 31b): test-or-keep with Bell-basis ground truth.
- The final studies are Study 26 (model-based layer at measured hardware levels), Study 27 (model-free certificate), Studies 28–29 (model check and heuristic response), Study 30 (provable closed loop), Studies 31/31b (hardware), Study 32 (recovering bound and robustness), Study 33 (fixed-K computation) and Study 34 (closed loop on larger grids). Every study except Study 33, a computation, was pre-registered and committed publicly before its first confirmatory job.

## The question
A quantum network cannot inspect a delivered entangled pair without destroying it. So what can a user actually be guaranteed about the pairs they receive, and what does each kind of guarantee cost?

## Main results (manuscript v0.6)

| Result | Evidence |
|---|---|
| **No-go (Prop. N).** No rule that relies only on test outcomes (no model) can certify that each kept pair clears a fidelity threshold. At test fraction p = 0.1 it wrongly certifies with probability ≥ 0.93 − α, while ≥ 59% of runs contain a bad kept pair. Fixed-confidence filters also cannot hold a target bad-pair rate (base-rate lemma). | Theory |
| **Model-based layer.** An anytime-valid mixture confidence sequence on each link's calibration counts, at level α/U_max over every link the user could be routed on. Under its model assumptions it bounds P(user ever receives a bad pair) ≤ α (Theorem 1). Learned priors keep validity if they are independent of the link's own data (Lemma B). | 0 bad pairs in 12.3M (Study 23) and 34.8M (Study 24) guarded deliveries; Study 26: 0 of 91,392 users |
| **…its failure modes at measured hardware levels** | Study 26: undeclared over-dispersion or model optimism breaks the guarantee. Declaring them from calibration data restores it, at a throughput cost set by calibration precision. **Persistent (slowly varying) noise broke the safety bar of every model-based arm**, including one told the true per-epoch level. |
| **Model-free layer.** Random X/Y/Z tests hidden from the network give an anytime-valid lower bound on the fraction of kept pairs that would pass a Φ⁺ test. That fraction is the average fidelity when pairs are not entangled with each other. The construction is standard; we use it as a component. | Study 27: wrong for 0–0.33% of eligible users (α = 5%), including where the model-based layer failed |
| **…but it sees only averages** | Under undeclared model optimism (64 networks), 25% of delivered pairs were below threshold, while the certified kept-pair average was 0.888 (true value 0.926) |
| **Cost.** No model-free certifier can certify 0.9 from perfect pairs with fewer than 330 kept pairs (p = 0.1; converse, Prop. LB); ours needs 678, so the factor of about 2 is the price of anytime validity. Certifying 0.9 needs 315–1,404 kept pairs per user even from perfect pairs (p = 0.2 to 0.05), and about 850–3,900 for pairs of fidelity 0.97. Thin (NV/SiV-like) hardware could not reach a useful certificate within 45 simulated minutes. | Prop. C1 resource curve; Study 27; converse Prop. LB |
| **Model check (Study 28).** The same tests check the guard's own validity condition with an e-process (Prop. MC: false alarms ≤ β). After an alarm, the declared margin is raised. | Ion networks with undeclared model error: detected in 128/128 networks, with 70–92% fewer bad pairs; false alarms 0.29%. **H4 FAILED:** in one network an alarm after 8 tests raised the margin too little, so 0.8% of post-alarm pairs were bad (bar 1%). Harm is limited, not prevented; the check is blind to sparse failures and thin hardware (as predicted). |
| **Network-wide guarantee (Cor. NW).** Link confidence sequences at α/\|E\| give P(any user ever receives a bad pair) ≤ α. | Study 28: 0/128 networks with a bad pair; cost 0.5 points on ions, 2.4 on SiV |
| **Margin response (Study 29).** After an alarm, the margin tracks an exact upper bound on the model offset, estimated from post-alarm tests and probe tests of blocked pairs; it can come back down. | 0 bad pairs in 5.8M post-alarm deliveries, including Study 28's failure case (0/128 vs 127/128); margin within +0.006–0.011 of the true offset; throughput 0.78 of oracle vs 0.48 (Study 28) and 0.35–0.53 (tomography). 6/6 primary PASS |
| **Caveat on Studies 28–29** | Those simulations added the model offset to the model, which let model fidelities exceed 1 and **inflated detection power** (ledger E134). Study 30 re-tests the loop with the offset in the true state. |
| **Provable closed loop (Theorem 2; Study 30).** After an alarm, the margin is a time-uniform upper confidence bound on the model offset, built from the users' own tests; P(user gets a bad pair after the first alarm) ≤ α + α_hi + α′ for offsets of a declared shape. Run from t = 0 (Corollary 3) it covers every pair. | Study 30 (8,384 runs, offset in the true state): 5/5 primary PASS. 230 of 89,585 users bad after an alarm (bound 0.6%; all from 2 runs, one a false alarm before onset); forced early alarm 0/384; always-on margin 0 of 208,896 users. **Detection is the bottleneck:** whole-run per-user risk at offset 0.044 falls only from 0.53 to 0.47–0.49. |
| **A bound that can recover (Study 32).** The offset bound need not be a running minimum (Remark R). | 6/6 primary PASS: same guarantee, cost −0.3 points; after a forced miscoverage it recovered in 128/128 runs (median 502 tests) vs 0/128; robust at τ 0.85/0.92 and with less calibration data; thin hardware never alarms. |
| **Hardware (Studies 31, 31b; IBM ibm_fez).** | Certificate valid in both runs. Study 31: the fixed-bet check missed an injected degradation (deficit before the change; W3 FAIL). Study 31b (fresh seed, hybrid check, Prop. D): alarm at test 170 of 472 (fixed-bet check: 214); post-alarm offset bound valid but about 3× loose. |
| **Fixed-K vs anytime (S33, computation).** | A single bet planned for K and F needs 870/420/195 kept pairs to certify 0.9 (p = 0.05/0.1/0.2), 1.2–1.4× the converse floor; the anytime certificate needs about 1.6× that. |
| **Scale (G3, Study 34).** | The anytime guard on a 30 × 30 grid (900 nodes, 1,740 links): 0 bad pairs in about 2.1 M deliveries (exact model, stationary links). Study 34: the provable closed loop on 10 × 10 and 30 × 30 grids: 0 of 4.2 M post-alarm pairs bad, always-on 0 of 7.8 M; detection depends on test volume, not grid size. 3/3 primary PASS. |
| **Earlier results (Studies ≤ 25)** | Label-free risk controller, learned priors on thin hardware, latency, faults (a fault-exposure no-go), re-alignment drift. See the study folders and the theory notes. |

## Real-data checks (pre-registered; data are not redistributed)

| Dataset | What we found |
|---|---|
| **Innsbruck** 230 m trapped ions (Zenodo 7031042) | Stage 1 reproduced the ion–photon fidelity: 0.920 ± 0.004, against 0.924 in the authors' repository (0.929 in the paper). Stage 2: event-count mismatch (581 vs 491), reported. **Stage 3: a model-free certificate F ≥ 0.887 at 95%** (point estimate 0.914). Stage 3 is not blind: the counts had been seen in Stage 1, so only the method was fixed in advance. |
| **ICFO** 2021 solid-state memories (Zenodo 6454536) | Reproduced the paper's claims: concurrence falls with storage time and stays positive at 25 µs (6.2σ); two-photon suppression 0.033 vs 0.036(8). The primary visibility estimator **failed**, because the phase settings are not in the data. The echo probability per herald is over-dispersed in 7 of 11 runs (5 of 11 after Bonferroni). |
| **USTC** 2026 remote ion–ion entanglement (Liu et al., Nature 2026; Zenodo 18218281, figure data) | Point estimates of our memory model are 2–4 fidelity points optimistic at all four storage times. The offset is **not significant** (0.029 ± 0.044). The error rate is over-dispersed (ratio 3.57). |

**What the real data imply:** calibration counts need not be binomial, and model optimism cannot be ruled out. A safe declaration must therefore use the upper bound on the model margin (0.10 for USTC), not the point estimate.

## Theory
- **Certified-delivery theory:** `study27_certification/THEORY_CERTIFIED_2026-10-11.md`, covering Prop. N, Lemma F, Prop. C1 and the resource floor.
- **Model-based guard:** `docs/THEORY_NOTE_2026-10-11.md` and `audit/reviews_2026-10-11/PROOF_REVIEW.md`, covering Theorem 1 (per user), Lemmas A–E, the drift corollaries and the fault-exposure no-go.
- **Correction:** the earlier "Prop. 10" (informed priors need no extra assumption) was **false**. Lemma B replaces it with a sufficient condition. The earlier per-path statement of the guard is replaced by the per-user Theorem 1.
- **Closed loop:** `study30_closed_loop/THEORY_30.md` (Theorem 2, Lemma A, Corollary O, Prop. D) and `study32_robustness/THEORY_32.md` (Remark R).
- **Human review:** AI proof reviews are in the repository. A human check of the proofs by the authors is in progress.

## Known limitations
- **Limited hardware.** Two single-device IBM runs (no distribution over distance); otherwise the real-data checks re-analyse published data.
- **Model-based guarantees hold only under stated assumptions.** These are: a correct or declared-pessimistic physics model; counts that are not over-dispersed, or a declared dispersion; and declared drift or re-alignment bounds. Persistent noise is not covered.
- **The model-free certificate** assumes trusted measurements and hidden, fresh test choices. It certifies an aggregate, not individual pairs. The simulations use ideal measurements.
- **Guarantees are per user,** not simultaneous over all users of a network.
- **Network model:** a 5 × 5 grid with stylised noise and fault models (the closed loop also on 10 × 10 and 30 × 30 grids; the guard alone on 30 × 30). The baselines are re-implemented class representatives.
- **Before the first alarm** no data-driven rule can protect users (Prop. N); detection of small offsets is slow.

## Method
- **Pre-registration.** Every confirmatory study was pre-registered before its run: hypotheses, pass bars, a locked analysis script tested on synthetic data, task lists and code hashes. Failures are kept and reported.
  - Over the project, 83 primary hypotheses were tested: 74 PASS, 9 FAIL (`audit/SCOREBOARD_v2.md` covers up to Study 27; Study 28: 6/7; Study 29: 6/6; Study 30: 5/5; Study 31: 2/3; Study 31b: 3/3; Study 32: 6/6; Study 34: 3/3; see the RESULTS files).
  - See `PREREGISTRATION_TIMELINE.md` and `audit/EVIDENCE_LEDGER.md` (entries E1–E149).
- **Timestamps** (`audit/PREREG_TIMESTAMP_CHECK.md`):
  - For every study run on PSC Bridges-2, the pre-registration was on the cluster before the first confirmatory job.
  - Studies 26 and 27 were committed publicly 2 min 15 s and 1 min 51 s before their first job.
  - Exceptions are disclosed in the ledger: Study 25 Block A started about 2 min before its public commit, and v11 and v16 had partial exposure to confirmatory data.
  - Each `des_*_psc/` folder holds the job-written metadata (code hash, task hash, start time).
  - From v0.1.0 on, every release is archived on Zenodo.

## Layout

| Folder | Contents |
|---|---|
| `study18c_controller_and_guard/` | Simulators (`drift_queue_des_*.py`), the physics model (`ptm_model.py` + NetSquid cross-checks), pre-registrations (`README_*.md`), locked analyses, confirmatory outputs (`des_*_psc/`) and the theory note. Studies v5–v21, C1–C2, P1, S1, G1–G7. |
| `study23_ai_rl_guard/` | Global AI model + RL router under the guard (Study 23) |
| `study24_ai_v2_hardware/` | AI v2; five hardware types; unseen correlation patterns; latency; drift carry-over (Study 24) |
| `study25_realism/` | Model error, finite calibration, shared noise, parallel load, declared re-alignment bound (Study 25): 9/9 primary PASS, secondary T3 FAIL; see `RESULTS_25.md` |
| `study26_certified/` | Per-user guarantee level, real-hardware noise and model-error levels (ICFO/USTC), published baselines at matched safety, finite memory (Study 26): 7/7 primary PASS; secondary U2, R5 FAIL; see `RESULTS_26.md` |
| `study27_certification/` | Model-free, anytime-valid certificate of kept-pair fidelity on top of the control layer, under model error, persistent noise and memory faults (Study 27): 2/2 primary PASS; certificate valid where the control layer fails; theory note and adversarial review included; see `RESULTS_27.md` |
| `study28_model_check/` | Model check (e-process on the certification tests), network-wide guard, converse resource bound (Study 28): 6/7 primary PASS, H4 FAIL (disclosed); 4/4 secondary PASS; theory note, adversarial review, pilot and confirmatory runs; see `RESULTS_28.md` |
| `study29_margin_response/` | Margin response after a model-check alarm: tracking with an exact upper bound and probe tests (Study 29): 6/6 primary, 4/4 secondary PASS; replay of Study 28's failing network; see `RESULTS_29.md` |
| `study30_closed_loop/` | Provable closed loop (Theorem 2, Corollary 3, Prop. D), offset in the true state (Study 30): 5/5 primary, 6/6 secondary PASS; see `RESULTS_30.md` |
| `study31_hardware_testkeep/` | IBM hardware test-or-keep (Study 31): W1, W2 PASS; W3 FAIL (disclosed); see `RESULTS_31.md` |
| `study31b_hardware_detector/` | IBM hardware rerun with the hybrid check (Study 31b): W1, W2, W3, W5 PASS; see `RESULTS_31b.md` |
| `study32_robustness/` | Recovering offset bound and robustness (Study 32): 6/6 primary, 4/4 secondary PASS; see `RESULTS_32.md` |
| `study33_fixedk/` | Fixed-K vs anytime certificate (computation, not pre-registered) |
| `study34_grids/` | Closed loop on 5 × 5, 10 × 10 and 30 × 30 grids (Study 34): 3/3 primary, 5/5 secondary PASS; see `RESULTS_34.md` |
| `external_checks/` | `innsbruck_230m/`, `icfo_2021/`, `ustc_2026/`: pre-registrations, code and results |
| `audit/` | Evidence ledger, timestamp check, PSC job history, hardware provenance, novelty map, audit scripts |
| `docs/` | Theory note v4 for the model-based guard (Prop. 10 there is superseded by Lemma B; see `audit/reviews_2026-10-11/PROOF_REVIEW.md`) |

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
- Cite via `CITATION.cff`. Zenodo: **doi:10.5281/zenodo.23287414** (all versions); v0.3.0 (certified delivery): doi:10.5281/zenodo.23291355; v0.6.0 (manuscript v0.6: provable closed loop, hardware, robustness): doi:10.5281/zenodo.23306520; v0.6.1 (adds Study 34): doi:10.5281/zenodo.23308490.
