"""LOCKED analysis for C2 (README_C2.md). Usage: python3 analyze_c2.py des_c2_psc"""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); BIG = 200; rng = np.random.default_rng(0); rows = []
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400)


def boot(d, b):
    if len(d) == 0: return np.nan
    I = rng.integers(0, len(d), (4000, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


for (blk, c, g, mem, law), x in R.groupby(["block", "cell", "g", "mem", "law"]):
    d = x.delivered.values; b = x.bad.values; f = x[x.faulted == 1]
    rows.append(dict(block=blk, cell=c, g=f"{g:.0e}", mem=mem, law=law, paths=len(x), faulted_paths=len(f), delivered=int(d.sum()), bad=int(b.sum()),
                     r_pct=100 * b.sum() / max(d.sum(), 1), boot95_pct=boot(d, b), top_path_bad=int(b.max()),
                     frac_oracle=x.qual.sum() / max(x.oracle_qual.sum(), 1),
                     post_fault_deliv=int(x.post_fault_delivered.sum()), post_fault_r_pct=100 * x.post_fault_bad.sum() / max(x.post_fault_delivered.sum(), 1)))
G = pd.DataFrame(rows); print(G.round(4).to_string(index=False)); G.to_csv(f"{D}/c2_groups.csv", index=False)
print("tasks:", len(R), "(expected 16640)")


def test(name, sub, col="r_pct"):
    x = sub[sub.delivered >= BIG]; v = x[x[col] > 1]
    print(f"\n{name}: {len(v)} exceed 1% of {len(x)} -> {'PASS' if len(v) == 0 and len(x) else 'FAIL'}")
    if len(v): print(v[["cell", "g", "mem", "law", "delivered", "bad", "r_pct", "boot95_pct", "top_path_bad"]].round(3).to_string(index=False))
    sm = sub[sub.delivered < BIG]
    if len(sm): print(f"   (not tested, < {BIG} deliveries: {len(sm)} groups: {sorted(set(sm.cell))})")


test("C2-A1 (primary) core block, r<=1% every group", G[G.block == "A"])
test("C2-A2 (stricter) core block, path-bootstrap 95% upper <=1%", G[G.block == "A"], "boot95_pct")
test("C2-B fleet-law stresses, r<=1% every group", G[G.block == "B"])
test("C2-R rare faults (5% of paths, matching the declared fault model), r<=1% every cell", G[G.block == "R"])
C = G[G.block == "C"]
print("\nC2-C (exploratory) always-fault worst case, post-fault r by cell:")
print(C[["cell", "post_fault_deliv", "post_fault_r_pct", "r_pct"]].round(3).to_string(index=False))
print("\nD (descriptive) fraction of oracle, block A, by cell x memory (mean over g):")
print(G[G.block == "A"].pivot_table(index="cell", columns="mem", values="frac_oracle", aggfunc="mean").round(3).to_string())
