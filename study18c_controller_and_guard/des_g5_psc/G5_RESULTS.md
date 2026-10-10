# Study 18C G5 results: a cheaper drift-valid guard (confirmatory, 9 Oct 2026)

**Pre-registration:** `README_G5.md` (E77).

**Provenance:**
- 1,024 of 1,024 tasks, 64 networks per group.
- PSC runs.csv sha `c992739821a87fb2`, matching the copy on the Mac.
- Module `6a3760751656f798`, tasks `084506ae9237a184` and analyzer `a28effcdded14d6e` are unchanged from pre-registration.

## Verdicts

| | Question | Result |
|---|---|---|
| **H1** (primary) | Is `gexact` safe under D and Dj, both hw? | **PASS.** 0 bad pairs in 1,183,827 delivered; 0 of 57,408 paths bad |
| **H2** (primary) | Does `gexact` keep more throughput than `gdrift` in all 4 cells? | **PASS.** Gain +0.038 / +0.046 (ion2020 D / Dj) and +0.129 / +0.126 (ionproj D / Dj); every 95% lower bound > 0 |
| H3 (secondary) | Under D, is `gpersist` safe and cheaper still? | **PASS.** 0 bad; +0.083 (ion2020) and +0.140 (ionproj) over `gexact` |
| H4 (prediction) | Does `gpersist` break when re-alignment jitters (Dj)? | **CONFIRMED.** 43 bad (ion2020, 18 of 64 networks) and 211 bad (ionproj, 54 of 64 networks). r = 0.018% and 0.048%; 0.59% of delivering paths bad |

## Throughput (fraction of oracle) and cost relative to no guard

| Cell | cal (no guard) | gdrift (G4) | gexact (new, valid) | gpersist (needs exact re-alignment) |
|---|---|---|---|---|
| ion2020 D | 0.854 | 0.695 (−19%) | **0.733 (−14%)** | 0.816 (−4%) |
| ion2020 Dj | 0.860 | 0.691 (−20%) | **0.737 (−14%)** | 0.813, unsafe |
| ionproj D | 0.950 | 0.627 (−34%) | **0.756 (−20%)** | 0.896 (−6%) |
| ionproj Dj | 0.953 | 0.641 (−33%) | **0.767 (−20%)** | 0.895, unsafe |

- Without a guard, r was 1.21–1.36% in every cell, and 12–28% of paths delivered at least one bad pair. That matches G4: the grid simulator lacks C2's drift-aware likelihood.
- **`gexact` closes 24–27% of the gap to no guard on ion2020 and 40% on ionproj.**

## Reading

1. **The tighter bound works and keeps the guarantee.** Replacing the worst-case drift margin with the exact drift likelihood (Prop. 6″) cut the drift cost from 19–34% to 14–20%, with zero bad pairs.
2. **Most of the remaining cost is the restart.** The gap between `gexact` and `gpersist` is 8 points of oracle throughput (ion2020) and 14 points (ionproj). It comes from discarding a link's history at every re-alignment. `gpersist` itself still costs 4–6% against no guard, which is the price of finite-sample confidence.
3. **Re-using that information is cheap but needs an assumption.** `gpersist` recovers most of the remaining cost, but only if each re-alignment returns the link to exactly the same level.
4. **With a modest re-alignment jitter, that assumption fails as predicted.** The failure is small: r ≤ 0.05%, and 0.6% of paths are bad, under the 5% per-path budget. But it is a real loss of the guarantee, not noise, since it appeared in 72 of 128 networks.
5. Larger jitter was not tested, so we do not claim `gpersist` is "nearly safe" in general.
6. **Next step for a paper:** a principled middle option, "persist with a declared jitter bound" (a robust set as in G4). That would be another pre-registered run. It is not needed for the current claim.

## Prop. 6″ (for the theory note)

**Setup.**
- θ is the link level at its last re-alignment.
- The parity probability of epoch j is p_j(θ) = (1 + r(θ − g·φ̄_j))/2, with g and the re-alignment times known.
- M_t(θ) = ∫ Π_j Bin(k_j | n_j, p_j(θ′)) π(dθ′) / Π_j Bin(k_j | n_j, p_j(θ)) is a nonnegative martingale with mean 1 under the true θ, for any fixed π.

**Construction.**
- CS = {θ : M_t(θ) < Lmax/α_c} covers θ at all times (Ville's inequality).
- λ_now ≥ θ_lo − g·(t − t_reset), with no extra margin.
- Restart at every re-alignment and spend α as 6α/(π²c²) per cycle.

**Guarantee.** Per path, P(ever delivering a bad pair) ≤ α.

**Comparison with Prop. 6′.** 6′ uses stochastic dominance, so it is coarser but needs only an upper bound on the drift. 6″ needs the drift model to be exact. That trade-off should be stated: if g is only bounded rather than known, use 6′ or a worst case over g.
