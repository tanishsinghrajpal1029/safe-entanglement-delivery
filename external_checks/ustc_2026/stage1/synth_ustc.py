"""synthetic USTC-like workbooks: KDD contrasts exp(-t/50) and exp(-t/80) ms; XX0 = 0.8, ZZ = 0.9; F decays as the model says;
QBER sets binomial (no drift) with n = 4.05e5/201."""
import sys, os, math, numpy as np, openpyxl
d = sys.argv[1]; os.makedirs(d, exist_ok=True); rng = np.random.default_rng(3)
def wb(path, sheets):
    w = openpyxl.Workbook(); w.remove(w.active)
    for name, rows in sheets.items():
        ws = w.create_sheet(name)
        for r in rows: ws.append(list(r))
    w.save(path)
tA = np.linspace(0, 60, 11); tB = np.linspace(0, 90, 16)
wb(f"{d}/Fig_S2b.xlsx", {"Fig_S2b_Alice_KDD": [("t", "c", "s")] + [(t, 0.95 * math.exp(-t / 50), 0.01) for t in tA],
                         "Fig_S2b_Bob_KDD": [("t", "c", "s")] + [(t, 0.93 * math.exp(-t / 80), 0.01) for t in tB]})
ts = [0, 10, 20, 40, 60]; F0 = (1 + 0.9 + 2 * 0.8) / 4
wb(f"{d}/Fig_3d.xlsx", {"Fig_3d_alpha=17%": [("t", "F", "s")] + [(t, F0 + 0.4 * (math.exp(-t / 50 - t / 80) - 1) + rng.normal(0, .005), 0.01) for t in ts],
                        "Fig_3d_inset": [("t", "XX", "s", "ZZ", "s")] + [(t, 0.8 * math.exp(-t / 50 - t / 80), .01, .9, .01) for t in ts]})
n = 4.05e5 / 201; q = rng.binomial(round(n), 0.03, 201) / round(n) * 100
wb(f"{d}/Fig_S8.xlsx", {"Fig_S8": [("i", "chsh", "q")] + [(i, 2.6 + rng.normal(0, .02), q[i]) for i in range(201)]})
