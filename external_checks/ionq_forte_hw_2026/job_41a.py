# Study 41a job script (Qollab Playground, IonQ). Change ONLY the number on the next line; run once per job (0..29).
JOB = 0
RECOVER = ""   # leave empty. Only to recover a lost output: put that job's id here (same JOB number); nothing new is submitted.
# Qollab calls main() itself: do NOT add a call to main() below.
import json, hashlib
from qiskit import QuantumCircuit

SHOTS = 1000
THETA = 3.141592653589793 / 4          # planted phase size; sign per faulty pair is in the design table
# Design table, fixed before any hardware job (derived from seeds by make_design_41a.py; its hash is frozen).
TABLE = json.loads('''{"b_jobs":[0,1,2,7,8,9,18,21,23,29],"design":[{"axes":"XXYYZZXZYXZXZYZYXY","pairs":[[12,34],[31,3],[20,33],[23,28],[27,17],[13,5],[11,19],[4,6],[21,24],[1,7],[29,2],[35,8],[9,16],[25,22],[10,32],[15,26],[30,18],[14,0]],"faulty":{"1":-1,"4":1,"5":-1,"6":1,"8":-1,"13":1}},{"axes":"ZXZYZZYXYYYZXXXZXY","pairs":[[18,22],[10,27],[34,25],[14,9],[24,26],[12,19],[30,33],[2,35],[4,21],[23,15],[17,13],[29,7],[32,28],[3,20],[0,6],[5,31],[8,1],[16,11]],"faulty":{"4":-1,"5":1,"9":-1,"13":1,"14":-1,"17":1}},{"axes":"YYXXYZZYYXZZXZYXZX","pairs":[[4,5],[13,10],[18,28],[26,12],[29,2],[24,25],[21,19],[14,0],[1,11],[3,27],[34,16],[17,31],[35,6],[22,20],[9,32],[30,15],[8,33],[7,23]],"faulty":{"1":-1,"8":1,"9":-1,"11":1,"13":-1,"15":1}},{"axes":"XXYZZZZYZXYXXYZYYX","pairs":[[7,3],[16,19],[34,30],[14,10],[24,22],[31,21],[35,26],[2,25],[6,13],[9,23],[20,11],[33,8],[32,18],[15,5],[12,17],[28,0],[29,4],[1,27]],"faulty":{}},{"axes":"ZXYZXZXYZYXYZXZYYX","pairs":[[10,35],[4,9],[22,16],[6,18],[8,28],[0,31],[23,29],[15,25],[1,26],[3,27],[30,19],[12,11],[32,17],[7,24],[13,5],[2,34],[20,33],[21,14]],"faulty":{}},{"axes":"XXZXYYZXYXYZZZYYZX","pairs":[[10,17],[6,12],[31,16],[13,28],[8,4],[1,0],[21,20],[22,3],[11,18],[32,30],[34,26],[25,14],[24,9],[7,23],[19,33],[5,27],[2,15],[35,29]],"faulty":{}},{"axes":"XZXYZYYZXYXYXZZYXZ","pairs":[[33,29],[24,18],[1,15],[30,13],[3,26],[25,35],[16,32],[27,21],[28,19],[9,20],[12,22],[2,7],[8,10],[4,17],[23,5],[31,6],[0,11],[14,34]],"faulty":{}},{"axes":"XXXYZZYYZZYYZYXZXX","pairs":[[25,26],[21,20],[1,24],[27,16],[30,0],[23,2],[22,33],[5,10],[17,18],[32,19],[11,31],[15,4],[8,14],[3,7],[29,28],[35,13],[12,6],[34,9]],"faulty":{"1":1,"2":-1,"5":-1,"7":-1,"11":1,"12":1}},{"axes":"XZYXYZXZYZZXZYYXXY","pairs":[[19,1],[32,0],[8,35],[18,2],[9,29],[31,23],[14,13],[30,22],[27,3],[33,6],[5,25],[28,34],[15,21],[11,24],[12,4],[20,10],[26,16],[17,7]],"faulty":{"0":-1,"1":1,"6":1,"8":1,"9":-1,"17":-1}},{"axes":"YXYZYYZXXXZYXYZZXZ","pairs":[[2,19],[28,12],[35,7],[8,27],[11,9],[14,30],[16,0],[34,32],[6,21],[23,1],[25,10],[13,15],[31,26],[24,22],[29,33],[17,18],[3,4],[5,20]],"faulty":{"4":1,"6":1,"8":1,"9":-1,"11":-1,"15":-1}},{"axes":"ZYZYZYZYXYYXXXZXXZ","pairs":[[15,28],[13,3],[21,29],[12,0],[26,22],[33,17],[35,16],[2,7],[10,34],[31,20],[23,4],[30,9],[5,32],[27,1],[24,6],[14,25],[19,18],[11,8]],"faulty":{}},{"axes":"XYZXYXXYYZZXZZYZYX","pairs":[[21,2],[5,31],[6,14],[24,3],[26,28],[16,0],[29,20],[15,23],[18,25],[27,8],[1,4],[33,35],[12,9],[13,32],[10,22],[19,34],[7,11],[30,17]],"faulty":{}},{"axes":"ZYZYXYZYZZXYXXXXYZ","pairs":[[5,34],[3,14],[10,4],[16,25],[9,11],[1,24],[23,30],[21,8],[31,15],[32,18],[28,19],[13,17],[7,26],[2,33],[12,22],[29,0],[20,35],[6,27]],"faulty":{}},{"axes":"ZYYZZYXYZZXYXXZXYX","pairs":[[18,15],[6,29],[14,26],[10,22],[2,11],[0,35],[4,30],[1,12],[33,25],[28,8],[32,9],[21,19],[27,31],[13,34],[3,23],[17,7],[16,20],[5,24]],"faulty":{}},{"axes":"ZYZYXZZYXXYZXZXYXY","pairs":[[17,2],[7,16],[24,35],[29,15],[27,22],[28,4],[25,26],[0,12],[23,31],[32,11],[13,14],[8,18],[19,30],[1,33],[9,6],[5,3],[21,34],[20,10]],"faulty":{}},{"axes":"YZZZXYZXYZXZXYYXYX","pairs":[[0,7],[1,26],[9,12],[3,34],[20,35],[21,22],[10,24],[6,25],[31,30],[19,33],[4,17],[2,28],[32,16],[15,5],[13,11],[27,18],[8,23],[14,29]],"faulty":{}},{"axes":"ZXYZYYXXYYXZZZXZYX","pairs":[[6,14],[27,33],[17,11],[32,29],[28,20],[25,24],[31,30],[9,16],[2,3],[8,10],[12,34],[19,15],[4,18],[0,7],[5,13],[21,23],[1,35],[26,22]],"faulty":{}},{"axes":"XYZXZZZYZXXZXYYYXY","pairs":[[32,18],[12,2],[1,16],[13,10],[34,19],[25,3],[15,0],[21,30],[22,28],[11,24],[4,9],[5,29],[35,8],[33,26],[31,20],[27,17],[7,6],[14,23]],"faulty":{}},{"axes":"YXYZZYXYYXYZZZZXXX","pairs":[[1,13],[5,30],[35,21],[14,32],[25,34],[8,16],[4,20],[29,2],[0,15],[10,18],[24,27],[33,26],[6,17],[9,22],[11,3],[7,31],[12,19],[28,23]],"faulty":{"4":-1,"7":1,"10":-1,"13":1,"16":-1,"17":1}},{"axes":"YXZYXZYZZXYXYXXYZZ","pairs":[[29,19],[17,15],[8,4],[3,33],[24,18],[28,32],[9,12],[10,13],[2,31],[26,1],[6,5],[22,35],[34,30],[14,20],[16,11],[0,21],[27,25],[23,7]],"faulty":{}},{"axes":"YYXXXZZZXZZZYXYYXY","pairs":[[23,35],[9,6],[3,5],[34,8],[18,33],[10,14],[2,4],[17,24],[13,19],[7,12],[27,21],[25,11],[31,30],[22,29],[26,20],[0,16],[15,1],[32,28]],"faulty":{}},{"axes":"ZYZZYXZXYXYYXXZZXY","pairs":[[0,23],[27,34],[12,14],[8,15],[11,13],[20,10],[21,1],[33,17],[22,26],[30,4],[28,18],[9,2],[32,3],[35,6],[19,7],[29,25],[16,24],[5,31]],"faulty":{"9":1,"10":-1,"11":1,"12":-1,"14":-1,"15":1}},{"axes":"YZXXYZZYXXZXZYXYYZ","pairs":[[1,19],[17,35],[4,9],[26,13],[3,15],[12,34],[30,33],[0,31],[18,25],[6,5],[14,28],[21,7],[22,32],[11,2],[8,23],[24,29],[20,27],[10,16]],"faulty":{}},{"axes":"YXYZZYXZXZXYZXYYZX","pairs":[[7,27],[5,1],[19,15],[11,12],[25,34],[35,10],[6,13],[26,21],[20,23],[29,14],[3,30],[22,9],[32,31],[16,17],[4,28],[18,2],[24,33],[0,8]],"faulty":{"1":1,"2":-1,"7":1,"9":-1,"15":1,"17":-1}},{"axes":"ZZXXXZYYYXYZZYXZXY","pairs":[[22,10],[1,35],[4,15],[8,16],[13,32],[23,20],[2,18],[12,5],[25,27],[3,9],[19,21],[11,29],[34,26],[28,6],[30,17],[14,33],[7,31],[24,0]],"faulty":{}},{"axes":"ZXXYYZYYYZXXZXXZYZ","pairs":[[23,28],[35,20],[13,6],[18,9],[32,7],[24,15],[10,34],[19,12],[1,5],[25,22],[31,33],[3,0],[26,2],[4,8],[29,14],[16,27],[30,11],[21,17]],"faulty":{}},{"axes":"YZZYZYYXXYZXXZXYXZ","pairs":[[8,30],[9,14],[4,31],[23,12],[16,3],[29,15],[19,13],[28,25],[10,5],[32,11],[21,18],[20,2],[26,6],[1,17],[7,22],[0,24],[34,27],[35,33]],"faulty":{}},{"axes":"YZYXYYXXYZXYZXZZZX","pairs":[[2,23],[35,29],[10,31],[18,27],[30,5],[8,33],[13,12],[16,22],[32,0],[14,15],[25,9],[24,11],[21,19],[6,1],[3,20],[34,17],[28,4],[26,7]],"faulty":{}},{"axes":"XYXXZXYZYZYXZZYXYZ","pairs":[[1,2],[29,18],[4,23],[19,0],[8,28],[33,6],[16,9],[12,22],[31,21],[35,27],[13,30],[17,5],[10,34],[11,24],[3,25],[7,14],[15,32],[20,26]],"faulty":{}},{"axes":"XXXXYYZYZZZYYYZZXX","pairs":[[5,31],[7,24],[21,27],[22,19],[34,20],[23,25],[29,0],[8,26],[35,12],[10,13],[30,6],[16,2],[14,18],[33,11],[15,4],[28,1],[17,3],[32,9]],"faulty":{"1":-1,"5":1,"6":-1,"10":1,"13":-1,"17":1}}]}''')
B_JOBS = TABLE["b_jobs"]


def circuit(axes, pairs, faulty, n):
    qc = QuantumCircuit(n, n)
    for k, (ax, (a, b)) in enumerate(zip(axes, pairs)):
        qc.h(a); qc.cx(a, b)                       # Phi+ = (|00> + |11>)/sqrt2
        if str(k) in faulty:
            qc.rz(faulty[str(k)] * THETA, a)       # planted phase error +-theta (Block B only)
        for q in (a, b):
            if ax == "X": qc.h(q)
            if ax == "Y": qc.sdg(q); qc.h(q)
    qc.measure(range(n), range(n))                 # qubit q -> classical bit q (rightmost character of a key = bit 0)
    return qc


def rehearsal(d, n_pairs=12):
    """Simulator rehearsal only (29 qubits): first 12 pairs of the job's design, qubits relabelled 0..23."""
    pairs = d["pairs"][:n_pairs]; used = sorted(q for p in pairs for q in p); lab = {q: i for i, q in enumerate(used)}
    return {"axes": d["axes"][:n_pairs], "pairs": [[lab[a], lab[b]] for a, b in pairs],
            "faulty": {k: v for k, v in d["faulty"].items() if int(k) < n_pairs}}


def n_qubits():
    for f in (lambda: backend.num_qubits, lambda: backend.configuration().n_qubits):
        try:
            return int(f())
        except Exception:
            pass
    return None


def emit(out):
    s = json.dumps(out, separators=(",", ":"), default=str)
    print("JOB", out["job"], "BLOCK", out["block"], "MODE", out["mode"], "SHA", hashlib.sha256(s.encode()).hexdigest()[:16], "LEN", len(s), flush=True)
    try:
        from js import sendFile
        name = f"s41a_job_{out['job']:02d}{'_recovered' if out.get('recovered') else ''}{'_' + out['mode'] if out['mode'] != 'hardware' else ''}.json"
        sendFile(name, "application/json", s)
        print("download offered:", name, flush=True)
    except Exception as e:
        print("no download:", e, flush=True)
    print(s, flush=True)


def main():
    import qiskit
    from qiskit import qasm2
    from qiskit_ionq import ErrorMitigation
    assert 0 <= JOB < len(TABLE["design"])
    name = str(getattr(backend, "name", "?")); low = name.lower(); nq = n_qubits()
    if "simulator" in low:
        mode, d = "rehearsal", rehearsal(TABLE["design"][JOB])
    elif "forte" in low:
        mode, d = "hardware", TABLE["design"][JOB]
    else:
        raise RuntimeError(f"unexpected backend {name!r}; nothing was submitted")
    n = 2 * len(d["pairs"])
    qc = circuit(d["axes"], d["pairs"], d["faulty"], n)
    out = {"study": "41a", "job": JOB, "block": "B" if JOB in B_JOBS else "A", "mode": mode, "n_pairs": len(d["pairs"]),
           "axes": d["axes"], "pairs": d["pairs"], "faulty": d["faulty"], "shots": SHOTS, "backend": name, "n_qubits": nq,
           "debias_requested": str(ErrorMitigation.NO_DEBIASING), "qasm": qasm2.dumps(qc),
           "versions": {"qiskit": qiskit.__version__}}
    try:
        import qiskit_ionq; out["versions"]["qiskit_ionq"] = qiskit_ionq.__version__
    except Exception:
        pass
    print("READY: job", JOB, "block", out["block"], "mode", mode, "backend", name, "qubits", nq, "pairs", out["n_pairs"], flush=True)
    if RECOVER:
        job = backend.retrieve_job(RECOVER); out["recovered"] = True
    else:
        job = backend.run(qc, shots=SHOTS, error_mitigation=ErrorMitigation.NO_DEBIASING)
    out["job_id"] = job.job_id()
    print("SUBMITTED: job id", out["job_id"], "(keep this line)", flush=True)
    try:
        res = job.result()
        counts = res.get_counts()
        out["counts_hex"] = {format(int(k.replace(" ", ""), 2), "x"): int(v) for k, v in counts.items()}
    except Exception as e:
        out["error"] = repr(e)
        print("RESULT ERROR:", repr(e), "-- the job id above can be recovered with RECOVER", flush=True)
        try:
            print("raw counts:", repr(counts), flush=True)
        except Exception:
            pass
    try:
        probs = res.get_probabilities()
        probs = probs[1] if isinstance(probs, tuple) else probs
        out["prob_check"] = {"n": len(probs), "sum": float(sum(probs.values()))}
    except Exception as e:
        out["prob_check"] = "unavailable: " + type(e).__name__
    try:
        meta = {k: v for k, v in getattr(job, "_metadata", {}).items() if k not in ("metadata", "data", "results")}
        sm = json.dumps(meta, default=str)
        out["ionq_meta"] = json.loads(sm) if len(sm) <= 6000 else sm[:6000]
    except Exception as e:
        out["ionq_meta"] = "unavailable: " + type(e).__name__
    emit(out)
