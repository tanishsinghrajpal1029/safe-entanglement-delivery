"""Study 41b analysis: the certificate for GHZ-3 and GHZ-4 states on IonQ Forte 1 (settings fixed in advance).

Usage:  python analyze_41b.py --raw RAW_DIR --stage 1      (gates)
        python analyze_41b.py --raw RAW_DIR --stage 2      (hypotheses; runs only if Stage 1 passed)
RAW_DIR holds the downloaded job files (s41b_job_XX.json). Needs numpy, scipy and job_41b.py, make_design_41b.py and
cert.py next to this script. Qiskit is NOT needed.

Test per GHZ state (fixed by the design table): 'Z' (pass iff all outcomes equal) with marginal probability 1/3, or an
even-#Y string s in {X,Y}^n with probability (2/3)/2^(n-1) (pass iff the outcome parity equals (-1)^(#Y/2)). Then
P(fail) = (2/3)(1 - F_GHZ) exactly for every state, so cert.py (a = 2/3) certifies the GHZ fidelity of kept states.
Linear estimate: F = 1 - e_Z/2 - mean_s e_s (mean over the 2^(n-1) XY strings).
"""
import argparse, glob, hashlib, json, os, re, sys, types, uuid, datetime
import numpy as np
from scipy.stats import beta

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cert import Certifier                                                         # unchanged since Study 27

N_JOBS, SHOTS = 20, 1000
PS = (0.05, 0.1, 0.2)
ALPHA = 0.05
H5_THRESHOLD = {3: 0.90, 4: 0.85}
TEST_SMALL = os.environ.get("S41B_TEST_SMALL") == "1"                             # synthetic tests only; never set for the real run
SEEDS = range(61001, 61101) if TEST_SMALL else range(61001, 62001)              # 1,000 test-or-keep draws per p
OUT = os.path.join(HERE, "out")
FROZEN = ("PREREG_41b.md", "job_41b.py", "make_design_41b.py", "analyze_41b.py", "cert.py")


def sha16(path): return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
def cp_lo(k, n, a): return np.where(k == 0, 0.0, beta.ppf(a, np.maximum(k, 1), np.maximum(n - k + 1, 1)))


def xy_strings(n):
    import itertools
    return ["".join(c) for c in itertools.product("XY", repeat=n) if c.count("Y") % 2 == 0]


def categories(n): return ["Z"] + xy_strings(n)


def load_job_script():
    path = os.path.join(HERE, "job_41b.py")
    try:
        import qiskit  # noqa: F401
    except ImportError:
        stub = types.ModuleType("qiskit"); stub.QuantumCircuit = None; sys.modules["qiskit"] = stub
    ns = {"__name__": "job_41b"}
    exec(compile(open(path).read(), path, "exec"), ns)
    return ns


def expected_ops(groups, tests):
    ops = []
    for g, t in zip(groups, tests):
        ops.append(("h", None, (g[0],)))
        ops += [("cx", None, (a, b)) for a, b in zip(g[:-1], g[1:])]
        if t != "Z":
            for q, ax in zip(g, t):
                if ax == "X": ops.append(("h", None, (q,)))
                if ax == "Y": ops += [("sdg", None, (q,)), ("h", None, (q,))]
    nq = sum(len(g) for g in groups)
    return ops + [("measure", None, (q, q)) for q in range(nq)]


def parse_qasm(text):
    ops = []
    for line in str(text).splitlines():
        line = line.strip()
        if not line or line.startswith(("OPENQASM", "include", "qreg", "creg", "//", "barrier")): continue
        m = re.fullmatch(r"measure q\[(\d+)\]\s*->\s*c\[(\d+)\];", line)
        if m: ops.append(("measure", None, (int(m[1]), int(m[2])))); continue
        m = re.fullmatch(r"(\w+)(?:\(([^)]*)\))?\s+(.+);", line)
        if not m: ops.append(("?", None, (line,))); continue
        par = None if m[2] is None else float(eval(m[2], {"__builtins__": {}}, {"pi": np.pi}))
        ops.append((m[1], par, tuple(int(x) for x in re.findall(r"q\[(\d+)\]", m[3]))))
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
        why = [w for w, bad in (("not study 41b", d.get("study") != "41b"), ("not hardware mode", d.get("mode") != "hardware"),
                                ("no counts", "counts_hex" not in d), ("job id not UUIDv7", d["_t"] is None),
                                ("job number not an integer in 0-19", not (isinstance(d.get("job"), int) and 0 <= d["job"] < N_JOBS))) if bad]
        if why: aside.append(f"{name} (job {d.get('job')}, id {d.get('job_id')}): {', '.join(why)}")
        else: rows.append(d)
    return rows, aside


def frozen_hashes_check(log):
    hp = os.path.join(HERE, "HASHES_PREREG_41b.txt")
    if not os.path.exists(hp):
        log("   G0: HASHES_PREREG_41b.txt not found (allowed only for tests)"); return TEST_SMALL
    bad, listed = [], set()
    for line in open(hp):
        parts = line.split()
        if len(parts) == 2 and len(parts[0]) == 64:
            listed.add(parts[1]); fp = os.path.join(HERE, parts[1])
            if not os.path.exists(fp) or hashlib.sha256(open(fp, "rb").read()).hexdigest() != parts[0]: bad.append(parts[1])
    bad += [f"{f} (not listed)" for f in FROZEN if f not in listed]
    log(f"G0 (code and design files identical to the frozen hashes): {'PASS' if not bad else 'FAIL ' + str(bad)}")
    return not bad


def choose(rows):
    by_job = {}
    for r in rows: by_job.setdefault(r["job"], []).append(r)
    return {j: min(v, key=lambda r: r["_t"]) for j, v in by_job.items()}, by_job


def decode(chosen):
    """Per (job, group) cluster: n, category index, errors, shots; plus per-shot error matrices for D3."""
    out = {}
    for n in (3, 4):
        jobs = sorted((j for j in chosen if chosen[j]["n"] == n), key=lambda j: chosen[j]["_t"])  # time order
        cats = categories(n)
        cl = dict(job=[], cat=[], nerr=[], n=[], q=[]); shotmats = []
        for j in jobs:
            r = chosen[j]; keys = list(r["counts_hex"]); w = np.array([r["counts_hex"][k] for k in keys])
            nq = sum(len(g) for g in r["groups"])
            bits = np.array([[int(ch) for ch in format(int(k, 16), f"0{nq}b")[::-1]] for k in keys])   # bits[:, q] = qubit q
            E = np.zeros((len(keys), len(r["groups"])), dtype=int)
            for i, (g, t) in enumerate(zip(r["groups"], r["tests"])):
                b = bits[:, g]
                if t == "Z":
                    E[:, i] = (b.min(1) != b.max(1))                       # not all equal
                else:
                    E[:, i] = (b.sum(1) % 2) != ((t.count("Y") // 2) % 2)  # parity sign != (-1)^(#Y/2)
                cl["job"].append(j); cl["cat"].append(cats.index(t)); cl["nerr"].append(int((E[:, i] * w).sum()))
                cl["n"].append(int(w.sum())); cl["q"].append(g)
            shotmats.append((E, w))
        out[n] = {k: (np.array(v) if k != "q" else v) for k, v in cl.items()}
        out[n]["jobs"] = jobs; out[n]["shots"] = shotmats; out[n]["ncat"] = len(cats)
    return out


def cat_rates(B, mask=None):
    m = np.ones(len(B["n"]), bool) if mask is None else mask
    return np.array([B["nerr"][m & (B["cat"] == c)].sum() / max(B["n"][m & (B["cat"] == c)].sum(), 1) for c in range(B["ncat"])])


def lin_F(e, present=None):
    """F = 1 - e_Z/2 - mean of the XY strings' error rates (over the strings present)."""
    xy = e[1:] if present is None else e[1:][present[1:]]
    return 1 - e[0] / 2 - (xy.mean() if len(xy) else 0.0)


# ----------------------------------------------------------------------------------------------------------------- Stage 1
def stage1(rows, aside, ns, log):
    log("== Stage 1 (gates)")
    g0 = frozen_hashes_check(log)
    from make_design_41b import table as derive_table
    tab = ns["TABLE"]; tab_ok = derive_table() == tab
    log(f"   design table embedded in job_41b.py equals the seed derivation (make_design_41b.py): {tab_ok}; sizes {tab['sizes']}")
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
    stats_log = []
    for j, r in sorted(chosen.items()):
        d = tab["design"][j]
        c = r.get("counts_hex", {}); vals = list(c.values())
        meta_ok = isinstance(r.get("ionq_meta"), dict)
        meta = r.get("ionq_meta") if meta_ok else {}
        flat = json.dumps(meta).lower()
        st = meta.get("stats", {}) if isinstance(meta.get("stats"), dict) else {}
        stats_log.append(f"{j}:{st.get('qubits')}q/{(st.get('gate_counts') or {}).get('1q')}+{(st.get('gate_counts') or {}).get('2q')}")
        checks = {
            "design": r.get("n") == d["n"] and r.get("groups") == d["groups"] and r.get("tests") == d["tests"],
            "circuit": same_ops(parse_qasm(r.get("qasm", "")), expected_ops(d["groups"], d["tests"])),
            "shots": r.get("shots") == SHOTS and len(vals) > 0 and all(isinstance(v, int) and v > 0 for v in vals) and sum(vals) == SHOTS,
            "keys": all(int(k, 16) < 2 ** 36 for k in c),
            "hardware": meta_ok and "forte" in str(r.get("backend", "")).lower() and "simulator" not in str(r.get("backend", "")).lower()
                        and not any("simulator" in str(meta.get(k, "")).lower() for k in ("backend", "target")) and "noise" not in meta,
            "no_debiasing": "no_debias" in str(r.get("debias_requested", "")).lower()
                            and not any(x in flat for x in ('"debiasing": true', '"debias": true', '"applied": true')),
        }
        bad = [k for k, v in checks.items() if not v]
        if bad: problems.append(f"job {j} ({r['_file']}): {bad}")
    order = sorted(chosen, key=lambda j: chosen[j]["_t"])
    log(f"   time order of jobs (by job-id timestamp) equals job-number order: {order == sorted(chosen)}")
    log(f"   IonQ compiled stats per job (job:qubits/1q+2q gates; reported, not gated): {' '.join(stats_log)}")
    for p in problems: log("   PROBLEM: " + p)
    g1 = not problems
    log(f"G1 (complete; design and submitted circuit as fixed in advance; Forte hardware; no debiasing; integrity): {'PASS' if g1 else 'FAIL'}")
    if not (g0 and g1):
        return dict(pass_=False)
    data = decode(chosen); worst = []
    for n in (3, 4):
        B = data[n]
        for j in B["jobs"]:
            m = B["job"] == j; e = cat_rates(B, m)
            present = np.array([(m & (B["cat"] == c)).any() for c in range(B["ncat"])])
            worst.append((float(e[present].max()), float(lin_F(e, present)), j))
    g2 = all(mx < 0.25 and F > 0.5 for mx, F, _ in worst)
    log(f"   per job: largest test error rate {max(worst)[0]:.4f} (job {max(worst)[2]}); lowest linear F {min(w[1] for w in worst):.4f}")
    log(f"G2 (bit order and conventions sane in every job: each test's error rate < 0.25, linear F > 0.5): {'PASS' if g2 else 'FAIL'}")
    return dict(pass_=g0 and g1 and g2, order=order)


# ------------------------------------------------------------------------------------------------------------------- Stage 2
def U_ref(kerr, kn, level):
    """Conservative upper reference for the kept states' GHZ fidelity: F = 1 - e_Z/2 - mean_s e_s, each e at its CP lower bound."""
    lo = cp_lo(kerr, kn, level / kerr.shape[0])
    return 1 - lo[0] / 2 - lo[1:].mean(0)


def draws(B, p):
    C = Certifier(p, ALPHA)
    jobs = B["jobs"]; J = len(jobs); K = B["ncat"]
    jidx = np.array([jobs.index(j) for j in B["job"]])
    res = dict(final=[], viol=0, viol_any=0, path=[])
    for sd in SEEDS:
        rng = np.random.default_rng(sd)
        te = rng.binomial(B["nerr"], p); to = rng.binomial(B["n"] - B["nerr"], p)
        kerr = B["nerr"] - te; kn = B["n"] - te - to
        E_j = np.bincount(jidx, te, J).cumsum(); K_j = np.bincount(jidx, kn, J).cumsum()
        kerr_jc = np.stack([np.bincount(jidx[B["cat"] == c], kerr[B["cat"] == c], J).cumsum() for c in range(K)])
        kn_jc = np.stack([np.bincount(jidx[B["cat"] == c], kn[B["cat"] == c], J).cumsum() for c in range(K)])
        L = np.array([C.lower(int(E_j[t]), int(K_j[t])) for t in range(J)])
        U_any = U_ref(kerr_jc, kn_jc, 0.025 / J)
        U_fin = U_ref(kerr_jc[:, -1:], kn_jc[:, -1:], 0.025)[0]
        res["final"].append(L[-1]); res["viol"] += L[-1] > U_fin; res["viol_any"] += bool(np.any(L > U_any)); res["path"].append(L)
    n = len(SEEDS)
    res["viol_lo"] = float(cp_lo(np.array(res["viol"]), np.array(n), ALPHA)); res["viol_any_lo"] = float(cp_lo(np.array(res["viol_any"]), np.array(n), ALPHA))
    res["median"] = float(np.median(res["final"])); res["n"] = n
    P = np.array(res["path"]); res["path_median"] = np.median(P, 0); res["first_gt05"] = float((P[:, 0] > 0.5).mean())
    return res


def stage2(chosen, log):
    log("\n== Stage 2")
    data = decode(chosen); R = {}
    for n in (3, 4):
        B = data[n]
        log(f"   GHZ-{n}: {len(B['jobs'])} jobs, {int(B['n'].sum())} states ({len(B['n'])} clusters)")
        R[n] = {p: draws(B, p) for p in PS}
        for p in PS:
            x = R[n][p]
            log(f"   GHZ-{n} p={p}: final violations {x['viol']}/{x['n']} (CP95 lower {x['viol_lo']:.3f}); any of {len(B['jobs'])} checkpoints "
                f"{x['viol_any']}/{x['n']} (CP95 lower {x['viol_any_lo']:.3f}); median certificate {x['median']:.4f}")
    h3 = all(R[n][p]["viol_lo"] <= 0.05 for n in (3, 4) for p in PS)
    h4 = all(R[n][p]["viol_any_lo"] <= 0.05 for n in (3, 4) for p in PS)
    log(f"H3b (final certificate never above the conservative reference, GHZ-3 and GHZ-4; prediction PASS): {'PASS' if h3 else 'FAIL'}")
    log(f"H4b (anytime: never above the reference at any job checkpoint in time order, both sizes; prediction PASS): {'PASS' if h4 else 'FAIL'}")
    h5 = all(R[n][0.2]["median"] > H5_THRESHOLD[n] for n in (3, 4))
    log(f"H5b (median certificate at p = 0.2 above 0.90 for GHZ-3 and 0.85 for GHZ-4; prediction PASS): "
        f"{R[3][0.2]['median']:.4f}, {R[4][0.2]['median']:.4f} -> {'PASS' if h5 else 'FAIL'}")
    h6 = all(R[n][0.05]["first_gt05"] >= 0.99 for n in (3, 4))
    log(f"H6b (genuine multipartite entanglement of the kept ensemble certified from the first job alone: certificate > 0.5 at the first checkpoint "
        f"in >= 99% of draws at p = 0.05, both sizes; prediction PASS): {R[3][0.05]['first_gt05']:.3f}, {R[4][0.05]['first_gt05']:.3f} -> {'PASS' if h6 else 'FAIL'}")

    log("\n== Descriptive")
    Fs = {}
    for n in (3, 4):
        B = data[n]; e = cat_rates(B); Fs[n] = lin_F(e)
        cnt = [int((B["cat"] == c).sum()) for c in range(B["ncat"])]
        log(f"D1 GHZ-{n} realised test counts (clusters): " + ", ".join(f"{c} {k}" for c, k in zip(categories(n), cnt)))
        log(f"D1 GHZ-{n}: error rates " + ", ".join(f"{c} {x:.4f}" for c, x in zip(categories(n), e)) +
            f"; linear F {Fs[n]:.4f}; certificate minus F (p = 0.2) {R[n][0.2]['median'] - Fs[n]:+.4f}")
        cats = categories(n)
        for c in range(B["ncat"]):
            m = B["cat"] == c; k = B["nerr"][m]; nn = B["n"][m]; pb = k.sum() / nn.sum()
            if m.sum() > 1 and 0 < pb < 1:
                chi = (((k - nn * pb) ** 2) / (nn * pb * (1 - pb))).sum()
                log(f"D2 GHZ-{n} test {cats[c]}: {m.sum()} clusters; dispersion chi2/df {chi / (m.sum() - 1):.2f}; range {(k / nn).min():.3f}-{(k / nn).max():.3f}")
        perjob = []
        for j in B["jobs"]:
            mj = B["job"] == j; ej = cat_rates(B, mj)
            pres = np.array([(mj & (B["cat"] == c)).any() for c in range(B["ncat"])]); perjob.append(lin_F(ej, pres))
        log(f"D2 GHZ-{n} per-job linear F (time order): {' '.join(f'{x:.3f}' for x in perjob)}")
        ratios, cors = [], []
        for E, w in B["shots"]:
            Ex = np.repeat(E, w, axis=0); em = Ex.mean(0)
            ratios.append(Ex.sum(1).var() / max((em * (1 - em)).sum(), 1e-12))
            with np.errstate(invalid="ignore", divide="ignore"):
                Cm = np.corrcoef(Ex.T)
            cors.append(np.nanmean(Cm[~np.eye(E.shape[1], dtype=bool)]))
        log(f"D3 GHZ-{n} within-shot independence: variance ratio median {np.median(ratios):.3f} (range {min(ratios):.3f}-{max(ratios):.3f}); "
            f"mean pairwise error correlation {np.nanmean(cors):+.4f}")
        log(f"D6 GHZ-{n} median certificate (p = 0.2) at each job checkpoint: {' '.join(f'{x:.3f}' for x in R[n][0.2]['path_median'])}")
    t = sorted(chosen[j]["_t"] for j in chosen)
    fmt = lambda x: datetime.datetime.fromtimestamp(x, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log(f"D4 timeline: first job {fmt(t[0])}, last {fmt(t[-1])}, span {(t[-1] - t[0]) / 3600:.2f} h; backend(s) {sorted({r['backend'] for r in chosen.values()})}; "
        f"versions {sorted({json.dumps(r.get('versions', {}), sort_keys=True) for r in chosen.values()})}")
    log(f"D5 scaling with the Bell pairs of Study 41a (linear F 0.978, 1 CX): 1 - F per CX = {(1 - Fs[3]) / 2:.4f} (GHZ-3, 2 CX), "
        f"{(1 - Fs[4]) / 3:.4f} (GHZ-4, 3 CX), 0.022 (Bell)")
    return dict(h3=h3, h4=h4, h5=h5, h6=h6, F3=Fs[3], F4=Fs[4], med3={p: R[3][p]["median"] for p in PS}, med4={p: R[4][p]["median"] for p in PS})


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--raw", required=True); ap.add_argument("--stage", type=int, choices=(1, 2), required=True)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True); lines = []
    def log(s): print(s, flush=True); lines.append(s)
    ns = load_job_script()
    log(f"STUDY 41b ANALYSIS (stage {a.stage}, {datetime.datetime.now().isoformat(timespec='seconds')})")
    log(f"   analyze_41b.py {sha16(__file__)}; cert.py {sha16(os.path.join(HERE, 'cert.py'))}; job_41b.py {sha16(os.path.join(HERE, 'job_41b.py'))}; "
        f"numpy {np.__version__}; test switch {'ON (synthetic tests only)' if TEST_SMALL else 'off'}")
    rows, aside = read_raw(a.raw)
    log(f"   hardware files: {', '.join(r['_file'] for r in rows)}")
    s1 = stage1(rows, aside, ns, log)
    if a.stage == 2:
        if not s1["pass_"]:
            log("Stage 1 did not pass: Stage 2 not run (as pre-registered)")
        else:
            chosen, _ = choose(rows)
            res = stage2(chosen, log)
            json.dump(res, open(os.path.join(OUT, "stage2_41b.json"), "w"), indent=1, default=float)
    path = os.path.join(OUT, f"analysis_41b_stage{a.stage}.txt")
    open(path, "w").write("\n".join(lines) + "\n")
    print(f"(written {path}, sha256/16 {sha16(path)})")


if __name__ == "__main__":
    main()
