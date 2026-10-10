# Hardware-parameter provenance: demonstrated performance vs project configuration

Prepared 3 October 2026. Numbers are quoted from primary papers (abstracts or summaries where marked). This is the first pass; supplementary-table values (readout fidelity, gate fidelity, measured drift) still need to be pulled from full texts before anything is frozen.

## Demonstrated remote entanglement (elementary links)

| Platform | Paper | Link fidelity | Heralded rate | Memory | Notes |
|---|---|---|---|---|---|
| Trapped ions (Sr⁺, Oxford) | Stephenson et al., PRL 124, 110501 (2020), arXiv:1911.10841 (abstract) | F = 0.940(5) | 182 s⁻¹ | — | Success probability 2.18×10⁻⁴ per attempt |
| NV centres (Delft, 3 nodes) | Pompili et al., Science 372, 259 (2021), arXiv:2102.04471 (summary) | 0.820(5) and 0.808(5) | 9 Hz and 7 Hz | ¹³C memory decays over ≈1,800 entanglement attempts | Entanglement swapping gives F = 0.551(13); a swap about every 40 s |
| SiV in nanophotonic cavities (Harvard/AWS) | Knaut et al., Nature 629, 573 (2024), arXiv:2310.01316 (full-text summary) | Electron–electron 0.86(3) (20 m); nuclear–nuclear 0.69(7) over a 35 km deployed loop, with error detection | About 1 Hz (electron); about 6 mHz (nuclear) | ²⁹Si nuclear storage > 2 s; entanglement kept up to 1 s with DD | — |
| Trapped ions, distributed QC (Oxford) | Main et al., Nature (2025) (abstract) | Not in abstract | — | — | Teleported CZ fidelity 86% |
| Drift (trapped-ion fiber link) | Data used in arXiv:2606.18167 | Link fidelity drifts from ≈1 to ≈0.5 over ≈10⁴ s | — | — | ≈2-minute recalibration |

## Project configuration (Studies 08–17; `configs/grid_30x30.json`)

| Parameter | Value | Label in config |
|---|---|---|
| Link depolarization | 0.001–0.005 (link F ≈ 0.996–0.999) | "aspirational sensitivity scenario; not calibrated to deployed hardware" |
| BSM | Success 1.0, depolarization 0 | ideal |
| Source and detector efficiency | 0.95 each | — |
| Memory | T2_DD = 24 / 80 / 192 ms; DD pulse error 10⁻⁶ | — |
| Path length (Study 17 final, 30×30) | Median **20 hops** (10th–90th percentile: 8–34; max 53) | — |
| Single-pair true fidelity | Median 0.923 | — |

## Gap and consequences

1. **Per-link infidelity.** The config's link infidelity, 0.75·p = 0.00075–0.00375, is **16–80× smaller** than the best demonstrated remote link (1 − F ≈ 0.06 for ions) and 48–240× smaller than NV (≈ 0.18).
2. **Path length.** With demonstrated link fidelities and *no* storage noise, a 20-hop Bell-diagonal chain has F ≈ ¼ + ¾·((4F_link − 1)/3)²⁰, which is about 0.39 at F_link = 0.94. Delivering ≥ 0.9 over 20 hops requires F_link ≳ 0.995, or heavy purification.
3. **Rates.** The config's 0.95 × 0.95 efficiencies make heralding nearly deterministic per attempt, against 2×10⁻⁴ per attempt demonstrated. Storage times, and hence memory-decoherence effects, are mis-scaled accordingly.
4. **Headline results.** All headline results from Studies 08–17 come from a regime one to two orders of magnitude beyond demonstrated hardware. They remain valid *as simulation results in that regime*, but **any PRX claim must either**:
   - **(a)** restrict to a near-term regime anchored to the table above (small networks, ≤ 3–4 hops, ion-like links, F_th chosen accordingly, purification essential); **or**
   - **(b)** present the aspirational regime explicitly as a projection, with a sensitivity sweep connecting it to the near-term regime.

## Open items

- Readout (SPAM) error per platform, needed for the calibration-cost law (E5). Ions are typically ≥ 99.9%; NV single-shot readout is typically 0.9–0.98; SiV is high. **To be confirmed from primary sources.**
- Memory T1/T2 *during network activity* for NV (Pompili et al. and Hermans et al. 2022) and ions.
- BSM success and fidelity for photonic heralding schemes (≤ 50% for linear-optics BSM).
