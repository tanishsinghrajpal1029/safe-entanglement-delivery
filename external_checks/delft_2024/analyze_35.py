"""Study 35 (Delft) locked analysis. Usage: python3 analyze_35.py delft_extract_35.json > results_35.txt
Locked with PREREG_35.md. numpy + scipy only. Order: gates G1-G3, then D1, D2 (primary), then S1-S3 (secondary).
If a gate fails, the run stops and no hypothesis is scored.
"""
import json, sys
import numpy as np
from scipy.stats import norm
from delft_core import (BELL, Z95, parse_bell, correlator_from_p, errors_from_counts, certificate, fid_from_corr,
                        u_fid_from_corr, offset_test)

WINDOWS = np.linspace(5, 20, 16)          # herald-window lengths (ns) of the authors' sweep (Figure3.ipynb)
MAIN_W = 10.0                             # main-text window (Figure3.ipynb: "Circle data used in B" at x = 10)
STATES = ("state_0", "state_1")           # the two heralded states plotted in Fig. 3


def basis_of(rec):
    b1 = str(rec["node1_readout_basis"]).strip().upper()[-1:]; b2 = str(rec["node2_readout_basis"]).strip().upper()[-1:]
    return b1 if b1 == b2 and b1 in "XYZ" else None


def main(path):
    d = json.load(open(path)); out = {}; P = lambda *a: print(*a, flush=True)
    # ---------------- G1: labels, bases, targets
    olab = [str(x).strip() for x in (d["ssro_outcome_tick_labels"] or [])]
    if sorted(olab) != ["00", "01", "10", "11"]:
        P(f"G1 note: outcome labels {olab!r} not 00/01/10/11; using the authors' order ['00','01','10','11']")
        olab = ["00", "01", "10", "11"]
    slabs = d["state_generated_tick_labels"]; targets = {}
    for j, st in enumerate(STATES):
        targets[st] = parse_bell(slabs[j]) if slabs and j < len(slabs) else None
    order = {st: [basis_of(d["states"][st]["datasets"][k]) for k in sorted(d["states"][st]["datasets"])] for st in STATES}
    P(f"G1 outcome order {olab}; state labels {slabs}; targets {targets}; basis order {order}")
    g1 = all(targets.values()) and all(sorted(v) == ["X", "Y", "Z"] for v in order.values())
    P(f"G1 {'PASS' if g1 else 'FAIL'}"); out["G1"] = g1
    if not g1: P("STOP: gate G1 failed; no hypothesis scored."); return out
    sg = {st: BELL[targets[st]] for st in STATES}
    # ---------------- G2: parity convention (our correlator from p vs the authors' correlation attribute)
    dev = max(abs(correlator_from_p(r["p"], olab) - float(r["correlation"])) for st in STATES for r in d["states"][st]["datasets"].values())
    g2 = dev <= 0.002; P(f"G2 parity convention: max |c(p) - correlation| = {dev:.5f} (<= 0.002) {'PASS' if g2 else 'FAIL'}"); out["G2"] = g2
    if not g2: P("STOP: gate G2 failed."); return out
    # ---------------- G0: target mapping (our F from the correlation attributes vs the authors' fidelity attribute)
    c = {st: {basis_of(r): float(r["correlation"]) for r in d["states"][st]["datasets"].values()} for st in STATES}
    uc = {st: {basis_of(r): float(r["u_correlation"]) for r in d["states"][st]["datasets"].values()} for st in STATES}
    Fd = {st: fid_from_corr(c[st], sg[st]) for st in STATES}
    dev0 = max(abs(Fd[st] - float(d["states"][st]["fidelity"])) for st in STATES)
    g0 = dev0 <= 0.005; P(f"G0 target mapping: our F {Fd} vs attribute; max diff {dev0:.5f} (<= 0.005) {'PASS' if g0 else 'FAIL'}"); out["G0"] = g0
    if not g0: P("STOP: gate G0 failed."); return out
    rd = max(abs(np.asarray(r["p"]) - np.asarray(r["N"]) / max(sum(r["N"]), 1)).max() for st in STATES for r in d["states"][st]["datasets"].values())
    P(f"info: max |p - N/sum(N)| = {rd:.4f} ({'p is readout-corrected' if rd > 1e-6 else 'p equals raw frequencies'})")
    n_b = {b: sum(sum(r["N"]) for st in STATES for r in d["states"][st]["datasets"].values() if basis_of(r) == b) for b in "XYZ"}
    P(f"info: events per basis (both states) {n_b}")

    P("\n== PRIMARY")
    # ---------------- D1: model-free certificate from raw counts, pooled over the two heralded states
    pooled = {b: [0, 0] for b in "XYZ"}; per_state = {}
    for st in STATES:
        eb = {}
        for r in d["states"][st]["datasets"].values():
            b = basis_of(r); k, n = errors_from_counts(r["N"], olab, sg[st][b]); eb[b] = (k, n); pooled[b][0] += k; pooled[b][1] += n
        per_state[st] = certificate(eb)
    cert = certificate({b: tuple(v) for b, v in pooled.items()})
    d1 = cert["F_lo"] > 0.5
    P(f"D1 {'PASS' if d1 else 'FAIL'}  raw-count certificate (both states pooled): F_hat {cert['F_hat']:.4f}, F_lo(95%) {cert['F_lo']:.4f} (bar > 0.5); "
      f"per state: " + "; ".join(f"{st} F_hat {v['F_hat']:.4f} F_lo {v['F_lo']:.4f}" for st, v in per_state.items()))
    out["D1"] = dict(pass_=d1, **{k: cert[k] for k in ("F_hat", "F_lo")}, per_state={k: (v["F_hat"], v["F_lo"]) for k, v in per_state.items()})
    # ---------------- D2: model offset at the main window (authors' model correlators, correlation_results)
    cr = np.asarray(d["correlation_results"], dtype=float)       # [value/unc, state, dataset index]
    ks = {st: sorted(d["states"][st]["datasets"]) for st in STATES}
    cm = {st: {basis_of(d["states"][st]["datasets"][k]): cr[0, j, i] for i, k in enumerate(ks[st])} for j, st in enumerate(STATES)}
    um_ok = np.all((cr[1, :2] >= 0) & (cr[1, :2] < 0.2))
    um = {st: {basis_of(d["states"][st]["datasets"][k]): (cr[1, j, i] if um_ok else 0.0) for i, k in enumerate(ks[st])} for j, st in enumerate(STATES)}
    Fm = np.mean([fid_from_corr(cm[st], sg[st]) for st in STATES]); Fdat = np.mean([Fd[st] for st in STATES])
    ud = 0.5 * np.hypot(*[u_fid_from_corr(uc[st]) for st in STATES]); umod = 0.5 * np.hypot(*[u_fid_from_corr(um[st]) for st in STATES])
    r = offset_test(Fm, Fdat, ud, umod); pw = float(norm.cdf(0.03 / r["u"] - Z95))
    d2 = r["adequate"]
    tag = "optimism detected" if r["optimism_detected"] else ("underpowered: power at 0.03 < 0.8" if pw < 0.8 else "adequately powered")
    P(f"D2 {'PASS' if d2 else 'FAIL'}  model offset at {MAIN_W:.0f} ns: F_model {Fm:.4f}, F_data {Fdat:.4f}, Delta {r['delta']:+.4f} +- {r['u']:.4f} "
      f"(bar |Delta| <= 2u + 0.02 = {r['bar']:.4f}{'; WEAK TEST' if r['weak'] else ''}); one-sided 95% interval [{r['lb']:+.4f}, {r['ub']:+.4f}]; "
      f"power at Delta = 0.03: {pw:.2f} -> {tag}; model uncertainty {'used' if um_ok else 'NOT usable, set to 0'}")
    out["D2"] = dict(pass_=d2, power003=pw, model_u_used=bool(um_ok), **{k: (bool(v) if isinstance(v, (bool, np.bool_)) else float(v)) for k, v in r.items()})

    P("\n== SECONDARY")
    s1 = (Fdat - Z95 * ud) > 0.5
    P(f"S1 {'PASS' if s1 else 'FAIL'}  readout-corrected (model-dependent) bound: F_data {Fdat:.4f} - 1.645 x {ud:.4f} = {Fdat - Z95 * ud:.4f} (bar > 0.5)")
    P(f"S2 descriptive  declared margin a safe guard would need: Delta upper bound {r['ub']:+.4f}")
    sw = np.asarray(d["total_result_sweep"], dtype=float)      # [window, state, (data, unc, model), dataset index]
    rows = []
    for w in range(sw.shape[0]):
        fd = np.mean([fid_from_corr({basis_of(d["states"][st]["datasets"][k]): sw[w, j, 0, i] for i, k in enumerate(ks[st])}, sg[st]) for j, st in enumerate(STATES)])
        fm = np.mean([fid_from_corr({basis_of(d["states"][st]["datasets"][k]): sw[w, j, 2, i] for i, k in enumerate(ks[st])}, sg[st]) for j, st in enumerate(STATES)])
        uu = 0.5 * np.hypot(*[u_fid_from_corr({basis_of(d["states"][st]["datasets"][k]): sw[w, j, 1, i] for i, k in enumerate(ks[st])}) for j, st in enumerate(STATES)])
        rows.append((WINDOWS[w], fd, fm, uu))
    iw = int(np.argmin(abs(WINDOWS - MAIN_W))); g3 = abs(rows[iw][1] - Fdat) <= 0.005
    P(f"S3 descriptive  sweep (G3 {'PASS' if g3 else 'FAIL'}: sweep F at {MAIN_W:.0f} ns {rows[iw][1]:.4f} vs main {Fdat:.4f}); nested windows, no test:")
    for w, fd, fm, uu in rows: P(f"   window {w:4.1f} ns: F_data {fd:.4f} +- {uu:.4f}, F_model {fm:.4f}, Delta {fm - fd:+.4f}")
    out["S1"] = bool(s1); out["S3"] = dict(G3=bool(g3), rows=[list(map(float, x)) for x in rows])
    json.dump(out, open("results_35.json", "w"), indent=1, default=float)
    return out


if __name__ == "__main__":
    main(sys.argv[1])
