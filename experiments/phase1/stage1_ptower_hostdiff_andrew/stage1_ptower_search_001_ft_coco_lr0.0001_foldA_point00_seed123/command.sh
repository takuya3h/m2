#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/slocal2/m2
source scripts/load_env.sh
export CUDA_VISIBLE_DEVICES=0,1
export WANDB_MODE=offline
export WANDB_DIR=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-andrew/phase/seed123
export PYTHONPATH=/home/ubuntu/slocal2/m2/src:/home/ubuntu/slocal2/m2/scripts
export CUDA_HOME=/usr/local/cuda
export NCCL_P2P_DISABLE=1
export TOWER_SEARCH_TASK=T-2026-11-02-hostdiff-andrew
export TOWER_SEARCH_OBSERVER=/home/ubuntu/slocal2/m2/tasks/T-2026-11-02-hostdiff-andrew/tools/observer.py
export TOWER_SEARCH_PHASE_PUBLISH=experiments/phase1/stage1_ptower_hostdiff_andrew
cd /home/ubuntu/slocal2/m2
exec /home/ubuntu/slocal2/m2/.venv/bin/python -m torch.distributed.run --nproc_per_node=2 --master_port=29811 scripts/run_ptower_search.py action=finetune +point_id=0 +artifact_root=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-andrew/phase/seed123 manifest_dir=data/processed/phase_manifest_all_phase cache=/home/ubuntu/m2-scratch/T-2026-11-02-hostdiff-andrew/phase/seed123/features/all_gap.npz workers=4 seed=123
