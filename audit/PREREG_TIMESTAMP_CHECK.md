# Pre-registration vs. first confirmatory run: independent timestamps (PSC Bridges-2)

**Sources:**
- `audit/prereg_timestamps.txt`: PSC file-system modification times of each pre-registration file, as uploaded to the cluster.
- `audit/job_history.txt`: Slurm `sacct` records.
- `shard_*_meta.json` in each confirmatory output folder: the start time written by the job itself, together with the code and task-list hashes.

A positive lead means the pre-registration was on the cluster **before** the first confirmatory shard started. Times are UTC.

| Pre-registration | On PSC | First confirmatory shard | Lead (min) | Shards |
|---|---|---|---|---|
| README_C1.md | 2026-10-07 02:34 | 2026-10-07 02:37 | 3 | 16 |
| README_C2.md | 2026-10-07 04:21 | 2026-10-07 04:44 | 23 | 16 |
| README_G1.md | 2026-10-08 15:32 | 2026-10-08 15:46 | 14 | 8 |
| README_G2.md | 2026-10-08 18:44 | 2026-10-08 18:45 | 1 | 8 |
| README_G3.md | 2026-10-08 23:30 | 2026-10-08 23:31 | 1 | 8 |
| README_G4.md | 2026-10-09 00:12 | 2026-10-09 00:13 | 1 | 8 |
| README_G5.md | 2026-10-09 07:09 | 2026-10-09 07:15 | 6 | 8 |
| README_G6.md | 2026-10-09 16:45 | 2026-10-09 16:46 | 1 | 8 |
| README_G7.md | 2026-10-10 01:38 | 2026-10-10 01:39 | 1 | 8 |
| README_P1.md | 2026-10-07 05:36 | 2026-10-07 05:58 | 22 | 8 |
| README_S1.md | 2026-10-08 18:44 | 2026-10-08 18:45 | 1 | 16 |
| README_v10b.md | 2026-10-05 15:35 | 2026-10-05 15:39 | 4 | 20 |
| README_v10.md | 2026-10-05 14:54 | run on the Mac, not PSC | — | 0 |
| README_v11.md | 2026-10-05 15:02 | 2026-10-05 15:20 | 19 | 8 |
| README_v12.md | 2026-10-05 16:25 | 2026-10-05 16:29 | 4 | 12 |
| README_v14.md | 2026-10-05 18:56 | 2026-10-05 19:07 | 11 | 12 |
| README_v15.md | 2026-10-06 00:40 | 2026-10-06 01:22 | 42 | 8 |
| README_v16.md | 2026-10-06 11:11 | 2026-10-06 11:16 | 5 | 8 |
| README_v17.md | 2026-10-06 11:42 | 2026-10-06 11:46 | 4 | 8 |
| README_v18.md | 2026-10-06 18:23 | 2026-10-06 18:25 | 2 | 8 |
| README_v20.md | 2026-10-07 01:13 | 2026-10-07 01:17 | 4 | 8 |
| README_v5.md | 2026-10-04 05:43 | run on the Mac, not PSC | — | 0 |
| README_v6.md | 2026-10-04 09:26 | run on the Mac, not PSC | — | 0 |
| README_v7.md | 2026-10-05 05:38 | run on the Mac, not PSC | — | 0 |
| README_v8.md | 2026-10-05 13:49 | run on the Mac, not PSC | — | 0 |
| README_v9.md | 2026-10-05 14:44 | run on the Mac, not PSC | — | 0 |
| README_23.md | 2026-10-10 15:22 | 2026-10-10 15:26 | 4 | 16 |
| README_24.md | 2026-10-10 18:31 | 2026-10-10 18:32 | 1 | 40 |

**Result:** in **22 of 22** PSC-run studies, the pre-registration file was on the cluster before the first confirmatory shard started.

**Caveats:**
- A file's modification time records its *last* upload. A later re-upload would make the lead look smaller, never larger, so the check is conservative in that direction.
- Modification times can be set by the account owner. Together with the job-written shard metadata, the Slurm records, the ledger hashes and (from 10 Oct 2026) the public GitHub/Zenodo history, this is strong evidence, not proof.
- Studies v5–v10 ran on the Mac and rely on the ledger alone.
