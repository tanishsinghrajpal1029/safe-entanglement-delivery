"""Study 39: pre-registered test of the delivered-pair certificate on an Oxford Sr-Sr remote-entanglement run
(RID 565472, 200,000 heralded events; data provided by G. Araneda, University of Oxford; not redistributed).

New in this dataset: the measurement axis is drawn at random for every event, independently at each node, and
recorded, so the matched-axis events (XX, YY, ZZ) are a random, time-interleaved subset. This lets us test the
certificate's anytime property in time order (H4), which no earlier dataset allowed.

Usage
  python3 analyze_39.py --h5 <file.h5> --out <dir> --stage 1          # gates only
  python3 analyze_39.py --h5 <file.h5> --out <dir> --stage 2          # gates, then H2-H5 and descriptives
  python3 analyze_39.py --synthetic <file.h5> --out <dir> --stage 2   # writes and analyses synthetic data (testing)
"""
import argparse, hashlib, json, os, sys, time
import numpy as np
import h5py
from scipy.stats import beta, chi2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cert import Certifier  # noqa: E402  (Prop. C1, unchanged from study27_certification/cert.py)

ALPHA = 0.05; SEEDS = range(39001, 40001); PS = (0.05, 0.1, 0.2); N_CHECK = 20
BAND_SEED, BAND_DRAWS = 3900, 2000
if os.environ.get("S39_TEST_SMALL"):
    SEEDS, BAND_DRAWS = range(39001, 39101), 300
RID = 565472
PFX = f"datasets/ndscan.rid_{RID}.point."
AX = {0: "X", 1: "Y", 2: "X", 3: "Y", 4: "Z", 5: "Z"}       # basis code -> axis (guide); codes 2, 3, 5 are the negative orientation
NEG = {2, 3, 5}
# Target: Psi+ = (|01> + |10>)/sqrt2 in the authors' common frame: <XX> = <YY> = +1, <ZZ> = -1.
GOOD_PROD = {"X": +1, "Y": +1, "Z": -1}                    # outcome product of a matched-axis event with no error


def sha16(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
def cp_lo(k, n, a): return 0.0 if k == 0 else float(beta.ppf(a, k, n - k + 1))
def cp_up(k, n, a): return 1.0 if k >= n else float(beta.ppf(1 - a, k + 1, n - k))


def chi2_blocks(succ, tot):
    succ, tot = np.asarray(succ, float), np.asarray(tot, float)
    for _ in range(2):
        p = succ.sum() / tot.sum(); e1, e0 = tot * p, tot * (1 - p)
        if min(e1.min(), e0.min()) >= 5: break
        if len(succ) <= 5: return None
        succ, tot = succ.reshape(-1, 2).sum(1), tot.reshape(-1, 2).sum(1)
    else:
        return None
    p = succ.sum() / tot.sum(); e1, e0 = tot * p, tot * (1 - p)
    if min(e1.min(), e0.min()) < 5: return None
    x2 = (((succ - e1) ** 2) / e1 + (((tot - succ) - e0) ** 2) / e0).sum()
    return float(x2), len(succ) - 1, float(chi2.sf(x2, len(succ) - 1))


# ---------------------------------------------------------------- reading
def read(path):
    with h5py.File(path, "r") as f:
        g = lambda s: f[PFX + s][()]
        d = dict(bl=g("leader_generated_bases").reshape(-1).astype(int), bf=g("follower_generated_bases").reshape(-1).astype(int),
                 ol=g("leader_sr_brights").reshape(-1).astype(bool), of=g("follower_sr_brights").reshape(-1).astype(bool),
                 her=g("herald_pattern_idxs").reshape(-1).astype(int), t=g("leader_t_success_mus").reshape(-1).astype(np.int64),
                 tf=g("follower_t_success_mus").reshape(-1).astype(np.int64), tries=g("leader_tries_taken").reshape(-1).astype(np.int64),
                 aborts=g("protocol_aborts").reshape(-1).astype(np.int64))
        d["stored"] = dict(fid=[float(f[PFX + f"fidelity_{k}"][()]) for k in range(4)],
                           fid_psi_plus=float(f[PFX + "fidelity_to_psi_plus"][()]))
    return d


def eigen(d, conv):
    """Pauli eigenvalues (+1/-1) per node under a candidate convention.
    conv = (bright_sign_leader, bright_sign_follower, apply_negative_orientation_flip)."""
    sl, sf, flip = conv
    el = np.where(d["ol"], sl, -sl); ef = np.where(d["of"], sf, -sf)
    if flip:
        el = np.where(np.isin(d["bl"], list(NEG)), -el, el); ef = np.where(np.isin(d["bf"], list(NEG)), -ef, ef)
    return el, ef


def correlators(d, el, ef, mask=None):
    m = np.ones(len(el), bool) if mask is None else mask
    al = np.array([AX[b] for b in d["bl"]]); af = np.array([AX[b] for b in d["bf"]])
    out = {}
    for a in "XYZ":
        for b in "XYZ":
            s = m & (al == a) & (af == b); n = int(s.sum())
            out[a + b] = (float((el[s] * ef[s]).mean()) if n else np.nan, n)
    return out


def fid_psi_plus(c):                      # F(Psi+) = (1 + <XX> + <YY> - <ZZ>)/4
    return (1 + c["XX"][0] + c["YY"][0] - c["ZZ"][0]) / 4


def fid_phase_opt(c):                     # max over phi of F(Psi(phi)), Psi(phi) = (|01> + e^{i phi}|10>)/sqrt2
    a = c["XX"][0] + c["YY"][0]; b = c["XY"][0] - c["YX"][0]
    return (1 - c["ZZ"][0] + np.hypot(a, b)) / 4, float(np.arctan2(b, a))


# ---------------------------------------------------------------- Stage 1
def stage1(d, log):
    log("== Stage 1 (gates)")
    n = len(d["bl"]); s1 = dict(G1=True, G2=False)
    for name, b in (("leader", d["bl"]), ("follower", d["bf"])):
        fr = np.bincount(b, minlength=6) / n
        exp = np.array([1 / 6, 1 / 6, 1 / 6, 1 / 6, 1 / 3, 0]); sd = np.sqrt(exp * (1 - exp) / n)
        ok = bool(np.all(np.abs(fr - exp) <= 5 * np.maximum(sd, 1e-12)) and set(np.unique(b)) <= {0, 1, 2, 3, 4})
        s1["G1"] &= ok
        log(f"   {name} basis-code frequencies {np.round(fr, 4).tolist()} -> {'OK' if ok else 'NOT as described'}")
    dep = np.mean(d["bl"] == d["bf"]); log(f"   fraction of events with identical codes at both nodes: {dep:.4f} (independent choice predicts {4 / 36 + 1 / 9:.4f})")
    her_ok = set(np.unique(d["her"])) <= {0, 1, 2, 3}; s1["G1"] &= bool(her_ok)
    mono = bool(np.all(np.diff(d["t"]) > 0)); off = np.unique(d["tf"] - d["t"]).size == 1
    s1["G1"] &= mono
    log(f"   events {n}; herald patterns in 0-3: {her_ok}; timestamps strictly increasing: {mono}; constant leader-follower offset: {off}; "
        f"events with protocol_aborts > 0: {int((d['aborts'] > 0).sum())}")
    log(f"G1 (design as described): {'PASS' if s1['G1'] else 'FAIL'}")
    # G2: conventions
    cands = [(sl, sf, fl) for sl in (1, -1) for sf in (1, -1) for fl in (True, False)]
    st = d["stored"]; passing = []
    for cv in cands:
        el, ef = eigen(d, cv)
        fk = [float(fid_phase_opt(correlators(d, el, ef, d["her"] == k))[0]) for k in range(4)]
        fp = float(fid_psi_plus(correlators(d, el, ef)))
        ok = all(abs(fk[k] - st["fid"][k]) <= 0.01 for k in range(4)) and abs(fp - st["fid_psi_plus"]) <= 0.01
        log(f"   convention bright->({cv[0]:+d},{cv[1]:+d}), negative-orientation flip {cv[2]}: per-pattern phase-optimised F "
            f"{[round(x, 4) for x in fk]}, F(Psi+) {fp:.4f} -> {'MATCH' if ok else 'no'}")
        if ok: passing.append(cv)
    # the two global bright mappings are equivalent for correlators; count distinct physics
    distinct = {(cv[0] * cv[1], cv[2]) for cv in passing}
    s1["G2"] = len(distinct) == 1; s1["conv"] = passing[0] if passing else None
    log(f"   stored: per-pattern fidelity {[round(x, 4) for x in st['fid']]}, fidelity_to_psi_plus {st['fid_psi_plus']:.4f}")
    log(f"G2 (exactly one convention reproduces the stored fidelities within 0.01): {'PASS' if s1['G2'] else 'FAIL'}")
    return s1


# ---------------------------------------------------------------- Stage 2
def matched(d, el, ef):
    al = np.array([AX[b] for b in d["bl"]]); af = np.array([AX[b] for b in d["bf"]])
    m = al == af
    idx = np.flatnonzero(m)                                           # time order = array order
    ax = al[m]; err = np.array([0 if (el[i] * ef[i]) == GOOD_PROD[a] else 1 for i, a in zip(idx, ax)])
    bas = np.array(["XYZ".index(a) for a in ax])
    return idx, err, bas


def U_ref(err, bas, sel, level):
    return 1 - sum(cp_lo(int(err[sel & (bas == k)].sum()), int((sel & (bas == k)).sum()), level) for k in range(3)) / 2


def certificate_draws(err, bas):
    N = len(err); checks = np.linspace(N / N_CHECK, N, N_CHECK).astype(int)
    out = {}
    for p in PS:
        C = Certifier(p, ALPHA); finals = []; v_final = 0; v_any = 0; ab08 = ab09 = 0; first08 = []
        for sd in SEEDS:
            T = np.random.default_rng(sd).random(N) < p
            K = int((~T).sum()); E = int(err[T].sum()); L = C.lower(E, K); finals.append(L)
            U = U_ref(err, bas, ~T, 0.025 / 3); v_final += L > U; ab08 += L > 0.8; ab09 += L > 0.9
            bad = False; f08 = None
            for c in checks:                                          # anytime check in time order (H4)
                Tc = T[:c]; Kc = int((~Tc).sum()); Lc = C.lower(int(err[:c][Tc].sum()), Kc)
                if Lc > U_ref(err[:c], bas[:c], ~Tc, 0.025 / 3 / N_CHECK): bad = True
                if f08 is None and Lc > 0.8: f08 = c
            v_any += bad; first08.append(f08 if f08 is not None else np.nan)
        n = len(finals)
        out[p] = dict(n=n, viol=int(v_final), viol_lo=cp_lo(int(v_final), n, ALPHA), viol_any=int(v_any), viol_any_lo=cp_lo(int(v_any), n, ALPHA),
                      median=float(np.median(finals)), above08=ab08 / n, above09=ab09 / n, N=N,
                      first08_median=float(np.nanmedian(first08)) if np.any(np.isfinite(first08)) else None)
    return out


def predicted_band(F, N, p):
    e = 2 * (1 - F) / 3; C = Certifier(p, ALPHA); rng = np.random.default_rng(BAND_SEED)
    T = rng.binomial(N, p, BAND_DRAWS); E = rng.binomial(T, e)
    return [float(x) for x in np.quantile([C.lower(int(a), int(N - t)) for a, t in zip(E, T)], [0.1, 0.5, 0.9])]


def stage2(d, s1, log):
    log("\n== Stage 2")
    el, ef = eigen(d, s1["conv"]); idx, err, bas = matched(d, el, ef)
    log(f"   matched-axis events (XX, YY, ZZ): {len(idx)} of {len(el)}")
    # H2 drift
    tests = []
    bl = np.array_split(np.arange(len(el)), 10)
    if np.all(d["tries"] >= 1):
        tests.append(("success per attempt", chi2_blocks([len(b) for b in bl], [d["tries"][b].sum() for b in bl])))
    else:
        tests.append(("success per attempt", None))
    for k in range(3):
        z = np.flatnonzero(bas == k)
        if len(z) >= 20:
            bb = np.array_split(z, 10); tests.append((f"{'XYZ'[k]}{'XYZ'[k]} error", chi2_blocks([err[b].sum() for b in bb], [len(b) for b in bb])))
        else:
            tests.append((f"{'XYZ'[k]}{'XYZ'[k]} error", None))
    for k in range(4):
        tests.append((f"herald pattern {k} share", chi2_blocks([(d["her"][b] == k).sum() for b in bl], [len(b) for b in bl])))
    valid = [(n, r) for n, r in tests if r is not None]; m = len(valid)
    log(f"H2 drift within the run: {m} valid tests (Bonferroni x{m}); predictions: success per attempt DETECTED, error rates NOT detected")
    for n, r in tests:
        log(f"   {n}: " + ("NA" if r is None else f"chi2 {r[0]:.1f}, df {r[1]}, p {r[2]:.2g}, Bonferroni {min(1, r[2] * m):.2g} -> "
                            f"{'detected' if r[2] * m < 0.05 else 'not detected'}"))
    # H3, H4, H5
    o = certificate_draws(err, bas)
    fail3 = fail4 = False
    for p in PS:
        r = o[p]; fail3 |= r["viol_lo"] > 0.05; fail4 |= r["viol_any_lo"] > 0.05
        log(f"H3/H4 p={p}: matched events {r['N']}; final violations {r['viol']}/{r['n']} (CP95 lower {r['viol_lo']:.3f}); "
            f"any-checkpoint violations {r['viol_any']}/{r['n']} (CP95 lower {r['viol_any_lo']:.3f}); median certificate {r['median']:.4f}; "
            f"> 0.8 in {r['above08']:.0%}, > 0.9 in {r['above09']:.0%}; median matched events before first checkpoint above 0.8: {r['first08_median']}")
    log(f"H3 (final certificate never above a conservative bound; prediction PASS): {'FAIL' if fail3 else 'PASS'}")
    log(f"H4 (anytime: never above the bound at any of {N_CHECK} checkpoints in time order; prediction PASS): {'FAIL' if fail4 else 'PASS'}")
    Fst = d["stored"]["fid_psi_plus"]
    for p in PS:
        lo, med, hi = predicted_band(Fst, o[p]["N"], p); got = o[p]["median"]
        log(f"H5{'' if p == 0.2 else ' (secondary)'} p={p}: median certificate {got:.4f}; predicted {med:.4f} [10-90%: {lo:.4f}, {hi:.4f}] "
            f"from stored F(Psi+) {Fst:.4f} -> {'PASS (inside band)' if lo <= got <= hi else 'FAIL (outside band)'}")
    # Descriptive
    log("\n== Descriptive")
    c = correlators(d, el, ef); Fp = fid_psi_plus(c); Fo, ph = fid_phase_opt(c)
    log(f"D1 pooled: F(Psi+) {Fp:.4f}; phase-optimised F {Fo:.4f} at phi = {ph:+.3f} rad; correlators " +
        ", ".join(f"{k} {v[0]:+.3f} (n={v[1]})" for k, v in c.items()))
    for k in range(4):
        ck = correlators(d, el, ef, d["her"] == k); fo, pk = fid_phase_opt(ck)
        log(f"D1 herald pattern {k}: events {int((d['her'] == k).sum())}; F(Psi+) {fid_psi_plus(ck):.4f}; phase-optimised {fo:.4f} at {pk:+.3f} rad")
    for i, b in enumerate(bl):
        mk = np.zeros(len(el), bool); mk[b] = True; cb = correlators(d, el, ef, mk); fo, pb = fid_phase_opt(cb)
        log(f"D2 block {i}: F(Psi+) {fid_psi_plus(cb):.4f}; phase-optimised {fo:.4f}; phi {pb:+.3f} rad")
    # calibrate-then-certify (descriptive): phase from the first 10% of events, fidelity to Psi(phi_cal) on the rest
    cal = np.zeros(len(el), bool); cal[: len(el) // 10] = True
    _, phc = fid_phase_opt(correlators(d, el, ef, cal)); cr = correlators(d, el, ef, ~cal)
    Fcal = (1 - cr["ZZ"][0] + np.cos(phc) * (cr["XX"][0] + cr["YY"][0]) + np.sin(phc) * (cr["XY"][0] - cr["YX"][0])) / 4
    log(f"D3 phase calibrated on the first 10% (phi = {phc:+.3f} rad): fidelity of the remaining events to Psi(phi_cal) {Fcal:.4f}")


# ---------------------------------------------------------------- synthetic data (testing only)
def make_synthetic(path, n=200000, seed=11, phi=0.25, F0=0.965):
    rng = np.random.default_rng(seed)
    codes = np.array([0, 1, 2, 3, 4]); pr = np.array([1, 1, 1, 1, 2]) / 6
    bl, bf = rng.choice(codes, n, p=pr), rng.choice(codes, n, p=pr)
    her = rng.integers(0, 4, n)
    # Werner-like mixture of Psi(phi) with white noise: sample correlated eigenvalues per axis pair
    w = (4 * F0 - 1) / 3
    al = np.array([AX[b] for b in bl]); af = np.array([AX[b] for b in bf])
    E = {("X", "X"): np.cos(phi), ("Y", "Y"): np.cos(phi), ("Z", "Z"): -1.0, ("X", "Y"): np.sin(phi), ("Y", "X"): -np.sin(phi)}
    corr = np.array([w * E.get((a, b), 0.0) for a, b in zip(al, af)])
    el = rng.choice([1, -1], n); ef = np.where(rng.random(n) < (1 + corr) / 2, el, -el)
    rl = np.where(np.isin(bl, list(NEG)), -el, el); rf = np.where(np.isin(bf, list(NEG)), -ef, ef)   # recorded orientation
    t = np.cumsum(rng.integers(500, 5000, n)).astype(np.int64)
    with h5py.File(path, "w") as f:
        def put(s, v): f.create_dataset(PFX + s, data=v)
        put("leader_generated_bases", bl.astype(np.int8)); put("follower_generated_bases", bf.astype(np.int8))
        put("leader_sr_brights", (rl == 1).reshape(-1, 1)); put("follower_sr_brights", (rf == 1).reshape(-1, 1))
        put("herald_pattern_idxs", her.reshape(-1, 1).astype(np.int32)); put("leader_t_success_mus", t.reshape(-1, 1))
        put("follower_t_success_mus", (t + 123456789).reshape(-1, 1)); put("leader_tries_taken", rng.geometric(0.02, (n, 1)).astype(np.int32))
        put("protocol_aborts", np.zeros((n, 1), np.int32))
        Fk = (1 + w * 3) / 4
        for k in range(4): put(f"fidelity_{k}", Fk)
        put("fidelity_to_psi_plus", (1 + w * (2 * np.cos(phi) + 1)) / 4)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--h5"); ap.add_argument("--synthetic"); ap.add_argument("--out", required=True)
    ap.add_argument("--stage", type=int, default=2); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    path = a.h5
    if a.synthetic: make_synthetic(a.synthetic); path = a.synthetic
    lines = []
    def log(s): print(s, flush=True); lines.append(s)
    log(f"STUDY 39 ANALYSIS{'  ***SYNTHETIC DATA: NOT A RESULT***' if a.synthetic else ''}  ({time.strftime('%Y-%m-%d %H:%M:%S')})")
    log(f"   data file sha256 {sha16(path)}; analyze_39.py sha256 {sha16(__file__)}; cert.py sha256 {sha16(os.path.join(HERE, 'cert.py'))}")
    if os.environ.get("S39_TEST_SMALL"): log("   S39_TEST_SMALL set: reduced draws (testing only; not the pre-registered settings)")
    d = read(path); s1 = stage1(d, log)
    if a.stage >= 2:
        if not (s1["G1"] and s1["G2"]): log("Stage 2 not run: a gate failed")
        else: stage2(d, s1, log)
    open(os.path.join(a.out, "analysis_39.txt"), "w").write("\n".join(lines) + "\n")
    json.dump({k: v for k, v in s1.items()}, open(os.path.join(a.out, "stage1_39.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
