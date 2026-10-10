# Study 18C G7 results: a GLR alarm for small faults (confirmatory, 10 Oct 2026)

**Pre-registration:** `README_G7.md` (E82).

**Provenance:**
- 1,024 of 1,024 tasks.
- runs.csv sha `5157931a11f3410f` on PSC and on the Mac.
- The module (`33bf5888`) and analyzer (`2cdb7a2b`) are unchanged.

## Verdicts

| | Question | Result |
|---|---|---|
| **H1** (primary) | Does the GLR alarm keep late post-fault bad low, and no higher than `galarm`'s? | **FAIL (one clause).** The late rate is within the bar on both hw: 0.068% (ion2020) and 0.065% (ionproj), against ≤ 0.1%. But on ion2020, `gglr` had **8** late bad pairs against `galarm`'s **4**, so "≤ galarm" fails there. ionproj passes (20 vs 24). |
| **H2** (primary) | Does it detect 2-SD faults, the G6 failure? | **PASS.** 252 of 255 detected (98.8%), against `galarm` 218 of 255 (85%) |
| H3 (secondary) | Are false alarms rare? | **PASS.** 6 false alarms in 256 networks |
| H4 (secondary) | Is it safe overall? | **PASS.** r ≤ 0.053%, upper bound ≤ 0.070% |
| H5 (secondary) | Is it cheap? | **PASS.** −0.3 to +0.05 points of throughput against `galarm` |

## Detection (% of faults) and mean delay (epochs after the fault epoch)

| Faults | galarm | **gglr** | gglr_s |
|---|---|---|---|
| 2-SD, ion2020 | 98.5%, 0.4 | **100%, 0.2** | 100%, 0.1 |
| 2-SD, ionproj | 71.3%, 1.7 | **97.5%, 1.3** | 99.2%, 0.6 |
| 1-SD, ion2020 | 30.5%, 3.7 | **83.7%, 2.6** | 96.5%, 1.5 |
| 1-SD, ionproj | 7.4%, 3.6 | **41.3%, 4.0** | 65.3%, 3.1 |

**False alarms in 256 networks:** `galarm` 5, `gglr` 6, `gglr_s` 183 (about 0.7 per network).

## Late post-fault bad pairs

| Group | cal | galarm | gglr | gglr_s |
|---|---|---|---|---|
| ion2020 F1 | 49 | 4 | 6 | 0 |
| ion2020 F2 | 50 | 0 | 2 | 0 |
| ionproj F1 | 292 | 2 | 2 | 0 |
| ionproj F2 | 378 | 22 | 18 | 14 |
| **Total** | **769** | **28** | **28** | **14** |

## Reading

1. **The GLR alarm fixes detection.** It catches almost every 2-SD fault (99% against 85%) and many more 1-SD faults, at no throughput cost and with as few false alarms as before.
2. **Better detection did not lower late bad pairs below the simple alarm's** (28 against 28). The small faults it newly detects cause few bad pairs anyway. The remaining late bad pairs happen during the 1–4 epochs it takes to collect enough evidence.
3. **The sensitive version (`gglr_s`) halves late bad pairs (14) and has zero in 3 of 4 groups.** The price is about 0.7 false alarms per network. They cost almost no throughput, because a false alarm only restarts one link's estimate.
4. **Combined with G6:**
   - alarm-based guards cut post-fault bad pairs by about 96–97% against no guard;
   - they keep the late rate below about 0.1%;
   - first-epoch exposure and a formal guarantee under unannounced faults remain open.
5. **H1 failed on a 4-pair difference** (8 against 4 on ion2020). It stays a failure, as pre-registered.
