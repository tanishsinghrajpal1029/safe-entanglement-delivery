# Scoreboard rows for S3D-1 to S3D-3 (pre-registered; 3D repository release v1.0.0)

| Study | Hyp | Tier | Question | Outcome | Key number |
|---|---|---|---|---|---|
| S3D-1 | H1 | primary | Safety (Thm. 2 after an alarm; Cor. 3 always-on) on the 5³ cube, both ion presets | PASS | 0/32 harmed networks in every cell; 0 bad in 3.49 M |
| S3D-1 | H2 | primary | Cube serves more of the hardest near-neighbour requests than both grids (4 comparisons) | FAIL | 1/4 pass (ionproj vs 13×13, +0.091) |
| S3D-1 | H3 | secondary | Delivered fidelity unchanged within ±0.01 | PASS | −0.002 to −0.003 |
| S3D-1 | S1 | secondary (prediction) | Detection carries over (alarm rate within 0.15) | FAIL | ion2020 0.69 vs 0.97; ionproj 0.97 vs 1.00 |
| S3D-1 | S2 | secondary (prediction) | No check, offset 0.044 harms > 10% of served users | PASS | 0.68–0.74 |
| S3D-1 | S3 | secondary (falsification) | Certificate not invalidated | PASS | largest lower bound 0.013 |
| S3D-2 | R1 | primary | Safety at reach on the 10³ cube, three link levels | PASS | 0/32 in every cell; 0 bad in 3.78 M (all lattices) |
| S3D-2 | R2 | primary | Cube serves a larger share of uniform demand than 32×32 and 37×37 (6 comparisons) | PASS | 6/6 |
| S3D-2 | R3 | secondary | Cube / 32×32 ratio ≥ 1.5 | PASS | 2.33 / 2.78 / 3.46 |
| S3D-2 | R4 | secondary | Advantage survives the always-on margin | PASS | 3/3 |
| S3D-2 | S1 | secondary (prediction) | No check, offset 0.044 harms > 10% | PASS | 0.65–0.77 |
| S3D-2 | S2 | secondary (falsification) | Certificate not invalidated | PASS | largest lower bound 0.014 |
| S3D-3 | K1 | primary | Cube serves more than the 32×32 grid with diagonals, three link levels | PASS | 1.16 / 1.38 / 1.71 |
| S3D-3 | K2 | primary | Safety on the grid with diagonals | PASS | 0/32 in every cell; 0 bad in 1.52 M |
| S3D-3 | K3 | secondary | Diagonals help a plain grid | PASS | 2.0× at every level |
| S3D-3 | K4 | secondary | Cube's lead over the grid with diagonals survives the always-on margin | FAIL | not significant at link fidelity 0.97 (+0.0012 [−0.0008, +0.0032]); passes at 0.98, 0.99 |
| S3D-3 | S1 | secondary (prediction) | No check, offset 0.044 harms > 10% | PASS | 0.64–0.68 |
| S3D-3 | S2 | secondary (falsification) | Certificate not invalidated | PASS | largest lower bound 0.009 |

**Counts:** 6 primary (5 passed, 1 failed); 12 secondary (10 passed, 2 failed). With these, the manuscript's totals are 95 primary (83 passed, 12 failed) and 68 secondary (58 passed or confirmed, 9 failed, 1 unclear).
