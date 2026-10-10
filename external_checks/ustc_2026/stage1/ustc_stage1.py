"""USTC 2026 (Zenodo 18218281; 'Long-lived remote ion-ion entanglement for scalable quantum repeaters', figure data) Stage 1.
Pre-registration: PREREG_USTC_STAGE1.md. Usage: python3 ustc_stage1.py <dir with Fig_*.xlsx> <out.json>
U1  model-predicts-real: predict the remote entangled-state fidelity decay vs storage time (Fig 3d, alpha = 17%) from the
    SINGLE-ion KDD coherence curves (Fig S2b, Alice and Bob) with our simulator's memory model (pure dephasing:
    Z-correlations kept, X-correlations multiplied by each memory's coherence), anchored only at t = 0.
U2  real-link drift + guard replay: per-data-set QBER (Fig S8, 201 sets, in index order) -> over-dispersion against binomial
    with n = 4.05e5 / 201 pairs per set (assumption: equal set sizes; total from the paper), and the running Beta(1/2,1/2)
    mixture confidence sequence for the error rate: does it ever exclude the full-run rate?
"""
import json, math, sys
import numpy as np
import openpyxl

NTOT = 4.05e5; ALPHA = 0.05


def sheet(path, name, skip=1):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[name]
    rows = [r for r in ws.iter_rows(values_only=True)][skip:]
    return [r for r in rows if r and r[0] is not None and all(isinstance(x, (int, float)) for x in r[:3] if x is not None)]


def lgam(x): return math.lgamma(x)


def chi2_sf(x, dof):
    a, x = dof / 2.0, x / 2.0
    if x <= 0: return 1.0
    gln = lgam(a)
    if x < a + 1:
        ap, s, d = a, 1 / a, 1 / a
        for _ in range(100000):
            ap += 1; d *= x / ap; s += d
            if abs(d) < abs(s) * 1e-15: break
        return 1 - s * math.exp(-x + a * math.log(x) - gln)
    b = x + 1 - a; c = 1e300; d = 1 / b; h = d
    for i in range(1, 100000):
        an = -i * (i - a); b += 2; d = an * d + b; d = d if abs(d) > 1e-300 else 1e-300
        c = b + an / c; c = c if abs(c) > 1e-300 else 1e-300; d = 1 / d; de = d * c; h *= de
        if abs(de - 1) < 1e-15: break
    return math.exp(-x + a * math.log(x) - gln) * h


def coherence(t, T, C):
    """single-ion KDD contrast at time t (ms): linear interpolation inside the measured range, beyond it an exponential fit to
    the measured points (log-linear least squares), normalised to the contrast at t = 0 (interpolated)."""
    T, C = np.asarray(T, float), np.asarray(C, float); o = np.argsort(T); T, C = T[o], C[o]
    def raw(x):
        if T[0] <= x <= T[-1]: return float(np.interp(x, T, C))
        k, b = np.polyfit(T, np.log(np.clip(C, 1e-6, None)), 1); return float(math.exp(b + k * x))
    return raw(t) / raw(0.0)


def u1(d):
    A = sheet(f"{d}/Fig_S2b.xlsx", "Fig_S2b_Alice_KDD"); B = sheet(f"{d}/Fig_S2b.xlsx", "Fig_S2b_Bob_KDD")
    F = sheet(f"{d}/Fig_3d.xlsx", "Fig_3d_alpha=17%"); XZ = sheet(f"{d}/Fig_3d.xlsx", "Fig_3d_inset")
    tA, cA = [r[0] for r in A], [r[1] for r in A]; tB, cB = [r[0] for r in B], [r[1] for r in B]
    t, f, fs = np.array([r[0] for r in F]), np.array([r[1] for r in F]), np.array([r[2] for r in F])
    o = np.argsort(t); t, f, fs = t[o], f[o], fs[o]
    xx0 = abs(float(sorted(XZ, key=lambda r: r[0])[0][1]))                 # |XX| at the earliest storage time (inset)
    rows = []; ok = True
    for ti, fi, si in zip(t, f, fs):
        g = coherence(ti, tA, cA) * coherence(ti, tB, cB)
        dF_pred = (2 * xx0 / 4) * (g - 1); dF_meas = fi - f[0]
        tol = 2 * math.hypot(si, fs[0]) + 0.02
        hit = abs(dF_pred - dF_meas) <= tol; ok &= bool(hit) or ti == t[0]
        rows.append(dict(t_ms=float(ti), F_meas=float(fi), F_sd=float(si), coh_product=g, dF_pred=dF_pred, dF_meas=float(dF_meas), tol=tol, within=bool(hit)))
    xz = [dict(t_ms=r[0], XX=r[1], XX_sd=r[2], ZZ=r[3], ZZ_sd=r[4]) for r in sorted(XZ, key=lambda r: r[0])]
    return dict(pass_=bool(ok), xx0=xx0, rows=rows, inset_XX_ZZ=xz)


def u2(d):
    S = sheet(f"{d}/Fig_S8.xlsx", "Fig_S8"); S = sorted(S, key=lambda r: r[0])
    q = np.array([r[2] for r in S]) / 100.0; n = NTOT / len(S); k = np.round(q * n); N = np.full(len(q), round(n))
    p = k.sum() / N.sum(); X2 = float((((k - N * p) ** 2) / (N * p * (1 - p))).sum()); dof = len(k) - 1
    Kc, Nc = np.cumsum(k), np.cumsum(N)
    logM = np.array([lgam(a + .5) + lgam(b + .5) - lgam(a + b + 1) - (lgam(.5) * 2 - lgam(1.0)) - (a * math.log(p) + b * math.log(1 - p))
                     for a, b in zip(Kc, Nc - Kc)])
    excl = logM >= math.log(1 / ALPHA)
    chsh = np.array([r[1] for r in S])
    return dict(sets=len(S), n_per_set=n, qber_mean=float(p), dispersion=X2 / dof, disp_pvalue=chi2_sf(X2, dof),
                cs_ever_excludes_final=bool(excl.any()), cs_frac_excluding=float(excl.mean()),
                chsh_mean=float(chsh.mean()), chsh_sd_between_sets=float(chsh.std(ddof=1)))


if __name__ == "__main__":
    d, out = sys.argv[1], sys.argv[2]
    R = dict(U1=u1(d), U2=u2(d)); json.dump(R, open(out, "w"), indent=1, default=float)
    print("U1", "PASS" if R["U1"]["pass_"] else "FAIL", "xx0", round(R["U1"]["xx0"], 4))
    for r in R["U1"]["rows"]: print("  ", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})
    print("U2", {k: (round(v, 6) if isinstance(v, float) else v) for k, v in R["U2"].items()})
