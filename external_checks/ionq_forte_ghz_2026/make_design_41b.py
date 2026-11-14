"""Derives the Study 41b design table from the seeds (run once before freezing; the table is embedded in job_41b.py).

20 jobs: 10 with GHZ-3 states (12 per shot, 36 qubits) and 10 with GHZ-4 states (9 per shot), in a seeded random order
(seed 41199). Per job j (seed 41100 + j): a random partition of the 36 qubits into groups of n (each group's first qubit
is the H qubit, then a CX chain); a test per group, stratified so that every group's test is marginally:
  'Z'           with probability 1/3   (all qubits measured in Z; pass iff all outcomes are equal)
  an XY string  with probability (2/3) / 2^(n-1) each   (the even-#Y strings in {X,Y}^n; pass iff the outcome
                parity equals the stabiliser sign (-1)^(#Y/2))
n = 3: 4 'Z' + each of the 4 XY strings twice (12 groups).  n = 4: 3 'Z' + 6 of the 8 XY strings, drawn without
replacement (9 groups).  The multiset is randomly permuted over the groups.
With these marginals P(fail) = (2/3)(1 - F_GHZ) exactly for every state (Li, Han & Zhu), the same constant as the
Bell-pair test, so cert.py applies unchanged."""
import itertools, json
import numpy as np

N_JOBS = 20


def xy_strings(n):
    return ["".join(c) for c in itertools.product("XY", repeat=n) if c.count("Y") % 2 == 0]


def job_sizes():
    return [int(x) for x in np.random.default_rng(41199).permutation([3] * 10 + [4] * 10)]


def derive(job):
    n = job_sizes()[job]
    rng = np.random.default_rng(41100 + job)
    g = 36 // n
    perm = rng.permutation(36)
    groups = [[int(q) for q in perm[n * i: n * (i + 1)]] for i in range(g)]
    xy = xy_strings(n)
    if n == 3:
        multiset = ["Z"] * 4 + xy * 2
    else:
        multiset = ["Z"] * 3 + [xy[i] for i in sorted(rng.choice(len(xy), 6, replace=False))]
    tests = [multiset[i] for i in rng.permutation(len(multiset))]
    return {"n": n, "groups": groups, "tests": tests}


def table():
    return {"sizes": job_sizes(), "design": [derive(j) for j in range(N_JOBS)]}


if __name__ == "__main__":
    print(json.dumps(table(), separators=(",", ":")))
