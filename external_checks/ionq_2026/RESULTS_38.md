# Study 38 results: the certificate on IonQ's kHz ion–SiV link (public data)

Data: Hartung et al., arXiv 2610.10705; github.com/ionq-publications/khz-heterogeneous-entanglement @ 8a08f695fca8 (Apache-2.0, © IonQ, Inc.).

## Timeline (evidence)
| Event | Time (PST) |
|---|---|
| Pre-registration commit a4fe90b (`external_checks/ionq_2026/`), pushed | 2026-11-01 11:21:34 |
| Stage 1 run | 11:21:50 |
| Stage 2 run | 11:22:31 |
Frozen hashes `OK`; IonQ repo at the registered commit, unmodified; test switches off. Outputs (sha256/16): stage 1 `analysis_38.txt` 56ba59c68884f5bd; stage 2 `analysis_38.txt` 4533b3d247ed268c; `stage1_38.json` 8ccf15eda1e3d191.

## Stage 1: gates (all PASS)
- G0: our parser = the authors' outcome counts in all 7 runs × 9 settings; our F = their Fig. 2 formula. No missing outcomes; 3,000 XX/YY/ZZ heralds per run.
- G1: MLE F = 0.8794 ± 0.0073 (published 0.879(7), z = 0.06); rate 1.032 kHz (published 1.032(11), z = 0.02).

## Stage 2
**H2 drift within a run (prediction: not detected) — HELD.** 28 tests, min p × 28 = 1. Smallest p = 0.043 (run 69977 XX error), as expected by chance. Each run is about 9 s; slow drift is out of scope.

**H3 certificate validity (prediction: not falsified) — HELD.** 0 violating draws in all 21 cells (7 runs × p = 0.1, 0.2, 0.5; 1,000 draws each).

**H5 usefulness predicted in advance — HELD.** Run 64563, p = 0.2: median certificate **0.818**, predicted 0.817 [0.788, 0.842]. Secondary: p = 0.1 0.790 (predicted 0.789); p = 0.5 0.836 (predicted 0.834). The design curve (S37-D) predicted the real median to within 0.002 in all three.

**Headline:** first real-data certificate at the SiV threshold for a link with a solid-state (SiV) node. (Oxford's ion–ion link, Study 36, certified 0.917 but needed about 945,000 kept pairs.) At p = 0.2 the certified fidelity of the delivered pairs exceeds 0.8 in 82 % of draws (100 % at p = 0.5), from 3,000 Bell-basis heralds, about 2.9 s of link time at 1.03 kHz.

## Descriptives (D1): rate–fidelity–certificate trade-off
| Run | Setting | Rate (kHz) | F (linear) | Median certificate, p = 0.2 | > 0.8 |
|---|---|---|---|---|---|
| 64563 | Fig. 1 | 1.032 | 0.8805 (MLE 0.8794) | 0.818 | 82 % |
| 69967 | XY8-1 | 0.718 | 0.8730 | 0.808 | 68 % |
| 69963 | XY8-2 | 1.037 | 0.8710 | 0.806 | 63 % |
| 69977 | XY8-3 | 1.161 | 0.8565 | 0.789 | 28 % |
| 69969 | XY8-4 | 1.205 | 0.8530 | 0.784 | 24 % |
| 69971 | XY8-8 | 1.310 | 0.8105 | 0.734 | 0 % |
| 69974 | XY8-16 | 1.353 | 0.7415 | 0.654 | 0 % |
- Per-basis errors (Fig. 1): e_XX 0.101, e_YY 0.077, e_ZZ 0.061. Longer XY8 blocks raise XX/YY errors (dephasing), not ZZ.
- Certificate − F at N = 3,000, p = 0.2: −0.06 to −0.09.

## Limits (registered)
Settings blocked, not interleaved (anytime path in time order not tested); one device pair, one day; U is conservative (H3 power limited); the six cross settings unused.

## Meaning for the paper (draft)
1. Another platform's published numbers reproduced exactly from public data.
2. The certificate's usefulness is predictable in advance from fidelity and sample size alone: the design curve called the real median within 0.002.
3. At kHz rates the guarantee reaches the SiV threshold in about 3 s of data (design curve S37-D: a few hundred pairs would not be enough).
4. Certified fidelity vs rate gives an operating point: the best certified run is not the fastest one.
