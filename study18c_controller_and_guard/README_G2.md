# Study 18C G2: a per-path anytime-valid guard on networks (pre-registered 8 Oct 2026, before any confirmatory run)

**Status: post-hoc remedy.** G1 (E66) failed H1, and that verdict stands. The diagnosis (E67, exploratory) is that the fleet-prior posterior is calibrated **marginally**, averaged over paths drawn from the fleet. So Proposition 2 bounds the **pooled** risk, not the risk on a given path. A path whose true fidelity sits at the threshold can receive many all-bad deliveries in one optimistic calibration window.

## Remedy

Keep the frozen Bayesian rule, which controls the pooled risk at δ = 1%, and **add a per-path guard**:

- Every link keeps all its calibration counts since the start. Links are stationary (g ≈ 0), as in G1.
- For each link, compute a (1 − α/Lmax) **anytime-valid** lower confidence bound on its parity probability. It comes from the Beta(1/2, 1/2) mixture martingale (Robbins; prior–posterior ratio): CS = {p : B(1/2 + K, 1/2 + N − K)/B(1/2, 1/2) / (p^K (1 − p)^(N − K)) < Lmax/α}.
- Deliver only if, in addition, the PTM-model fidelity at the links' lower bounds, using the actual waits, is ≥ τ.
- α = 0.05.

**Proposition 6 (per-path anytime guarantee).** Assume the physics model is exact and the links are stationary. Then for **every** path, whatever its true quality,

P(the path ever delivers a pair with true F < τ) ≤ α, over the whole run.

*Proof.* By Ville's inequality, all of the path's link bounds hold at all times with probability ≥ 1 − α. F is increasing in each λ, so on that event every delivered pair has true F ≥ F_guard ≥ τ. ∎

**Checked before the run.** On simulated stationary links (p = 0.96, about 5,400 counts per epoch, 30 epochs, 2,000 repetitions), miscoverage at level 0.025 was 0. The interval half-width in p is 0.012 after one epoch, 0.004 after 10 and 0.002 after 30.

## Design (1,280 tasks; G1's networks and simulator, fresh seeds 19111–19114)

| Block | Groups | Networks |
|---|---|---|
| G grid 5 × 5 | hw {ion2020 τ 0.90, ionproj τ 0.90} × route {random, best} × ctrl {cal, calg} = 8 | 64 |
| K best-of-k | hw {nv τ 0.80 L1, ion2020 τ 0.90 L2} × k {1, 3, 8} × route best × ctrl {cal, calg} = 12 | 64 |

- `cal` is the frozen controller, as in G1. `calg` is `cal` plus the guard.
- Each network is paired across the two controllers.
- New per-network outputs: `paths_delivered`, `paths_bad` (paths with at least one bad delivery), `max_path_bad` and `guard_blocks`.

## Dev pilot (disclosed; cloud; seeds 20111–20114; used only for code checks and timing)

| Group | cal: delivered / bad / paths bad | calg: delivered / bad / paths bad |
|---|---|---|
| G ion2020 grid, best (1 network) | 3,632 / 35 / 19 of 79 | 3,350 / 0 / 0 of 50 |
| K nv k8 (4 networks) | 2,751 / 57 / 2 of 24 | 2,390 / 0 / 0 of 22 |
| K ion2020 k1 (6 networks; 5 have no feasible path, oracle 0) | 368 / 0 | 590 / 0 |

Under `cal`, 19 of 79 grid paths delivered at least one bad pair. **The per-path weakness is large.**

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_g2.py` | `b3f90eaa06042f35` |
| `tasks_g2.jsonl` | `96a5c77c2f6b89e2` |
| `analyze_g2.py` (locked; tested on synthetic data) | `78e46e33b137a444` |

G2 also uses `drift_queue_des_g1.py` (`4cc0016adedf331d`) unchanged.

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **H1** (primary) | The guarded controller is safe | `calg`: pooled r ≤ 1% in **every** tested group |
| **H1b** | The guard removes path clustering | `calg`: network-bootstrap 95% upper bound ≤ 1% in every tested group |
| **H2** (Prop. 6) | Per-path guarantee | `calg`: (paths with ≥ 1 bad delivery) / (paths with ≥ 1 delivery) ≤ 5%, pooled |
| H3 (descriptive) | Cost of the guard | fraction of oracle, `calg` vs `cal`, per group |
| H4 (descriptive) | G1 replicates on fresh seeds | `cal` risks, upper bounds, paths bad |

**Commitment.** No re-tuning of α or the guard after the run. If H1 or H2 fails, the failing groups are reported as limits.

**Scope (stated).** The guarantee needs stationary links and an exact physics model. Under drift, the confidence sequence must restart at each known re-alignment, and downward drift between re-alignments needs the drift-aware likelihood; that combination is untested here.

**PSC.** 8 shards × 16 cores × 30 min, so the ceiling is 64 SU. Expected about 10–15 SU.
