# Study 34 ("other grids"): design and dev pilot (12 Oct 2026)

**Status:** dev pilot only. The pre-registration (bars, locked `analyze_34.py`) follows the pilot and is committed before any confirmatory job.

## Why
Every closed-loop result so far (Studies 28–32) is on one 5×5 grid; only the guard alone was run at 30×30 (G3). This study asks whether the provable closed loop behaves the same on larger networks. It is a scaling sanity check, as the review called it: per-link calibration data, the offset and the check's test rate do not change with grid size, so most mechanisms predict that results carry over. The matched-exposure cells are the real test of size.

## Design (`study34.py`; reuses Study 32's network and arms, unchanged)
- **Grids:** 5×5 (reference, fresh seeds), 10×10 (180 links) and 30×30 (1,740 links). Each grid runs in its own job (`S34_GRID`).
- **Load variants:**
  - `base`: the same total request rate on every grid.
  - `u`: matched exposure, on 10×10 and 30×30. Demand is restricted to a random subset of users of the 5×5 size (204 / 340).
  - `m3`: three times the request rate, on 5×5 and 30×30.
- **Scenarios:** no offset; offset 0.044 (in the true state); forced alarm at the 8th test.
- **Arms:**
  - kg (no check);
  - kgMChN (hybrid check plus the current-look bound) at p = 0.1 and 0.2;
  - kgMCa (always-on) at p = 0.1.
- **Size:**

| | Tasks | Networks per cell | Seeds |
|---|---|---|---|
| Pilot | 616 (176 + 176 + 264) | 4 | dev 20341–20344 |
| Confirmatory | 4,928 (1,408 + 1,408 + 2,112) | 32 | 19341–19344 |

- **Metrics added because of review B1:**
  - risk per served user (`users_bad_served / users_served`);
  - the per-delivery bad rate.

  These are needed because users dilute about 60× on 30×30 at the base rate.

## Review (`REVIEW_34.md`)
**Confirmed:**
- the grid size propagates to every module (link-count assert holds at 1,740);
- `m3` is applied consistently;
- per-link levels stay valid. Expected cost: about +0.001 on the margin from the larger union over links;
- memory is about 1.4 GB per worker on 30×30;
- run time is about 11 s per epoch at `m3`.

**Fixed:**
- **B1 (dilution):** served-user and per-delivery metrics added, plus the matched-exposure variant `u`.
- **M1:** framed as a scaling sanity check, with predictions per mechanism.
- **M2:** `m3` added on 5×5, so a rate effect is separable from a grid effect.
- **Minor:** `S34_GRID` is checked against the task; `S32_DIR` is exported.

## Smoke runs (disclosed)
- All three grids and all three variants run.
- 10×10: kgMChN with a forced early alarm ran correctly. The `u` variant gives 204 users, of which 89 were served in 6 epochs.
- 30×30 kg at offset 0.044: 242 of 429 delivered pairs were bad over 6 epochs.

## Pilot commands
1. **Mac terminal:**
```bash
cd ~/Documents/Independent-Study/quantum_grid_router/Files11-EndToEnd-PRX-Claude/prx_work
ssh <psc-user>@bridges2.psc.edu 'cd /ocean/projects/cis260277p/<psc-user> && tar xzf - && ls -d s34' < s34_pilot.tgz
```
2. **PSC** (three jobs, one per grid):
```bash
cd /ocean/projects/cis260277p/$USER/s34 && mkdir -p s18c-logs
for G in 5 10 30; do
  N=16; [ $G = 30 ] && N=32
  sbatch --account=cis260277p --array=0-$((N-1)) --cpus-per-task=16 --time=03:00:00 \
    --export=ALL,S34_GRID=$G,S18C_DIR=$PWD,PY=/opt/packages/anaconda3-2024.10-1/bin/python3,S18C_MODULE=study34,S18C_TASKS=tasks_p34_g$G.jsonl,S18C_OUT=des_p34_g$G,S18C_NSHARDS=$N,S18C_LIB=$PWD/../s18c,S26_DIR=$PWD/../s26,S27_DIR=$PWD/../s27,S30_DIR=$PWD/../s30,S32_DIR=$PWD/../s32 \
    s18c_array.sbatch
done
```
3. **PSC, when `squeue -u $USER` is empty:**
```bash
for G in 5 10 30; do /opt/packages/anaconda3-2024.10-1/bin/python3 psc_array_runner.py --merge des_p34_g$G; done
/opt/packages/anaconda3-2024.10-1/bin/python3 pilot_summary_34.py des_p34_g5/runs.csv des_p34_g10/runs.csv des_p34_g30/runs.csv > pilot_summary_34.txt; head -3 pilot_summary_34.txt
```
4. **Mac terminal:**
```bash
mkdir -p ~/Documents/Independent-Study/quantum_grid_router/Files11-EndToEnd-PRX-Claude/prx_work/34_grids && cd ~/Documents/Independent-Study/quantum_grid_router/Files11-EndToEnd-PRX-Claude/prx_work/34_grids
ssh <psc-user>@bridges2.psc.edu 'cd /ocean/projects/cis260277p/<psc-user>/s34 && tar czf - des_p34_g5 des_p34_g10 des_p34_g30 pilot_summary_34.txt' | tar xzf -
```

**Cost estimate:**
- Pilot: about 80 SU.
- Confirmatory: about 500 SU. The 30×30 tasks dominate: 10–17 min each at `m3`.
