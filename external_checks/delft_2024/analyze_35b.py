"""Study 35B (Delft, fully heralded delivered Psi- states, paper Fig. 4) locked analysis.
Usage: python3 analyze_35b.py delft_extract_35b.json > results_35b.txt     (numpy + scipy; uses delft_core.py of Study 35)
Order: gates G1, G2, G0 (stop rules), G3/G4 (flags), then D1', D2' (primary), S1'-S3' (secondary). See PREREG_35B.md.
"""
import json, sys
import numpy as np
from scipy.stats import norm
from delft_core import BELL, Z95, correlator_from_p, errors_from_counts, certificate, fid_from_corr, u_fid_from_corr, offset_test

WINDOWS = np.linspace(5, 20, 16)      # Figure4.ipynb: plotx = np.linspace(5, 20, 16), 'Window length' [ns]
MAIN_W = 15.0                         # Figure4.ipynb circle at (15.0, 0.533); paper: 15 ns window, F = 0.534(15)
TARGET = BELL["Psi-"]                 # Figure4.ipynb: signs = [-1,-1,-1] for every state (feedback maps both heralds to Psi-)
STATES = ("state_0", "state_1", "state_2")   # state_2 = 'Combined' (the delivered states the paper reports)


def basis_of(rec):
    b1 = str(rec["node1_readout_basis"]).strip().upper()[-1:]; b2 = str(rec["node2_readout_basis"]).strip().upper()[-1:]
    return b1 if b1 == b2 and b1 in "XYZ" else None


def main(path):
    d = json.load(open(path)); out = {}; P = lambda *a: print(*a, flush=True)
    olab = [str(x).strip() for x in (d["ssro_outcome_tick_labels"] or [])]
    if sorted(olab) != ["00", "01", "10", "11"]:
        P(f"G1 note: outcome labels {olab!r}; using ['00','01','10','11']"); olab = ["00", "01", "10", "11"]
    order = {st: [basis_of(d["states"][st]["datasets"][k]) for k in sorted(d["states"][st]["datasets"])] for st in STATES}
    g1 = all(sorted(v) == ["X", "Y", "Z"] for v in order.values())
    P(f"G1 {'PASS' if g1 else 'FAIL'}  outcome order {olab}; state labels {d['state_generated_tick_labels']} (logged only); basis order {order}")
    out["G1"] = g1
    if not g1: P("STOP: gate G1 failed."); return out
    dev = max(abs(correlator_from_p(r["p"], olab) - float(r["correlation"])) for st in STATES for r in d["states"][st]["datasets"].values())
    g2 = dev <= 0.002; P(f"G2 {'PASS' if g2 else 'FAIL'}  parity convention: max |c(p) - correlation| = {dev:.5f} (<= 0.002)"); out["G2"] = g2
    if not g2: P("STOP: gate G2 failed."); return out
    c = {st: {basis_of(r): float(r["correlation"]) for r in d["states"][st]["datasets"].values()} for st in STATES}
    Fd = {st: fid_from_corr(c[st], TARGET) for st in STATES}
    dev0 = max(abs(Fd[st] - float(d["states"][st]["fidelity"])) for st in STATES)
    g0 = dev0 <= 0.005; P(f"G0 {'PASS' if g0 else 'FAIL'}  Psi- target for all states: our F {Fd}; max diff to attribute {dev0:.5f} (<= 0.005)"); out["G0"] = g0
    if not g0: P("STOP: gate G0 failed."); return out
    byb = lambda st: {basis_of(r): r for r in d["states"][st]["datasets"].values()}
    g4 = all(np.array_equal(np.asarray(byb("state_2")[b]["N"]), np.asarray(byb("state_0")[b]["N"]) + np.asarray(byb("state_1")[b]["N"])) for b in "XYZ")
    P(f"G4 info  combined counts = state_0 + state_1 in every basis: {g4}")
    n_b = {b: int(sum(byb("state_2")[b]["N"])) for b in "XYZ"}; P(f"info: delivered-state events per basis {n_b}")

    P("\n== PRIMARY")
    eb = {b: errors_from_counts(byb("state_2")[b]["N"], olab, TARGET[b]) for b in "XYZ"}
    cert = certificate(eb); d1 = cert["F_lo"] > 0.5
    P(f"D1' {'PASS' if d1 else 'FAIL'}  raw-count certificate, delivered (combined) states: F_hat {cert['F_hat']:.4f}, F_lo(95%) {cert['F_lo']:.4f} (bar > 0.5)")
    out["D1b"] = dict(pass_=bool(d1), F_hat=cert["F_hat"], F_lo=cert["F_lo"])

    sw = np.asarray(d["total_result_sweep"], float); cps = np.asarray(d["total_cps_sweep"], float); cr = np.asarray(d["correlation_results"], float)
    ks = sorted(d["states"]["state_0"]["datasets"]); bk = [basis_of(d["states"]["state_0"]["datasets"][k]) for k in ks]
    corr = lambda w, j, q: {bk[i]: sw[w, j, q, i] for i in range(3)}
    iw = int(np.argmin(abs(WINDOWS - MAIN_W)))

    def at(w):
        wt = cps[w, :, 1] / cps[w, :, 1].sum()                       # authors' count-rate weights (Figure4.ipynb)
        fd = fid_from_corr(corr(w, 2, 0), TARGET); ud = u_fid_from_corr(corr(w, 2, 1))
        fm = sum(wt[j] * fid_from_corr(corr(w, j, 2), TARGET) for j in (0, 1))
        return fd, ud, fm, wt
    Fdat, ud, Fm, wt = at(iw)
    um_ok = bool(np.all((cr[1, :2] >= 0) & (cr[1, :2] < 0.2)))
    umod = float(np.hypot(*[wt[j] * u_fid_from_corr({bk[i]: cr[1, j, i] for i in range(3)}) for j in (0, 1)])) if um_ok else 0.0
    g3 = abs(Fdat - Fd["state_2"]) <= 0.005
    P(f"G3 flag  sweep at {MAIN_W:.0f} ns reproduces the h5 combined fidelity: {Fdat:.4f} vs {Fd['state_2']:.4f} -> {'PASS' if g3 else 'FAIL (flagged)'}")
    r = offset_test(Fm, Fdat, ud, umod); pw = float(norm.cdf(0.03 / r["u"] - Z95))
    tag = "optimism detected" if r["optimism_detected"] else ("underpowered: power at 0.03 < 0.8" if pw < 0.8 else "adequately powered")
    P(f"D2' {'PASS' if r['adequate'] else 'FAIL'}  model offset at {MAIN_W:.0f} ns (delivered states): F_model {Fm:.4f} (count-rate weights {wt.round(3).tolist()}), "
      f"F_data {Fdat:.4f}, Delta {r['delta']:+.4f} +- {r['u']:.4f} (bar {r['bar']:.4f}{'; WEAK TEST' if r['weak'] else ''}); "
      f"one-sided 95% interval [{r['lb']:+.4f}, {r['ub']:+.4f}]; power at 0.03: {pw:.2f} -> {tag}; model uncertainty {'used' if um_ok else 'NOT usable, set to 0'}")
    out["D2b"] = dict(pass_=bool(r["adequate"]), power003=pw, G3=bool(g3), **{k: (bool(v) if isinstance(v, (bool, np.bool_)) else float(v)) for k, v in r.items()})

    P("\n== SECONDARY")
    s1 = (Fdat - Z95 * ud) > 0.5
    P(f"S1' {'PASS' if s1 else 'FAIL'}  readout-corrected (model-dependent) bound: {Fdat:.4f} - 1.645 x {ud:.4f} = {Fdat - Z95 * ud:.4f} (bar > 0.5)")
    P(f"S2' descriptive  declared margin a safe guard would need: Delta upper bound {r['ub']:+.4f}")
    P("S3' descriptive  sweep (nested windows; no test):")
    rows = []
    for w in range(sw.shape[0]):
        fd, u_, fm, _ = at(w); rows.append([float(WINDOWS[w]), fd, u_, fm])
        P(f"   window {WINDOWS[w]:4.1f} ns: F_data {fd:.4f} +- {u_:.4f}, F_model {fm:.4f}, Delta {fm - fd:+.4f}")
    out["S1b"] = bool(s1); out["S3b"] = rows
    json.dump(out, open("results_35b.json", "w"), indent=1, default=float)
    return out


if __name__ == "__main__":
    main(sys.argv[1])
