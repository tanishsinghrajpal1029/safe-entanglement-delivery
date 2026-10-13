"""Delft (Stolk et al. 2024) data: STRUCTURE ONLY, before any pre-registration.
Prints file names, HDF5 group/dataset names, shapes, dtypes and attribute NAMES (not values);
.npy/.npz shapes and dtypes. No data values or statistics are read or printed.
Usage (Mac terminal, a Python with h5py + numpy, e.g. anaconda):
  python3 dump_structure_35.py ~/Documents/Independent-Study/quantum_grid_router/DataRepository > structure_35.txt
"""
import os, sys
import numpy as np
import h5py

root = os.path.expanduser(sys.argv[1])
for dp, dn, fn in sorted(os.walk(root)):
    dn[:] = sorted(d for d in dn if not d.startswith(".") and d != "output")
    for f in sorted(fn):
        p = os.path.join(dp, f); rel = os.path.relpath(p, root)
        if f.endswith(".h5"):
            print(f"== {rel}  ({os.path.getsize(p)} bytes)")
            with h5py.File(p, "r") as h:
                print("   root attr names:", sorted(h.attrs.keys()))
                def v(name, obj):
                    if isinstance(obj, h5py.Dataset):
                        print(f"   {name}  shape={obj.shape} dtype={obj.dtype} attr names={sorted(obj.attrs.keys())}")
                    else:
                        print(f"   [{name}] attr names={sorted(obj.attrs.keys())}")
                h.visititems(v)
        elif f.endswith(".npy"):
            a = np.load(p, mmap_mode="r", allow_pickle=False)
            print(f"== {rel}  shape={a.shape} dtype={a.dtype}")
        elif f.endswith(".npz"):
            with np.load(p, allow_pickle=False) as z:
                print(f"== {rel}  arrays:", {k: (z[k].shape, str(z[k].dtype)) for k in z.files})
