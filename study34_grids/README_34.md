# Study 34 ("other grids"): pre-registration (12 Oct 2026)

**Status:** locked. Commit this folder publicly **before** any confirmatory job.

Design, review and pilot: `README_34_PILOT.md`, `REVIEW_34.md`, `pilot_analysis_34.txt`. Locked analysis: `analyze_34.py`.

## Runs
- **Code:** `study34.py` (05acdad26f113f5d) on Study 32's code, unchanged (study32.py 3d1462ed; study30.py e796ebb7; core30.py 9091e336).
- **Confirmatory tasks** (seeds 19341–19344, 32 networks per cell):

  | Grid | Task file | sha | Tasks |
  |---|---|---|---|
  | 5×5 | `tasks_s34_g5.jsonl` | 4818399d4f9e56f1 | 1,408 |
  | 10×10 | `tasks_s34_g10.jsonl` | eb09915b29244e5b | 1,408 |
  | 30×30 | `tasks_s34_g30.jsonl` | 349db9882349e67d | 2,112 |

- **Dev pilot:** 616 runs (runs.csv shas c78898336e352538, 7e296f0546541df3, 2db35cfb03bafeca).
  - Every hypothesis passes on the pilot data. That only shows the analysis runs end to end.
  - All bars were fixed after the pilot.

## Hypotheses
Bootstrap: network clusters within grid × load × hardware type. Per-user measures use **served** users.

| | Tier | Hypothesis | Passes if | Pilot |
|---|---|---|---|---|
| **K1** | primary | Theorem 2 on 10×10 and 30×30 (gated arm kgMChN; offset 0.044 and forced early alarm; all loads) | Post-alarm bad pairs: upper bound ≤ 0.01. Post-alarm users: upper bound ≤ 0.10 | 0/508,665; 0/116,352 |
| **K2** | primary | Corollary 3 on 10×10 and 30×30 (always-on arm kgMCa; all cells) | Bad pairs: upper bound ≤ 0.01. Served users ever given a bad pair: upper bound ≤ 0.10 | 0/948,325; 0/181,064 |
| **K3** | primary | The 5×5 reference reproduces Studies 30 and 32 with fresh seeds | Same bars as K1 and K2 | 0; 0 |
| S1 | secondary (prediction) | The test can tell rules apart: with no check, offset 0.044 harms > 10% of served users on every grid and load | All > 0.10 | 0.67–0.74 |
| S2 | secondary (prediction) | Detection carries over: alarm rate at offset 0.044 (base load) on 30×30 is within 0.15 of 5×5 | \|diff\| ≤ 0.15 | 1.00 vs 0.94 |
| S3 | secondary (prediction) | Three times the load detects earlier, on 5×5 and on 30×30 | Median first-alarm epoch, m3 < base | 12 vs 22; 10 vs 22 |
| S4 | secondary | Matched exposure: gated served-user risk at offset 0.044 on 30×30 'u' is within 0.10 of 5×5 base | \|diff\| ≤ 0.10 | 0.70 vs 0.65 |
| S5 | secondary | The certificate stays valid under feedback | Violations: CP95 upper bound ≤ 0.05 | 1/616; 6/616 |

## Confirmatory commands (PSC; three jobs, one per grid; about 500 SU)
```bash
cd /ocean/projects/cis260277p/$USER/s34
for G in 5 10 30; do
  N=32; [ $G = 30 ] && N=64
  sbatch --account=cis260277p --array=0-$((N-1)) --cpus-per-task=16 --time=04:00:00 \
    --export=ALL,S34_GRID=$G,S18C_DIR=$PWD,PY=/opt/packages/anaconda3-2024.10-1/bin/python3,S18C_MODULE=study34,S18C_TASKS=tasks_s34_g$G.jsonl,S18C_OUT=des_s34_g$G,S18C_NSHARDS=$N,S18C_LIB=$PWD/../s18c,S26_DIR=$PWD/../s26,S27_DIR=$PWD/../s27,S30_DIR=$PWD/../s30,S32_DIR=$PWD/../s32 \
    s18c_array.sbatch
done
```
