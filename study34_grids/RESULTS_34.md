# Study 34 ("other grids"): confirmatory results (12 Oct 2026)

## What was run
- **Pre-registration:** `README_34.md` (380770f9fba9d345) and the locked `analyze_34.py` (2819448cb47de63d).
  - Public commit `1f5636c`, made at 00:52:51 UTC. The first shard started at 00:54:40 UTC, 1 min 49 s later. Confirm the push time on GitHub.
- **Code:** `study34.py` 05acdad26f113f5d, recorded in every shard.
- **Tasks** (seeds 19341–19344; 4,928 runs in total; no epoch clamped):

  | Grid | Task file sha | Shards | Longest shard | runs.csv sha |
  |---|---|---|---|---|
  | 5×5 | 4818399d | 32 | 1,817 s | a00b94cf1882257f |
  | 10×10 | eb09915b | 32 | 855 s | bfc3461784fcf31b |
  | 30×30 | 349db988 | 64 | 3,439 s | 423e18e6898770fa |

- **Compute:** about 450 SU.
- **Analysis:** run on PSC and re-run in the cloud; the two are identical.

## Verdicts: 3/3 primary PASS, 6/6 secondary PASS

| | Tier | Result | Numbers |
|---|---|---|---|
| **K1** | primary | **PASS** | **Theorem 2 on 10×10 and 30×30:** 0 of 4,166,012 post-alarm pairs bad; 0 of 940,391 post-alarm users |
| **K2** | primary | **PASS** | **Corollary 3 on 10×10 and 30×30:** 0 of 7,827,544 pairs bad; 0 of 1,495,612 served users |
| **K3** | primary | **PASS** | **The 5×5 reference reproduces Studies 30 and 32** with fresh seeds: 0 post-alarm bad pairs; always-on 0 |
| S1 | secondary (prediction) | PASS | **The cells can tell rules apart:** with no check, 0.67–0.75 of served users get a bad pair on every grid and load |
| S2 | secondary (prediction) | PASS | **Detection carries over:** at offset 0.044 the alarm rate is 0.938 on both 5×5 and 30×30 |
| S3 | secondary (prediction) | PASS | **More traffic, earlier alarms:** median first alarm at epoch 10.1 vs 25.6 (5×5) and 11.8 vs 27.5 (30×30) |
| S4 | secondary | PASS | **Matched exposure:** served-user risk of the gated rule at offset 0.044 is 0.705 (30×30) vs 0.629 (5×5) |
| S5 | secondary | PASS | **Certificate under feedback:** violated in 53 (p = 0.1) and 72 (p = 0.2) of 4,928 runs (upper bounds 1.35% and 1.77%) |

## Descriptive results (served users; fraction of oracle)

**No model error:**
- The gated rule matches no check: throughput 0.88–0.91 on every grid.
- False alarms occurred in at most 0.8% of runs per cell.
- The always-on margin costs 15–25 points of throughput: 0.63–0.75 against 0.88–0.91.

**Offset 0.044:**
- **Gated rule:**
  - Alarms in 94–100% of runs, at a median epoch of 26–29, or 10–12 with three times the traffic.
  - Margin about 0.056, the same on every grid.
  - Throughput 0.52–0.60.
  - Served-user risk 0.43–0.71, almost all of it before the alarm. It is lower on the 30×30 grid at base load (0.52) and with three times the traffic (0.43).
- **No check:** served-user risk 0.67–0.75.
- **Always-on:** no harm, at throughput 0.37–0.50.

## What it shows
1. **The closed loop scales.** The provable guarantees, Theorem 2 and Corollary 3, held on grids of 180 and 1,740 links. That is 0 bad pairs after the alarm and 0 for the always-on margin across 4,928 runs, with the margin and throughput essentially unchanged.
2. **Detection depends on the test volume, not the topology.** It was the same on every grid at the same rate, and twice as fast with three times the traffic.
3. **The honest limit carries over too.** Harm before the alarm dominates on every grid.

## Limits
- Simulation, ion hardware only, square grids only.
- Calibration per link and the offset do not change with size, as expected for a scaling sanity check.
