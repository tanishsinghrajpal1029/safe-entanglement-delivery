# Theory note v4 (11 Oct 2026): Propositions 8–10, and the novelty and contributions statement

This adds to the notes of 5–8 Oct (Props 1–7). It closes weak spots 4 and 5a, sets up 5b (tested in Study 25 Block D), and settles item 6 (novelty).

## Proposition 8 (fault exposure: a no-go plus an exact accounting)

**Setting.**
- A delivery rule decides at time t using only information available before t: the filtration F_t of calibration counts, waits and past outcomes, plus independent randomisation.
- At an **unannounced** time τ_f, independent of F_{τ_f}, a link's level drops from λ to λ′, with F(λ′) < τ along every path through it.
- The first post-fault calibration data become available at τ_f + Δ. Here Δ is the data latency: up to one epoch.

**Claim.**
1. On [τ_f, τ_f + Δ) the joint law of the rule's decisions is the same as in the no-fault world, because every decision is F_t-measurable and F_t does not yet depend on the fault.
2. Every pair delivered through the faulted link in that window is therefore bad, and the expected number is **E[bad per fault] = E[N_Δ]**, where N_Δ is the number of deliveries through that link in the window **had the fault not happened**.
3. No rule using only past data can do better: a per-pair guarantee within the window would require not delivering in the window at all.
4. **Exposure = (delivery rate through the link) × (detection latency) + (post-latency exposure until detection).**
   - The first term can be reduced only by delivering less, or by faster calibration (smaller Δ).
   - The second term is what the alarms of G6/G7 attack. They cut it by about 97% against no alarm (G6: 24 vs 793 late bad pairs). It is bounded by the detection delay, which is a k ≳ 2 ln(1/α) σ_w²/Δλ² epoch statistic (Prop. 5).

**Consequences for the paper:**
- A per-user guarantee under unannounced faults is impossible for any data-driven controller. This is a no-go, not a weakness of ours.
- What is achievable is the aggregate rate under a declared fault frequency (C2-R) plus a measured reduction of post-latency exposure (G6/G7). Both are reported.

*Proof sketch.* Decisions in the window are functions of F_t and independent randomness. The fault time is independent of F_{τ_f}, and the post-fault counts arrive only at τ_f + Δ. So the conditional law of the decision process on the window, given the fault, equals the unconditional one. Deliveries through the faulted link are bad by assumption. ∎

## Proposition 9 (re-alignment with a declared bound: the design rule)

**Setting.** As G5/Prop. 6″, with restart per cycle and α spending α_c = 6α/(π²c²)/L_max. Suppose the operator **declares** |θ_c − θ_{c−1}| ≤ B for every re-alignment.

**Claim.**
- Define comb_c = max(CS_c, comb_{c−1} − B), with comb_1 = CS_1, where CS_c is the lower end of cycle c's confidence sequence.
- If the declaration holds, then with probability ≥ 1 − Σ_c α_c = 1 − α/L_max per link, comb_c ≤ θ_c for all c and all times.
- The per-path guarantee of Prop. 6 therefore holds unchanged.

**Proof.**
1. On the event that every CS_c covers θ_c (probability ≥ 1 − α/L_max by Ville and the union over c): CS_1 ≤ θ_1.
2. If comb_{c−1} ≤ θ_{c−1}, then comb_{c−1} − B ≤ θ_{c−1} − B ≤ θ_c, and CS_c ≤ θ_c. So comb_c ≤ θ_c. ∎

**Cost, the design curve:**
- At the start of a cycle, gexact has no bound at all, while gb<B> keeps comb_{c−1} − B.
- So the cost of restarting falls from "lose the link until data accumulate" to "lose B of headroom".
- B → 0 recovers gpersist (assume nothing changes). B → ∞ recovers gexact.

**If the promise is broken** by δ (a jump of B + δ), the bound can be optimistic by up to δ, so the guarantee fails. This is exactly what gpersist (B = 0) showed in G5 and Study 24 under jitter.

**Pre-registered test:** Study 25 Block D.

## Proposition 10 (the AI prior adds no independence assumption beyond the guard's own data model)

**Setting.**
- Per-epoch counts with n_j ≥ 2 trials, conditionally independent across links and epochs given the link levels λ and any shared environment E (lasers, detectors, timing).
- The link's own parity probability is p(λ, E).

**Claim.** The following are equivalent:
- (a) the link's own counts are exactly binomial Bin(n_j, p(λ)) given λ, which is what every guard in this work assumes;
- (b) p does not depend on E.

Under (b), the link's own counts are independent of all other links' data given λ. So any prior built from other links' data, including the AI's, is a valid mixing prior.

**Proof.**
- If p varies with E, the own count is a non-degenerate mixture of binomials. For n ≥ 2 its variance strictly exceeds n p̄(1 − p̄), so it is not binomial.
- If p does not depend on E, the own count given (λ, E) does not depend on E. By conditional independence given (λ, E), it is independent of the other links' counts given λ. ∎

**Consequence:** shared noise that couples neighbours' data to a link's own data necessarily also makes the link's own counts over-dispersed. That breaks the baseline guard as well, not only the AI's.
- Study 25 Block T tests this directly, and measures a declared over-dispersion correction (counts deflated by φ). The correction is quasi-likelihood: approximate, not a theorem.
- Real data show such over-dispersion: ICFO in 7 of 11 runs, USTC ×3.6. So declared dispersion is a practical requirement, and the paper says so.

## Novelty and contributions (literature re-checked 10–11 Oct 2026)

**New since the 3 Oct novelty matrix:**
- **Optimal Calibration of Quantum Network Links** (arXiv 2606.18167, Jun 2026): schedules calibration vs activation under a deterministic fidelity requirement. No statistical guarantee on delivered pairs.
- **QPing** (arXiv 2508.03806): a Bayesian sequential "is there usable entanglement" test. It explicitly leaves rigorous error control to future work and does not bound delivered-pair or per-user risk.
- **Interval estimation of entangled-state fidelity** (arXiv 2409.19282) and a tailored fidelity-estimation-plus-purification method (2602.18011): per-estimate confidence intervals. Prop. 1 shows such per-decision guarantees do not bound delivered-pair risk.
- **RL routing** (RELiQ, qRL, DRL routing): throughput-oriented, with no delivery guarantee.

**Contributions** (each is a claim the evidence supports):
1. **A no-go plus a fix for delivered-pair risk.** Fixed-margin rules cannot hold a target rate of below-threshold deliveries (Prop. 1). A label-free calibrated controller holds it on average (Prop. 2) across the hardware tested, with stated boundaries: thin data, model error, faults.
2. **An anytime-valid per-user guarantee.** A per-path guard (Prop. 6, with drift variants 6′, 6″) guarantees P(a user ever receives a below-threshold pair) ≤ α using only routine parity data. It held at 0 bad pairs in tens of millions of guarded deliveries across five hardware types.
3. **Learning without losing the guarantee.** Any learned prior, AI or linear, enters the guard safely, and helps exactly where Prop. 7's Occam term predicts.
   - It rescues thin-data hardware: SiV from about 4% to about 30% of oracle at 0 bad pairs.
   - The AI's own value beyond informed priors is measured separately.
   - Prop. 10 shows it adds no independence assumption.
4. **Limits stated as theorems and design rules:**
   - faults (Prop. 8, a no-go plus the measured alarm reduction);
   - re-alignment (Prop. 9, the declared-bound design curve);
   - model error (Study 25 Block M map, with the margin a real device needs; USTC: about 0.04);
   - over-dispersion (Prop. 10 plus Block T).
5. **Real-data checks.** Innsbruck (Stage 1 reproduced), ICFO (claims reproduced; real drift; the anytime bound held in 10 of 11 runs) and USTC (memory model predicts real decay within error but 2–4 points optimistic; real drift).
6. **Method.** Every study pre-registered with locked analyses; failures kept. Public repository with a Zenodo DOI and an independent timestamp audit (22 of 22 PSC pre-registrations predate their runs).

**Not claimed:**
- not the first fidelity-aware routing, purification planning or RL routing;
- no live-hardware deployment.
