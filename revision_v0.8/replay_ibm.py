"""Replay of the recorded IBM outcomes (S31, S31b) for the evidence figure. Uses the frozen schedule, certificate and
check code; reproduces the stored summary values (asserted) and records the trajectories. Not a new test."""
import json, copy, os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "study31b_hardware_detector"))   # frozen schedule, certificate and checks of S31b
from scipy.stats import beta as betad
from scipy.special import logsumexp
import ibm_testkeep as base
from cert import Certifier
from mcheck import ModelCheck, CAP, LAMS
from core30 import HybridCheck
THR = float(np.log(1 / (base.BETA * 6 / np.pi ** 2)))
def replay(seed, out):
    S = base.schedule(seed)
    e0 = [base.error_of(m, b) for (ph, _, m), b in zip(S, out) if ph == "0"]
    k0, n0 = sum(e0), len(e0); F_decl = 1 - 1.5 * betad.ppf(0.95, k0 + 1, n0 - k0); q = (2 / 3) * (1 - F_decl)
    cert = Certifier(base.P, base.ALPHA, rmax=base.SMAX); hyb = HybridCheck(base.BETA); mix = ModelCheck(base.BETA)
    K = Err = passK = 0; nt = 0; T = dict(t=[], ph=[], mix=[], hyb=[]); C = dict(K=[], L=[], bell=[], lo=[], hi=[]); al = {}
    for (ph, st, m), b in zip(S, out):
        if ph == "0": continue
        E = base.error_of(m, b)
        if m != "BELL":
            nt += 1; Err += E
            hc = copy.deepcopy(hyb); hc.reset = lambda: None          # copy without reset, to read the crossing value
            mc = copy.deepcopy(mix)
            h_al = hyb.update(E, q); m_al = mix.update(E, q)
            if h_al: hc.update(E, q); hcross = float(np.logaddexp(logsumexp(hc.logm) - np.log(len(hc.lams)), hc.lp) - np.log(2))
            if m_al:
                qq = float(min(max(q, 1e-6), 1 - 1e-6)); lam = np.minimum(mc.lams, CAP / qq)
                mcross = float(logsumexp(mc.logm + np.log1p(lam * (E - qq)) + np.log(mc.w)))
            if h_al and "hyb" not in al: al["hyb"] = nt
            if m_al and "mix" not in al: al["mix"] = nt
            lmix = float(logsumexp(mix.logm + np.log(mix.w)))
            lhyb = float(np.logaddexp(logsumexp(hyb.logm) - np.log(len(hyb.lams)), hyb.lp) - np.log(2))
            if h_al and al.get("hyb") == nt: lhyb = hcross   # value that crossed the alarm level (the check resets after it)
            if m_al and al.get("mix") == nt: lmix = mcross
            T["t"].append(nt); T["ph"].append(ph); T["mix"].append(np.nan if "mix" in al and nt > al["mix"] else lmix)
            T["hyb"].append(np.nan if "hyb" in al and nt > al["hyb"] else lhyb)
        else:
            K += 1; passK += 1 - E
            C["K"].append(K); C["L"].append(cert.lower(Err, K)); C["bell"].append(passK / K)
            C["lo"].append(betad.ppf(0.025, passK, K - passK + 1) if passK > 0 else 0.0)
            C["hi"].append(betad.ppf(0.975, passK + 1, K - passK) if passK < K else 1.0)
    thr = float(np.log(1 / (base.BETA * 6 / np.pi ** 2)))
    nA = sum(1 for (ph, _, m) in S if ph == "A" and m != "BELL")
    return dict(F_decl=F_decl, q=q, al=al, thr=thr, nA=nA, T=T, C=C, cert_final=C["L"][-1], bell_final=C["bell"][-1])
R = {}
for name, f, seed in (("S31", os.path.join(ROOT, "study31_hardware_testkeep", "hw_result.json"), 31031), ("S31b", os.path.join(ROOT, "study31b_hardware_detector", "hw_result_31b.json"), 31032)):
    d = json.load(open(f)); r = replay(seed, d["outcomes"]); R[name] = r
    print(name, "F_decl", round(r["F_decl"], 4), "q", round(r["q"], 4), "alarms", r["al"], "nA", r["nA"], "cert", round(r["cert_final"], 4), "bell", round(r["bell_final"], 4), "thr", round(r["thr"], 3))
    assert abs(round(r["F_decl"], 4) - d["result"]["F_decl"]) < 1e-9 and abs(round(r["cert_final"], 4) - d["result"]["cert_final"]) < 1e-9
json.dump({k: dict(v, T={a: [float(x) if not isinstance(x, str) else x for x in b] for a, b in v["T"].items()},
                   C={a: [float(x) for x in b] for a, b in v["C"].items()}) for k, v in R.items()}, open(os.path.join(HERE, "ibm_traj.json"), "w"))
