# Study 41b job script (Qollab Playground, IonQ): GHZ states. Change ONLY the number on the next line; run once per job (0..19).
JOB = 0
# Qollab calls main() itself: do NOT add a call to main() below.
import json, hashlib
from qiskit import QuantumCircuit

SHOTS = 1000
# Design table, fixed before any hardware job (derived from seeds by make_design_41b.py; its hash is frozen).
# Per job: n (3 or 4), groups of n qubits (first = H qubit, then a CX chain), and per group a test: "Z" or an XY string.
TABLE = json.loads('''{"sizes":[4,3,3,4,3,3,3,4,3,3,4,4,4,4,3,4,3,4,3,4],"design":[{"n":4,"groups":[[0,22,33,30],[21,27,7,32],[25,8,35,31],[26,14,16,1],[17,28,19,5],[13,12,20,15],[34,24,2,9],[11,23,18,3],[6,29,4,10]],"tests":["Z","YYYY","XXYY","Z","Z","YXYX","XYXY","YYXX","XXXX"]},{"n":3,"groups":[[9,27,13],[29,30,19],[34,3,35],[24,23,7],[20,28,16],[25,15,14],[18,26,33],[10,12,17],[4,31,0],[22,21,5],[1,11,32],[6,2,8]],"tests":["YYX","XYY","YXY","Z","XXX","XYY","YXY","XXX","Z","Z","Z","YYX"]},{"n":3,"groups":[[30,10,25],[3,27,11],[8,22,9],[24,33,6],[23,0,7],[16,31,14],[34,15,20],[26,32,5],[21,19,28],[1,35,18],[13,29,4],[2,17,12]],"tests":["YYX","YXY","YXY","Z","XXX","XXX","XYY","XYY","Z","YYX","Z","Z"]},{"n":4,"groups":[[18,0,2,26],[15,1,22,35],[29,32,10,4],[28,8,9,27],[13,20,6,12],[14,24,19,33],[7,30,17,34],[5,25,3,23],[11,16,31,21]],"tests":["YXYX","Z","Z","YYXX","XYXY","XYYX","XXXX","Z","YXXY"]},{"n":3,"groups":[[16,9,1],[22,2,29],[14,17,31],[28,13,34],[21,7,3],[19,18,5],[4,6,0],[35,27,30],[23,32,24],[8,33,20],[10,25,12],[26,15,11]],"tests":["XXX","YYX","XXX","Z","YXY","Z","YXY","Z","XYY","XYY","Z","YYX"]},{"n":3,"groups":[[11,9,17],[8,25,15],[4,34,32],[19,13,29],[30,5,22],[2,28,20],[35,24,3],[12,1,18],[21,10,6],[26,0,27],[14,23,7],[16,33,31]],"tests":["YYX","YXY","YXY","Z","Z","Z","YYX","XYY","Z","XXX","XYY","XXX"]},{"n":3,"groups":[[18,9,12],[30,16,13],[33,22,7],[6,3,10],[29,15,0],[27,24,4],[23,11,8],[31,2,35],[28,34,26],[1,25,32],[19,14,20],[21,5,17]],"tests":["Z","XYY","YXY","Z","Z","XXX","YYX","Z","XXX","YYX","YXY","XYY"]},{"n":4,"groups":[[26,0,27,33],[9,31,21,15],[32,11,1,2],[35,30,6,20],[19,17,8,12],[22,29,7,25],[23,13,16,10],[14,34,4,3],[18,24,5,28]],"tests":["Z","Z","Z","XYYX","YYXX","YXYX","YXXY","XXXX","YYYY"]},{"n":3,"groups":[[30,7,27],[17,22,6],[4,9,18],[20,5,8],[1,29,23],[11,32,2],[0,21,25],[13,12,28],[15,26,35],[14,33,34],[31,3,16],[24,10,19]],"tests":["YXY","Z","YYX","YYX","Z","XYY","XYY","Z","YXY","XXX","XXX","Z"]},{"n":3,"groups":[[24,22,9],[8,10,27],[0,1,14],[3,6,5],[11,16,34],[26,21,15],[35,23,25],[17,29,13],[32,12,7],[20,2,30],[31,18,28],[4,33,19]],"tests":["Z","YYX","XYY","XYY","Z","XXX","XXX","YYX","YXY","Z","Z","YXY"]},{"n":4,"groups":[[20,21,17,16],[23,18,14,31],[8,33,34,11],[27,7,9,3],[25,5,10,24],[29,26,4,32],[1,13,30,2],[28,0,22,6],[19,12,15,35]],"tests":["XYXY","YXXY","Z","Z","YYXX","XXYY","XYYX","Z","YXYX"]},{"n":4,"groups":[[15,2,21,35],[5,10,20,17],[16,24,19,33],[18,28,13,11],[30,26,31,27],[1,8,12,29],[9,22,6,23],[4,32,25,14],[7,3,34,0]],"tests":["XXXX","YYYY","YXXY","Z","Z","YYXX","XXYY","Z","XYXY"]},{"n":4,"groups":[[0,5,6,7],[28,25,4,20],[16,30,32,10],[26,9,34,11],[8,24,15,3],[27,17,35,13],[21,33,14,12],[23,19,18,1],[29,31,22,2]],"tests":["Z","Z","XYYX","YYYY","YXYX","XXYY","Z","XXXX","XYXY"]},{"n":4,"groups":[[15,8,4,6],[21,2,34,26],[10,11,18,32],[23,7,3,24],[30,1,12,20],[31,27,14,35],[5,17,0,22],[9,29,16,33],[19,25,13,28]],"tests":["YXYX","YXXY","XXXX","XYYX","XYXY","YYXX","Z","Z","Z"]},{"n":3,"groups":[[17,28,6],[9,32,20],[12,15,13],[10,35,5],[33,22,16],[29,14,1],[8,25,4],[34,11,30],[2,7,3],[23,24,27],[19,21,0],[18,26,31]],"tests":["XXX","YXY","YYX","Z","YYX","Z","XYY","YXY","XYY","XXX","Z","Z"]},{"n":4,"groups":[[12,5,9,33],[7,4,29,11],[6,13,18,22],[27,20,3,30],[19,8,23,32],[16,35,17,0],[31,26,2,1],[25,24,34,15],[21,14,10,28]],"tests":["Z","Z","YXXY","YYXX","YYYY","XYYX","XXXX","XYXY","Z"]},{"n":3,"groups":[[32,35,9],[15,2,5],[7,14,17],[22,24,3],[26,27,16],[6,30,19],[12,11,25],[23,20,8],[31,0,21],[29,34,4],[33,1,13],[18,28,10]],"tests":["YXY","YYX","XXX","Z","Z","XXX","YYX","YXY","XYY","Z","Z","XYY"]},{"n":4,"groups":[[23,19,4,32],[30,16,11,14],[2,15,6,9],[25,29,12,17],[1,0,7,18],[28,10,5,22],[21,20,34,8],[35,3,33,26],[27,31,13,24]],"tests":["XXYY","YYYY","Z","XYYX","Z","Z","YXXY","YYXX","XYXY"]},{"n":3,"groups":[[15,25,14],[20,2,18],[7,12,6],[13,4,30],[3,29,9],[8,27,35],[33,1,17],[21,11,34],[22,5,26],[32,24,0],[31,23,28],[10,16,19]],"tests":["XYY","XXX","YYX","Z","YXY","YYX","Z","XXX","Z","Z","XYY","YXY"]},{"n":4,"groups":[[10,5,31,29],[16,7,25,27],[15,2,34,17],[26,9,0,23],[14,33,20,28],[35,1,19,12],[18,8,32,21],[30,11,13,4],[3,24,22,6]],"tests":["YXXY","YYXX","XXXX","YXYX","Z","XXYY","Z","XYYX","Z"]}]}''')


def circuit(groups, tests, nq):
    qc = QuantumCircuit(nq, nq)
    for g, t in zip(groups, tests):
        qc.h(g[0])
        for a, b in zip(g[:-1], g[1:]):
            qc.cx(a, b)                            # GHZ_n = (|0..0> + |1..1>)/sqrt2
        if t != "Z":
            for q, ax in zip(g, t):
                if ax == "X": qc.h(q)
                if ax == "Y": qc.sdg(q); qc.h(q)
    qc.measure(range(nq), range(nq))               # qubit q -> classical bit q (rightmost character of a key = bit 0)
    return qc


def rehearsal(d, nq_max=29):
    """Simulator rehearsal only (29 qubits): as many of the job's groups as fit, qubits relabelled 0.."""
    k = nq_max // d["n"]
    groups = d["groups"][:k]; used = sorted(q for g in groups for q in g); lab = {q: i for i, q in enumerate(used)}
    return {"n": d["n"], "groups": [[lab[q] for q in g] for g in groups], "tests": d["tests"][:k]}


def n_qubits():
    for f in (lambda: backend.num_qubits, lambda: backend.configuration().n_qubits):
        try:
            return int(f())
        except Exception:
            pass
    return None


def emit(out):
    s = json.dumps(out, separators=(",", ":"), default=str)
    print("JOB", out["job"], "N", out["n"], "MODE", out["mode"], "SHA", hashlib.sha256(s.encode()).hexdigest()[:16], "LEN", len(s), flush=True)
    try:
        from js import sendFile
        name = f"s41b_job_{out['job']:02d}{'_' + out['mode'] if out['mode'] != 'hardware' else ''}.json"
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
    name = str(getattr(backend, "name", "?")); low = name.lower(); nq_backend = n_qubits()
    if "simulator" in low:
        mode, d = "rehearsal", rehearsal(TABLE["design"][JOB])
    elif "forte" in low:
        mode, d = "hardware", TABLE["design"][JOB]
    else:
        raise RuntimeError(f"unexpected backend {name!r}; nothing was submitted")
    nq = sum(len(g) for g in d["groups"])
    qc = circuit(d["groups"], d["tests"], nq)
    out = {"study": "41b", "job": JOB, "n": d["n"], "mode": mode, "n_groups": len(d["groups"]), "groups": d["groups"],
           "tests": d["tests"], "shots": SHOTS, "backend": name, "n_qubits": nq_backend,
           "debias_requested": str(ErrorMitigation.NO_DEBIASING), "qasm": qasm2.dumps(qc),
           "versions": {"qiskit": qiskit.__version__}}
    try:
        import qiskit_ionq; out["versions"]["qiskit_ionq"] = qiskit_ionq.__version__
    except Exception:
        pass
    print("READY: job", JOB, "n", d["n"], "mode", mode, "backend", name, "qubits", nq_backend, "groups", len(d["groups"]), flush=True)
    job = backend.run(qc, shots=SHOTS, error_mitigation=ErrorMitigation.NO_DEBIASING)
    out["job_id"] = job.job_id()
    print("SUBMITTED: job id", out["job_id"], "(keep this line)", flush=True)
    try:
        res = job.result()
        counts = res.get_counts()
        out["counts_hex"] = {format(int(k.replace(" ", ""), 2), "x"): int(v) for k, v in counts.items()}
    except Exception as e:
        out["error"] = repr(e)
        print("RESULT ERROR:", repr(e), "-- keep this output; the job number will be re-run", flush=True)
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
