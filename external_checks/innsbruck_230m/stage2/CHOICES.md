# Stage 2 decoding choices (E63) — logged as made, each justified from data / readmes / sequence code / paper protocol

Blinding kept: only run totals, the two tomographic fidelities, and decoding/synchronisation quantities were computed.
No within-run time-resolved statistic of heralds or outcomes was computed or looked at; `analyze_stage2.py` was not run.
Code: `stage2/decode/` (s01..s13 + common.py, tomo.py). Caches in `stage2/decode/cache/`.

## D0. Run / basis map
- From `Full_tomography/Basis_timestamps.png` (Node A / Node B / photon-file triplets with "Basis NodeA-NodeB"):
  1819/182128/2021_07_20_182031 ZZ; 1856/185817/185539 ZX; 1920/192216/191636 ZY; 2143/214507/214405 XZ; 2243/224512/224420 XX;
  0014/001652/2021_07_21_001507 XY; 2203/220456/220327 YZ; 2349/235147/235032 YX; 2302/230420/230331 YY.
- Cross-checks: Node A Parameters.txt flags X/Y agree for all 9; Node B ExperimentSettings `mes_type` = 0 for the 3 "Z" runs,
  1 for the 3 "X" runs, 2 for the 3 "Y" runs (consistent 1:1). Note: the Node B sequence comments say mes_type 1 = "sigma y",
  2 = "sigma x" (opposite to the table). This relabelling (X<->Y at B) is an improper transformation; it is resolved in D9.

## D1. BSM time-tag format (Photons/*.txt)
- "Time stamps<TAB>Channel", time in ps (ch0 spacing 423.5 us = attempt period), monotone. Cached as int64 ps.
- Channels found: 0,1,2,3,4,5,6,7 (+14 in 6 files = exact copy of ch6, same count; ignored).
- Readme says ch0 = start-of-Raman trigger, 2/6 = SNSPDs, 3/5 = APDs, 7 = new cycle. Data contradict "3 = APD": ch3 occurs exactly
  once per attempt (+1 per cycle), always 2–5 us after ch0 (constant ~3.2 us), like a trigger. Detectors (photon-like arrival
  envelope 4–50 us after ch0, background elsewhere) are ch2, ch4, ch5, ch6. Same in the Synchronicity calibration files.
  => ch3 = Node A (UIBK) Raman trigger sent over the link (Node A sequence: "Raman trigger: TTL UIBK -> IQOQI for each Raman pulse");
  APDs = ch4, ch5. Identification with paper Table I (backgrounds/efficiencies): ch2 low background = SNSPD1, ch6 = SNSPD2,
  ch4 = SPCM1, ch5 = SPCM2 (count ordering matches p_det ordering). ch1 = auxiliary (bursts), not used.
- Total ch0 tags after the first ch7 of each file, summed over 9 files = 13,656,928 = exactly the paper's number of attempts
  (442 ch0 tags precede the first ch7 and are excluded) -> same raw data and same attempt definition as the paper.

## D2. Cycles and steps on the BSM clock
- Cycle = interval between consecutive ch7 (Node B "IQOQI cycle start trigger"). Step (scan point) boundaries = ch7 gaps > 20 ms
  (in-step cycle spacing <= 12 ms, step gaps >= ~200 ms). Every step has exactly 200 cycles (= Cycles: 200 in both nodes),
  except the last one, truncated where the tag file ends. The last tagged cycle of each file is truncated and dropped.
- Per cycle, #ch3 = #ch0 + 1 in every cycle (except artefacts at file edges): both nodes ran the same number of attempts in every cycle.

## D3. Node A raw marker files (APD*.raw) — decoded format
- Big-endian uint32 words. 0xf0000000 = frame separator; a frame spans P = 13,168,640 counter units (from data: the in-loop
  marker1->marker0 gap equals raw difference + P whenever one separator intervenes; with this P all times are monotone).
  Data word = 0xf | 24-bit time | 4-bit channel (1 = apd_marker0, 2 = apd_marker1). Unit ~64 ps (loop period 6.61e6 units = 423.5 us).
  Rare words with top nibble 3/4 (~45 per file, trailer-like) ignored.
- Per cycle (gap > 20e6 units): marker0 count = 1 (pre-loop) + n_loops + 1 (after branch label), as in Ion_Ion_ent_UIBK_HZ.py.

## D4. Synchronisation BSM <-> Node A (no outcomes used)
- For every step, the per-cycle number of attempts at Node A (from markers) is compared with the per-cycle number of ch0 at the BSM.
  Exact equality of all 200 cycles holds for the offset raw file = BSM step - 3 (runs other than 1819; 350–370 informative steps
  agree, 0 at any other offset), and file = step - 5 for 1819. The only disagreement is the final truncated cycle.
- Raw file i <-> .dat row i+1 (same as Stage 1: row 0 has no raw file). Hence Node A .dat row = BSM step - 2 (1819: step - 4).
- 1819 exception: raw files 0–8 (BSM steps 5–13) do not match the BSM cycle pattern (they look like mixtures of neighbouring steps),
  and 164 rows of 1819.dat have the five APDscounts fields collapsed into one empty field (parsed by position; PMT sum check passes).
- Accepted data = steps whose Node A raw file matches the BSM exactly at every cycle (cycle-level validated). This drops BSM
  steps 0–2 (no raw file / no .dat row) in every run and steps 0–13 in 1819. No holes remain inside any run.
- Confirmation with outcomes (allowed for decoding): in ZZ (1819) the correlation <(-1)^(a+b)> is -0.86 (psi+), -0.78 (psi-),
  +0.85 (parallel-polarisation pairs) at this offset and |E| <= 0.17 at all others; in XY and YX the psi+/psi- correlations are
  opposite (+-0.25 at T=17.5 us) only at this offset.

## D5. Synchronisation BSM <-> Node B (no outcomes used)
- PMT1_2.txt: one row per step (400 rows), Start/Stop (ms, epoch), 200 per-cycle PMT columns (sum column checks).
- Step timing: the time of the last ch7 of BSM step j follows Node B Stop(j) with 3.3 ms rms (linear fit, ~44 ppm clock-rate
  difference) in all 9 runs; every other offset gives >= 48 ms rms. => Node B row = BSM step (offset 0); cycle i of the step = column i.
- Confirmed with outcomes as in D4 (ZZ/XY/YX correlations only at offset 0).
- PMT1_1 (Doppler-cooling detection at cycle start) not used.

## D6. Photon detection window and coincidence (time reference)
- t = tag time - preceding ch0 (Node B start-of-Raman trigger; readme). Window [5.5, 23] us, coincidence |tau| <= T, T = 1 us (main).
- Justification of the time reference: the paper's Fig. 2(a) is Calibrations/Synchronicity/wavepackets.pdf (Node A orange, Node B
  green, 1 us bins). Extracting its vector bars and cross-correlating with our ch0-referenced histograms of the two Synchronicity files
  gives a figure axis = ch0-frame - 2.00 us (corr 0.9999/1.000 at exactly 2.00). Its dashed coincidence-window lines are at 3.50 and
  21.00 us in figure units = [5.50, 23.00] us in the ch0 frame, which is the interval quoted in the paper text. So the paper's window
  is [5.5, 23] us after ch0. Per-detector onsets agree within 0.2 us (no per-channel delay correction).
- Event definition: an attempt with exactly two clicks inside [5.5, 23] us on two different detectors, |t1 - t2| <= T. Variants
  (first click per detector; exactly two clicks in the whole attempt) change the count by <= 1.
- Every such coincidence (all T, all patterns) occurred in the terminal attempt of its cycle (the nodes exited the loop), so the
  ion readout of that cycle belongs to it. Coincidences in attempt 20 (17 events at T=1) are kept: the sequence reads out anyway.

## D7. psi+ / psi- assignment (no outcomes used)
- Paper: SPCMs in one beam-splitter output, SNSPDs in the other, PBS in each output; psi+ = coincidence in the same output,
  psi- = opposite outputs, orthogonal polarisations. Same output: (2,6) and (4,5) -> psi+.
- The hardware heralds all six pairs. Which cross pairs are parallel-polarised: two-photon (HOM) interference suppresses
  parallel-polarisation coincidences in opposite outputs at small |tau|. Pooled over runs, counts at |tau| < 1 us vs counts per us at
  |tau| in 3–4 us: (2,4) 16 vs 57, (5,6) 34 vs 112 (dip) ; (2,5) 138 vs 96, (4,6) 123 vs 89, (2,6) 256 vs 239, (4,5) 70 vs 54 (no dip).
  => (2,4) and (5,6) parallel (not heralds; excluded); psi- = (2,5),(4,6). ZZ data later confirm: parallel pairs give correlated
  Z outcomes (+0.85), psi pairs anticorrelated.

## D8. Ion readout thresholds and outcome convention
- Node A: PMTcounts(i) of the .dat (one detection per cycle, Stage 1 C0). Histogram over all 9 runs: dark 0–34, bright 38+, minimum
  at 36 -> bright iff counts > 36 (same as Stage 1). Node B: PMT1_2 (readme: "the relevant file"); histogram: dark 0–3, bright peak ~17,
  minimum at 4 (247 vs 251 at 5) -> bright iff counts > 4.
- a, b = 0 for bright, 1 for dark. Z basis: bright <-> |D> = |3D5/2, m=-5/2> (mapped to S by the pi pulse in both sequences / paper),
  dark <-> |D'> = |m=-3/2>. Qubit |0> = |D>, |1> = |D'>. X/Y: bright <-> +1 eigenstate of sigma_x / sigma_y (label-based convention).
- Sensitivity (not tuned): Node A thr 30/44, Node B thr 3/6 change F by <= 0.0015 (no heralded event has an A count in 30–44).

## D9. Tomography and fidelity convention
- Per herald, 9 settings x 4 outcomes; maximum likelihood (R rho R) and linear inversion.
- Target |Psi+-(phi)> = (|01> +- e^{i phi}|10>)/sqrt2 = paper Eq. (1). Main F+-: one phi optimised jointly for both heralds
  (paper: phi optimised once, then fixed). Also reported: phi optimised per herald, linear inversion, max over all maximally entangled states.
- Handedness: label-based Node B axes vs the X<->Y (or Y-sign) alternative differ by an improper map. Data: table labels give
  linear-inversion min eigenvalue -0.13 (both heralds, n ~ 300: statistical), the alternative -0.45/-0.37 and F ~ 0.37–0.45.
  Choice: table labels. Our joint phi = 265.3 deg; the paper quotes 81.2 deg (= ours - 180 deg + 4 deg): the phi/psi+- sign convention differs
  by pi between us and the authors, which does not change F+ or F-.

## D10. Run windows (runs.csv)
- BSM clock zero = first ch7 tag of the photon file. t_start_s = first ch7 of the first validated step; t_end_s = start of the
  truncated last cycle (= end of the last complete cycle). t_s = time of the later click of the herald coincidence (ch0 + t2).
  Steps 0–2 (0–13 for 1819) and the untagged end of each node run are outside the window.

## Outcome bookkeeping
- BSM in-window two-click terminal coincidences (all T, all 6 pairs): 6,125; inside validated steps: 6,072.
- Main table (T = 1 us, psi+/psi-): 581 events (psi+ 324, psi- 257); before the validation cut 588.
- G3: count 581 vs 491 (+18%) -> OUTSIDE +-10%. F+ = 0.900, F- = 0.837 (paper 0.882, 0.822) -> inside 0.06.
- At T = 17.5 us: 4,490 events (4,534 before validation) vs paper 3,960 (+13%); F+ = 0.597, F- = 0.585 (paper 0.587, 0.580).
- The count excess is not explained by any data-loss, multi-click, window-edge (+-0.5 us: 573–586) or time-reference variant tried.
  Attempts agree exactly with the paper, fidelities agree within 0.02 at both T. Cause unknown; no change was made to approach 491.

## Post-G3 check requested by the coordinator (NOT a decoding fix; the single allowed fix is NOT used)
- Question: are the 581 main-table coincidences all in the last attempt of their cycle? Check on the BSM clock (decode/s14_lastattempt_check.py):
  after the herald attempt's ch0 there is no further ch0 and no further attempt-type ch3 (ch3 within 10 us after a ch0) before the next ch7,
  for 581/581 events (psi+ 324/324, psi- 257/257; every run). Each cycle carries exactly one extra ch3 ~1.6 ms after its last attempt
  (Node A raising 397sig_sw for the next cycle's handshake after its readout); it is not an attempt trigger.
- Sequence code: Node A `for i in range(n_loops): ... seq_branch(photons_BellState, Input_2_Trigger)` then `seq_insert_label(photons_BellState)`,
  mapping / rotation, `incl.PMTDetection(...)`; Node B `for i in range(int(n_loops)): ... if doBranching: jump_trigger('label_analysis',0x8)`,
  then `insert_label('label_analysis')`, 729 pulses, `PMTDetection(det_time)`. => the readout follows the last attempt (herald exit or attempt 20).
- The last-attempt rule was already applied from the start (s09: attempt == n_att-1, D6). Restricting to it removes 0 events, so no
  events_v2.csv was written and the pre-registered single fix was NOT spent. G3 count failure stands (581 vs 491).
- Early-ended cycles (validated steps, excluding the truncated last cycle): 10,442. With a main-table psi coincidence in the last attempt: 564
  (+17 main-table events at attempt 20, which do not end early). Without: 9,878 = parallel-polarisation pair in window 1,516; psi pattern in window
  but |tau| > 1 us 3,693; >=2 clicks on different detectors but not both in [5.5,23] us 4,655; >2 clicks in window 5; single click 9.
