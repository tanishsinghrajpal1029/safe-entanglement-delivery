"""Safety tests of job_41a.py with fake backends: wrong backend, result failure, recovery, rehearsal mode."""
import sys, types, enum, io, contextlib, json
class EM(enum.Enum):
    NO_DEBIASING = "no_debiasing"
sys.modules["qiskit_ionq"] = types.SimpleNamespace(ErrorMitigation=EM, __version__="fake")
JID = "01a1c80a-e2e7-7e72-8e41-fafca4d44be1"

class Fake:
    def __init__(s, name, nq, fail=False): s.name, s.num_qubits, s.fail, s.runs, s.retrieved = name, nq, fail, 0, 0
    def _job(s, qc):
        def result():
            if s.fail: raise TimeoutError("queue timeout")
            return types.SimpleNamespace(get_counts=lambda: {"0" * qc.num_qubits: 1000}, get_probabilities=lambda: {"0" * qc.num_qubits: 1.0})
        return types.SimpleNamespace(job_id=lambda: JID, result=result, _metadata={"target": "qpu.forte-1", "status": "completed"})
    def run(s, qc, shots, error_mitigation=None):
        s.runs += 1; s.last = qc; return s._job(qc)
    def retrieve_job(s, jid):
        s.retrieved += 1; return s._job(types.SimpleNamespace(num_qubits=36))

def go(backend, job=3, recover=""):
    src = open("main.py").read().replace("JOB = 0", f"JOB = {job}", 1).replace('RECOVER = ""', f'RECOVER = "{recover}"', 1)
    ns = {"__name__": "__main__", "backend": backend}; buf = io.StringIO(); err = None
    with contextlib.redirect_stdout(buf):
        try:
            exec(src, ns); ns["main"]()
        except Exception as e:
            err = repr(e)
    return buf.getvalue(), err

b = Fake("ionq_qpu", 36); out, err = go(b); print("generic name:", "runs", b.runs, "| error", err)
b = Fake("ionq_qpu.forte-1", 4); out, err = go(b); print("forte reporting 4 qubits: runs", b.runs, "| qubits in circuit", b.last.num_qubits)
b = Fake("ionq_qpu.forte-1", 36, fail=True); out, err = go(b)
print("result fails: runs", b.runs, "| job id printed", JID in out.split("\n")[1] if len(out.split("\n")) > 1 else False, "| output emitted", '"error"' in out, "| exception", err)
b = Fake("ionq_qpu.forte-1", 36); out, err = go(b, recover=JID); d = json.loads(out.strip().splitlines()[-1])
print("recover: runs", b.runs, "retrieved", b.retrieved, "| recovered flag", d.get("recovered"), "| counts", sum(d["counts_hex"].values()))
b = Fake("ionq_simulator", 29); out, err = go(b, job=0); d = json.loads(out.strip().splitlines()[-1])
print("rehearsal: mode", d["mode"], "pairs", d["n_pairs"], "qubits", b.last.num_qubits, "| faulty", d["faulty"])
