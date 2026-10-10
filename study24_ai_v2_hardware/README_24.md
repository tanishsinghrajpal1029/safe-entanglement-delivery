# Study 24: a better AI under the guard, five hardware types, patterns the AI never saw, and the drift restart cost (pre-registered 10 Oct 2026, before the confirmatory run)

**Plan:** `PLAN_24.md`. **Set-up and dev runs:** ledger E87. **PSC dev pilot:** E88 (below).

## Block A (`study24.py`)

**Network.** The G-series 5 × 5 grid with greedy best-path routing, exact physics and stationary links.
- Hardware (`hw24.py`): ion2020, ionproj, ionfut (L ≤ 3), nv2 (NV, L ≤ 2) and siv (SiV, L ≤ 2), each with calibration fraction 0.3.

**Link-quality patterns** (`corr_net24.py`; each keeps the fleet's mean and spread):
- `ind`;
- `field` (ℓ = 1.5, ρ = 0.7, Study 23's pattern);
- three that AI v2 **never saw in training**:
  - `short` (ℓ = 0.4);
  - `region` (a step between two areas);
  - `outlier` (8% of links shifted ± 2.5 SD, unlike their neighbours).

**Arms** (all greedy routing):

| Arm | Belief | Guard |
|---|---|---|
| `b` | empirical-Bayes fleet | none |
| `bg` | EB fleet | Beta(½,½) mixture (today's guarded controller) |
| `fg` | EB fleet | fleet-Gaussian mixture |
| **`kg`** | **known fleet law** (Gaussian with the true fleet spread) | fleet-Gaussian mixture. **Informed priors everywhere, no AI.** |
| `ag1` | AI v1 (Study 23; latest window; told ρ = 0.7) | AI v1 prior, frozen at warm-up |
| **`lg`** | linear model on AI v2's features | hedged prior (as `ag2`) |
| **`ag2`** | **AI v2** | **hedged prior** |

**AI v2** (`ai_model24.py`; trained in the cloud, weights `ai2_<hw>.npz`, hashes in E87):
- predicts a link's quality and its own uncertainty from **other links' accumulated** calibration counts;
- two leave-one-out network statistics let it estimate the correlation itself;
- trained on smooth fields only (ℓ ∈ {0.75, 1, 1.5, 2, 3}, ρ ~ U(0, 0.9)).

**Hedged guard** (Prop. 6 with an informative prior):
- The prior is π = 0.5 N(μ_AI, σ_AI) + 0.25 fleet Gaussian + 0.25 Jeffreys, frozen at the end of warm-up from other links' data only.
- Given the link qualities, other links' counts are independent of this link's counts, so the mixture is a test martingale. Hence **P(a path ever delivers a bad pair) ≤ α = 5% whatever the AI predicts.**
- A wrong prediction costs at most ln 2 in the threshold.
- Design chosen on dev runs (E87): J = 1, weight 0.5.

**Latency** (added at the advisor's request before this run; recorded only, with no random draws; checked to leave deliveries identical on 4 dev tasks). Per delivered request:
- end-to-end latency = queue wait + service time (all generation attempts, including rejected ones);
- attempts used;
- memory hold time;
- the oracle's service time as the reference;
- pooled 50/95/99th percentiles from per-network histograms.

Classical signalling delay is not modelled.

**Design:** 5 hw × 5 patterns × 7 arms × 64 networks = **11,200 tasks**. Networks are paired across arms. Fresh seeds 19241–19244.

## Block B (`study24b.py`): carrying information across re-alignments

**`gcarry`:** G5's `gexact` (restart per cycle, α spending), but from cycle 2 on, the mixing prior is
0.25 N(θ_prev, 0.002) + 0.25 N(θ_prev, 0.006) + 0.25 N(θ_prev, 0.02) + 0.25 fleet prior,
where θ_prev is the previous cycle's estimate.
- It is valid for any re-alignment jitter, because the previous cycle's counts are independent of the current cycle's given the levels.

**Scenarios:** D (exact re-alignment), Dj (jitter 0.005, as G5) and Djb (jitter 0.02).
**Controllers:** `cal`, `gexact`, `gpersist`, `gcarry`.
**Design:** 2 hw × 3 × 4 × 64 = **1,536 tasks**. Fresh seeds 19251–19254.

## Proposition 7 (stated before the run; why Block B should buy little)
For any mixing prior π, the mixture CS is exactly the likelihood-ratio region

  { θ : ℓ_t(θ̂) − ℓ_t(θ) < log(1/level) + O_t(π) },  O_t(π) = ℓ_t(θ̂) − log ∫ e^{ℓ_t} dπ ≥ 0.

- A prior acts **only** through the Occam term O_t, and its gain over a default π₀ is at most O_t(π₀).
- Gains are large where the default prior is diffuse relative to the true spread (Beta(½,½) on thin hardware).
- Gains are small where the default is already the fleet law (`gexact`).

## PSC dev pilot (disclosed; seeds 20241–20244 / 20251–20254; 8 networks per cell)

**Block A** (runs.csv sha 57ceeaf7; 1,400 tasks):
- **0 bad pairs in every guarded arm.** Without a guard, `b` had 173–659 bad pairs per ion cell and 0–6 on NV and SiV.

| Comparison | Pilot (points) |
|---|---|
| `ag2 − bg` on NV + SiV (10 cells) | **+21.7** |
| `ag2 − kg` on NV + SiV, correlated patterns | **+14.0** (cells +23.4, +19.3, +31.8, +9.3, +11.0, −0.5, +6.6, +11.4) |
| `ag2 − kg` on unseen patterns, 5 hw | +5.3 (ions ≈ 0; NV, SiV large) |
| `ag2 − kg` on independent links | +0.3 (−0.4 to +1.8) |
| `ag2 − ag1` (all cells) | **−0.09** (v2 is not better than v1 overall) |
| `ag2 − lg` (correlated) | **+0.06** (the neural net adds nothing over linear) |
| `kg − fg` on NV + SiV (known-law belief) | +9.3 |
| `fg − bg` (all cells) | +1.2 |
| On ions: `ag2 − bg` / `ag2 − kg` | +1.6 / +0.2 |

**Block B** (runs.csv sha 6f36b42b; 192 tasks):
- `gcarry − gexact` per cell: +0.8, −0.4, −0.3, +0.5, +0.2, +0.2.
- `gcarry` and `gexact` had 0 bad pairs.
- `gpersist`: 0 bad in D; 12 and 23 in Dj; 122 and 463 in Djb.

**What the pilot says, stated before the run:**
- on thin hardware, informed priors rescue throughput. About 9 points come from knowing the fleet law and about 14 more from the AI's correlation learning.
- on ion hardware the AI adds almost nothing;
- v2 does not beat v1 overall;
- a linear model does as well as the neural net;
- carrying a link's own history across re-alignment buys ~0, as Prop. 7 predicts.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `study24.py` | `7be8c2925e66b10b` |
| `study24b.py` | `5d24bef6d4408494` |
| `analyze_24.py` (locked; tested on synthetic data) | `f8ef96d648b6bda9` |
| `tasks_s24.jsonl` (11,200) | `ea8f322eb4aecfaf` |
| `tasks_s24b.jsonl` (1,536) | `619f6add40d74825` |
| `hw24.py` | `27d2df220d6c4285` |
| `corr_net24.py` | `97104d05b747ca4a` |
| `ai_model24.py` | `02a9220f4f1e35dc` |
| `corr_net.py` / `study23.py` (unchanged from Study 23) | `3f6df6215f05861c` / `10f75e0ec5711e85` |

Weights and checks are as in E87.

## Hypotheses

Gains are the mean over cells of the per-cell ratio-of-sums difference in fraction of oracle, with a paired network bootstrap. Safety bars are as in Studies 23 and G.

| | Question | Bar |
|---|---|---|
| **H1** (primary) | Is every guarded arm safe? | `bg, fg, kg, ag1, lg, ag2` in all 25 cells: r ≤ 1%, upper bound ≤ 1%, bad paths ≤ 5% |
| **H2** (primary) | Is thin hardware rescued? | `ag2 − bg` over NV + SiV (10 cells) ≥ 10 points **and** 95% lower bound > 0 |
| **H3** (primary) | Does the AI add value beyond informed priors? | `ag2 − kg`, NV + SiV, correlated patterns (8 cells): lower bound > 0 |
| **H4** (primary) | Does it hold on patterns never seen in training? | `ag2 − kg`, short/region/outlier × 5 hw (15 cells): lower bound > 0 |
| H5 (secondary) | Does it do no harm on independent links? | `ag2 − kg`, ind × 5 hw: lower bound > −1 point |
| H6 (secondary) | Is v2 better than v1? | `ag2 − ag1`, 25 cells: lower bound > 0. **Pilot suggests FAIL.** |
| H7 (secondary) | Is the neural net needed? | `ag2 − lg`, correlated × 5 hw: lower bound > 0. **Pilot suggests FAIL.** |
| H8 (descriptive) | | Per-hw gains for `fg−bg`, `kg−fg`, `ag2−kg`, `ag2−bg`, `ag1−kg`, `lg−kg`; risk of `b`; **latency table** (hw × arm) |
| **B1** (primary) | Is `gcarry` safe? | All 6 cells: r ≤ 1%, upper bound ≤ 1%, bad paths ≤ 5% |
| **B2** (primary, Prop. 7) | Does carrying information buy little? | `gcarry − gexact`, 90% CI inside [−2, +2] |
| B3 (secondary) | Does `gpersist` fail when re-alignment jitters? | bad > 0 in all 4 Dj/Djb cells |
| B4 (descriptive) | | `gexact` safety and cost vs `cal` |

**Commitment.** No re-tuning after the run. Every outcome is reported, including H6, H7 and B2, which the pilot predicts will go against "more AI is better".

**PSC.**
- Block A: 32 shards × 16 cores × 30 min (ceiling 256 SU).
- Block B: 8 × 16 × 30 min (ceiling 64 SU).
- Expected about 70–90 SU in total.
