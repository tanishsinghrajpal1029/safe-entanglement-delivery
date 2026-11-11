"""Derives the Study 41a design table from the seeds (run once before freezing; the table is embedded in job_41a.py).

Per job j (seed 41000 + j): a random arrangement of 6 X, 6 Y, 6 Z axes over the 18 pairs; a random pairing of the 36 qubits;
in Block B (10 of 30 jobs, seed 41999) 2 faulty pairs per axis group with planted phase +theta and -theta."""
import json, sys
import numpy as np

N_JOBS, N_PAIRS = 30, 18


def b_jobs():
    return sorted(int(j) for j in np.random.default_rng(41999).choice(N_JOBS, 10, replace=False))


def derive(job, n_pairs=N_PAIRS):
    rng = np.random.default_rng(41000 + job)
    axes = rng.permutation(np.repeat(np.array(list("XYZ")), n_pairs // 3))
    perm = rng.permutation(2 * n_pairs)
    pairs = [[int(perm[2 * k]), int(perm[2 * k + 1])] for k in range(n_pairs)]
    faulty = {}
    if job in b_jobs():
        for ax in "XYZ":
            idx = np.flatnonzero(axes == ax)
            for m, i in enumerate(rng.choice(idx, n_pairs // 9, replace=False)):
                faulty[str(int(i))] = 1 if m % 2 == 0 else -1
    return {"axes": "".join(axes), "pairs": pairs, "faulty": dict(sorted(faulty.items(), key=lambda kv: int(kv[0])))}


def table():
    return {"b_jobs": b_jobs(), "design": [derive(j) for j in range(N_JOBS)]}


if __name__ == "__main__":
    print(json.dumps(table(), separators=(",", ":")))
