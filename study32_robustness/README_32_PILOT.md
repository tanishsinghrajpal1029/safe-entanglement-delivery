# Study 32 ("re-opening and robustness"): design and dev pilot (11 Oct 2026)

**Status:** dev pilot only. The pre-registration (hypotheses, bars, locked `analyze_32.py`) follows the pilot and is committed before any confirmatory job. Theory: `THEORY_32.md`.

## Why
Two referee items remained open, plus one episode from Study 30:
- **COULD 26 (Study 30, network 11).** The offset bound is a running minimum. One unlucky early look kept it below the true offset for the rest of the run (2,075 bad pairs).
- **M16/E3 (robustness).** Nothing has varied the threshold τ, the calibration fraction, or the hardware for the closed loop. Study 30 was ion-only.

## Design (`study32.py`; builds on Study 30's network and code, unchanged)

| Block | Question | Cells | Arms |
|---|---|---|---|
| **R** | Does a bound with no intersection (U′, Remark R) recover from a miscoverage, and is it still valid? | ion2020 and ionproj; p = 0.1 and 0.2; '-', o0.044, L0.044, **L0.044F** (false alarm before onset: a natural failure of B2), and **o0.044FM** (forced early alarm + forced miscoverage: all tests before the window's first look are recorded as passes) | kgMCh (running minimum) vs **kgMChN** (no intersection) |
| **E** | Robustness of Theorem 2 and Corollary 3 | ion2020 and ionproj; p = 0.1; '-' and o0.044; with τ = 0.85, τ = 0.92, or **less calibration data** (fraction 0.1 instead of 0.3; service rate unchanged); paired base controls for kg and kgMCa. Cells with no good pairs for the oracle (ion2020, τ = 0.92, o0.044) are report-only | kg, kgMCh, kgMCa |
| **T** | **Descriptive:** the limit on thin hardware | nv2 and siv (native τ 0.8); '-' and o0.044; p = 0.1 and 0.2. Only tens of tests in 90 epochs, so the check is not expected to alarm, and the always-on margin (starting at 0.10) is not expected to deliver | kg, kgMCh, kgMCa |

- **Not varied:** network topology. The correlated-network generator is built for the 5×5 grid; this is stated as a limitation.
- **Size:**

| | Tasks | Networks per cell | Seeds |
|---|---|---|---|
| Pilot | 416 | 4 | dev 20331–20334 |
| Confirmatory | 3,328 | 32 | 19331–19334 |

  104 configs in total.
- **New outputs:** for window 1 of the bound, the number of tests forced to pass (`npois`), looks, looks below θ, the first look below θ, the recovery look and the tests to recover (constant-offset cells), plus alarm counts (re-alarms).

## Adversarial review (`REVIEW_32.md`) and changes
- **B1:** Block T cannot exercise the loop on thin hardware. It is now descriptive (predictions only).
- **M1:** ion2020 at τ = 0.92 with o0.044 has an oracle count of 0. That cell is report-only, behind a gate of oracle > 0.
- **M2:** direct recovery and coverage diagnostics added.
- **M3:** L0.044F added to Block R.
- **M4:** paired base controls added to Block E.
- **Minor:** Remark R is credited as standard (Howard et al.); the restart behaviour is described correctly; the calibration cell is relabelled "less calibration data"; the pilot summary uses an oracle gate.
- **Verified:** the Remark R proof, bounded restarts, the overrides (τ, calibration) and the bound swap.

## Checks before the pilot (disclosed)
- **All-paths check:** all 38 distinct configs ran for 8 epochs.
  - τ = 0.95 delivered almost nothing on ion2020, so it was replaced by 0.92 before the pilot.
  - SiV delivers nothing in 8 epochs. That is expected: thin hardware with a 3-epoch warm-up.
- **Full-length smoke run** (ion2020, o0.044FM, p = 0.2, dev network 0):
  - **Running minimum:** U stuck at about 0 (mean post-alarm margin 0.0003). 4,225 of 7,514 post-alarm pairs were bad, until the check alarmed again.
  - **No intersection:** recovered within the warm-up. 122 bad post-alarm pairs, none after warm-up. Margin 0.051.
- **First forcing design rejected:** poisoning only the first 150 tests did not force a miscoverage, because the first look came after about 480 tests. The forcing was changed to "all tests before the first look".
- **Toy check:** see THEORY_32.md.

## Also in this round (computation, not pre-registered): fixed-K vs anytime certificate (`../s33/fixedk.py`)
Kept pairs needed to certify τ = 0.9 at α = 0.05:

| p | C1 (anytime) | Best single bet, tuned for that F and K | Converse floor (perfect pairs) |
|---|---|---|---|
| 0.05 | 1,404 | 870 | 720 |
| 0.1 | 678 | 420 | 330 |
| 0.2 | 315 | 195 | 140 |

- Results above are for perfect pairs (F = 1). At F = 0.97 and 0.95 the ratio C1 / fixed is 1.5–1.75.
- The price of not planning K or F in advance is therefore about 1.6× (the 8-bet mixture). A fixed plan with an oracle-chosen bet comes within 1.2–1.4× of the converse.

## Pilot commands
1. **Mac terminal:**
```bash
cd ~/Documents/Independent-Study/quantum_grid_router/Files11-EndToEnd-PRX-Claude/prx_work
ssh <psc-user>@bridges2.psc.edu 'cd /ocean/projects/cis260277p/<psc-user> && tar xzf - && ls -d s32' < s32_pilot.tgz
```
2. **PSC:**
```bash
cd /ocean/projects/cis260277p/$USER/s32 && mkdir -p s18c-logs
sbatch --account=cis260277p --array=0-31 --cpus-per-task=16 --time=02:00:00 \
  --export=ALL,S18C_DIR=$PWD,PY=/opt/packages/anaconda3-2024.10-1/bin/python3,S18C_MODULE=study32,S18C_TASKS=tasks_p32.jsonl,S18C_OUT=des_p32_psc,S18C_NSHARDS=32,S18C_LIB=$PWD/../s18c,S26_DIR=$PWD/../s26,S27_DIR=$PWD/../s27,S30_DIR=$PWD/../s30 \
  s18c_array.sbatch
```
3. **PSC, when `squeue -u $USER` is empty:**
```bash
/opt/packages/anaconda3-2024.10-1/bin/python3 psc_array_runner.py --merge des_p32_psc
/opt/packages/anaconda3-2024.10-1/bin/python3 pilot_summary_32.py des_p32_psc/runs.csv > pilot_summary_32.txt; head -5 pilot_summary_32.txt
```
4. **Mac terminal:**
```bash
cd ~/Documents/Independent-Study/quantum_grid_router/Files11-EndToEnd-PRX-Claude/prx_work/32_robustness
ssh <psc-user>@bridges2.psc.edu 'cd /ocean/projects/cis260277p/<psc-user>/s32 && tar czf - des_p32_psc pilot_summary_32.txt' | tar xzf -
```

**Cost:** pilot about 60 SU; confirmatory about 300 SU.
