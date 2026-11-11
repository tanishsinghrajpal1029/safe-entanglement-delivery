"""Produces all 30 job files by running job_41a.py exactly as Qollab would, on a noisy local Aer backend (test data only)."""
import sys, types, enum, uuid, json, io, contextlib, os, time
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError

class EM(enum.Enum):
    NO_DEBIASING = "no_debiasing"
sys.modules["qiskit_ionq"] = types.SimpleNamespace(ErrorMitigation=EM, __version__="fake")
nm = NoiseModel(); nm.add_all_qubit_quantum_error(depolarizing_error(0.02, 2), ["cx"])
nm.add_all_qubit_quantum_error(depolarizing_error(0.002, 1), ["h", "sdg", "rz"])
nm.add_all_qubit_readout_error(ReadoutError([[0.996, 0.004], [0.006, 0.994]]))
SIM = AerSimulator(method="matrix_product_state", noise_model=nm, seed_simulator=11)
T0 = [1_763_000_000_000]

class FakeBackend:
    num_qubits = 36; name = "fake_aer_forte"
    def run(s, qc, shots, error_mitigation=None):
        c = SIM.run(qc, shots=shots).result().get_counts(); T0[0] += 300_000
        jid = str(uuid.UUID(f"{T0[0]:012x}7abc8" + "0" * 15))
        return types.SimpleNamespace(job_id=lambda: jid, result=lambda: types.SimpleNamespace(get_counts=lambda: c))

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for job in range(30):
    src = open("main.py").read().replace("JOB = 0", f"JOB = {job}", 1)
    ns = {"__name__": "__main__", "backend": FakeBackend()}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(src, ns); ns["main"]()
    open(os.path.join(out, f"s41a_job_{job:02d}.json"), "w").write(buf.getvalue().splitlines()[-1])
print("done")
