"""LOCKED analysis for C1 (README_C1.md). Usage: python3 analyze_c1.py des_c1_psc"""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]; R = pd.read_csv(f"{D}/runs.csv"); BIG = 200; rng = np.random.default_rng(0); rows = []
pd.set_option("display.width", 260); pd.set_option("display.max_rows", 400)


def boot(d, b):
    I = rng.integers(0, len(d), (4000, len(d))); return 100 * float(np.quantile(b[I].sum(1) / np.maximum(d[I].sum(1), 1), .95))


for (blk, c, g, mem, law), x in R.groupby(["block", "cell", "g", "mem", "law"]):
    d = x.delivered.values; b = x.bad.values; pd_ = x.post_fault_delivered.values; pb = x.post_fault_bad.values
    rows.append(dict(block=blk, cell=c, g=f"{g:.0e}", mem=mem, law=law, paths=len(x), delivered=int(d.sum()), bad=int(b.sum()),
                     r_pct=100 * b.sum() / max(d.sum(), 1), boot95_pct=boot(d, b), top_path_bad=int(b.max()),
                     frac_oracle=x.qual.sum() / max(x.oracle_qual.sum(), 1),
                     post_fault_deliv=int(pd_.sum()), post_fault_r_pct=100 * pb.sum() / max(pd_.sum(), 1),
                     post_fault_boot95=boot(pd_, pb) if blk == "C" else np.nan))
G = pd.DataFrame(rows); print(G.round(4).to_string(index=False)); G.to_csv(f"{D}/c1_groups.csv", index=False)
print("tasks:", len(R), "(expected 16384)")
A = G[(G.block == "A") & (G.delivered >= BIG)]; v = A[A.r_pct > 1]
print(f"\nC-A1 (primary) frozen controller, core block: r<=1% in every group with >={BIG} deliveries: {len(v)} violations of {len(A)} -> {'PASS' if len(v) == 0 and len(A) else 'FAIL'}")
if len(v): print(v[["cell", "g", "mem", "delivered", "bad", "r_pct", "boot95_pct", "top_path_bad"]].round(3).to_string(index=False))
v2 = A[A.boot95_pct > 1]
print(f"C-A2 (stricter) path-bootstrap 95% upper <=1%: {len(v2)} exceed of {len(A)} -> {'PASS' if len(v2) == 0 and len(A) else 'FAIL'}")
if len(v2): print(v2[["cell", "g", "mem", "delivered", "bad", "r_pct", "boot95_pct", "top_path_bad"]].round(3).to_string(index=False))
small = G[(G.block == "A") & (G.delivered < BIG)]; print(f"   (A groups with < {BIG} deliveries, not tested: {len(small)}: {sorted(set(small.cell))})")
B = G[(G.block == "B") & (G.delivered >= BIG)]; vb = B[B.r_pct > 1]
print(f"C-B fleet-law stresses: r<=1% in every group: {len(vb)} violations of {len(B)} -> {'PASS' if len(vb) == 0 and len(B) else 'FAIL'}")
if len(vb): print(vb[["cell", "law", "delivered", "bad", "r_pct", "boot95_pct"]].round(3).to_string(index=False))
C = G[(G.block == "C") & (G.post_fault_deliv >= BIG)]
print(f"C-C (exploratory) unannounced 2-sd link fault, post-fault r by cell (groups with >={BIG} post-fault deliveries):")
print(C[["cell", "post_fault_deliv", "post_fault_r_pct", "post_fault_boot95", "r_pct"]].round(3).to_string(index=False))
print("\nD (descriptive) fraction of oracle, block A, by cell x memory (mean over g):")
print(G[G.block == "A"].pivot_table(index="cell", columns="mem", values="frac_oracle", aggfunc="mean").round(3).to_string())
