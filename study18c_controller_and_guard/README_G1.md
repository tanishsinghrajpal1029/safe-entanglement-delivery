# Study 18C G1: the frozen final controller on networks with route choice (pre-registered 8 Oct 2026, before any confirmatory run)

**Why.** Real networks are not one line. A router picks a path, usually the one that *looks* best from the same calibration data the delivery controller then uses. Picking the best-looking of several noisy estimates is a selection effect (winner's curse). G1 asks whether the label-free controller stays safe when the path itself is chosen from the data.

## Theory (stated before any run)

Proposition 2 extends to route choice. If:
- the router's choice is a function of the data D, and
- the controller's p = P(F < τ | D) is the posterior under the true law, given **all** of D (including the data used to choose the path),

then {path chosen, p ≤ t} is D-measurable, and the tower property still gives r(t) = E[p | delivered].

So selection on D does **not** bias a calibrated controller. A controller whose p is not the true posterior (flat prior, `flat`) is exposed: selection picks paths whose estimates are optimistic by luck.

## Model

New module `drift_queue_des_g1.py`. Physics is the NetSquid-validated PTM model; the fleet prior is v21's (`m123`); the threshold rule is C2's.

| | |
|---|---|
| Topology `grid` | 5 × 5 nodes, 40 nearest-neighbour links. Requests between random node pairs at hop distance 1..Lmax (ion-2020: 2, ion-proj: 3). Candidates = all shortest paths (1–3 per request). |
| Topology `par` | Best-of-k: two end nodes joined by k ∈ {1, 3, 8} disjoint paths of Lmax links (NV-like L = 1; ion-2020 L = 2). |
| Links | F0 ~ Normal(F0, 0.2(1 − F0)) (v18 law), drift phase u ~ U(0, 1), λ = (4F0 − 1)/3 − 0.02u; g ≈ 0 (no drift in time, as P1); dephasing-only memory. |
| Calibration | ρ = 0.3. Every T = 100 s epoch, each link yields n ~ Poisson(ρRT), k ~ Binomial(n, (1 + rλ)/2). Decisions use the previous complete epoch, so **router and controller see the same counts**. |
| Requests | Poisson arrivals (ion 3/s, NV 0.3/s), served one at a time; path chosen once per request; ≤ 4 attempts of two chains plus DEJMPS; true F from the PTM model with true λ and the actual waits. |
| Horizon | 30 epochs (3,000 s); first 3 epochs excluded from statistics. |
| Controllers | `cal` = frozen C2 controller: EB fleet prior from 128 fleet link-windows, uniform-s hyperprior, 5% fault component, exact binomial likelihood, PTM physics, window local-fdr threshold δ = 1%. `flat` = same rule with a Jeffreys posterior per link. |
| Routers | `random` ignores data. `best` maximises Σ log λ̂ over the path's links, with λ̂ the controller's **own** point estimate (posterior mean for `cal`; Jeffreys centre for `flat`). |
| Oracle | Knows the true λ; picks the truly best candidate; delivers iff true F ≥ τ. Gives the throughput reference. |

**Simplifications, stated:**
- no link contention or concurrent requests;
- no drift in time;
- dephasing-only memory;
- a batched 100-s window.

These isolate the selection effect. They are not claims about full network operation.

## Design (1,280 tasks)

| Block | Groups | Networks per group |
|---|---|---|
| G grid 5 × 5 | hw {ion2020 τ 0.90, ionproj τ 0.90} × route {random, best} × ctrl {cal, flat} = 8 | 64 |
| K best-of-k | hw {nv τ 0.80 L1, ion2020 τ 0.90 L2} × k {1, 3, 8} × route best × ctrl {cal, flat} = 12 | 64 |

The network draw depends only on (block, hw, topology, k, idx), so it is **paired across controllers and routers**. Seeds 19101–19104 are fresh.

## Dev pilot (disclosed; cloud; seeds 20101–20104; 1 network each; used only for code checks and timing)

| Group | Deliveries | Bad | Selection bias (est − true, Σ log λ) |
|---|---|---|---|
| G ion2020 best, cal | 4,056 | 31 (0.76%) | −0.0001 |
| G ion2020 best, flat | 3,932 | 68 (1.73%) | +0.0006 |
| K nv k = 8, cal | 781 | 10 (1.28%) | −0.022 |
| K nv k = 8, flat | 825 | 3 (0.36%) | +0.033 |
| G ionproj random, cal | 7,018 | 58 (0.83%) | −0.0007 |

- **At risk:** NV best-of-8 under `cal` (1.28% in one network; 781 deliveries is small).
- In the pilot, `cal` risks sit close to δ = 1%. This is expected: the window rule targets δ, and easy short requests let the threshold loosen.

**Files (sha256, first 16):**

| File | sha |
|---|---|
| `drift_queue_des_g1.py` | `4cc0016adedf331d` |
| `tasks_g1.jsonl` | `bf06e4a190c464c2` |
| `analyze_g1.py` (locked; tested on synthetic data) | `0c9a19c04fe76abb` |

G1 uses v15, v16, v17, v18, v21, `ptm_model` and `memory_t1t2_exact` unchanged (hashes as C2).

## Hypotheses (groups need ≥ 200 deliveries)

| | Prediction | Bar |
|---|---|---|
| **H1** (primary) | The calibrated controller is safe with route choice | `cal`: pooled r ≤ 1% in **every** tested group (10 groups) |
| H1b (stricter) | Same, allowing for clustering by network | `cal`: network-bootstrap 95% upper bound ≤ 1% in every group |
| **H2** (mechanism) | Winner's curse exists for `flat` but not for `cal` | For both nv and ion2020: `flat` selection bias at k = 8 > at k = 1, and `cal` selection bias at k = 8 ≤ 0 |
| **H3** (consequence) | Selection raises the uncalibrated controller's risk | `flat` r at k = 8 > r at k = 1, both hardware types |
| H4 (descriptive) | Cost and benefit of route choice | r and fraction of oracle, best vs random (grid) and vs k |

**How results will be read:**
- **H1 pass:** route choice does not break the calibrated controller. This is the network-level claim, stated with its simplifications.
- **H1 fail:** route choice is a stated limitation, with the failing groups named. No re-tuning and no re-run on new seeds.

**PSC.** 8 shards × 16 cores × 30 min, so the ceiling is 64 SU. Expected about 5–15 SU (≈ 5 CPU-hours by cloud timing). About 650 SU are charged so far, of the 1,000 approved.
