"""Dev-pilot functional summary for Study 26 (dev data only; not confirmatory)."""
import sys, pandas as pd, numpy as np
import analyze_26 as A
df = pd.read_csv(sys.argv[1]).drop_duplicates("run"); df["blk"] = df.block.str[-1]
print("rows", len(df), "clamped", int(df.epoch_clamped.sum()))
cols = ["delivered", "bad", "r", "r_ub", "users_bad", "pu", "pu_ub", "nets_zero", "frac_oracle"]
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 600)
U = df[(df.blk == "U") & ~df.arm.isin(["plugM", "cut"])]
t = A.table(U, ["hw", "arm"]); print("\nU"); print(t[["hw", "arm"] + cols].round(4).to_string(index=False))
R = df[df.blk == "R"]; t = A.table(R, ["hw", "cfg", "arm"]); t["SAFE"] = [A.safe(r) for r in t.to_dict("records")]
print("\nR"); print(t[["hw", "cfg", "arm"] + cols + ["phi_true", "phi_decl", "SAFE"]].round(4).to_string(index=False))
O = df[df.blk == "O"]; t = A.table(O, ["hw", "cfg"]); print("\nO"); print(t[["hw", "cfg"] + cols + ["dec", "dec_viol"]].round(4).to_string(index=False))
S = df[df.blk == "S"]; t = A.table(S, ["hw", "cfg", "arm"]); print("\nS"); print(t[["hw", "cfg", "arm"] + cols + ["lat"]].round(4).to_string(index=False))
