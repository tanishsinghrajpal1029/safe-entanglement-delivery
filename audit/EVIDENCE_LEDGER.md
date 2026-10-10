# Evidence ledger: independent audit for Study 18

This folder is maintained by Claude (Cowork session), working as the skeptical coauthor and auditor. It deliberately sits **beside** `../18_loaded_network/`, which another agent is actively writing, and never edits it. Each entry records what was measured, where the output is, and what it changes. Negative and null results stay in the ledger.

Status key: **VERIFIED** (reproduced from raw data or code), **FALSIFIED** (tested and contradicted), **OPEN** (not yet tested), **CLAIMED** (stated elsewhere, not yet checked by me).

## E1 — Study 17 final results (3 Oct 2026) — VERIFIED

**Measured.** F1 +4.38 [3.63, 5.13]; F2 +12.58 [10.95, 14.21]; F3 PASS (upper bounds 0.988% and 0.955%); F4 FAIL (−1.04 [−1.27, −0.81]); cal30 6.25% bad.

**Evidence.**
- Recomputed from the raw files with independent code.
- Phase order and frozen-file hashes checked.
- The calibration rule reproduces the frozen choices exactly.

See `../STUDY17_INDEPENDENT_VERIFICATION.md`. Study 17 is frozen and must not be touched.

## E2 — Information boundary of the Study 18 controller (3 Oct) — VERIFIED (static code audit)

- **Inputs.** `decision_policy.PairObservation` carries only event metadata: herald, swap and evaluation times, storage intervals, Bell outcomes, purification bits, and estimates.
- **Oracle use.** In `concurrent_quantum.py`, `qapi.fidelity` is read only *after* a `deliver` decision (lines ≈652, 691, 787, 805) and passed to `finish()` for scoring.
- **Imports.** Policy-side modules import neither NetSquid nor `qapi`.

**Caveat (OPEN).** Calibration in the development probe is `Calibration.build(..., rel_error=0.2)`: a synthetic perturbation of the *true* parameters. That is not an operational measurement. Generation-success probabilities are passed unperturbed.

## E3 — "Pauli/Werner estimator fails by up to 0.2076 under T1" (3 Oct) — FALSIFIED as a decision-relevant effect

**Claimed in.** `../18_loaded_network/RAW_ESTIMATOR_VALIDATION.md`, `ESTIMATOR_MODEL_SPEC.md`, `STATUS_2026-10-03.md`.

**Independent test.** `pauli_vs_density.py` and `pauli_vs_density_hetero.py`, plain NumPy written from scratch, no NetSquid. They model amplitude damping to |0⟩ plus dephasing (T2 ≤ 2T1) on stored qubits, BSM projection on each Bell outcome, and Pauli-frame correction. Two runs:
- 1,296 symmetric cases;
- 4,000 random heterogeneous chains (2–3 links, per-node T1/T2, depolarizing links, post-delivery storage), giving 40,012 outcome branches.

**Results** (`out_pauli_symmetric.txt`, `out_pauli_hetero.txt`):

| Region | Largest Pauli-model error |
|---|---|
| All cases | 0.1925 per outcome |
| Rows where true or predicted F ≥ 0.9 | 0.0013 (heterogeneous) / 0.0027 (symmetric) |
| Rows with F ≥ 0.95 | 0.0002 |

- Near threshold the Pauli model almost always **under**-estimates fidelity; its largest overestimate at F ≥ 0.9 is 0.00023.
- At threshold 0.9 the Pauli model would have caused **0** bad deliveries, and lost goodput in 2 of 40,012 branches.
- Bell-outcome dependence of the true fidelity is ≤ 0.0009 for average F in [0.9, 0.95]. It reaches 0.25 only for average F < 0.6.

**Interpretation.**
- The dropped non-unital term is O(γ²) (≈ γ²/4 for a stored Φ+). It is large only when pairs have decayed toward F ≈ 0.5, far below a 0.9 threshold.
- This explains why the development probe's policy counts did not change when the estimator was swapped.
- The density replay is still correct and harmless to use. But "Bell-diagonal/Werner models mislead threshold decisions under T1" is **not** a viable contribution at F_th ≈ 0.9. It may matter at F_th ≲ 0.75: worst error 0.017 at F ≥ 0.7.

**Limits of this test.** No BSM or gate depolarization (these are Pauli and are captured exactly by the Pauli model); no purification; no crosstalk. The 0.2076 figure came from a different scenario set. It has not been reproduced here, only bounded in the decision-relevant region.

## E4 — Prior-art boundary (literature, 3 Oct) — see `NOVELTY_MAP.md`

## Open items for Gate 1 (validation of the loaded model)

| Item | Status | Needs |
|---|---|---|
| Re-run all 72 Study 18 tests independently | OPEN | NetSquid → the user's Mac (command in `NEXT_COMMANDS.md`) |
| Repeater QuantumMemory component replay vs the manual model | OPEN (other agent lists it as missing) | — |
| Classical-control message delay or loss in decisions | OPEN | — |
| Multi-request (≥ 3), many-slot, purification-under-load invariants at larger scale | OPEN | — |
| Hardware parameter provenance (T1/T2/BSM/gate/readout from primary experiments) | OPEN | A literature table |

## E5 — Is threshold-qualified delivery calibration-limited? (3 Oct) — NOT FALSIFIED; supported in a model

**Test.** `calibration_overhead_test_v2.py` (NumPy). It uses the Study-18 pilot's calibration protocol (local X/Y/Z parity of consumed pairs at holds {0, 0.4, 1.6}·T2, with a known readout flip q = 0.03), fitted by weighted least squares. It then makes delivery decisions on L-link paths with the Pauli predictor, which E3 showed is adequate near 0.9.

**v1 is retained but was biased.** `calibration_overhead_test.py` / `out_calibration_overhead_v1_BIASED.txt` clipped the fitted p at ≥ 0, which biased estimates upward. On long paths the true fidelities were also entirely below 0.9. v2 fixes both: the fit is unbounded, and link noise is scaled so the true F straddles 0.9 at each L.

**Measured** (`out_calibration_overhead_v2.txt`, `calibration_overhead_table_v2.csv`). RMS error of the fitted depolarization:

| Pairs per link | 250 | 1,000 | 2,250 | 10,000 | 50,000 |
|---|---|---|---|---|---|
| RMS error in p | 0.065 | 0.032 | 0.020 | 0.010 | 0.0048 |

The error falls roughly as 1/√n. Good links have p ≈ 0.01, so at the pilot's 2,250 pairs the *relative* error in p exceeds 100%.

Share of the perfect-knowledge qualified deliveries kept at r_cond ≤ 1% (margin chosen from {0, …, 0.04}):

| Path | 2,250 pairs/link | 10,000 | 50,000 |
|---|---|---|---|
| L = 1 | 75% | 91% | 99% |
| L = 3 | 17% | 50% | 89% |
| L = 6 | ≈ 0% | ≈ 0% | 11% |

**Interpretation (model-level only).**
- Calibration precision, not physics, limits qualified delivery on multi-link paths at F_th = 0.9.
- The pairs needed per link grow roughly as L/m².
- With measured trapped-ion drift periods of about 10⁴ s and heralding rates of 10–200 Hz (10⁵–2×10⁶ pairs per link per period), 5×10⁴ pairs per link per period is 2.5–50% of capacity. The bottleneck is regime-dependent and lands in realistic territory, so H-cal survives this first test.

**Mechanism noticed (hypothesis to verify).**
- The parity-estimator variance is about 1 − (1−2q)⁴(1−p)² ≈ 8q + 2p.
- For high-quality links, readout (SPAM) error, not channel noise, dominates the calibration cost whenever q > p/4.
- SPAM-robust, benchmarking-style protocols (network benchmarking; LINKSELFIE) are therefore the obvious strong baseline and a likely scalable alternative. This is not new by itself.

**Limits.**
- No NetSquid in this test.
- Only symmetric per-link parameters.
- No drift inside a period, no tier pooling, no end-to-end (per-path) estimation, no purification.
- The margin grid is capped at 0.04.
- The q = 0.03 value is an assumption pending the hardware-provenance table.

## E6 — Independent rerun of the Study 18 and core test suites (3 Oct 2026, your Mac) — VERIFIED

`logs/gate1_s18_tests.log`: Ran 72 tests, OK. `logs/gate1_core_tests.log`: Ran 29 tests, OK. Both used the pinned x86 NetSquid Python 3.9. These confirm the prototype's *invariants and small-case replays* only (see `../18_loaded_network/EVENT_MODEL_SPEC.md`). They do not validate scale, hardware realism or performance.

## E7 — Hardware realism gap (3 Oct) — ESTABLISHED (see `HARDWARE_PROVENANCE.md`)

- **Project config.** Link infidelity 0.00075–0.00375 with ideal BSM and 0.95 efficiencies. Median 20-hop paths at 30×30.
- **Demonstrated links.** F = 0.940 at 182 Hz (ions, 2020); F = 0.82 at 9 Hz (NV, 2021), with swapped F = 0.55; F = 0.86 electron and 0.69 nuclear over 35 km (SiV, 2024).
- **Consequence.** Twenty hops at F ≥ 0.9 would require link F ≳ 0.995 without purification. Studies 08–17 are therefore valid only as projections in an aspirational regime.
- **For PRX.** Any claim must be anchored to a near-term regime (≤ 3–4 hops, ion-like links, purification) or explicitly framed as a projection with a sensitivity bridge. This is a **material weakness of the current results for a PRX submission**, not a detail.

## E8 — Parallel work by the other agent: `../19_calibration_decisions/` (3 Oct, files dated 09:39–14:21 UTC) — CLAIMED, not yet audited

It covers the same calibration-to-decision question as my H-cal candidate. Contents:
- finite-shot decision reversals near F_th;
- a bootstrap lower-quantile rule (expensive in good yield);
- calibration records generated in NetSquid;
- an identifiability derivation (equal holds cannot label endpoint T1/T2; one-sided holds can);
- an equal-pair comparison of oriented vs symmetric calibration, with no reliable win and negatives retained.

**Decision.** I will not duplicate it. My remaining distinct contributions are:
1. this hardware-provenance table;
2. the analytic calibration-cost law (E5) and its test against folder-19 simulations;
3. a SPAM-robust (network-benchmarking-style) calibration baseline;
4. an audit of folder 19's numbers.

**Coordination status.** `ListAgents` shows no other Claude session on this machine, so the other agent is a different tool or stopped. I still have not had an answer from the user on who owns Study 18/19.

## E9 — Workspace split (3 Oct 2026, ~17:37 UTC)

At the user's request, all of Claude's work moved to `Files11-EndToEnd-PRX-Claude/`, a full snapshot of `Files11-EndToEnd-PRX/` (3,846 files; manifest `SNAPSHOT_SHA256SUMS.txt`; see `CLAUDE_COPY_README.md`). The other agent kept editing the original at 17:39–17:40 UTC, which confirms the two agents were writing concurrently.

- Entries E1–E8 above were written while this folder lived in the original workspace. The copy of this folder left there is a stale record and receives no further updates.
- Two other notes stay in the original: `STUDY17_INDEPENDENT_VERIFICATION.md` and `18_audit_independent/`. They are left unedited so as not to touch the other agent's workspace.
- From this entry on, this ledger is the authoritative one.

## E10 — Near-term regime map: is static calibration a bottleneck? (3 Oct) — FALSIFIED in static form

**Test.** `nearterm_calibration_regimes.py` → `out_nearterm_regime_map.txt`, `nearterm_regime_map.csv`. NumPy Werner/Bell-diagonal model, adequate near threshold per E3. Presets:

| Preset | Basis |
|---|---|
| `ion_2020` | F = 0.94 and R = 182 Hz from Stephenson et al. 2020; T2 = 1 s, q = 0.001, e = 0.005 **assumed** |
| `ion_proj` | F = 0.97 (projected) |
| `nv_2021` | F = 0.82 and R = 9 Hz from Pompili et al. 2021; T2 = 10 ms and q = 0.03 assumed |
| `aspir_cfg` | Project config |

Chains have L = 1–4 links, raw or with one round of end-to-end DEJMPS. Each link's Werner λ is estimated from n consumed parity pairs, with memory and gate parameters known.

**Results.**

Feasibility at F_th = 0.9 with perfect knowledge (fraction of requests above threshold):

| Preset | L = 1 | L = 2 | L = 3 | L = 4 |
|---|---|---|---|---|
| ion_2020 (purify / raw) | 1.0 / 1.0 | 0.36 / 0.05 | 0 / 0 | 0 / 0 |
| ion_proj (purify / raw) | 1.0 / 1.0 | 1.0 / 1.0 | 0.80 / 0.27 | 0.04 / 0 |
| nv_2021 | ≤ 0.008 | 0 | 0 | 0 |

**Without drift**, calibration costs ≤ 0.5% of link capacity (n / (R·10⁴ s)) wherever delivery is feasible. Static calibration is therefore *not* a bottleneck. Only the marginal cells (ion_2020 L = 2, ion_proj L = 3–4) fail to keep 90% of oracle deliveries even at 10⁵ pairs per link.

## E11 — Drift creates a precision–freshness tradeoff near the feasibility frontier (3 Oct) — SUPPORTED (model-level, exploratory)

**Test.** `drift_floor.py` → `out_drift_floor.txt`, `drift_floor_table.csv`. Link λ drifts down at rate g ∈ {10⁻⁶, 10⁻⁵, 10⁻⁴} s⁻¹. A window of length T uses a fraction ρ of heralded pairs to estimate λ, and the estimate is used during the next window.
- **Static** estimator: stale, so it *overestimates*, which is the unsafe direction.
- **Drift-aware** estimator: crude OLS extrapolation with an approximate variance factor.

ρ, T and the margin are grid-searched for r_cond ≤ 1%, and the score is (1−ρ) × qualified kept / oracle. Selection and evaluation use the same draws, so this is exploratory and optimistic.

**Results.**

| Regime | Static: g = 10⁻⁶ → 10⁻⁵ → 10⁻⁴ | Drift-aware (≈ flat in g) |
|---|---|---|
| Far above threshold (ion L = 1; ion_proj L = 2 raw; aspirational L = 10) | 0.96–0.99, insensitive to drift | — |
| **ion_2020, L = 2, purify** | 0.80 → 0.55 → **0.26** | ≈ 0.47–0.48 |
| **ion_proj, L = 3, purify** | 0.90 → 0.80 → **0.64** | ≈ 0.76 |
| aspirational, L = 20 | 0.80–0.83 | 0.77–0.79 |

There is a crossover near g ≈ 10⁻⁵ s⁻¹.

**Interpretation (hypothesis).** Near the multi-hop feasibility frontier, which is where near-term networks will operate, drift-limited link estimation, not physics, costs roughly 20–75% of qualified goodput at 1% risk. Far from the frontier it is negligible.

**Limits.**
- The drift-aware variance factor is a rough approximation.
- Drift is linear and only λ drifts.
- No NetSquid.
- Margins were selected on the evaluation draws.
- The drift rates are swept, not measured. The arXiv 2606.18167 data imply about 5×10⁻⁵ s⁻¹ initial fidelity slope without stabilization; arXiv 2608.07163 has 48 h of polarization drift.

## E12 — Prior art: Clayton et al., "Rate-Fidelity Control for Wide-Area Quantum Links", arXiv 2608.07163 (2026)

This paper does **single-link** drift tracking through classical polarization-reference checks (44 ms), with conservative rate control so that Pr[F < F_min] ≤ 0.1. On a deployed link with 48 h of measured drift it gains 14% over static policies. It does not model multi-hop, swapping, purification or memories, and calls multi-hop "a broad and largely open problem".

**Consequence.** Our candidate must be the **multi-hop** version: drift-aware, swap- and purification-aware delivery decisions near the feasibility frontier, estimated from quantum (parity) data and compared against a single-link-style tracking baseline. It must not be presented as "drift tracking", which is not new.

## E13 — Surrogate check against an exact NumPy circuit (3 Oct) — PARTIAL FAILURE, retained

`18c_drift_frontier/check_surrogate_numpy.py` → `out_check_surrogate_numpy.txt`.
- The DEJMPS closed form for Werner inputs is exact (max error 5.6×10⁻¹⁶).
- **The gate-error shortcut used in E10/E11, (1−e)F′ + e/4, is optimistic**, by up to 0.0040 at e = 0.005 and 0.0079 at e = 0.01, which is the unsafe direction.

The E10/E11 numbers for **purified** paths are therefore provisional until they are recomputed with the exact gate model. A NetSquid confirmation is queued: `18c_drift_frontier/netsquid_surrogate_check.py`, with pass criteria fixed in its README before running.

## E14 — NetSquid check of the surrogate (3 Oct, your Mac, NetSquid 1.1.6) — PASS (all pre-set criteria)

`18c_drift_frontier/netsquid_surrogate_check.py --seed 18401` → `logs/netsquid_surrogate_check.json` (35 s).

| Check | Result | Pre-set criterion |
|---|---|---|
| Swap chains (60 cases) vs closed form | max error 4.4×10⁻¹⁶ | < 10⁻⁹ |
| DEJMPS success probability (18 cases × 3,000 trials) | max \|z\| = 2.55 | < 4 standard errors |
| DEJMPS fidelity vs exact NumPy circuit | max error 4.4×10⁻¹⁴ | < 0.003 |
| Old shortcut (1−e)F′ + e/4 | **optimistic** by 0.0037–0.0078 whenever e > 0 | (E13 confirmed) |

**Consequence.** The exact NumPy model is an independently validated stand-in for NetSquid on these primitives: Werner links, depolarizing storage, noisy BSM and DEJMPS with gate depolarization. It does **not** validate queueing, contention or non-Werner (T1) states; see E3 for why T1 effects are minor near F ≥ 0.9.

## E15 — Drift-frontier analysis v2 (3 Oct) — SUPPORTED at model level; evaluated on separate draws

`18c_drift_frontier/drift_frontier_v2.py` → `drift_frontier_v2_table_cloud.csv` (sha256 74fe6cd0…), `out_drift_frontier_v2_cloud.txt`.

**What changed from E11.**
- Exact DEJMPS with gate error, from a table whose interpolation error is ≤ 4.4×10⁻⁶.
- Estimators sampled from their exact distributions, including rolling (sliding-window) variants.
- **ρ, T and the margin are chosen on dev draws and scored once on independent eval draws.**
- A non-reproducible `hash()` seed was found and fixed before this run. The earlier output was discarded and never reported.

**Eval results.** Net qualified fraction of oracle, at drift g = 10⁻⁶ / 10⁻⁵ / 10⁻⁴ s⁻¹:

| Cell (share of requests above threshold with perfect knowledge) | Best estimator | Batch-static |
|---|---|---|
| Far above threshold: ion L = 1, ion_proj L = 2 | 0.96–0.99, any estimator | — |
| **ion_2020, L = 2, purify (27%)** | rolling-static 0.73 / 0.68 / 0.51; rolling-OLS 0.58 / 0.55 / **0.55** | 0.68 / 0.49 / **0.16** |
| **ion_proj, L = 3, purify (78%)** | rolling-static 0.89 / 0.88 / 0.73; rolling-OLS 0.82 / 0.82 / **0.83** | 0.89 / 0.78 / **0.55** |
| aspirational, L = 20 (21%) | 0.81–0.88 | — |

Eval r_cond ≤ 1% in every row except one, at **1.17%** (aspirational, batch-static, g = 10⁻⁶), where the dev-chosen margin missed on eval. It is retained.

**Interpretation.**
1. Near the multi-hop feasibility frontier, imperfect knowledge of drifting links costs **12–45%** of the qualified goodput that perfect knowledge would deliver at 1% risk. With naive batch calibration under fast drift the loss reaches **84%**.
2. **A standard sliding-window estimator recovers most of it.** Drift-extrapolating (OLS) estimators help only at the highest drift, by +4 to +10 points. So a better tracker is **not** a strong novel mechanism. The candidate contribution is the *quantification*: the size of the loss near the frontier, how it depends on drift, rate and path length, and when tracking matters.

**Limits.**
- Linear drift on λ only.
- Swept g, not measured.
- No queueing or contention.
- Five cells, one seed stream each.
- A single DEJMPS round.
- Memory and gate parameters assumed known.

## E16 — Cross-environment reproduction of E15 (3 Oct, your Mac) — VERIFIED (bit-identical)

The Mac run (NetSquid env: Python 3.9.23) of `drift_frontier_v2.py drift_frontier_v2_table_mac.csv` produced table sha256 `74fe6cd0e9d4…`, **identical to the cloud run** (Python 3.11). Every number in E15 is reproducible.

## E17 — Load × drift (3 Oct) — SUPPORTED at model level (fluid capacity sharing, no queueing)

`drift_load_v3.py` → `drift_load_v3_table_cloud.csv` (sha256 e339cad5…), `out_drift_load_v3_cloud.txt`. Same validated primitives and dev → eval protocol as E15. Each link's capacity R is shared by user traffic (offered load ℓ) and calibration under three policies:
- **fixed:** a reserved fraction ρ;
- **opportunistic:** idle capacity only, at no cost to users;
- **hybrid:** both.

Score = fraction of the ideal (perfect-knowledge, zero-overhead) qualified service.

**Eval results** (best policy; opportunistic-only in brackets):

| Cell | ℓ = 0.3–0.6 | ℓ = 0.9 | ℓ = 0.99 |
|---|---|---|---|
| ion_2020, L = 2, purify | 0.79–0.94 (0.79–0.94) | 0.79–0.85 (0.64–0.75) | 0.69–0.73 (**0.16–0.46**) |
| ion_proj, L = 3, purify | 0.92–0.99 | 0.92–0.99 | 0.83–0.91 (0.54–0.83) |
| ion_proj, L = 2, raw | ≈ 1.0 | ≈ 1.0 | ≈ 1.0 |

Six of 108 eval rows exceeded 1% r_cond (max **1.27%**). The dev-chosen margins are slightly optimistic at the edges; these rows are retained.

**Interpretation (hypothesis).**
- At low load, idle link time pays for calibration and drift costs little.
- At high load, near the feasibility frontier, opportunistic calibration starves. Any reservation instead takes capacity from users, so the loss returns: **10–30% with the best policy, up to 84% with idle-only calibration.**

The candidate contribution is this **load × drift × frontier interaction**, with the best calibration allocation depending on all three.

**Limits.**
- A fluid model: no queueing, deadlines or memory occupancy of calibration pairs.
- Single paths, not networks.
- Swept drift.

**Next step.** A NetSquid loaded check with drifting links, using `concurrent_quantum.py`, which reads each link's depolarization at generation time (line 615) and already supports consumed calibration pairs.

## E18 — Reproduction of E17 on the Mac (3 Oct) — VERIFIED (bit-identical, sha256 e339cad5…)

## E19 — Discrete-event test with queueing: pilot (3 Oct) — FLUID MODEL CONTRADICTED; provisional

**Script.** `drift_queue_des.py` (sha256 cc954805…), an independent discrete-event implementation built on the E14-validated primitives. It models:
- a FIFO whole-path server with Poisson arrivals;
- a 0.25 s deadline counted from arrival;
- a retry budget of 4;
- sawtooth link drift (re-alignment every 0.02/g);
- calibration parities sampled exactly from the realized busy/idle timeline, with sliding-window inversion of the known readout flip.

Path draws are the replication unit: 8 dev paths, plus 8 different eval paths on a different random stream.

**Speed fixes, verified exact.** The scalar bilinear lookup matches SciPy to 3×10⁻¹⁶. The closed-form sawtooth average matches numerical integration to 10⁻¹⁶.

**Pilot (cloud, combos 1 and 4: ion_2020, L = 2, purify, load 0.9):**

| Drift | Policy | Result |
|---|---|---|
| g = 10⁻⁵ | fixed | **0.052** of oracle qualified rate; eval r_cond **3.05%** |
| g = 10⁻⁵ | hybrid | **0.050** of oracle; eval r_cond **1.35%** |
| g = 10⁻⁵ | opportunistic | no dev setting met 1% |
| g = 10⁻⁴ | fixed / hybrid | **0.000** (no deliveries) |
| g = 10⁻⁴ | opportunistic | no dev setting met 1% |

The oracle itself missed 38–49% of deadlines: retries inflate service time, so the queue is effectively overloaded.

**Interpretation (provisional).**
- With queueing and deadlines, near the frontier and at high load, verified delivery *collapses*: below 6% of the perfect-knowledge rate. The fluid model (E17: 0.64–0.85) was far too optimistic.
- Dev-chosen settings also **failed the 1% target on eval** (3.05% and 1.35%). Eight paths are too few to select safely.

**Risks of artifact.**
- The deadline, retry budget and margin grid (minimum margin 0.0125) were not varied.
- Load is defined relative to *oracle* service capacity.
- Only one cell and one load have run.

The full 12-combo sweep was handed to the Mac on 3 Oct.

## E20: v4 queueing simulation (DES), full 12-combo Mac run (4 Oct 2026). PROVISIONAL; v5 artifact check pre-registered

**Run.** `18c_drift_frontier/des_v4_mac/ALL.csv`, sha256 `a966c00f…`. 1,423 s on 17 workers.

**Reproducibility.** Combos 01 and 04 are bit-identical to the cloud pilot. The cached DEJMPS tables differ between platforms by at most 3.3e-16, with no effect on outputs.

**Measured.** EVAL qualified delivery as a fraction of the oracle, for the fixed policy at loads 0.5 / 0.9 / 0.97:

| Cell | g = 1e-5 | g = 1e-4 |
|---|---|---|
| ion_2020, 2 links | 0.070 / 0.052 / 0.051 | 0 |
| ion_proj, 3 links | 0.319 / 0.241 / 0.244 | ≤ 0.002 |

- **Hybrid** matches fixed within 0.004.
- **Opportunistic** calibration: no dev setting met the 1% target in 12 of 12 combos.
- **Load vs drift.** Load moves the fraction by ≤ 0.08 absolute, while drift (g = 1e-4) removes nearly everything.
- **Safety out of sample.** EVAL r_cond exceeded 1% in 6 of 24 feasible rows (maximum 4.6%, on 65 deliveries). The dev point-estimate selection does not generalise.
- **Oracle.** The oracle itself missed 10–58% of deadlines (D = 0.25 s).

**Flaws found (could create the result):**
- W1: grid edges binding (rho 0.1 maximum, margin 0.0125 minimum); the code's grid (T {100, 300}, m {0.0125, 0.025, 0.04}) differs from what its docstring states.
- W2: the estimator ignores the known re-alignment times and the linear drift.
- W3: selection uses a point estimate on 8 paths, and zero-delivery settings count as passing (at g = 1e-4 the "selected" setting delivers nothing).
- W4: the deadline is tight.

**Next.** `drift_queue_des_v5.py` (sha `49e10e8a…`) with predictions P1–P4 fixed in `README_v5.md` (sha `d1387b3a…`) before any v5 run. The new estimators were unit-checked in the cloud: biases g·T/2 (static), g·(t − t_reset)/2 (reset) and ≈ 0 (ols_reset), as derived. A spawn-start smoke run passed.

## E21: v5 artifact check, Mac (4 Oct 2026; 11,744 s). Mixed: frontier survives, smarter estimators failed for a diagnosed reason

**Run.** `18c_drift_frontier/des_v5_mac/SUMMARY.csv`, sha256 `0ee68bf7…`. Script sha `49e10e8a…`. Predictions were pre-registered in `README_v5.md`.

**Results by prediction:**
- **P1 PASS.** At g = 1e-4, the best `ucb` rule reaches 0.146 (ion_2020) and 0.012 (ion_proj) of the oracle, both below 0.5. Caveat: the best rho is at the grid edge (0.3).
- **P2 FAIL.** `reset` and `ols_reset` are infeasible at g = 1e-4. At g = 1e-5, `reset` beats `static` by 0.066 (ion_proj, below the 0.10 bar) and is infeasible on ion_2020.
  - *Diagnosis.* After a re-alignment the window holds few pairs, and with a fixed margin the controller trusts them. P(all 10 parities even | λ = 0.93) = 0.70, so λ̂ = 1. Dev r_cond for `reset` *rises* with the margin (0.14 → 0.65 at rho 0.3, T 100).
  - **Finding: a fixed margin is unsafe for variable-precision estimators.**
- **P3.** Under `ucb`, 0 of 21 eval rows exceed 1% (PASS). But the point rule (≥ 50 deliveries) was also safe, so the prediction "the point rule violates" FAILS. v4's violations came from low-delivery selections on 8 paths.
- **P4 PASS.** Moving D from 0.25 to 1.0 s changes results by at most 0.011.

**W1 confirmed.** The static fraction rose from 5% to 30% (ion_2020, slow drift) and from 0% to 15% (fast drift) when rho could reach 0.3. Path draws also changed, so the two effects are confounded.

**New issue.** Dev and eval path populations differ hugely (best dev qualified rate 0.37/s vs 4.26/s on eval). Per-path heterogeneity near threshold dominates the aggregates.

**Next.** v6, `drift_queue_des_v6.py` (sha `3dac7de5…`):
- confidence-bound (LCB) controller; SE checked against empirical SD within 5%;
- 32 + 32 paths, with per-path outputs;
- rho up to 0.5.

Predictions Q1–Q4 are fixed in `README_v6.md` (sha `11c32b67…`).

## E22: v6 confidence-bound (LCB) controller, Mac (5 Oct 2026; 17,566 s). Frontier holds; dev-certified risk does NOT transfer to fresh paths

**Run.** `des_v6_mac/SUMMARY.csv`, sha256 `0578583b…`. Script sha `3dac7de5…`. 32 dev + 32 eval paths.

**Results by prediction:**
- **Q1 FAIL.** Smarter estimators gain ≤ 0.012 over `static` at g = 1e-4.
- **Q2 PASS.** Best fraction of the oracle at g = 1e-4 is 0.018 (ion_2020) and 0.065 (ion_proj).
- **Q3 FAIL.** 6 of 11 feasible eval rows have r_cond > 1% (max 6.0%), although every one met CP-UCB ≤ 1% on dev. All three ion_2020 slow-drift rows fail (1.24–4.3%).
- **Q4 partial.** Fraction is monotone in headroom; no collapse without normalisation.

**Mechanism.** Bad deliveries concentrate on sub-threshold paths. In combo 0: 198 bad of 539 deliveries on paths with h < −0.01, against 11 of 11,512 on paths with h > 0.003. Eval sets had more sub-threshold paths than dev (91% vs 84%; 97% vs 91%; 72% vs 69%; 84% vs 78%).

**Interpretation (hypothesis H-FDR, to be tested in v7).** Threshold delivery is a false-discovery problem. Per-decision confidence fixes α(h) per attempt, but r_cond depends on the base rate of sub-threshold attempts. The same mechanism plausibly explains why folder 19 certified zero routes.

**Next.** v7 (`drift_queue_des_v7.py`, sha `07d639c7…`): a controlled-headroom sweep with per-attempt binning. Predictions R1–R3 are fixed in `README_v7.md` (sha `3424d643…`).

## E23: v7 controlled-headroom sweep, Mac (5 Oct 2026; 1,728 s; 1,872 runs). Error model and risk law SUPPORTED; R3 FAILED

**Run.** `des_v7_mac/runs.csv`, sha256 `082d433d…`. Script sha `07d639c7…`. Analysis `analyze_v7.py` (sha `c9f06b92…`); output in `des_v7_mac/analysis_v7_out.txt`.

**R1 PASS.** Per attempt, P(deliver | h) = Φ((h + μ − off)/s) fits the observations with a median per-run maximum deviation of 0.0026 (g ≤ 1e-5). At g = 1e-4 it is 0.018 (ols_reset) and **0.176 (static)**: the drift-phase correlation between error and headroom breaks the model for static, as anticipated in the pre-registration.

**R2 PASS (narrowly).**
- 534 runs: Spearman 0.916 (bar 0.9); median |ln ratio| 0.374 over runs with bad > 0 (bar 0.405).
- With the 0.5 continuity correction over all runs it would be 0.638. This was not pre-specified; it is reported as a sensitivity.
- Pooled predicted vs measured r_cond agree within about 1.4× in every (g, est) group.

**R3 FAIL.** 28% of the 36 series have τ ≤ −0.6. F0 is not a monotone proxy for the base rate, because raising F0 also moves the attempt density at the threshold. Many series (z = 3) also sit at r = 0.

**EXPLORATORY (not pre-registered), `explore_kappa_v7.py`.** A single number κ = p0·s/P(h ≥ 0) orders the trade-off:

| κ bin | z = 1: power | z = 1: median r_cond | z = 2: power |
|---|---|---|---|
| ≤ 0.05 | 0.91 | 0.0006 | 0.78 |
| 0.4–0.8 | 0.34 | 0.052 | 0.06 |
| > 0.8 | 0.09 | 0.54 | — |

The closed-form small-r approximation κ·G(a) ranks runs well (Spearman 0.86) but is off by about 2× in level. Only the histogram integral (R2) is quantitative.

**Novelty spot-check (2 extended searches, 5 Oct).** No paper found that frames threshold delivery as false discovery under estimator uncertainty. Nearest:
- arXiv 2602.18011 (tomography + purification with confidence intervals);
- arXiv 2505.12459 (routing/purification to fidelity targets).

The full Gate-3 novelty check is still OPEN. It needs to cover LINKSELFIE, QNT tomography, 2606.18167, Clayton 2608.07163, and conformal/"Learn-then-Test" risk control in ML.

**Next.** v8 confirmatory test (S1–S3), fixed in `README_v8.md`.

## E24: v8 confirmatory test of the risk law, Mac (5 Oct 2026; 2,153 s; 1,872 runs). S1, S2 and S3 all PASS

**Run.** `des_v8_mac/runs.csv`, sha256 `2670b8a2…`. Script sha `5e165d38…`. Analysis scripts unchanged since pre-registration (`c9f06b92…`, `c1a855e6…`); outputs in `des_v8_mac/analysis_S1S3_out.txt` and `analysis_S2_out.txt`.

**Results:**
- **S1 PASS.** r_cond predicted from each run's attempt histogram: 745 runs, Spearman 0.987, median |ln ratio| 0.228 (bar 0.405). With the 0.5 continuity correction over all runs, 0.316. Pooled predicted vs measured agree within 1.3× in all six (g, est) groups, *including g = 1e-4*.
- **S2 PASS.** At z = 1 and z = 2, median power never rises and median r_cond never falls across all five κ bins.
- **S3 PASS.** Gaussian per-attempt model: median per-run maximum deviation 0.017 (bar 0.05).

**Limits (must be stated in any paper):**
- κ is an **ordering** variable, not a universal curve. At z = 1, κ ≤ 0.05: power is 0.91 in v7 but 0.74 in v8, so power at a given κ still depends on s and z.
- The closed-form small-r approximation κ·G(a) fails quantitatively (Spearman 0.36 overall; about −0.03 to 0.36 for ols_reset, where κ explodes on paths almost entirely below threshold).
- **The quantitative law is the histogram integral**, not κ.

**Conclusion.** Conditional delivery risk under finite calibration is predicted accurately by the base-rate (histogram) integral of a Gaussian per-attempt error model. This is now replicated on fresh conditions. It is the mechanistic explanation of E22's failure of dev-certified risk to transfer.

## E25: v9 self-calibrating controller, design and pre-registration (5 Oct 2026). OPEN

**Files.** `drift_queue_des_v9.py` (sha `788ec1aa…`) and `README_v9.md` (sha `875114fb…`), with predictions T1–T4.

**Controller.** It predicts its own r_cond from observables using the E24 law, and picks z per path online so that predicted r_cond ≤ 1%.

**Smoke test (cloud, before pre-registration):**
- **Bug found and fixed.** An empty passing set was treated as zero risk, so a sub-threshold path delivered 9 bad pairs. Fix: a z needs ≥ 20 supporting window attempts.
- **After the fix,** on an above-threshold path (ion_proj, F0 0.98, g = 1e-5), adaptive delivered 136 good / 0 bad against 398 / 0 for fixed z = 2. Adaptive is markedly more conservative; it had no admissible z on 57% of attempts.

**PSC.** cis260277p shows Bridges-2 RM 9,869 / 10,000 SU (shown by Tanish on 5 Oct). No PSC job has been submitted.

**PSC approval (5 Oct 2026).** Tanish approved **400 SU in total** on cis260277p (RM-shared) for Study 18C. That covers the frontier map and the final run.
- **Infrastructure:** `psc_array_runner.py` (sha `f5eca179…`, tested in the cloud) and `s18c_array.sbatch` (sha `e0e00051…`; at most 64 SU per array element).
- **Ledger of PSC spending:** 0 SU used so far.

**Merge decision (Tanish, 5 Oct).** Merge folder-19 results only if doing so improves the paper. The plan is to test whether the E24 risk law explains folder 19's bad-accept rates and zero certified routes. Merge as corroboration only if it does.

## E26: v10 frontier map, design and pre-registration (5 Oct 2026). OPEN (PSC)

**Files.** `drift_queue_des_v10.py` (sha `105b0e3b…`) and `README_v10.md` (sha `c96b9857…`), with predictions M1–M3. The task list holds 13,824 path-runs (`tasks_v10.jsonl` sha `4cf402f3…` when generated with `--write-tasks`).

**Environment.** PSC check by Tanish (5 Oct): `/opt/packages/anaconda3-2024.10-1/bin/python3` with numpy 1.26.4, pandas 2.2.2, scipy 1.13.1. Code copied to `/ocean/projects/cis260277p/<psc-user>/s18c`; sha256 checks match for v9 and the runner.

**SU plan.** Test shard, then a 20-element array with a 0.5 h limit. Ceiling 320 SU; expected 110–180.

## E27: Wald standard-error collapse after re-alignment (5 Oct 2026). FOUND in v9 partial results; fix pre-registered as v11

**Observed** (v9, 658 of 2,160 runs, partial). ion_2020, g = 1e-5, `ols_reset`, population A:
- adaptive r_cond 6.21% (161 deliveries);
- fixed z = 3 r_cond 37.8% (90 deliveries).

`static` with no drift stays ≤ 0.11% (adaptive).

**Diagnosis.** With few parities and all of them even, the Wald variance collapses.

**Unit check.** One-sided coverage at z = 2 for `reset` after 0.5 s: Wald 0.786, Agresti–Coull 1.000.

**Fix.** Agresti–Coull variances: `drift_queue_des_v11.py` (sha `cc2e53c2…`), `README_v11.md` (sha `afabde38…`), with predictions U1–U3. The task list has 2,160 tasks (`tasks_v11.jsonl` sha `25d5fe82…`).

**Consequence.** v10 (the PSC frontier map) is ON HOLD because it used the Wald SE. It gets re-specified after v11.

**Cost seen in smoke tests.** Honest error bars make `ols_reset` very conservative (adaptive delivered 16 good pairs vs 136 under Wald, ion_proj F0 0.98).

## E28: v9 self-calibrating controller, full Mac run (5 Oct 2026; 2,583 s; 2,160 path-runs). T2, T3, T4 as predicted; T1 FAILED in 3 of 20 groups (all Wald-SE collapse)

**Run.** `des_v9_mac/runs.csv`, sha256 `6a19ede9…`. Analysis `analyze_v9.py`; output `des_v9_mac/analysis_v9_out.txt`.

**T1 FAIL** (adaptive r_cond > 1% in 3 of 20 target groups). All three are ion_2020 + `ols_reset`:
- A, g = 1e-5: 6.2% (10 of 161);
- A, g = 1e-4: 14.6% (88 of 602);
- B, g = 1e-4: 1.5% (31 of 2,054).

This is the E27 Wald collapse, which v11 targets.

**The positive part:**
- Adaptive + `static` with g ≤ 1e-5: r_cond ≤ 0.11% in **8 of 8** groups, where fixed z = 1 violates in all 8.
- ion_proj + `ols_reset`: ≤ 0.6% in all 6 groups.

**T2 PASS.** Fixed z = 2 violates in 7 of 20 groups. **U2-like:** fixed z = 3 also violates in 5 of 20 (Wald collapse again).

**T3 PASS.** Where both are safe, adaptive delivers ≥ fixed z = 3 in **15 of 15** groups, often 2–4×. Example, ion_proj population B, no drift, `static`: fraction of oracle 0.297 at r 0.02%, against fixed z = 3 at 0.173 and fixed z = 2 at 0.259.

**T4 CONFIRMED (expected limitation).** `static` at g = 1e-4: adaptive r_cond 1.1–4.3% in 4 of 4 groups. Drift bias is not in the error model.

**Interpretation.** The self-calibrating rule turns the risk law into a controller that holds conditional risk across path populations, without a dev set and at higher goodput than a conservative fixed rule. It does so **provided the estimator's SE is honest and its bias is zero**. The two failure modes are named and testable: SE collapse (v11) and drift bias (needs a bias term).

## E29: v11 (Agresti–Coull SE), PSC (5 Oct 2026; job 47438937, 8 × 16 cores, about 2.8 min each, **5.7 SU**). U1 PASS, U2 FAIL, T3 PASS

**Run.** `des_v11_psc/runs.csv`, sha256 `b1507c58…`. Python 3.12.7 / numpy 1.26 on Bridges-2. Analysis output in `des_v11_psc/analysis_v11_out.txt`.

**U1 PASS.** Adaptive r_cond ≤ 1% in **all 20** target groups (max 0.725%, ion_2020 A g = 1e-5, 1 of 138). Same paths as v9: adaptive + `ols_reset` bad pairs fell from 155 to 3, while qualified deliveries fell to 0.79× of v9. For `static`, AC changes almost nothing (0.99×).

**U2 FAIL.** Fixed z = 3 still violates in 3 groups, all ion_2020 + `ols_reset`: 5.6% (2/36), 20% (7/35), 1.66% (3/181), so the counts are small. With honest SE, a per-decision z = 3 still does not control r_cond where most attempts are sub-threshold. This is the base-rate (FDR) mechanism of E22–E24 again, and the self-calibrating rule handles it.

**T3 PASS.** Adaptive qualified count ≥ fixed z = 3 in **17 of 17** groups where both are safe.

**T4 (expected) CONFIRMED again.** `static` at g = 1e-4: 1.2–4.5%.

**PSC accounting.** 5.7 SU (v11) + about 0.3 SU (v10 test 47438275, cancelled on Claude's advice after E27). Total **≈ 6 of 400 SU**.

**Next.** v10b frontier map re-specified with RunV11 (`drift_queue_des_v10b.py` sha `b44fc6e5…`, `README_v10b.md` sha `99786b01…`, predictions M1–M3, ceiling 240 SU).

## E30: v10b frontier map, PSC (5 Oct 2026; job 47439542, 20 × 16 cores, about 12–14 min each, **≈ 69 SU**). M1 PASS, M2 FAIL, M3 FAIL (narrowly)

**Run.** `des_v10b_psc/runs.csv`, sha256 `a25bfc2c…` (10,368 path-runs). Analysis `analyze_v10b.py`; output `des_v10b_psc/analysis_v10b_out.txt`; per-cell table `cells.csv`.

**M1 PASS.** Pooled r_cond ≤ 1% in **all 118** checked cells (≥ 200 deliveries; `ols_reset:adaptive` at all g, `static:adaptive` at g ≤ 1e-5). By contrast:
- `static:fixed2` violates in 10 of 81 cells;
- `static:adaptive` at g = 1e-4 violates in 3 of 25 (known drift bias).

**M2 FAIL, in the opposite direction.** Raising q from 0.001 to 0.03 costs ion_future nothing (L = 2: 0.578 → 0.578), while ion_2020 L = 2 drops 0.079 → 0.002 (−97%) and ion_proj L = 3 drops 0.184 → 0.035. Readout error matters where **headroom above threshold is thin**, not where links are best. That is consistent with the risk law: q inflates s, which only matters when attempt mass sits near threshold. The E5 "SPAM dominates the cost when q > p/4" statement concerns *calibration pairs*, not goodput at fixed rho, and does not carry over to this regime.

**M3 FAIL (0.78 vs a 0.80 bar).** Most violations are noise-level rises in flat regions (ion_future, L = 1 rows, identical to 3 decimals).

**Structure of the frontier:**
1. L = 1 caps at about 0.63–0.65 for every preset and method. That is the calibration share (users get (1 − rho)·R = 0.7R), not estimation.
2. Feasibility is set by oracle headroom: the oracle itself delivers 0 at ion_2020 L ≥ 3 and only ~10–40 per path at ion_proj L = 4.
3. Inside the feasible region, the calibrated loss concentrates at the **edge**: ion_2020 L = 2 (0.08 of oracle), ion_proj L = 3 (0.18). There, drift and readout bite.
4. ion_future is essentially lossless beyond the calibration share.

**Implication for the paper.** The headline "drift dominates" (E15/E20) is **too strong** at rho 0.3 with honest-SE adaptive control. The supported claim is narrower: losses concentrate where κ is large (thin headroom), and there drift and readout both matter.

**PSC accounting.** About 69 SU (v10b) + 6 earlier = **≈ 75 of 400 SU**.

## E31: Gate-3 novelty check (5 Oct 2026; independent subagent, about 49 searches/fetches). C1 partial, C2 partial (the stronger), C3 incremental

**C1 (risk law / false discovery): PARTIALLY NOVEL.**
- The statistics are established: Bayes, Efron local fdr, Benjamini–Hochberg, Learn-then-Test (arXiv 2110.01052).
- QKD composable security (Portmann–Renner; Tomamichel–Leverrier) and state verification (Pallister–Linden–Montanaro; Takeuchi–Morimae PRX 2018) bound *joint* rather than *conditional* failure for the same reason. *(The QKD point is cited from memory and not yet verified.)*
- Nearest network papers treat F_th as met by planning (Li et al. TCOM 2022; arXiv 2505.12459; Q-GUARD 2605.00246) or use per-estimate CIs (Oka et al. 2602.18011; 2409.19282).
- No paper found predicting r_cond for delivery controllers from the headroom histogram, and none proposing κ.
- **Must not** claim discovery of the effect. Frame it as an established principle that is missing from quantum-network delivery; κ is local fdr at threshold.

**C2 (self-calibrating controller): PARTIALLY NOVEL, and the strongest contribution.**
- Closest: Clayton et al. arXiv 2608.07163 (drift-aware belief and δ-quantile control on a deployed link, but no shot noise and no delivered-pair violation rate), LinkSelFiE (INFOCOM 2024), and LTT / conformal risk control (which need labelled calibration data).
- Agresti–Coull is textbook: present it as an engineering requirement.
- **Required:** a direct comparison with an LTT/conformal baseline that uses a dev set. Also an honest statement that the plug-in rule relies on the Gaussian model and unbiasedness, so it has no finite-sample validity guarantee.

**C3 (hardware frontier): INCREMENTAL** relative to Kumar et al. 2606.18167, Avis et al. npj QI 2023 (2207.10579) and trapped-ion repeater modelling. Present it as the application case study.

**Consequence for venue.** A PRX Quantum case is possible only if C2 holds against a strong label-based baseline, and C1 is framed as a principle the field is missing. Otherwise: Quantum / PR Applied / PRA.

## E32: v12 Learn-then-Test baseline, design and pre-registration (5 Oct 2026). OPEN (PSC)

**Files.** `drift_queue_des_v12.py` (sha `b982b2b7…`), `README_v12.md` (sha `a36f9d0f…`), `analyze_v12.py` (sha `08ec9cf7…`). 12,672 tasks (`tasks_v12.jsonl` sha `ddcefe9d…`). Predictions L1–L3.

**Design.** The baseline gets free dev labels. S0 = iid dev paths; S1 = dev paths shifted to link F0 + 0.005. Eval reuses v11 population A exactly.

**Checks before running.** A cloud smoke run of the eval z = 2 path (ion_proj, static, g = 1e-5, idx 0) reproduces the v11 PSC `fixed2` row exactly (31 / 31 / 0). The analysis pipeline was tested on synthetic data.

## E33: v12 Learn-then-Test vs the label-free controller, PSC (5 Oct 2026; job 47440981, 12 × 16 cores, about 6.3–7.5 min each, **≈ 22 SU**). L1 PASS, L2 PASS, L3 FAIL

**Run.** `des_v12_psc/runs.csv`, sha256 `5a03c05d…`. Analysis `analyze_v12.py` (`08ec9cf7…`, unchanged); output `des_v12_psc/analysis_v12_out.txt`.

**Reproducibility.** v12 eval z = 2 is identical to v11 `fixed2` in **384 of 384** path-runs (separate PSC jobs).

**Pre-registered results (fixed-sequence LTT):**
- **L1 PASS.** S0 LTT eval r_cond ≤ 1% in 10 of 10 groups. But in **8 of 10 groups LTT abstained** (it delivers nothing): fixed-sequence starts at z = 5, where dev deliveries are too few to reject.
- **L2 PASS.** Under the S1 shift, LTT violates in 1 group (ion_proj, static, g = 1e-5: 1.51%, 706 of 46,159), while adaptive is ≤ 1% in 10 of 10.
- **L3 FAIL.** Where both deliver (2 groups), adaptive gets 0.59× and 0.70× LTT's qualified count.

**EXPLORATORY: stronger LTT (Bonferroni over the z grid)** (`explore_ltt_bonf_v12.py`; output `explore_ltt_bonf_out.txt`):
- S0: 0 violations; delivers in 6 of 10 groups, often 1.0–2.3× adaptive's goodput.
- S1: **2 violations** (ion_2020 ols g = 1e-5: 5.56% on 34; ion_proj static g = 1e-5: 1.51%).
- Adaptive: 0 violations in 10 groups; ≥ LTT goodput in 5 of 10 groups (counting LTT abstentions as 0).

**Interpretation (honest).**
- With labels and no shift, LTT is valid and delivers more than the label-free rule.
- Under a modest shift (link F0 + 0.005), label-based tuning violates 1% in 1–2 of 10 groups. The label-free rule never violated in any group of v11, v10b or v12.
- The C2 claim is supported as **robustness without labels at a goodput cost (roughly 0.4–1× of LTT where LTT is valid)**, not as dominance.
- The shift effect is real but modest in size and frequency.

**PSC accounting.** About 22 SU, so **≈ 97 of 400 SU** used in total.

## E34: FINAL confirmatory protocol frozen (5 Oct 2026), before any final-run data

**Protocol.** `FINAL_PROTOCOL.md` (sha `f70198ea…`). Primary hypotheses: F1 (risk law) and F2 (label-free safety). Supporting: F3 (fixed z fails), F4 (LTT valid iid, breaks under shift), F5 (cost, descriptive).

**Code:**
- `drift_queue_des_final.py` (sha `40ee6079…`), 26,880 tasks (`tasks_final.jsonl` sha `50fe0d1f…`);
- `analyze_final.py` (sha `2a3487c6…`, tested on synthetic data);
- `drift_queue_des_final_law.py` (sha `e85527e5…`, generated by `make_final_law.sh`, sha `6d2e8312…`, from v8);
- F1 analysis: `analyze_v7.py` (`c9f06b92…`).

**Deviation logged before the run.** The S2 (F0 − 0.005) dev arm was dropped for PSC budget, before any data.

**Smoke test (cloud).** An ion_future L4 adaptive path delivered 39,398 good / 30 bad (r = 0.076%, oracle 69,075).

**Budget.** Expected 110–170 SU; ceiling 216 SU. Used before the final run: ≈ 97 of 400 SU.

## E35: FINAL CONFIRMATORY RUN (5 Oct 2026; PSC jobs 47442631 [24 × 16 cores, about 19–22 min] and 47442640 [32 cores, 7 min]; **≈ 138 SU**). F1 PASS, F2 PASS, F3 PASS, F4 FAIL (as specified), F5 reported

**Integrity.** All code and protocol hashes match `FINAL_PROTOCOL.md`:
- final `40ee6079…`, final_law `e85527e5…`, analyze_final `2a3487c6…`, analyze_v7 `c9f06b92…`, protocol `f70198ea…`;
- tasks `50fe0d1f…`.

**Data.** `des_final_psc/runs.csv`, sha256 `5baba536…` (26,880 rows); `des_final_law/runs.csv`, sha256 `670415ee…` (1,872 rows). Outputs: `des_final_law/F1_analysis_out.txt`, `des_final_psc/F2_F5_analysis_out.txt`. The analyses ran unmodified.

**F1 PASS (risk law, primary).**
- 609 runs: Spearman 0.961 (bar 0.9); median |ln ratio| 0.252 (bar 0.405); the 0.5-corrected all-runs version is 0.395.
- R1 statistic 0.0059 (bar 0.05).
- Pooled predicted vs measured r_cond agree within 1.15× in all six (g, est) groups, including g = 1e-4.

**F2 PASS (label-free safety, primary).**
- Adaptive pooled r_cond ≤ 1% in **13 of 13** groups with ≥ 200 deliveries.
- Pooled over all adaptive deliveries: 0.0081% (CP95 upper 0.0086%).
- **Caveats for the paper:**
  - The pooled figure is dominated by ion_future (millions of deliveries); per-group results are the meaningful ones.
  - Two ion_2020 groups are close to the bar with wide uncertainty: static g = 1e-5, 0.39% (2/512, CP upper 1.22%); ols g = 1e-4, 0.96% (2/208, CP upper 3.0%).

**F3 PASS.** Fixed z = 2 exceeds 1% in 5 groups (up to 27.8%).

**F4 FAIL, as specified.** LTT-Bonferroni tuned on S0 violated in **1** group (ion_2020, static, g = 1e-5: 5.85%, chose z = 2). Tuned on S1 it violated in 4. The prediction "0 S0 violations" therefore fails, so per the protocol **the paper makes no shift-robustness claim over LTT**. Descriptively:
- LTT with a pooled binomial test was not valid even in-distribution in 1 of 15 groups, plausibly because deliveries cluster by path (they are not iid);
- adaptive had 0 of 13 violations.

This is reported as a descriptive observation, not a confirmed hypothesis.

**F5 (descriptive).** Median adaptive / LTT-S0 qualified ratio 0.723 over the 11 groups where LTT delivers; LTT-S0 abstains in 4 of 15. Adaptive fraction-of-oracle (95% path-bootstrap CI):
- ion_future 0.50–0.57;
- ion_proj 0.002–0.14;
- ion_2020 ≤ 0.03.

**PSC accounting.** ≈ 138 SU, so total **≈ 235 of 400 SU**.

**Evidence archive (5 Oct 2026).** Tanish created `~/Documents/Study18C_FINAL_evidence_2026-10-05.tgz`, sha256 `bf76cbf03f055253510238b7a8abdb68b276ccd134f896d342438f0888e0a096`. Intended contents: the frozen protocol, final code, analysis scripts, `des_final_psc`, `des_final_law`, and this ledger as of E35. Completeness **VERIFIED** by Tanish: 64 entries, including `des_final_psc/runs.csv`, `des_final_law/runs.csv`, `FINAL_PROTOCOL.md`, `analyze_final.py`, `analyze_v7.py` and `EVIDENCE_LEDGER.md` (as of E35).

**PSC balance check (5 Oct 2026, by Tanish).** Bridges-2 Regular Memory shows 9,634 / 10,000 SU, against 9,869 when the 400 SU cap was approved. That is **235 SU used**, exactly matching the ledger estimate (6 + 0.3 + 69 + 22 + 138). Remaining under the cap: **165 SU**.

## E36: Response to external critique, part 1: theory note and v14 baseline pre-registration (5 Oct 2026)

**Tanish's decision.** Start the plan: novelty statement, assumptions and limits, appropriate baselines, generality, relevance beyond the simulator. The cap stays at 400 SU for now (165 SU remain); no increase has been approved.

**`THEORY_NOTE.md`** (sha `0b0b4b00…`) contains:
- the exact Bayes risk identity r = π₀α / (π₀α + (1 − π₀)β);
- the headroom-histogram law (validated by F1);
- **Proposition 1** (no fixed per-decision rule bounds conditional risk; proof by a two-point mixture), with bounded-error and Bayesian/δ-quantile corollaries;
- the local-fdr link;
- an assumptions table A1–A7, with observed failure modes;
- a known-vs-new table.
- Limit stated: the label-free rule has no finite-sample guarantee.

**v14 pre-registration.** `README_v14.md` (sha `807e83d9…`) with hypotheses B1–B4:
- code `drift_queue_des_v14.py` (sha `0bfa4d38…`), tasks `3447f462…` (21,760);
- locked analysis `analyze_v14.py` (sha `7d42f5ef…`), tested on synthetic data;
- adds cluster-aware LTT (path bootstrap), the δ = 0.10 quantile rule (Clayton-style) and the Bayesian flat-prior 1% rule;
- fresh seeds;
- PSC ceiling 96 SU.

## E37: v14 statistically appropriate baselines, PSC (6 Oct 2026; job 47446238, 12 × 16 cores, 11.9–14.2 min, **≈ 43 SU**). B1 FAIL (n = 9), B2 PASS, B3 PASS

**Integrity.** Module `0bfa4d38…` and tasks `3447f462…` match the pre-registration. Data: `des_v14_psc/runs.csv`, sha256 `a9e305d0…` (21,760 rows). Analysis `analyze_v14.py` (`7d42f5ef…`, unchanged); output in `des_v14_psc/analysis_v14_out.txt` and `v14_groups.csv`.

**B1 FAIL.** Cluster-aware LTT tuned on S0 violated in 1 of 8 delivering groups: ion_proj, ols_reset, g = 1e-4, which chose z = 3.5 and delivered **9 pairs, 1 bad (11%)**. The other 7 were ≤ 0.6%. The sample is tiny, but the pre-registered rule has no minimum-delivery clause, so it counts as a failure. Contrast: the pooled-binomial LTT (as in the final run) violated in 2 groups under S0.

**B2 PASS.** Under the S1 shift, cluster-aware LTT violated in **4** groups (1.17%, 1.21%, 1.25%, 3.73%). Label-free adaptive: **0 of 9** groups with ≥ 200 deliveries (max 0.142%; CP95 upper ≤ 0.58%). Pooled-binomial LTT under S1: 5 violations.

**B3 PASS (Proposition 1 borne out).**
- δ = 0.10 quantile / belief rule (z = 1.28, Clayton-style) exceeded 1% in **8** groups (up to 30.8%).
- Bayesian flat-prior "P(bad) ≤ 1%" rule (z = 2.33) exceeded 1% in **3** groups (2.06%, 2.39%, 13.6%).

**B4 (descriptive).**
- Median adaptive / cluster-LTT-S0 qualified ratio 0.663 over 8 groups.
- Cluster-LTT-S0 abstained in 2 of 10 groups (ion_2020 ols g = 0 and g = 1e-4), where adaptive delivered 515 and 715 pairs with 0 bad.
- Adaptive abstained entirely in ion_proj ols g = 1e-4; cluster-LTT delivered 9 there, 1 of them bad.

**Interpretation.** Against a statistically appropriate (cluster-aware) labelled baseline, the label-free controller:
- was the **only method with 0 violations in both scenarios**;
- delivered about two-thirds as much as cluster-aware LTT where LTT was valid;
- delivered where LTT abstained.

Per-decision belief rules, Bayesian or δ-quantile, failed as Proposition 1 predicts. This is the strongest comparative result so far, and it is pre-registered.

**PSC accounting.** About 43 SU, so total **≈ 278 of 400 SU** (122 left).

## E38: v15 generality / assumption-stress sweep, pre-registration (6 Oct 2026). OPEN (PSC)

**Files.** `README_v15.md` (sha `fddf3632…`), hypotheses G1–G4. Code `drift_queue_des_v15.py` (sha `8ea82ead…`), tasks `22ef330b…` (5,632). Locked analysis `analyze_v15.py` (sha `8312add0…`), tested on synthetic data.

**Variants.** Thresholds 0.85 and 0.95; NV-like and SiV-like hardware at τ = 0.80; uneven links (×3 spread); best-of-3 path choice; controller memory-model mismatch (T2 1.3 s / 0.7 s vs a true 1.0 s).

**Smoke finding.** Adaptive abstains entirely on some marginal paths (< 20 supporting attempts). This was reproduced with the unmodified v11 controller, so it is a cost, not a v15 bug.

**Ceiling.** 64 SU.

## E39: v15 generality / stress sweep, PSC (6 Oct 2026; job 47453896, 8 × 16 cores, 6.0–7.3 min, **≈ 14 SU**). G1 FAIL (NV-like), G2 CONFIRMED, G3 PASS

**Integrity.** Module `8ea82ead…` and tasks `22ef330b…` match the pre-registration. Data: `des_v15_psc/runs.csv`, sha256 `47a2e4bb…` (5,632 rows). Analysis unchanged (`8312add0…`); output in `des_v15_psc/analysis_v15_out.txt`.

**G1 FAIL.** Adaptive exceeded 1% in **4 of 32** eligible groups, **all NV-like** (F0 0.82, 9 Hz, readout q = 0.03, τ = 0.80): static 1.40% and 1.47%; ols_reset 8.0% and 8.3%. Safe (≤ 0.15%) in every other variant:
- thresholds 0.85 and 0.95;
- uneven links;
- best-of-3 path choice;
- pessimistic memory model.

**Diagnosis (cloud, post hoc, exploratory).**
- Unconditional standardized per-link λ errors at NV settings have mean ≈ 0 and sd ≈ 1.0, **but heavy tails**: P(z > 3) = 0.42% (static) and 0.52% (ols), against 0.13% for a Gaussian.
- With low rate and high readout error, s_F is large relative to headroom (mean s_F 0.029 vs 0.007 for ion-2020 at τ = 0.85). Deliveries then happen in the error tail, where the Gaussian plug-in Φ(−d/s) underestimates risk.
- **Assumption A1 (Gaussian tails) fails for low-rate, high-readout-error hardware.** This is a new, stated limitation.
- Candidate fix (not yet tested): an exact-binomial or likelihood-based posterior in place of the Gaussian plug-in.

**G2 CONFIRMED (expected limitation).** With an optimistic memory model (assumed T2 1.3 s vs a true 1.0 s), static adaptive exceeds 1% (1.68%, 2.01%). ols_reset stays ≤ 0.21%. The pessimistic model is safe (0 bad), at a large goodput cost.

**G3 PASS.** Fixed z = 2 exceeds 1% in 3 variants: NV (up to 14.8%), SiV L1 (10.7%), and t2_opt (1.19%).

**G4 (descriptive).**
- At τ = 0.85, adaptive keeps **0.80** (ion-2020 L2) and **0.65** (ion-proj L3) of the oracle, versus ≤ 0.03 and ≤ 0.14 at τ = 0.90. The frontier is extremely threshold-sensitive.
- τ = 0.95: 0.59 (ion-proj L1), 0.30 (ion-future L3).
- uneven 0.24; best-of-3 0.05, with heavy abstention (z_inf 0.82).
- SiV-like L1: 0.012; **SiV-like L2: the oracle delivers nothing** (infeasible).

**PSC accounting.** About 14 SU, so total **≈ 292 of 400 SU** (108 left).

## E40: v16 calibrated-posterior controllers, pre-registration (6 Oct 2026). Post-hoc improvement; E39 G1 stays FAIL
- **Files** (`18c_drift_frontier/`, sha256 first 16):
  - `drift_queue_des_v16.py` bf7882e7948b5749
  - `tasks_v16.jsonl` d8217837d7566ed3 (3,584 tasks)
  - `analyze_v16.py` 4d50170ec09ee715
  - `README_v16.md`
- **Methods:**
  - Gaussian `adaptive` (v11)
  - Jeffreys `exact` (Monte-Carlo posterior)
  - fleet-prior `pop` (path law minus a uniform sawtooth offset), plus `popwide` (sd ×2) and `popopt` (mean +1 sd)
- **Cloud dev pilot.** Seeds 19931/19932, disclosed. Exact likelihood alone still violated on NV; a prior without the drift offset failed (ion-proj 1.91%); the drift-aware prior was safe.
- **Peeking.** Smoke tests ran 9 confirmatory tasks (paths 0–3) for runtime only.
- **Hypotheses:**
  - H1: `pop` ≤ 1% in every group.
  - H2: `exact` > 1% in ≥ 1 NV group.
  - H3: Gaussian replicates the NV failure.
  - H4: `pop` ≥ 0.8× Gaussian qualified deliveries in the ion cells.
  - H5: `popopt` > 1% in ≥ 1 group.

## E41: v16, PSC (6 Oct 2026; 8 × 16 cores, 258–291 s, **≈ 10 SU**, total ≈ 302 / 400). H1 PASS (fragile in 1 group), H2–H5 as predicted
- runs.csv sha 44cd1014012262d3; module/analysis hashes verified on the Mac.
- **H1 PASS.** `pop` r ≤ 1% in 8/8 groups:
  - NV: 0 / 3591 and 2 / 3618;
  - ion-proj L3: 0.18% and 0.39%;
  - τ 0.85: 0.34% and 0.47%;
  - ion-2020 L2 τ 0.9: 0.17% and **0.80% (8 / 1001; 7 bad on one path)**.

  **Caveat (descriptive path bootstrap, B = 4000):** the 95% upper bound for that ion-2020 group is 2.04%, so in that thin cell the pass is a point estimate only. Every other `pop` group has an upper bound ≤ 0.6%.
- **H2 CONFIRMED.** Jeffreys `exact` on NV with ols: 1.89% and 1.49%. `exact` also violates in ion-2020 (static g = 0: 1.50%; ols: 3.65% and 1.09%). A flat prior is not enough, even at higher SNR.
- **H3 REPLICATED.** Gaussian adaptive on NV: ols 5.63% and 5.78%; static g = 0: 1.13%.
- **H4 PASS.** `pop` qualified deliveries relative to Gaussian (static): ion-2020 1.81× and 1.28×; ion-proj 1.60× and 1.61×; τ 0.85 1.06× and 1.05×.
- **H5 CONFIRMED.** `popopt` violates in 3 of 8 groups (NV 1.47% and 1.32%; τ 0.85 at g 1e-5: 1.09%).

  **Also: `popwide` violates in 1 of 8 groups** (ion-2020 g = 0: 1.22%). The wider prior is closer to flat, so it is NOT safely conservative.
- **Interpretation:**
  - The guarantee needs a calibrated posterior: A1 is restated as posterior calibration, giving r = E[lfdr | delivered] under the true prior.
  - The Gaussian rule is a conservative high-SNR approximation; it fails at low SNR.
  - Sensitivity runs both ways (optimistic and wide priors).
  - In the simulation the prior equals the generating law, which is the best case.
- **Thin regime.** In the ion-2020 τ 0.9 cells every method delivers only 1–13% of the oracle.

## E42: v17 estimated (empirical-Bayes) fleet prior, pre-registration (6 Oct 2026). OPEN (PSC)
- **Files** (`18c_drift_frontier/`, sha256 first 16):
  - `drift_queue_des_v17.py` 604f743db935a327
  - `tasks_v17.jsonl` a8993752fa82df12 (6,144 tasks, 128 fresh paths, seeds 18951–18953)
  - `analyze_v17.py` f3240a28624e589a
  - `README_v17.md`
- **Method.** The prior is estimated from K other fleet paths' parity counts (hierarchical Bayes, posterior-predictive). No labels; drift amplitude known.
- **Dose-response:** `eb8`, `eb32`, `eb128` (one window each) and `eb32x10`; plus `pop` (oracle) and Gaussian `adaptive`.
- **Cloud dev pilot** (seeds 19951–19953): NV failed with `eb8` (3.75/2.36%) and `eb32` (3.05/1.46%); `eb128` and `eb32x10` gave 0 bad. No runs on confirmatory seeds.
- **Hypotheses:**
  - V1: `eb128` & `eb32x10` ≤ 1% in every group.
  - V2: path-bootstrap 95% upper bound ≤ 1% (stricter).
  - V3: small fleets break on NV.
  - V4: `pop` replicates.
  - V5: `eb128` ≥ 0.8× `pop`.

## E43: v17, PSC (6 Oct 2026; 8 × 16 cores, 454–567 s, **≈ 17.8 SU**, total ≈ 320 / 400). V1 PASS, V2 PASS, V3 CONFIRMED, V4 REPLICATED, V5 PASS
- runs.csv sha 696020b0005701fa; module and tasks hashes verified in the shard metadata.
- **V1 PASS.** `eb128` and `eb32x10`: r ≤ 1% in 16/16 groups.
  - NV: eb128 0/4953 and 0/5226; eb32x10 1/4969 and 2/4989.
  - Maximum anywhere 0.40% (ion-proj and τ 0.85 cells).
- **V2 PASS.** Path-bootstrap 95% upper bound ≤ 0.49% in all 16 groups.
- **V3 CONFIRMED.** Too little fleet data breaks it on NV:
  - eb8: 1.39% and 1.32%;
  - eb32: 1.01% (g = 0; bootstrap upper bound 2.36%, one path holds 44 bad) and 0.51%.

  **Mechanism (descriptive).** eb32 paths whose fleet estimate was optimistic by more than 0.5 population sd: r = 1.46%; all others: 0.09%.
- **V4 REPLICATED.** `pop` ≤ 1% in all 8 groups. The v16 fragile ion-2020 τ 0.9 cell (0.80%) is now 0.10% and 0.13% with 128 fresh paths, so v16's value was driven by one bad path.
- **V5 PASS.** eb128 / pop qualified ratio is 0.976–1.115 (NV 1.05 and 1.12).
- **Gaussian adaptive on NV:** 1.39% and 1.35%. This is the third independent replication of the low-SNR failure.
- **Cost (fraction of oracle):**
  - NV: safe methods 0.12–0.14 vs unsafe Gaussian 0.21;
  - ion-proj: eb and pop 0.22 vs Gaussian 0.13 (≈ 1.7×);
  - ion-2020 τ 0.9: 0.17 vs 0.14; τ 0.85: 0.89 vs 0.86.
- **Note.** ion-2020 τ 0.9 per-path oracle volume differs about 2.5× between the v16 and v17 path draws: the cell sits near feasibility.
- **Remaining caveat.** The empirical-Bayes model family matches the generator (Normal fleet, known drift amplitude). A misspecification stress is not yet run.

## E44: v18 misspecification stress for the empirical-Bayes controller, pre-registration (6 Oct 2026). OPEN (PSC)
- **Files** (`18c_drift_frontier/`, sha256 first 16):
  - `drift_queue_des_v18.py` 0d53da93eb90bf2f
  - `tasks_v18.jsonl` dc2201b4fef76d28 (10,240 tasks, 128 fresh paths, seeds 18961–18963)
  - `analyze_v18.py` 6aa06ebad379de03
  - `README_v18.md`
- **Design.** The controller's model stays fixed (Normal fleet fit, assumed drift amplitude) while the truth or the assumption changes:
  - t3 heavy-tailed fleet;
  - mixlow / mixhigh (15% of links at −3 / +3 sd);
  - drift amplitude assumed 0.01 or 0.03 (truth 0.02).

  Methods: eb128 and eb32x10.
- **Cloud dev pilot** (seeds 19961–19963). Everything was safe except t3 on ion-proj: 2.25% (13/579, 5 paths). This was flagged in advance as at risk.
- **Hypotheses:**
  - S1: fleet-law shape (t3, mixlow, mixhigh), r ≤ 1% in every group.
  - S2: drift amplitude ±50%, r ≤ 1%.
  - S3: descriptive.
- A first submission attempt produced no output: the files never reached PSC because the browser download failed. SU charged by that attempt is not verified (likely negligible); check `sacct` if exact accounting is needed.

## E45: v18, PSC (6 Oct 2026; 8 × 16 cores, 872–996 s, **≈ 33.8 SU**, total ≈ 354 / 400). S1 PASS, S2 PASS (two near-limit cells)
- runs.csv sha b818316cae60ee45; module and tasks hashes verified in the shard metadata; 10,240 / 10,240 tasks.
- **S1 PASS.** Fleet-law shape: 0 violations in 48 groups.
  - t3 max 0.745%; mixlow max 0.455%; mixhigh max 0.574%.
  - **Fragile cell:** t3, NV, g 1e-5, eb128: 0.745%, but the path-bootstrap upper bound is 2.09%. One path (idx 37, link F0 ≈ 0.78, a lower-tail outlier) holds 33 of the 35 bad deliveries.
  - **Mechanism:** the Normal empirical-Bayes fit under-estimates the fleet spread (geometric-mean s_hat ≈ 0.007 vs true sd 0.036), so an outlier path is shrunk toward the fleet mean.
  - eb32x10 in the same cell: 0.23%.
- **S2 PASS.** Drift amplitude ±50%: 0 violations in 32 groups.
  - amp01 (optimistic) max 0.39%.
  - **amp03 (pessimistic) max 0.94%** (ion-proj g 1e-5, eb128; upper bound 1.12%). Over-stating the drift is NOT conservative; it pushes the prior up. This matches v16's finding that a wider prior is not safer.
- **Dev pilot vs confirmatory.** The pilot's t3 ion-proj alarm (2.25%, 5 paths) did not replicate: confirmatory 0.31–0.41% on 128 paths.
- **Cost.** Fraction of oracle is similar to v17 under every stress (NV 0.09–0.25; ion-proj 0.17–0.30; τ 0.85 0.80–0.92).
- **Reading.** The controller is robust in point estimate to every pre-registered misspecification. The stated limits are:
  1. Heavy-tailed fleets can hide individual outlier paths (clustered uncertainty above 1% in one cell).
  2. Drift-amplitude error in either direction erodes the margin.

  Per-path outlier screening is suggested as future work, not claimed.

## E46: B: is the parity likelihood calibrated on the other agent's NetSquid calibration bits? (6 Oct 2026, read-only)
- **Script** `22_external_checks/check_parity_posterior_calibration.py` (sha 4ddac929), output `parity_posterior_calibration.json` (cb523edc).
- **Source data, read-only:** `Files11-EndToEnd-PRX/prx_work/21_live_parity_law/runs`. 20 seeds × 54 cells × 30 shots = 32,400 NetSquid-generated parity bits:
  - four-node loaded route;
  - T1/T2 memories;
  - X/Y/Z bases × holds 0/200/800 µs.
- **Test.** The Jeffreys Beta posterior for each cell's positive-parity probability (the likelihood v16–v18 use) is evaluated at the known channel value. The reference is a 2,000-replicate parametric null that accounts for discreteness.
- **Result: calibrated.**
  - Optimistic 1% tail: 0.83% (null mean 1.03%, p = 0.77).
  - 95% coverage: 95.9% (null 95.5%).
  - PIT KS: p = 0.735.
  - Per basis × hold: optimistic 1% tail 0–2.5% on 120 cells each (the largest is Z @ 800 µs: 3/120).
- **Caveats** (inherited from that study):
  - the seed set was fixed after seed 69601 was inspected;
  - cells within a seed share a timeline;
  - known parameters are used only after generation.
- **Not usable:** that agent's delivery outcomes. The pre-correction `run_batch` used an oracle veto, the later archives have a seed collision, and the loaded runs use a zero-score diagnostic policy. So **no delivery-risk check is possible on their data**; only the parity-likelihood check is.

## E47: v19 non-Werner (T1/T2) memories, pre-registration (6 Oct 2026). OPEN (cloud run)
- **Files** (`18c_drift_frontier/`):
  - `memory_t1t2_exact.py` fc044e14
  - `netsquid_t1t2_check.py` 447cf33c (for the Mac)
  - `memory_bias_scan.py` 4d498cf9
  - `drift_queue_des_v19.py` 541b21bf
  - `tasks_v19.jsonl` 55b8fa84 (768 tasks)
  - `analyze_v19.py` 1e2a0a57
- **Self-check.** With depolarizing storage, the exact model equals the controller model to 3.9e-6.
- **Disclosed bias scan** (true F minus model F):
  - dephasing-only: model pessimistic everywhere;
  - T1 = T2: ≈ 0 (NV down to −0.014 on 2%);
  - AD limit (T2 = 2 T1): model optimistic (median −0.008 to −0.016).
- **Hypotheses:**
  - N1: `deph` safe in 4/4 cells.
  - N2: `t1eq` safe in 4/4.
  - N3: `ad` breaks (expected limitation).
  - N4: paired, dephasing never adds bad deliveries.

## E48: A: NetSquid validation of the exact T1/T2 memory model (6 Oct 2026, your Mac). PASS
- **Script** `18c_drift_frontier/netsquid_t1t2_check_v2.py` (sha 6493d55a), seed 22201, 1,500 trials per case, 76.9 s → `netsquid_t1t2_check.json`.
  - v1 crashed before any physics: NetSquid rejected T1 = 0.
  - v2 represents T1 = ∞ as 1e6·T2 in both NetSquid and NumPy.
- **Part 1, channel.** max |density-matrix difference| = 2.2e-16 across 8 (T1, T2, t) cases. **PASS** (pre-set < 1e-9).
  - Cases with T2 ≤ T1 used NetSquid's `T1T2NoiseModel`.
  - The amplitude-damping limit (T1 = T2/2) is **rejected by `T1T2NoiseModel`'s constraint**. It was validated with NetSquid primitives instead (`amplitude_dampen` + `dephase`).
- **Part 2, end to end.** Full delivered-pair protocol: Werner links, T1/T2 storage, noisy swaps, hold, DEJMPS, postselection. 24/24 cases within 4 SE + 1e-4, max |diff| 8e-5. **PASS**.
- **Consequence.** `memory_t1t2_exact.py` is a validated stand-in for NetSquid with T1/T2 memories, which closes E14's "non-Werner states not validated" gap. The bias scan and v19 rest on it.

## E49: v19, non-Werner (T1/T2) memories end to end (6 Oct 2026; cloud, 2 cores, ≈ 2.9 h incl. one container restart + resume; 0 SU). N1 PASS, N2 PASS, N3 CONFIRMED, N4 YES
- runs.csv sha 6aa6bbee8a5bc279; 768 / 768 tasks; module, tasks and analysis hashes as in E47.
- **Design.** Paired: the controller's decisions are identical across memory regimes, so the delivered sets are the same and only the truth label changes.
- **N1 PASS. Dephasing-only memories (T1 ≫ T2):** **0 bad in 438,764 deliveries** across 4 cells. The model is pessimistic (mean true − model +0.004 to +0.010).
- **N2 PASS. T1 = T2:** r ≤ 0.51%.
  - ion-2020 τ 0.9: 0.51% (bootstrap upper bound 1.07%);
  - ion-proj 0.45%; τ 0.85 0.33%; NV 0.
  - Close to the Werner-truth values (0.56 / 0.48 / 0.38%).
- **N3 CONFIRMED (limitation). Amplitude-damping limit (T2 = 2 T1):**
  - ion-proj **38.6%**, ion-2020 **16.2%**, τ 0.85 **10.0%**;
  - NV 0.90% (upper bound 2.2%).

  The model is optimistic by 0.004–0.009 on the delivered pairs, and that is decisive near threshold.
- **N4 YES.** Dephasing never adds bad deliveries relative to the Werner truth.
- **Reading.**
  - With T2 interpreted as the memory coherence time, the depolarising controller model is safe for memories with T1 ≳ T2 (trapped ions, nuclear-spin memories).
  - It is **unsafe for amplitude-damping-limited memories** unless the controller models amplitude damping.
  - The convention caveat stands: if T2 is fitted to fidelity decay instead, the dephasing margin shrinks.

## E50: v20 T1-aware controller, pre-registration (7 Oct 2026). OPEN (PSC)
- **Files** (`18c_drift_frontier/`):
  - `ptm_model.py` bf59d252 (vectorised Pauli-transfer form of the exact T1/T2 model; matches it to 6e-16 in all regimes, L 1–3)
  - `drift_queue_des_v20.py` d3242555
  - `tasks_v20.jsonl` 7523813a (1,536 tasks, 64 fresh paths, seeds 18981–18983)
  - `analyze_v20.py` 6ffdf7c9
  - `README_v20.md`
  - Also needs `memory_t1t2_exact.py` (fc044e14) and `drift_queue_des_v19.py` (541b21bf) on PSC.
- **Configs:** ad/depolarising (replication), ad/T1-aware, ad/T1-aware with T1 +25%, t1eq/T1-aware, deph/T1-aware, deph/depolarising.
- **Cloud dev pilot** (seeds 19981–19983, 2–12 paths):
  - T1-aware ad: ion-proj 0.88%, τ 0.85 0.61% (vs 41.5% / 11.9% depolarising);
  - T1 +25%: 9.9% / 4.0%;
  - t1eq ion-proj **1.20% (4 paths)**;
  - deph ion-proj 6.7× deliveries.
- **Hypotheses:**
  - Q1: T1-aware ≤ 1% in every cell under ad/t1eq/deph.
  - Q2: depolarising under ad > 1% (replication).
  - Q3: T1 +25% > 1% in ≥ 1 cell.
  - Q4: under deph, T1-aware ≥ depolarising in qualified deliveries.

## E51: v20 T1-aware controller, PSC (7 Oct 2026; 8 × 16 cores, 273–396 s, **≈ 11.6 SU**, total ≈ 366 / 400). Q1 PASS, Q2 REPLICATED, Q3 CONFIRMED, Q4 PASS
- runs.csv sha 58cc2295383ced45; module and tasks hashes verified in the shard metadata; 1,536 / 1,536 tasks.
- **Q1 PASS.** The T1-aware controller with correct T1: r ≤ 1% in 12/12 cells under ad, t1eq and deph.
  - Max r 0.52%; max path-bootstrap upper bound 0.73%.
  - Amplitude-damping limit: ion-2020 0.52%, ion-proj 0.48%, τ 0.85 0.52%, NV 0.
- **Q2 REPLICATED.** The depolarising controller under amplitude damping fails: ion-2020 15.0%, ion-proj 37.3%, τ 0.85 8.7% (NV 0.43%).
- **Q3 CONFIRMED (sensitivity limit).** With T1 over-estimated by 25%: ion-2020 2.2%, ion-proj 6.2%, τ 0.85 3.1% (NV 0.17%). **T1 must be known to better than 25%.**
- **Q4 PASS.** Under dephasing-only memories, the T1-aware controller removes the depolarising model's pessimism:
  - qualified deliveries 5.1× (ion-2020), 3.8× (ion-proj), 2.3× (NV), 1.02× (τ 0.85);
  - at r ≤ 0.07%.
- **Dev pilot vs confirmatory.** The pilot's t1eq ion-proj 1.20% (4 paths) did not replicate: 0.40% on 64 paths.
- **Reading.** The amplitude-damping limitation (E49) is resolved *given a T1 estimate accurate to within 25%*. The depolarising model leaves 1–5× throughput on the table for ion-like memories.

## E52: PSC accounting check (7 Oct 2026, `projects` after v20)
- Bridges-2 RM balance: **9,515 / 10,000 SU**.
- From the post-final-run checkpoint (9,634, which matched the 235 SU project total exactly), the drop is 119 SU for v14–v20.
- **Project total charged ≈ 354 SU of the 400 approved.**
- Timing-based estimates were 85 SU for v14–v17 (the account matched exactly) and 45.4 SU for v18 + v20, but the account dropped only 34 SU over that span. Either v20 is not yet fully posted, or elapsed × cores over-estimates the charge.
- Worst case using the timing estimate: ≈ 366 SU. Either way it is within the cap. GPU allocation untouched (200 / 200).

## E53: C1, confirmatory run of the FROZEN final controller, pre-registration (7 Oct 2026). OPEN (PSC). PSC cap raised to 1,000 SU by the user
- **Files:** `drift_queue_des_c1.py` 070acce4; `tasks_c1.jsonl` 2f93b652 (16,384 tasks); `analyze_c1.py` 24241553; `README_C1.md`.
- **Frozen controller:** eb128 empirical-Bayes fleet prior, T1/T2-aware Pauli-transfer fidelity model, window local-fdr threshold.
- **Design:**
  - Block A: 8 cells × 2 g × 3 memories, 256 paths (confirmatory).
  - Block B: 8 cells × 3 fleet laws, 128 paths (confirmatory).
  - Block C: unannounced 2-sd link fault, 128 paths (exploratory).
  - Same-seed oracle for cost.
- **Cloud dev pilot** (seeds 19991–19994; runtime and code checks only; nothing tuned). **At-risk cells flagged before the run:**
  - ion-future L3 τ 0.95, amplitude damping: 1.37% (2 paths);
  - SiV L1, dephasing: 5/98 bad on 8 paths, against a mean predicted risk of 1.2%.
- **Hypotheses:**
  - C-A1 (primary): Block A ≤ 1% in every group.
  - C-A2: bootstrap upper bound ≤ 1%.
  - C-B: Block B ≤ 1%.
  - C-C: exploratory.
  - D: cost.
- **Commitment:** no re-tuning and no new-seed re-run to make it pass.

## E54: C1, frozen final controller, confirmatory (7 Oct 2026; 16 × 32 cores, max 2,068 s; timing estimate ≈ 274 SU; account showed 9,503 shortly after, likely billing lag). C-A1 FAIL, C-A2 FAIL, C-B FAIL, C-C unsafe
- runs.csv sha 49b52dbbaf717cdb; 16,384 / 16,384 tasks; module and tasks hashes verified in the shard metadata.
- **C-A1 FAIL (pre-registered verdict).** 7 of 48 groups exceed 1%:
  - **all 6 SiV-like groups**, 1.97–5.79% (bootstrap upper bound up to 9.4%; bad spread over 97 of 1,536 paths, not a single outlier);
  - **ion-future L3 τ 0.95, amplitude damping, g 1e-5: 1.43%** (upper bound 1.54%).

  Both were flagged at risk before the run.
  - *Post hoc, labelled as such:* all other 41 of 42 groups pass, max 0.80%. These include NV, ion-2020, ion-proj, τ 0.85 ×2, ion-proj L1 τ 0.95, and ion-future dephasing / T1 = T2.
- **C-A2 FAIL.** The same 7 groups.
- **C-B FAIL.** 3 of 24 groups, all SiV (1.1%, 8.0%, 3.7%). Every non-SiV fleet-law stress passes (max 0.78%; NV t3 upper bound 2.2%).
- **C-C (exploratory). Unannounced 2-sd link fault: UNSAFE in 7 of 8 cells.** Post-fault r:
  - ion-2020 100% (11 paths); SiV 40%; NV 31%; ion-proj 4.5%; τ 0.85 ion-2020 3.4%; ion-future 2.3%; ion-proj L1 1.7%;
  - τ 0.85 ion-proj 0.015% (the exception).
- **Mechanism (diagnosed post hoc on confirmatory task C / tau095_ionproj1 / 48, deterministic replay).**
  - After the 100 s window catches up, the window-average λ equals the truth (0.9142), but the posterior mean stays at 0.9227: +2 posterior sd, persistently.
  - The empirical-Bayes fleet prior (λ sd ≈ 0.008) is tighter than one window's data (≈ 0.013), so a degraded link is shrunk back toward the fleet. **The controller assumes each path is exchangeable with the fleet. A faulted or outlier link breaks that assumption, and the controller cannot see it.**
  - Same family as the v18 t3 outlier path.
- **SiV mechanism (interpretation).** About 30 parity pairs per window, so the 128-window fleet sample has only ≈ 3,800 pairs. The fleet spread is poorly identified, the prior is over-confident, and calibration fails. The fleet-data requirement is in *pairs*, not windows.
- **Cost (fraction of oracle).** τ 0.85 cells 0.62–0.91; ion-proj L1 0.62–0.65; ion-future 0.39–0.52; ion-proj τ 0.9 0.12–0.42; NV 0.10–0.20; SiV 0.04–0.15.
- **Commitment honoured:** no re-tuning, no re-run. These are the paper's headline numbers.

## E55: v21 robust prior + C2 confirmatory, pre-registration (7 Oct 2026). OPEN (PSC). Post-hoc fix after the C1 FAIL (E54 stands)
- **Files:** `drift_queue_des_v21.py` 3cbf3be8; `drift_queue_des_c2.py` 0832684b; `tasks_c2.jsonl` 7b176bfb (16,640 tasks, fresh seeds 19011–19014); `analyze_c2.py` cbab5fff; `README_C2.md`.
- **v21 changes (prior only):**
  - M1: uniform-in-s hyperprior.
  - M3: drift-aware window likelihood (exact sawtooth offset, verified to 5e-8).
  - M2: declared fault component, ε = 0.05, D ~ U(0, 4ŝ).
- **Dev pilots** (seeds 20001–20004):
  - ion-future AD g 1e-5: 1.63% → 0.37%. Mechanism: the static-window drift bias, confirmed by M3 alone.
  - SiV: 7.4% → 1.5–1.6% (small n), with throughput down sharply. **Still at risk.**
  - NV always-fault: not fixed (36–53%).
  - No regressions.
- **Blocks:**
  - A core (256 paths);
  - B fleet law (96);
  - R rare faults, 5% of paths matching the declared model (192);
  - C always-fault (64, exploratory).
- **Hypotheses:** C2-A1 (primary), C2-A2, C2-B, C2-R, C2-C (exploratory), D.
- **Commitment:** no further re-tuning. The paper reports C1 and C2 side by side.

## E56: C2, v21 robust-prior controller, confirmatory (7 Oct 2026; 16 × 32 cores, max 2,326 s; timing estimate ≈ 303 SU, so project ≈ 931 / 1,000 by timing; account balance not yet re-checked). C2-A1 FAIL (SiV only), C2-A2 FAIL (SiV only), C2-B FAIL (SiV only), C2-R PASS
- runs.csv sha 4bca8492ee3a6785; 16,640 / 16,640 tasks; module and tasks hashes verified in the shard metadata.
- **C2-A1 FAIL.** 1 of 44 tested groups: SiV, dephasing, g 0, **1.42%** (11 / 776, 7 of them on one path). The other 4 SiV groups had < 200 deliveries and were not tested: v21 makes the controller abstain almost entirely on SiV (fraction of oracle 0.001–0.036).
- **All 42 non-SiV core groups pass:** max 0.51%, all path-bootstrap upper bounds ≤ 0.55%. This includes **ion-future L3 τ 0.95, amplitude damping, g 1e-5: 0.32%** (C1: 1.43%). The C1 failure was the static-window drift bias, and M3 fixes it.
- **C2-A2 FAIL.** SiV dephasing at both g values (upper bounds 3.1%, 1.2%).
- **C2-B FAIL.** 1 of 23 tested: SiV mixhigh 2.08% (5 / 240, all on one path). All 21 non-SiV fleet-law groups pass (max 0.07%).
- **C2-R PASS.** Rare faults (5% of paths, matching the declared model): 8/8 cells ≤ 1% (max 0.31%).

  **But per faulted episode it is still unsafe:** post-fault r is ion-2020 15.6%, NV 59% (68 deliveries), τ 0.85 ion-2020 7.7%, ion-proj 5.4%, ion-proj L1 2.2%. Calibration holds *in aggregate* only; a user on a faulted link is not protected.
- **C2-C, always-fault (exploratory).** Better than C1 for high-SNR cells (ion-future 2.3 → 0.59%; ion-proj L1 1.7 → 0.22%; τ 0.85 ion-2020 3.4 → 1.9%), but still unsafe for ion-2020 (87%), NV (37%), SiV (15%) and ion-proj (6.2%).
- **Cost.** Non-SiV throughput is essentially unchanged from C1 (fraction of oracle within ±0.05). SiV collapses to near-zero.
- **Reading, final for this paper (no further fixes, as committed):**
  - The controller holds r ≤ 1% for every non-SiV hardware cell × drift × memory × fleet-shape condition, on a fresh pre-registered run.
  - Thin-data hardware (SiV-like, ≈ 30 pairs per window) is outside its regime: it fails (C1) or abstains (C2).
  - Undeclared or frequent faults require explicit fault detection; a declared rare-fault prior gives aggregate, not per-episode, protection.

## E57: PSC accounting after C2 (7 Oct 2026, `projects`)
- Bridges-2 RM balance: **9,227 / 10,000 SU**.
- From the 9,634 checkpoint (project total 235 at that point): **project total charged ≈ 235 + 407 = 642 SU of the 1,000 approved.**
- Timing estimates (elapsed × cores) summed to ≈ 931. Either they over-estimate the charge for the 32-core RM-shared shards, or some of C2 is not yet posted. Planning uses the higher figure.
- GPU allocation untouched. No further PSC runs are planned.

## E58: P1, safety phase diagram vs fleet identifiability, pre-registration (7 Oct 2026). OPEN (PSC). Characterization, not rescue
- **Files:** `drift_queue_des_p1.py` c7a3b36d; `tasks_p1.jsonl` fd18cd8c (8,192 tasks, seeds 19021–19023); `analyze_p1.py` f36f97895; `README_P1.md`.
- **Theory index:** I = √(KL/2) / (1 + (σ_w² + A²/12)/s²). Values already observed: SiV 0.72, NV 3.73, ion cells 2.37–9.08.
- **Design:** SiV-like and NV-like L1; g ≈ 0; dephasing-only memory; window T ∈ {50, 100, 200, 400} s; fleet windows K ∈ {16, 64, 256, 512}; 256 paths per group; frozen C2 controller.
- **Hypotheses:**
  - P-1: I ≥ 3 → r ≤ 1%.
  - P-2: no group with I < 1 is both safe and useful (≥ 5% of oracle).
  - P-3, P-4: descriptive.

## E59: P1 phase diagram, PSC (7 Oct 2026). P-1 PASS, P-2 FAIL; risk is NON-MONOTONE in identifiability
- Hashes as E58; 8,192 / 8,192 tasks.
- **P-1 PASS.** Every tested group with I ≥ 3 has r ≤ 1%: 12/12, max 0.53%. Combined with C2, every cell with I ≥ 3 that was ever tested is safe.
- **P-2 FAIL (pre-registered "no free lunch" falsified as stated).** 3 groups with I < 1 were both safe and useful:
  - NV, T 50, K 16 (I 0.86): 0.11%, 8.6% of oracle;
  - SiV, T 400, K 16 (I 0.80): 0.13%, 14.5%;
  - SiV, T 200, K 64 (I 0.93): 0.27%, 6.8%.

  The uniform-s hyperprior keeps very-low-I fleets conservative (ŝ/s = 1.1–1.6, i.e. over-estimated). Corollary 3a is withdrawn.
- **P-3 (descriptive): violations occur only at INTERMEDIATE identifiability.** In the band 1 < I ≤ 2: 3 of 7 groups, all with ŝ/s ≤ 0.96:
  - NV T 50 K 64: 1.34%;
  - SiV T 100 K 512: 1.95%;
  - SiV T 200 K 256: 1.05%.

  Bands I ≤ 1 and I > 2 had 0 violations in 22 groups.

  **Interpretation:** with partial information, the fleet data are strong enough to shrink the hyperposterior but too weak to get s right (under-estimated), so the prior is over-confident. Below that the hyperprior dominates (conservative); above it, s is learned. **The most dangerous regime is partial information.**
- **P-4 (descriptive):** throughput is driven by window length T (NV 0.05–0.09 → 0.45–0.46 of oracle from T = 50 to 400 s; SiV 0.002–0.04 → 0.15–0.23). Fleet size K mainly affects safety, not throughput.
- **Design rule for the paper:** I ≥ 3 has been sufficient everywhere tested. Thin hardware can reach it by longer windows (T) and larger fleets (K). Example: SiV at T = 400 s, K = 512 → I 4.5, r 0.09%, 21% of oracle, versus C2's 0.1–3.6%.

## E60: Innsbruck 230 m two-node trapped-ion dataset obtained; feasibility check only (7 Oct 2026). NO OUTCOME DATA ANALYSED
- Source: Zenodo record 7031042 (CC-BY), downloaded by the user on his Mac (Zenodo is blocked from the cloud and the desktop sandbox). Files in `22_external_checks/innsbruck_230m/`: Data.zip (351,028,036 B), Experiment_parameters.zip (40,073 B); 4,624 files unpacked (1.1 GB).
- What it is: RAW lab data, not processed outcomes. Ion-ion runs (9 per node, 20–21 Jul 2021) hold per-step PMT counts at each node plus photon time tags at the Bell-state station. Ion-ion correlations would have to be reconstructed (herald detection from time tags, herald→attempt synchronisation, PMT thresholding, basis per run). No author analysis code is included; Experiment_parameters.xlsx is a physics-parameter sheet, not a data map.
- Usable validation target: `Calibrations/Node A/Local_ion_photon_entanglement` has 18 scans with a basis map and the authors' own analysis result, so a reconstruction pipeline can be checked against their numbers before it touches ion-ion data.
- Only file structure and headers were inspected; no correlation, fidelity or count statistic was computed. Any analysis will be pre-registered first, with a "pipeline reproduces the authors' local ion-photon result" gate.
- sha256 (first 16): Data.zip 721aa4ed2a1bc003; Experiment_parameters.zip 555763a06da1cbc1.

## E61: Innsbruck Stage 1, blind reproduction of the authors' local ion-photon tomography from raw data (7 Oct 2026). G1 PASS; G2 magnitudes consistent, phase convention differs
- Pre-registration `22_external_checks/innsbruck_230m/PREREG_INNSBRUCK_STAGE1.md` (568c7b973f8e94f4), written before reconstruction. Decoding and tomography done by a subagent blinded to the authors' figure; choices logged in `stage1/CHOICES.md`.
- Script `stage1/reconstruct_ion_photon.py` (587f735216996b81); result `stage1/stage1_result.json` (3db7c287e82de9e3). 18 scans, 21,793 heralded cycles. Threshold at the empty histogram bin (36 counts); no time-window cut beyond the hardware gate; APD mapping chosen because the alternative is unphysical (min eigenvalue −0.42).
- Ours: closest maximally entangled 0.920 ± 0.004 (ML; linear inversion 0.920); best-local-phase 0.9135 ± 0.004. Authors: Fid_arb_max 0.924, Fid_theta 0.914 ± 0.004, Fid_alpha / alpha_theta 0.919. All differences ≤ 0.006 (tolerance 0.02). **G1 PASS.**
- G2: populations and coherence magnitude agree within ≈ 0.02; the coherence phase differs (−2° vs −87°) by a local frame convention that the raw data do not fix. Not counted as pass or fail.
- Sensitivity (after choices were fixed): threshold 30–50 → 0.918–0.920; time windows → 0.921.
- **Reading:** our decoding of this group's raw format is validated. Stage 2 (ion-ion over 230 m) still needs Node B, Bell-state-station and synchronisation decoding; to be pre-registered separately. This is a calibration-model check, not a hardware test of the controller.

## E62: Working-draft manuscript v0.1 and fact-check (7 Oct 2026). Corrections recorded
- `manuscript_2026-10-07/Rajpal_LabelFreeDeliveryRisk_draft_2026-10-07.pdf` (sha bffefeb7ae4157a1; builder make_manuscript.py b2251229a74bf74a; figures make_ms_figs.py 9e3ef4eee6907957). 8 pages, marked "working draft, not peer reviewed, do not circulate".
- An independent fact-check subagent compared every number with E35–E61 and the group CSVs. Corrections applied before release:
  - C2 is now described as **failing its primary pre-registered test on SiV** (C2-A1/A2/B FAIL). The non-SiV restriction is labelled post hoc. SiV exceeded 1% in two groups (1.42%, 2.08%), not one.
  - "Violations only at 1 < I ≤ 2" is now limited to P1. C2's SiV failures are at I = 0.72.
  - P-2 explanation corrected: of the three safe-and-useful I < 1 groups, ŝ/s was 1.007, 1.118 and 0.938, so "s over-estimated" is not the explanation for all three.
  - C2-R maximum is 0.32% (SiV included), not 0.31%. Post-fault r is 2.2–59% in 5 of 8 cells.
  - v14's 0/9 label-free result was the earlier Gaussian controller, not the EB controller.
  - T1 requirement now reads "better than 25%; under-estimates untested".
  - The depolarising model is pessimistic only for dephasing-only memories.
- **Innsbruck note (affects E61's reading):** the PRL (Krutyanskiy et al. 2023) quotes Node A ion-photon fidelity 92.9 (+0.4/−0.5)%. Our blind 0.920 ± 0.004 is 0.009 below that, still inside the pre-registered 0.02 gate, which was set against the repository figure (0.924). The paper reports only 491 ion-ion coincidences, so Stage 2 will have limited power.

## E63: Innsbruck Stage 2 (ion-ion, 230 m), pre-registered (7 Oct 2026). Gate G3 FAIL on event count, so Step 2 was NOT run
- Pre-registration `innsbruck_230m/PREREG_INNSBRUCK_STAGE2.md` (00356d058c4e233c). Analysis `stage2/analyze_stage2.py` (dd68ff9ec7de209b) was locked and tested on synthetic data before any decoding. Pre-stated power: H-a detects only a ≥ 60–110% loss of correlation within a run, so a "consistent" result would have been weak.
- Decoder (a subagent blinded to within-run time structure): events.csv bea45cf8161a7da8, gate.json 4edb59ca866a7829, CHOICES.md 07b36a1006feb80e.
- **G3:**
  - 581 heralded events at 1 µs vs the paper's 491 (+18%, outside the ±10% tolerance): **FAIL**.
  - F+ 0.900 ± 0.038 vs 0.882: pass. F− 0.837 ± 0.058 vs 0.822: pass.
  - The attempt count matches the paper exactly (13,656,928).
  - At 17.5 µs: 4,490 events vs 3,960 (+13%).
- **Post-fail check (documented):** the last-attempt rule was already satisfied by all 581 events, so no fix was made and the single allowed fix is unused. Dropping detector pair (4,5) would give 518, but nothing in the data or paper justifies it, so it was not adopted.
- **Reading:** the decoding is right on attempts, synchronisation and fidelities, but our herald selection differs from the paper's in an unknown way. As pre-registered, no assumption test was run on the ion-ion data. Real-data support for the paper therefore stays at Stage 1 (E61) plus this partial reproduction.

## E64: Delft metropolitan NV dataset, access attempt (7 Oct 2026). BLOCKED (repository storage maintenance)
- Dataset: 4TU.ResearchData doi:10.4121/983e4771-1d12-457f-a98e-fab3a2959288 (CC-BY), supporting Stolk et al., arXiv:2404.03723. One zip file, DataRepository_metropolitan_entanglement_20240501.zip, 35,384,410 B, MD5 0faf02feb5d4863850a618967d5c83ef.
- The page is up, but the files show as "temporarily unavailable while storage is under maintenance". The file-list API returns 503. No mirror found. Nothing downloaded and nothing analysed; retry later.

## E65: G1, the frozen final controller on networks with route choice, pre-registration (8 Oct 2026). OPEN (PSC)
- Motivation (the user's request): real networks are not one line. A router choosing the best-looking path from the same calibration data creates a selection effect (winner's curse).
- Theory, stated in advance: if the router's choice is a function of the data D and p is the true posterior given all of D, the tower property still gives r = E[p | delivered]. So a calibrated controller is immune to selection, and a flat-prior controller is exposed.
- Design: 5 × 5 grid (40 links; requests at hop distance 1–Lmax; all shortest paths are candidates), plus a best-of-k block (k = 1, 3, 8 disjoint paths). Controllers `cal` (frozen C2) and `flat` (Jeffreys); routers `random` and `best`. 64 networks per group, 1,280 tasks, fresh seeds 19101–19104.
- Simplifications: no contention, no drift in time, dephasing-only memory, batched 100-s window.
- Files: `drift_queue_des_g1.py` 4cc0016adedf331d, `tasks_g1.jsonl` bf06e4a190c464c2, `analyze_g1.py` 0c9a19c04fe76abb (locked; tested on synthetic data), `README_G1.md`.
- Hypotheses:
  - H1: `cal` r ≤ 1% in every group.
  - H1b: network-bootstrap upper bound ≤ 1%.
  - H2: winner's curse for `flat` but not for `cal`.
  - H3: `flat` r rises from k = 1 to k = 8.
  - H4: descriptive.
- Dev pilot (cloud, seeds 20101–20104, 1 network each, disclosed): NV best-of-8 `cal` 1.28% (10 of 781), flagged at risk.
- PSC: ceiling 64 SU; expected 5–15.

## E66: G1, networks with route choice, PSC (8 Oct 2026; 8 × 16 cores). H1 FAIL (1 of 10 groups), H1b FAIL, H2 NOT CONFIRMED (bar missed by a small margin), H3 NOT CONFIRMED
- Output pasted by the user. runs.csv and its hash are pending copy-back.
- **H1 FAIL (9/10).** The only `cal` group above 1% is K ion2020 par **k = 1**: 1.173% (254 of 21,659).
  - k = 1 means a single path, so **no route choice** is involved.
  - One network holds 190 of the 254 bad deliveries; the bootstrap upper bound is 4.14%.
- Every grid `cal` group was ≤ 1%:
  - ion2020: random 0.90%, best 0.95%;
  - ionproj: random 0.73%, best 0.68%.
- Best-of-k `cal`:
  - NV: k1 0.14%, k3 0.60%, k8 0.49%;
  - ion2020: k3 0.44%, k8 0.63%.
- **H1b FAIL:** network-bootstrap upper bounds above 1% in 4 groups: 4.14% (ion2020 k1), 1.05% (ion2020 k3), 1.04% (grid ion2020 best), 1.005% (ion2020 k8).
- **H2 NOT CONFIRMED as registered** (bar: `cal` selection bias at k = 8 ≤ 0).
  - `cal` bias at k = 8: +0.0006 (NV), +0.0001 (ion2020).
  - `flat` bias: −0.0018 → +0.0586 (NV), −0.0004 → +0.0031 (ion2020).
  - Qualitatively as predicted: the winner's curse is 30–100× smaller for `cal`. But the pre-set bar was missed.
- **H3 NOT CONFIRMED.**
  - NV `flat` rose with selection: 1.23% → 1.93%.
  - ion2020 `flat` fell: 4.39% → 1.04%. Choosing among more paths also finds genuinely better paths with more headroom, and in ion2020 that outweighed the winner's curse. The pre-registered prediction ignored this.
- **H4 (descriptive):** best routing raised throughput (grid ionproj 0.86 → 0.95 of oracle; ion2020 0.81 → 0.86) with `cal` risk essentially unchanged. `flat` failed on the ion2020 grid (1.53–1.62%) but not on ionproj (0.65–0.69%).
- **Reading:** route choice by itself did not break the calibrated controller. Every grid and every k ≥ 3 group was ≤ 1% in point estimate. The failure sits in a no-selection single-path group and is concentrated in one network; diagnosis is exploratory (see E67). With calibration data batched in 100-s windows, risk clusters by network, so per-network protection is weaker than the pooled average.

## E67: G1 failure diagnosis (8 Oct 2026; cloud, 0 SU; EXPLORATORY, post hoc)
- The failing group (K ion2020 par k = 1 `cal`) was rerun in the cloud with the same code and seeds. It reproduced exactly: 21,659 delivered, 254 bad.
- **Calibration check.** An instrumented copy summed the controller's own p over delivered pairs: Σp = 196.3, so its mean predicted risk was 0.91%. The observed rate was 254 / 21,659 = 1.17%.
- **Concentration.** Network 42 had 190 delivered and 190 bad, with Σp = 1.74.
  - Its true links are λ = 0.932 and 0.906 (link F 0.949 and 0.930), well inside the fleet law.
  - True delivered F at zero wait is 0.9001, essentially on the threshold, so any real wait makes the pair bad.
  - Its per-window λ estimates have sd ≈ 0.005. When a 100-s window is optimistic by about 2.5 sd, the controller assigns p ≈ 1% to every decision in that window. All of those pairs are bad by tiny margins.
  - Without network 42 (post hoc), the group's r is 0.30%.
  - Network 4 is similar: true F 0.898 at zero wait; 13 delivered, 13 bad, Σp 0.10.
- **Reading.**
  - The controller's average prediction (0.91%) stayed under 1%. The realised 1.17% comes mainly from one cluster: a path sitting at the threshold plus an optimistic calibration window. Proposition 2 holds in expectation, but with batched windows, risk clusters by path and window. Per-path or per-window protection is weaker than the pooled guarantee, the same aggregate-versus-per-episode limit as with faults (Prop. 5).
  - **Methodological consequence for earlier runs (v16–C2, P1).** The single-path simulator drew fresh window counts for every decision. That is valid for the mean but removes this clustering, so the earlier network-bootstrap upper bounds (e.g. C2 ≤ 0.55%) are likely optimistic. The paper must say so.
  - Candidate remedies need their own pre-registration and are not tested: per-window delivery caps, requiring agreement across consecutive windows, or computing the threshold over windows rather than over decisions.

## E68: G2 (per-path anytime-valid guard) and S1 (C2 re-check with realistic overlapping windows), pre-registration (8 Oct 2026). OPEN (PSC)
- G1 raw data copied home: `des_g1_psc/runs.csv` sha e57bdd53c04bf7c8, which matches the PSC output pasted in E66.
- **G2. Post-hoc remedy for E66/E67**; G1's verdict stands.
  - The frozen controller plus a per-link anytime-valid lower bound (Beta(1/2, 1/2) mixture confidence sequence at α/Lmax, α = 0.05). Deliver only if the PTM fidelity at those lower bounds, with the actual waits, is ≥ τ.
  - Proposition 6: for every path, P(it ever delivers a bad pair) ≤ α, assuming stationary links and exact physics.
  - Checked before the run: miscoverage 0 in 2,000 simulated repetitions.
  - Design: G1's design, `cal` vs `calg`, fresh seeds 19111–19114, 1,280 tasks.
  - Files: `drift_queue_des_g2.py` b3f90eaa06042f35, `tasks_g2.jsonl` 96a5c77c2f6b89e2, `analyze_g2.py` 78e46e33b137a444.
  - Hypotheses: H1 `calg` r ≤ 1% in every group; H1b upper bound ≤ 1%; H2 bad paths / delivering paths ≤ 5%; H3, H4 descriptive.
  - Dev pilot (seeds 20111–20114): grid `cal` had 35 bad deliveries and 19 of 79 paths bad; `calg` had 0 bad.
- **S1. Sensitivity re-check of C2's data model.**
  - Each link gets one pre-generated calibration stream, and windows overlap as they would in reality. Only the counts change from C2.
  - Design: C2 block A, first 128 paths per group, paired with C2; 6,144 tasks.
  - Files: `drift_queue_des_s1.py` 42d09f65e55a5d6d, `tasks_s1.jsonl` 2b05fc1e92d9fef0, `analyze_s1.py` 1ece7f04fdddc9f7.
  - Hypotheses: S1-a non-SiV r ≤ 1%; S1-b upper bounds widen (median ratio > 1); S1-c descriptive.
- PSC ceilings: G2 64 SU, S1 256 SU. Worst case ≈ 990 of the 1,000 approved.

## E69: G2, per-path anytime-valid guard on networks, PSC (8 Oct 2026). H1 PASS, H1b PASS, H2 PASS
- runs.csv sha 46d09d4cd0fbcf1d (PSC merge; copy-back pending); 1,280 / 1,280 tasks.
- **H1 PASS (10/10).** The guarded controller `calg` delivered **0 bad pairs** in every group: about 1.67 M deliveries in total, every group's network-bootstrap upper bound 0.000% (**H1b PASS**).
- **H2 PASS.** Under `calg`, 0 of 56,959 delivering paths ever delivered a bad pair. For comparison, `cal` had 6,783 of 69,646 (**9.7%** of delivering paths had at least one bad delivery).
- **H3 (cost of the guard), fraction of oracle `cal` → `calg`:**
  - grid ion2020: best 0.855 → 0.809, random 0.807 → 0.771;
  - grid ionproj: best 0.951 → 0.876, random 0.861 → 0.789;
  - K ion2020: k1 0.391 → 0.355, k3 0.424 → 0.415, k8 0.498 → 0.442;
  - K nv: k1 0.267 → 0.257, k3 0.536 → 0.460, k8 0.837 → 0.746.
  - Overall a 2–15% relative throughput loss.
- **H4 (replication of G1 on fresh seeds).** `cal` max r 0.943%, 0 of 10 groups above 1% (G1 had 1 of 10), but network-bootstrap upper bounds reach 1.40% (nv k3) and 1.38% (ion2020 k3). G1's single failure is consistent with path clustering rather than a systematic excess.
- **Reading and limits.**
  - Proposition 6 holds as predicted, at a modest throughput cost.
  - Zero bad deliveries is partly by construction: the simulator's truth uses the same exact physics model as the guard, and links are stationary (g ≈ 0). The guarantee is only as good as those two assumptions. Under drift, the confidence sequence must restart at re-alignments; model error in T1/T2 or gate noise would directly break it. Both are untested.
  - With the guard on, the Bayesian δ-rule is no longer the binding constraint. The guard is conservative and dominates.

## E70: S1, C2 re-checked with realistic overlapping calibration windows, PSC (8 Oct 2026). S1-a PASS, S1-b CONFIRMED; point risks also rose
- runs.csv sha 2c14797e183d4ba8 (PSC merge; copy-back pending); 6,144 / 6,144 tasks, paired with C2 rows idx < 128.
- **S1-a PASS.** All 42 non-SiV groups have r ≤ 1% (max 0.834%: ionproj τ 0.90, g 1e-5, t1eq).
- **S1-b CONFIRMED.** The median upper-bound ratio S1/C2 is 2.01. Groups with upper bound ≤ 1%: 33 of 42 under S1, against 42 of 42 under C2 on the same paths. Max upper bound 2.01% (ion2020 τ 0.90, g 1e-5, ad).
- **Not predicted, and important.** Point risk also rose, in 37 of 42 groups (4 ties): median ratio 1.8 (IQR 1.45–3.9).
  - Pooled non-SiV r rose from 0.19% to 0.32%.
  - By memory type: ad 0.39 → 0.59%, t1eq 0.24 → 0.42%, deph 0.008 → 0.038%.
  - Throughput unchanged (median S1/C2 0.99).
- **Correction to E67.** E67 said fresh per-decision draws are "valid for the mean". That is **wrong**: the mean shifts too.
- **Post-hoc mechanism (exploratory, to be tested).** The window threshold t is chosen from the recent history of p. With realistic data, that history's estimation errors are correlated with the current window's error. When a stretch of data is optimistic, recent p values are low, t loosens, and deliveries concentrate in optimistic stretches. Proposition 2's tower argument needs p = P(bad | everything that influences the decision). Here t carries information about the current data error that p ignores, so pooled calibration is only approximate. Fresh independent draws hid this.
- **SiV (outside the regime):** deph 1.28% (g 0) and 3.01% (g 1e-5), on 391 and 299 deliveries.
- **Consequence for the paper.**
  - C2's headline (non-SiV ≤ 1%) survives the realistic data model, with about half the margin.
  - The C2 / P1 upper bounds must be replaced by S1-type clustering-aware bounds.
  - Proposition 2's condition must be stated carefully, including the threshold's information.
- PSC accounting for G1, G2 and S1 is pending (`projects` output).

## E71: G2 and S1 raw data copied home (8 Oct 2026)
- des_g2_psc/runs.csv sha 46d09d4cd0fbcf1d (1,280 rows) and des_s1_psc/runs.csv sha 2c14797e183d4ba8 (6,144 rows), both matching the PSC merges in E69/E70. All 16 S1 shards are present.

## E72: G3, 30 × 30 grid, pre-registration (8 Oct 2026). OPEN (PSC)
- **Design.** 900 nodes, 1,740 links, best routing, 10 requests per s over 3,000 s.
  - Controllers: `cal` vs `calg` (anytime guard, α 0.05).
  - Fleet prior: `ext` (128 external link-windows) vs `own` (one pre-run window on 512 of the network's own links; new).
  - Hardware: ion2020 and ionproj.
  - 32 networks per group, paired; 256 tasks; fresh seeds 19121–19124.
- **Files.** `drift_queue_des_g3.py` 0baa303cb5722863, `tasks_g3.jsonl` 06cf28e8d3e95caa, `analyze_g3.py` 7789af9963077495 (locked; tested on synthetic data).
- **Hypotheses.**
  - H1: `calg` r ≤ 1% in all 4 groups.
  - H1b: network-bootstrap upper bound ≤ 1%.
  - H2: `calg` bad paths ≤ 5% of delivering paths.
  - H3: `cal` r ≤ 1% in all 4 groups.
  - H4, H5: descriptive (own vs external prior; cost of the guard).
- **Cloud smoke (seeds 20121–20124, disclosed).**
  - ionproj `cal` own: 0.72%, 1.2% of paths bad, ŝ/s 1.02, 111 s.
  - ion2020 `calg` own: 0 bad, 142 s.
  - Peak memory 1.4 GB per worker.
- **PSC.** Ceiling 64 SU.

## E73: G3, 30 × 30 grid, PSC (8 Oct 2026). H1 PASS, H1b PASS, H2 PASS, H3 PASS
- runs.csv sha e9cd30683b249213 (PSC merge; copy-back pending); 256 / 256 tasks.
- **H1 / H1b PASS.** The guarded controller `calg` had **0 bad deliveries** in all 4 groups (about 2.11 M delivered), with every network-bootstrap upper bound 0.000%.
- **H2 PASS.** 0 of 930,435 delivering paths ever delivered a bad pair.
- **H3 PASS.** The frozen controller `cal` had pooled r of:
  - ion2020: 0.83% (external prior) and 0.80% (own-link prior);
  - ionproj: 0.74% and 0.69%;
  - the maximum network-bootstrap upper bound is 0.87%, tighter than 5 × 5.
  - Per path it is still exposed: 3.0% (ion2020) and 1.2–1.3% (ionproj) of delivering paths had at least one bad pair.
- **H4 (own-link prior vs external):** equal or slightly safer (r 0.80 vs 0.83%; 0.69 vs 0.74%), throughput the same, ŝ/s 0.99–1.01. **The network can learn its prior from 512 of its own links.**
- **H5 (cost of the guard), fraction of oracle `cal` → `calg`:** ion2020 0.83 → 0.78 (−6%), ionproj 0.94 → 0.85 (−9%).
- **Limits (unchanged from G2).** Zero is partly by construction: the truth uses the same exact physics as the guard, and links are stationary. Also: no contention, no drift in time, dephasing-only memory, and requests of 2–3 hops. The guard under drift and under model error is the main untested point.

## E74: G3 raw data copied home (8 Oct 2026)
- des_g3_psc/runs.csv sha e9cd30683b249213 (256 rows), matching the PSC merge in E73; all 8 shards present.

## E75: G4, the guard under drift and physics-model error, pre-registration (8 Oct 2026). OPEN (PSC)
- **Scenarios.**
  - D: sawtooth drift at g = 1e-5, re-aligned every 2,000 s.
  - M: the controller believes T2 is 1.25× and e is 0.8× the truth.
  - M50: 1.5× T2 and 0.6× e.
- **Controllers.**
  - `cal` (no guard, reference).
  - `gnaive`: the G2 guard (ignores drift).
  - `gdrift`: Proposition 6′, which restarts at known re-alignments, subtracts g(t − t_reset), and spends α as 6α/(π²c²) over cycles. Validity comes from stochastic dominance plus monotonicity of the Beta-mixture bound.
  - `gnom`: the guard with the wrong nominal physics.
  - `grobust`: the worst case over a declared set T2 ∈ [0.75, 1]·T2_c, e ∈ [e_c, 1.25 e_c]. It covers the truth under M but not under M50.
- **Design.** 5 × 5 grid, best routing, ion2020 and ionproj; 18 groups × 64 networks = 1,152 tasks; fresh seeds 19131–19134.
- **Files.** `drift_queue_des_g4.py` 3ac4099bb4badc02, `tasks_g4.jsonl` 24156666586ce1df, `analyze_g4.py` 5c432f4a7cac66a4 (locked; tested on synthetic data).
- **Hypotheses.**
  - H1: `gdrift` is safe (r ≤ 1%, upper bound ≤ 1%, bad paths ≤ 5%).
  - H2 (prediction): `gnaive` delivers bad pairs.
  - H3 (open): `gnom` under M.
  - H4: `grobust` under M is safe.
  - H5: descriptive.
  - H6 (open): M50.
- **Dev pilots (seeds 20131–20134, disclosed).**
  - D: cal 95 bad, gnaive 9, gdrift 0.
  - M: cal 4.0%, gnom 0, grobust 0. Because the nominal guard survived here, H3 was turned into an open question and M50 was added **before** any confirmatory run.
  - M50: gnom 14 and 49 bad (10–14% of paths), grobust 0.
- **PSC.** Ceiling 64 SU.

## E76: G4, the guard under drift and physics-model error, PSC (8–9 Oct 2026). H1 PASS, H2 CONFIRMED, H4 PASS; H3 and H6 answered
- runs.csv sha 015ec7b242ab7db6. Copied home; the hash matches and all 8 shards are present. 1,152 / 1,152 tasks.
- **H1 PASS (drift).** `gdrift` (Prop. 6′) had **0 bad** in about 514 k deliveries, with 0 of 21,434 paths bad. **Cost is large:** fraction of oracle 0.68 vs 0.85 (`cal`) for ion2020, and 0.63 vs 0.95 for ionproj. It restarts after every re-alignment and pays a g(t − t_reset) margin.
- **H2 CONFIRMED.** `gnaive` delivered bad pairs: 69 (0.03%) and 463 (0.11%), with 1.3–1.5% of delivering paths bad. Ignoring drift breaks the per-path guarantee in principle. The fraction of bad paths stayed under α here, but bad deliveries are no longer prevented.
- **H3 (open), answered yes, slightly.** Under a 25% optimistic model, the nominal guard `gnom` delivered 5 and 16 bad pairs (0.002–0.004%; 0.06–0.11% of paths). With wrong physics, Prop. 6 no longer guarantees zero, but the statistical margin keeps the damage tiny.
- **H4 PASS (model error).** `grobust` (declared ±25% set that covers the truth) had **0 bad**, 0 of 26,174 paths bad. Cost: fraction of oracle 0.82 vs 0.89 (ion2020) and 0.88 vs 0.97 (ionproj).
- **H6 (open; the declared set does not cover the truth, M50).**
  - `gnom` breaks: r 0.54% and 0.38%; 15.3% and 5.9% of paths bad (above α).
  - `grobust` degrades gracefully: 16 and 2 bad (0.006%, 0.0004%); 0.28% and 0.009% of paths.
- **H5 (descriptive): the unguarded Bayesian controller is fragile.**
  - Under drift: r 1.18% (ion2020) and 1.26% (ionproj), above 1%.
  - Under a 25% model error: 2.6–2.7%.
  - Under a 50% model error: 5.0–6.3%. Up to 48% of paths delivered a bad pair.
- **Caveat on the drift result for `cal`.** The grid simulator's Bayesian controller does **not** include C2's drift-aware window likelihood (v21 M3); its counts also lag by up to one epoch. So `cal` under D reflects the simplified grid controller, not C2's controller. The guards are unaffected: they have their own drift handling.
- **Reading.**
  1. The guard needs drift handling (Prop. 6′) and a physics uncertainty set that covers the truth. With both, it delivered no bad pairs under drift or 25% model error.
  2. The price is throughput: up to −34% under drift, −8 to −9% under model error.
  3. When the declared set is too narrow, protection degrades gracefully rather than collapsing.
  4. Without a guard, a 25% physics error alone pushes the Bayesian controller to about 2.6% bad.

## E77 — G5 pre-registered: cheaper drift-valid guard (9 Oct 2026; no confirmatory data yet)
- **Prereg:** `18c_drift_frontier/README_G5.md`.
- **Hashes:** `drift_queue_des_g5.py` 6a3760751656f798, `tasks_g5.jsonl` 084506ae9237a184 (1,024 tasks), `analyze_g5.py` a28effcdded14d6e (locked; tested on synthetic data). Uses g4 3ac4099b, g2 b3f90eaa and g1 4cc0016a unchanged.
- **New guards:**
  - `gexact` (Prop. 6″): exact drift-offset mixture CS on the re-alignment level, restarted per cycle. The bound subtracts the actual drift since the reset, not a worst case.
  - `gpersist`: one CS for the whole run. It assumes every re-alignment restores the same level.
- **Scenarios:** D (as G4) and Dj (re-alignment jitter N(0, 0.005), which violates gpersist's assumption). Fresh seeds 19141–19144.
- **Dev pilot (seeds 20141–20144, 1–2 networks per cell), fraction of oracle:**

  | Controller | ion2020 | ionproj |
  |---|---|---|
  | gdrift | 0.65–0.68 | 0.62–0.63 |
  | gexact | 0.72–0.74 | 0.74–0.78 |
  | gpersist | 0.80–0.84 | 0.89–0.91 |

  - gdrift and gexact had 0 bad pairs.
  - gpersist under Dj (ionproj) had 10 bad pairs in 14,171, with 9 of 910 paths bad. That pilot result informs H4 (disclosed).
- **Primary tests:** H1, gexact safe in all 4 groups; H2, gexact > gdrift throughput in all 4 cells (paired-bootstrap 95% lower bound > 0).
- **PSC:** ceiling 64 SU.

## E78 — G5 confirmatory: exact-drift guard cuts the drift cost from 19–34% to 14–20%, still 0 bad (9 Oct 2026)
- **Provenance:** 1,024 of 1,024 tasks. PSC runs.csv `c992739821a87fb2` matches the Mac copy. Module, tasks and analyzer are unchanged from E77. Write-up: `18c_drift_frontier/des_g5_psc/G5_RESULTS.md`.
- **H1 PASS:** gexact had 0 bad pairs in 1,183,827 delivered and 0 of 57,408 paths bad (D and Dj, both hw).
- **H2 PASS:** gexact beat gdrift by +0.038 / +0.046 (ion2020 D / Dj) and +0.129 / +0.126 (ionproj D / Dj); all 95% lower bounds > 0.
- **Fraction of oracle vs cal:**

  | hw | cal | gdrift | gexact |
  |---|---|---|---|
  | ion2020 | 0.85–0.86 | 0.69–0.70 | 0.73–0.74 |
  | ionproj | 0.95 | 0.63–0.64 | 0.76–0.77 |

  gexact closes 24–27% (ion2020) and 40% (ionproj) of the gap to no guard.
- **H3 PASS:** gpersist under D had 0 bad, at 0.816 / 0.896 of oracle.
- **H4 CONFIRMED:** gpersist under Dj delivered 43 / 211 bad pairs (r 0.018% / 0.048%) in 18 / 54 of 64 networks, with 0.59% of paths bad. Restoring the level exactly is a load-bearing assumption.
- **cal:** r 1.21–1.36%, with 12–28% of paths bad (same caveat as G4).
- **New theory:** Prop. 6″ (exact-drift mixture CS) needs g known exactly; Prop. 6′ needs only an upper bound on g.

## E79 — Compute check and advisor materials (9 Oct 2026)
- **PSC `projects` (pasted by Tanish):** cis260277p Bridges-2 Regular Memory balance 8,767 / 10,000 SU, so **1,233 SU** have been charged to the allocation (all work in the project). The approved cap for this study's runs was 1,000 SU, and the earlier ~850 estimate was low. No further PSC runs until the budget is re-approved.
- **Advisor materials** in `advisor_report_2026-10-10/`:
  - report v2, 20 pages, adds Chapters 10–12 and Diagrams A–E;
  - chapter-wise study guide, 30 pages;
  - 14-slide deck as a claude.ai artifact.
  - Two independent fact-check passes were made; all issues were fixed.

## E80 — G6 pre-registered: per-user protection after sudden link faults (9 Oct 2026; no confirmatory data; PSC run awaits budget approval)
- **Prereg:** `18c_drift_frontier/README_G6.md`.
- **Hashes:** `drift_queue_des_g6.py` 70769aae4b66680e, `tasks_g6.jsonl` 1f60786441a8fa9a (1,024 tasks), `analyze_g6.py` a9fa7a461865bd0a (locked; tested on synthetic data).
- **Scenario:** on a 5×5 grid, each link faults with probability 0.05 at a random epoch; the drop is 2 SD (F2) or 4 SD (F4).
- **Controllers:**
  - `cal`
  - `gnaive` (G2 guard)
  - `galarm` (guard plus a per-link change alarm; restart with 6α/(π²c²) spending)
  - `gwin` (guard plus a last-epoch bound)
- **Dev pilot (seeds 20151–20154; 3 networks per group; 28 faults):**
  - `galarm` had **0 late** post-fault bad pairs in all 4 groups, against `cal` 6–15 and `gnaive` 1–13.
  - Early (first-epoch) bad pairs remained: 6–43. That is an unavoidable data latency.
  - `galarm` detected 27/28 faults with 1 false alarm, at a throughput cost of about 0.01 versus `gnaive`.
  - `gwin` had 0 late bad pairs but costs throughput (0.64–0.77 of oracle).
- **Primary tests:**
  - **H1:** `galarm` late post-fault bad ≤ 0.1% of post-fault deliveries, and fewer than `cal` in every group.
  - **H2:** `galarm` r ≤ 1%, upper bound ≤ 1%, bad paths ≤ 5%.
- **Budget:** ceiling 64 SU; expected 10–15. Not to be submitted until Tanish approves a budget (account at 1,233 SU, E79).

## E81 — G6 confirmatory: the change alarm cuts late post-fault bad pairs by 97%, but H1 and H3 fail narrowly (9 Oct 2026)
- **Provenance:** 1,024 of 1,024 tasks; 475 faults. runs.csv `9a980977de17635e` (PSC = Mac). Module and analyzer unchanged from E80. Write-up: `18c_drift_frontier/des_g6_psc/G6_RESULTS.md`.
- **H1 FAIL (narrowly).** `galarm` late post-fault bad was 9 / 0 / 15 / 0, against `cal` 20 / 191 / 413 / 169, so fewer in every group. But the ion2020 pooled rate is 0.14%, above the 0.1% bar; ionproj is 0.07%.
- **H2 PASS.** r ≤ 0.12%, UB ≤ 0.15%, bad paths 0.5–2.8%.
- **H3 FAIL.** 414/475 faults detected (87%, bar 90%); 4-SD faults 100%; 2-SD faults on ionproj 76/132; 2 false alarms in 256 networks.
- **H4 PASS.** Cost of 0.4–0.7 points versus `gnaive`.
- **Totals:**
  - Late bad: `cal` 793, `gnaive` 286, `galarm` 24, `gwin` 5.
  - Early (first-epoch) bad remains: `galarm` 97–444 per group.
  - `gwin`: 166 bad pairs in total, at 0.66–0.72 of oracle.
  - Worst single path: `galarm` 3–7 bad, `cal` 9–21.
- **Reading:**
  - Large faults are solved: 100% detected, 0 late bad.
  - Small faults and the first post-fault epoch remain open.
  - There is no formal guarantee under unannounced faults.

## E82 — G7 pre-registered: a GLR change alarm for small faults (9 Oct 2026; Tanish approved the run)
- **Prereg:** `18c_drift_frontier/README_G7.md`.
- **Hashes:** `drift_queue_des_g7.py` 33bf5888af5420e6, `tasks_g7.jsonl` 13cd909784aefd73, `analyze_g7.py` 2cdb7a2b2cb76d87.
- **New alarm `gglr`:** a multi-epoch GLR change detector (W = 4, h = 9; a sensitive variant `gglr_s` uses h = 6). Thresholds were fixed from the χ² approximation before the pilot.
- **Scenarios:** F2 (2-SD faults) and F1 (1-SD faults).
- **Dev pilot (24 faults):** `gglr` detected 20/24 against `galarm` 10/24, with 1 false alarm in 12 networks.
- **Primary tests:**
  - H1: late post-fault bad ≤ 0.1% and ≤ `galarm`'s, per hw.
  - H2: detects ≥ 90% of 2-SD faults.
- **Budget:** ceiling 64 SU.

## E83 — G7 confirmatory: the GLR alarm fixes detection (99% of 2-SD faults) but not late bad pairs; H1 fails on one clause (10 Oct 2026)
- **Provenance:** 1,024 of 1,024 tasks. runs.csv `5157931a11f3410f` (PSC = Mac). Write-up: `18c_drift_frontier/des_g7_psc/G7_RESULTS.md`.
- **H1 FAIL.** The late rate is within the bar (0.068% / 0.065% ≤ 0.1%), but on ion2020 `gglr` had 8 late bad pairs against `galarm`'s 4.
- **H2 PASS.** 252/255 2-SD faults detected (98.8%), against `galarm` 218/255.
- **H3 PASS** (6 false alarms in 256 networks). **H4 PASS.** **H5 PASS.**
- **Late bad pairs in total:** `cal` 769, `galarm` 28, `gglr` 28, `gglr_s` 14 (with 183 false alarms).
- **1-SD detection:** `gglr` 84% / 41%, against `galarm` 30% / 7%.
- **Reading:**
  - Detection is solved for 2-SD faults.
  - The remaining late bad pairs occur during the evidence-gathering delay.
  - The sensitive threshold halves them at the cost of about 0.7 cheap false alarms per network.

## E84 — Study 23 started: global AI model plus RL routing under the guard (4-day trial, 10–13 Oct 2026); go/no-go #1 PASS
- **Folder:** `prx_work/23_ai_rl_guard/`. Plan: `PLAN.md` (stop rules fixed before any result).
- **Day 1:**
  - Correlated-link 5×5 grid. Link quality = fleet mean + Gaussian spatial field (ℓ = 1.5) + own noise, mixed with weight ρ.
  - MLP global model (32-32) predicts a link's quality from its **neighbours' data only**. Trained on networks with seeds 100000–121499; checked on held-out seeds 23900–24299 (ion2020).
  - Hashes: `ai_weights.npz` e3ba6ca7ad0d84d8, `corr_net.py` 3f6df6215f05861c, `ai_model.py` 0ce9fbbb7b352054.
- **Offline check (held out), prior error versus the fleet prior:**

  | Data | ρ = 0.7 | ρ = 0 (control) |
  |---|---|---|
  | Dense | **−30.6%** | −0.2% |
  | Thin | **−25.0%** | −0.1% |

  **Go/no-go #1 (≥ 20%): PASS.**
- **Caveat:** after one epoch of the link's own data, the gain shrinks to −5.3% (dense) and −15.9% (thin). Throughput gains are therefore expected mainly with thin data and early epochs.

## E85 — Study 23: RL training + dev pilot done; go/no-go #2 PASS; confirmatory run pre-registered (10 Oct 2026)
- **RL training on PSC (CEM, 8 configs, seeds 50000+):** learned routers beat greedy by −0.1 to +1.4 points on fresh training networks.
- **Dev pilot** (PSC, 384 tasks, seeds 20231–20234; runs.csv sha 1ef5bd4ba156bd14).
- **Go/no-go #2 PASS:** `ag` or `arg` beat `bg` by ≥ 2 points on correlated networks in 3 of 4 cells (`arg`: +1.73 / +2.67 / +2.99 / +6.26). All guarded arms had 0 bad pairs. No-guard arms had 0.43–1.07% bad.
- **New control `fg`** (an informed fleet prior in the guard, with no AI) was added after the pilot. Cloud check: `fg − bg` −0.6 to +2.3; `ag − fg` +0.25 to +0.77 on correlated cells and −0.5 to −0.7 on independent ones. So much of the pilot's gain comes from an informed guard prior, not from the AI. This is stated in the prereg, and H3 tests the AI against `fg`.
- **Prereg:** `23_ai_rl_guard/README_23.md`.
- **Hashes:** `study23.py` 10f75e0ec5711e85, `analyze_23.py` 541ca7422406cbed, `tasks_s23.jsonl` 0c74b19279fc1662 (3,584 tasks).
- **Primary tests:**
  - H1: safety of all guarded arms.
  - H2: `arg − bg` ≥ 2 points on correlated cells.
  - H3: `ag − fg` > 0 on correlated cells.
- **Budget:** ceiling 128 SU.

## E86 — Study 23 confirmatory run (10 Oct 2026)

**Run:** PSC job 49005581; 3,584 tasks; about 34.6 SU.

**Hashes:** runs.csv 7c398c48ef653d8b; study23 10f75e0ec5711e85; tasks 0c74b19279fc1662; analysis 541ca7422406cbed. Reproduced on the Mac.

**Outcomes:**
- **H1 PASS:** 0 guarded bad pairs.
- **H2 PASS:** `arg − bg` +3.05 [2.75, 3.36].
- **H3 PASS:** `ag − fg` +1.07 [0.83, 1.33].
- **H4 PASS:** +0.05.
- **H5 PASS:** +0.34 [0.27, 0.41].

**Decomposition on correlated cells:** informed prior +1.59, AI +1.07, RL +0.39.

**Without the guard:** r 0.53–1.11%; 5–21% of paths bad.

**Limits:** the AI is tested in-distribution only; the effects are small (AI about 1 point, RL about 0.3 points).

Details: `23_ai_rl_guard/RESULTS_23.md`. Policy-file hashes: ion2020 dense arg 6215e9a5, ion2020 dense rg 7d769df0, ion2020 thin arg 0aca13f7, ion2020 thin rg ff96e1db, ionproj dense arg 5b228f98, ionproj dense rg 83682b48, ionproj thin arg 19ef0e88, ionproj thin rg 74814064. Hashed after the run. File times 04:09–04:13 UTC are before the run start (15:26:54 UTC), so the check is settled.

**E86 addendum (10 Oct, post hoc).** H3 (`ag − fg`) mixes the AI's correlation learning with the AI belief's use of the known fleet spread. The ρ = 0 cells bound the second effect (+0.05 pooled). Study 24 adds a direct control (`kg`).

## E87 — Study 24 set-up and dev runs (10 Oct 2026; nothing confirmatory yet)

**Folder:** `24_ai_v2_hardware/`. Plan: `PLAN_24.md`.

**Models trained in the cloud:**
- AI v2 + its linear control for 5 hw (ai2_*.npz): ion2020 21fb38be, ionproj 8af23867, ionfut 32a2c9ae, nv2 413a5fbb, siv aa9ca5a7.
- AI v1 for the 3 new hw with the unchanged ai_model.py (a39bc058): siv 6dbcd949, nv2 e9f25e99, ionfut c0a29a9a.

**Offline prior RMSE on held-out networks (z units; fleet prior = 1), AI v2 MLP / linear:**

| Hardware | field | region | outlier | ind |
|---|---|---|---|---|
| SiV | 0.78 / 0.80 | 0.85 / 0.85 | 0.86 / 0.87 | 1.03 / 1.04 |
| NV | 0.68 / 0.69 | 0.76 / 0.76 | | |
| ion2020 | 0.71 / 0.71 | | | |
| ionproj | 0.81 / 0.80 | | | |
| ionfut | 0.99 / 0.96 | | | |

- ionfut is unpredictable because the drift phase dominates its spread.
- The MLP is not better than the linear model offline.

**Cloud dev findings (3 networks each, dev seeds):**
- SiV field: bg 0.04, fg 0.02, kg 0.18, ag1 0.32, ag2 0.26–0.34. NV field: bg 0.24, kg 0.26, ag1 0.37, ag2 0.36–0.39.
- **New confound found:** the AI belief uses the known fleet law, while the EB fleet belief nearly abstains on SiV. Hence the new `kg` control.
- **v2 guard design chosen on dev runs:** a single prior frozen at warm-up end (REFRESH = (2,)), hedge weight 0.5. Refreshing at (2, 5, 11, 23) cost more (ln 4) than it gained.

**Block B smoke test** (`gcarry`, 1 network): +0.6 points on D, −1.2 on Djb against `gexact`. This is consistent with Prop. 7's prediction that it buys little.

**Next:** PSC dev pilot P24 (1,400 tasks) + P24B (192); then lock the pre-registration.

## E88 — Study 24 PSC dev pilot, latency added, pre-registration locked (10 Oct 2026)

**Dev pilot on PSC** (8 networks per cell):
- P24 runs.csv sha 57ceeaf7 (1,400 tasks); P24B sha 6f36b42b (192).
- Guarded arms: 0 bad pairs everywhere.
- **Block A pilot gains:**
  - `ag2 − bg` on NV + SiV: +21.7;
  - `ag2 − kg` on thin hw, correlated patterns: +14.0;
  - on unseen patterns: +5.3;
  - on independent links: +0.3;
  - `ag2 − ag1`: −0.09;
  - `ag2 − lg`: +0.06;
  - `kg − fg` (thin): +9.3;
  - on ions, `ag2 − kg`: +0.2.
- **Block B pilot:** `gcarry − gexact` from −0.4 to +0.8 per cell; `gpersist` bad 12 and 23 (Dj), 122 and 463 (Djb).

**Latency added before the confirmatory run** (advisor's request): queue, service, end-to-end histograms, attempts, hold time, oracle service.
- Recording only. Deliveries were identical to the previous code (028a2538) on 4 dev tasks.

**Locked:**

| File | sha |
|---|---|
| `study24.py` | 7be8c292 |
| `study24b.py` | 5d24bef6 |
| `analyze_24.py` | f8ef96d6 (tested on synthetic data) |
| `tasks_s24` | ea8f322e (11,200 tasks) |
| `tasks_s24b` | 619f6add (1,536 tasks) |

**Hypotheses:** H1–H4 primary; H5–H7 secondary, with H6 and H7 predicted to FAIL; B1–B2 primary; B3 secondary. Details: `24_ai_v2_hardware/README_24.md`.

## E89 — Study 24 confirmatory results (10 Oct 2026)

**Runs:**
- A: runs.csv 71e3cc31 (11,200 tasks; 60.7 SU).
- B: runs.csv 9f8633ed (1,536 tasks; 14.9 SU).
- Hashes match the pre-registration (E88). Reproduced on the Mac.

**Block A:**
- **H1 PASS:** 0 bad in 34.8M guarded deliveries. `b` had r > 1% in 9 of 25 cells (max 2.2%, SiV).
- **H2 PASS:** `ag2 − bg` on thin hw +20.0 [19.2, 20.9].
- **H3 PASS:** `ag2 − kg` +11.4 [10.5, 12.3].
- **H4 PASS:** unseen patterns +4.4 [4.0, 4.8].
- **H5 PASS:** +1.07.
- **H6 PASS, barely:** +0.22, lower bound +0.001. The pilot predicted FAIL.
- **H7 PASS:** +0.54 [0.35, 0.74], thin hw only. The pilot predicted FAIL.
- **Decomposition, SiV:** known law +17.7, AI +5.8. **NV:** AI +13.6. **Ions:** AI ≤ 0.4.

**Block B:**
- **B1 PASS:** 0 bad.
- **B2 PASS:** `gcarry − gexact` +0.30 [0.22, 0.38].
- **B3 CONFIRMED:** `gpersist` bad 55/204 (Dj) and 1,251/3,002 (Djb), with 7–11% of paths bad under Djb.

**Latency (descriptive):** the guard adds no measurable latency on ion hardware. On SiV, queueing dominates (about 20 of about 25 s), and the AI serves 6.5× more requests at similar latency.

Details: `24_ai_v2_hardware/RESULTS_24.md`.

## E90 — ICFO 2021 Stage 1 pre-registered (10 Oct 2026; before any visibility or concurrence on real data)

**Dataset:** Zenodo 6454536 (Lago-Rivera et al., Nature 2021), raw time tags, downloaded by Tanish into `22_external_checks/icfo_2021/`.

**Looked at before pre-registering** (structure only): file names, the authors' MATLAB scripts, singles rates, and one herald–signal delay histogram (echo near 2.04 µs).

**Locked files:**

| File | sha |
|---|---|
| `PREREG_ICFO_STAGE1.md` | f3ebc014 |
| `stage1/icfo_stage1.py` | 79a2caad (tested on synthetic data: V = 0.80 recovered as 0.78–0.81) |
| `stage1/synth_icfo.py` | fa13fb43 |

**Tests:**
- **R1-A** (primary): 2 µs V ∈ [0.78, 0.90].
- **R1-B** (primary): 2 µs F_eff ∈ [0.89, 0.95].
- R1-C (secondary): 2 µs C ∈ [0.80, 1.50]e−2.
- R1-D (secondary): ρ(τ, C) ≤ −0.7 and C(25 µs) z ≥ 5.
- **R3** (descriptive): real-data over-dispersion and coverage of the anytime-valid confidence sequence.

## E91 — ICFO Stage 1: environment shim and the single decoding fix (10 Oct 2026, recorded before the fixed re-run)

**Environment.** The Mac VM has no scipy and no network. A minimal shim (`stage1/shim/scipy`: betaln, chi2.sf) was validated against scipy in the cloud: max relative error 7e−14 for betaln, max absolute error 9e−15 for chi2.sf. The analysis is unchanged.

**First run (79a2caad), 2 µs.** V(rms) = 1.014 ± 0.011; max|E| = 0.884; F_eff = 1.007; p10 = 0.0103; p01 = 0.0210; h_c(2) = 0.0345; C = 0.0263; R3 dispersion 9.6. The script crashed at 19 µs.

**Bug found.** 12 of 254 files contain a backward time jump near the end of a run (a "Hydra" glitch, which the authors' own script trims with Tremove). `count_in` assumes sorted tags.

**Single allowed fix** (as pre-registered): keep only tags ≥ the running maximum. This drops 885–1,057 tags in the affected files and none elsewhere. Fixed script: a4d4124c. The 2 µs coherence files were not affected, so R1-A is unchanged by the fix.

## E92 — ICFO Stage 1 results (10 Oct 2026)

**Run:** fixed script a4d4124c; output `stage1/out_all_fix1.json`.

**Pre-registered verdicts:**
- **R1-A FAIL:** V(rms, 2 µs) = 1.014. The estimator assumed evenly spread phases, which the data violate.
- **R1-B FAIL:** F_eff = 1.007.
- **R1-C FAIL:** C = 2.64e−2.
- **R1-D PASS:** ρ = −0.90; C(25 µs) = 6.2σ.
- **R3:** over-dispersion in 9 of 12 runs (dispersion 0.73–5.6); the anytime confidence sequence never excluded the full-run estimate in 11 of 12 runs.

**Exploratory, post hoc:** h_c(2) = 0.033 vs 0.036(8); max|E| = 0.884 vs 84(2)%; per-output C = 1.12e−2 vs 1.15(5)e−2.

Details: `22_external_checks/icfo_2021/STAGE1_RESULT.md`.

## E93 — Public release (10 Oct 2026)

**GitHub:** https://github.com/tanishsinghrajpal1029/safe-entanglement-delivery
- Initial commit e0d2029.
- ICFO Stage 1 commit 5aa185c.

**Zenodo:** concept DOI 10.5281/zenodo.23287414 (all versions); v0.1.0 DOI 10.5281/zenodo.23287415.
- From this release on, every pre-registration has a third-party timestamp.

## E94 — ICFO Stage 1 re-run on PSC with real scipy (10 Oct 2026)

**Run:** same script, a4d4124c (hash checked on PSC).

**Result:** every primary and secondary number is identical to the Mac run, at all 5 storage times: window, p10, p01, h_c(2), C, C_sd, C_z, F_eff, V, V_max and E_k.

**Coverage:** these numbers do not use scipy. The R3 lines, the only ones that do (betaln, chi2.sf), are to be compared from `out_psc.json`.

**v0.1.1 released on GitHub** by Tanish, which archives the ICFO stage on Zenodo.

## E95 — Correction to E92 and ICFO R3 shim check (10 Oct 2026)

**Correction.** There are **11** both-open runs, not 12 (2 µs: 1; 7 µs: 2; 12 µs: 1; 19 µs: 3; 25 µs: 4).
- Over-dispersion is significant (p < 0.05) in **7 of 11** runs, not "9 of 12".
- The anytime confidence sequence never excluded the full-run estimate in **10 of 11** runs, not "11 of 12".
- The E92 text stands as written; this entry supersedes those two counts. `STAGE1_RESULT.md` has been corrected and marked.

**Shim check.** The PSC R3 output (real scipy) matches the Mac (shim) in all 11 runs. Dispersion ratios are identical, p-values agree to about 1e−15, and the CS flags are identical. The scipy caveat is closed.

## E96 — USTC 2026 Stage 1 pre-registered (10 Oct 2026; headers only were seen)

**Dataset:** Zenodo 18218281 (18 figure workbooks), downloaded by Tanish into `22_external_checks/ustc_2026/`.

**Locked files:**

| File | sha |
|---|---|
| `PREREG_USTC_STAGE1.md` | 10dad084 |
| `stage1/ustc_stage1.py` | 9ae8a9fc |
| `stage1/synth_ustc.py` | a26a3dc1 |

**Tests:**
- **U1** (primary): our pure-dephasing memory model, fed only the single-ion KDD coherence (Fig. S2b), predicts the remote ion–ion fidelity decay (Fig. 3d). Bar: within 2σ + 0.02 at every storage time.
- **U2** (secondary): per-set QBER (Fig. S8) — over-dispersion, and coverage of the anytime confidence sequence.

## E97 — USTC Stage 1 results (10 Oct 2026)

**U1 PASS, but a weak test.** The predicted fidelity decay is within the bar at all 4 storage times (100–450 ms). The model is optimistic by 0.020–0.044 at every point.

**U2:**
- 200 sets (not 201); dispersion 3.57 (p ≈ 0).
- The confidence sequence excluded the full-run rate for 3.5% of the run.
- Caveat: equal set sizes were assumed.

Details: `22_external_checks/ustc_2026/STAGE1_RESULT.md`.
