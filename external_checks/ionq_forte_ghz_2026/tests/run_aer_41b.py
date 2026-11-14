"""Produces all 20 job files by running job_41b.py exactly as Qollab would, on a noisy local Aer backend (test data only)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tests_common import Fake, run_job
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError
cx = float(sys.argv[2]) if len(sys.argv) > 2 else 0.012
nm = NoiseModel(); nm.add_all_qubit_quantum_error(depolarizing_error(cx, 2), ["cx"])
nm.add_all_qubit_quantum_error(depolarizing_error(0.001, 1), ["h", "sdg"])
nm.add_all_qubit_readout_error(ReadoutError([[0.996, 0.004], [0.006, 0.994]]))
sim = AerSimulator(method="stabilizer", noise_model=nm, seed_simulator=11)
out = sys.argv[1]; os.makedirs(out, exist_ok=True); be = Fake("ionq_qpu.forte-1", 36, sim)
for j in range(20):
    d = run_job(j, be)
    json.dump(d, open(os.path.join(out, f"s41b_job_{j:02d}.json"), "w"), separators=(",", ":"))
print("done")
