"""Robust merge of Study 25 pilot shards written before the column fix: rows of campaign arms carry two extra trailing
fields (camp_muF_err, camp_sdF_ratio) that other rows lack. Usage: python3 merge_robust.py <outdir>"""
import csv, glob, hashlib, sys
import pandas as pd
EX = ["camp_muF_err", "camp_sdF_ratio"]; rows = []
for f in sorted(glob.glob(f"{sys.argv[1]}/shard_*.csv")):
    with open(f) as fh:
        r = csv.reader(fh); h = next(r)
        for row in r:
            if len(row) == len(h): rows.append(dict(zip(h, row)))
            elif len(row) == len(h) + 2 and EX[0] not in h: rows.append(dict(zip(h + EX, row)))
            elif len(row) == len(h) - 2 and h[-2:] == EX: rows.append(dict(zip(h[:-2], row)))
            else: raise SystemExit(f"unexpected row length {len(row)} vs {len(h)} in {f}")
M = pd.DataFrame(rows).drop_duplicates("run")
for c in M.columns:
    try: M[c] = pd.to_numeric(M[c])
    except (ValueError, TypeError): pass
out = f"{sys.argv[1]}/runs.csv"; M.to_csv(out, index=False)
print(f"merged -> {len(M)} rows; runs.csv sha256 {hashlib.sha256(open(out, 'rb').read()).hexdigest()}")
