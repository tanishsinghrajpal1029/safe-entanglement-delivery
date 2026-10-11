# Innsbruck Stage 3 result: model-free fidelity certificate on real ion–photon data (11 Oct 2026)

**Pre-registration:** `PREREG_INNSBRUCK_CERT.md` (9f9463dc), ledger E111.
**Script:** `innsbruck_cert.py` (7b282350), run unchanged.
**Input:** `stage1_counts.csv` (8a661f7b), produced by the frozen Stage 1 decoder.
**Output:** `innsbruck_cert_result.json`, `innsbruck_cert_output.txt`.

**Headline (target Φ⁺, mapping M2):**

| | Value |
|---|---|
| Point estimate F̂ | **0.9139** |
| **Certified lower bound F_L** | **0.8867** (95%, simultaneous over all 8 candidate targets) |

**Per-basis error counts (pooled detector-swapped scans):**

| Basis | Errors | Rate | 95% upper bound (α/24) |
|---|---|---|---|
| X | 170 / 2,355 | 0.072 | 0.092 |
| Y | 144 / 2,406 | 0.060 | 0.078 |
| Z | 97 / 2,411 | 0.040 | 0.056 |

## Verdicts
- **R1-A (primary): PASS.** F_L = 0.887 > 1/2. Heralded ion–photon entanglement is certified at 95% without any state model or reconstruction, under the stated assumptions (T, FS, H, S).
- **R1-C (diagnostic): PASS.** The detector-swapped scan pairs agree in every basis: Fisher exact p = 0.056 (X), 0.39 (Y), 0.26 (Z), against a Bonferroni threshold of 0.0033.
- **R1-D (descriptive).**
  - F̂ = 0.9139 equals Stage 1's linear-inversion Φ⁺ fidelity (0.9139) to four decimals. That independently confirms the error rules and the frame.
  - F_L sits below both the Stage 1 value of 0.920 and the authors' 0.924, as expected.
- **Cost of certification:** the model-free, finite-sample certificate costs 0.027 relative to the point estimate. The union over 8 targets is part of that cost.

## Meaning for the paper
- On a real heralded link, model-free certification of fidelity ≥ 0.887 needs about 7,200 measured pairs (about 2,400 per basis).
- This is consistent with the resource floor in the theory note: certification costs thousands of pairs per user.
- **Not claimed:**
  - This is not a demonstration of Proposition C1, because the data do not randomise test vs keep per pair.
  - It is not a device-independent bound.
