# Pre-registration timeline

Every confirmatory study was written down **before** its confirmatory run. The pre-registration recorded:
- the hypotheses and pass bars;
- the locked analysis script, tested on synthetic data;
- the task list;
- the sha256 of the code.

Dev pilots used separate seeds and are disclosed in each pre-registration.

**Independent evidence of order** (beyond our own ledger, `audit/EVIDENCE_LEDGER.md`):
- each confirmatory run's `shard_*_meta.json` records the module and task-list sha256 and the start time, written by the cluster job itself;
- the pre-registration files were uploaded to PSC Bridges-2 before each job, and their file times and Slurm job records exist there;
- this public repository fixes everything from its first commit onward.

The table below is generated from the files in this repository (sha256, first 16 hex characters).

| Folder | Pre-registration | sha | Results document | Confirmatory runs.csv |
|---|---|---|---|---|
| study18c_controller_and_guard | README_C1.md | 547ec9df6bc2e021 | — | des_c1_psc/runs.csv `49b52dbbaf717cdb` |
| study18c_controller_and_guard | README_C2.md | 1f343126d247c3f4 | — | des_c2_psc/runs.csv `4bca8492ee3a6785` |
| study18c_controller_and_guard | README_G1.md | 265d329d8b4f420b | — | des_g1_psc/runs.csv `e57bdd53c04bf7c8` |
| study18c_controller_and_guard | README_G2.md | 382d1562cc20035d | — | des_g2_psc/runs.csv `46d09d4cd0fbcf1d` |
| study18c_controller_and_guard | README_G3.md | 4be553061b3e45e7 | — | des_g3_psc/runs.csv `e9cd30683b249213` |
| study18c_controller_and_guard | README_G4.md | f6edd660ab8b0174 | — | des_g4_psc/runs.csv `015ec7b242ab7db6` |
| study18c_controller_and_guard | README_G5.md | 19877104e88f0ca1 | des_g5_psc/G5_RESULTS.md | des_g5_psc/runs.csv `c992739821a87fb2` |
| study18c_controller_and_guard | README_G6.md | 38cd297730146d72 | des_g6_psc/G6_RESULTS.md | des_g6_psc/runs.csv `9a980977de17635e` |
| study18c_controller_and_guard | README_G7.md | d88533e3494ee940 | des_g7_psc/G7_RESULTS.md | des_g7_psc/runs.csv `5157931a11f3410f` |
| study18c_controller_and_guard | README_P1.md | 9caf1736d056fa16 | — | des_p1_psc/runs.csv `0880a63403b7d435` |
| study18c_controller_and_guard | README_S1.md | 7660a194cd28ff35 | — | des_s1_psc/runs.csv `2c14797e183d4ba8` |
| study18c_controller_and_guard | README_v10.md | c96b9857c7617523 | — | des_v10b_psc/runs.csv `a25bfc2c29a8b3a7` |
| study18c_controller_and_guard | README_v10b.md | 99786b016affd1f7 | — | des_v10b_psc/runs.csv `a25bfc2c29a8b3a7` |
| study18c_controller_and_guard | README_v11.md | afabde38d01dd70d | — | des_v11_psc/runs.csv `b1507c58249ef0e7` |
| study18c_controller_and_guard | README_v12.md | a36f9d0fd40add07 | — | des_v12_psc/runs.csv `5a03c05dcdc1d87a` |
| study18c_controller_and_guard | README_v14.md | 807e83d988ba0ef5 | — | des_v14_psc/runs.csv `a9e305d098bd0714` |
| study18c_controller_and_guard | README_v15.md | fddf36324e9786c3 | — | des_v15_psc/runs.csv `47a2e4bbad7274fd` |
| study18c_controller_and_guard | README_v16.md | af35f75ece3d369a | — | des_v16_psc/runs.csv `44cd1014012262d3` |
| study18c_controller_and_guard | README_v17.md | 1400488c7d54a028 | — | des_v17_psc/runs.csv `696020b0005701fa` |
| study18c_controller_and_guard | README_v18.md | ad3517178c87795d | — | des_v18_psc/runs.csv `b818316cae60ee45` |
| study18c_controller_and_guard | README_v19.md | 75ff4ece230a4da5 | — | — |
| study18c_controller_and_guard | README_v20.md | c39c9ef62bf7f8a4 | — | des_v20_psc/runs.csv `58cc2295383ced45` |
| study18c_controller_and_guard | README_v5.md | d1387b3aac322ef7 | — | — |
| study18c_controller_and_guard | README_v6.md | 11c32b674b9e7a27 | — | — |
| study18c_controller_and_guard | README_v7.md | 3424d643409beff5 | — | — |
| study18c_controller_and_guard | README_v8.md | 503dbae34ecac3dc | — | — |
| study18c_controller_and_guard | README_v9.md | 875114fb2252d3ea | — | — |
| study23_ai_rl_guard | README_23.md | 742352d154d84065 | RESULTS_23.md | des_s23_psc/runs.csv `7c398c48ef653d8b` |
| study24_ai_v2_hardware | README_24.md | 952a5c51ff80135c | RESULTS_24.md | des_s24b_psc/runs.csv `9f8633ed3e590f8f`, des_s24_psc/runs.csv `71e3cc31467c2efb` |
| external_checks/innsbruck_230m | PREREG_INNSBRUCK_STAGE1.md | 568c7b973f8e94f4 | — | — |
| external_checks/innsbruck_230m | PREREG_INNSBRUCK_STAGE2.md | 00356d058c4e233c | — | — |
| study25_realism | README_25.md | b9c1718afa201133 | RESULTS_25.md | des_s25_psc/runs.csv `3826490aaf20734b`, des_s25d_psc/runs.csv `7bb3996c177a281d` (locked files on cluster before submission; commit `370a823` timestamped 2 min after Block A start — ledger E102) |
| study26_certified | README_26.md | 58cccbb64d383638 | RESULTS_26.md | des_s26_psc/runs.csv `b31b9c98b934a16e` (commit `fc22091` 2 min 15 s before the first job; ledger E110) |
| study27_certification | README_27.md | dd6335aad65a910b | pending | pending (pushed **before** the confirmatory run) |
| external_checks/innsbruck_230m/stage3_cert | PREREG_INNSBRUCK_CERT.md | 9f9463dc3267f4ab | STAGE3_RESULT.md | not blind (counts seen earlier); method fixed before computing (E111–E112) |

Where "Results document" is "—", the confirmatory outcome is recorded in `audit/EVIDENCE_LEDGER.md` (entries E35–E89), next to the run hashes.
