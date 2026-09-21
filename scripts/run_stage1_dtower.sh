#!/usr/bin/env bash
# Stage 1 の検出塔 run を 1 本起こす。契約 T-2026-09-18-stage1-detector-towers。
#
# 使い方: scripts/run_stage1_dtower.sh <tower: coco|imagenet> <fold: A..E> <seed> <port>
#
# **処方は凍結源と同一である。** 変えるのは注釈ディレクトリ（折り）・seed・出力先・
# accelerate の待受ポート（同時起動のため）だけで、epoch・batch・lr・増強・解像度・
# 最適化器・数値精度（fp16）には手を触れない。
#
# 同じ 2 枚の上で複数の run を重ねられる。**どの run も 2 枚を使う**（--num_processes 2、
# per-GPU batch 2 = 実効 4）ので、実効バッチは単独実行と変わらない。
set -euo pipefail

TOWER="$1"; FOLD="$2"; SEED="$3"; PORT="$4"
BODY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN="d${TOWER}_fold${FOLD}_seed${SEED}"
DIR="$BODY/experiments/baselines/stage1_dtower/$RUN"

case "$TOWER" in
  coco)     CFG="configs/train_config_egosurgery_seed${SEED}.py" ;;
  imagenet) CFG="configs/train_config_egosurgery_stage1_imagenet_seed${SEED}.py" ;;
  *) echo "[ERROR] tower は coco か imagenet" >&2; exit 2 ;;
esac

mkdir -p "$DIR/work"
cat > "$DIR/command.sh" <<CMD
#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録
# 契約 T-2026-09-18-stage1-detector-towers / 塔 ${TOWER} / 折り ${FOLD} / seed ${SEED}
cd third_party/Relation-DETR
export EGO_ANN_DIR=$BODY/data/annotations/egosurgery_tool_folds/${FOLD}
export RELDETR_OUTPUT_DIR=$DIR/work
export CUDA_HOME=/usr/local/cuda
accelerate launch --num_processes 2 --main_process_port ${PORT} main.py \\
    --config-file ${CFG} --seed ${SEED} --mixed-precision fp16
CMD
chmod +x "$DIR/command.sh"

date -u '+%Y-%m-%d %H:%M:%S UTC' > "$DIR/start.txt"
# 起動時点で同じ装置を使っている run の本数を記録する（計時の解釈に要る）。
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$DIR/gpu_at_start.txt"

cd "$BODY/third_party/Relation-DETR"
# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export EGO_ANN_DIR="$BODY/data/annotations/egosurgery_tool_folds/${FOLD}"
export RELDETR_OUTPUT_DIR="$DIR/work"
export CUDA_HOME=/usr/local/cuda
# 記録は run ディレクトリの中に置く（呼び出し側で経路がばらつかないようにする）。
exec accelerate launch --num_processes 2 --main_process_port "$PORT" main.py \
    --config-file "$CFG" --seed "$SEED" --mixed-precision fp16 \
    >> "$DIR/train.log" 2>&1
