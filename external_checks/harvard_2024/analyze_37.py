"""Study 37: pre-registered re-analysis of the Harvard SiV-SiV / 29Si-29Si entanglement records (Knaut et al., Nature 2024).

The authors' own analysis functions are executed from their shared notebooks (cells listed below; notebook hashes are
checked), never copied into this repository. We add only: (i) a recorder that keeps the per-herald readout thresholds
and contrasts the authors' code computes, so that every herald can be placed in time order; (ii) our tests (PREREG_37.md).

Usage
  python3 analyze_37.py --root <path>/To_share --out <dir> --stage 1          # gates only
  python3 analyze_37.py --root <path>/To_share --out <dir> --stage 2          # gates, then H1-H4 and descriptives
  python3 analyze_37.py --synthetic <empty dir> --out <dir> --stage 2         # same pipeline on synthetic data (testing)
"""
import argparse, hashlib, json, os, sys, time
import numpy as np
from scipy.stats import beta, chi2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cert import Certifier  # noqa: E402  (the paper's Prop. C1 certificate, unchanged from study27_certification/cert.py)

ALPHA = 0.05; B_BOOT = 20000; BOOT_SEED = 3037; SEEDS = range(37001, 38001); PS = (0.1, 0.2)
if os.environ.get("S37_TEST_SMALL"):                     # synthetic testing only: fewer resamples and draws (never for the real run)
    B_BOOT, SEEDS = 500, range(37001, 37101)
NB_EE = ("analysis scripts", "YC_2026_E-E_musweep_analysis_new_new_dyn.ipynb")
NB_NN = ("analysis scripts", "N-N_hold_telecom_analysis_new_eff_dyn.ipynb")
NB_SHA = {NB_EE[1]: "758f87b801c21d63", NB_NN[1]: None}         # NN hash recorded at freeze time (HASHES_PREREG_37.txt)
EE_DEF_CELLS, EE_CFG_CELL = [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], 17
NN_DEF_CELLS, NN_CFG = [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16], {"hold": 18, "telecom": 22}
PUBLISHED = {"EE_minus": (0.86, 0.03), "EE_plus": (0.74, 0.03), "NH10_ED_minus": (0.77, 0.05), "NH10_raw_minus": (0.64, 0.05)}
T2_MS = (2110.0, 2100.0)                                         # Knaut et al. Table S4, XY8-128, nodes A and B
HOLD_MS = {1: 250, 4: 500, 3: 750, 2: 1000, 0: 10}               # index in the authors' hold configuration -> hold time
GOOD_EE = {"Z": {0, 3}, "X": {"m": {1, 2}, "p": {0, 3}}, "Y": {"m": {0, 3}, "p": {1, 2}}}


# ---------------------------------------------------------------- loading the authors' code
def load_cells(nb_path, cells, ns):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    nb = json.load(open(nb_path))
    for i in cells:
        c = nb["cells"][i]; assert c["cell_type"] == "code", (nb_path, i)
        exec(compile("".join(c["source"]), f"{os.path.basename(nb_path)}[{i}]", "exec"), ns)
    plt.show = lambda *a, **k: plt.close("all")
    return ns


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


class Recorder:
    """Wraps the authors' dynamic_readout_thresholding_local and keeps its outputs in call order."""
    def __init__(s, f): s.f, s.calls = f, []
    def __call__(s, x, plot=False):
        r = s.f(x, plot=False); s.calls.append(r); return r


def ee_namespace(root):
    ns = {"__name__": "ee_ns"}
    load_cells(os.path.join(root, *NB_EE), EE_DEF_CELLS + [EE_CFG_CELL], ns)
    ns["BASEPATH"] = os.path.join(root, "data", "electron-electron entanglement", "mu-sweep")
    return ns


def nn_namespace(root, which):
    ns = {"__name__": "nn_ns"}
    load_cells(os.path.join(root, *NB_NN), NN_DEF_CELLS + [NN_CFG[which]], ns)
    ns["BASEPATH"] = os.path.join(root, "data", "nucleus-nucleus entanglement", which)
    return ns


# ---------------------------------------------------------------- per-herald records with the authors' pipeline
def heralds_ee(ns, idx):
    """Runs the authors' EE pipeline for run idx; returns their Bell counts and per-herald records in time order."""
    rd = ns["retrieve_data"](ns["filename_id_s"][idx])
    B16, G12, A1, A2 = ns["normalize_lengths"](rd)
    rec = Recorder(ns["dynamic_readout_thresholding_local"]); ns["dynamic_readout_thresholding_local"] = rec
    try:
        out = ns["split_and_apd_threshold_data"](B16, G12, A1, A2, ns["dynamic_threshold"], ns["len_chunk"],
                                                 ns["thresholds_contrasts"][idx], ns["contrast_postselection"], print_vals=False)
    finally:
        ns["dynamic_readout_thresholding_local"] = rec.f
    b16c, g12c, a1c, a2c, _, b16eth, g12eth = out
    bell, bell_raw, clicks = ns["generate_bell_counts"](b16c, g12c, a1c, a2c, b16eth, g12eth, ns["dynamic_threshold"], ns["thresholds_array"][idx])
    rows = []; pos = 0; thc = ns["thresholds_contrasts"][idx]
    for k in range(3):
        a1k, a2k = A1[k::3], A2[k::3]
        one = np.where((a1k > 0) | (a2k > 0))[0]
        calls = rec.calls[pos:pos + 2 * len(one)]; pos += 2 * len(one)
        bc = np.array([c[1] for c in calls[0::2]]); gc = np.array([c[1] for c in calls[1::2]])
        be = np.array([c[0] for c in calls[0::2]]); ge = np.array([c[0] for c in calls[1::2]])
        keep = np.where((bc > thc[0]) & (gc > thc[1]))[0] if ns["contrast_postselection"] else np.arange(len(one))
        sel = one[keep]
        up_b = B16[k::3][sel] > be[keep]; up_g = G12[k::3][sel] > ge[keep]
        o = up_b.astype(int) + 2 * up_g.astype(int)
        for sgn, apd in (("p", a1k[sel]), ("m", a2k[sel])):                   # authors' rule: herald counted if (count & 1)
            on = (apd & 1).astype(bool)
            for j in np.where(on)[0]:
                rows.append((3 * int(sel[j]) + k, k, sgn, int(o[j]), 1))
    assert pos == len(rec.calls), "recorder/one_count mismatch"
    return bell, bell_raw, clicks, rows, len(B16), rd


def heralds_nn(ns, idx):
    """Authors' NN pipeline for configuration idx; per-herald rows carry an error-detection flag."""
    fid = ns["filename_id_s"][idx]; dates = ns["date_array"][idx]; times = ns["times_array"][idx]
    if isinstance(fid, list):
        rd = ns["combine_multiaxis"](fid, dates, times) if fid[0] is True else ns["reformat_single_axis"](fid, dates, times)
    else:
        rd = ns["retrieve_data"](fid, dates, times)
    B16, G12, B16S, G12S, A1, A2 = ns["normalize_lengths"](rd, ns["len_chunk"])
    rec = Recorder(ns["dynamic_readout_thresholding_local"]); ns["dynamic_readout_thresholding_local"] = rec
    try:
        out = ns["split_and_apd_threshold_data"](B16, G12, B16S, G12S, A1, A2, ns["dynamic_threshold"], ns["len_chunk"],
                                                 ns["thresholds_contrasts"][idx], ns["contrast_postselection"], print_vals=False)
    finally:
        ns["dynamic_readout_thresholding_local"] = rec.f
    b16c, g12c, a1c, a2c, b16sc, g12sc, b16eth, g12eth = out
    flip = ns["flip_phone_array"][idx]
    bell, bell_raw, clicks = ns["generate_bell_counts"](b16c, g12c, b16sc, g12sc, a1c, a2c, b16eth, g12eth, ns["dynamic_threshold"],
                                                        ns["thresholds_array"][idx], flip, plot=False)
    rows = []; pos = 0; thc = ns["thresholds_contrasts"][idx]
    for k in range(3):
        a1k, a2k = A1[k::3], A2[k::3]
        one = np.where((a1k > 0) | (a2k > 0))[0]
        calls = rec.calls[pos:pos + 2 * len(one)]; pos += 2 * len(one)
        bc = np.array([c[1] for c in calls[0::2]]); gc = np.array([c[1] for c in calls[1::2]])
        be = np.array([c[0] for c in calls[0::2]]); ge = np.array([c[0] for c in calls[1::2]])
        keep = np.where((bc > thc[0]) & (gc > thc[1]))[0] if ns["contrast_postselection"] else np.arange(len(one))
        sel = one[keep]; be, ge = be[keep], ge[keep]
        eb = B16[k::3][sel] > be; eg = G12[k::3][sel] > ge
        nb = np.abs(eb.astype(int) - (B16S[k::3][sel] > be).astype(int)).astype(bool)
        ng = np.abs(eg.astype(int) - (G12S[k::3][sel] > ge).astype(int)).astype(bool)
        pb = eb if flip[0] is True else ~eb; pg = eg if flip[1] is True else ~eg
        o = nb.astype(int) + 2 * ng.astype(int); ed = (pb & pg)
        for sgn, apd in (("p", a1k[sel]), ("m", a2k[sel])):
            on = (apd & 1).astype(bool)
            for j in np.where(on)[0]:
                rows.append((3 * int(sel[j]) + k, k, sgn, int(o[j]), int(ed[j])))
    assert pos == len(rec.calls)
    return bell, bell_raw, clicks, rows, len(B16), rd


def recount(rows, ed=None):
    """Bell counts (basis, sign[p,m], outcome) from per-herald rows; ed=True keeps error-detection passes only."""
    c = np.zeros((3, 2, 4))
    for (_, k, s, o, f) in rows:
        if ed is True and not f: continue
        c[k, 0 if s == "p" else 1, o] += 1
    return c


def good_sets(ns=None):
    """Outcome indices that count as 'good' per (basis, sign), read from the authors' conventions."""
    if ns is None or "MINUS_INDICES" not in ns:
        return {(0, "m"): GOOD_EE["X"]["m"], (0, "p"): GOOD_EE["X"]["p"], (1, "m"): GOOD_EE["Y"]["m"], (1, "p"): GOOD_EE["Y"]["p"],
                (2, "m"): GOOD_EE["Z"], (2, "p"): GOOD_EE["Z"]}
    MI, PI = ns["MINUS_INDICES"], ns["PLUS_INDICES"]
    return {(0, "m"): set(MI[0][:2]), (0, "p"): set(PI[0][:2]), (1, "m"): set(MI[1][:2]), (1, "p"): set(PI[1][:2]),
            (2, "m"): {0, 3}, (2, "p"): {0, 3}}


def fid_from_rows(rows, good, sign, ed=None):
    """F = 1 - (eX + eY + eZ)/2 and P_ZZ for one herald sign."""
    e = np.zeros(3); n = np.zeros(3)
    for (_, k, s, o, f) in rows:
        if s != sign or (ed is True and not f): continue
        n[k] += 1; e[k] += o not in good[(k, s)]
    er = e / np.maximum(n, 1)
    return 1 - er.sum() / 2, 1 - er[2], n, e


def cp_lo(k, n, a): return 0.0 if k == 0 else float(beta.ppf(a, k, n - k + 1))
def cp_up(k, n, a): return 1.0 if k >= n else float(beta.ppf(1 - a, k + 1, n - k))


# ---------------------------------------------------------------- stage 1
def stage1(root, log):
    res = {"EE": [], "NH10": None}
    ee = ee_namespace(root); G = good_sets()
    log("== Stage 1 (gates): the authors' own pipeline and settings")
    match = []
    for i in range(len(ee["filename_id_s"])):
        bell, bell_raw, clicks, rows, n, _ = heralds_ee(ee, i)
        g0 = np.array_equal(recount(rows), bell_raw)
        _, _, F_total, F_err, *_ = ee["calc_fidelities"](bell, clicks)
        Fp, Fm = float(F_total[0]), float(F_total[1]); ep, em = float(F_err[0]), float(F_err[1])
        okm = abs(Fm - PUBLISHED["EE_minus"][0]) <= 2 * np.hypot(PUBLISHED["EE_minus"][1], em)
        okp = abs(Fp - PUBLISHED["EE_plus"][0]) <= 2 * np.hypot(PUBLISHED["EE_plus"][1], ep)
        z = np.hypot((Fm - 0.86) / np.hypot(0.03, em), (Fp - 0.74) / np.hypot(0.03, ep))
        res["EE"].append(dict(run=i, aom=ee["aom_voltages_array"][i], shots=n, heralds=len(rows), G0=bool(g0),
                              F_minus=Fm, err_minus=em, F_plus=Fp, err_plus=ep, match=bool(okm and okp), z=float(z)))
        log(f"   EE run {i} (AOM {ee['aom_voltages_array'][i]}): heralds {len(rows)}; G0 recount = authors' counts: {g0}; "
            f"F(-) {Fm:.3f}+/-{em:.3f}, F(+) {Fp:.3f}+/-{ep:.3f} -> {'MATCH' if okm and okp else 'no match'}")
        if okm and okp: match.append((z, i))
    res["G1"] = bool(match); res["EE_published_run"] = min(match)[1] if match else None
    nh = nn_namespace(root, "hold")
    bell, bell_raw, clicks, rows, n, _ = heralds_nn(nh, 0)
    g0_ed = np.array_equal(recount(rows, ed=True), bell_raw[0]); g0_raw = np.array_equal(recount(rows), bell_raw[1])
    _, _, F_total, F_err, *_ = nh["calc_fidelities"](bell, clicks)
    Fed, Fraw = float(F_total[0][1]), float(F_total[1][1]); eed, eraw = float(F_err[0][1]), float(F_err[1][1])
    ok2 = abs(Fed - 0.77) <= 2 * np.hypot(0.05, eed) and abs(Fraw - 0.64) <= 2 * np.hypot(0.05, eraw)
    res["NH10"] = dict(F_ED_minus=Fed, err_ED=eed, F_raw_minus=Fraw, err_raw=eraw, G0=bool(g0_ed and g0_raw), match=bool(ok2))
    res["G2"] = bool(ok2)
    log(f"   NH 10 ms (XY8-1), Phi-: G0 {g0_ed and g0_raw}; F_ED {Fed:.3f}+/-{eed:.3f} (pub 0.77(5)), F_raw {Fraw:.3f}+/-{eraw:.3f} (pub 0.64(5)) -> {'MATCH' if ok2 else 'no match'}")
    g0all = all(r["G0"] and r["heralds"] > 0 for r in res["EE"]) and res["NH10"]["G0"] and len(rows) > 0
    res["G0"] = g0all
    log(f"G0 (per-herald records reproduce the authors' Bell counts exactly): {'PASS' if g0all else 'FAIL'}")
    log(f"G1 (EE published fidelities reproduced): {'PASS, run ' + str(res['EE_published_run']) if res['G1'] else 'FAIL'}")
    log(f"G2 (NH 10 ms published fidelities reproduced): {'PASS' if res['G2'] else 'FAIL'}")
    return res


# ---------------------------------------------------------------- stage 2
def boot_delta(rows_by_t, good, ts_pred, t0=250.0):
    """H1: Delta(t) = F_pred(t) - F_meas(t), with F_pred from the 250 ms anchor (ED, Phi-). Bootstrap over heralds."""
    rate = 1 / T2_MS[0] + 1 / T2_MS[1]
    def summ(rows):
        F, Pzz, *_ = fid_from_rows(rows, good, "m", ed=True); return F, Pzz
    rng = np.random.default_rng(BOOT_SEED)
    base = {t: [r for r in rows_by_t[t] if r[2] == "m" and r[4]] for t in rows_by_t}
    F0, P0 = summ(base[t0])
    pt = {t: 0.5 * P0 + (F0 - 0.5 * P0) * np.exp(-(t - t0) * rate) for t in ts_pred}
    point = {t: pt[t] - summ(base[t])[0] for t in ts_pred}
    bs = {t: np.empty(B_BOOT) for t in ts_pred}
    arr = {t: np.array([(r[1], r[3]) for r in base[t]]) for t in base}
    gm = {k: np.array(sorted(good[(k, "m")])) for k in range(3)}
    def fast(a):
        e = np.zeros(3); n = np.zeros(3)
        for k in range(3):
            m = a[:, 0] == k; n[k] = m.sum(); e[k] = (~np.isin(a[m, 1], gm[k])).sum()
        er = e / np.maximum(n, 1); return 1 - er.sum() / 2, 1 - er[2]
    for b in range(B_BOOT):
        a0 = arr[t0][rng.integers(0, len(arr[t0]), len(arr[t0]))]; F0b, P0b = fast(a0)
        for t in ts_pred:
            at = arr[t][rng.integers(0, len(arr[t]), len(arr[t]))]
            bs[t][b] = 0.5 * P0b + (F0b - 0.5 * P0b) * np.exp(-(t - t0) * rate) - fast(at)[0]
    v = {t: bs[t].var() for t in ts_pred}; w = {t: 1 / v[t] for t in ts_pred}
    pooled = sum(w[t] * point[t] for t in ts_pred) / sum(w.values())
    pooled_bs = sum(w[t] * bs[t] for t in ts_pred) / sum(w.values())
    return pt, point, {t: np.quantile(bs[t], [0.025, 0.975]) for t in ts_pred}, pooled, np.quantile(pooled_bs, [0.025, 0.975]), F0, P0


def chi2_blocks(succ, tot):
    """Heterogeneity across blocks; blocks merged pairwise (10 -> 5) if any expected count < 5; None if still too small."""
    succ, tot = np.asarray(succ, float), np.asarray(tot, float)
    for _ in range(2):
        p = succ.sum() / tot.sum(); exp1, exp0 = tot * p, tot * (1 - p)
        if min(exp1.min(), exp0.min()) >= 5: break
        if len(succ) <= 5: return None
        succ, tot = succ.reshape(-1, 2).sum(1), tot.reshape(-1, 2).sum(1)
    else:
        return None
    p = succ.sum() / tot.sum(); exp1, exp0 = tot * p, tot * (1 - p)
    if min(exp1.min(), exp0.min()) < 5: return None
    x2 = (((succ - exp1) ** 2) / exp1 + (((tot - succ) - exp0) ** 2) / exp0).sum()
    return float(x2), len(succ) - 1, float(chi2.sf(x2, len(succ) - 1))


def h2_tests(name, rows, nshots, ed=None):
    """ZZ error rate across 10 equal-herald blocks; heralds per shot across 10 equal-shot blocks."""
    out = []
    z = sorted([r for r in rows if r[1] == 2 and (ed is not True or r[4])])
    if len(z) >= 20:
        bl = np.array_split(np.arange(len(z)), 10)
        err = [sum(1 for j in b if z[j][3] not in (0, 3)) for b in bl]; tot = [len(b) for b in bl]
        out.append((f"{name} ZZ error", chi2_blocks(err, tot)))
    else:
        out.append((f"{name} ZZ error", None))           # fewer than 20 Z-basis heralds: reported as NA
    edges = np.linspace(0, nshots, 11); h = np.histogram([r[0] for r in rows if ed is not True or r[4]], edges)[0]
    out.append((f"{name} herald rate", chi2_blocks(h, np.diff(edges))))
    return out


def certificate_draws(rows, good, sign):
    """H3/H4: random test-or-keep labelling on time-ordered heralds of one sign; returns per-p violation and level counts."""
    r = sorted([x for x in rows if x[2] == sign])
    err = np.array([0 if x[3] in good[(x[1], sign)] else 1 for x in r]); bas = np.array([x[1] for x in r])
    out = {}
    for p in PS:
        cert = Certifier(p, ALPHA); viol = 0; ab05 = ab08 = 0; finals = []
        for sd in SEEDS:
            T = np.random.default_rng(sd).random(len(r)) < p
            K = int((~T).sum()); Err = int(err[T].sum())
            if K == 0: continue
            L = cert.lower(Err, K); finals.append(L)
            # conservative upper bound on the kept pairs' fidelity: 1 - sum_B CP_lower(e_B)/2, each at 0.025/3
            U = 1 - sum(cp_lo(int(err[~T & (bas == k)].sum()), int((~T & (bas == k)).sum()), 0.025 / 3) for k in range(3)) / 2
            viol += L > U; ab05 += L > 0.5; ab08 += L > 0.8
        n = len(finals)
        out[p] = dict(n=n, viol=int(viol), viol_lo=cp_lo(int(viol), n, ALPHA), viol_up=cp_up(int(viol), n, ALPHA),
                      above05=ab05 / max(n, 1), above08=ab08 / max(n, 1), median_cert=float(np.median(finals)) if finals else None,
                      heralds=len(r))
    return out


def stage2(root, s1, log):
    log("\n== Stage 2")
    ee = ee_namespace(root); G = good_sets()
    nh = nn_namespace(root, "hold"); Gn = good_sets(nh)
    ee_rows, ee_n = {}, {}
    for i in range(len(ee["filename_id_s"])):
        _, _, _, rows, n, _ = heralds_ee(ee, i); ee_rows[i], ee_n[i] = rows, n
    nh_rows, nh_n = {}, {}
    for i in range(len(nh["filename_id_s"])):
        _, _, _, rows, n, _ = heralds_nn(nh, i); nh_rows[HOLD_MS[i]], nh_n[HOLD_MS[i]] = rows, n

    if s1["G2"]:
        pt, point, ci, pooled, pci, F0, P0 = boot_delta(nh_rows, Gn, [500, 750, 1000])
        log(f"H1 memory model (ED, Phi-), anchor 250 ms: F={F0:.3f}, P_ZZ={P0:.3f}; T2 = {T2_MS} ms")
        for t in (500, 750, 1000):
            log(f"   {t} ms: predicted {pt[t]:.3f}, offset {point[t]:+.3f} [{ci[t][0]:+.3f}, {ci[t][1]:+.3f}]")
        log(f"   pooled offset {pooled:+.3f} [{pci[0]:+.3f}, {pci[1]:+.3f}] -> {'PASS (contains 0)' if pci[0] <= 0 <= pci[1] else 'FAIL (offset detected)'}; "
            f"declared margin would be {max(pci[1], 0):.3f}")
    else:
        log("H1 not run: gate G2 failed")

    tests = []
    if s1["G1"]:                                           # a failed gate removes that dataset from the tests
        for i in ee_rows: tests += h2_tests(f"EE run {i}", ee_rows[i], ee_n[i])
    else: log("H2: EE tests not run (gate G1 failed)")
    if s1["G2"]:
        for t in sorted(nh_rows): tests += h2_tests(f"NH {t} ms (ED)", nh_rows[t], nh_n[t], ed=True)
    else: log("H2: NH tests not run (gate G2 failed)")
    valid = [(n, r) for n, r in tests if r is not None]; m = len(valid)
    log(f"H2 calibration noise beyond chance: {m} valid tests (Bonferroni x{m})")
    for n, r in tests:
        log(f"   {n}: " + ("too few counts (NA)" if r is None else f"chi2 {r[0]:.1f}, df {r[1]}, p {r[2]:.2g}"))
    pmin = min((r[2] for _, r in valid), default=1.0)
    log(f"   min p x {m} = {min(1, pmin * m):.2g} -> {'PASS (over-dispersion detected)' if pmin * m < 0.05 else 'FAIL'}")

    if s1["G1"]:
        pub = s1["EE_published_run"]
        pooled_rows = []
        off = 0
        for i in sorted(ee_rows):
            pooled_rows += [(r[0] + off, *r[1:]) for r in ee_rows[i]]; off += ee_n[i]
        for label, rows in ((f"EE run {pub} (published)", ee_rows[pub]), ("EE pooled (5 runs)", pooled_rows)):
            for sign in ("m", "p"):
                o = certificate_draws(rows, G, sign)
                for p in PS:
                    d = o[p]
                    log(f"H3/H4 {label}, Phi{'-' if sign == 'm' else '+'}, p={p}: heralds {d['heralds']}; violating draws {d['viol']}/{d['n']} "
                        f"(CP95 lower {d['viol_lo']:.3f}) -> {'FAIL' if d['viol_lo'] > 0.05 else 'PASS'}; median certificate {d['median_cert']:.3f}; "
                        f"> 0.5 in {d['above05']:.0%}, > 0.8 in {d['above08']:.0%}")
    else:
        log("H3/H4 not run: gate G1 failed")

    log("\n== Descriptive")
    for i in ee_rows:
        Fm, *_ = fid_from_rows(ee_rows[i], G, "m"); Fp, *_ = fid_from_rows(ee_rows[i], G, "p")
        log(f"D1 EE AOM {ee['aom_voltages_array'][i]}: F(-) {Fm:.3f}, F(+) {Fp:.3f}, heralds {len(ee_rows[i])}, shots {ee_n[i]}")
    for t in sorted(nh_rows):
        Fe, *_ = fid_from_rows(nh_rows[t], Gn, "m", ed=True); Fr, *_ = fid_from_rows(nh_rows[t], Gn, "m")
        log(f"D2 NH {t} ms: F_ED(-) {Fe:.3f}, F_raw(-) {Fr:.3f}, heralds {len(nh_rows[t])}")
    try:
        nt = nn_namespace(root, "telecom"); Gt = good_sets(nt)
        for i in range(len(nt["filename_id_s"])):
            _, _, _, rows, n, _ = heralds_nn(nt, i)
            Fe, *_ = fid_from_rows(rows, Gt, "m", ed=True); Fr, *_ = fid_from_rows(rows, Gt, "m")
            log(f"D3 telecom {nt['distance'][i]} km: F_ED(-) {Fe:.3f}, F_raw(-) {Fr:.3f}, heralds {len(rows)}")
    except Exception as e:                                   # descriptive only; failure is reported, not hidden
        log(f"D3 telecom not computed: {type(e).__name__}: {e}")


# ---------------------------------------------------------------- synthetic data (testing only)
def make_synthetic(root, n_shots=60000, seed=1):
    """Writes data with the real file layout and ids, but random content, so the pipeline can be tested without the data."""
    import shutil
    rng = np.random.default_rng(seed)
    src = os.environ.get("S37_NOTEBOOKS")                        # folder holding the two notebooks (code is needed, not data)
    os.makedirs(os.path.join(root, "analysis scripts"), exist_ok=True)
    for nb in (NB_EE[1], NB_NN[1]): shutil.copy(os.path.join(src, nb), os.path.join(root, "analysis scripts", nb))
    n_shots -= n_shots % 3

    def bell(F, basis, sign, gs=None):
        """outcome index for one heralded pair, 'good' with probability F in each basis (0 X, 1 Y, 2 Z)."""
        good = (gs or good_sets())[(basis, sign)]
        pool = sorted(good) if rng.random() < F else sorted({0, 1, 2, 3} - set(good))
        return pool[rng.integers(len(pool))]

    def write(folder, prefix, fid, arrays, start="01/01/2023 00:00:00:000000"):
        os.makedirs(folder, exist_ok=True)
        for name, a in arrays.items(): np.save(os.path.join(folder, f"{prefix}_{name}_{fid}_12_00_00.npy"), a.astype(np.int32))
        json.dump({"exp_start_time": start}, open(os.path.join(folder, f"{prefix}_metadata_{fid}_12_00_00.json"), "w"))
        os.makedirs(os.path.join(folder, "pickled_data"), exist_ok=True)

    ee = {"__name__": "x"}; load_cells(os.path.join(root, *NB_EE), [EE_CFG_CELL], ee)
    for i, fid in enumerate(ee["filename_id_s"]):
        dark, bright = rng.poisson(1.5, (2, n_shots)), rng.poisson(30, (2, n_shots))
        up = rng.random((2, n_shots)) < 0.5
        her = rng.random(n_shots) < 0.01; sg = rng.random(n_shots) < 0.5
        for s in np.where(her)[0]:
            o = bell(0.85 - 0.02 * i, s % 3, "p" if sg[s] else "m"); up[0, s], up[1, s] = bool(o & 1), bool(o & 2)
        cnt = np.where(up, bright, dark)
        write(os.path.join(root, "data", "electron-electron entanglement", "mu-sweep"), f"si_init_{i}", fid,
              {"electron-b16-": cnt[0], "electron-g12-": cnt[1], "onebin-apd1-middle-peak": (her & sg).astype(int),
               "onebin-apd2-middle-peak": (her & ~sg).astype(int)})
    for which in ("hold", "telecom"):
        nn = {"__name__": "x"}; load_cells(os.path.join(root, *NB_NN), [NN_CFG[which]], nn); gsn = good_sets(nn)
        for i, fid in enumerate(nn["filename_id_s"]):
            ids = fid[1:] if isinstance(fid, list) and fid[0] is True else (fid if isinstance(fid, list) else [fid])
            dates = nn["date_array"][i]
            for j, one in enumerate(ids):
                F = 0.8 if which == "telecom" else {0: 0.8, 1: 0.78, 4: 0.72, 3: 0.67, 2: 0.62}[i]
                e = rng.random((2, n_shots)) < 0.1                    # electron flag 'up' = error-detection failure (10%)
                n = rng.random((2, n_shots)) < 0.5
                her = rng.random(n_shots) < 0.01; sg = rng.random(n_shots) < 0.5
                for s in np.where(her)[0]:
                    o = bell(F, s % 3, "p" if sg[s] else "m", gsn); n[0, s], n[1, s] = bool(o & 1), bool(o & 2)
                si = e ^ n                                             # authors' readout: nucleus = |e - si|
                lo, hi = rng.poisson(1.5, (2, n_shots)), rng.poisson(30, (2, n_shots))
                write(os.path.join(root, "data", "nucleus-nucleus entanglement", which), f"syn{which}", one,
                      {"electron-b16-": np.where(e[0], hi[0], lo[0]), "electron-g12-": np.where(e[1], hi[1], lo[1]),
                       "si29-b16-": np.where(si[0], hi[0], lo[0]), "si29-g12-": np.where(si[1], hi[1], lo[1]),
                       "onebin-apd1-middle-peak": (her & sg).astype(int), "onebin-apd2-middle-peak": (her & ~sg).astype(int)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root"); ap.add_argument("--synthetic"); ap.add_argument("--out", required=True)
    ap.add_argument("--stage", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    root = a.root
    if a.synthetic:
        make_synthetic(a.synthetic); root = a.synthetic
    lines = []
    def log(s): print(s, flush=True); lines.append(s)
    log(f"STUDY 37 ANALYSIS{'  ***SYNTHETIC DATA: NOT A RESULT***' if a.synthetic else ''}  ({time.strftime('%Y-%m-%d %H:%M:%S')})")
    for nb in (NB_EE, NB_NN):
        p = os.path.join(root, *nb); log(f"   notebook {nb[1]} sha256 {sha16(p)}")
    if os.environ.get("S37_TEST_SMALL"): log("   S37_TEST_SMALL set: reduced resamples/draws (testing only; not the pre-registered settings)")
    log(f"   analyze_37.py sha256 {sha16(__file__)}; cert.py sha256 {sha16(os.path.join(HERE, 'cert.py'))}")
    s1 = stage1(root, log)
    if os.environ.get("S37_TEST_FORCE_GATES"):            # synthetic testing only: exercise every Stage 2 code path
        s1.update(G1=True, G2=True, EE_published_run=s1["EE_published_run"] or 0)
        log("   S37_TEST_FORCE_GATES set: gates forced open (testing only; never for the real run)")
    if a.stage >= 2:
        if not s1["G0"]: log("Stage 2 not run: G0 failed (per-herald records do not reproduce the authors' counts)")
        else: stage2(root, s1, log)
    open(os.path.join(a.out, "analysis_37.txt"), "w").write("\n".join(lines) + "\n")
    json.dump(s1, open(os.path.join(a.out, "stage1_37.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
