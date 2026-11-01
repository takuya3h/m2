#!/usr/bin/env bash
# 把持塔 G の 1 本を起こす（非公式 T-2026-11-01-grasp-pilot-g、Task C-3）。run の置き場は experiments/phase1/grasppilot2_G_<videos>_seed42
#   bash scripts/grasppilot/run_g.sh all|H1|H2 <gpu>
set -u
cd "$(dirname "$0")/../.."
VIDEOS=$1; GPU=$2
TASK=T-2026-11-01-grasp-pilot-g
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
NAME=grasppilot2_G_${VIDEOS}_seed42
RUN=experiments/phase1/$NAME
mkdir -p "$RUN" "$S/logs"
source scripts/load_env.sh >/dev/null 2>&1 || true
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv > "$RUN/gpu_at_start.txt"
CUDA_VISIBLE_DEVICES=$GPU PYTHONPATH=src .venv/bin/python scripts/grasppilot/g_train.py --run-dir "$RUN" \
  --ckpt-dir "$S/g/ckpt/$NAME" --ann-dir "$S/g/ann" --videos "$VIDEOS" --workers 8 > "$RUN/train.log" 2>&1
echo $? > "$RUN/exit_code.txt"
