#!/usr/bin/env bash
# AlignDETR-S0-frozen: R50 backbone 全凍結 + head 学習 (12ep)、3 seed 直列。
# 台帳 Run「凍結源の下流有用性比較」用。
#
# 使用前提: philip 側 (.venv-detectron2 + third_party/detrex)。
# 実行順序:
#   wave 1: seed42  on 2 GPU (12ep, ~1-2h 想定)
#   wave 2: seed123 on 2 GPU
#   wave 3: seed456 on 2 GPU
# GPU 待機は run_when_gpu_free.sh 側で担保。
set -euo pipefail
trap 'echo "ERROR: $(basename "$0") line ${LINENO} rc=$?" >&2' ERR

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DETREX_DIR="$PROJECT_DIR/third_party/detrex"
D2_VENV="$PROJECT_DIR/.venv-detectron2"
CONFIG_FILE="$DETREX_DIR/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py"
LOG_DIR="${S0_FROZEN_LOG_DIR:-/tmp/aligndetr_s0frozen_logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
DESC="aligndetr_s0frozen_cocohead"
SERVER_NAME="${SERVER_NAME:-$(hostname)}"
NUM_GPUS="${NUM_GPUS:-2}"

mkdir -p "$LOG_DIR" "$PROJECT_DIR/experiments/baselines"

if [ ! -x "$D2_VENV/bin/python" ]; then
  echo "ERROR: .venv-detectron2 が見つかりません: $D2_VENV" >&2
  exit 1
fi
if [ ! -f "$CONFIG_FILE" ]; then
  echo "ERROR: AlignDETR-S0-frozen config が見つかりません: $CONFIG_FILE" >&2
  exit 1
fi

export PATH="$D2_VENV/bin:$PATH"

run_one_seed() {
  local seed="$1"
  local out_dir="/tmp/aligndetr_s0frozen_seed${seed}_${STAMP}"
  local log_file="$LOG_DIR/aligndetr_s0frozen_seed${seed}_${STAMP}.log"
  mkdir -p "$out_dir"
  echo "[$(date +%F_%T)] === Starting AlignDETR-S0-frozen seed=$seed (${NUM_GPUS}gpu) ===" | tee "$log_file"
  cd "$DETREX_DIR"
  python tools/train_net_egosurgery.py \
    --config-file "$CONFIG_FILE" \
    --num-gpus "$NUM_GPUS" \
    train.seed="$seed" \
    train.output_dir="$out_dir" \
    train.wandb.params.name="aligndetr_s0frozen_r50_12ep_seed${seed}" \
    2>&1 | tee -a "$log_file"
  # 完了後、experiments/baselines/ 配下に証跡を配置する層は launcher (train_net_egosurgery.py) が担うが、
  # 念のため out_dir に残る best mAP は notes.md に手動記録も可。
}

# デフォルト 3-seed 直列。SEEDS=42 のみ等の外部指定にも対応。
IFS=' ' read -r -a SEEDS <<< "${SEEDS:-42 123 456}"
echo "[$(date +%F_%T)] AlignDETR-S0-frozen 3-seed launcher: seeds=${SEEDS[*]}"
for s in "${SEEDS[@]}"; do
  run_one_seed "$s"
done
echo "[$(date +%F_%T)] === All seeds done (${SEEDS[*]}) ==="
