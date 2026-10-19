#!/usr/bin/env bash
# B-3 検出塔単独の val 再現（非公式 T-2026-10-18-stage2-pilot-folda）。val だけ。test は評価しない。
set -euo pipefail
BODY=/home/ubuntu/slocal2/m2
CKPT="${1:?ckpt}"; OUT="${2:?out json}"; PORT="${3:-29751}"
cd "$BODY"
source "$BODY/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda
# andrew は IOMMU が有効で GPU 間 P2P の all_reduce が止まる（2026-10-18 実測）。P2P を使わない
export NCCL_P2P_DISABLE=1
export EGO_ROOT="$BODY/data/raw/ego"
export EGO_ANN_DIR="$BODY/data/annotations/egosurgery_tool_folds/A"
python -c "import torch;print('[env] torch',torch.__version__,'cuda',torch.cuda.is_available())"
accelerate launch --num_processes 2 --main_process_port "$PORT" \
  "$BODY/scripts/eval_relation_detr_map.py" \
  --config configs/train_config_egosurgery_seed42.py --checkpoint "$CKPT" --split val --out "$OUT"
