"""Study 35 (Delft) extraction: copy exactly the fields the locked analysis needs from the authors' files into JSON.
Locked with PREREG_35.md. Needs h5py + numpy (run on the Mac).

  Dry run (prints field names, types and shapes only; no values):
    python3 extract_35.py DATA_DIR --check
  Real extraction (only after PREREG_35.md is committed publicly):
    python3 extract_35.py DATA_DIR delft_extract_35.json

DATA_DIR = ~/Documents/Independent-Study/quantum_grid_router/DataRepository
"""
import json, os, sys
import numpy as np
import h5py


def s(x):
    if isinstance(x, bytes): return x.decode("utf-8", "replace")
    if isinstance(x, np.ndarray): return [s(v) for v in x.tolist()] if x.dtype.kind in "SUO" else x.tolist()
    if isinstance(x, (list, tuple)): return [s(v) for v in x]
    if isinstance(x, np.generic): return x.item()
    return x


def extract(root):
    f3 = os.path.join(root, "Figure3")
    out = {"source": "doi:10.4121/983e4771-1d12-457f-a98e-fab3a2959288.v1, Figure3/"}
    with h5py.File(os.path.join(f3, "dataset_processed_RO_corrected.h5"), "r") as h:
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
    out["correlation_results"] = np.load(os.path.join(f3, "correlation_results.npy"), allow_pickle=False).tolist()
    out["total_result_sweep"] = np.load(os.path.join(f3, "total_result_sweep.npy"), allow_pickle=False).tolist()
    return out


def describe(x, pre=""):
    if isinstance(x, dict):
        for k, v in x.items(): print(f"{pre}{k}: {type(v).__name__}"); describe(v, pre + "   ")
    elif isinstance(x, list):
        a = np.asarray(x, dtype=object)
        print(f"{pre}(list, shape {np.shape(x) if all(not isinstance(v, str) for v in np.ravel(a)) else len(x)})")


if __name__ == "__main__":
    root = os.path.expanduser(sys.argv[1]); d = extract(root)
    if sys.argv[2:3] == ["--check"]:
        describe(d); print("\nDRY RUN OK: all fields found (no values printed).")
    else:
        json.dump(d, open(sys.argv[2], "w"), indent=1); print(f"wrote {sys.argv[2]}")
