"""Hardware test-or-keep experiment (Study 31): certificate (Prop. C1) and model check (Prop. MC) on a real QPU.

Each "delivered pair" is one shot of a two-qubit Bell-pair circuit. A pre-drawn, seeded schedule decides for every pair:
  - its source state: Phi+ (good) or Psi- (bad, injected),
  - test (probability p) in a uniformly random basis X/Y/Z, or keep.
Kept pairs are measured in the Bell basis (CX, H, Z-measurement; '00' = Phi+), which on a QPU is possible because both
qubits are local; this gives an (approximate) ground-truth label for each kept pair. Pairs that share (state, measurement)
run as shots of one circuit; outcomes are assigned to the pairs of that group in schedule order (shots are exchangeable).
Phases (in schedule order):
  0  calibration: 600 pairs, all tested, no injection  -> declared fidelity F_decl = lower 95% bound (Lemma F)
  A  1,000 pairs, p = 0.2, no injection                -> model check should NOT alarm (F_true >= F_decl)
  B  2,300 pairs, p = 0.2, Psi- injected w.p. 0.20     -> model check SHOULD alarm (unannounced source degradation)
The certificate runs over the kept pairs of A and B; it is compared, after every kept pair, with the Bell-measured pass
fraction of the kept pairs (approximate truth: the Bell measurement has its own error, reported separately).
Modes:
  --simulate   numpy simulation (depolarising + readout noise); no Qiskit needed
  --aer        Qiskit Aer with a fake IBM backend (free, local) - run this first to check the Qiskit path
  --hardware   IBM Quantum (uses the account you saved yourself with QiskitRuntimeService.save_account; this script
               never reads or asks for credentials). Hard caps: <= 4,000 shots in one job, max_execution_time = 120 s.
"""
import argparse, json, hashlib, time, sys, os
import numpy as np
from scipy.stats import beta as betad
from cert import Certifier
from mcheck import ModelCheck

SEED = 31031; P = 0.2; F_INJ = 0.20; N0, NA, NB = 600, 1000, 2300; SMAX = 0.05; ALPHA = 0.05; BETA = 0.05; MAX_SHOTS = 4000
STATES = ("good", "bad"); MEAS = ("X", "Y", "Z", "BELL")


def schedule(seed=SEED):
    rng = np.random.default_rng(seed); S = []
    for phase, n, p, f in (("0", N0, 1.0, 0.0), ("A", NA, P, 0.0), ("B", NB, P, F_INJ)):
        for _ in range(n):
            st = "bad" if rng.random() < f else "good"
            m = MEAS[int(rng.integers(3))] if rng.random() < p else "BELL"
            S.append((phase, st, m))
    return S


def error_of(meas, bits):
    """bits: 2-char string (qubit order q1q0 as Qiskit prints); error pattern that Phi+ never gives."""
    a, b = int(bits[-1]), int(bits[-2])
    if meas in ("X", "Z"): return int(a != b)
    if meas == "Y": return int(a == b)
    return int(bits[-2:] != "00")                     # BELL: 1 = not Phi+


def simulate_outcomes(S, dep=0.06, ro=0.015, seed=1):
    """numpy model: good pair = Werner with visibility 1-dep; bad = Psi-; independent readout flips per qubit."""
    rng = np.random.default_rng(seed); out = []
    for _, st, m in S:
        if st == "bad": lab = "psi-"
        else: lab = "phi+" if rng.random() > 0.75 * dep else ["phi-", "psi+", "psi-"][int(rng.integers(3))]
        # parity of outcome in each basis for the four Bell states: Phi+ (XX=+,YY=-,ZZ=+), Phi- (-,+,+), Psi+ (+,+,-), Psi- (-,-,-)
        sign = {"phi+": (1, -1, 1), "phi-": (-1, 1, 1), "psi+": (1, 1, -1), "psi-": (-1, -1, -1)}[lab]
        if m == "BELL":
            code = {"phi+": "00", "phi-": "01", "psi+": "10", "psi-": "11"}[lab]
            bits = list(code)
        else:
            k = "XYZ".index(m); a = int(rng.integers(2)); same = sign[k] > 0
            bits = [str(a if same else 1 - a), str(a)]
        bits = [str(int(x) ^ int(rng.random() < ro)) for x in bits]
        out.append("".join(bits))
    return out


def build_circuits():
    from qiskit import QuantumCircuit
    circs = {}
    for st in STATES:
        for m in MEAS:
            qc = QuantumCircuit(2, 2, name=f"{st}_{m}")
            qc.h(0); qc.cx(0, 1)                               # Phi+
            if st == "bad": qc.x(1); qc.z(0)                   # Psi-
            if m == "X": qc.h([0, 1])
            elif m == "Y": qc.sdg([0, 1]); qc.h([0, 1])
            elif m == "BELL": qc.cx(0, 1); qc.h(0)
            qc.measure([0, 1], [0, 1]); circs[(st, m)] = qc
    return circs


def run_qiskit(S, mode, backend_name=None):
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2
    groups = {}
    for i, (_, st, m) in enumerate(S): groups.setdefault((st, m), []).append(i)
    assert len(S) <= MAX_SHOTS, "shot cap"
    circs = build_circuits()
    if mode == "aer":
        from qiskit_ibm_runtime.fake_provider import FakeBrisbane
        from qiskit_aer import AerSimulator
        backend = AerSimulator.from_backend(FakeBrisbane())
    else:
        from qiskit_ibm_runtime import QiskitRuntimeService
        service = QiskitRuntimeService()                       # uses the account YOU saved; no credentials here
        backend = service.backend(backend_name) if backend_name else service.least_busy(operational=True, simulator=False)
    keys = [k for k in groups if groups[k]]
    tc = transpile([circs[k] for k in keys], backend=backend, optimization_level=1, seed_transpiler=SEED)
    sampler = SamplerV2(mode=backend)
    if mode == "hardware":
        sampler.options.max_execution_time = 120                # hard cap on billed QPU time (seconds)
        sampler.options.default_shots = 1
    pubs = [(c, None, len(groups[k])) for c, k in zip(tc, keys)]
    t0 = time.time(); job = sampler.run(pubs); res = job.result(); wall = time.time() - t0
    out = [None] * len(S)
    for k, r in zip(keys, res):
        bits = r.data.c.get_bitstrings()
        for i, b in zip(groups[k], bits): out[i] = b
    meta = dict(backend=getattr(backend, "name", str(backend)), job_id=getattr(job, "job_id", lambda: "local")(), wall_s=round(wall, 1),
                layouts=[str(getattr(c, "layout", None) and c.layout.final_index_layout()) for c in tc])
    try: meta["usage_s"] = job.usage()
    except Exception: pass
    return out, meta


def analyse(S, out):
    # phase 0: declared fidelity from all-test calibration (Lemma F: 1 - F = 1.5 * mean error; one-sided 95% CP)
    e0 = [error_of(m, b) for (ph, _, m), b in zip(S, out) if ph == "0"]
    k0, n0 = sum(e0), len(e0); ub = betad.ppf(0.95, k0 + 1, n0 - k0)
    F_decl = 1 - 1.5 * ub
    cert = Certifier(P, ALPHA, rmax=SMAX); mc = ModelCheck(BETA)
    K = Err = 0; passK = 0; viol = 0; first_alarm = None; trace = []; Lmax_gap = -1; tests = {"A": 0, "B": 0}
    for i, ((ph, st, m), b) in enumerate(zip(S, out)):
        if ph == "0": continue
        E = error_of(m, b)
        if m != "BELL":
            tests[ph] += 1; Err += E
            q = (2 / 3) * (1 - F_decl)
            if mc.update(E, q) and first_alarm is None: first_alarm = (i, ph)
        else:
            K += 1; passK += 1 - E
            L = cert.lower(Err, K); truth = passK / K
            if L > truth + 1e-12: viol = 1
            Lmax_gap = max(Lmax_gap, L - truth)
            if K % 100 == 0: trace.append(dict(i=i, phase=ph, K=K, L=round(L, 4), bell_pass=round(truth, 4)))
    bellA = [1 - error_of(m, b) for (ph, st, m), b in zip(S, out) if ph == "A" and m == "BELL"]
    bellB = [1 - error_of(m, b) for (ph, st, m), b in zip(S, out) if ph == "B" and m == "BELL"]
    return dict(n0=n0, err0=k0, F_hat0=round(1 - 1.5 * k0 / n0, 4), F_decl=round(float(F_decl), 4), tests=tests, kept=K,
                cert_final=round(cert.lower(Err, K), 4), bell_pass_final=round(passK / K, 4), cert_violation=viol,
                max_cert_minus_truth=round(float(Lmax_gap), 4), alarm_index=None if first_alarm is None else first_alarm[0],
                alarm_phase=None if first_alarm is None else first_alarm[1],
                bell_pass_A=round(float(np.mean(bellA)), 4), bell_pass_B=round(float(np.mean(bellB)), 4), trace=trace)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--simulate", action="store_true"); g.add_argument("--aer", action="store_true"); g.add_argument("--hardware", action="store_true")
    ap.add_argument("--backend", default=None); ap.add_argument("--out", default="study31_result.json"); a = ap.parse_args()
    S = schedule(); sh = hashlib.sha256(json.dumps(S).encode()).hexdigest()[:16]
    if a.simulate: out, meta = simulate_outcomes(S), dict(backend="numpy-sim")
    else: out, meta = run_qiskit(S, "aer" if a.aer else "hardware", a.backend)
    res = analyse(S, out); res.update(meta=meta, schedule_sha=sh, mode="simulate" if a.simulate else ("aer" if a.aer else "hardware"),
                                      script_sha=hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16])
    json.dump(dict(result=res, outcomes=out), open(a.out, "w"))
    print(json.dumps({k: v for k, v in res.items() if k != "trace"}, indent=1))
