#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/slocal2/m2
source scripts/load_env.sh
export CUDA_VISIBLE_DEVICES=0
export WANDB_MODE=offline
export WANDB_DIR=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/phase/seed42/head05
export PYTHONPATH=/home/ubuntu/slocal2/m2/src:/home/ubuntu/slocal2/m2/scripts
export CUDA_HOME=/usr/local/cuda
export NCCL_P2P_DISABLE=1
export TOWER_SEARCH_TASK=T-2026-11-02-hostdiff-bengio
export TOWER_SEARCH_SCRATCH=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio
export TOWER_SEARCH_PHASE_PUBLISH=experiments/phase1/stage1_ptower_hostdiff_bengio
cd /home/ubuntu/slocal2/m2
exec /home/ubuntu/slocal2/m2/.venv/bin/python scripts/run_ptower_search.py action=train +point_id=0 +artifact_root=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/phase/seed42/head05 manifest_dir=data/processed/phase_manifest_all_phase cache=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-bengio/phase/seed42/features/all_gap.npz workers=4 candidate=C layers=6 smoothing_weight=0.3 history=30
