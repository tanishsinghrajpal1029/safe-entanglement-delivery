# Study 30 ("provable closed loop"): pre-registration (11 Oct 2026)

**Status:** locked. Commit this folder publicly **before** any confirmatory job.

Theory: `THEORY_30.md`. Design and review: `README_30_PILOT.md`, `REVIEW_30.md`. Locked analysis: `analyze_30.py`.

## Runs
- **Code:** `study30.py` (e796ebb7c05a28cf), `core30.py` (9091e3364b19fe56), `mcheck.py` (a05f0822).
- **Confirmatory tasks:** `tasks_s30.jsonl` (15e156bc8734488c). 8,384 tasks, seeds 19321–19324, 32 networks per cell.
- **Dev pilot:** `des_p30_psc/runs.csv` (f6f1c34173bea250). 1,048 runs, dev seeds 20321–20324, 4 networks per cell. Pilot output: `pilot_analysis_30.txt`, `pilot_summary_30.txt`.
  - The bars below were fixed after the pilot. Bars marked "prediction informed by the pilot" are labelled as such.

## Hypotheses
Bootstrap: 4,000 network-cluster resamples within hardware type, one-sided 95%.

| | Tier | Hypothesis | Passes if | Pilot |
|---|---|---|---|---|
| **P1** | primary | **Theorem 2 in class.** Gated provable arms (kgMC, kgMCp, kgMCh) in constant-offset cells (o0.02, o0.044, o0.044F, o0.08, L0.044), plus kgMCs in s0.044 | Users with a post-alarm bad pair: upper bound ≤ 0.10 (the theorem's per-user bound). Post-alarm bad pairs: upper bound ≤ 0.01 | 0/9,932 users; 0/400,835 pairs |
| **P2** | primary | **Study 28's failure case** (forced alarm at test 8, offset 0.044), gated provable arms | Runs with any post-alarm bad pair: CP95 upper bound ≤ 0.05 | 0/48 (UB 0.06; too few runs) |
| **P3** | primary | **Always-on arm, full guarantee** where (B2) holds from t = 0 ('-', '-F', o0.02, o0.044, o0.044F, o0.08) | Users ever given a bad pair: upper bound ≤ 0.10 | 0/26,112 |
| **P4** | primary | **Validity of the new checks** (kgMCp, kgMCh; no stressor) | False segment alarms ≤ 0.05 per run, upper bound ≤ 0.08 | 0/16 each |
| **P5** | primary | **The offset bound is tight enough to be useful** (kgMCh at o0.044; kgMCs at s0.044; each hardware type and p) | Median (post-alarm margin − true offset) between 0 and 0.03 | +0.006 to +0.013 |
| S1 | secondary (prediction informed by the pilot) | **Price of provability** at o0.044 | fq(kgMT) − fq(kgMCh) between 0 and 15 points, each hw and p | +3.7 to +14.0 |
| S2 | secondary (prediction) | **Debt** under a late onset | Plug-in alarm rate > mixture alarm rate | 0.875 vs 0.688 |
| S3 | secondary | **The hybrid is robust** | Hybrid alarm rate ≥ min(mixture, plug-in) − 0.05 in L0.044, o0.044, s0.044 and h0.044 | yes |
| S4 | secondary (prediction: **unsafe**) | **Outside the theorem**: L0.044F (false alarm before onset); h0.044 (heterogeneous); s0.044 with constant shape; kgMCs under a constant offset; kgMCa under late onset | Per-user risk > 0.10 in every one of these cells | 0.17–0.90 |
| S5 | secondary | **Certificate valid under feedback** | Violations: CP95 upper bound ≤ 0.05 (p = 0.1 and 0.2) | 2/1,048; 0/1,048 |
| S6 | secondary (prediction) | **Static competitor** (fixed margin 0.10 from t = 0) | Throughput < 5% of oracle on both hw | 0 |

**Descriptive outputs**
- D1: detection rate and median first-alarm epoch.
- D2: **worst-user risk over the whole run.** This is the headline cost of Proposition N.
- D3: post-alarm risk by cell.
- D4: throughput.

## What the pilot already shows (dev data; disclosed)
1. **In class, the provable loop delivered no bad pair after any alarm** (256 runs), at a margin excess of about 0.01.
2. **Detection is much slower once the offset is physical** (in the truth) than in Studies 28–29, where it was added to the model.
   - At o0.044 on ion2020, the median first alarm comes at epoch 33–55 (Study 28: 8–23).
   - o0.02 is rarely detected.
   - Under late onset, 25–100% of runs alarm, typically about 35–55 epochs after the onset.
   - This confirms ledger E134: the earlier detection power was inflated.
3. **So the gated loop barely changes worst-user risk over the whole run:** 0.50 against 0.56 without a check at o0.044. Most harm happens before the alarm (Prop. N).
   - Only the always-on arm protects every user (0 bad), at 0.59–0.68 of oracle with no stressor and 0.21–0.62 at o0.044.
   - A fixed margin of 0.10 delivers nothing.
4. **Outside (B2) the guarantee fails badly.** Heterogeneous offsets, a wrong shape, or a false alarm before onset give post-alarm per-user risk of 0.17–0.90.

## Confirmatory commands (PSC)
Size: 8,384 tasks. Pilot timing was about 513 s per shard for 33 tasks with 16 workers. That implies about 1.2 h per shard, or about 600 SU in total.

```bash
cd /ocean/projects/cis260277p/$USER/s30
sbatch --account=cis260277p --array=0-31 --cpus-per-task=16 --time=04:00:00 \
  --export=ALL,S18C_DIR=$PWD,PY=/opt/packages/anaconda3-2024.10-1/bin/python3,S18C_MODULE=study30,S18C_TASKS=tasks_s30.jsonl,S18C_OUT=des_s30_psc,S18C_NSHARDS=32,S18C_LIB=$PWD/../s18c,S26_DIR=$PWD/../s26,S27_DIR=$PWD/../s27 \
  s18c_array.sbatch
```
