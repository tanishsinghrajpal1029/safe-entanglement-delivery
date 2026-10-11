# Can we certify fidelity, model-free, on published real data? Feasibility study (11 Oct 2026)

**Status: read-only feasibility study.** No certification statistic (lower bound, confidence bound or anytime bound) was computed on any real dataset. Everything below is about what *can* be computed, under which assumptions, from which files. A pre-registration must be written and hashed before any bound is run.

**How to read the labels**
- **[V]** = verified in this session, from a file, the code, or an opened web page; the source is given.
- **[I]** = inferred or derived here; it needs checking.
- **[U]** = unverified, because the source could not be opened or the information is not in the files.

---

## 0. Bottom line

1. **No public dataset lets us validate Theorem C1 itself.**
   - Theorem C1 needs, *per pair*, a test/keep choice and a test basis drawn at random and hidden from the source (A1).
   - **Innsbruck** measures its settings in fixed scans (blocks in time).
   - **USTC** does randomise settings per round [V, paper text], but publishes only per-set and cumulative summaries (no per-round records).
   - **ICFO** did not record its phase settings.
   - So any real-data demonstration is of the certificate's *statistics* under an extra, explicitly stated assumption (stationarity across scans). It is **not** a validation of the "no-iid" claim. The paper must say this.

2. **Innsbruck 230 m, ion–photon (Stage 1 data): a rigorous trusted-device lower bound on fidelity is feasible now. This is the recommended primary.**
   - The three correlators XX, YY and ZZ for |Φ⁺⟩ = (|0H⟩ + |1V⟩)/√2 come from exactly six of the 18 scans.
   - The Stage 1 CHOICES file already fixes every convention.
   - `stage1_counts.csv` alone is enough for a fixed-sample bound.
   - A time-ordered (anytime) version needs a per-shot export from six raw scans. The decoder already produces per-cycle records internally.

3. **USTC 2026: no rigorous finite-sample bound is possible from the deposited figure data.**
   - **Device-independent route.** Fig. S8 gives per-set CHSH and QBER values only. There are no counts per setting, no number of Bell-test rounds per set, and no error bars.
     - A per-set Kaniewski number can only be a plug-in (asymptotic) value.
     - A rigorous device-independent bound needs the Bell-round count and win count per set (or per round). We would have to obtain these from the Supplementary Information or the authors.
   - **Trusted-device route.** If the CHSH settings are the standard ones (unverified), then F ≥ S/(2√2) [I], a much stronger statement. It still needs counts.
   - **Fig. 3d fidelities are not model-free.** They equal (1 + |ZZ| + 2|XX|)/4 exactly [V], so they assume |YY| = |XX|.

4. **ICFO 2021: excluded** from fidelity certification (no phase settings; vacuum-dominated photonic state).

5. **Innsbruck ion–ion (Stage 2 events): a per-event dataset in all 9 setting pairs exists, but it is not recommended as a primary.**
   - Gate G3 failed: 581 events against the paper's 491.
   - Counts are small: 65–78 events per setting, split over ψ⁺ and ψ⁻.
   - The target phase φ was estimated from the same data.
   - At most an exploratory, labelled-deviation secondary.

---

## 1. Kaniewski's CHSH self-testing bound: checked against the literature

**Source.** J. Kaniewski, "Analytic and nearly optimal self-testing bounds for the Clauser-Horne-Shimony-Holt and Mermin inequalities", PRL 117, 070402 (2016), arXiv:1604.08176.
- Abstract opened: https://arxiv.org/abs/1604.08176 [V].
- PDF opened: https://arxiv.org/pdf/1604.08176. It was read through a fetch-and-summarise tool, so the equation numbers come from that summary [V, with the caveat that the quotes are machine-extracted].

**Formula: [V].**

  Ξ ≥ 1/2 + (1/2)·(β − β*)/(2√2 − β*),  β* = (16 + 14√2)/17 ≈ 2.1058  (paper Eq. 10)

- This is the same as the user's F ≥ (1 + (S − b*)/(2√2 − b*))/2.
- Equivalent linear form: Ξ ≥ s·β + μ, with s = (4 + 5√2)/16 and μ = −(1 + 2√2)/4 (Prop. 1 / Eq. 7).
- I checked the algebra numerically: sβ* + μ = 0.5000, s·2√2 + μ = 1.0000, and the two forms agree at test values of S (not data).

**What "F" means: [V].** Ξ is the *extractability*: the maximum over local channels Λ_A ⊗ Λ_B (CPTP, no communication) of the fidelity F(ρ, σ) = ‖√ρ√σ‖₁² between (Λ_A ⊗ Λ_B)(ρ_AB) and the singlet. Here σ is the singlet. The target is any maximally entangled two-qubit state up to local unitaries.
- It is **not** the fidelity of the raw delivered state to a fixed lab-frame Bell state.
- It is a weaker claim, which is the price of device independence.

**Assumptions: [V] where the paper states them, [I] where it is silent.**
- Quantum mechanics with a tensor-product split between Alice and Bob: no communication between the measuring devices, so the locality or no-signalling assumption must be stated if the locality loophole is open.
- The shared state may have any finite dimension.
- Measurements are uncharacterised, with two binary-outcome observables per party. Projectivity is taken without loss of generality.
- β is the **exact** quantum expectation of the CHSH operator. **There is no finite-statistics treatment, and iid sampling and detection efficiency are not addressed** [V: absent from the paper].
- Every round must give an outcome, or non-detections must be binned into an outcome, so that there is no post-selection that depends on the settings [I: standard requirement].
- The bound is not claimed to be tight. Valcarce et al., Quantum 4, 246 (2020), https://quantum-journal.org/papers/q-2020-03-23-246/ (opened), show that the minimum CHSH score that can certify non-trivial singlet fidelity is at least about 2.05. The summary tool's wording was garbled, so this is [U] in detail. In any case it does not change the validity of Kaniewski's bound.

**Extending it to many rounds [I].**
- Because the bound is linear in β (an operator inequality: K ≥ s·W + μ·1 on each Jordan qubit block), averaging it over rounds is allowed: (mean extractability over rounds) ≥ s·S̄_cond + μ, where S̄_cond is the average *conditional* CHSH value.
- With settings chosen uniformly at random and independently of the devices, the CHSH game indicator gives a bounded martingale. So a finite-sample lower confidence bound on S̄_cond needs no iid assumption: either the Azuma/Chernoff type of Zhang–Glancy–Knill and Bierhorst, or a test supermartingale.
- This extension is ours. It must be checked before any device-independent claim is made in the paper.

---

## 2. What each dataset supports

| Dataset | Trusted-device bound from XX/YY/ZZ (Lemma F), fixed sample | Sequential / anytime version | Device-independent bound (Kaniewski) | Main extra assumptions |
|---|---|---|---|---|
| **Innsbruck ion–photon** (Stage 1, 18 scans) | **Yes.** Rigorous for the pooled population of six scans, under the assumptions on the right | **Yes, per basis, in true time order**, after a per-shot export. Not Theorem C1 (settings are not random) | **No.** Only Pauli settings were measured. For a state near Φ⁺, Pauli-aligned CHSH is ≤ 2 [I] | Trusted ion and photon measurements; fair sampling after pooling the detector-swapped scans; the state does not depend on the fixed basis schedule (stationarity across ~13 min, see §3.4) |
| **Innsbruck ion–ion** (Stage 2 events.csv) | Possible but weak (~65–78 events per setting); needs XY and YX, because φ ≈ 265° in our frame | Possible (per-event times exist) | No (Pauli settings only) | All of the above, plus an unresolved event-count discrepancy (G3 FAIL) and a data-chosen φ |
| **USTC 2026** (figure xlsx) | **No rigorous version.** The Fig. 3d inset has XX and ZZ with std but no counts and no YY. Fig. 3a has contrasts for all 9 settings with std, but no counts, and the sign convention is unknown [U] | **No rigorous version.** Per-set CHSH and QBER values exist without counts (Fig. S8). Cumulative CHSH and QBER with std against time exist (Fig. 4c), next to cumulative pair counts (Fig. 4b) | **Plug-in only** per set, or on the total S. Rigorous only with Bell-round counts and win counts | Random settings per round [V]; the detection loophole is probably closed by event-ready heralding and near-unit ion readout [I/U]; locality is not stated [U] |
| **ICFO 2021** | No (phases not recorded; only one correlator family) | n/a | No | n/a |

---

## 3. Innsbruck ion–photon in detail

### 3.1 Which scans give XX, YY and ZZ [V: code `reconstruct_ion_photon.py`, CHOICES.md C5/C6, `stage1_counts.csv` settings columns]

**Conventions frozen in Stage 1 (C5).**
- Order: ion ⊗ photon.
- Photon: H = |0⟩, V = |1⟩, D = (H + V)/√2, A = (H − V)/√2, R = (H + iV)/√2, L = (H − iV)/√2. So D, R and H are the +1 eigenstates of σx, σy and σz.
- Ion setting "B" ∈ {X, Y, Z}: bright ↔ +1 eigenstate of σ_B. Bright = |0⟩.

**APD mapping M2 (C6).** APD3 detects the *second*-named state of the scan label, and APD4 the first. This was chosen from physicality: M1 gives a minimum eigenvalue of −0.42.

**Lemma F for |Φ⁺⟩ needs the following settings:**

| Correlator | Scan, photon label, ion basis | Error event per heralded shot |
|---|---|---|
| ZZ | **1651** (H/V, Z) and **1655** (V/H, Z) | ion ±1 ≠ photon ±1 (H = +1) |
| XX | **1653.02** (D/A, X) and **1659** (A/D, X) | ion ±1 ≠ photon ±1 (D = +1) |
| YY | **1656** (R/L, Y) and **1702.02** (L/R, Y) | ion ±1 **=** photon ±1 (R = +1; Φ⁺ has ⟨YY⟩ = −1) |

- Each correlator is measured twice, with the two detectors swapped.
- The other 12 scans are cross-basis settings (XZ, ZX, and so on). They are not needed for the fidelity to a fixed Bell state.
- The Stage 1 log reports 21,793 heralded cycles over 18 scans [V, CHOICES.md]. I did **not** read the per-scan heralded counts or outcome columns of `stage1_counts.csv`, to avoid looking at the data.
- The user's summary gives ~1,100–1,300 heralded shots per scan, so roughly 2,200–2,600 per basis.
- All six raw scan folders exist on the Mac with `<scan>.dat`, `Photons_time.dat` and `Parameters.txt` [V, listed].

### 3.2 Fixing the target and convention in advance

**What is already known (no blinding is possible here).** Stage 1's `run_main.log` [V] printed, under M2:
- Φ⁺ fidelity 0.9131 (maximum likelihood) and 0.9139 (linear inversion);
- best local phase 0.9135;
- maximum over all maximally entangled states 0.920;
- ≤ 0.046 for Φ⁻, Ψ⁺ and Ψ⁻.

The Lemma F fidelity is a *linear* function of these same counts. So its point estimate is effectively known already (≈ the linear-inversion Φ⁺ value, up to pooling details). A pre-registration here **controls analytic flexibility**: the target, the bound, α, the pooling and the scan set. It does **not** hide the point estimate. The paper must say this.

**Recommended fixed choices (all taken from Stage 1, not chosen anew):**
1. **Frame:** Stage 1 C5 conventions plus M2. The threshold (bright iff PMT > 36), the herald rule (C2), the window (C4: no extra cut) and the last-attempt rule are frozen exactly as in the script with sha256 587f7352….
2. **Target:** |Φ⁺⟩ = (|0H⟩ + |1V⟩)/√2 at phase 0. **No phase optimisation.** The optimum phase is −2.4° and costs only 0.0004 in fidelity, so a fixed φ = 0 loses almost nothing and removes a continuous selection.
3. **Scan set:** exactly the six diagonal scans in the table above. The choice is dictated by Lemma F, not by the data.
4. **Pooling:** pool each pair of detector-swapped scans by polarisation label (Stage 1 C7). With equal trial counts (2,000 tagged cycles per scan [V]) and stationarity between the two scans, each polarisation outcome then sees the average efficiency (η₃ + η₄)/2.
   - The fitted η₄/η₃ is 0.714 [V, CHOICES C7], so pooling matters.
   - [I] For a state with balanced photon marginals, unequal detector efficiencies leave the error rate unchanged even without pooling. A bias appears only when errors are correlated with the photon outcome. Pooling cancels it to first order.

**Selection-bias risks and the fix.**
- The Bell-state identity (Φ⁺ out of four) and the mapping (M2 out of two) were picked after seeing Stage 1 output.
  - M2 was chosen for physicality, not fidelity, but the Φ⁺ identity followed from the fitted state.
  - **Fix:** make the bound simultaneous over all 8 candidates (2 mappings × 4 Bell states in the C5 frame) with a union bound: α/8 per candidate, α/24 per basis error rate.
  - The cost is small: the planning projection in §6.4 gives a width of about 0.003–0.006 more than at α/3.
- Decoding choices (threshold, window, herald rule) were made in Stage 1 from histograms and sensitivity runs: threshold and window changes moved F by ≤ 0.002. **They must not be revisited.** No sensitivity variant may replace the primary.
- Do not choose between maximum likelihood and linear inversion. The certificate uses raw error counts only; there is no reconstruction step.

### 3.3 Assumptions the Innsbruck bound must state
- **(T) Trusted measurements.** The ion readout (with the mapping pulse) and the photon polarisation analysis implement the ideal Pauli measurements in the C5 frame. All imperfections are attributed to the state. Readout and waveplate errors therefore lower the certified fidelity of the *effective* state; this cannot be separated from them.
- **(FS) Fair sampling.** After pooling, the probability that a photon is heralded does not depend on its polarisation within a basis. This is the detection loophole for the photon. It is acceptable for a trusted-device certificate but must be named.
- **(H) Heralded population.** The certificate is about the ion–photon state *conditioned on a herald* (the photon is consumed by the measurement). It is a heralded-state fidelity, not an unconditional one.
- **(S) No covariance with the schedule / stationarity.**
  - Settings follow a fixed schedule rather than per-shot randomisation.
  - The certified quantity is the average fidelity over all heralded shots of the six scans. Lemma F needs each basis's average error rate over *its* scans to equal what that basis would show over all six scans.
  - This holds if the state process is stationary over the ~13-minute run, or if it varies in a way that is not correlated with the basis schedule.
  - It is weaker than iid but not testable in full.
- **(M) Within-scan dependence is allowed.** The chosen statistics (§6) need no iid shots within a scan: they bound the average conditional error probability for adaptive sequences.

### 3.4 Timing of the scans [I]
- The scan names appear to be HHMM clock stamps (the sequence goes …1659, 1700…). If so, all 18 scans fall within about 16:50–17:03, and the six diagonal scans are interleaved: ZZ at 16:51 and 16:55, XX at 16:53 and 16:59, YY at 16:56 and 17:02.
- The interleaving makes (S) milder, and it gives a partial test: each basis is measured twice, minutes apart, with the detectors swapped.
- **Confound:** a difference between the two halves mixes drift with detector imbalance, so this test can only flag a problem, not prove stationarity.

### 3.5 Why the device-independent route fails here [I]
- With ion settings {X, Z} and photon settings {X, Z}, a state near Φ⁺ in the C5 frame has a CHSH maximum of |⟨ZZ⟩ + ⟨XX⟩| ≤ 2.
- Violation needs ±45° settings on one side, which were not measured.

---

## 4. USTC 2026 in detail

### 4.1 What the files contain [V: sheet names and headers listed on the Mac copy; values not re-read]
- **Fig_S8 (200 data rows):** `Index of Data Set`, `CHSH_value`, `QBER_value/%`. **No std and no counts.** This is what `ustc_stage1.py` reads, as columns 1 and 2 (CHSH and QBER %).
- **Fig_4c `Fig_4c_CHSH_QBER` (2,349 rows):** `Accumulation_time/h`, `CHSH_value`, `CHSH_std`, `QBER`, `QBER_std`. These are cumulative values [I: from the name].
- **Fig_4b (2,349 rows):** `Time`, `Entanglement_accumulated`. These appear to be the cumulative pair counts on the same time grid as Fig 4c [I: same row count, not checked].
- **Fig_4c `inset_params`:** `Asymptotic_key_rate`, `Our_result_log10_N`, `Our_result_key_rate`.
- **Fig_4d:** our-result and other-work CHSH and QBER with std.
- **Fig_3a:** `Contrast_ρ±` with std for all 9 Pauli pairs (XY, XZ, YX, YZ, ZX, ZY, XX, YY, ZZ). Whether "contrast" is signed is [U].
- **Fig_3d inset:** XX and ZZ with std at 5 storage times. **No YY.**
- **Fig_S3b:** XX and ZZ against storage time, plus detection (readout) fidelity against storage time for each node.

### 4.2 Paper facts (arXiv:2602.08472 opened as https://www.arxiv.org/pdf/2602.08472, read via the summarise tool [V with that caveat]; the Supplementary Information was **not** available [U])
- The authors state: "Alice and Bob independently choose their settings at random", using random numbers from earlier device-independent randomness experiments.
- Rounds with X, Y ∈ {0, 1} are Bell tests; X = 0, Y = 2 are key rounds.
- N = 405,145 rounds over 10 km. S = 2.5758 ± 0.0059 and Q = 0.0360 ± 0.0006.
- The finite-key analysis follows "Zhang et al.". Its assumptions (iid or not) are not stated in the main text [U].
- The setting probabilities and the per-set sizes are not in the main text [U].
- The heralded state is ρ = (1 − α)|ψ±⟩⟨ψ±| + α|↓↓⟩⟨↓↓|.

### 4.3 Are per-set CHSH values enough? No, not for a rigorous bound.
1. Per-set CHSH comes from Bell-test rounds only, an unknown fraction of each set's rounds.
   - The n ≈ 2,025 per set used in Stage 1 is itself an equal-size assumption: 405,145/200 [V for N; I for equal sizes].
   - Without n_Bell per set (and ideally the realised count for each setting pair), neither a per-set confidence bound on S nor a test of whether S is over-dispersed between sets is possible.
   - The between-set sd of 0.090 [V, Stage 1 output] cannot be compared with shot noise.
2. The Kaniewski bound is asymptotic (§1). Plugging in a per-set or total S gives a "plug-in DI extractability", which is not a confidence statement.
3. **A rigorous device-independent statement needs:** per set (or per round), the realised number of rounds and CHSH wins for each setting pair. This is to be requested from the Supplementary Information or the authors.
   - With these and the random settings, a martingale lower bound on S̄_cond at level α, followed by the linear Kaniewski map, gives a valid DI lower bound on average extractability [I, see §1].
4. **Assumptions to state for a device-independent USTC claim:**
   - setting choices independent of the devices and the source, i.e. the randomness is trusted [V that it is "random"; independence is an assumption];
   - no communication between the two nodes' measuring devices during a round. Space-like separation is not claimed in the text [U], so this is an assumption, not a closed loophole;
   - every Bell round yields an outcome at both nodes (event-ready heralding and fluorescence readout), so there is no post-selection that depends on the settings. This also needs the herald to be independent of the settings, e.g. settings applied after the herald [U];
   - quantum mechanics;
   - **no iid needed** if the martingale construction is used. iid *would* be needed for a CLT- or std-based interval.
5. **Trusted-device alternative [I, derived here, to check].**
   - If the CHSH settings are the textbook ones (A0 = Z, A1 = X, B0,1 = (Z ± X)/√2, in the frame of the target ψ±), then S = √2(⟨ZZ⟩′ + ⟨XX⟩′) in that frame.
   - Since (XX + ZZ)/2 ≤ |Φ⟩⟨Φ| for the matching Bell state (checked on all four Bell states), **F ≥ S/(2√2)** under trusted measurements.
   - This is much stronger than the DI bound but rests on the setting angles, which are [U] until the Supplementary Information is read. It still needs counts for finite-sample rigour.
6. **Fig. 3d storage-time fidelities are not model-free [V].** On all five storage times, F_meas = (1 + |ZZ| + 2|XX|)/4 to 6 decimals, recomputed from `out_ustc.json`. The authors therefore assume |YY| = |XX|. The model-free two-basis bound from the same inset is (|XX| + |ZZ|)/2, valid if XX is measured along the state's phase axis. It is a plug-in only (std without counts) and was **not computed here**.

---

## 5. ICFO 2021
- The phase settings were not recorded [V, ICFO Stage 1 result]. With one effective correlator family and unknown phases, Lemma F (or its two-basis version) cannot be formed.
- A phase-free *lower* bound on coherence via max|E| over the recorded settings is conceivable [I]. It would need a multiplicity correction and would certify a vacuum-dominated path-entangled state (concurrence ~10⁻²), not a delivered Bell pair.
- **Exclude** it from the certification section. Keep it only for the drift evidence already in the paper.

---

## 6. Recommended pre-registerable plan

### 6.1 Primary: Study R1 (Innsbruck ion–photon), fixed-sample trusted-device certificate
- **Data:** the six diagonal scans (§3.1), decoded with the frozen Stage 1 script (sha 587f7352…). The counts must match `stage1_counts.csv` exactly. This is a gate: any mismatch is a stop, not a fix.
- **Statistic:** for each basis B ∈ {X, Y, Z}, k_B errors in n_B heralded shots (pooled detector-swapped scans), using the error rules in §3.1.
  - Per basis, a one-sided **Chernoff–KL upper confidence bound** e_B^U solving n_B·KL(k_B/n_B ‖ e_B^U) = ln(24/α).
  - [I, derived here] This bound stays valid for adaptively varying conditional error probabilities at a fixed n: use Jensen on the concave log(1 − p + p·e^{−λ}), then the martingale identity, then Markov. Clopper–Pearson needs independence and is not used.
- **Certificate:** F_L = 1 − (e_X^U + e_Y^U + e_Z^U)/2, simultaneous at 1 − α = 0.95 over the 8 candidate targets (2 mappings × 4 Bell states); only Φ⁺/M2 is reported as the headline.
  - The other seven are computed only so the union bound is honest; their values are not used for anything.
- **Pass/fail bars (fixed now, and not dependent on the unknown bound value):**
  - **R1-A (primary, external bar): F_L > 1/2**, so heralded ion–photon entanglement is certified without a state model at 95%. Given the known point estimate this is near-certain to pass. Say so in the prereg: its job is to demonstrate, not to discover.
  - **R1-B (machinery check):** F̂_Φ⁺(Lemma F) − F_L lies within ±0.005 of the width predicted *before the run* from n_B and k_B under the planning formula. In practice this checks the code against the theory.
  - **R1-C (stationarity diagnostic):** for each basis, the error rates of the two detector-swapped scans agree (exact two-proportion test, Bonferroni over 3, α = 0.01).
    - A FAIL does not void R1-A. It labels the certificate "assumption (S) contradicted by the data", and the paper must then report the per-scan-pair certificates separately.
  - **R1-D (descriptive):** F_L against the authors' published 0.929 (+0.004/−0.005) and our Stage 1 value of 0.920. F_L ≤ both is expected; F_L above either flags an error.

### 6.2 Secondary: Study R2 (Innsbruck ion–photon), time-ordered anytime bound
- A per-shot export (scan, cycle index 0..1999 in Scan_point order, heralding APD, bright/dark) from the frozen `load_scan`.
  - The new code is a wrapper that writes the existing `rec` arrays; the decoding logic is untouched.
  - Gate: per-scan totals identical to `stage1_counts.csv`.
- For each basis, a time-uniform upper confidence sequence for the running average error, at α/24 per basis.
  - Use the sub-Bernoulli/Bennett "stitched" or normal-mixture boundary of Howard et al. (2021), which is valid for martingale differences E_i − p_i (not iid). The Beta-binomial mixture used in USTC U2 assumes a constant p and is not appropriate here.
  - Combine as in R1 at each time point.
- **Report:** the trajectory of F_L(t) in true clock order over the interleaved scans, the cost of anytime validity (final F_L(R2) − F_L(R1)), and whether F_L(t) ever exceeds the full-run point estimate (a descriptive check of validity, as in ICFO R3).
- **Wording rule:** "anytime-valid under (T, FS, H, S)". Never "Theorem C1 validated on hardware".

### 6.3 Optional: USTC device-independent, Study R3 (only if the counts become available)
- Request from the Supplementary Information or the authors: per set (in time order), the realised Bell-round counts for each of the 4 setting pairs and the wins (or outcome counts), plus the setting probabilities and the timing of herald versus setting choice.
- **Statistic:** a CHSH-game test supermartingale (or Azuma) lower bound on S̄_cond at α = 0.05, mapped through Kaniewski's linear bound, giving a lower bound on average extractability.
- **Bar:** the DI extractability bound is > 1/2. This needs S̄_cond's lower bound to exceed β* ≈ 2.106.
- A trusted-device S/(2√2) version is allowed only after the setting angles are verified from the Supplementary Information.
- **If the counts are not available:** report plug-in Kaniewski values *explicitly labelled "asymptotic, no confidence statement"*, or omit them. Do **not** derive counts from the std columns for a confirmatory claim (std → n_eff assumes binomial errors and a known setting split). That may appear only as a labelled exploratory sensitivity analysis.

### 6.4 Planning projection (hypothetical inputs, not data)
- Using only the *published* fidelity scale (F ∈ {0.90, 0.92}), errors split equally across bases, and n_B ∈ {2,200, 2,600} (the user's ~1,100–1,300 per scan × 2), the R1 width F̂ − F_L would be about 0.020–0.024 at α/3 per basis and about 0.025–0.031 at α/24 per basis (Chernoff–KL, 95%).
- So the union over 8 targets costs about 0.005.
- Innsbruck ion–ion would be roughly √30 ≈ 5× wider (~0.1+), which is why it is not recommended. This is a rough scaling estimate.

### 6.5 Text the prereg must contain
- The Stage 1 point estimates already known: 0.913 / 0.914 / 0.920. Say so.
- Assumptions T, FS, H, S and M (and for USTC: random-setting independence, no inter-device communication, no post-selection on settings, quantum mechanics).
- The script hashes, the locked α = 0.05 and the 8-candidate union.
- "No other target, phase, pooling, threshold or scan subset will be reported as primary."
- A sentence that no public dataset randomises test/keep per pair, so Theorem C1's no-iid guarantee is illustrated, not validated, on real data.

---

## 7. Files to stage from the Mac

The base path is `~/Documents/Independent-Study/quantum_grid_router/Files11-EndToEnd-PRX-Claude/prx_work/22_external_checks/`. All paths below were checked to exist.

**Innsbruck ion–photon: needed for R1**
- `innsbruck_230m/stage1/stage1_counts.csv`
- `innsbruck_230m/stage1/reconstruct_ion_photon.py` (with `.sha256`)
- `innsbruck_230m/stage1/CHOICES.md`
- `innsbruck_230m/stage1/stage1_result.json`
- `innsbruck_230m/stage1/run_main.log`
- `innsbruck_230m/PREREG_INNSBRUCK_STAGE1.md`
- `innsbruck_230m/STAGE1_RESULT.md`

**Innsbruck ion–photon: also needed for R2 (per-shot export)**
- The 18 files below, under `innsbruck_230m/data/Data/Calibrations/Node A/Local_ion_photon_entanglement/<scan>/`. `load_scan` reads only these three per scan [V, code]; the APD*.raw files are not needed.
  - Scans: `1651`, `1655`, `1653.02`, `1659`, `1656`, `1702.02`
  - In each: `<scan>.dat`, `Photons_time.dat`, `Parameters.txt`
- Optional: `Readme.txt` and `Measurement_basis_and_scan_number.PNG` (the basis map). **Do not stage** `Analysis_fidelity_and_matrices.png`; it stayed blind in Stage 1.
- Alternative: run the export on the Mac VM, where numpy and pandas exist (the Stage 1 script was written for it), and stage only the resulting per-shot CSV.

**USTC: needed for R3 or the plug-in values**
- `ustc_2026/Fig_S8.xlsx`, `Fig_4b.xlsx`, `Fig_4c.xlsx`, `Fig_4d.xlsx`, `Fig_3a.xlsx`, `Fig_3d.xlsx`, `Fig_S3b.xlsx`
- `ustc_2026/stage1/out_ustc.json` (already in the cloud as `/home/claude/s26/recipe/out_ustc.json`)
- **Not on the Mac:** the paper's Supplementary Information (setting probabilities, set sizes, CHSH angles, finite-key assumptions). It must be downloaded or requested.

**Innsbruck ion–ion: only if an exploratory R4 is approved**
- `innsbruck_230m/stage2/events.csv`, `runs.csv`, `CHOICES.md`, `gate.json`
- `innsbruck_230m/STAGE2_RESULT.md`

---

## 8. Open items and checks before the prereg is locked
1. Have someone check the two derivations made here:
   - the Chernoff–KL bound is valid for adaptive Bernoulli sequences at fixed n;
   - the averaged Kaniewski bound holds over rounds with conditional states.
2. Read the USTC Supplementary Information: setting probabilities, per-set sizes, CHSH angles, herald/setting timing, and the finite-key assumptions.
3. Check that the scan names are clock times. Parameters.txt has no timestamp line in a quick grep; file modification times inside Data.zip may help.
4. Decide whether R1-C failing (detector-swapped halves disagree) should downgrade R1-A from "certified" to "conditional". The current proposal is that it labels the certificate but does not void it.
