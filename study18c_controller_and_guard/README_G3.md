# Study 18C G3: scaling to a 30 × 30 grid (pre-registered 8 Oct 2026, before any confirmatory run)

**Why.** G2 showed on a 5 × 5 grid that the anytime-guarded controller delivers no bad pairs, while the frozen controller's risk clusters by path (E69). G3 asks whether this holds at network scale, with thousands of paths and a prior learned from the network's own hardware.

## Design

The model is G2's (G1 simulator, `NetG` with the guard), with these changes:

| | |
|---|---|
| Grid | 30 × 30 nodes, 1,740 links. Requests between random node pairs at hop distance 1..Lmax (ion2020: 2; ionproj: 3), choosing among all shortest paths |
| Router | `best` only |
| Request rate | 10 per s over 3,000 s (≈ 27,000 requests per network) |
| Controllers | `cal` = frozen C2 controller; `calg` = `cal` plus the anytime guard, α = 0.05 (Prop. 6) |
| Fleet prior | `ext` = 128 external fleet link-windows (as G1/G2). `own` = one pre-run calibration window on 512 links sampled from the network itself, i.e. the network learns its prior from its own hardware (**new**) |
| Groups | hw {ion2020 τ 0.90, ionproj τ 0.90} × ctrl {cal, calg} × fleet {ext, own} = 8 groups × 32 networks = **256 tasks** |
| Pairing | Each network is paired across controller and fleet prior |
| Seeds | 19121–19124 (fresh) |

**Unchanged simplifications (stated):**
- no link contention;
- no drift in time (g ≈ 0);
- dephasing-only memory;
- batched 100-s windows;
- request distance limited by physics to 2–3 hops.

At τ = 0.90 there is no long-distance delivery without error correction, so a 30 × 30 grid is many neighbourhoods operating at once. It is not long paths.

## Cloud smoke and timing (disclosed; seeds 20121–20124; one network each)

| Group | Delivered | Bad | Paths bad / delivering | ŝ / s_true | Time |
|---|---|---|---|---|---|
| ionproj, cal, own | 23,727 | 171 (0.72%) | 162 / 13,262 (1.2%) | 1.02 | 111 s |
| ion2020, calg, own | 11,119 | 0 | 0 / 2,609 | 1.07 | 142 s |
| ion2020, calg, ext (earlier timing run) | 11,020 | 0 | 0 / 2,494 | — | 131 s |

Peak memory is about 1.4 GB per worker.

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_g3.py` | `0baa303cb5722863` |
| `tasks_g3.jsonl` | `06cf28e8d3e95caa` |
| `analyze_g3.py` (locked; tested on synthetic data) | `7789af9963077495` |

G3 uses `drift_queue_des_g2.py` (`b3f90eaa06042f35`), `drift_queue_des_g1.py` (`4cc0016adedf331d`) and the C2 modules unchanged.

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **H1** (primary) | The guarded controller is safe at scale | `calg`: r ≤ 1% in all 4 groups |
| H1b | No path clustering | `calg`: network-bootstrap 95% upper bound ≤ 1% in all 4 groups |
| **H2** (Prop. 6) | Per-path guarantee at scale | `calg`: bad paths / delivering paths ≤ 5%, pooled |
| **H3** | The frozen controller's pooled risk holds at scale | `cal`: r ≤ 1% in all 4 groups |
| H4 (descriptive) | Own-hardware prior vs external fleet | r, % paths bad, ŝ/s, fraction of oracle |
| H5 (descriptive) | Cost of the guard at scale | fraction of oracle, `calg` vs `cal` |

**Commitment.** No re-tuning after the run. Failures are reported as limits.

**PSC.** 8 shards × 16 cores × 30 min, so the ceiling is 64 SU. Expected about 10–20 SU.
