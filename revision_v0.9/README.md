# Revision v0.9: other topologies (S3D-1 to S3D-3) for manuscript v0.9

Manuscript v0.9 adds the safety results of three pre-registered topology studies: cubes of 5³ and 10³ nodes, a 32 × 32 grid with diagonal links, and square grids of side 11–37, with routing sets of up to U_max = 104 links (Appendix B.5 "Other topologies", Table 10, one row of Table VIII, and the Topology limitation).

The studies themselves (simulator fork, pre-registrations, gate jobs, run outputs, analyses, ledger) live in their own repository, whose commit history carries the pre-registration evidence:
**https://github.com/tanishsinghrajpal1029/quantum-3d-network**, release v1.0.0 (commit `724252b`), **DOI 10.5281/zenodo.23467683**.
This folder keeps copies of the three locked analysis outputs and a script that rebuilds every S3D number quoted in the manuscript from them. Nothing here is a new simulation.

| File | What it is |
|---|---|
| `s3d_analysis/analysis_3d{1,2,3}.txt` | Copies of `sim/evidence/analysis_3d{1,2,3}.txt` from the 3D repository; hashes in `s3d_analysis/SHA256SUMS` |
| `s3d_table10.py` | Rebuilds Table 10 (cells, harmed networks, bad / guarded deliveries, U_max) and the detection numbers (22 vs 31 of 32). Command: `python3 revision_v0.9/s3d_table10.py revision_v0.9/s3d_analysis` |
| `s3d_table10_output.txt` | Its output for the manuscript; re-running it reproduces this file exactly |
| `SCOREBOARD_S3D.md` | Every pre-registered S3D hypothesis with its verdict, failures included |
| `../audit/s3d_2026-10-19/` | Copies of the 3D repository's timing records: GitHub repository activity log (server-side push times), events feed, PSC `sacct` job times |

## Pre-registration timing (UTC; manuscript Table "Three levels of pre-registration evidence", Level 1b)
| Study | Pre-registration pushed | Gate job submitted | First confirmatory shard |
|---|---|---|---|
| S3D-1 | `fc3660d`, 18 Oct 05:13:42 | 05:46:16 | 21:07:07 |
| S3D-2 | `7e3dc97`, 19 Oct 02:27:40 | 02:28:23 | 02:41:55 |
| S3D-3 | `1fe2dba`, 19 Oct 04:29:40 | 04:30:32 | 04:42:12 |

The 3D repository was **private** when these pushes were made and was made public on 19 Oct 2026, which is why the manuscript lists these studies at their own level (1b) rather than with the studies of this repository. PSC times are recorded in EDT (UTC−4, checked with `date`) and converted.

## Summary of results (details in Appendix B.5)
- **Safety:** in each of 36 lattice × hardware × arm cells (32 networks each), no network had a harmed user (bound 8.9% per cell); 0 of 8,793,454 guarded deliveries were bad.
- **Detection:** on the 5³ cube with ion2020 hardware the check alarmed in 22 of 32 networks at offset 0.044, against 31 of 32 on an 11 × 11 grid (S3D-1's detection prediction failed; cause not established).
- **Lattice comparisons** (not part of this manuscript's claims; reported in the 3D repository): the cube served more of the hardest near-neighbour requests than both grids in 1 of 4 comparisons (failed); under uniform demand it served 2.3–3.5× the share of a 32 × 32 grid and 1.16–1.71× that of the grid with diagonals.

## Correction in v0.9.1 (19 Oct 2026)
After a targeted review, the wording of the S3D certificate tests and of the pair-level bound was corrected here (`SCOREBOARD_S3D.md`), in the 3D repository's results documents (its release v1.0.1) and in manuscript v0.9 (Appendix B.5): the falsification tests did not reject the nominal 5% violation rate, and violations did occur; the pooled bad-pair bound assumes independent deliveries and is not used for inference. The safety summary above is unchanged: it states the network-level bound and counts bad deliveries. Analysis copies, script and output are unchanged. Ledger E180.

