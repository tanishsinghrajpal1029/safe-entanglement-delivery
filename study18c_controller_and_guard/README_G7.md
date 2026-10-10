# Study 18C G7: a more sensitive alarm for small link faults (pre-registered 9 Oct 2026, before any confirmatory run)

**Why.** In G6 (E81) the single-epoch alarm `galarm` caught every 4-SD fault but only 87% of faults overall, and 58% of 2-SD faults on ionproj. That left 9 and 15 late bad pairs, and H1 and H3 failed. G7 tests an alarm that pools several epochs.

**Budget.** Tanish approved this run (chose option 2 on 9 Oct). Ceiling 64 SU; expected about 10–15.

## New alarm: `gglr`, a generalized-likelihood-ratio change detector per link

**How it works:**
- It looks at the link's parity counts since its last restart.
- For each candidate change point within the last W = 4 epochs, it compares the rate before (N0, K0) and after (N1, K1):
  - GLR = ℓ(K0, N0) + ℓ(K1, N1) − ℓ(K0 + K1, N0 + N1), where ℓ(K, N) = K log(K/N) + (N − K) log(1 − K/N).
  - Only drops count: the rate after must be lower.
  - It needs N0 ≥ 50.
- The alarm fires when max GLR > h.
- On alarm, the link's counts are discarded and its confidence sequence restarts, with α spent as 6α/(π²c²).

**Two thresholds, fixed before the pilot from the χ² approximation (2·GLR ≈ χ²₁):**
- **`gglr`, h = 9:** expected about 0.04 false alarms per network.
- **`gglr_s`, h = 6:** about 1 false alarm per network, but more sensitive.

**Controllers:** `cal`, `galarm` (G6), `gglr`, `gglr_s`.

**Scenarios:** as in G6 (5 × 5 grid; each link faults with probability 0.05 at a random epoch), with:
- **F2:** 2-SD drop;
- **F1:** 1-SD drop, harder to detect.

**Design:** 2 hw × 2 scenarios × 4 controllers × 64 networks = **1,024 tasks**. Fresh seeds 19161–19164.

## Dev pilot (disclosed; seeds 20161–20164; 3 networks per group; 24 faults)

| | cal | galarm | gglr | gglr_s |
|---|---|---|---|---|
| Faults detected | — | 10/24 (F1 3/16, F2 7/8) | **20/24** (F1 12/16, F2 8/8) | 23/24 |
| Late post-fault bad (all 4 groups) | 27 | 0 | **0** | 1 |
| False alarms (12 networks) | — | 0 | 1 | 4 |
| Fraction of oracle | 0.85–0.97 | 0.80–0.90 | 0.81–0.90 | 0.80–0.90 |

The pilot is too small to separate late-bad counts: there were few faults, and `galarm` also had 0 late bad pairs. Its main signal is detection.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `drift_queue_des_g7.py` | `33bf5888af5420e6` |
| `tasks_g7.jsonl` (1,024) | `13cd909784aefd73` |
| `analyze_g7.py` (locked; tested on synthetic data) | `2cdb7a2b2cb76d87` |

G7 also uses, unchanged:
- `drift_queue_des_g6.py` (`70769aae4b66680e`); G7 adds the F1 drop size at import;
- `drift_queue_des_g1.py` and `drift_queue_des_g2.py`.

## Hypotheses

| | Question | Bar |
|---|---|---|
| **H1** (primary) | Does the GLR alarm stop late post-fault bad pairs? | `gglr` late post-fault bad ≤ 0.1% of post-fault deliveries **and** ≤ `galarm`'s, per hw pooled over F2 and F1 |
| **H2** (primary) | Does it detect 2-SD faults (where `galarm` failed)? | `gglr` detects ≥ 90% of 2-SD faults, both hw pooled |
| H3 (secondary) | Are false alarms rare? | `gglr` ≤ 1 false alarm per 10 networks. False alarms are alarms on unfaulted links, or before the fault on faulted links. |
| H4 (secondary) | Is it safe overall? | `gglr` r ≤ 1%, upper bound ≤ 1%, bad paths ≤ 5% in all 4 groups |
| H5 (secondary) | Is it cheap? | `gglr` fraction of oracle ≥ `galarm` − 0.02 in every group |
| H6 (descriptive) | What does each controller miss and cost? | Late and early bad pairs, detection, false alarms and throughput for all controllers, including `gglr_s` and the F1 faults |

**Limitation, stated now.** First-epoch ("early") bad pairs are unaffected by any alarm, as in G6.

**Commitment.** No re-tuning after the run; every outcome is reported.
