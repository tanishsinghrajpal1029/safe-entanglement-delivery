"""Study 38: pre-registered test of the delivered-pair certificate on IonQ's public kHz ion-SiV data
(Hartung, Barral, ... Robens, Levonian, arXiv 2610.10705; data: github.com/ionq-publications/khz-heterogeneous-entanglement,
Apache-2.0, commit 8a08f695fca8aff540e85cd8a14b25b25927e82f).

The authors' own functions (their src/analysis, src/papertools) are imported from their repository for the gates;
our own parser reads the same HDF5 files for the tests (PREREG_38.md).

Usage
  python3 analyze_38.py --ionq <path>/IonQData --out <dir> --stage 1        # gates only
  python3 analyze_38.py --ionq <path>/IonQData --out <dir> --stage 2        # gates, then H2, H3, H5, descriptives
  python3 analyze_38.py --synthetic <empty dir> --out <dir> --stage 2       # same pipeline on synthetic data (testing)
"""
import argparse, hashlib, json, os, shutil, sys, time
import numpy as np
import h5py
from scipy.stats import beta, chi2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cert import Certifier  # noqa: E402  (the paper's Prop. C1 certificate, unchanged from study27_certification/cert.py)

ALPHA = 0.05; SEEDS = range(38001, 39001); PS = (0.1, 0.2, 0.5); PRIMARY_PS = (0.1, 0.2)
BAND_SEED, BAND_DRAWS = 3800, 2000
if os.environ.get("S38_TEST_SMALL"):                     # synthetic testing only (never for the real run)
    SEEDS, BAND_DRAWS = range(38001, 38101), 300
IONQ_COMMIT = "8a08f695fca8aff540e85cd8a14b25b25927e82f"
MAIN = 64563                                             # Fig. 1 full tomography (run_ids.ION_SIV_FULL_TOMOGRAPHY_FIGURE_1)
FIG2 = [69967, 69963, 69977, 69969, 69971, 69974]        # Fig. 2 trade-off runs: XY8-1, -2, -3, -4, -8, -16 (run_ids.RATE_FIDELITY_TRADEOFF)
XY8 = dict(zip(FIG2, (1, 2, 3, 4, 8, 16)))
PUB_F, PUB_F_SD = 0.879, 0.007                           # arXiv 2610.10705: F = 87.9(7) % to Phi+ (MLE)
PUB_RATE, PUB_RATE_SD = 1.032, 0.011                     # kHz, Fig. 1
BELL = ("XX", "YY", "ZZ")
# outcome o = ion_bit + 2*siv_bit, bit 1 = eigenvalue -1 (authors' convention); Phi+ has <XX> = <ZZ> = +1, <YY> = -1
GOOD = {"XX": {0, 3}, "YY": {1, 2}, "ZZ": {0, 3}}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
def cp_lo(k, n, a): return 0.0 if k == 0 else float(beta.ppf(a, k, n - k + 1))
def cp_up(k, n, a): return 1.0 if k >= n else float(beta.ppf(1 - a, k + 1, n - k))


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


# ---------------------------------------------------------------- our own parser
def read_run(root, rid):
    """Per-herald records in time order: (t_start, setting, outcome or -1 if missing, attempts)."""
    d = os.path.join(root, "data", "runs", str(rid))
    with h5py.File(os.path.join(d, "main.h5"), "r") as f:
        lab = [x.decode() if isinstance(x, bytes) else str(x) for x in f["correlator"][()]]
        ion, siv = f["ion_state"][()], f["siv_final_readout_state"][()]
        att = f["nof_attempts_this_success"][()]
    with h5py.File(os.path.join(d, "rate.h5"), "r") as f:
        lab_r = [x.decode() if isinstance(x, bytes) else str(x) for x in f["correlator"][()]]
        t0, t1 = f["repetition_start_timestamp"][()], f["readout_timestamp"][()]
    assert lab == lab_r, f"run {rid}: correlator order differs between main.h5 and rate.h5"
    rec = []
    for i, s in enumerate(lab):
        for j in range(ion.shape[1]):
            ok = np.isfinite(ion[i, j]) and np.isfinite(siv[i, j])
            o = int((ion[i, j] == 1) + 2 * (siv[i, j] == 1)) if ok else -1
            rec.append((float(t0[i, j]), s, o, float(att[i, j])))
    rec.sort(key=lambda r: r[0])
    return rec, lab, float(1 / np.mean(t1 - t0)) / 1000      # authors' rate definition (Fig. 1 notebook), kHz


def counts(rec):
    c = {}
    for _, s, o, _ in rec:
        if o >= 0: c.setdefault(s, np.zeros(4, int))[o] += 1
    return c


def lin_fid(c):
    """F(Phi+) = (1 + <XX> - <YY> + <ZZ>)/4 = 1 - (eX + eY + eZ)/2."""
    e = {s: 1 - sum(c[s][k] for k in GOOD[s]) / c[s].sum() for s in BELL}
    return 1 - sum(e.values()) / 2, e


# ---------------------------------------------------------------- the authors' pipeline (gates only)
def authors(root, rid, mle=False):
    sys.path.insert(0, os.path.join(root, "src"))
    from analysis.tomography import make_two_qubit_state, calculate_histogram_population_and_correlator
    from papertools import load_dataset
    np.random.seed(list(b"IonQ-R&D"))                    # as in their Fig. 1 notebook
    ds = load_dataset(rid, "main.h5")
    st = make_two_qubit_state(state_1=ds["ion_state"], state_1_high_value=1, state_2=ds["siv_final_readout_state"],
                              state_2_high_value=1, name="ion_siv", label="Ion-SiV")
    hist, _, corr = calculate_histogram_population_and_correlator(st, label="Ion-SiV", prefix="ion_siv", rep_dim="success_idx")
    h = {hist.correlator[i].item(): hist[i].values.astype(int) for i in range(hist.correlator.size)}
    m = corr["ion_siv_corr_mean"]
    f_lin = float((1 + m.sel(correlator="XX") - m.sel(correlator="YY") + m.sel(correlator="ZZ")).item() / 4)   # their Fig. 2 formula
    f_mle = None
    if mle:
        from analysis import density_matrix_mle
        tomo = {hist.correlator[i].item(): {f"{s & 0b01}{(s & 0b10) >> 1}": hist[i, s].item() for s in range(4)}
                for i in range(hist.correlator.size)}
        r = density_matrix_mle.reconstruct_density_matrix(tomo, num_bootstrap_samples=1000)
        f_mle = (float(r.fidelity), float(r.fidelity_error))
    ds.close()
    return h, f_lin, f_mle


def stage1(root, log):
    log("== Stage 1 (gates)")
    s1 = dict(G0=True, G1=False, runs={})
    for rid in [MAIN] + FIG2:
        rec, lab, rate = read_run(root, rid); c = counts(rec)
        h, f_lin_auth, f_mle = authors(root, rid, mle=(rid == MAIN))
        same = set(c) == set(h) and all(np.array_equal(c[s], h[s]) for s in h)
        f_lin, _ = lin_fid(c)
        nb = sum(c[s].sum() for s in BELL); miss = sum(1 for r in rec if r[2] < 0)
        g0 = same and abs(f_lin - f_lin_auth) < 1e-9 and nb > 0
        s1["G0"] &= g0
        s1["runs"][rid] = dict(n_bell=int(nb), missing=miss, f_lin=f_lin, rate_khz=rate)
        tag = "Fig. 1" if rid == MAIN else f"Fig. 2, XY8-{XY8[rid]}"
        log(f"   run {rid} ({tag}): heralds {len(rec)} (missing outcome {miss}); XX/YY/ZZ heralds {nb}; "
            f"G0 counts = authors': {same}; F_lin ours {f_lin:.4f} vs authors' formula {f_lin_auth:.4f}; rate {rate:.3f} kHz")
        if rid == MAIN:
            zf = abs(f_mle[0] - PUB_F) / PUB_F_SD; zr = abs(rate - PUB_RATE) / PUB_RATE_SD
            s1["G1"] = bool(zf <= 2 and zr <= 2); s1["f_mle"] = f_mle
            log(f"   run {MAIN} MLE (authors' code): F = {f_mle[0]:.4f} +/- {f_mle[1]:.4f} (published {PUB_F}({PUB_F_SD})), "
                f"z = {zf:.2f}; rate {rate:.3f} kHz (published {PUB_RATE}({PUB_RATE_SD})), z = {zr:.2f}")
    log(f"G0 (our parser reproduces the authors' counts and Fig. 2 fidelity formula, all 7 runs): {'PASS' if s1['G0'] else 'FAIL'}")
    log(f"G1 (Fig. 1 fidelity and rate reproduced, within 2 s.d.): {'PASS' if s1['G1'] else 'FAIL'}")
    return s1


# ---------------------------------------------------------------- Stage 2
def h2_tests(rid, rec):
    out = []
    att = np.array([r[3] for r in rec])
    if np.all(np.isfinite(att)) and np.all(att >= 1):
        bl = np.array_split(np.arange(len(rec)), 10)
        out.append((f"run {rid} success per attempt", chi2_blocks([len(b) for b in bl], [att[b].sum() for b in bl])))
    else:
        out.append((f"run {rid} success per attempt", None))
    for s in BELL:
        z = [r for r in rec if r[1] == s and r[2] >= 0]
        if len(z) >= 20:
            bl = np.array_split(np.arange(len(z)), 10)
            out.append((f"run {rid} {s} error", chi2_blocks([sum(1 for j in b if z[j][2] not in GOOD[s]) for b in bl], [len(b) for b in bl])))
        else:
            out.append((f"run {rid} {s} error", None))
    return out


def certificate_draws(rec):
    r = [x for x in rec if x[1] in BELL and x[2] >= 0]
    err = np.array([0 if x[2] in GOOD[x[1]] else 1 for x in r]); bas = np.array([BELL.index(x[1]) for x in r])
    out = {}
    for p in PS:
        cert = Certifier(p, ALPHA); viol = 0; ab05 = ab08 = 0; finals = []
        for sd in SEEDS:
            T = np.random.default_rng(sd).random(len(r)) < p
            K = int((~T).sum()); E = int(err[T].sum())
            if K == 0: continue
            L = cert.lower(E, K); finals.append(L)
            U = 1 - sum(cp_lo(int(err[~T & (bas == k)].sum()), int((~T & (bas == k)).sum()), 0.025 / 3) for k in range(3)) / 2
            viol += L > U; ab05 += L > 0.5; ab08 += L > 0.8
        n = len(finals)
        out[p] = dict(n=n, viol=int(viol), viol_lo=cp_lo(int(viol), n, ALPHA), viol_up=cp_up(int(viol), n, ALPHA),
                      above05=ab05 / max(n, 1), above08=ab08 / max(n, 1), median=float(np.median(finals)), N=len(r))
    return out


def predicted_band(N, p):
    """H5 band: synthetic 10-90% quantiles of the final certificate at the published F, this N and p (seed 3800)."""
    e = 2 * (1 - PUB_F) / 3; C = Certifier(p, ALPHA); rng = np.random.default_rng(BAND_SEED)
    T = rng.binomial(N, p, BAND_DRAWS); E = rng.binomial(T, e)
    L = np.array([C.lower(int(a), int(N - t)) for a, t in zip(E, T)])
    return [float(x) for x in np.quantile(L, [0.1, 0.5, 0.9])]


def stage2(root, s1, log):
    log("\n== Stage 2")
    recs = {rid: read_run(root, rid)[0] for rid in [MAIN] + FIG2}
    # H2
    tests = []
    for rid in recs: tests += h2_tests(rid, recs[rid])
    valid = [(n, r) for n, r in tests if r is not None]; m = len(valid)
    log(f"H2 drift within a run (prediction: NOT detected): {m} valid tests (Bonferroni x{m})")
    for n, r in tests:
        log(f"   {n}: " + ("too few counts (NA)" if r is None else f"chi2 {r[0]:.1f}, df {r[1]}, p {r[2]:.2g}"))
    pmin = min((r[2] for _, r in valid), default=1.0)
    det = pmin * m < 0.05
    log(f"   min p x {m} = {min(1, pmin * m):.2g} -> {'drift DETECTED (prediction failed)' if det else 'not detected (prediction held)'}")
    # H3 and H5
    viol_fail = False; res = {}
    for rid in recs:
        if rid == MAIN and not s1["G1"]:
            log(f"H3/H5 run {MAIN} not run: gate G1 failed"); continue
        o = certificate_draws(recs[rid]); res[rid] = o
        tag = "Fig. 1" if rid == MAIN else f"XY8-{XY8[rid]}"
        for p in PS:
            d = o[p]; prim = p in PRIMARY_PS
            if prim and d["viol_lo"] > 0.05: viol_fail = True
            log(f"H3 run {rid} ({tag}), p={p}{'' if prim else ' (secondary)'}: XX/YY/ZZ heralds {d['N']}; violating draws {d['viol']}/{d['n']} "
                f"(CP95 lower {d['viol_lo']:.3f}) -> {'FAIL' if d['viol_lo'] > 0.05 else 'PASS'}; median certificate {d['median']:.3f}; "
                f"> 0.5 in {d['above05']:.0%}, > 0.8 in {d['above08']:.0%}")
    log(f"H3 overall (primary cells: 7 runs x p in {PRIMARY_PS}): {'FAIL (certificate falsified)' if viol_fail else 'PASS'}")
    if MAIN in res:
        for p in PS:
            lo, med, hi = predicted_band(res[MAIN][p]["N"], p); got = res[MAIN][p]["median"]
            ok = lo <= got <= hi
            log(f"H5{'' if p == 0.2 else ' (secondary)'} run {MAIN}, p={p}: median certificate {got:.3f}; predicted {med:.3f} "
                f"[10-90%: {lo:.3f}, {hi:.3f}] -> {'PASS (inside band)' if ok else 'FAIL (outside band)'}")
    log("\n== Descriptive")
    for rid in recs:
        r = s1["runs"][rid]; c = counts(recs[rid]); _, e = lin_fid(c)
        tag = "Fig. 1" if rid == MAIN else f"XY8-{XY8[rid]}"
        log(f"D1 run {rid} ({tag}): F_lin {r['f_lin']:.4f}; e_XX {e['XX']:.4f}, e_YY {e['YY']:.4f}, e_ZZ {e['ZZ']:.4f}; "
            f"rate {r['rate_khz']:.3f} kHz; XX/YY/ZZ heralds {r['n_bell']}")
    if s1.get("f_mle"): log(f"D1 run {MAIN} MLE fidelity {s1['f_mle'][0]:.4f} +/- {s1['f_mle'][1]:.4f}")


# ---------------------------------------------------------------- synthetic data in the same layout (testing only)
def make_synthetic(out, seed=7):
    import xarray as xr
    src = os.environ["S38_IONQ_SRC"]                       # a copy of the authors' src/ (not redistributed)
    shutil.copytree(src, os.path.join(out, "src"), dirs_exist_ok=True)
    rng = np.random.default_rng(seed); labs = ["XX", "YY", "ZZ", "XY", "XZ", "YX", "YZ", "ZX", "ZY"]
    for k, rid in enumerate([MAIN] + FIG2):
        F = 0.88 - 0.01 * k; e = 2 * (1 - F) / 3; d = os.path.join(out, "data", "runs", str(rid)); os.makedirs(d, exist_ok=True)
        ion = rng.integers(0, 2, (9, 1000)).astype(float); siv = ion.copy()
        for i, s in enumerate(labs):
            if s in BELL:
                want_par = 0 if s != "YY" else 1                                   # Phi+: even parity in XX, ZZ; odd in YY
                flip = rng.random(1000) < e
                siv[i] = np.where(flip, 1 - ((ion[i] + want_par) % 2), (ion[i] + want_par) % 2)
            else:
                siv[i] = rng.integers(0, 2, 1000)
        ion[rng.random((9, 1000)) < 0.002] = np.nan
        att = rng.geometric(0.05, (9, 1000)).astype(float)
        dt = rng.exponential(1e-3, (9, 1000)); start = np.cumsum(dt + 2e-4).reshape(9, 1000)
        coords = dict(correlator=("correlator", np.array(labs, dtype=object)), success_idx=("success_idx", np.arange(1000)))
        dims = ("correlator", "success_idx")
        xr.Dataset({"ion_state": (dims, ion), "siv_final_readout_state": (dims, siv), "nof_attempts_this_success": (dims, att)},
                   coords=coords).to_netcdf(os.path.join(d, "main.h5"), engine="h5netcdf")
        xr.Dataset({"repetition_start_timestamp": (dims, start), "readout_timestamp": (dims, start + dt)},
                   coords=coords).to_netcdf(os.path.join(d, "rate.h5"), engine="h5netcdf")
        json.dump({"id": rid, "created_at": "synthetic", "metadata": {}}, open(os.path.join(d, "provenance.json"), "w"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ionq"); ap.add_argument("--synthetic"); ap.add_argument("--out", required=True)
    ap.add_argument("--stage", type=int, default=2)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    root = a.ionq
    if a.synthetic:
        make_synthetic(a.synthetic); root = a.synthetic
    lines = []
    def log(s): print(s, flush=True); lines.append(s)
    log(f"STUDY 38 ANALYSIS{'  ***SYNTHETIC DATA: NOT A RESULT***' if a.synthetic else ''}  ({time.strftime('%Y-%m-%d %H:%M:%S')})")
    if not a.synthetic:
        head = os.popen(f"git -C '{root}' rev-parse HEAD 2>/dev/null").read().strip()
        dirty = os.popen(f"git -C '{root}' status --porcelain --untracked-files=no 2>/dev/null").read().strip()
        log(f"   IonQ repository commit {head or 'UNKNOWN'} (registered {IONQ_COMMIT[:12]}); tracked files modified: {'YES' if dirty else 'no'}")
        if head != IONQ_COMMIT or dirty:
            log("STOP: the IonQ repository is not at the registered commit, or its tracked files were modified."); sys.exit(2)
    if os.environ.get("S38_TEST_SMALL"): log("   S38_TEST_SMALL set: reduced draws (testing only; not the pre-registered settings)")
    log(f"   analyze_38.py sha256 {sha16(__file__)}; cert.py sha256 {sha16(os.path.join(HERE, 'cert.py'))}")
    s1 = stage1(root, log)
    if os.environ.get("S38_TEST_FORCE_GATES"):
        s1.update(G1=True); log("   S38_TEST_FORCE_GATES set: gate G1 forced open (testing only; never for the real run)")
    if a.stage >= 2:
        if not s1["G0"]: log("Stage 2 not run: G0 failed")
        else: stage2(root, s1, log)
    open(os.path.join(a.out, "analysis_38.txt"), "w").write("\n".join(lines) + "\n")
    json.dump(s1, open(os.path.join(a.out, "stage1_38.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
