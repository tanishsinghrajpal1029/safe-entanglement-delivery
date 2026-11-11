"""Synthetic job files in the exact Study 41a format (for testing the analysis only; never mixed with real data)."""
import json, os, sys, uuid, types, hashlib
import numpy as np
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(HERE) == "tests": HERE = os.path.dirname(HERE)          # helpers live in tests/
sys.modules.setdefault("qiskit", types.SimpleNamespace(QuantumCircuit=None))
ns = {"__name__": "job_41a"}; exec(open(os.path.join(HERE, "job_41a.py")).read(), ns)



def qasm_text(axes, pairs, faulty):
    """Same text as qiskit.qasm2.dumps of circuit() (format of Qiskit 2.x)."""
    L = ['OPENQASM 2.0;', 'include "qelib1.inc";', 'qreg q[36];', 'creg c[36];']
    for k, (ax, (a, b)) in enumerate(zip(axes, pairs)):
        L += [f"h q[{a}];", f"cx q[{a}],q[{b}];"]
        if k in faulty: L.append(f"rz({'-' if faulty[k] < 0 else ''}pi/4) q[{a}];")
        for q in (a, b):
            if ax == "X": L.append(f"h q[{q}];")
            if ax == "Y": L += [f"sdg q[{q}];", f"h q[{q}];"]
    L += [f"measure q[{q}] -> c[{q}];" for q in range(36)]
    return "\n".join(L)


def uuid7(ms, rng):
    h = f"{ms:012x}" + "7" + "".join(rng.choice(list("0123456789abcdef"), 3)) + "8" + "".join(rng.choice(list("0123456789abcdef"), 15))
    return str(uuid.UUID(h))


def make(outdir, seed=1, exy=0.012, ez=0.007, het=0.004, phi0=0.0, corr=0.0, backend="ionq_qpu.forte-1", jobs=range(30),
         qasm_fn=None, dup=None, t0=1_763_000_000_000):
    os.makedirs(outdir, exist_ok=True)
    rng = np.random.default_rng(seed)
    qbad = rng.gamma(2.0, het / 2, 36)                                    # per-qubit extra error (heterogeneity)
    for i, j in enumerate(list(jobs) + ([dup] if dup is not None else [])):
        dd = ns["TABLE"]["design"][j]; axes, pairs = dd["axes"], dd["pairs"]; faulty = {int(k): v for k, v in dd["faulty"].items()}
        bits = np.zeros((1000, 36), int)
        common = rng.random(1000) < corr                                  # shot-wide correlated error events
        for k, (ax, (a, b)) in enumerate(zip(axes, pairs)):
            e = (exy if ax in "XY" else ez) + qbad[a] + qbad[b]           # incoherent part
            if ax in "XY":                                                # coherent phase: native phi0 plus planted +-theta
                ph = phi0 + (faulty.get(k, 0) * ns["THETA"])
                e = e + (1 - 2 * e) * np.sin(ph / 2) ** 2
            err = (rng.random(1000) < e) | (common & (rng.random(1000) < 0.5))
            x = rng.integers(0, 2, 1000)
            y = x ^ err.astype(int) ^ (1 if ax == "Y" else 0)
            bits[:, a] = x; bits[:, b] = y
        keys = ["".join(str(v) for v in row[::-1]) for row in bits]       # key string: leftmost = highest qubit
        cnt = Counter(keys)
        out = {"study": "41a", "job": j, "block": "B" if j in ns["B_JOBS"] else "A", "mode": "hardware", "n_pairs": 18, "axes": axes, "pairs": pairs,
               "faulty": dd["faulty"], "shots": 1000, "job_id": uuid7(t0 + i * 400_000, rng), "backend": backend, "n_qubits": 36,
               "debias_requested": "ErrorMitigation.NO_DEBIASING", "qasm": (qasm_fn or qasm_text)(axes, pairs, faulty), "versions": {},
               "ionq_meta": {"backend": "qpu.forte-1", "settings": {"error_mitigation": {"debiasing": False}}},
               "counts_hex": {format(int(k, 2), "x"): v for k, v in cnt.items()}}
        name = f"s41a_job_{j:02d}.json" if i < len(list(jobs)) else f"s41a_job_{j:02d} (1).json"
        json.dump(out, open(os.path.join(outdir, name), "w"), separators=(",", ":"))


if __name__ == "__main__":
    make(sys.argv[1], **json.loads(sys.argv[2]) if len(sys.argv) > 2 else {})
