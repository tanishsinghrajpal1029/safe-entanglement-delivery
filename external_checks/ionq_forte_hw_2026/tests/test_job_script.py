"""Runs job_41a.py (as Qollab would: exec, then main()) against a noiseless local fake backend, to check circuits and decoding."""
import sys, types, enum, uuid, time, json, io, contextlib, os
import numpy as np
from qiskit_aer import AerSimulator
SIM = AerSimulator(method="matrix_product_state", seed_simulator=5)

class EM(enum.Enum):
    NO_DEBIASING = "no_debiasing"
sys.modules["qiskit_ionq"] = types.SimpleNamespace(ErrorMitigation=EM, __version__="fake")

class FakeBackend:
    def __init__(s, nq, name): s.num_qubits = nq; s.name = name
    def run(s, qc, shots, error_mitigation=None):
        assert not isinstance(qc, list) and error_mitigation is EM.NO_DEBIASING
        c = SIM.run(qc, shots=shots).result().get_counts()
        jid = str(uuid.UUID(f"{int(time.time()*1000):012x}7abc8" + "0"*15))
        return types.SimpleNamespace(job_id=lambda: jid, result=lambda: types.SimpleNamespace(get_counts=lambda: c))

def run(job, nq):
    src = open("main.py").read().replace("JOB = 0", f"JOB = {job}", 1)
    ns = {"__name__": "__main__", "backend": FakeBackend(nq, "fake_forte" if nq >= 36 else "fake_simulator")}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(src, ns); ns["main"]()
    lines = buf.getvalue().splitlines(); return lines, json.loads(lines[-1]), ns

def errors(d):
    out = []
    for ax, (a, b) in zip(d["axes"], d["pairs"]):
        e = 0
        for h, c in d["counts_hex"].items():
            bits = format(int(h, 16), f"0{2*d['n_pairs']}b")[::-1]
            e += c * ((bits[a] != bits[b]) if ax in "XZ" else (bits[a] == bits[b]))
        out.append(e / d["shots"])
    return np.array(out)

for job, nq in ((3, 36), (0, 36), (7, 36), (0, 29)):
    lines, d, ns = run(job, nq)
    e = errors(d); f = [int(k) for k in d["faulty"]]
    print(f"job {job} nq {nq}: {lines[0]}")
    print("   ", lines[1] if len(lines) > 2 else "", "| qasm lines", len(d["qasm"].splitlines()), "| ops", d["ops"])
    clean = [k for k in range(d["n_pairs"]) if k not in f]
    print(f"    errors on clean pairs: max {e[clean].max():.3f}; faulty {[(d['axes'][k], round(e[k],3)) for k in f]} (expected X/Y 0.146, Z 0)")
