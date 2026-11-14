"""Helpers for Study 41b tests: run job_41b.py as Qollab would against a local Aer backend; decode errors."""
import sys, types, enum, uuid, io, contextlib, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(HERE) == "tests": HERE = os.path.dirname(HERE)          # helpers live in tests/
class EM(enum.Enum):
    NO_DEBIASING = "no_debiasing"
sys.modules["qiskit_ionq"] = types.SimpleNamespace(ErrorMitigation=EM, __version__="fake")
from qiskit_aer import AerSimulator

class Fake:
    def __init__(s, name, nq, sim, t0=1_763_000_000_000):
        s.name, s.num_qubits, s.sim, s.t = name, nq, sim, [t0]
    def run(s, qc, shots, error_mitigation=None):
        assert error_mitigation is EM.NO_DEBIASING and not isinstance(qc, list)
        c = s.sim.run(qc, shots=shots).result().get_counts(); s.t[0] += 300_000
        jid = str(uuid.UUID(f"{s.t[0]:012x}7abc8" + "0" * 15))
        return types.SimpleNamespace(job_id=lambda: jid, result=lambda: types.SimpleNamespace(get_counts=lambda: c),
                                     _metadata={"backend": "qpu.forte-1", "settings": {"error_mitigation": {"debiasing": False}}})

def run_job(job, backend, path=os.path.join(HERE, "job_41b.py")):
    src = open(path).read().replace("JOB = 0", f"JOB = {job}", 1)
    ns = {"__name__": "__main__", "backend": backend}; buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(src, ns); ns["main"]()
    return json.loads(buf.getvalue().splitlines()[-1])

def group_errors(d):
    nq = sum(len(g) for g in d["groups"]); out = []
    for g, t in zip(d["groups"], d["tests"]):
        e = 0
        for h, c in d["counts_hex"].items():
            b = format(int(h, 16), f"0{nq}b")[::-1]; bits = [int(b[q]) for q in g]
            if t == "Z": fail = len(set(bits)) > 1
            else: fail = (-1) ** sum(bits) != (-1) ** (t.count("Y") // 2)
            e += c * fail
        out.append(e / d["shots"])
    return out
