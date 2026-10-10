#!/bin/bash
#SBATCH --job-name=s18c
#SBATCH --partition=RM-shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=02:00:00
#SBATCH --output=s18c-logs/s18c_%A_%a.out
#SBATCH --error=s18c-logs/s18c_%A_%a.err
# Study 18C sweep array. Cost per element <= 32 cores x 2 h = 64 SU (RM-shared bills per core-hour).
# Required:  --export=ALL,S18C_DIR=<.../18c_drift_frontier>,PY=<python with numpy/pandas/scipy>,
#            S18C_MODULE=<module>,S18C_TASKS=<tasks.jsonl>,S18C_OUT=<outdir>,S18C_NSHARDS=<N = array size>
set -euo pipefail
: "${S18C_DIR:?}"; : "${PY:?}"; : "${S18C_MODULE:?}"; : "${S18C_TASKS:?}"; : "${S18C_OUT:?}"; : "${S18C_NSHARDS:?}"
cd "$S18C_DIR"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
"$PY" psc_array_runner.py --module "$S18C_MODULE" --tasks "$S18C_TASKS" --outdir "$S18C_OUT" \
  --shard "$SLURM_ARRAY_TASK_ID" --nshards "$S18C_NSHARDS" --workers "$SLURM_CPUS_PER_TASK"
