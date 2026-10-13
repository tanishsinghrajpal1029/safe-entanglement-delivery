"""Study 35B (Delft, fully heralded delivered states, paper Fig. 4): extract exactly the fields the locked analysis needs.
Locked with PREREG_35B.md. Needs h5py + numpy (run on the Mac).
  Dry run (names/types/shapes only):  python3 extract_35b.py DATA_DIR --check
  Real (only after PREREG_35B.md is committed publicly):  python3 extract_35b.py DATA_DIR delft_extract_35b.json
"""
import json, os, sys
import numpy as np
import h5py
from extract_35 import s, describe          # same helpers as Study 35 (locked)


def extract(root):
    f4 = os.path.join(root, "Figure4_FigureS6")
    out = {"source": "doi:10.4121/983e4771-1d12-457f-a98e-fab3a2959288.v1, Figure4_FigureS6/ (main text Fig. 4, no PSB correction)"}
    with h5py.File(os.path.join(f4, "dataset_processed_RO_corrected_NoPSBcorrection.h5"), "r") as h:
        out["ssro_outcome_tick_labels"] = s(h["ssro_outcome"].attrs.get("tick_labels"))
        out["state_generated_tick_labels"] = s(h["state_generated"].attrs.get("tick_labels"))
        out["states"] = {}
        for st in sorted(k for k in h.keys() if k.startswith("state_") and k != "state_generated"):
            g = h[st]; d = {"fidelity": s(g.attrs.get("fidelity")), "u_fidelity": s(g.attrs.get("u_fidelity")), "datasets": {}}
            for k in sorted(g.keys()):
                ds = g[k]; rec = ds[()]
                d["datasets"][k] = {"N": s(np.asarray(rec["N"])), "p": s(np.asarray(rec["p"])), "u_p": s(np.asarray(rec["u_p"])),
                                    **{a: s(ds.attrs.get(a)) for a in ("correlation", "u_correlation", "node1_readout_basis",
                                                                       "node2_readout_basis", "combined_readout")}}
            out["states"][st] = d
    for name in ("correlation_results", "total_result_sweep", "total_cps_sweep"):
        out[name] = np.load(os.path.join(f4, name + ".npy"), allow_pickle=False).tolist()
    return out


if __name__ == "__main__":
    root = os.path.expanduser(sys.argv[1]); d = extract(root)
    if sys.argv[2:3] == ["--check"]:
        describe(d); print("\nDRY RUN OK: all fields found (no values printed).")
    else:
        json.dump(d, open(sys.argv[2], "w"), indent=1); print(f"wrote {sys.argv[2]}")
