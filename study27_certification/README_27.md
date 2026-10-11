# Study 27 ("certified delivery, certification layer"): pre-registered 11 Oct 2026, before the confirmatory run

**Why.** This study runs the model-free certificate (Proposition C1, `THEORY_CERTIFIED_2026-10-11.md` v2) on top of the model-based control layer from Study 26. It covers the scenarios where Studies 25 and 26 showed the model-based layer breaks.

It checks four things:
- **(i)** that the certificate stays valid where the control layer fails, as theory says it must;
- **(ii)** how tight it is;
- **(iii)** what it costs;
- **(iv)** the per-user resource floor.

Proposition C1 is a known-type result (prior art in the theory note §3). This study measures its behaviour **in an adaptive network**; it does not claim novelty for the theorem.

## Design (`study27.py`)
**Network:** the 5 × 5 grid, the 'field' link pattern, serial service and greedy routing, with the Study 26 Net26 code (locked, sha 56436cc8). 32 networks per cell, paired across arms and scenarios.

**Hardware:** ion2020, ionproj, nv2, siv.

**Scenarios:**

| Scenario | What it does |
|---|---|
| `-` | No stressor |
| `o0.044_m0` | Undeclared model optimism Δ = 0.044 (the USTC level) |
| `n0.184_a` | USTC-level persistent (AR 0.9) shared noise |
| `fault` | From epoch 15, every memory's true T2 drops by 5×. Calibration counts and models are unaware |

**Traffic:**
- `uni`: users chosen uniformly.
- `hot`: 80% of requests come from 4 fixed one-hop users.

**Control arms:**
- `kg`: per-user corrected guard;
- `b`: risk controller only, no guard;
- `plug`: the published-style plug-in rule.

**Certification layer:**
- Every delivered pair in the measurement period is tested with probability p ∈ {0.05, 0.1, 0.2}, using fresh user randomness, in a random basis X/Y/Z. The error is drawn from the pair's **true** correlators (`ptm_corr.py`; the identity 1 − F = Σe/2 is checked to 2·10⁻¹⁶).
- The three values of p use independent test streams on the same deliveries.
- `cert.py`: α = 0.05, an 8-value λ grid on [λ_max/16, 0.98λ_max], ideal measurements.

**Checks:**
- After **every** kept pair, each user's certificate and the network-pooled certificate are compared with the true running average fidelity of kept pairs.
- **Violated:** a certificate that is ever above the truth.
- **Eligible:** a certificate that was ever above 0. Only eligible certificates can be violated.

**Sizes and seeds:** 96 cells × 32 = **3,072 tasks**. Seeds 19291–19294 (fresh). Dev pilot: 20291–20294.

## Dev pilot (disclosed; dev data only)
- **Run:** sha `c5dd2ae6`, 768 tasks, 8 networks per cell.
- **Violations** (p = 0.05 / 0.1 / 0.2):
  - users: 0/828, 4/924 and 5/5,343;
  - networks: 2/479, 4/550 and 3/584.
- **Control layer broken, certificate still valid.**
  - Under undeclared optimism, ion2020 kg delivered 28% bad pairs.
  - The network's kept average fidelity was still 0.924, and the certificate (0.878) was valid.
  - So the average-fidelity certificate does **not** reveal per-pair threshold failures. That is exactly Proposition N.
- **Tightness:** hot ion users (≥ 500 kept pairs) saw gaps of 0.06–0.10. On SiV no certificate ever rose above 0, because there are too few pairs.
- **No code change** after the pilot.

## Hypotheses (`analyze_27.py`, sha 8d455051)

| | Tier | What is checked | Pass if |
|---|---|---|---|
| **C1** | primary | Per-user validity over all 96 cells, for each p: violated / eligible users, one-sided 95% cluster-bootstrap upper bound over networks | ≤ 5% |
| C1b | secondary | Every cell and p with ≥ 20 eligible users | Violation rate ≤ 10% (cell-level noise allowance) |
| **C2** | primary | Network-pooled certificate, for each p: violated / eligible networks, Clopper–Pearson 95% upper bound | ≤ 5% |
| C3 | descriptive | Validity in the cells where the control layer is not safe (per-user risk > 5% or r > 1%) | — |
| C4 | descriptive | Tightness for users with ≥ 500 kept pairs; the per-user resource floor | — |
| C5 | descriptive | Network-pooled certificate vs truth, by hw, scenario and arm | — |
| C6 | descriptive | Cost: kept qualified pairs by p | — |

**Commitment.** No change after this point; every outcome is reported. Study 27 is a check of the certificate in an adaptive network. Its primary hypotheses follow from the theorem, so a FAIL would mean a bug or a broken assumption, and would be reported as such.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `study27.py` | `1281b710d04137bf` |
| `cert.py` | `6b84bbdd3c10fd36` |
| `ptm_corr.py` | `47d89f1555c07513` |
| `analyze_27.py` | `8d4550512e715cb5` |
| `tasks_s27.jsonl` (3,072) | `452a078e01f090c9` |
| `study26.py` (locked) | `56436cc8` |

**PSC:** 32 shards × 16 cores × 45 min. Ceiling 384 SU; expected about 30 SU.
