"""Rebuilds the S3D numbers of manuscript v0.9 (Table 10, the 'Other topologies' paragraph and the Table VIII row)
from the three locked analysis outputs of the topology studies. It reads records only; nothing is simulated.

Usage (from the repository root):  python3 revision_v0.9/s3d_table10.py revision_v0.9/s3d_analysis
The analysis outputs are copies from https://github.com/tanishsinghrajpal1029/quantum-3d-network (release v1.0.0,
commit 724252b, DOI 10.5281/zenodo.23467683), path sim/evidence/analysis_3d{1,2,3}.txt; SHA256SUMS lists their hashes.
"""
import hashlib, os, re, sys

D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "s3d_analysis")
STUDIES = (("S3D-1", "analysis_3d1.txt"), ("S3D-2", "analysis_3d2.txt"), ("S3D-3", "analysis_3d3.txt"))


def umax_values(text):
    """U_max column of the descriptive per-hop table (header row contains 'umax'; it is the third column from the end)."""
    vals, lines = [], text.splitlines()
    for i, l in enumerate(lines):
        if re.search(r"\bumax\b", l) and "s1" in l:
            k = l.split().index("umax") - len(l.split())
            for r in lines[i + 1:]:
                if not r.strip() or r.startswith("=="):
                    break
                t = r.split()
                try:
                    vals.append(float(t[k]))
                except (ValueError, IndexError):
                    pass
    return vals


tot_cells = tot_del = tot_bad = tot_harm = 0
print(f"{'Study':6s} {'cells':>5s} {'harmed nets':>11s} {'bad/guarded deliveries':>24s} {'U_max':>8s}  sha256 (first 16)")
for name, f in STUDIES:
    raw = open(os.path.join(D, f), "rb").read(); t = raw.decode("utf-8")
    cells = re.findall(r"harmed networks (\d+)/(\d+).*?bad pairs (\d+)/(\d+)", t)
    harm = sum(int(c[0]) for c in cells); nets = {int(c[1]) for c in cells}
    bad = sum(int(c[2]) for c in cells); dl = sum(int(c[3]) for c in cells); u = umax_values(t)
    assert nets == {32}, nets
    tot_cells += len(cells); tot_del += dl; tot_bad += bad; tot_harm += harm
    print(f"{name:6s} {len(cells):5d} {harm:11d} {bad:>10d} / {dl:>11,d} {min(u):>3.0f}-{max(u):<4.0f}  {hashlib.sha256(raw).hexdigest()[:16]}")
print(f"{'total':6s} {tot_cells:5d} {tot_harm:11d} {tot_bad:>10d} / {tot_del:>11,d}")
a = re.search(r"ion2020: 3D ([\d.]+), 2D 11x11 ([\d.]+)", open(os.path.join(D, "analysis_3d1.txt")).read())
b = re.search(r"ionproj: 3D ([\d.]+), 2D 11x11 ([\d.]+)", open(os.path.join(D, "analysis_3d1.txt")).read())
print(f"S3D-1 detection (alarm rate, gated check, offset 0.044; 32 networks): ion2020 cube {a[1]} vs 11x11 {a[2]}"
      f" ({round(float(a[1]) * 32)} vs {round(float(a[2]) * 32)} of 32); ionproj {b[1]} vs {b[2]}"
      f" ({round(float(b[1]) * 32)} vs {round(float(b[2]) * 32)} of 32)")
