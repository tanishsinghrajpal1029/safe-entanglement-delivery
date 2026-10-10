"""Generic Bridges-2 array runner for Study 18C sweeps (no NetSquid needed; numpy/pandas/scipy only).

Each array element runs one shard of a task list with a local multiprocessing pool sized to the allocation.
    python3 psc_array_runner.py --module drift_queue_des_v10 --func run_one --tasks tasks_v10.jsonl \
        --outdir des_v10_psc --shard $SLURM_ARRAY_TASK_ID --nshards 40 --workers $SLURM_CPUS_PER_TASK
Task file: one JSON list per line (the positional args of <func>, passed as a single tuple).
Output: <outdir>/shard_XXX.csv (append; rows must carry a unique 'run' id, already-finished ids are skipped),
        <outdir>/shard_XXX_meta.json (code sha256s, host, timing). Merge with:  python3 psc_array_runner.py --merge <outdir>
"""
import argparse, hashlib, importlib, json, multiprocessing as mp, os, platform, socket, sys, time
from pathlib import Path


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _call(args):
    mod, fn, t = args
    return getattr(importlib.import_module(mod), fn)(tuple(t))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--module"); ap.add_argument("--func", default="run_one"); ap.add_argument("--tasks")
    ap.add_argument("--outdir"); ap.add_argument("--shard", type=int, default=0); ap.add_argument("--nshards", type=int, default=1)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1)); ap.add_argument("--merge")
    a = ap.parse_args()
    import pandas as pd
    if a.merge:
        d = Path(a.merge); fs = sorted(d.glob("shard_*.csv"))
        M = pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates("run")
        M.to_csv(d / "runs.csv", index=False)
        print(f"merged {len(fs)} shards -> {len(M)} rows; runs.csv sha256 {sha(d / 'runs.csv')}"); return
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    mod = importlib.import_module(a.module)
    tasks = [json.loads(l) for l in open(a.tasks) if l.strip()]
    mine = tasks[a.shard::a.nshards]
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True); csv = out / f"shard_{a.shard:03d}.csv"
    done = set(pd.read_csv(csv).run) if csv.exists() else set()
    rid = getattr(mod, "run_id", None)
    if rid: mine = [t for t in mine if rid(tuple(t)) not in done]
    t0 = time.time()
    meta = dict(module=a.module, module_sha=sha(mod.__file__), runner_sha=sha(__file__), tasks_sha=sha(a.tasks),
                shard=a.shard, nshards=a.nshards, n=len(mine), workers=a.workers, host=socket.gethostname(),
                python=platform.python_version(), start=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    print(json.dumps(meta), flush=True)
    with mp.Pool(a.workers) as pool:
        for k, row in enumerate(pool.imap_unordered(_call, [(a.module, a.func, t) for t in mine], chunksize=1), 1):
            pd.DataFrame([row]).to_csv(csv, mode="a", header=not csv.exists(), index=False)
            if k % 50 == 0 or k == len(mine): print(f"  {k}/{len(mine)} {time.time() - t0:.0f}s", flush=True)
    meta["elapsed_s"] = round(time.time() - t0, 1)
    (out / f"shard_{a.shard:03d}_meta.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
