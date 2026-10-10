# Study 18C G6 results: per-user protection after sudden link faults (confirmatory, 9 Oct 2026)

**Pre-registration:** `README_G6.md` (E80).

**Provenance:**
- 1,024 of 1,024 tasks, 64 networks per group.
- runs.csv sha `9a980977de17635e` on PSC and on the Mac.
- The module (`70769aae`) and analyzer (`a9fa7a46`) are unchanged.
- 475 faults in total.

## Verdicts

| | Question | Result |
|---|---|---|
| **H1** (primary) | Does the alarm guard stop bad deliveries on faulted paths after the first post-fault epoch? | **FAIL, narrowly.** Fewer late bad pairs than `cal` in every group: 9 vs 20, 0 vs 191, 15 vs 413, 0 vs 169. But the pooled late rate for ion2020 was **0.14%**, above the 0.1% bar (9 of 6,545). ionproj passed at 0.07%. |
| **H2** (primary) | Is the alarm guard safe overall? | **PASS.** r ≤ 0.12%, upper bound ≤ 0.15%, bad paths 0.5–2.8% |
| H3 (secondary) | Does the alarm work as a detector? | **FAIL.** It detected 414 of 475 faults (87%; the bar was 90%), with 2 false alarms in 256 networks. Detection was 100% for 4-SD faults and lower for 2-SD faults: 113/118 on ion2020, **76/132 on ionproj**. |
| H4 (secondary) | Is the alarm cheap? | **PASS.** It cost 0.4–0.7 points of oracle throughput against the plain guard. |

## Late post-fault bad pairs (after the first epoch)

| Group | cal | gnaive | **galarm** | gwin |
|---|---|---|---|---|
| ion2020 F2 (2-SD faults) | 20 | 12 | **9** | 0 |
| ion2020 F4 (4-SD faults) | 191 | 125 | **0** | 5 |
| ionproj F2 | 413 | 47 | **15** | 0 |
| ionproj F4 | 169 | 102 | **0** | 0 |
| **Total** | **793** | **286** | **24 (−97% vs cal, −92% vs gnaive)** | **5** |

## Other results

- **Early bad pairs**, in the epoch the fault happened, were the large remainder for `cal`, `gnaive` and `galarm`: 97–444 per group for `galarm`. No method can see a fault before its data arrive.
- **Worst single user (max bad pairs on one path):**
  - `galarm` 3–7;
  - `cal` 9–21;
  - `gnaive` up to 22.
- **`gwin`** (requires the last epoch's data alone to clear the bar):
  - **only 166 bad pairs in total across all 4 groups**, including the early ones;
  - 0 late bad in 3 of 4 groups;
  - but throughput 0.66–0.72 of oracle, against 0.81–0.87 for `galarm`.

## Reading

1. **Large faults (4 SD): the alarm works.** Every one was detected, there were 0 late bad pairs, and it costs almost nothing.
2. **Small faults (2 SD) are the hard case.** They are often not detected at this alarm level (only 58% on ionproj), so a few late bad pairs remain: 9 and 15. That is still 55–96% fewer than with no guard. This failed the pre-registered bar narrowly on ion2020, and the failure stands.
3. **The real per-user exposure is the first epoch after a fault.** Removing it needs either faster calibration data or a costlier bound such as `gwin`. `gwin` shows the trade-off: almost no bad pairs at all, but 15–20 points less throughput.
4. **For the paper:**
   - the alarm guard reduces post-fault harm by about 97% at almost no cost;
   - it does not give a formal guarantee under unannounced faults;
   - small faults and the first epoch remain open.
5. **Possible next step (needs its own pre-registration and budget):** a more sensitive alarm, such as a CUSUM over several epochs, to catch small faults. That trades off against false alarms.
