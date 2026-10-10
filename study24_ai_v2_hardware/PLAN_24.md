# Study 24 plan (10 Oct 2026): a better AI, more hardware, patterns it never saw, and the old failures

**Why.** Study 23 passed every test, but its AI was only tested on the correlation pattern it was trained on, and only on
ion hardware. Tanish chose option B (an out-of-distribution test) and asked for three more things:
- make the AI better;
- test it on SiV, NV and ion-future;
- check whether it fixes earlier failures.

## Block A (`study24.py`): AI v2 across 5 hardware types × 5 link patterns

**Hardware:** ion2020, ionproj, ion-future, NV (paths up to 2 links), SiV (thin data: C1 failed and C2 abstained).

**Patterns:**
- `ind` (no correlation);
- `field` (Study 23's pattern);
- three the AI never saw in training:
  - `short` (ℓ = 0.4);
  - `region` (a step between two areas);
  - `outlier` (8% of links unlike their neighbours).

**Arms:** `b`, `bg`, `fg`, **`kg`** (new control: known fleet law, no AI), `ag1` (Study 23 AI), **`lg`** (linear model, same machinery as v2), **`ag2`** (AI v2).

**AI v2:**
- learns from accumulated neighbour data;
- estimates the correlation itself;
- trained on many smooth patterns;
- predicts its own uncertainty;
- its guard prior is hedged 50/50 with default priors.

## Block B (`study24b.py`): the drift restart cost (G5)

**`gcarry`:** carry the previous cycle's estimate as a scale-mixture prior. Valid for any re-alignment jitter.
- Scenarios: D, Dj and Djb (four times G5's jitter).
- Prediction from Prop. 7 (below): little gain, because a prior cannot replace data.

## Faults (G6/G7): not addressed
A fault on one link is invisible in its neighbours' data, so no neighbour-based AI can detect it earlier. The G6/G7 alarms stay the answer.

## Proposition 7 (what any prior can buy)
For the mixture CS with prior π, the identity

  CS_t(π) = { θ : ℓ_t(θ̂) − ℓ_t(θ) < log(1/level) + O_t(π) },  with O_t(π) = ℓ_t(θ̂) − log ∫ e^{ℓ_t} dπ ≥ 0,

shows that every CS is a likelihood-ratio region whose radius is at least log(1/level).
- A prior acts **only** through the Occam term O_t.
- Its gain over a default prior π₀ is at most O_t(π₀).
- In the Gaussian approximation, O_t ≈ ½ log(1 + τ² I_t) + (θ̂ − m)²/(2(τ² + 1/I_t)).

**Predictions:**
1. Gains are large only where the default prior is very diffuse relative to the fleet (Beta(½,½) on SiV and NV).
2. Gains are small where the default is already the fleet law (`gexact`'s fleet prior, so `gcarry` buys little).
3. A wrong informed prior costs at most −log(its weight) in a hedged mixture.

## Steps
1. **Cloud:** train AI v2 and the linear model (5 hw); train AI v1 for the 3 new hw (ai_model.py unchanged); smoke tests; choose the v2 guard design on dev seeds.
2. **PSC dev pilot:** P24 (1,400 tasks) + P24B (192 tasks), about 10 SU.
3. Lock README_24 + analyze_24.py (tested on synthetic data) and tasks; then the PSC confirmatory run.
4. RESULTS_24, ledger, paper section.
