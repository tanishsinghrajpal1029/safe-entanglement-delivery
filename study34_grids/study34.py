"""Study 34 ("other grids"): the provable closed loop on larger networks.

Same network model, guard, checks and current-look offset bound as Study 32 (study32.Net32, arm kgMChN = hybrid check +
current-look bound, Remark R; kgMCa = always-on margin, Corollary 3), on square grids of side 5 (reference, fresh seeds), 10
(100 nodes, 180 links) and 30 (900 nodes, 1,740 links). The correlated-link generator builds its grid from g1.GRID_N at import,
so ONE PROCESS RUNS ONE GRID SIZE: set the environment variable S34_GRID (5, 10 or 30) and use the matching task file.
This is a SCALING SANITY CHECK (review M1): calibration data per link, the offset and the check's test rate do not change with
grid size, so most mechanisms predict carry-over. Load variants ('var', third cfg field):
  base  the same total request rate as Studies 30-32 on every grid. Users grow with the grid (5x5: 204/340 users; 10x10: 1,004/1,860;
        30x30: 10,204/19,940 for ion2020/ionproj), so requests per user fall about 60x on 30x30 and per-user risk is diluted:
        use the per-delivery rate and risk per SERVED user (review B1).
  u     matched exposure: demand restricted to a random subset of users of the 5x5 size (204 / 340), drawn once per network, so
        requests per user match the 5x5 reference (10x10 and 30x30).
  m3    three times the request rate (as G3's scaled load), on 5x5 and 30x30, so a rate effect is separable from a grid effect.
Scenarios: '-' (no offset), 'o0.044' (constant offset in the true state), 'o0.044F' (forced alarm at the 8th test).
Arms: kg (no check), kgMChN at p = 0.1 and 0.2, kgMCa at p = 0.1.
"""
import hashlib, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S18C_LIB", ""), os.environ.get("S26_DIR", ""), os.environ.get("S27_DIR", ""), os.environ.get("S30_DIR", ""),
          os.environ.get("S32_DIR", ""), os.path.join(HERE, "..", "s30"), os.path.join(HERE, "..", "s32"),
          "/home/claude/s18c", "/home/claude/s26", "/home/claude/s27", "/home/claude/s30", "/home/claude/s32"):
    if p and p not in sys.path: sys.path.append(p)
import drift_queue_des_g1 as g1
GRID = int(os.environ.get("S34_GRID", "5"))
g1.GRID_N = GRID                                          # must precede every import that builds the grid (corr_net)
import study32 as s32
import corr_net as cn1
assert cn1.NL == 2 * GRID * (GRID - 1), (cn1.NL, GRID)

SEEDS = (19341, 19342, 19343, 19344); DEV = (20341, 20342, 20343, 20344); NNET = 32
HWS = ("ion2020", "ionproj")


VARS = {5: ("base", "m3"), 10: ("base", "u"), 30: ("base", "m3", "u")}
N5 = {"ion2020": 204, "ionproj": 340}                     # users on the 5 x 5 grid


def configs(grid):
    C = []
    for mult in VARS[grid]:
        for hw in HWS:
            for sc in ("-", "o0.044"): C.append((hw, "kg", f"{sc}|p00|{mult}"))
            for sc in ("-", "o0.044", "o0.044F"):
                for p in ("p10", "p20"): C.append((hw, "kgMChN", f"{sc}|{p}|{mult}"))
                C.append((hw, "kgMCa", f"{sc}|p10|{mult}"))
    return C


class Net34(s32.Net32):
    def __init__(s, hw, pat, arm, cfg, seed):
        super().__init__(hw, pat, arm, cfg, seed)
        var = cfg.split("|")[2]; s.var34 = var
        s.mult = 3.0 if var == "m3" else 1.0
        s.rate25 *= s.mult
        s.users_all = len(s.cands)
        if var == "u":                                             # matched exposure: same random user subset for every arm
            import numpy as np
            ur = np.random.default_rng(list(seed[2:]) + [341]); n = min(N5[hw], len(s.cands))
            s.cands = [s.cands[i] for i in sorted(ur.choice(len(s.cands), n, replace=False))]

    def run(s):
        out = super().run()
        out.update(grid=GRID, nl=s.nl, rate_mult=s.mult, var34=s.var34, users_all=s.users_all, users_served=len(s.ustat),
                   users_bad_served=sum(1 for x in s.ustat.values() if x[1] > 0))
        return out


def tasks(prefix="S34", nnet=NNET, grid=GRID):
    return [[f"{prefix}g{grid}", hw, "field", arm, cfg, i] for (hw, arm, cfg) in configs(grid) for i in range(nnet)]


def run_id(t):
    return hashlib.sha256("s34|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, cfg, idx = t
    assert blk.endswith(f"g{GRID}"), f"task grid {blk} != S34_GRID={GRID}: run each grid in its own job"
    if blk.startswith("P34"): seeds = DEV
    nseed = int(hashlib.sha256(f"s34net|g{GRID}|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s34run|g{GRID}|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net34(hw, pat, arm, cfg, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    r = net.run(); r.pop("arm32", None)
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, cfg=cfg, idx=idx, **r)


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P34", int(sys.argv[3]) if len(sys.argv) > 3 else 4)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"grid {GRID}: wrote {len(ts)} tasks")
