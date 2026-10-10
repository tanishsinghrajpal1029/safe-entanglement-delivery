# Study 18C: multi-hop delivery near the feasibility frontier under link drift

This is Claude's working area in `Files11-EndToEnd-PRX-Claude`, and it is still **development, not a claim**. The scientific background is in `../18_audit_independent/EVIDENCE_LEDGER.md` (entries E10–E12).

## Gate 1 checks for the surrogate used in E10/E11

The checks run in order:

1. **`check_surrogate_numpy.py`** (done, no NetSquid; output in `out_check_surrogate_numpy.txt`). It compares the closed forms against an exact 4-qubit NumPy circuit.
   - The DEJMPS formula for Werner inputs is exact (agreement to 10⁻¹⁵).
   - **Failure, retained:** the drift study's gate-error shortcut, (1−e)F′ + e/4, is *optimistic*. It is wrong by up to 0.0024, 0.0040 and 0.0079 at e = 0.003, 0.005 and 0.01. The E11 numbers for purified paths must be recomputed with the exact gate model before any use.
2. **`netsquid_surrogate_check.py`** (run on the Mac). The same comparisons, done in NetSquid's density-matrix formalism:
   - 60 random swap chains (L = 2–4, storage, BSM error);
   - 18 DEJMPS cases, 3,000 trials each.

   Output: `logs/netsquid_surrogate_check.json`.

**Pass criteria, fixed before running:**
- Chains: max |F_NetSquid − F_formula| < 10⁻⁹.
- DEJMPS: NetSquid success probability within 4 standard errors of the NumPy exact value. NetSquid fidelity within 0.003 of NumPy exact, which allows Monte Carlo mixing of the two outcome branches.
- Expected: NetSquid ≈ exact, and below the surrogate whenever e > 0.
