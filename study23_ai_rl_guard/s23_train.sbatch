#!/bin/bash
#SBATCH --job-name=s23train
#SBATCH --partition=RM-shared
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=32
#SBATCH --time=01:00:00
#SBATCH --array=0-7
#SBATCH --output=s23-logs/train_%A_%a.out
#SBATCH --error=s23-logs/train_%A_%a.err
# Study 23 RL training: one array element per (hw, data, arm) config; <= 32 cores x 1 h = 32 SU each, <= 256 SU total.
# Required: --export=ALL,S23_DIR=<.../s23>,S18C_LIB=<.../s18c>,PY=<python with numpy/scipy>
set -euo pipefail
: "${S23_DIR:?}"; : "${PY:?}"; : "${S18C_LIB:?}"
cd "$S23_DIR"
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 S18C_LIB
"$PY" train_rl.py "$SLURM_ARRAY_TASK_ID" "$SLURM_CPUS_PER_TASK"
