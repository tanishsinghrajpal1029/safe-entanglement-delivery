# USTC 2026 Stage 1: does our memory model predict real ion–ion entanglement decay, and does a real link drift? (pre-registered 10 Oct 2026, before any data values were read)

**Dataset.** Zenodo 18218281: figure data for "Long-lived remote ion–ion entanglement for scalable quantum repeaters" (USTC, Pan group; probably arXiv 2602.08472). 18 workbooks, CC BY 4.0.

**What was looked at before this pre-registration:** sheet names, column headers and table sizes only. No data values.

## U1 (primary): model predicts real decay
- **Input:** single-ion coherence under KDD dynamical decoupling, measured separately on each memory (Fig. S2b, Alice and Bob).
- **Model:** our simulator's memory model (pure dephasing):
  - Z–Z correlations are kept;
  - X–X correlations are multiplied by each memory's normalised coherence ĉ(t);
  - so the fidelity change is ΔF(t) = (2|XX₀|/4)·(ĉ_A(t)ĉ_B(t) − 1).
- **Anchors and fitting:** the model is anchored only at t = 0 (|XX₀| from the Fig. 3d inset at the earliest time). ĉ(t) is interpolated linearly inside the measured range and extended with a log-linear fit beyond it. **No fitting to the entangled-state data.**
- **Target:** the measured fidelity change vs storage time (Fig. 3d, α = 17%).
- **Bar: PASS** if, at every storage time > 0, |ΔF_pred − ΔF_meas| ≤ 2√(σ_t² + σ_0²) + 0.02.

## U2 (secondary, descriptive with a prediction): a real link over time
- **Data:** per-data-set QBER (Fig. S8; 201 sets, taken in index order as time order).
- **Assumed counts:** n = 4.05×10⁵/201 pairs per set. That's the paper's stated total, assuming equal set sizes, which we cannot check.
- **Reported:**
  - over-dispersion of the error count against binomial (ratio and χ² p-value);
  - whether the running Beta(½,½) mixture confidence sequence (α = 0.05) for the error rate ever excludes the full-run rate;
  - the spread of CHSH between sets.
- **Prediction:** a stable link shows a dispersion ratio ≈ 1. ICFO (E92/E95) suggests real links drift, so we expect > 1 here too.

**How results will be read:**
- U1 PASS means our memory model, fed only single-ion calibration data, predicts how remote entanglement decays on real trapped ions. That answers part of the "simulator grades itself" weakness.
- A FAIL is reported as found, and shows which physics the model misses (for example readout loss over storage, which Fig. S3b records).
- No re-tuning.

## Files (sha256, first 16)

| File | sha |
|---|---|
| `ustc_stage1.py` (tested on synthetic workbooks: U1 passes on a model-consistent synthetic; U2 dispersion 0.97 on binomial data) | `9ae8a9fc3c48e39d` |
| `synth_ustc.py` | `a26a3dc119a9d263` |
