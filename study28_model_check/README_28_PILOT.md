# Study 28 ("model-checked delivery"): design and dev pilot (11 Oct 2026)

**Status:** dev pilot only. The confirmatory pre-registration (hypotheses, bars, locked `analyze_28.py`) will be written after the pilot and committed publicly before any confirmatory job, as in Studies 26 and 27.

## Question
Can the tests a user already runs for the model-free certificate also detect when the model behind the per-pair guard is wrong, and limit the harm? What does a network-wide guarantee cost?

## Design (`study28.py`)
- **Network:** as in Studies 26–27, with a horizon of 90 epochs × 100 s (2.5 h), three times longer, because detection needs hundreds of tests.
- **Two test streams** per delivered pair (p = 0.1 and 0.2), each fresh and hidden from the network.
- **Readout:** test outcomes are flipped by readout error. Every check and certificate declares the hardware's own readout error as its bound (ions 0.001, NV 0.03, SiV 0.01).
- **Arms:**

  | Arm | What it is |
  |---|---|
  | kg | Study 26/27 guard (reference) |
  | kgN | Network-wide guard: link confidence sequences at α/40 |
  | kgM | kg + model check (e-process, `mcheck.py`) with margin response |
  | kgNM | kgN + model check |
  | kgP | kg + naive per-epoch binomial detector (Bonferroni over 90 epochs) with the same response |

- **Scenarios:**
  - none;
  - undeclared model optimism Δ = 0.044;
  - USTC-level persistent noise;
  - memory fault at epoch 45 (T₂ ÷ 5);
  - readout error at the declared bound.
- **Baselines on ion hardware, Δ = 0.044:**
  - margin declared from 16 tomography points (Study 26);
  - margin known exactly (oracle).
- **Hardware:** ion2020, ionproj, NV, SiV. Seeds: dev 20301–20304 (pilot); confirmatory 19301–19304 (fresh).
- **Tasks:**
  - pilot `tasks_p28.jsonl`: 1,312 tasks, 8 networks per cell;
  - confirmatory `tasks_s28.jsonl`: 5,248 tasks, 32 networks per cell.

## Theory (`THEORY_28.md`)
- **Proposition MC:** false-alarm probability ≤ β (validity), with restarts.
- **MC-delay:** a bound on the detection delay.
- **Proposition LB:** converse floor for model-free certification. Our certificate is within a factor of 1.9–2.3 of it.
- **Corollary NW:** a network-wide guarantee.
- **Numerical checks:** `mcheck_out.json`, `lb_out.json`.

## Review and dev changes (disclosed)
**Adversarial review** (`REVIEW_28.md`): no blocker, seven major findings, all addressed before the pilot.
- **M1 power:** the pilot measures tests per run and alarm rates. kgM hypotheses will be tested only in powered cells; the rest are declared as predicted nulls.
- **M2 margin update:**
  - The increment is now capped at DMAX = 0.10 (the USTC 95% bound).
  - Segments with fewer than 50 tests use the fixed step 0.02.
- **M3 false-alarm metrics:**
  - first alarm against the delivered-pair and the tested-pair nulls;
  - per-segment false alarms;
  - reported by scenario.
- **M4 readout:** declared readout bound in q, plus a readout scenario.
- **M5/M6 converse:** product-form proof, the "every all-pass record" hypothesis, and a γ-sensitivity table.
- **M7 baselines:** tomography and oracle margins added, plus a naive detector.
- **Minor items:**
  - safety metrics over all deliveries;
  - kept-pair harm counts;
  - cache trimming (memory);
  - the fault epoch recorded in each row;
  - an assertion on the horizon;
  - a restart check in the Monte Carlo.

**Design choices made on 1–4 dev smoke networks** (ion2020/ionproj, Δ = 0.044; disclosed here, not tuned on the pilot):
- **Margin response:**
  - first tried: the point estimate (unbounded) — reviewer flagged that it can shut delivery down;
  - then a Hoeffding upper bound: over-conservative, margin 0.086 vs true 0.044;
  - now: an empirical-Bernstein upper estimate (margin 0.066–0.074 on ion2020/ionproj).
- **Readout bound:** a fixed 1% removed all detection power on ions, so it was replaced by each hardware's own specified readout error.

## Smoke results (dev networks, not evidence)
**ion2020, Δ = 0.044, p = 0.1:**

| Arm | Bad pairs delivered | First alarm | Bad pairs after the alarm | Qualified pairs |
|---|---|---|---|---|
| kg | 13,820 | — | — | 12,164 |
| kgM | 5,129 | epoch 35 | 0 of 6,472 | 10,978 |

**Other cells:**
- **No stressor, readout at the bound:** no alarms.
- **Naive per-epoch detector:** no alarm under Δ = 0.044.
- **SiV:** 3–30 tests per run, so no power.
