#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/local/m2
source scripts/load_env.sh
export CUDA_VISIBLE_DEVICES=2
export WANDB_MODE=offline
export WANDB_DIR=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point08
export PYTHONPATH=/home/ubuntu/local/m2/src:/home/ubuntu/local/m2/scripts
export CUDA_HOME=/usr/local/cuda
cd /home/ubuntu/local/m2
exec /home/ubuntu/local/m2/.venv/bin/python scripts/run_ptower_search.py action=extract checkpoint=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point08/runs/phase1/stage1_ptower_search_001_ft_coco_lr0.000113_foldA_point08_seed42/checkpoints/best.pth +point_id=8 +artifact_root=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point08 manifest_dir=data/processed/phase_manifest_all_phase cache=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point08/features/all_gap.npz workers=4
