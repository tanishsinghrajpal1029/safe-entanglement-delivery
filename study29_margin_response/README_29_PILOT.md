# Study 29 ("margin response"): design and dev pilot (11 Oct 2026)

**Status:** dev pilot only. The pre-registration (hypotheses, bars, locked `analyze_29.py`) follows the pilot and will be committed publicly before any confirmatory job.

## Why
Study 28's model check detected wrong models reliably, but two weaknesses remained:
- **H4 failed.** One network alarmed after 8 tests, raised its margin by only 0.02 (the true offset was 0.044), and never alarmed again. As a result, 0.8% of post-alarm pairs were bad.
- **Margins were too high.** Post-alarm margins were about twice the true offset, so throughput was about half of oracle.

## Design (`study29.py`)
Study 28's network, check, horizon and test streams, on ion hardware only.

**Arms**

| Arm | Response after an alarm |
|---|---|
| kg | No check (reference) |
| kgM | Study 28's response, unchanged. A replay reproduces Study 28's network 19 exactly: 6,232 bad of 24,134 |
| kgMJ | Jump: an alarm based on fewer than 50 tests sets the margin to at least 0.10 |
| **kgMT** | **Tracking** (described below) |
| kgMTp | Tracking with the point estimate only (baseline) |
| kgMTa | Always-track: no alarm gate (baseline) |

**How kgMT tracks**
- After an alarm, the margin is held at 0.10 until 50 post-alarm tests have arrived.
- Then, every 10 epochs, the margin is reset to an exact Clopper–Pearson upper bound on the model offset, at level β/9 (Bonferroni over the looks).
- The offset estimate uses only post-alarm tests and the model's central prediction with zero readout error.
- **The margin can go down.** Each decrease restarts the e-process at its next spending level.
- **Probe tests.** A pair blocked only by the margin is not delivered; it is probe-tested instead and added to the estimate. Blocked pairs are free test material, so a high margin cannot starve the estimate.

**Scenarios**
- none;
- undeclared offsets of 0.02, 0.044 and 0.08;
- **forced-alarm cells**: an alarm injected at the 8th test, in "none" (recovery from a false alarm) and at offset 0.044 (Study 28's failure case).

**Baselines:** exact margin at each offset; 16-point tomography at 0.044.

**Replay:** block R28 re-runs Study 28's failing network under every arm.

**Size**
- Pilot: 1,094 tasks (dev seeds 20311–20314, 8 networks per cell, plus 6 replay tasks).
- Confirmatory: 4,352 tasks (seeds 19311–19314, 32 networks per cell).

## Review (`REVIEW_29.md`) and changes before the pilot
**What the reviewer confirmed:**
- kgM is identical to Study 28.
- The arms are paired, and the e-process is intact.
- Biases and correlation between tests are small.

**Blocker B1 (fixed).** The tracking window used to include the alarm segment, which overstates the offset (the replay stayed at margin 0.10). It now uses post-alarm tests only, plus probe tests.

**Major findings**

| Finding | Status |
|---|---|
| M1: readout | Fixed. The central prediction uses zero readout error, so readout is charged to the offset (conservative) |
| M2: normal bound misses 7–14% of the time | Fixed. Now an exact Clopper–Pearson bound, with Bonferroni over 9 looks |
| M3: restarted check blind after tracking starts | Fixed. Restart on every decrease |
| M4: protection after a decrease is heuristic | Stated in the docstring and the paper |
| M5: the failure case is too rare to test | Fixed. Forced-alarm cells and the replay added |
| M6: missing outputs | Fixed. Margin below offset, lowest margin, decreases, probes, post-alarm tests and throughput |
| M7: missing baselines | Partly. Added always-track, point estimate and tomography. Pair-varying model error and a changing offset are listed as limitations |

## Dev smoke tests (disclosed; not evidence)
Design choices were made on these few networks:
- the switch from an empirical-Bernstein to a normal bound, then to the exact bound;
- adding probes after the replay showed starvation.

| Network | Margin | Bad pairs after the alarm | Qualified pairs |
|---|---|---|---|
| Replay of Study 28's network 19, kgMT | 0.046 (true offset 0.044) | 0 | 14,451 (kgM: 17,902 with 6,232 bad; kgMJ: 1,462) |
| Forced false alarm, kgMT | Recovered to 0.014 | — | 9,402 |
| Offset 0.044, dev network 0, kgMT | 0.050 | 0 | — |
