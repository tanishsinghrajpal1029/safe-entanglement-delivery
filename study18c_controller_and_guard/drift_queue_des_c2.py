"""Study 18C C2: confirmatory run of the FROZEN v21 controller (pre-registered in README_C2.md; fresh seeds).
Controller = C1 frozen controller + v21 prior variant 'm123' (uniform-s hyperprior, drift-aware window likelihood,
declared fault component eps = 0.05). Blocks: A core (256 paths), B fleet law (96), R rare faults: each path faulted
with prob 0.05, matching the declared model (192), C always-fault worst case, exploratory (64)."""
import hashlib, json, sys
import drift_queue_des_c1 as c1
import drift_queue_des_v21 as v21

SEEDS = (19011, 19012, 19013, 19014)     # fresh (never used); v21 dev pilots used 20001-20004
NP = {"A": 256, "B": 96, "R": 192, "C": 64}; VARIANT = "m123"


def tasks():
    T = [["A", c, g, m, "normal", i] for c in c1.CELLS for g in (1e-9, 1e-5) for m in c1.MEMS for i in range(NP["A"])]
    T += [["B", c, 1e-5, "deph", law, i] for c in c1.CELLS for law in ("t3", "mixlow", "mixhigh") for i in range(NP["B"])]
    T += [["R", c, 1e-5, "deph", "normal", i] for c in c1.CELLS for i in range(NP["R"])]
    T += [["C", c, 1e-5, "deph", "normal", i] for c in c1.CELLS for i in range(NP["C"])]
    return T


def run_id(t):
    return hashlib.sha256("c2|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t):
    r = v21.run_one(t, VARIANT, npaths=NP, seeds=SEEDS); r["run"] = run_id(t); return r


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
