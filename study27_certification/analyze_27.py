"""Study 27 analysis (locked before the confirmatory run). Usage: python analyze_27.py <runs.csv>
Certificate validity (Theorem C1): a user (or a network-pooled certificate) is VIOLATED if its certificate was ever above the
true running average fidelity of its kept pairs. Bars use one-sided 95% Clopper-Pearson upper bounds."""
import os, sys
import numpy as np
import pandas as pd
from scipy.stats import beta

ALPHA = 0.05; PS = ("p05", "p10", "p20"); EXPECT_CELLS = 4 * 4 * 2 * 3


def cp_ub(k, n, conf=0.95):
    return 1.0 if n == 0 else (1.0 if k >= n else float(beta.ppf(conf, k + 1, n - k)))


def main(df):
    n0 = len(df); df = df.drop_duplicates("run").copy()
    if len(df) != n0: print(f"note: dropped {n0 - len(df)} duplicate rows")
    cells = df.groupby(["hw", "arm", "cfg"]).size(); assert len(cells) == EXPECT_CELLS, len(cells); assert (cells == 32).all()
    assert (df.epoch_clamped == 0).all(); print(f"tasks: {len(df)} (expected {EXPECT_CELLS * 32})"); assert len(df) == EXPECT_CELLS * 32
    df["scen"] = df.cfg.str.split("|").str[0]; df["traf"] = df.cfg.str.split("|").str[1]
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400)
    # ---- validity (only ELIGIBLE users can violate: a certificate that never rose above 0 cannot exceed a fidelity >= 0)
    rng = np.random.default_rng(2027)

    def boot_ub(g, num, den, nb=2000):
        n = g[num].to_numpy(float); d = g[den].to_numpy(float)
        if d.sum() == 0 or n.sum() == 0: return 0.0
        idx = rng.integers(0, len(n), (nb, len(n))); dd = d[idx].sum(1)
        return float(np.quantile(np.where(dd > 0, n[idx].sum(1) / np.maximum(dd, 1), 0.0), 0.95))

    rows = []
    for (hw, arm, cfg), g in df.groupby(["hw", "arm", "cfg"]):
        r = dict(hw=hw, arm=arm, cfg=cfg, delivered=int(g.delivered.sum()), bad=int(g.bad.sum()),
                 r=g.bad.sum() / max(g.delivered.sum(), 1), pu=g.users_bad.sum() / g.users_total.sum())
        for p in PS:
            r[f"{p}_uv"] = int(g[f"{p}_u_viol"].sum()); r[f"{p}_ue"] = int(g[f"{p}_u_elig"].sum())
            r[f"{p}_nv"] = int(g[f"{p}_net_viol"].sum()); r[f"{p}_ne"] = int(g[f"{p}_net_elig"].sum())
        rows.append(r)
    t = pd.DataFrame(rows); print(t.round(4).to_string(index=False))
    res1 = {}
    for p in PS:
        uv, ue = int(df[f"{p}_u_viol"].sum()), int(df[f"{p}_u_elig"].sum()); res1[p] = (uv, ue, boot_ub(df, f"{p}_u_viol", f"{p}_u_elig"))
    ok1 = all(v[2] <= ALPHA for v in res1.values()) and all(v[1] > 0 for v in res1.values())
    print("C1 (primary) per-user certificate validity over all 96 cells: violated / ELIGIBLE users (certificate ever > 0), one-sided 95% "
          "cluster-bootstrap upper bound over networks <= 5%, for each p: " + ("PASS" if ok1 else "FAIL") + " "
          + "; ".join(f"{p}: {uv}/{ue} (ub {ub:.4f})" for p, (uv, ue, ub) in res1.items()))
    cellrates = [(r[f"{p}_uv"] / r[f"{p}_ue"], r["hw"], r["arm"], r["cfg"], p, r[f"{p}_uv"], r[f"{p}_ue"])
                 for r in t.to_dict("records") for p in PS if r[f"{p}_ue"] >= 20]
    cellrates.sort(reverse=True)
    ok1b = all(c[0] <= 2 * ALPHA for c in cellrates)
    print(f"C1b (secondary) in every cell and p with >= 20 eligible users, the violation rate is <= 10% (2 alpha; cell-level noise allowance): "
          f"{'PASS' if ok1b else 'FAIL'} (cells checked {len(cellrates)}; worst {cellrates[:3]})")
    res2 = {p: (int(df[f"{p}_net_viol"].sum()), int(df[f"{p}_net_elig"].sum())) for p in PS}
    ok2 = all(cp_ub(nv, ne) <= ALPHA for nv, ne in res2.values() if ne > 0) and all(ne > 0 for _, ne in res2.values())
    print(f"C2 (primary) network-pooled certificate validity: violated / eligible networks, Clopper-Pearson 95% upper bound <= 5%, each p: "
          f"{'PASS' if ok2 else 'FAIL'} " + "; ".join(f"{p}: {nv}/{ne} (ub {cp_ub(nv, ne):.4f})" for p, (nv, ne) in res2.items()))
    br = t[(t.pu > ALPHA) | (t.r > 0.01)]
    print(f"C3 (descriptive) cells where the model-based control layer is NOT safe (per-user risk > 5% or r > 1%): {len(br)}; their certificate "
          f"violations (each p): " + "; ".join(f"{p}: {int(br[f'{p}_uv'].sum())}/{int(br[f'{p}_ue'].sum())} users, {int(br[f'{p}_nv'].sum())}/{int(br[f'{p}_ne'].sum())} networks" for p in PS))
    print("   broken-control cells:", [(r["hw"], r["arm"], r["cfg"], round(r["pu"], 3), round(r["r"], 3)) for r in br.to_dict("records")])
    # ---- tightness (descriptive): observed vs the certificate predicted by cert.py for Werner-like pairs at the observed counts
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from cert import Certifier
    print("C4 (descriptive) tightness, users with >= 500 kept pairs (hot users), arm kg, no stressor, by hw and p: mean true, mean certificate, gap:")
    for p in PS:
        for hw in sorted(df.hw.unique()):
            sel = df[(df.hw == hw) & (df.scen == "-") & (df.traf == "hot") & (df.arm == "kg") & (df[f"{p}_u_big"] > 0)]
            if len(sel): print(f"   {p} {hw}: networks {len(sel)}, true {sel[f'{p}_u_big_F'].mean():.4f}, certificate {sel[f'{p}_u_big_L'].mean():.4f}, gap {(sel[f'{p}_u_big_F'] - sel[f'{p}_u_big_L']).mean():.4f}")
    print("   floor (cert.py, alpha 0.05): kept pairs needed to certify >= 0.9 with perfect pairs:",
          {p: next(K for K in range(1, 10 ** 6, 1) if Certifier(float(p[1:]) / 100, ALPHA).lower(0, K) >= 0.9) for p in PS})
    print("C5 (descriptive) network-pooled certificate vs truth, p = 0.1, by hw, scenario, arm (certificates < 0 shown as 0):")
    d = df.assign(netL=df.p10_net_L.clip(lower=0)).groupby(["hw", "scen", "arm"]).agg(
        netL=("netL", "mean"), netF=("p10_net_F", "mean"), kept_qual=("p10_kept_qual", "sum"), deliv=("delivered", "sum"), bad=("bad", "sum")).reset_index()
    print(d.round(4).to_string(index=False))
    base = df["p05_kept_qual"].sum()
    print("C6 (descriptive) certification cost: kept qualified pairs relative to p = 0.05:", {p: round(float(df[f"{p}_kept_qual"].sum() / base), 4) for p in PS})


if __name__ == "__main__":
    path = sys.argv[1]; assert path.endswith("runs.csv"), path
    main(pd.read_csv(path))
