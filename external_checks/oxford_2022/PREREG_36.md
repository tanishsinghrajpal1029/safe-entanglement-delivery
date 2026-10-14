# Study 36, "Oxford": pre-registration (14 Oct 2026)

**Written before any data value was read.** Only the header comment, the column names and the row count have been seen (§2). Commit this file and the locked scripts publicly **before** running `analyze_36.py`.

## 1. Data and why it matters
- **Data:** shot-by-shot events of the 1,920,000-round characterisation run of Nadlinger et al., *Experimental quantum key distribution certified by Bell's theorem*, Nature 607, 682 (2022), doi:10.1038/s41586-022-04941-5. These are the raw data of the paper's Fig. 3, shown per round in Fig. S4.
- **Provenance:** exported and shared privately by D. P. Nadlinger on 14 Oct 2026, in reply to the request in E98.
  - File: `link-quality-events.csv.xz`, sha256 fae103d8bfdb179b.
  - **Not redistributed.** It is kept outside the repository. Results will be shared with the authors before any submission, and permission to report has been asked.
- **Why it matters:** this is the first dataset in the project with **one record per pair, in time order, where the choice to test or keep is randomised per pair after the herald**:
  - Bob chooses the round type with a quantum random number generator after the heralding signal (paper, Methods/S4);
  - in this run the test probability is γ = 1/2;
  - in test rounds the settings are uniform;
  - key rounds use x = 0, y = 2.
- **This matches the assumptions of Prop. C1** (fresh, private test choice made after delivery). It allows the first real-data run of an **anytime-valid certificate on the kept pairs**, and a real-data check of whether link noise is **persistent**, the stressor that broke every model-based arm in S26.

## 2. What was seen before this pre-registration
- **The header comment:**
  - one row per heralded Bell pair, in chronological order;
  - 96 ARTIQ chunks, 1,920,000 events, 8.53 h, 15 May 2021;
  - the column definitions.
- **The column names, and the row count of 1,920,000.**
- **The paper** (arXiv:2109.14600v2): for this run S = 2.677(6) and Q = 1.44(2)%; γ = 1/2; the settings and the timing of the round-type choice; the Fig. 3 caption ("stable link performance"; moving averages over 100,000 rounds; vertical steps mark ion loss and recalibration). The Fig. 3 image itself was not looked at.
- **Synthetic data only** (§7).

## 3. Gates (a failure stops the run)
| Gate | Check |
|---|---|
| **G1, design** | 1,920,000 rows; test-round fraction 0.5 ± 0.01; every key round has x = 0; time non-decreasing; each of the four test settings at 0.25 ± 0.01 of test rounds; outcomes in {0, 1} |
| **G2, reproduction** | Of the 8 CHSH conventions (which correlator carries the minus sign, × Alice's outcome inversion), exactly one gives S within 0.02 of the published 2.677. It **fixes the convention.** With that convention, the key-round QBER is within 0.2 points of 1.44%. |

## 4. Primary hypotheses (2)
**O1: anytime certificate on the kept (key) pairs.**
- **Method:**
  - L_i = 1 if test round i loses the CHSH game under the fixed convention.
  - For the conditional loss probability q_i of pair i, a pair measured at the nominal settings (trusted measurements) has fidelity F_i ≥ √2(1 − 2q_i) to the maximally entangled state of the measurement frame. This holds for any two-qubit state.
  - Because the test/keep choice is independent of the pair, d_i = (1−p)T_iL_i − p(1−T_i)q_i is a martingale difference with range 1.
  - Hoeffding supermartingales on a grid of 20 values of λ (level α/20 each, α = 0.05) give, simultaneously for all t: p·Q_K(t) ≤ (1−p)·Σ_{i≤t} T_iL_i + B_t.
  - The certified bound is F_L(t) = √2(1 − 2·Q_K^ub(t)/K_t).
- **PASS** if the final F_L > 0.9, i.e. the kept pairs certify the manuscript's threshold 0.9 from real data.
- **Prediction: PASS** (about 0.93 if S is near 2.68).

**O2: link noise beyond binomial.**
- **Method:** the CHSH loss rate per chunk (96 blocks of 20,000 rows, about 10,000 test rounds each). Pearson χ² for heterogeneity, df = 95, one-sided.
- **PASS** (over-dispersion detected) if p < 0.05.
- **Prediction: PASS,** given ICFO and USTC, and the recalibration steps mentioned in the caption. A FAIL would mean the link is binomially stable at this scale, which is informative too.

## 5. Secondary
- **S1: consistency on the kept pairs.** At every t with at least 1,000 kept pairs, F_L(t) ≤ 1 − (kept-pair Z-error fraction)/2 (because 1 − F ≥ e_Z/2). **Prediction: PASS.**
- **S2 (descriptive): device-independent bound.** Kaniewski's self-testing bound F_ext ≥ ½ + ½(S − β*)/(2√2 − β*), with β* = (16 + 14√2)/17, applied to the same anytime S bound.
- **S3: persistence.** Lag-1 autocorrelation of the chunk loss rates; one-sided permutation test (10,000 permutations, seed 36). **PASS** if p < 0.05. **Prediction: PASS.**
- **S4 (descriptive):** QBER dispersion across chunks.

## 6. Assumptions and limits (stated now)
- **Trusted measurements at the nominal settings** for O1 and S1:
  - Alice measures two orthogonal axes;
  - Bob measures at ±π/4 between them, with φ calibrated per click pattern;
  - readout error below 10⁻³ and gate error about 5×10⁻⁴ (paper).
  - Settings that are slightly off nominal are not covered. S2 needs no trust.
- **Fidelity target:** the maximally entangled state of the measurement frame. Because the bound is linear in q, it is valid for the average conditional fidelity of the kept pairs.
- **One device pair, one run of 8.5 h. Both qubits are trapped ions** (two Oxford Sr⁺ nodes linked by optical fibre).
- **Not a closed-loop test:** no physics model of the link is supplied, so Theorem 2 is not exercised.
- **The chunk is fixed** as the block for O2 and S3. No other block size is tested.
- **The convention is selected by reproducing the published S** (disclosed). Candidate values are reported.

## 7. Synthetic pre-run (`synth_36.py`, seed 36, output `synth_36.txt`)
| Check | Result |
|---|---|
| **O1 coverage:** rate of any violation over the run (bar ≤ 0.05) | **0.0000** in every scenario: stationary, drift 0.96→0.90, three random steps, random walk; n = 200,000 (400 runs) and 1,920,000 (20 runs); adaptive adversary (200 runs). The bound is conservative. |
| **O1 margin at the end:** true bound − F_L | 0.044 at n = 200,000; **0.014 at n = 1,920,000** |
| **O2 false positive** under a stationary link (1,000 runs) | **0.051** |
| **S3 false positive** | 0.034 |
| **Power,** AR(1) ρ = 0.9 chunk noise with relative sd 1% / 2% / 4% | O2: 0.28 / 0.88 / 1.00; S3: 0.35 / 0.87 / 1.00 |

**End-to-end test** (`make_synth_csv_36.py`; planted convention: minus sign on (1,1), Alice inverted):
- G2 recovered the convention.
- O1 F_L = 0.934, against a point value of 0.947.
- In the **stationary** file, O2 gave **p = 0.038**: a false positive of the kind expected 5% of the time. A single O2 PASS is therefore weak evidence. It is reported with the dispersion ratio and the excess fluctuation, not only p.
- With planted drift: O2 p = 2×10⁻⁴⁵ and S3 lag-1 = +0.70.
- A wrong test fraction stops at G1.

## 8. Procedure
1. Commit and push this file and the locked scripts.
2. Claude runs `python3 analyze_36.py link-quality-events.csv.xz > results_36.txt` once, in the cloud workspace where the file was uploaded. The run prints its UTC start time and the data hash.
3. Results go to the ledger. Any deviation is labelled exploratory.

## 9. Locked files (sha256, first 16)
| File | sha |
|---|---|
| `oxford_core.py` | 0ab19cc02e82ad96 |
| `analyze_36.py` | aa8001b58560851d |
| `synth_36.py` | 17f3828a1776f636 |
| `make_synth_csv_36.py` | 9577cede5a0997b6 |
| `synth_36.txt` | 58ad84b0e02f05a9 |
| data `link-quality-events.csv.xz` (not in the repository) | fae103d8bfdb179b |
