# Stage 1 analysis choices (E61) — logged as made, before any comparison with the authors

Blinding: `Analysis_fidelity_and_matrices.png` was never opened, staged or read. No web search for the paper's numbers.
Files viewed: PREREG_INNSBRUCK_STAGE1.md, Readme.txt, Measurement_basis_and_scan_number.PNG (a byte copy was placed in
`stage1/view/basis_map.png` only because the original path is too deeply nested for the staging tool), Parameters.txt,
the sequence file Config/Ion_Ion_ent_UIBK_HZ.py (identical md5 in all 18 scans), the .dat and Photons_time.dat files.

## C0. File formats (decoded, all 18 scans identical layout)
- `<scan>.dat`: tab-separated, 1 header + 11 rows (one per scan step of the dummy variable AO.397sig_pow 0..9).
  608 columns = AO.397sig_pow, meanExc, APDscounts(0..4), PMTcounts(sum), PMTcounts(0..199), addPMTcounts(0,0..0,199), probs(0..199).
  * PMTcounts(i) = ion-readout PMT counts of cycle i (bimodal; sum column verified exactly).
  * addPMTcounts: unimodal (~15–95, peak ~40–50), never bimodal -> NOT a second qubit readout; not used.
  * probs(i) = authors' online threshold of PMTcounts (1 = bright); one global threshold 38 < thr <= 40 reproduces every probs entry.
  * meanExc = 1 - mean(probs) exactly (fraction dark = "excited" to D5/2).
  * APDscounts(3), APDscounts(4) = number of APD3 / APD4 time tags in that step (see C1). APDscounts(1),(2) = 0 always.
    APDscounts(0) (~140–210/step) does not match any click statistic tried; meaning unknown, not used.
- The sequence has ONE PMT detection per cycle (incl.PMTDetection after the branch label). So "two PMT readouts per cycle"
  is not correct: there is one ion readout per cycle (PMTcounts), plus an unused auxiliary count (addPMTcounts).
- `Photons_time.dat`: header `Scan_point Loop APD1 APD2 APD3 APD4`; one row per photon-generation attempt.
  Scan_point = global cycle index 1..2000 (= 10 steps x 200 cycles); Loop = attempt number (<= n_loops = 20); APDk = arrival
  time in µs of a click (0 = none). APD1/APD2 never click; only APD3 and APD4 are used.
- Only 10 APD*.raw files per scan but 11 .dat steps: the photon tags exist for 10 steps only.
- `all_files_in_one/photons_time.dat` (present in only 6 scans): headerless, more rows, last line duplicated; its per-block
  APD3 counts match no offset of APDscounts -> treated as a superseded/derived file, NOT used.

## C1. Alignment Photons_time <-> PMT  (data-driven)
- Block b of Photons_time (Scan_point 200b+1 .. 200b+200) <-> .dat row b+1, cycle index j = (Scan_point-1) mod 200.
  .dat row 0 (first scan step) has no photon tags and is discarded (200 cycles/scan lost).
- Evidence 1: per-block APD3/APD4 tag counts equal APDscounts(3),(4) of rows 1..10 exactly for 9/18 scans; in the others
  342/360 block-channel entries agree and the 18 disagreements are all ±1 (scan totals differ by 0–3 tags; Photons_time
  contains a few duplicated (Scan_point,Loop) rows). No other row offset matches.
- Evidence 2 (cycle level): the ion–photon correlation P(bright|APD3) - P(bright|APD4) in the six "diagonal" settings
  (photon basis matching ion basis) is ±0.83..0.93 only for (row b+1, same j); shifting j by ±1 or using row b gives |corr| <= 0.10.

## C2. Heralding rule (from the sequence code)
- Sequence: up to 20 attempts; `seq_branch(photons_BellState, Input_2_Trigger)` leaves the loop on a detector trigger; otherwise
  falls through after attempt 20; then mapping, optional rotation, PMT detection. Hence the ion readout belongs to the LAST attempt.
- A cycle is heralded iff the last attempt row(s) contain a click on exactly one of APD3/APD4.
  * clicks in earlier (non-terminal) attempts are ignored (ion was re-prepared afterwards): 191 such clicks in total; their time
    histogram peaks at 52–54 µs, i.e. mostly clicks arriving too late for the branch decision.
  * cycles that end before attempt 20 with no recorded click (69 cycles): excluded (no photon outcome available).
  * duplicated rows for the same attempt with clicks on BOTH detectors: excluded as double clicks (17 such attempts in the
    raw tag files, only 1 of them in a terminal attempt -> 1 cycle excluded). Same-detector duplicates
    (two tags ~0.2 µs apart) count as one detection.
  * terminal click at attempt 20 (718 cycles): kept (ion state is entangled with that photon).
- Result: 21,793 heralded cycles of 36,000 tagged cycles (18 x 2000).

## C3. PMT bright/dark threshold
- Histogram of PMTcounts over all used cycles (36,000 values: 18 scans x 10 tagged steps x 200) is bimodal: dark 0–34, bright 38–135; the values are (almost) all even;
  1-count bins 34:2, 36:0, 38:2, 40:3. The empty bin at 36 is the histogram minimum.
- Choice: bright iff counts > 36. Bright := ion |0> (S1/2 after the mapping pulse), dark := |1>.
- Sensitivity (not used for tuning): thr 30/40/44/50 change F by <= 0.002.

## C4. Photon arrival-time window
- Terminal-click arrival-time envelope (2 µs bins): 16 counts in 0–2 µs (onset), peak 6–8 µs, monotone decay to ~107/bin at 48–50 µs,
  38 counts in 52–54 µs, nothing beyond 53.8 µs (hardware gate). Raman pulse length APD_det_time = 50 µs.
- Upper bound on uniform background from the 0–2 µs bin: <= 16 per 2 µs, i.e. the envelope is >= 7x background everywhere up to 50 µs.
- Choice: no additional time cut (accept every terminal click inside the hardware gate, 0.08–53.8 µs).
- Sensitivity (not used for tuning): [0,50) and [2,50) µs change F by +0.0015 / +0.0017.

## C5. Measurement bases
- From the PNG; ion basis independently confirmed from Parameters.txt flags (X:True -> X, Y:True -> Y, both False -> Z) for all 18 scans;
  `mapping: True` in all. Photon label "P/Q" = the two orthogonal states separated by the PBS for that waveplate setting; each photon
  axis is measured twice with the two detectors swapped (H/V vs V/H [HWP 0 vs 45], D/A vs A/D [HWP ±22.5], R/L vs L/R [QWP ±45]).
- State conventions: order ion (x) photon; basis |0H>,|0V>,|1H>,|1V>. Photon H=|0>, V=|1>, D=(H+V)/√2, A=(H−V)/√2, R=(H+iV)/√2,
  L=(H−iV)/√2. Ion setting "X"/"Y"/"Z": bright <-> +1 eigenstate of σx/σy/σz (label-based convention).
  Note: a pulse model R(π/2,φ)=exp(−iπ/4 σφ) with phase 0 ("X") / 0.5π ("Y") would instead measure +σy / −σx; this differs from the
  label-based frame only by a local z-rotation of the ion (unitary) -> no effect on max fidelity, but it changes which Bell state/phase appears.

## C6. APD channel <-> polarisation (resolved from physicality, given the C5 conventions)
- Candidate M1: APD3 detects the first-named state of the PNG label (H in "H/V"); M2: APD3 detects the second-named state.
- M1 and M2 differ by an anti-unitary (universal-NOT) relabelling of the photon, so only one can yield a physical state
  for an entangled source. Data: M1 -> linear-inversion min eigenvalue −0.42, det T = +0.71, ML logL lower by 1660;
  M2 -> min eigenvalue −0.012, det T = −0.71. Choice: M2 (APD3 = second-named, e.g. V in "H/V").
- Caveat: this fixes only the PARITY of {APD mapping, photon handedness, ion handedness, bright=|0> choice}. Under other
  equally valid conventions, M1 could be the physical one; the max fidelity over maximally entangled states is the same,
  but the identity of the Bell state and the sign of imaginary parts depend on conventions (see result json, both mappings reported).

## C7. Combination of the 18 scans / detector-imbalance compensation
- Primary: for each (ion basis, photon axis) setting the counts of the two swapped-detector scans are pooled by polarisation
  label (so every polarisation outcome is seen by both APDs), giving 9 settings x 4 outcomes; then linear inversion and ML (RρR).
- Cross-check: full 18-scan conditional-multinomial ML with a free relative efficiency η4/η3 (fitted: 0.714); gives the same F to 1e-4.

## C8. Figures of merit and uncertainty
- Fidelity to each of Φ±=(|0H>±|1V>)/√2, Ψ±=(|0V>±|1H>)/√2; max over local phase φ in |0H>+e^{iφ}|1V> and |0V>+e^{iφ}|1H>;
  and max over ALL maximally entangled states (closed form (1+s1+s2−sgn(det T)s3)/4).
- Bootstrap: 500 replicates, resampling the 2000 tagged cycles with replacement independently within each scan; seed 20261007.

## Outcome bookkeeping (main run)
- 36,000 tagged cycles: 21,793 heralded; 14,137 no click in 20 attempts; 69 early end without tag; 1 terminal double click; 0 outside window.
- Script: reconstruct_ion_photon.py, sha256 587f735216996b810535500e9182bc5ad100897b62ee02072839bf8e499e0ea5 (also in stage1_result.json).
- Sensitivity runs in sensitivity/ were produced with the pre-speed-up version of the same script (only the RρR inner loop
  was vectorised afterwards; logic unchanged, point estimates identical to 1e-4 as verified by the nboot=20 timing run in dev/).
