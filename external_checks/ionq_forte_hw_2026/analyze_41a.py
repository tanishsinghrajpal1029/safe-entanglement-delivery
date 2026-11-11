"""Study 41a analysis: the certificate on IonQ Forte 1 hardware, settings fixed in advance (Blocks A and B).

Usage:  python analyze_41a.py --raw RAW_DIR --stage 1      (gates)
        python analyze_41a.py --raw RAW_DIR --stage 2      (hypotheses; runs only if Stage 1 passed)
RAW_DIR holds the downloaded job files (s41a_job_XX.json; browser duplicates such as "s41a_job_03 (1).json" are allowed).
Needs numpy, scipy and the files job_41a.py and cert.py next to this script. Qiskit is NOT needed.
"""
import argparse, glob, hashlib, json, os, sys, types, uuid, datetime
import numpy as np
from scipy.stats import beta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cert import Certifier                                                         # unchanged since Study 27

N_JOBS, N_PAIRS, SHOTS = 30, 18, 1000
PS = (0.05, 0.1, 0.2)
ALPHA = 0.05
TEST_SMALL = os.environ.get("S41A_TEST_SMALL") == "1"                             # synthetic tests only; never set for the real run
SEEDS = range(51001, 51101) if TEST_SMALL else range(51001, 52001)              # 1,000 test-or-keep draws per p
OUT = os.path.join(HERE, "out")


def sha16(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
def cp_lo(k, n, a): return np.where(k == 0, 0.0, beta.ppf(a, np.maximum(k, 1), n - k + 1))


def load_job_script():
    """Executes job_41a.py (the script that ran on Qollab) to reuse its TABLE, B_JOBS and THETA."""
    path = os.path.join(HERE, "job_41a.py")
    try:
        import qiskit  # noqa: F401
    except ImportError:
        stub = types.ModuleType("qiskit"); stub.QuantumCircuit = None; sys.modules["qiskit"] = stub
    ns = {"__name__": "job_41a"}
    exec(compile(open(path).read(), path, "exec"), ns)
    return ns, sha16(path)


def expected_ops(axes, pairs, faulty, theta):
    """Gate list that circuit() in job_41a.py builds for this design (no Qiskit needed)."""
    ops = []
    for k, (ax, (a, b)) in enumerate(zip(axes, pairs)):
        ops += [("h", None, (a,)), ("cx", None, (a, b))]
        if k in faulty: ops.append(("rz", faulty[k] * theta, (a,)))
        for q in (a, b):
            if ax == "X": ops.append(("h", None, (q,)))
            if ax == "Y": ops += [("sdg", None, (q,)), ("h", None, (q,))]
    ops += [("measure", None, (q, q)) for q in range(2 * len(pairs))]
    return ops


def parse_qasm(text):
    """Gate list from the OpenQASM 2 text that Qollab submitted (recorded in the job file)."""
    import re
    ops = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(("OPENQASM", "include", "qreg", "creg", "//", "barrier")): continue
        m = re.fullmatch(r"measure q\[(\d+)\]\s*->\s*c\[(\d+)\];", line)
        if m: ops.append(("measure", None, (int(m[1]), int(m[2])))); continue
        m = re.fullmatch(r"(\w+)(?:\(([^)]*)\))?\s+(.+);", line)
        if not m: ops.append(("?", None, (line,))); continue
        par = None if m[2] is None else float(eval(m[2], {"__builtins__": {}}, {"pi": np.pi}))
        qs = tuple(int(x) for x in re.findall(r"q\[(\d+)\]", m[3]))
        ops.append((m[1], par, qs))
    return ops


def same_ops(a, b):
    return len(a) == len(b) and all(x[0] == y[0] and x[2] == y[2] and (x[1] is None) == (y[1] is None)
                                    and (x[1] is None or abs(x[1] - y[1]) < 1e-9) for x, y in zip(a, b))


def uuid7_time(job_id):
    try:
        u = uuid.UUID(str(job_id))
    except (ValueError, AttributeError, TypeError):
        return None
    return int(u.hex[:12], 16) / 1000.0 if u.version == 7 else None


def read_raw(raw):
    """All job files; simulator rehearsals, failed or malformed files are set aside (logged), never chosen."""
    rows, aside = [], []
    for f in sorted(glob.glob(os.path.join(raw, "*.json"))):
        name = os.path.basename(f)
        try:
            d = json.load(open(f))
        except Exception as e:
            aside.append(f"{name}: unreadable ({type(e).__name__})"); continue
        d["_file"] = name; d["_t"] = uuid7_time(d.get("job_id"))
        why = [w for w, bad in (("not study 41a", d.get("study") != "41a"), ("not hardware mode", d.get("mode") != "hardware"),
                                ("no counts", "counts_hex" not in d), ("job id not UUIDv7", d["_t"] is None),
                                ("job number not an integer in 0-29", not (isinstance(d.get("job"), int) and 0 <= d["job"] < N_JOBS))) if bad]
        if why: aside.append(f"{name}: {', '.join(why)}")
        else: rows.append(d)
    return rows, aside


def frozen_hashes_check(log):
    """G0: the files used now are the frozen ones (HASHES_PREREG_41a.txt, lines 'sha256  filename')."""
    hp = os.path.join(HERE, "HASHES_PREREG_41a.txt")
    if not os.path.exists(hp):
        log("   G0: HASHES_PREREG_41a.txt not found (allowed only for tests)"); return TEST_SMALL
    bad = []
    for line in open(hp):
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            fp = os.path.join(HERE, parts[1])
            if not os.path.exists(fp) or hashlib.sha256(open(fp, "rb").read()).hexdigest() != parts[0]: bad.append(parts[1])
    log(f"G0 (code and design files identical to the frozen hashes): {'PASS' if not bad else 'FAIL ' + str(bad)}")
    return not bad


def choose(rows):
    """One file per job number: the earliest hardware submission (UUIDv7 time); a recovered output counts as that job."""
    by_job = {}
    for r in rows: by_job.setdefault(r["job"], []).append(r)
    return {j: min(v, key=lambda r: (r["_t"], bool(r.get("recovered")))) for j, v in by_job.items()}, by_job


# ----------------------------------------------------------------------------------------------------------------- Stage 1
def stage1(rows, aside, ns, log):
    log("== Stage 1 (gates)")
    g0 = frozen_hashes_check(log)
    from make_design_41a import table as derive_table
    tab = ns["TABLE"]
    tab_ok = derive_table() == tab
    log(f"   design table embedded in job_41a.py equals the seed derivation (make_design_41a.py): {tab_ok}; Block B jobs {ns['B_JOBS']}")
    for a in aside: log("   set aside: " + a)
    problems = [] if tab_ok else ["embedded design table differs from the seed derivation"]
    chosen, by_job = choose(rows)
    ids = {}
    for r in rows: ids.setdefault(r["job_id"], set()).add(r["job"])
    shared = {i: sorted(js) for i, js in ids.items() if len(js) > 1}
    if shared: problems.append(f"one job id used for different job numbers: {shared}")
    rep = {j: len({r['job_id'] for r in v}) for j, v in by_job.items() if len({r['job_id'] for r in v}) > 1}
    log(f"   hardware files {len(rows)}; job numbers submitted more than once {rep or 'none'} (earliest kept)")
    missing = [j for j in range(N_JOBS) if j not in chosen]
    if missing: problems.append(f"missing jobs {missing}")
    for j, r in sorted(chosen.items()):
        d = tab["design"][j]; faulty = {int(k): v for k, v in d["faulty"].items()}
        c = r.get("counts_hex", {}); vals = list(c.values())
        meta = r.get("ionq_meta") if isinstance(r.get("ionq_meta"), dict) else {}
        flat = json.dumps(meta).lower()
        debias_meta = [k for k in ("debias", "debiasing") if f'"{k}": true' in flat]
        checks = {
            "design": r.get("axes") == d["axes"] and r.get("pairs") == d["pairs"] and r.get("faulty") == d["faulty"]
                      and r.get("block") == ("B" if j in ns["B_JOBS"] else "A") and r.get("n_pairs") == N_PAIRS,
            "circuit": same_ops(parse_qasm(r.get("qasm", "")), expected_ops(d["axes"], d["pairs"], faulty, ns["THETA"])),
            "shots": r.get("shots") == SHOTS and len(vals) > 0 and all(isinstance(v, int) and v > 0 for v in vals) and sum(vals) == SHOTS,
            "keys": all(int(k, 16) < 2 ** (2 * N_PAIRS) for k in c),
            "hardware": "forte" in str(r.get("backend", "")).lower() and "simulator" not in str(r.get("backend", "")).lower()
                        and not any("simulator" in str(meta.get(k, "")).lower() for k in ("backend", "target")) and "noise" not in meta,
            "no_debiasing": "no_debias" in str(r.get("debias_requested", "")).lower() and not debias_meta,
        }
        bad = [k for k, v in checks.items() if not v]
        if bad: problems.append(f"job {j} ({r['_file']}): {bad}")
    order = sorted(chosen, key=lambda j: chosen[j]["_t"])
    log(f"   time order of jobs (by job-id timestamp) equals job-number order: {order == sorted(chosen)}")
    for p in problems: log("   PROBLEM: " + p)
    g1 = not problems
    log(f"G1 (complete; design and submitted circuit as fixed in advance; Forte hardware; no debiasing; integrity): {'PASS' if g1 else 'FAIL'}")
    if not (g0 and g1):
        return dict(pass_=False)
    # G2: conventions sanity, per job (a bit-order or convention error in any single job fails it)
    data = decode(chosen, ns); worst = []
    for blk in "AB":
        Bk = data[blk]
        for j in Bk["jobs"]:
            m = (Bk["job"] == j) & ~Bk["faulty"]
            e = [Bk["nerr"][m & (Bk["basis"] == b)].sum() / Bk["n"][m & (Bk["basis"] == b)].sum() for b in range(3)]
            worst.append((max(e), 1 - sum(e) / 2, j))
    g2 = all(mx < 0.25 and F > 0.5 for mx, F, _ in worst)
    mx = max(worst)
    log(f"   per job (clean pairs): largest basis error rate {mx[0]:.4f} (job {mx[2]}); lowest linear F {min(w[1] for w in worst):.4f}")
    log(f"G2 (bit order and error convention sane in every job: each basis error rate < 0.25, F > 0.5): {'PASS' if g2 else 'FAIL'}")
    return dict(pass_=g0 and g1 and g2, order=order)


# ------------------------------------------------------------------------------------------------------------------ decoding
def decode(chosen, ns):
    """Per (job, position) cluster: basis, faulty flag, errors, shots; plus per-shot error matrices for D3."""
    out = {}
    for blk in "AB":
        jobs = sorted((j for j in chosen if chosen[j]["block"] == blk), key=lambda j: chosen[j]["_t"])  # time order
        cl = dict(job=[], pos=[], basis=[], faulty=[], sign=[], nerr=[], n=[], qa=[], qb=[]); shotmats = []
        for j in jobs:
            r = chosen[j]; keys = list(r["counts_hex"]); w = np.array([r["counts_hex"][k] for k in keys])
            bits = np.array([[int(ch) for ch in format(int(k, 16), f"0{2 * N_PAIRS}b")[::-1]] for k in keys])   # bits[:, q] = qubit q
            E = np.zeros((len(keys), N_PAIRS), dtype=int)
            for k, (ax, (a, b)) in enumerate(zip(r["axes"], r["pairs"])):
                same = bits[:, a] == bits[:, b]
                E[:, k] = (~same) if ax in "XZ" else same                       # Phi+: XX, ZZ agree; YY disagree
                cl["job"].append(j); cl["pos"].append(k); cl["basis"].append("XYZ".index(ax)); cl["faulty"].append(str(k) in r["faulty"]); cl["sign"].append(r["faulty"].get(str(k), 0))
                cl["nerr"].append(int((E[:, k] * w).sum())); cl["n"].append(int(w.sum())); cl["qa"].append(a); cl["qb"].append(b)
            shotmats.append((E, w))
        out[blk] = {k: np.array(v) for k, v in cl.items()}; out[blk]["jobs"] = jobs; out[blk]["shots"] = shotmats
    return out


# ------------------------------------------------------------------------------------------------------------------- Stage 2
def draws(B, p, n_check_level):
    """Test-or-keep labels per pair outcome, drawn independently with probability p (equivalently, binomially per cluster and
    outcome type). Returns final certificate, final reference U, any-checkpoint violation, and the certificate at each checkpoint."""
    C = Certifier(p, ALPHA)
    jobs = B["jobs"]; J = len(jobs)
    jidx = np.array([jobs.index(j) for j in B["job"]])
    res = dict(final=[], U=[], viol=0, viol_any=0, path=[])
    for sd in SEEDS:
        rng = np.random.default_rng(sd)
        te = rng.binomial(B["nerr"], p); to = rng.binomial(B["n"] - B["nerr"], p)
        kerr = B["nerr"] - te; kn = B["n"] - te - to                     # kept errors, kept outcomes
        # cumulative over jobs in time order
        E_j = np.bincount(jidx, te, J).cumsum(); K_j = np.bincount(jidx, kn, J).cumsum()
        kerr_jb = np.stack([np.bincount(jidx[B["basis"] == b], kerr[B["basis"] == b], J).cumsum() for b in range(3)])
        kn_jb = np.stack([np.bincount(jidx[B["basis"] == b], kn[B["basis"] == b], J).cumsum() for b in range(3)])
        L = np.array([C.lower(int(E_j[t]), int(K_j[t])) for t in range(J)])
        U_any = 1 - cp_lo(kerr_jb, kn_jb, 0.025 / 3 / n_check_level).sum(0) / 2
        U_fin = 1 - cp_lo(kerr_jb[:, -1], kn_jb[:, -1], 0.025 / 3).sum() / 2
        res["final"].append(L[-1]); res["U"].append(U_fin)
        res["viol"] += L[-1] > U_fin; res["viol_any"] += bool(np.any(L > U_any)); res["path"].append(L)
    n = len(SEEDS)
    res["viol_lo"] = float(cp_lo(np.array(res["viol"]), np.array(n), ALPHA)); res["viol_any_lo"] = float(cp_lo(np.array(res["viol_any"]), np.array(n), ALPHA))
    res["median"] = float(np.median(res["final"])); res["n"] = n; res["N"] = int(B["n"].sum())
    res["path_median"] = np.median(np.array(res["path"]), 0)
    return res


def basis_rates(B, mask=None):
    m = np.ones(len(B["n"]), bool) if mask is None else mask
    return np.array([B["nerr"][m & (B["basis"] == b)].sum() / max(B["n"][m & (B["basis"] == b)].sum(), 1) for b in range(3)])


def stage2(chosen, ns, log):
    log("\n== Stage 2")
    data = decode(chosen, ns); A, B = data["A"], data["B"]
    log(f"   Block A: {len(A['jobs'])} jobs, {A['n'].sum()} pair outcomes; Block B: {len(B['jobs'])} jobs, {B['n'].sum()} pair outcomes "
        f"({int(B['faulty'].sum())} faulty clusters of {len(B['n'])})")
    rA = {p: draws(A, p, len(A["jobs"])) for p in PS}
    rB = {p: draws(B, p, len(B["jobs"])) for p in PS}
    for name, r, J in (("A", rA, len(A["jobs"])), ("B", rB, len(B["jobs"]))):
        for p in PS:
            x = r[p]
            log(f"   Block {name} p={p}: final violations {x['viol']}/{x['n']} (CP95 lower {x['viol_lo']:.3f}); any of {J} checkpoints "
                f"{x['viol_any']}/{x['n']} (CP95 lower {x['viol_any_lo']:.3f}); median certificate {x['median']:.4f}")
    h3 = all(rA[p]["viol_lo"] <= 0.05 for p in PS); h4 = all(rA[p]["viol_any_lo"] <= 0.05 for p in PS)
    log(f"H3 (Block A final certificate never above the conservative reference; prediction PASS): {'PASS' if h3 else 'FAIL'}")
    log(f"H4 (Block A anytime: never above the reference at any of {len(A['jobs'])} job checkpoints in time order; prediction PASS): {'PASS' if h4 else 'FAIL'}")
    h5 = rA[0.2]["median"] > 0.9
    log(f"H5 (Block A median certificate at p = 0.2 above 0.9; prediction PASS): {rA[0.2]['median']:.4f} -> {'PASS' if h5 else 'FAIL'}")
    h6 = all(rB[p]["viol_lo"] <= 0.05 and rB[p]["viol_any_lo"] <= 0.05 for p in PS)
    log(f"H6 (Block B, planted fault: final and anytime validity as H3/H4; prediction PASS): {'PASS' if h6 else 'FAIL'}")
    # H7: power against a known planted fault
    eA = basis_rates(A); FA = 1 - eA.sum() / 2
    f = B["faulty"].mean(); s = np.sin(ns["THETA"] / 2) ** 2
    d_pred = 0.5 * f * s * ((1 - 2 * eA[0]) + (1 - 2 * eA[1]))
    d_cert = rA[0.2]["median"] - rB[0.2]["median"]; R = d_cert / d_pred
    h7 = 0.5 <= R <= 1.5
    log(f"H7 (Block B certificate lower than Block A by the planted amount: ratio in [0.5, 1.5]; prediction PASS): predicted drop {d_pred:.4f}, "
        f"observed drop of the median certificate (p = 0.2) {d_cert:.4f}, ratio {R:.2f} -> {'PASS' if h7 else 'FAIL'}")

    # ---------------------------------------------------------------------------------------------------------- descriptive
    log("\n== Descriptive")
    eBc = basis_rates(B, ~B["faulty"]); eBf = basis_rates(B, B["faulty"]); eB = basis_rates(B)
    FB = 1 - eB.sum() / 2
    pf = eA + (1 - 2 * eA) * s
    log(f"D1 error rates X/Y/Z: Block A {np.round(eA, 4)} (F {FA:.4f}); Block B clean {np.round(eBc, 4)}; Block B faulty {np.round(eBf, 4)} "
        f"(predicted X, Y {pf[0]:.4f}, {pf[1]:.4f}; Z unchanged {eA[2]:.4f}); Block B F {FB:.4f} (predicted {FA - d_pred:.4f})")
    for sg in (1, -1):
        log(f"D1 Block B faulty pairs with phase {'+' if sg > 0 else '-'}theta: X/Y/Z error {np.round(basis_rates(B, B['sign'] == sg), 4)}")
    log(f"D1 certificate minus linear F (p = 0.2): A {rA[0.2]['median'] - FA:+.4f}; B {rB[0.2]['median'] - FB:+.4f}; B median certificate vs "
        f"ground-truth reference F_A - predicted drop {FA - d_pred:.4f}: {rB[0.2]['median'] - (FA - d_pred):+.4f}")
    for b in range(3):                                                                       # D2 clustering across (job, position)
        m = A["basis"] == b; k = A["nerr"][m]; n = A["n"][m]; pb = k.sum() / n.sum()
        chi = (((k - n * pb) ** 2) / (n * pb * (1 - pb))).sum(); df = m.sum() - 1
        log(f"D2 Block A basis {'XYZ'[b]}: {m.sum()} clusters; dispersion chi2/df {chi / df:.2f} (1 = no excess heterogeneity); cluster error range "
            f"{(k / n).min():.3f}-{(k / n).max():.3f}")
    perjob = [1 - basis_rates(A, A["job"] == j).sum() / 2 for j in A["jobs"]]
    log(f"D2 Block A per-job linear F (time order): {' '.join(f'{x:.3f}' for x in perjob)}")
    perjobB = [1 - basis_rates(B, (B["job"] == j) & ~B["faulty"]).sum() / 2 for j in B["jobs"]]
    log(f"D2 Block B per-job linear F of clean pairs (time order; jobs {B['jobs']}): {' '.join(f'{x:.3f}' for x in perjobB)}")
    ratios = []; cors = []                                                                    # D3 independence within a shot
    for E, w in data["A"]["shots"]:
        Ex = np.repeat(E, w, axis=0); e = Ex.mean(0)
        ratios.append(Ex.sum(1).var() / max((e * (1 - e)).sum(), 1e-12))
        with np.errstate(invalid="ignore", divide="ignore"):
            Cm = np.corrcoef(Ex.T)
        cors.append(np.nanmean(Cm[~np.eye(N_PAIRS, dtype=bool)]))
    log(f"D3 within-shot independence (Block A): variance ratio of errors per shot, median {np.median(ratios):.3f} (range {min(ratios):.3f}-{max(ratios):.3f}); "
        f"mean pairwise error correlation {np.nanmean(cors):+.4f}")
    t = [chosen[j]["_t"] for j in sorted(chosen, key=lambda j: chosen[j]["_t"])]
    fmt = lambda x: datetime.datetime.fromtimestamp(x, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log(f"D4 timeline: first job {fmt(t[0])}, last {fmt(t[-1])}, span {(t[-1] - t[0]) / 3600:.2f} h; backend(s) {sorted({r['backend'] for r in chosen.values()})}; "
        f"versions {sorted({json.dumps(r['versions'], sort_keys=True) for r in chosen.values()})}")
    q = np.zeros(2 * N_PAIRS); qn = np.zeros(2 * N_PAIRS)
    for a, b_, k, n in zip(A["qa"], A["qb"], A["nerr"], A["n"]):
        for qq in (a, b_): q[qq] += k; qn[qq] += n
    qe = q / np.maximum(qn, 1); worst = np.argsort(qe)[::-1][:3]
    log(f"D5 per logical qubit (the compiler may place logical qubits on different ions per job; mean error of pairs containing it, Block A): median {np.median(qe):.4f}; worst qubits "
        + ", ".join(f"q{w} {qe[w]:.4f}" for w in worst))
    path = rA[0.2]["path_median"]
    first09 = next((i + 1 for i, x in enumerate(path) if x > 0.9), None)
    log(f"D6 Block A median certificate (p = 0.2) at each job checkpoint: {' '.join(f'{x:.3f}' for x in path)}; first checkpoint above 0.9: {first09}")
    log("D7 simulator rehearsal (noise model, 10 Nov): linear F about 0.985, for comparison")
    return dict(h3=h3, h4=h4, h5=h5, h6=h6, h7=h7, FA=FA, FB=FB, d_pred=d_pred, d_cert=d_cert, ratio=R,
                medA={p: rA[p]["median"] for p in PS}, medB={p: rB[p]["median"] for p in PS})


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", required=True); ap.add_argument("--stage", type=int, choices=(1, 2), required=True)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True); lines = []
    def log(s): print(s, flush=True); lines.append(s)
    ns, _ = load_job_script()
    log(f"STUDY 41a ANALYSIS (stage {a.stage}, {datetime.datetime.now().isoformat(timespec='seconds')})")
    log(f"   analyze_41a.py {sha16(__file__)}; cert.py {sha16(os.path.join(HERE, 'cert.py'))}; job_41a.py {sha16(os.path.join(HERE, 'job_41a.py'))}; "
        f"numpy {np.__version__}; test switch {'ON (synthetic tests only)' if TEST_SMALL else 'off'}")
    rows, aside = read_raw(a.raw)
    log(f"   hardware files: {', '.join(r['_file'] for r in rows)}")
    s1 = stage1(rows, aside, ns, log)
    if a.stage == 2:
        if not s1["pass_"]:
            log("Stage 1 did not pass: Stage 2 not run (as pre-registered)")
        else:
            chosen, _ = choose(rows)
            res = stage2(chosen, ns, log)
            json.dump({k: (v if not isinstance(v, (np.floating, np.bool_)) else v.item()) for k, v in res.items()},
                      open(os.path.join(OUT, "stage2_41a.json"), "w"), indent=1, default=float)
    path = os.path.join(OUT, f"analysis_41a_stage{a.stage}.txt")
    open(path, "w").write("\n".join(lines) + "\n")
    print(f"(written {path}, sha256/16 {sha16(path)})")


if __name__ == "__main__":
    main()
