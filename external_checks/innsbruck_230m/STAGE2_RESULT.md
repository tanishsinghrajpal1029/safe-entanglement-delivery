# Innsbruck Stage 2 result (7 Oct 2026): gate G3 FAILS on event count; Step 2 NOT run, as pre-registered

Pre-registration: PREREG_INNSBRUCK_STAGE2.md (sha 00356d058c4e233c); locked analysis stage2/analyze_stage2.py (dd68ff9ec7de209b), NOT executed.
Decoder (subagent, blinded to within-run time structure): stage2/decode/, choices stage2/CHOICES.md; outputs events.csv (bea45cf8161a7da8), runs.csv (f5f6e20dabdf4aca), gate.json (4edb59ca866a7829).

| Gate item | Ours | Paper (PRL 130, 050803) | Tolerance | |
|---|---|---|---|---|
| Heralded ion-ion events, 1 µs | **581** (ψ+ 324, ψ− 257) | 491 | ±10% (442–540) | **FAIL** (+18%) |
| F+ (1 µs) | 0.900 ± 0.038 | 0.882 (+0.023/−0.060) | ±0.06 | pass |
| F− (1 µs) | 0.837 ± 0.058 | 0.822 (+0.025/−0.064) | ±0.06 | pass |
| Attempts (channel-0 tags after first cycle start) | 13,656,928 | 13,656,928 | — | exact match |
| 17.5 µs window (supporting) | 4,490 events; F+ 0.597, F− 0.585 | 3,960; 0.587, 0.580 | — | count +13% |

- Synchronisation is strongly supported without outcomes (Node A per-cycle attempt counts match the BSM station for every cycle of every validated step; Node B step ends match to 3.3 ms rms) and confirmed by outcomes (ZZ correlations −0.86/−0.78/+0.85 only at the chosen alignment).
- The excess is not explained by multi-click rules, ±0.5 µs window shifts (573–586), the time reference, or the last-attempt rule (all 581 are last-attempt coincidences; checked after the fail, the code confirms readout follows the herald; no events removed, so the one allowed fix was not used).
- Unadopted observation: dropping one ψ+ detector pair (4,5) would give 518 — no justification in data or paper, so NOT used.
- **Per the pre-registration, Step 2 (H-a, H-b, H-c, H-d) was not run.** We report: "ion-ion decoding reproduces the paper's attempt count exactly and both fidelities, but finds 18% more heralds than published; the cause is unresolved."
- Possible resolutions (need a decision): ask the authors how the 491 events were selected; or run Step 2 as an explicitly labelled protocol deviation (exploratory).
