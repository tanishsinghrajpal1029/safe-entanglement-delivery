"""ICFO 2021 (Lago-Rivera et al., Nature 594, 37; Zenodo 6454536) Stage 1: pre-registered blind rebuild + real-data checks.
Pre-registration: PREREG_ICFO_STAGE1.md (written and hashed before this script was run on any coherence data).

Data: uint64 little-endian time tags [ps]. Channels: i = heralding idler (1436 nm), s1/s2 = the two outputs of the beam splitter
that recombines the two memories' signal modes (606 nm), t = trigger (unused).  Folders per storage time tau:
  'data - coherences': coh_k files (one interference phase setting each; phases not recorded);
  'data - diagonal'  : *tom* (only memory A read out), *jerry* (only B), and both-open runs (no 'tom'/'jerry'/'pit' in name).
Usage: python3 icfo_stage1.py <icfo_2021 dir> <out.json> [taus, e.g. 2,7]
"""
import glob, json, os, re, sys
import numpy as np

TAUS = (2, 7, 12, 19, 25)          # us
BIN = 20_000                       # ps (authors' 20 ns bins)
WIN = 400_000                      # ps (400 ns coincidence window, as the paper)
NOISE = (640_000, 960_000)         # ps after the window start (authors' 2 us script: bins 325-340 vs window 293-312)
BLOCK = 60.0                       # s, R3 blocks
ALPHA = 0.05
RNG = np.random.default_rng(20261011)


def rd(f):
    """read time tags; the single pre-allowed decoding fix (ledger E91): 12 of 254 files contain a 'Hydra' glitch where tags
    jump backwards near the end of a run (the authors' own script trims such tails, 'Tremove'); keep only tags that are >= the
    running maximum (drops 0.02-0.5% of tags in the affected files, none elsewhere)."""
    x = np.fromfile(f, dtype="<u8").astype(np.int64)
    return x[x >= np.maximum.accumulate(x)]


def count_in(i, s, lo, hi):
    """per herald: number of s clicks with delay in [lo, hi) ps."""
    return np.searchsorted(s, i + hi, "left") - np.searchsorted(s, i + lo, "left")


def classify(folder):
    files = sorted(glob.glob(os.path.join(folder, "i_*.pt"))); out = {"coh": [], "tom": [], "jerry": [], "both": []}
    for f in files:
        b = os.path.basename(f)[2:-3].lower()
        if "pit" in b: continue
        if "coh" in b: out["coh"].append(f)
        elif "tom" in b: out["tom"].append(f)
        elif "jerry" in b: out["jerry"].append(f)
        else: out["both"].append(f)
    return out


def triple(fi):
    d, b = os.path.dirname(fi), os.path.basename(fi)[2:]
    return rd(fi), rd(os.path.join(d, "s1_" + b)), rd(os.path.join(d, "s2_" + b))


def find_window(coh_files, tau):
    """window start: maximise pooled (s1 + s2) coincidences in [s, s + 400 ns) over s in [tau - 400, tau + 200] ns, 20 ns steps.
    Uses only the herald-signal coincidence total (not the s1/s2 split that carries the visibility)."""
    starts = np.arange(tau * 1_000_000 - 400_000, tau * 1_000_000 + 200_001, BIN); tot = np.zeros(len(starts))
    for f in coh_files:
        i, s1, s2 = triple(f)
        for j, s0 in enumerate(starts): tot[j] += count_in(i, s1, s0, s0 + WIN).sum() + count_in(i, s2, s0, s0 + WIN).sum()
    return int(starts[np.argmax(tot)])


def net_counts(i, s, s0):
    c = count_in(i, s, s0, s0 + WIN); a = count_in(i, s, s0 + NOISE[0], s0 + NOISE[1])
    return c, a.sum() * WIN / (NOISE[1] - NOISE[0])


def visibility(coh_files, s0):
    m1, m2, n1r, n2r, H = [], [], [], [], []
    for f in coh_files:
        i, s1, s2 = triple(f); c1, a1 = net_counts(i, s1, s0); c2, a2 = net_counts(i, s2, s0)
        m1.append(c1.sum() - a1); m2.append(c2.sum() - a2); n1r.append(c1.sum()); n2r.append(c2.sum()); H.append(len(i))
    m1, m2, n1r, n2r, H = map(np.array, (m1, m2, n1r, n2r, H))

    def est(m1, m2, n1r, n2r, H):
        r = m1.sum() / m2.sum(); E = (m1 - r * m2) / (m1 + r * m2)
        varE = (1 - E ** 2) / np.maximum(n1r + n2r, 1)
        V = np.sqrt(max(2 * np.mean(E ** 2) - 2 * np.mean(varE), 0))
        R1, R2 = m1 / H, m2 / H                                        # per-output fringes (normalised by heralds)
        V1 = np.sqrt(max(2 * (np.var(R1) - np.mean(n1r / H ** 2)) / np.mean(R1) ** 2, 0))
        V2 = np.sqrt(max(2 * (np.var(R2) - np.mean(n2r / H ** 2)) / np.mean(R2) ** 2, 0))
        return V, float(np.max(np.abs(E))), V1, V2, E
    V, Vmax, V1, V2, E = est(m1, m2, n1r, n2r, H)
    B = []                                                             # parametric bootstrap (Poisson counts)
    for _ in range(500):
        n1b, n2b = RNG.poisson(n1r), RNG.poisson(n2r); a1b = np.maximum(n1r - m1, 0); a2b = np.maximum(n2r - m2, 0)
        B.append(est(n1b - a1b, n2b - a2b, n1b, n2b, H)[0])
    return dict(V=V, V_sd=float(np.std(B)), V_max_absE=Vmax, V_out1=V1, V_out2=V2, E=[round(float(x), 4) for x in E],
                n_settings=len(coh_files), heralds=int(H.sum()), net1=float(m1.sum()), net2=float(m2.sum()))


def diag_probs(files, s0):
    """net probability per herald of a click at either output in the window (both outputs summed), and h_c(2) for both-open."""
    N = 0; net = 0.0; raw = 0; n1 = n2 = n12 = 0
    for f in files:
        i, s1, s2 = triple(f); c1, a1 = net_counts(i, s1, s0); c2, a2 = net_counts(i, s2, s0)
        N += len(i); net += c1.sum() + c2.sum() - a1 - a2; raw += int(c1.sum() + c2.sum())
        n1 += int((c1 > 0).sum()); n2 += int((c2 > 0).sum()); n12 += int(((c1 > 0) & (c2 > 0)).sum())
    return dict(heralds=N, p=net / max(N, 1), p_sd=np.sqrt(raw) / max(N, 1), n1=n1, n2=n2, n12=n12,
                hc2=(n12 * N / max(n1 * n2, 1)) if n1 and n2 else float("nan"))


def r3_blocks(files, s0):
    """R3: per both-open run, 60-s blocks of (heralds, echo clicks). Over-dispersion vs binomial, and anytime-valid coverage:
    running Beta(1/2,1/2) mixture CS for the per-herald echo probability; does it ever exclude the full-run estimate?"""
    from scipy.special import betaln
    from scipy.stats import chi2
    out = []
    for f in files:
        i, s1, s2 = triple(f); c = count_in(i, s1, s0, s0 + WIN) + count_in(i, s2, s0, s0 + WIN); k = (c > 0).astype(int)
        t = (i - i[0]) * 1e-12; b = (t // BLOCK).astype(int); nb = b.max() + 1
        Nb = np.bincount(b, minlength=nb); Kb = np.bincount(b, weights=k, minlength=nb); keep = Nb > 0.5 * np.median(Nb)
        Nb, Kb = Nb[keep], Kb[keep]; p = Kb.sum() / Nb.sum()
        X2 = float((((Kb - Nb * p) ** 2) / (Nb * p * (1 - p))).sum()); dof = len(Nb) - 1
        Nc, Kc = np.cumsum(Nb), np.cumsum(Kb)                       # CS checked at block ends
        logM = betaln(Kc + 0.5, Nc - Kc + 0.5) - betaln(0.5, 0.5) - (Kc * np.log(p) + (Nc - Kc) * np.log(1 - p))
        excl = logM >= np.log(1 / ALPHA)
        out.append(dict(file=os.path.basename(f), blocks=int(len(Nb)), heralds=int(Nb.sum()), p=float(p), dispersion=X2 / max(dof, 1),
                        disp_pvalue=float(chi2.sf(X2, dof)), cs_ever_excludes_final=bool(excl.any()), cs_frac_excluding=float(excl.mean())))
    return out


def main(root, outp, taus=TAUS):
    res = {}
    for tau in taus:
        coh = classify(os.path.join(root, f"{tau}us", "data - coherences"))["coh"]
        dg = classify(os.path.join(root, f"{tau}us", "data - diagonal"))
        s0 = find_window(coh, tau); vis = visibility(coh, s0)
        pt, pj, pb = diag_probs(dg["tom"], s0), diag_probs(dg["jerry"], s0), diag_probs(dg["both"], s0)
        p10, p01 = pt["p"], pj["p"]; hc = pb["hc2"]; p11 = hc * p10 * p01
        V = vis["V"]; C = V * (p01 + p10) - 2 * np.sqrt(max(p11, 0))
        F = 0.5 * (p01 + p10) * (1 + V) / (p01 + p10 + p11)
        # C uncertainty: propagate V_sd, p sds, and h_c(2) Poisson error on n12
        Cs = []
        for _ in range(2000):
            Vb = RNG.normal(V, vis["V_sd"]); a = RNG.normal(p10, pt["p_sd"]); bq = RNG.normal(p01, pj["p_sd"])
            hb = RNG.poisson(max(pb["n12"], 0)) * pb["heralds"] / max(pb["n1"] * pb["n2"], 1)
            Cs.append(Vb * (a + bq) - 2 * np.sqrt(max(hb * a * bq, 0)))
        res[f"{tau}us"] = dict(window_start_ns=s0 / 1000, vis=vis, tom=pt, jerry=pj, both=pb, p10=p10, p01=p01, hc2=hc, p11=p11,
                               C=C, C_sd=float(np.std(Cs)), C_z=C / max(np.std(Cs), 1e-12), F_eff=F, r3=r3_blocks(dg["both"], s0))
        print(json.dumps({k: (round(v, 5) if isinstance(v, float) else v) for k, v in res[f"{tau}us"].items() if k not in ("vis", "tom", "jerry", "both", "r3")}), flush=True)
        print("  V", round(V, 4), "+-", round(vis["V_sd"], 4), "Vmax", round(vis["V_max_absE"], 4), "V_out", round(vis["V_out1"], 3), round(vis["V_out2"], 3), "E", vis["E"], flush=True)
        for x in res[f"{tau}us"]["r3"]: print("  R3", x, flush=True)
    json.dump(res, open(outp, "w"), indent=1, default=float)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], tuple(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else TAUS)
