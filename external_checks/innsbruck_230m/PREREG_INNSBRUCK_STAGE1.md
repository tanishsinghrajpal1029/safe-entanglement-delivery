# Innsbruck 230 m dataset, Stage 1: can we rebuild the authors' analysis from raw data? (pre-registered 7 Oct 2026, before any reconstruction)

Ledger: E60 (data obtained). This file: E61.

## Why
The dataset (Zenodo 7031042, CC-BY) is raw: PMT counts per ion readout and APD photon time tags. No processed outcomes and no analysis code.
Before we use any ion-ion data to test our controller's assumptions, our reconstruction must reproduce a result the authors computed themselves.

## Target (validation only, not a hypothesis about our controller)
`Calibrations/Node A/Local_ion_photon_entanglement`: 18 scans (1650.02–1703.02), basis map in `Measurement_basis_and_scan_number.PNG`, authors' result in `Analysis_fidelity_and_matrices.png`.

## Gate (fixed now)
G1 PASS if our reconstructed ion-photon state fidelity is within max(2 × the authors' quoted 1-sigma uncertainty, 0.02) of the authors' value.
G2 (supporting) the reconstructed density-matrix elements match the authors' plotted matrix to within 0.05 absolute on every element we can read from their figure.
Free choices allowed BEFORE comparison, and logged: PMT bright/dark threshold, photon detection time window, APD channel-to-polarisation mapping. Each choice must be justified from the data alone (histogram minimum; wavepacket envelope; the authors' readme), NOT tuned against the authors' number.
Allowed AFTER a fail: one documented fix of a decoding bug (wrong file format, wrong channel), never a re-tuning of thresholds to hit the target. If G1 still fails, Stage 2 is abandoned and reported as "raw data not reproducible by us".

## Stage 2 (outline only; frozen in a separate file after G1 passes and before any ion-ion statistic is computed)
Ion-ion runs (9 settings, ~20 Jul 2021 18:19–00:14). Questions for our controller's assumptions:
- S2-a: are per-window correlation counts consistent with binomial sampling at a constant rate (overdispersion test), or do they drift?
- S2-b: drift amplitude over the ~6 h session, in units of the per-window noise, compared with the A used in simulation.
- S2-c: posterior-predictive calibration of the Jeffreys/exact binomial likelihood used by the controller, on held-out windows.
No claim about delivered-pair risk on hardware will be made from this dataset (no deliver/discard decisions exist in it).
