# Study 30: adversarial review before the pilot (11 Oct 2026)

**Reviewer:** an independent agent acting as a hostile PRX referee and code reviewer, with no edit rights. It read THEORY_30.md, core30.py, study30.py, study29.py, mcheck.py and cs_lower_mix, and ran 2 full simulations plus offline checks.

**Verified correct**
- Theorem 2's steps:
  - Lemma A;
  - c_i is predictable;
  - every factor is ≥ 0.1;
  - K_t(m) is nondecreasing in m;
  - Ville bound with spending 6/(π²k²);
  - per-user union (lower ends on u's links, upper ends on all 40 links);
  - a_i ≤ â_i holds even when F_M > 1.
- Fhi uses the previous epoch on both the probe path and the test path.
- No pair is counted twice.
- The guard is F0 − U·φ; the check's q uses the actual guard.
- kgMCa starts at θ_max with its window at t = 0.
- The forced-alarm path works for every detector.
- PlugInCheck and HybridCheck are valid e-processes.
- kgMT matches Study 29 apart from seeds.

## Findings and resolution

| # | Severity | Finding | Resolution |
|---|---|---|---|
| B1 | Blocker | Remark 1 claimed kgMCa covers every pair. False under late onset: smoke run had 3,960 bad pairs and no alarm in 60 epochs | Claim restricted to "(B2) from t = 0, no onset"; kgMCa in L0.044 pre-registered as expected failure |
| B2 | Blocker | A false or forced alarm before onset breaks (B2); the text implied otherwise | (B2) restated "after the first alarm, one θ"; Corollary O (onset class) adds β; cell L0.044F added |
| B3 | Blocker | "No debt" false when the guard is nearly exact: plug-in loses about 1.1 nats per 1,000 tests at q − p = 0.004 | Reworded to "limited debt"; hybrid check made the default; detector table added; lower-confidence variants tried and rejected (lose hardware power) |
| B4 | Blocker | Optimism added to the model let F_M exceed 1 (2.7–63% of attempts), clipping q to 10⁻⁶ | Offset moved into the truth (extra depolarizing noise). Affects the Study 28–29 detection power; disclosed |
| M1 | Major | (B2) needs exact proportionality; no near-class or heterogeneous cell | h0.044 cell added (per-link Gamma offsets, out of class) |
| M2 | Major | No static baseline | '-_fix', 'o0.044_fix' added (margin 0.10 from t = 0) |
| M3 | Major | Pre-alarm exposure dominates the headline metric | Whole-run per-user risk reported and pre-registered; per-user bound stated as 0.10 |
| M4 | Major | Post-alarm counters excluded warm-up; no whole-run violation counters | `*_after_alarm_all`, `viol_all`, `below_all` added |
| M5 | Major | OffsetCS consumed k = 1 at construction (first window at k = 2) | Fixed: k = 0 until the first restart; kgMCa restarts at t = 0 |
| M6 | Major | Re-alarm after a post-alarm change untested; mixture builds debt during the θ_max phase | L0.044F added; check restarted (with spending) when U falls by 0.01 |
| M7 | Major | H̄ origin unclear; s-offset not matched; φ unbounded | H̄ = 0.0105 (mean hold over attempts, dev network 0, both hw); φ capped at 3; realised mean offset reported per run |
| M8 | Major | θ_max = 0.10 sits just above the largest offset | Justified as about 2× the measured gaps (0.02–0.044); out-of-B4 not tested (stated) |

**Minor items, all fixed**
- notation of the bet grid;
- definition of the empty set (U = 0) and a pessimism diagnostic;
- cs_upper_mix now returns the conservative end;
- A_MAX docstring;
- Lemma A conditions (F ≥ 1/4; symmetric readout);
- Prop D's bound is stated on G1;
- remark on the conservative union;
- mcheck hash recorded (a05f0822, identical to Study 28);
- the 14/500 null unit check is labelled underpowered.
