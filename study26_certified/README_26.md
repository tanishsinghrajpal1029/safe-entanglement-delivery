# Study 26 ("certified delivery, control layer"): per-user level, real-data noise and margins, published baselines, finite memory

**Pre-registered 11 Oct 2026, before the confirmatory run.**

**Why.** This study fixes problems found after Study 25:
- the weakness review (`WEAKNESSES_REVIEW_2026-10-11.md`, items 1, 2, 4 and 6);
- the adversarial proof review (`26_certified/proofcheck/PROOF_REVIEW.md`).

Ledger E106–E108. Model-free certification of delivered pairs is a separate study (Study 27). This study tests the **model-based control layer** that decides what to deliver.

## What changed in the theory (and why the arms look different)
1. **Per-user level.** A user (an ordered source–destination pair) is served on a data-chosen candidate path. So Prop. 6's per-*path* bound gives only |U|·α/Lmax per user, where U is the set of links the user could touch.
   - Here every guard runs at **α/Umax**: Umax = 4 (Lmax = 2) and 7 (Lmax = 3).
   - Legacy arms (`…L`) keep α/Lmax, so the cost can be measured.
2. **Per-user metric.** `users_bad / users_total` counts every user that *ever* received a pair below threshold, over **all** users of the network.
   - This replaces "bad paths / delivering paths". That ratio is still reported, but the theorem doesn't imply it.
3. **The AI arm with a valid guarantee is `ag2t`.**
   - Prop. 10 is withdrawn. It is replaced by Lemma B: the prior must be independent of the link's own data that the confidence sequence uses.
   - `ag2t` meets Lemma B whenever the shared noise does not persist across epochs. `ag2` is not run.

## Design
Every block uses the 5 × 5 grid, the 'field' link pattern, greedy best-path routing and exact physics (PTM). Each cell has 32 networks, paired across arms and configurations within a block and hardware.

**Block U** (per-user level and published baselines).
- Hardware: ion2020, ionproj, nv2, siv. No shared noise. Serial service.
- Guard arms: bg, kg, ag2t (corrected level) and bgL, kgL, ag2tL (legacy level).
- Baselines (no risk controller and no guard; same fleet belief and same routing):
  - `plug`: plug-in fidelity rule, deliver iff F(point estimates) ≥ τ (the EFiRAP / Q-PATH / Q-GUARD class);
  - `plugM`: plug-in with a margin m;
  - `cut`: memory cut-off, deliver iff hold ≤ x / ((1 − ρ)R) (the Rozpędek et al. class).
- **m and x were tuned on the dev pilot** by the pre-registered rule in `analyze_26.py tune`: the full SAFE bar on 16 dev networks; plugM = smallest dev-SAFE m; cut = largest x such that every x' ≤ x is dev-SAFE.

  | hw | plugM m | cut x |
  |---|---|---|
  | ion2020 | 0.01 | 0.01 (infeasible) |
  | ionproj | 0.01 | 0.1 |
  | nv2 | 0.06 | 0.01 (infeasible) |
  | siv | 0.10 | 0.01 (infeasible) |

  "Infeasible" means no x was dev-SAFE, so the strictest value is used. A cut-off cannot see link-to-link differences.

**Block R** (shared noise at levels measured on real hardware).
- **Noise model:** a node common-mode shift of the parity probability, with link sd = rel·q̄.
  - rel ∈ {0.033 (ICFO median), 0.075 (ICFO max), 0.184 (USTC)}, from `recipe/dispersion_levels.py` on the pre-registered ICFO/USTC re-analyses.
  - Variants: `e` (homogeneous); `h` (lognormal node multipliers, E g² = 1); `a` (AR(1) persistence 0.9 across epochs, USTC level).
- **Arms:**
  - bg, kg, ag2t: undeclared;
  - kgR, ag2tR: declared fleet φ = one-sided 95% t upper bound over the independent epochs of a 30-epoch campaign on all links;
  - kgRp, ag2tRp: per-link one-sided 95% χ² upper bounds;
  - kgO, ag2tO: oracle per-link per-epoch φ.
- Declaring φ means deflating the counts by φ. That is a quasi-likelihood correction and approximate.

**Block O** (model optimism measured on real hardware).
- Controller and guard both add an undeclared offset Δ ∈ {0.02, 0.044} to every model fidelity. That is the USTC gap range: GLS 0.029 ± 0.044 (`recipe/ustc_margin.py`).
- The guard requires F_model − d ≥ τ, with:
  - d = 0 (`m0`);
  - recipe d = Δ̂ + 1.645·se, from M ∈ {4, 16, 64, 256} simulated tomography points with USTC precision (se = 0.0436·√(4/M));
  - oracle d = Δ (`orc`).
- Arm kg. Hardware: ion2020, ionproj.
- Theory: with the recipe, per-user risk ≤ α + β = 10%.

**Block S** (finite memory).
- Parallel service at 4× load and 50 km/hop. Q ∈ {2, 4, ∞} qubits per node: 1 at path ends, 2 at intermediate nodes, held for the whole service.
- Arms bg, kg, ag2t. Hardware: ion2020, nv2, siv.

**Sizes and seeds:** 339 cells × 32 = **10,848 tasks**. Seeds 19281–19284 (fresh). Dev pilot: 20281–20284.

## Safety bar (SAFE)
- Per-user risk: one-sided 95% cluster-bootstrap upper bound (over networks) ≤ **5%**.
- Delivered-pair risk r: upper bound ≤ **1%**.
- Block O recipe arms: per-user bound ≤ **10%** (α + β); r is reported but not part of the bar.
- A cell with no deliveries counts as SAFE, but it is listed as **vacuous** in every verdict.

## Dev pilot (disclosed)
- **Runs:** sha `a38182dc`, 3,896 tasks, 8–16 dev networks per cell, code `7e13e41a`. The full summary is in `pilot_summary_26.txt`. Dev data only.
- **Block U:** every guard arm had 0 bad pairs. The un-margined plug-in rule had 18% of ion2020 users bad (r 4.6%), showing a model-based guarantee is tautological. The correction costs at most about 0.5 points on ions and about 6 points for ag2t on SiV.
- **Block R:**
  - At the USTC level (iid), undeclared guards on ion2020 broke: per-user risk 1.7–5.8%, r 0.5–1.4%. These were the only non-SAFE iid cells.
  - Recipe and oracle arms gave at most 1 bad pair per cell.
  - **Persistent (AR) noise broke every model-based arm on ion2020, including the oracle.** This motivates model-free certification (Study 27).
  - SiV cost little at any level, because it has few counts per epoch.
- **Block O:** undeclared Δ gave 37–54% of ion2020 users bad. The recipe was safe except in networks where d < Δ, as expected at a 5% rate. M = 4 tomography points (USTC-like) left only 19% of oracle throughput on ion2020; M = 256 left 75%.
- **Block S:** memory limits barely bind at this load, except nv2 and siv at Q = 2 (latency up 25–50%).
- **After the pilot,** the tuned values were inserted, and R6 was added as a prediction informed by the pilot. **No other change.**

## Hypotheses (`analyze_26.py all`)

| | Tier | Test | Bar |
|---|---|---|---|
| **U1** | primary | Corrected bg, kg, ag2t | SAFE on every hw (12 cells) |
| U2 | secondary | Correction cost, legacy − corrected | ≤ 2 points for every arm and hw |
| U3 | secondary, prediction | Some dev-tuned baseline (plugM or cut) | NOT SAFE on some hw |
| U4 | secondary | ag2t − plugM, kg − plugM | Two-sided 90% CI, on hw where plugM is SAFE |
| U5 | descriptive | Plug-in rule without a margin | — |
| **R1** | primary | Oracle φ (kgO, ag2tO) | SAFE in every iid cell (48) |
| **R2** | primary | Recipe arms (kgR, ag2tR, kgRp, ag2tRp) | SAFE at ICFO levels (64 cells) |
| **R3** | primary | Recipe arms | SAFE at the USTC level, iid (32 cells) |
| R4 | secondary, prediction | Undeclared guards at the USTC level on ion hardware | NOT SAFE in at least one cell |
| R5 | secondary | Fleet recipe on SiV | Costs ≤ 3 points at every iid level |
| R6 | secondary, prediction (informed by the pilot) | AR persistent noise, ion2020 | Every arm NOT SAFE |
| R7 | descriptive | Declared vs true φ | — |
| **O1** | primary | Oracle margin | SAFE (4 cells) |
| **O2** | primary | Recipe margin | Per-user upper bound ≤ 10% (16 cells) |
| O2b | secondary | Recipe arms, in networks where d ≥ Δ | SAFE |
| O3 | secondary, prediction | Undeclared Δ = 0.044 on ion2020 | NOT SAFE |
| O4 | descriptive | Design curve over M | — |
| **S1** | primary | bg, kg, ag2t under finite memory | SAFE (27 cells) |
| S2 | descriptive | Throughput and latency by Q | — |

**Commitment.** No re-tuning; every outcome is reported. The code review (`REVIEW_26.md`) and its fixes are disclosed in ledger E106.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `study26.py` | `56436cc89a20325b` |
| `analyze_26.py` (locked) | `e44895fa5b49cc3e` |
| `tasks_s26.jsonl` (10,848) | `a693357da0b5880b` |
| study25 / study24 / study23 (unchanged) | `ecccd63c` / `7be8c292` / as in Study 23 |

**PSC:** 32 shards × 16 cores × 60 min (ceiling 512 SU). Expected about 60–90 SU.
