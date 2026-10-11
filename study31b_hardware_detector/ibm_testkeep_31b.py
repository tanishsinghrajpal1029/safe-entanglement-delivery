"""Study 31b: hardware rerun of the test-or-keep experiment with the hybrid model check (Prop. D) - pre-registered.

Identical to Study 31 (ibm_testkeep.py, sha 3b94867c13068e85, imported unchanged) except:
  1. a FRESH schedule seed (SEED_31B = 31032), so no pair, basis or injection pattern is shared with Study 31;
  2. the PRIMARY model check is core30.HybridCheck (average of the fixed-bet mixture and the plug-in e-process, written
     after Study 31's summary rates were seen and frozen in core30.py sha 9091e3364b19fe56 before this run);
     Study 31's mixture check (mcheck.ModelCheck) runs on the same outcomes as a paired comparison;
  3. after the first hybrid alarm, the offset confidence sequence of Theorem 2 (core30.OffsetCS, level 0.025, constant
     class, no declared maximum: U starts at 1) runs on the post-alarm tests with a_i = F_decl - 1 + 1.5 E_i, and its final
     value U is compared with the Bell-measured offset of the post-alarm kept pairs (secondary, W5).
Phases, sizes, injection, certificate, readout bound, levels and caps are Study 31's: 3,900 shots in one job, <= 4,000 cap,
max_execution_time = 120 s. Hardware mode uses the IBM account YOU saved; this script never reads or asks for credentials.
Modes: --simulate [--dep0 D] (numpy; D = depolarising in phase 0 only, to mimic a conservative calibration), --aer, --hardware.
"""
import argparse, json, hashlib, sys, os
import numpy as np
from scipy.stats import beta as betad
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ibm_testkeep as base
from cert import Certifier
from mcheck import ModelCheck
from core30 import HybridCheck, OffsetCS

SEED_31B = 31032
P, ALPHA, BETA, SMAX = base.P, base.ALPHA, base.BETA, base.SMAX
ALPHA_TH = 0.025


def simulate(S, dep=0.06, dep0=None, ro=0.015, seed=1):
    """numpy model as Study 31; optionally a different depolarising level in phase 0 (calibration)."""
    if dep0 is None: return base.simulate_outcomes(S, dep=dep, ro=ro, seed=seed)
    o0 = base.simulate_outcomes([x for x in S if x[0] == "0"], dep=dep0, ro=ro, seed=seed)
    o1 = base.simulate_outcomes([x for x in S if x[0] != "0"], dep=dep, ro=ro, seed=seed + 7919)
    it0, it1 = iter(o0), iter(o1)
    return [next(it0) if x[0] == "0" else next(it1) for x in S]


def analyse(S, out):
    e0 = [base.error_of(m, b) for (ph, _, m), b in zip(S, out) if ph == "0"]
    k0, n0 = sum(e0), len(e0); F_decl = 1 - 1.5 * betad.ppf(0.95, k0 + 1, n0 - k0)
    q = (2 / 3) * (1 - F_decl)
    cert = Certifier(P, ALPHA, rmax=SMAX); hyb = HybridCheck(BETA); mix = ModelCheck(BETA); cs = OffsetCS(ALPHA_TH, 1.0)
    K = Err = passK = viol = 0; gap = -1.0; tests = {"A": 0, "B": 0}; first = {"hybrid": None, "mixture": None}
    trace = []; post_keep = post_pass = 0; Utrace = []
    for i, ((ph, st, m), b) in enumerate(zip(S, out)):
        if ph == "0": continue
        E = base.error_of(m, b)
        if m != "BELL":
            tests[ph] += 1; Err += E
            if hyb.update(E, q) and first["hybrid"] is None:
                first["hybrid"] = dict(i=i, phase=ph, test=tests[ph]); cs.restart()
            elif first["hybrid"] is not None:
                cs.add(F_decl - 1 + 1.5 * E, 1.0, F_decl + 0.5)
                if cs.n % 25 == 0: Utrace.append(dict(n=cs.n, U=round(cs.update(), 4)))
            if mix.update(E, q) and first["mixture"] is None: first["mixture"] = dict(i=i, phase=ph, test=tests[ph])
        else:
            K += 1; passK += 1 - E
            if first["hybrid"] is not None: post_keep += 1; post_pass += 1 - E
            L = cert.lower(Err, K); truth = passK / K
            if L > truth + 1e-12: viol = 1
            gap = max(gap, L - truth)
            if K % 100 == 0: trace.append(dict(i=i, phase=ph, K=K, L=round(L, 4), bell_pass=round(truth, 4)))
    U = cs.update() if first["hybrid"] is not None else None
    off_bell = (F_decl - post_pass / post_keep) if post_keep else None
    bell = lambda P_: round(float(np.mean([1 - base.error_of(m, b) for (ph, _, m), b in zip(S, out) if ph == P_ and m == "BELL"])), 4)
    return dict(n0=n0, err0=k0, F_decl=round(float(F_decl), 4), q=round(q, 4), tests=tests, kept=K,
                cert_final=round(cert.lower(Err, K), 4), bell_pass_final=round(passK / K, 4), cert_violation=viol,
                max_cert_minus_truth=round(gap, 4), alarm_hybrid=first["hybrid"], alarm_mixture=first["mixture"],
                U_final=None if U is None else round(U, 4), cs_tests=cs.n, post_alarm_kept=post_keep,
                offset_bell_post=None if off_bell is None else round(off_bell, 4),
                W1=viol == 0, W2=not (first["hybrid"] and first["hybrid"]["phase"] == "A"),
                W3=bool(first["hybrid"] and first["hybrid"]["phase"] == "B"),
                W5=None if (U is None or off_bell is None) else bool(U >= off_bell),
                bell_pass_A=bell("A"), bell_pass_B=bell("B"), trace=trace, U_trace=Utrace)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--simulate", action="store_true"); g.add_argument("--aer", action="store_true"); g.add_argument("--hardware", action="store_true")
    ap.add_argument("--backend", default=None); ap.add_argument("--out", default="study31b_result.json")
    ap.add_argument("--dep0", type=float, default=None); ap.add_argument("--simseed", type=int, default=1); a = ap.parse_args()
    S = base.schedule(SEED_31B); sh = hashlib.sha256(json.dumps(S).encode()).hexdigest()[:16]
    assert len(S) <= base.MAX_SHOTS
    if a.simulate: out, meta = simulate(S, dep0=a.dep0, seed=a.simseed), dict(backend="numpy-sim", dep0=a.dep0, simseed=a.simseed)
    else: out, meta = base.run_qiskit(S, "aer" if a.aer else "hardware", a.backend)
    res = analyse(S, out)
    res.update(meta=meta, schedule_sha=sh, seed=SEED_31B, mode="simulate" if a.simulate else ("aer" if a.aer else "hardware"),
               script_sha=hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16],
               base_sha=hashlib.sha256(open(base.__file__, "rb").read()).hexdigest()[:16])
    json.dump(dict(result=res, outcomes=out), open(a.out, "w"))
    print(json.dumps({k: v for k, v in res.items() if k not in ("trace", "U_trace")}, indent=1))
