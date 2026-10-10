# Study 18C v20: a T1-aware controller (pre-registered 7 Oct 2026, before any confirmatory run)

**Why.** v19 (E49) found the depolarising-storage controller model unsafe for amplitude-damping-limited memories (T2 = 2 T1): 10–39% bad deliveries on ion cells. v20 gives the controller the physical memory model.

**Method.**

- The controller's per-draw fidelity prediction uses `ptm_model.delivered_F`. This is a vectorised Pauli-transfer form of the NetSquid-validated exact T1/T2 model: it matches the exact model to 6×10⁻¹⁶ for all memory regimes and L = 1–3, and costs 0.5 ms per attempt for 256 draws.
- The controller uses the per-link waits it observes.
- Everything else is the v17 eb128 controller (estimated fleet prior, window threshold).
- The truth is the exact T1/T2 model, as in v19.

| Config | Truth memory | Controller |
|---|---|---|
| `ad_eb128` | T1 = T2/2 | Depolarising model (replicates v19) |
| `ad_eb128t1` | T1 = T2/2 | T1-aware, correct T1 |
| `ad_eb128t1opt` | T1 = T2/2 | T1-aware, assumes T1 25% too long (under-states damping) |
| `t1eq_eb128t1` | T1 = T2 | T1-aware |
| `deph_eb128t1` | T1 = ∞ | T1-aware. This removes the depolarising model's built-in pessimism, so it is a margin test. |
| `deph_eb128` | T1 = ∞ | Depolarising model (paired efficiency reference) |

**Design.** 4 cells (as v16–v19) × 6 configs × 64 fresh paths (seeds 18981–18983), g = 1e-5. That gives **1,536 tasks**.

## Cloud dev pilot (disclosed; seeds 19981–19983; 2–12 paths per cell; no confirmatory-seed runs)

| Cell | ad, depolarising | ad, T1-aware | ad, T1 +25% | t1eq, T1-aware | deph: T1-aware / depolarising deliveries |
|---|---|---|---|---|---|
| ion-proj L3 (4 paths) | 41.5% | 0.88% | 9.9% | **1.20%** (36/2990) | 6.7× at 0.05% |
| τ 0.85 (2 paths) | 11.9% | 0.61% | 4.0% | 0.31% | 1.02× at 0 |
| NV (12 paths) | 0 | 0 | 0 | 0 | 2.2× at 0 |

**What the pilot showed:** the fix works on the failing cells. But a +25% error in T1 already breaks it, and one small pilot cell (t1eq ion-proj) was above 1%.

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `ptm_model.py` | `bf59d252191eefbd` |
| `drift_queue_des_v20.py` | `d32425558dcc19e6` |
| `tasks_v20.jsonl` | `7523813a0511098e` |
| `analyze_v20.py` (locked; tested on synthetic data) | `6ffdf7c91b035620` |

## Hypotheses (cells need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **Q1** (primary) | A T1-aware controller with correct T1 is safe | r ≤ 1% in every cell under ad, t1eq and deph |
| **Q2** | Replication | The depolarising controller under ad exceeds 1% in ≥ 1 cell |
| **Q3** | Sensitivity limit | T1 over-estimated by 25% exceeds 1% in ≥ 1 cell (predicted from the pilot) |
| **Q4** | Efficiency | Under deph, T1-aware qualified deliveries ≥ depolarising (paired) in every cell |

**How results will be read:**

- **Q1 pass:** the amplitude-damping limitation is resolved *given T1 known*, with the T1-accuracy requirement stated via Q3.
- **Q1 fail:** the amplitude-damping regime stays a stated limitation.

**PSC.** 8 × 16 cores × 20 min, so the ceiling is 42.7 SU (worst case ≈ 397 of 400); expected about 8–12 SU.
