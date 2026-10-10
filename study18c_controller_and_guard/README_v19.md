# Study 18C v19: non-Werner (T1/T2) memories, NetSquid-validated, end to end (pre-registered 6 Oct 2026, before any confirmatory run)

**Why.** The critique asked about "relevance beyond this simulator". E14 validated our primitives against NetSquid, but only for Werner states with depolarizing storage. Real memories, and NetSquid's `T1T2NoiseModel`, combine **amplitude damping with dephasing**. The other agent's NetSquid parity data shows exactly this: at 200 µs the Z parity is 0.64 while X/Y is 0.47.

**What changes.** Only the truth. The controller (eb128) keeps its depolarizing-storage model. Each delivered pair's real fidelity is computed exactly with T1/T2 memories (coherence time T2 = the model's T2):

| Memory regime | T1 | Typical of |
|---|---|---|
| `deph` | ∞ | Trapped-ion hyperfine memories (pure dephasing) |
| `t1eq` | T2 | Mixed |
| `ad` | T2/2 | The amplitude-damping limit |

**Files (sha256, first 16):**

| File | Role | sha |
|---|---|---|
| `memory_t1t2_exact.py` | Exact branch-summed density-matrix model | `fc044e141f7c90ca` |
| `netsquid_t1t2_check.py` | NetSquid validation of that model (run on the Mac) | `447cf33ce5af2395` |
| `memory_bias_scan.py` | Pointwise bias scan (deterministic, no controller) | `4d498cf9eaf98a0b` |
| `drift_queue_des_v19.py` | Controller end to end | `541b21bf9ef8fdab` |
| `tasks_v19.jsonl` | 768 tasks: 4 cells × 3 memories × 64 fresh paths, g = 1e-5, seeds 18971–18973 | `55b8fa84ba21215d` |
| `analyze_v19.py` | Locked analysis; tested on synthetic data | `1e2a0a57b2064ae4` |

**Self-check.** With depolarizing storage, the exact model reproduces the controller's model to 3.9×10⁻⁶. That residual is the DEJMPS table interpolation.

## Disclosed before the run: pointwise bias scan (true F minus model F, 400 operating points per cell)

| Memory regime | Result |
|---|---|
| `deph` | The model is **pessimistic everywhere**: bias ≥ +3×10⁻⁵ (median +0.009 to +0.038). Zero label flips. |
| `t1eq` | Bias ≈ 0 for the ion cells (≥ 0). NV goes down to −0.014 on 2% of points, with no label flips. |
| `ad` | The model is **optimistic**: median −0.008 to −0.016, and 5–60 label flips per 400 points. |

Dev smoke tests ran on seeds 19971–19973 only.

## Hypotheses (cells need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **N1** | Safe with dephasing-only memories | `deph`: r ≤ 1% in all 4 cells |
| **N2** | Safe with T1 = T2 | `t1eq`: r ≤ 1% in all 4 cells |
| **N3** | Expected limitation | `ad`: r > 1% in ≥ 1 cell |
| **N4** | Paired check | Under `deph`, bad deliveries are never more than under the model's own (Werner) truth, in every cell |

**How results will be read:**

- **N1 and N2:** guarantee transfer to physical memories with T1 ≳ T2.
- **N3:** memories near the T1 limit need amplitude damping in the controller's model. This is stated as a limitation and is not fixed here.

**Compute.** Runs in the cloud workspace (2 cores, about 1 h). No PSC.
