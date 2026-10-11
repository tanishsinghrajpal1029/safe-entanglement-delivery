# Study 30 ("provable closed loop"): design and dev pilot (11 Oct 2026)

**Status:** dev pilot only. The pre-registration (hypotheses, bars, locked `analyze_30.py`) follows the pilot, and is committed publicly before any confirmatory job. Theory: `THEORY_30.md`.

## Why
Two referee-level gaps remained after Studies 29 and 31:
1. **The margin response is a heuristic.** Study 29's response worked (0 post-alarm bad pairs in 512 runs), but had no proof.
2. **The check went blind on real hardware.** On IBM (Study 31, W3), the check never alarmed. The cause was "debt": the fixed-bet e-process lost 3.75 nats while the declared model was conservative, then could not recover in time.

## What is new
- **Theorem 2 (provable post-alarm margin).** After an alarm, a time-uniform upper confidence sequence on the model offset θ is built from the tests users already run (a_i = F_model(upper link bounds) − 1 + 1.5 E_i). The margin is U_t · φ_i.
  - Guarantee: P(user gets a bad pair after the first alarm) ≤ α + α_hi + α′ (0.05 + 0.025 + 0.025).
  - Assumptions: the offset has a declared shape after the first alarm (B2), and is at most θ_max = 0.10 (B4).
  - Corollary O (offset with an onset time): add β.
- **Proposition D (check with limited debt).** A plug-in bet is placed only when recent tests show an excess. The hybrid (mixture + plug-in average) is the default.

## Arms (`study30.py`)

| Arm | Response |
|---|---|
| kg | No check |
| kgMT | Study 29's tracking response (heuristic), unchanged |
| **kgMC** | Provable margin (constant shape) + Study 28's mixture check |
| kgMCp | Provable margin + plug-in check |
| **kgMCh** | Provable margin + hybrid check |
| kgMCs | As kgMCh, with storage-proportional shape φ = min(hold/0.0105, 3) |
| kgMCa | Always-on: the offset CS and margin run from t = 0 (start at 0.10), with no alarm gate |

**Scenarios.** The truth is worse than the model by Δ, implemented as extra depolarizing noise, so model fidelity never exceeds 1.
- **In class:** none; constant 0.02, 0.044, 0.08.
- **Storage-proportional:** 0.044 × φ.
- **Heterogeneous per link** (out of class for every arm): mean 0.044, sd 0.02.
- **Late onset:** 0.044 from epoch 30.
- **Forced alarm at the 8th test:** in "none", in 0.044, and in late onset. In late onset the forced alarm comes before the onset, which is a deliberate (B2) failure.

**Baselines.** Exact per-pair margin (constant and storage); a fixed margin of 0.10 from t = 0, which is provable with no data (static competitor).

**Size**

| | Tasks | Networks per cell | Seeds |
|---|---|---|---|
| Pilot | 1,048 | 4 | dev 20321–20324 |
| Confirmatory | 8,384 | 32 | 19321–19324 |

262 configs: 2 ion hardware types × 10 scenarios × 6 feedback arms × 2 test rates, plus kg and baselines.

## Adversarial review before the pilot (`REVIEW_30.md`) and changes
The reviewer confirmed Theorem 2's proof steps, predictability, the factor bounds, the spending, the per-user union, no double counting, and the validity of the plug-in and hybrid checks.

**Fixed blockers**
1. **kgMCa overclaimed.** The always-on guarantee now needs (B2) from t = 0 (no onset). kgMCa under late onset is pre-registered as an expected failure.
2. **A false alarm before the onset breaks (B2).** (B2) is now stated after the *first* alarm, Corollary O adds β, and the cell L0.044F was added.
3. **"No debt" was false in the near-exact regime.** The plug-in loses about 1.1 nats per 1,000 tests when q − p ≈ 0.004. The claim is now "limited debt", the hybrid is the default, and a detector table is in THEORY_30.
4. **Model fidelity could exceed 1.** This affected Studies 28–29 for 2.7–63% of attempts. The offset now goes into the truth. The effect is disclosed as a limitation of the Study 28–29 detection power.

**Major findings, all addressed**
- heterogeneous-offset cell added;
- static baseline added;
- warm-up-inclusive post-alarm and whole-run counters added;
- spending index off by one fixed (the first window is k = 1);
- check restarted when the margin falls by 0.01;
- H̄ recorded (mean hold over attempts, dev network 0) and φ capped at 3;
- θ_max justified from the measured gaps (out-of-B4 not tested).

## Dev smoke tests (disclosed; not evidence)
Two batches of smoke runs, both on dev network 0 or 1.

**Before the review fixes** (offset added to the model):
- **kgMCp, forced alarm at 0.044:** 0 bad pairs; margin 0.057 vs offset 0.044; 65% of oracle.
- **L0.044:** the mixture alarmed at epoch 52.8 and the plug-in at 60.0. In this near-exact regime the plug-in is not faster.
- **kgMCa, no stressor:** 61% of oracle.

**After the fixes** (offset in the truth):
- **ionproj, o0.044, p = 0.2, kgMCh:** alarm at epoch 16; 0 bad pairs after the alarm; margin 0.059.
- **L0.044F, kgMCh:** the false alarm comes before onset, and no second alarm follows in 60 epochs, so 3,942 bad pairs. This is the Corollary O failure mode, now a pre-registered prediction.

**All-paths check:** 71 configs × 8 epochs; every arm and scenario runs.

## Pilot commands
**1. Mac terminal** (copy to PSC, next to `s29`):
```bash
cd ~/Documents/Independent-Study/quantum_grid_router/Files11-EndToEnd-PRX-Claude/prx_work
ssh <psc-user>@bridges2.psc.edu 'cd "$(dirname "$(find /ocean/projects/cis260277p/$USER -maxdepth 4 -type d -name s29 | head -1)")" && tar xzf - && ls -d s30' < s30_pilot.tgz
```

**2. PSC** (log in, then):
```bash
cd "$(dirname "$(find /ocean/projects/cis260277p/$USER -maxdepth 4 -type d -name s29 | head -1)")/s30" && mkdir -p s18c-logs
sbatch --account=cis260277p --array=0-31 --cpus-per-task=16 --time=02:00:00 \
  --export=ALL,S18C_DIR=$PWD,PY=/opt/packages/anaconda3-2024.10-1/bin/python3,S18C_MODULE=study30,S18C_TASKS=tasks_p30.jsonl,S18C_OUT=des_p30_psc,S18C_NSHARDS=32,S18C_LIB=$PWD/../s18c,S26_DIR=$PWD/../s26,S27_DIR=$PWD/../s27 \
  s18c_array.sbatch
```

**3. PSC, when `squeue -u $USER` is empty:**
```bash
/opt/packages/anaconda3-2024.10-1/bin/python3 psc_array_runner.py --merge des_p30_psc
srun -p RM-shared -A cis260277p -n 1 -c 4 -t 00:20:00 /opt/packages/anaconda3-2024.10-1/bin/python3 pilot_summary_30.py des_p30_psc/runs.csv > pilot_summary_30.txt; tail -40 pilot_summary_30.txt
```

**4. Mac terminal** (bring results back):
```bash
cd ~/Documents/Independent-Study/quantum_grid_router/Files11-EndToEnd-PRX-Claude/prx_work/30_closed_loop
ssh <psc-user>@bridges2.psc.edu 'cd "$(dirname "$(find /ocean/projects/cis260277p/$USER -maxdepth 4 -type d -name s29 | head -1)")/s30" && tar czf - des_p30_psc pilot_summary_30.txt' | tar xzf -
```

**Cost estimate**
- Pilot: about 32 × 16 cores × 0.4 h ≈ 200 SU.
- Confirmatory: about 8× more (≈ 1,500 SU). Its job size gets its own approval after the pilot.
