"""Study 26 analysis (locked before the confirmatory run). Usage:
    python analyze_26.py tune  <pilot runs.csv>      # dev pilot only: the pre-registered tuning rule for plugM and cut
    python analyze_26.py all   <runs.csv>            # confirmatory: every hypothesis in README_26.md
SAFE (the study-wide safety bar):
    per-user risk  = sum(users_bad) / sum(users_total)  with a one-sided 95% cluster-bootstrap upper bound (over networks) <= LEVEL
    delivered-pair risk r = sum(bad) / sum(delivered)  with a one-sided 95% cluster-bootstrap upper bound <= 1%
  LEVEL = alpha = 5% everywhere except Block O recipe arms, where the recipe adds beta = 5% (LEVEL = 10%).
A cell with no deliveries is SAFE (it delivered nothing) but is VACUOUS: every verdict lists its vacuous cells, and a hypothesis whose
cells are all vacuous is reported as 'PASS (vacuous)'. nets_zero = networks in the cell that delivered nothing.
"""
import sys
import numpy as np
import pandas as pd

ALPHA, BETA, DELTA = 0.05, 0.05, 0.01
NB = 2000
EXPECT = {"U": 4 * 9, "R": 4 * 7 * 9, "O": 2 * 2 * 6, "S": 3 * 3 * 3}   # cells per block (confirmatory)


def boot_ub(df, num, den, seed=12345):
    """one-sided 95% upper bound of sum(num)/sum(den), resampling networks (rows) with replacement."""
    n = df[num].to_numpy(float); d = df[den].to_numpy(float)
    if d.sum() == 0: return 0.0
    if n.sum() == 0: return 0.0
    rng = np.random.default_rng(seed); idx = rng.integers(0, len(n), (NB, len(n)))
    dd = d[idx].sum(1); vals = np.where(dd > 0, n[idx].sum(1) / np.maximum(dd, 1), 0.0)
    return float(np.quantile(vals, 0.95))


def cell(df):
    deliv = df.delivered.sum(); bad = df.bad.sum(); ut = df.users_total.sum(); ub = df.users_bad.sum()
    oq = df.oracle_qual.sum()
    return dict(nets=len(df), delivered=int(deliv), bad=int(bad), r=bad / deliv if deliv else 0.0, r_ub=boot_ub(df, "bad", "delivered"),
                users=int(ut), users_bad=int(ub), pu=ub / ut if ut else 0.0, pu_ub=boot_ub(df, "users_bad", "users_total"),
                pu_served=ub / max(df.users_served.sum(), 1), nets_with_bad=int((df.bad > 0).sum()),
                frac_oracle=(df.qual.sum() / oq) if oq else 0.0, paths_bad_pct=100 * df.paths_bad.sum() / max(df.paths_delivered.sum(), 1),
                nets_zero=int((df.delivered == 0).sum()), vacuous=bool(deliv == 0), users_req=int(df.users_requested.sum()),
                pu_req=ub / max(df.users_requested.sum(), 1),
                lat=df.loc[df.lat_e2e_mean >= 0, "lat_e2e_mean"].mean(), phi_true=df.phi_true_mean.mean(), phi_decl=df.phi_decl_mean.mean(),
                dec=df.dec.mean(), dec_viol=int(df.dec_viol.sum()))


def safe(c, level=ALPHA):
    return c["pu_ub"] <= level and c["r_ub"] <= DELTA


def table(df, keys):
    rows = []
    for k, g in df.groupby(keys): rows.append(dict(zip(keys, k if isinstance(k, tuple) else (k,)), **cell(g)))
    return pd.DataFrame(rows)


def paired_diff(df, a, b, keys=("hw",), seed=7):
    """frac_oracle(a) - frac_oracle(b), paired by network idx, 90% two-sided cluster-bootstrap CI (points)."""
    out = []
    for k, g in df.groupby(list(keys)):
        A = g[g.arm == a].set_index("idx"); B = g[g.arm == b].set_index("idx"); ix = A.index.intersection(B.index)
        if len(ix) == 0: continue
        qa, oa, qb, ob = A.loc[ix, "qual"].to_numpy(float), A.loc[ix, "oracle_qual"].to_numpy(float), B.loc[ix, "qual"].to_numpy(float), B.loc[ix, "oracle_qual"].to_numpy(float)
        est = 100 * (qa.sum() / oa.sum() - qb.sum() / ob.sum())
        rng = np.random.default_rng(seed); idx = rng.integers(0, len(ix), (NB, len(ix)))
        bs = 100 * (qa[idx].sum(1) / oa[idx].sum(1) - qb[idx].sum(1) / ob[idx].sum(1))
        out.append(dict(key=k, n=len(ix), diff=est, lo=float(np.quantile(bs, 0.05)), hi=float(np.quantile(bs, 0.95))))
    return out


def verdict(name, ok, detail, cells=None):
    vac = [] if cells is None else [tuple(str(r[k]) for k in ("hw", "arm", "cfg") if k in r) for r in cells.to_dict("records") if r["vacuous"]]
    allvac = cells is not None and len(cells) > 0 and len(vac) == len(cells)
    tag = ("PASS (vacuous)" if allvac else "PASS") if ok else "FAIL"
    print(f"{name}: {tag} ({detail}; vacuous cells: {vac or 'none'})")


def tune(df):
    print("DEV TUNING (pre-registered rule, 16 dev networks per value): a value is dev-SAFE if r_ub <= 1% and pu_ub <= 5% (the study's")
    print("SAFE bar) and it delivered something. plugM = smallest dev-SAFE m; cut = largest x such that every x' <= x is dev-SAFE.")
    print("If no value qualifies: the strictest value (largest m, smallest x), flagged infeasible.")
    df = df.drop_duplicates("run"); out = {}
    for hw, g in df[df.arm.isin(["plugM", "cut"])].groupby("hw"):
        res = {}
        for arm in ("plugM", "cut"):
            gg = g[g.arm == arm].copy(); gg["val"] = gg.cfg.str[1:].astype(float)
            t = pd.DataFrame([dict(val=v, **cell(x)) for v, x in gg.groupby("val")]).sort_values("val")
            t["devsafe"] = [safe(r) and not r["vacuous"] for r in t.to_dict("records")]
            print(f"  {hw} {arm}:"); print(t[["val", "nets", "delivered", "bad", "r", "r_ub", "pu", "pu_ub", "frac_oracle", "devsafe"]].round(4).to_string(index=False))
            if arm == "plugM":
                ok = t[t.devsafe]; v = float(ok.val.min()) if len(ok) else float(t.val.max()); feas = len(ok) > 0
            else:
                pref = t.devsafe.cumprod().astype(bool); ok = t[pref]; v = float(ok.val.max()) if len(ok) else float(t.val.min()); feas = len(ok) > 0
            res[arm] = v; res[arm + "_feasible"] = feas
        out[hw] = res
    print("TUNED =", {hw: {"plugM": v["plugM"], "cut": v["cut"]} for hw, v in out.items()})
    print("feasible:", {hw: {k: v[k] for k in v if k.endswith("feasible")} for hw, v in out.items()})


def main(df):
    n0 = len(df); df = df.drop_duplicates("run").copy(); df["blk"] = df.block.str[-1]
    if len(df) != n0: print(f"note: dropped {n0 - len(df)} duplicate run rows")
    for b, n in EXPECT.items():
        got = df[df.blk == b].groupby(["hw", "arm", "cfg"]).ngroups; nets = df[df.blk == b].groupby(["hw", "arm", "cfg"]).size()
        assert got == n, (b, got, n); assert (nets == 32).all(), (b, nets[nets != 32])
    print(f"tasks: {len(df)} (expected {sum(EXPECT.values()) * 32})"); assert len(df) == sum(EXPECT.values()) * 32
    assert (df.epoch_clamped == 0).all()
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
    cols = ["delivered", "bad", "r", "r_ub", "users_bad", "pu", "pu_ub", "pu_req", "nets_with_bad", "nets_zero", "frac_oracle", "paths_bad_pct"]

    # ---------------- Block U
    U = df[df.blk == "U"]; tu = table(U, ["hw", "arm", "cfg"]); print("\nBLOCK U"); print(tu[["hw", "arm", "cfg"] + cols + ["lat"]].round(4).to_string(index=False))
    cu = tu[tu.arm.isin(["bg", "kg", "ag2t"])]; ok = all(safe(r) for r in cu.to_dict("records"))
    verdict("U1 (primary) corrected-level guards bg, kg, ag2t SAFE on every hw (12 cells)", ok,
            f"bad {cu.bad.sum()} in {cu.delivered.sum()}; users_bad {cu.users_bad.sum()} of {cu.users.sum()}; max pu_ub {cu.pu_ub.max():.4f}; max r_ub {cu.r_ub.max():.4f}", cu)
    diffs = []
    for a in ("bg", "kg", "ag2t"):
        for d in paired_diff(U, a + "L", a): diffs.append((a, d))
    worst = max(d["diff"] for _, d in diffs)
    verdict("U2 (secondary) the correction costs <= 2 points of oracle throughput for every arm and hw (legacy - corrected)", worst <= 2.0,
            "; ".join(f"{a} {d['key']}: {d['diff']:+.2f} [{d['lo']:+.2f}, {d['hi']:+.2f}]" for a, d in diffs))
    bu = tu[tu.arm.isin(["plugM", "cut"])]; unsafe = [f"{r['hw']} {r['arm']}" for r in bu.to_dict("records") if not safe(r)]
    print(f"U3 (secondary, prediction) at their dev-tuned settings, at least one baseline (plugM or cut) is NOT SAFE on some hw: "
          f"{'CONFIRMED' if unsafe else 'NOT CONFIRMED'} (not SAFE: {unsafe or 'none'})")
    print("U4 (secondary, two-sided) matched-risk throughput, ag2t - plugM and kg - plugM (points of oracle, 90% CI), on hw where plugM is SAFE:")
    for hw in sorted(U.hw.unique()):
        r = bu[(bu.hw == hw) & (bu.arm == "plugM")].to_dict("records")[0]
        if not safe(r): print(f"   {hw}: plugM not SAFE, comparison not at matched safety"); continue
        for a in ("ag2t", "kg"):
            d = paired_diff(U[U.hw == hw], a, "plugM")[0]; print(f"   {hw} {a} - plugM: {d['diff']:+.2f} [{d['lo']:+.2f}, {d['hi']:+.2f}]")
    p = tu[tu.arm == "plug"]; print("U5 (descriptive) plug-in rule without margin:", "; ".join(f"{r['hw']} r {100*r['r']:.2f}% pu {100*r['pu']:.2f}%" for r in p.to_dict("records")))

    # ---------------- Block R
    R = df[df.blk == "R"]; tr = table(R, ["hw", "cfg", "arm"]); print("\nBLOCK R"); print(tr[["hw", "cfg", "arm"] + cols + ["phi_true", "phi_decl"]].round(4).to_string(index=False))
    iid = tr[~tr.cfg.str.endswith("_a")]
    c1 = iid[iid.arm.isin(["kgO", "ag2tO"])]
    verdict("R1 (primary) oracle-declared phi (kgO, ag2tO) SAFE in every iid-noise cell (48 cells)", all(safe(r) for r in c1.to_dict("records")),
            f"bad {c1.bad.sum()}; not SAFE: {[(r['hw'], r['cfg'], r['arm']) for r in c1.to_dict('records') if not safe(r)] or 'none'}", c1)
    rec = ["kgR", "ag2tR", "kgRp", "ag2tRp"]
    c2 = iid[iid.arm.isin(rec) & iid.cfg.str.match(r"n0\.0(33|75)_")]
    verdict("R2 (primary) recipe-declared arms SAFE at ICFO levels (rel 0.033, 0.075; homogeneous and heterogeneous; 64 cells)",
            all(safe(r) for r in c2.to_dict("records")), f"bad {c2.bad.sum()}; not SAFE: {[(r['hw'], r['cfg'], r['arm']) for r in c2.to_dict('records') if not safe(r)] or 'none'}", c2)
    c3 = iid[iid.arm.isin(rec) & iid.cfg.str.startswith("n0.184_")]
    verdict("R3 (primary) recipe-declared arms SAFE at the USTC level (rel 0.184; homogeneous and heterogeneous; 32 cells)",
            all(safe(r) for r in c3.to_dict("records")), f"bad {c3.bad.sum()}; not SAFE: {[(r['hw'], r['cfg'], r['arm']) for r in c3.to_dict('records') if not safe(r)] or 'none'}", c3)
    c4 = iid[iid.arm.isin(["kg", "ag2t", "bg"]) & iid.cfg.str.startswith("n0.184_") & iid.hw.isin(["ion2020", "ionproj"])]
    un = [(r["hw"], r["cfg"], r["arm"]) for r in c4.to_dict("records") if not safe(r)]
    print(f"R4 (secondary, prediction) undeclared guards at the USTC level on ion hardware are NOT SAFE in at least one cell: "
          f"{'CONFIRMED' if un else 'NOT CONFIRMED'} (not SAFE: {un or 'none'}; bad {c4.bad.sum()})")
    print("R5 (secondary) cost of the recipe on thin hardware: kgR - kg, ag2tR - ag2t (points of oracle, 90% CI), SiV, every iid level:")
    worst5 = 0.0
    for cfg in sorted(R[R.hw == "siv"].cfg.unique()):
        if cfg.endswith("_a"): continue
        for a in ("kg", "ag2t"):
            d = paired_diff(R[(R.hw == "siv") & (R.cfg == cfg)], a + "R", a)[0]; worst5 = min(worst5, d["diff"])
            print(f"   siv {cfg} {a}R - {a}: {d['diff']:+.2f} [{d['lo']:+.2f}, {d['hi']:+.2f}]")
    verdict("R5 bar: on SiV the fleet recipe costs no more than 3 points at every iid level", worst5 >= -3.0, f"worst {worst5:+.2f}")
    ar = tr[tr.cfg.str.endswith("_a") & (tr.hw == "ion2020")]; unsafe6 = [r["arm"] for r in ar.to_dict("records") if not safe(r)]
    print(f"R6 (secondary, prediction informed by the dev pilot) persistent (AR 0.9) noise at the USTC level breaks the model-based guard "
          f"on ion2020 for every arm, including the oracle per-epoch phi: {'CONFIRMED' if len(unsafe6) == len(ar) else 'NOT CONFIRMED'} "
          f"(not SAFE: {unsafe6})")
    print("R6 table (all hw):")
    print(tr[tr.cfg.str.endswith("_a")][["hw", "arm", "delivered", "bad", "pu", "pu_ub", "r_ub", "frac_oracle"]].round(4).to_string(index=False))
    print("R7 (descriptive) declared vs true phi (cell means):")
    print(tr[tr.arm.isin(["kgR", "kgRp", "kgO"])][["hw", "cfg", "arm", "phi_true", "phi_decl"]].round(3).to_string(index=False))

    # ---------------- Block O
    O = df[df.blk == "O"]; to = table(O, ["hw", "cfg"]); print("\nBLOCK O"); print(to[["hw", "cfg"] + cols + ["dec", "dec_viol"]].round(4).to_string(index=False))
    o1 = to[to.cfg.str.endswith("_orc")]
    verdict("O1 (primary) oracle-declared margin d = Delta SAFE (4 cells)", all(safe(r) for r in o1.to_dict("records")), f"bad {o1.bad.sum()}", o1)
    o2 = to[to.cfg.str.contains(r"_m(?:4|16|64|256)$")]
    verdict("O2 (primary) recipe-declared margin: per-user risk upper bound <= alpha + beta = 10% (16 cells; r reported, not part of the bar)",
            all(r["pu_ub"] <= ALPHA + BETA for r in o2.to_dict("records")),
            f"bad {o2.bad.sum()}; max pu_ub {o2.pu_ub.max():.4f}; max r_ub {o2.r_ub.max():.4f}; networks with d < Delta: {int(o2.dec_viol.sum())} of {32 * len(o2)}", o2)
    Ok = O[(O.dec_viol == 0) & O.cfg.str.contains(r"_m(?:4|16|64|256)$")]; tk = table(Ok, ["hw", "cfg"])
    verdict("O2b (secondary) in networks where the declared margin held (d >= Delta), the recipe arms are SAFE (16 cells)",
            all(safe(r) for r in tk.to_dict("records")), f"bad {tk.bad.sum()}; max pu_ub {tk.pu_ub.max():.4f}; max r_ub {tk.r_ub.max():.4f}", tk)
    o3 = to[(to.hw == "ion2020") & (to.cfg == "o0.044_m0")].to_dict("records")[0]
    print(f"O3 (secondary, prediction) undeclared Delta = 0.044 on ion2020 is NOT SAFE: {'CONFIRMED' if not safe(o3) else 'NOT CONFIRMED'} "
          f"(pu {100*o3['pu']:.2f}%, pu_ub {100*o3['pu_ub']:.2f}%, r_ub {100*o3['r_ub']:.3f}%)")
    print("O4 (descriptive) design curve: fraction of oracle by tomography points M:")
    print(to[["hw", "cfg", "frac_oracle", "dec"]].round(4).to_string(index=False))

    # ---------------- Block S
    S = df[df.blk == "S"]; ts = table(S, ["hw", "cfg", "arm"]); print("\nBLOCK S"); print(ts[["hw", "cfg", "arm"] + cols + ["lat"]].round(4).to_string(index=False))
    verdict("S1 (primary) bg, kg, ag2t SAFE under finite memory (27 cells)", all(safe(r) for r in ts.to_dict("records")),
            f"bad {ts.bad.sum()} in {ts.delivered.sum()}; max pu_ub {ts.pu_ub.max():.4f}", ts)


if __name__ == "__main__":
    mode, path = sys.argv[1], sys.argv[2]
    assert path.endswith("runs.csv"), path
    d = pd.read_csv(path)
    if mode == "tune": tune(d)
    else: main(d)
