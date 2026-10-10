# Novelty map and candidate contribution (3 October 2026)

This is a working hypothesis, not a claim. Prior work is described as its authors present it; where only an abstract or summary was read, that is stated. If our idea overlaps, **we change our question, not their description.**

## PRX Quantum bar (journals.aps.org/prxquantum/about)

A paper must be exceptional in at least one of four ways: an *advance*, a *connection*, a *capability*, or an *insight*. A better heuristic on a simulated benchmark is not enough by itself. A network-control simulation study reaches this bar only if it shows something general and consequential, such as a regime boundary, a scaling law, or a capability others can use.

## What is already done (do not claim)

| Topic | Prior work | What we read |
|---|---|---|
| Distributed fidelity-threshold routing with purification, reservation and concurrency | Q-GUARD, arXiv 2605.00246 (Werner model, BBPSSW, expected goodput, k-hop link state) | Full text, earlier session; summary rechecked |
| Contention-aware asynchronous routing using memory occupancy and BSM depth | RADAR-Q, arXiv 2603.27570 | Abstract |
| Local-information GNN/RL routing that generalizes across topologies | RELiQ, arXiv 2511.22321 | Full text, earlier session |
| Purify-or-not under input asymmetry and decoherence | DeltaPurify, arXiv 2605.08771 | Full text, earlier session |
| Adaptive purification depth and protocol selection for goodput above a threshold | APC, arXiv 2601.18351 | Abstract |
| Joint routing and purification optimization by dynamic programming | arXiv 2605.23331 | Abstract |
| Routing with uncertain link fidelities; competing requests | Lavi et al., arXiv 2609.29752 | Sections 4–5, earlier session |
| Calibration as link downtime under exponential drift; closed-form optimal schedules (QLO theorem); "grey-box" routing from end-to-end estimates | Kumar thesis, arXiv 2606.22316; arXiv 2606.18167 | Full-text summary |
| Cost-adaptive fidelity estimation (network benchmarking) for **best-link identification**, with sample-cost bounds | LINKSELFIE (Liu, Li, Wang, Lui) | Paper summary |
| Identifying internal link Pauli channels from end-to-end measurements, including SPAM, on general topologies | Quantum network tomography, arXiv 2511.01074 and 2405.11396 | Abstract |
| Control-plane latency as a coherence cost; centralized vs local decisions | Dey & Marchetti, arXiv 2609.23047 | Summary |
| Fidelity-age-aware swap and purification scheduling under memory limits | Ercetin & Gedik, arXiv 2602.09562 | Summary |

**Consequences.**
- Our Study 17 adaptive-delivery result is a careful, verified simulation finding. It is not novel as a mechanism.
- The candidate "Werner models mislead decisions under T1" is falsified at F_th ≈ 0.9 (ledger E3).
- "Calibrate links adaptively" is partly taken by LINKSELFIE and the tomography papers.

## The gap that remains (narrowest version we could defend)

None of the works above connects three things:

1. the **number of consumed calibration pairs** (finite shots, readout error, drift);
2. the resulting **parameter uncertainty**, propagated through **time-dependent storage, swapping and purification**;
3. the **below-threshold delivery risk and net qualified goodput** of a network that must decide, pair by pair, whether to deliver, retry or purify.

Q-GUARD, APC and Fidelity-Age assume fidelity is known. LINKSELFIE and the tomography papers estimate fidelity but make no delivery decisions under memory decay. Kumar's work models calibration as time rather than as a statistical input to decisions.

## Candidate claim (hypothesis; falsifiable)

**H-cal (insight): fidelity-qualified entanglement delivery is calibration-limited.**

To keep P(F < F_th | delivered) ≤ α, the safety margin must cover the uncertainty of the predicted fidelity. That uncertainty grows with path length, storage time and parameter error, and parameter error shrinks only as 1/√(calibration pairs). Drift forces recalibration. Combining these gives a predicted calibration-overhead fraction:

overhead ≈ calibration pairs per drift period ÷ (calibration pairs + user pairs delivered per drift period).

The claim is that this predicts a **regime boundary**: beyond a critical path length, threshold margin, or drift-rate × delivery-rate product, verified delivery at risk α is impossible without one of the following.

**H-mech (capability; compared against strong baselines):** a decision-aware calibration allocator. It spends calibration pairs only where parameter uncertainty can flip delivery decisions near F_th, given the actual traffic and storage times. The prediction is that it moves the boundary by a measurable factor at equal risk, compared with:
- uniform per-edge calibration;
- tier-pooled calibration;
- a LINKSELFIE-inspired best-arm allocator;
- tomography-style end-to-end estimation;

with every arm charged for the pairs it consumes.

**What would falsify it:**
1. Overhead stays small (say < 5%) across realistic drift and rate regimes. Then no bottleneck exists and the insight is empty.
2. The analytic overhead or risk predictions miss NetSquid outcomes beyond pre-stated tolerances.
3. The decision-aware allocator does not beat the strongest uniform or tier-pooled baseline at equal risk on fresh topologies.

**Early evidence that motivates it (not proof):**
- Study 17's cal20 synthetic error was safe at m = 0.02, while cal30 failed (6.25% bad).
- The one-link finite-shot fit (2,250 pairs) produced parameter errors of roughly 10–20%, comparable to cal10–cal20.
- Charged per edge, that is 3.9 million pairs on a 30×30 grid, against about 2×10³ user pairs per 1,000-request run. Whether this is negligible or dominant depends entirely on drift time × delivery rate.

That dependence is exactly what H-cal must quantify.

## Honest prior for venue

H-cal plus H-mech is a credible, novel *systems-physics* paper. Whether it meets PRX Quantum's "exceptional insight" bar depends on two things:
- whether the regime boundary is sharp and general (it must hold across topology families and hardware platforms, with parameters taken from primary experiments);
- whether it changes how the field should design verified delivery.

If the boundary is soft or platform-specific, the honest venues are PR Applied, IEEE TQE or IEEE QCE.
