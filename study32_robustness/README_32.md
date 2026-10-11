# Study 32 ("re-opening and robustness"): pre-registration (11 Oct 2026)

**Status:** locked. Commit this folder publicly **before** any confirmatory job.

Theory: `THEORY_32.md`. Design, review and pilot: `README_32_PILOT.md`, `REVIEW_32.md`. Locked analysis: `analyze_32.py`.

## Runs
- **Code:** `study32.py` (3d1462ed528bb311) on Study 30's code, unchanged (study30.py e796ebb7, core30.py 9091e336, mcheck.py a05f0822, hw24.py from s26).
- **Confirmatory tasks:** `tasks_s32.jsonl` (f8dbba7c61d6fe44): 3,328 tasks, seeds 19331–19334, 32 networks per cell.
- **Dev pilot:** `des_p32_psc/runs.csv` (2a7d2da377d947b9): 416 runs, dev seeds, 4 networks per cell.
  - Output: `pilot_analysis_32.txt`, `pilot_summary_32.txt`.
  - All bars were fixed after the pilot.

## Hypotheses
Bootstrap: 4,000 network-cluster resamples within hardware type, one-sided 95%.

| | Tier | Hypothesis | Passes if | Pilot |
|---|---|---|---|---|
| **R1** | primary | The bound without intersection keeps Theorem 2 in class (kgMChN; o0.044, L0.044) | Post-alarm users: upper bound ≤ 0.10. Post-alarm pairs: upper bound ≤ 0.01 | 0/1,485; 0/59,906 |
| **R2** | primary | No throughput cost in class ('-', o0.044, L0.044) | Paired fq(kgMChN) − fq(kgMCh): lower bound ≥ −2 points | −0.2 (LB −0.5) |
| **R3** | primary | Recovery limits the damage of a miscoverage (o0.044FM) | Ratio of post-alarm bad-pair rates (no intersection ÷ running minimum): upper bound ≤ 0.5 | 0.18 (UB 0.25) |
| **R4** | primary | The bound recovers (o0.044FM) | Runs that went below θ and came back: CP95 lower bound ≥ 0.8 | 16/16 (LB 0.83); median 486 tests |
| **E1** | primary | Theorem 2 is robust to τ 0.85 and 0.92 and to less calibration data (kgMCh, o0.044, pooled) | Post-alarm users: upper bound ≤ 0.10. Post-alarm pairs: upper bound ≤ 0.01 | 0/1,995; 0/93,708 |
| **E2** | primary | Corollary 3 is robust (kgMCa; all Block E cells, whole run) | Users ever given a bad pair: upper bound ≤ 0.10 | 0/17,408 |
| S1 | secondary (prediction) | A false alarm before onset (L0.044F): no intersection lowers post-alarm pair risk. Per-user risk stays high because (B2) fails | rate(N) < rate(running minimum) | 0.15 vs 0.33 |
| S2 | secondary (prediction) | Fewer re-alarms with no intersection (o0.044FM) | Mean real alarms per run, N < running minimum | 0.06 vs 0.94 |
| S3 | secondary (prediction) | Thin hardware documents the limit | kgMCh alarms in ≤ 10% of runs, and kgMCa throughput < 5% | 0; 0.007 |
| S4 | secondary | The certificate stays valid under feedback | Violations: CP95 upper bound ≤ 0.05 | 1/416; 0/416 |

**Descriptive outputs:** Block R by cell; Block E and Block T by cell, including throughput costs. The ion2020 cell at τ = 0.92 with o0.044 has a very small oracle count, so it is report-only.

## Confirmatory commands (PSC)
Expected cost is about 300 SU; the pilot took at most 325 s per shard.
```bash
cd /ocean/projects/cis260277p/$USER/s32
sbatch --account=cis260277p --array=0-31 --cpus-per-task=16 --time=03:00:00 \
  --export=ALL,S18C_DIR=$PWD,PY=/opt/packages/anaconda3-2024.10-1/bin/python3,S18C_MODULE=study32,S18C_TASKS=tasks_s32.jsonl,S18C_OUT=des_s32_psc,S18C_NSHARDS=32,S18C_LIB=$PWD/../s18c,S26_DIR=$PWD/../s26,S27_DIR=$PWD/../s27,S30_DIR=$PWD/../s30 \
  s18c_array.sbatch
```
