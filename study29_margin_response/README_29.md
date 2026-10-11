# Study 29 ("margin response"): pre-registration (11 Oct 2026)

**Status:** locked. This file and `analyze_29.py` must be committed publicly before the first confirmatory job.

**Related files**
- Design and dev history: `README_29_PILOT.md`.
- Review: `REVIEW_29.md`.

## Question
After the model check (Study 28, Prop. MC) alarms, how should the network set its margin so that:
- the model error does not keep causing harm (Study 28's H4 failure), and
- throughput is not wasted (Study 28's margins were about 2× the true offset)?

## Design
`study29.py` is unchanged since the pilot.

**Setup**
- **Hardware:** ion2020 and ionproj.
- **Test fraction:** p = 0.1 and 0.2.
- **Horizon:** 90 epochs.

**Arms**
- kg: no model check (reference).
- kgM: Study 28's response.
- kgMJ: jump to the maximum margin.
- **kgMT: tracking** (main arm). It uses an exact upper bound on the offset, computed from post-alarm user tests plus probe tests of pairs blocked by the margin. The margin can go down, and every decrease restarts the e-process.
- kgMTp: kgMT with the point estimate instead of the bound.
- kgMTa: kgMT with no alarm gate (always tracking).

**Scenarios**
- **No stressor.**
- **Undeclared offset** of 0.02, 0.044 or 0.08.
- **Forced early alarm** (an alarm injected at the 8th test):
  - with no stressor, to test recovery from a false alarm;
  - with offset 0.044, which reproduces Study 28's failure.

**Baselines:** an exact margin at each offset, and 16-point tomography at offset 0.044.

**Replay (descriptive):** block R28 re-runs Study 28's network 19.

**Size:** 4,352 tasks, 32 networks per cell. Seeds 19311–19314 (fresh).

## Dev pilot (dev seeds only)
The pilot run is `des_p29_psc/runs.csv` (sha `8d2888f6`, 1,094 rows). There was no code change after it.

**kgMT results**
- **Safety after the alarm:** 0 bad pairs in 1,529,000 post-alarm deliveries, across all model-error and forced-alarm cells.
  - Study 28's response (kgM): 9.3% / 7.8% bad after the alarm.
  - Jump (kgMJ): 0–0.2% bad, but throughput 0.54.
- **Margin accuracy:** the post-alarm margin is 0.008–0.011 above the true offset (median).
- **Throughput:** about 0.80–0.84 of oracle at offset 0.044. Study 28's response reaches 0.39–0.59, and 16-point tomography 0.33–0.56.
- **Recovery from a forced false alarm:** the margin returns to 0.007–0.014. Jump stays at 0.10 and delivers nothing.
- **Replay of Study 28's network 19:** 0 bad pairs and margin 0.046. Study 28's response gave 6,232 bad pairs.

**The baselines show why each part of kgMT is needed**
- **The upper bound matters:** with the point estimate (kgMTp), 23 of 128 runs had post-alarm bad pairs.
- **The alarm gate matters:** always-tracking (kgMTa) costs 14 points with no stressor.

## Hypotheses (`analyze_29.py`, locked)
Bootstrap: 4,000 resamples of networks within each hardware type, one-sided 95%.

| | Tier | What is tested | Pass if |
|---|---|---|---|
| **T1** | primary | kgMT post-alarm delivered-pair risk, all model-error cells pooled (both hw, both p) | Bootstrap upper bound ≤ 1% |
| **T2** | primary | Study 28's failure case (forced early alarm, offset 0.044): kgMT runs with any post-alarm bad pair | Clopper–Pearson upper bound ≤ 5% |
| **T3** | primary | Margin accuracy: median over networks of (time-averaged post-alarm margin − offset), offsets 0.044 and 0.08 × hw × p (8 cells) | Within [0, 0.02] in each cell |
| **T4** | primary | Throughput gain over Study 28's response at offset 0.044: fq(kgMT) − fq(kgM), paired | Bootstrap lower bound ≥ +10 points, each hw and p |
| **T5** | primary | Validity of the check when the margin can fall: kgMT false segment alarms per run, in the no-stressor and forced-false-alarm cells | Mean ≤ 0.05 and bootstrap upper bound ≤ 0.08 |
| **T6** | primary | Recovery from a false alarm: median time-averaged post-alarm margin, forced-false-alarm cells | ≤ 0.02 in each hw and p |
| U1 | secondary (prediction) | The bound matters: runs with a post-alarm bad pair, kgMTp vs kgMT | kgMTp > kgMT |
| U2 | secondary | kgMT throughput beats 16-point tomography at offset 0.044 | On each hw |
| U3 | secondary (prediction) | The alarm gate matters: fq(kg) − fq(kgMTa) with no stressor | ≥ 5 points on each hw |
| U4 | secondary | Network certificate validity (each p) | Clopper–Pearson upper bound ≤ 5% |
| D1–D3 | descriptive | Cells, no-stressor behaviour, and the R28 replay | — |

## Disclosures
- **T2 and T5 were redefined after the pilot.**
  - T2 failed on the pilot only because of its size (0/32 runs gives an upper bound of 8.9%).
  - T5 was changed from "false first alarms with no stressor" to "false segment alarms after margin decreases". In the no-stressor cells, kgMT is identical to kgM up to the first alarm, so the first version tested nothing new.
- **The response is a heuristic.** Once the margin has fallen, Theorem 1's protection is heuristic. The formal guarantee remains the e-process (Prop. MC).
- **Probe tests need cooperation:** the end nodes must measure pairs that the margin blocks.

**Commitment.** No change after this point, and every outcome is reported.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `study29.py` | `532e612f0de478ef` |
| `analyze_29.py` (locked) | `4a54c1e339839150` |
| `tasks_s29.jsonl` (4,352) | `e9c11dcb77432c14` |
| `tasks_p29.jsonl` (1,094, pilot) | `9664b6bec7c4c9fd` |
| `mcheck.py` | `a05f0822c0335f3f` (unchanged) |

**PSC:** 32 shards × 16 cores × 90 min. Ceiling 768 SU; expected about 150–200 SU.
