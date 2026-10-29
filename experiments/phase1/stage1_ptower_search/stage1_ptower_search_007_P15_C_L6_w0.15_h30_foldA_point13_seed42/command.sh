#!/usr/bin/env bash
set -euo pipefail
cd /home/ubuntu/local/m2
source scripts/load_env.sh
export CUDA_VISIBLE_DEVICES=3
export WANDB_MODE=offline
export WANDB_DIR=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point13
export PYTHONPATH=/home/ubuntu/local/m2/src:/home/ubuntu/local/m2/scripts
export CUDA_HOME=/usr/local/cuda
cd /home/ubuntu/local/m2
exec /home/ubuntu/local/m2/.venv/bin/python scripts/run_ptower_search.py action=train +point_id=13 +artifact_root=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point13 manifest_dir=data/processed/phase_manifest_all_phase cache=/home/ubuntu/m2-scratch/T-2026-10-22-tower-reselect-search-dlsta/phase/point13/features/all_gap.npz workers=4 candidate=C layers=6 smoothing_weight=0.15 history=30
