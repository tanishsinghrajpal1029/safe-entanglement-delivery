# Revision v0.8: re-analysis scripts for manuscript v0.8

These scripts re-analyse existing records only. Nothing here is a new experiment or a new simulation, and nothing here was pre-registered: the manuscript labels this material as re-reporting or exploratory. Run them from the repository root. The study folders they read are already in this repository.

| Script | What it produces | Command |
|---|---|---|
| `cluster_bounds.py` | Table IV of the manuscript: harmed users, runs and networks, with one-sided 95% Clopper–Pearson bounds. Writes `cluster_rows.tex`. | `python3 revision_v0.8/cluster_bounds.py .` |
| `cluster_strata.py` | Design check (runs per network) and per-stratum bounds; the "worst stratum" column. | `python3 revision_v0.8/cluster_strata.py .` |
| `replay_ibm.py` | Replays the recorded IBM outcomes of S31 and S31b using their frozen schedule, certificate and checks. It reproduces the stored F_decl, certificate and alarm indices, then writes the trajectories in `ibm_traj.json`, used for Fig. 6(a, b). | `python3 revision_v0.8/replay_ibm.py` |
| `make_figs_v08.py` | Figs 1 and 3–6, with 95% bootstrap intervals over networks. Also prints the plotted values (`figvals.json`). | `cd revision_v0.8 && python3 make_figs_v08.py .. ibm_traj.json trajectory_36.csv` |
| `trajectory_36.py` | Time course of the pre-registered S36 (Oxford) certificate, for Fig. 6(c). | Needs the Oxford record, which is **not redistributed**; data available from the authors of Nadlinger et al. (2022). Without it, `make_figs_v08.py` skips Fig. 6. |

Outputs from the run used for the manuscript are kept next to the scripts: `cluster_bounds_output.txt`, `cluster_strata_output.txt`, `ibm_traj.json`, `figvals.json`. Re-running the scripts in this repository reproduced all four exactly.

## Audit records for this revision (in `audit/`)

| File | Contents |
|---|---|
| `github_push_events_2026-10-16.json` | GitHub's server-side PushEvent records. The events API keeps them for only 90 days, so they are archived here. |
| `github_push_times_2026-10-16.txt` | The same push times as a readable list. |
| `github_repo_meta_2026-10-16.json` | Repository metadata: created 2026-10-10 19:28 UTC, public. |
| `ibm_job_times.json` | IBM job records of S31 and S31b, fetched read-only with `study31b_hardware_detector/ibm_job_times.py`. Each job was created after its pre-registration push: by 913 s and 29 s. |
