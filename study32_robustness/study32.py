"""Study 32 ("re-opening and robustness"): three blocks on top of Study 30's network and provable loop (study30.Net30, unchanged).

Block R (re-opening; referee COULD 26; the S30 network-11 episode). Theorem 2 uses U_t = min over looks of sup{m: K_t(m) < 1/a'}.
  The running minimum is not needed for validity: U'_t = sup{m: K_t(m) < 1/a'} (no intersection) fails only on the same event
  {exists t: K_t(theta) >= 1/a'} (K_t is nondecreasing in m), so P(exists t: theta > U'_t) <= a' as well (THEORY_32.md).
  U' can rise again when later tests contradict an early unlucky stretch.
  Arms: kgMCh (Study 30, running minimum) vs kgMChN (same, no intersection).
  Scenarios: '-', 'o0.044', 'L0.044', and 'o0.044FM' = forced alarm at the 8th test (Study 28's case; an earlier real alarm
  also opens the window) PLUS a forced miscoverage: every test of the first offset window before its first look (at least
  NPOIS = 150 tests) is recorded as a pass (E = 0), reproducing the S30 network-11 mechanism deliberately (the guarantee is
  broken by construction there; the question is recovery).
Block E (robustness; referee M16/E3): threshold tau in {0.85, 0.92} and LESS calibration data (rho_cal = 0.1 instead of 0.3;
  the service rate is unchanged), ion hardware, p = 0.1, scenarios '-' and 'o0.044'; arms kg, kgMCh, kgMCa; paired base
  controls ('base') for kg and kgMCa (kgMCh's base cells are Block R's, same seeds). theta_max = 0.10 was set for tau = 0.9.
  ion2020 at tau = 0.92 with o0.044 has no good pairs (oracle 0): such cells are report-only.
Block T (thin hardware; DESCRIPTIVE, predictions only): nv2 and siv (native tau 0.8), scenarios '-' and 'o0.044', p = 0.1 and
  0.2; arms kg, kgMCh, kgMCa. With the native request rates the networks produce only tens of tests in 90 epochs, so the check is
  not expected to alarm and the always-on margin (starting at theta_max = 0.10) is not expected to deliver: this block documents
  the limit, it does not test the loop.
Not varied: network topology (the correlated-network generator is built for the 5x5 grid; stated as a limitation).
"""
import hashlib, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.environ.get("S30_DIR", ""), os.path.join(HERE, "..", "s30"), "/home/claude/s30"):
    if p and p not in sys.path: sys.path.append(p)
import study30 as s30
import drift_queue_des_g1 as g1
import hw24
from core30 import OffsetCS

NPOIS = 150
SEEDS = (19331, 19332, 19333, 19334); DEV = (20331, 20332, 20333, 20334); NNET = 32
ION = ("ion2020", "ionproj"); THIN = ("nv2", "siv")


class OffsetCS32(OffsetCS):
    """OffsetCS with (i) optional no-intersection bound and (ii) optional forced miscoverage of the FIRST window: every test
    recorded before the window's first look (with at least NPOIS tests) is recorded as a pass (E = 0)."""
    def __init__(s, level0, m_hi, monotone=True, poison=False):
        s.monotone, s.poison, s.looked = monotone, poison, False; s.npois = 0; s.log = []; super().__init__(level0, m_hi)

    def restart(s):
        super().restart(); s.looked = False

    def add(s, a, phi, amax=1.5):
        if s.poison and s.k == 1 and not s.looked: a = float(amax) - 1.5; s.npois += 1   # record this test as a pass (E = 0)
        super().add(a, phi, amax)

    def update(s):
        U = s._update(); s.log.append((s.k, s.n, U)); return U

    def _update(s):
        if s.n >= NPOIS: s.looked = True
        if s.monotone: return super().update()
        if s.n == 0: return s.U
        thr = np.log(1 / s.level); s._arrays()
        if s._logK(s.m_hi) < thr: s.U = s.m_hi; return s.U
        if s._logK(0.0) >= thr: s.U = 0.0; return s.U
        lo, hi = 0.0, s.m_hi
        for _ in range(40):
            mid = (lo + hi) / 2
            if s._logK(mid) < thr: lo = mid
            else: hi = mid
        s.U = hi; return s.U


def configs():
    C = []
    for hw in ION:                                                                     # Block R
        for sc in ("-", "o0.044", "L0.044", "L0.044F", "o0.044FM"):
            for p in ("p10", "p20"):
                for a in ("kgMCh", "kgMChN"): C.append(("R", hw, a, f"{sc}|{p}|base"))
    for hw in ION:                                                                     # Block E (base: paired controls)
        for sc in ("-", "o0.044"):
            C.append(("E", hw, "kg", f"{sc}|p00|base")); C.append(("E", hw, "kgMCa", f"{sc}|p10|base"))
        for var in ("t0.85", "t0.92", "r0.1"):
            for sc in ("-", "o0.044"):
                C.append(("E", hw, "kg", f"{sc}|p00|{var}"))
                for a in ("kgMCh", "kgMCa"): C.append(("E", hw, a, f"{sc}|p10|{var}"))
    for hw in THIN:                                                                    # Block T
        for sc in ("-", "o0.044"):
            C.append(("T", hw, "kg", f"{sc}|p00|base"))
            for p in ("p10", "p20"):
                for a in ("kgMCh", "kgMCa"): C.append(("T", hw, a, f"{sc}|{p}|base"))
    return C


class Net32(s30.Net30):
    def __init__(s, hw, pat, arm, cfg, seed):
        sc, pt, var = cfg.split("|"); s.var = var; s.poisoned = sc.endswith("M")
        sc30 = sc[:-1] if s.poisoned else sc
        arm30 = "kgMCh" if arm == "kgMChN" else arm
        old = hw24.RHO_CAL
        if var.startswith("r"): hw24.RHO_CAL = float(var[1:])
        try:
            super().__init__(hw, pat, arm30, f"{sc30}|{pt}", seed, ttag=321)
        finally:
            hw24.RHO_CAL = old
        s.rho_used = float(var[1:]) if var.startswith("r") else old
        if var.startswith("t"): s.tau = float(var[1:])
        s.arm32 = arm
        if s.prov:
            s.cs = OffsetCS32(s30.ALPHA_TH, s30.THMAX, monotone=(arm != "kgMChN"), poison=s.poisoned)
            if arm == "kgMCa": s.cs.restart()

    def run(s):
        out = super().run()
        out.update(var=s.var, tau=s.tau, rho_cal=s.rho_used, poisoned=int(s.poisoned), arm32=s.arm32)
        # bound-coverage diagnostics (constant class, constant offset 'o' scenarios only: theta known; window-1 looks)
        lg = [(k, n, U) for (k, n, U) in (s.cs.log if s.prov and hasattr(s.cs, "log") else []) if k == 1 and n > 0]
        th = s.theta if s.okind == "o" else float("nan")
        below = [i for i, (_, _, U) in enumerate(lg) if U < th - 1e-12]
        first_b = below[0] if below else -1
        rec = next((i for i in range(first_b + 1, len(lg)) if lg[i][2] >= th), -1) if below else -1
        out.update(npois=getattr(s.cs, "npois", 0) if s.prov else 0, w1_looks=len(lg), w1_looks_below=len(below),
                   w1_first_below=first_b, w1_recover=rec, w1_recover_tests=(lg[rec][1] - lg[first_b][1]) if rec >= 0 else -1)
        return out


def tasks(prefix="S32", nnet=NNET):
    return [[prefix + blk, hw, "field", arm, cfg, i] for (blk, hw, arm, cfg) in configs() for i in range(nnet)]


def run_id(t):
    return hashlib.sha256("s32|{}|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, pat, arm, cfg, idx = t
    if blk.startswith("P32"): seeds = DEV
    nseed = int(hashlib.sha256(f"s32net|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"s32run|{hw}|{idx}".encode()).hexdigest()[:8], 16)
    net = Net32(hw, pat, arm, cfg, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    r = net.run(); r.pop("arm32", None)
    return dict(run=run_id(t), block=blk, hw=hw, pat=pat, arm=arm, cfg=cfg, idx=idx, **r)


if __name__ == "__main__":
    if sys.argv[1:2] in (["--write-tasks"], ["--write-pilot"]):
        ts = tasks() if sys.argv[1] == "--write-tasks" else tasks("P32", int(sys.argv[3]) if len(sys.argv) > 3 else 4)
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
