#!/usr/bin/env bash
# S0-frozen′（②特徴レベル系統の検出分母）: Relation-DETR frozen seed42 backbone +
# COCO-init head + 共有 C5 線形 neck（trainable, zero-init）。
#
# run_s0_frozen.sh と**唯一の差**は config-file（neck 挿入検出器）と証跡ラベル。
# init / recipe / optimizer / epochs / schedule は S0-frozen と完全一致 → 「neck の有無」の1軸のみ。
# trainable_total = 25,238,688（基底）+ 4,196,352（c5_neck）= 29,435,040（プリフライト検証済）。
#
# 3 seeds: wave1 seed42@GPU0 / seed123@GPU1, wave2 seed456@GPU0。
set -euo pipefail
trap 'echo "ERROR: run_s0_frozen_neck.sh line ${LINENO} rc=$?" >&2' ERR

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELDETR_DIR="$PROJECT_DIR/third_party/Relation-DETR"
REL_VENV="$PROJECT_DIR/.venv-relation-detr"
PROJECT_PY="$PROJECT_DIR/.venv/bin/python"
INIT_CKPT="${RELDETR_S0FROZEN_INIT:-$PROJECT_DIR/data/external/weights/relation_detr_s0frozen_init_seed42.pth}"
LOG_DIR="${S0_FROZEN_LOG_DIR:-/tmp/s0_frozen_neck_logs}"
STAMP="$(date +%Y%m%d_%H%M%S)"
DESC="relationdetr_s0frozen_neck_cocohead"
SERVER_NAME="${SERVER_NAME:-${SERVERNAME:-$(hostname)}}"
RELDETR_NUM_EPOCHS="${RELDETR_NUM_EPOCHS:-12}"
RELDETR_BATCH_SIZE="${RELDETR_BATCH_SIZE:-2}"
RELDETR_NUM_WORKERS="${RELDETR_NUM_WORKERS:-4}"
RELDETR_LR="${RELDETR_LR:-1e-4}"
CUDA_HOME="${CUDA_HOME:-/usr/local/cuda}"
export PATH="$REL_VENV/bin:$PATH"

mkdir -p "$LOG_DIR" "$PROJECT_DIR/experiments/baselines"

if [ ! -x "$REL_VENV/bin/python" ] || [ ! -x "$REL_VENV/bin/accelerate" ]; then
    echo "ERROR: .venv-relation-detr が不完全です: $REL_VENV" >&2
    exit 1
fi
if [ ! -x "$PROJECT_PY" ]; then
    echo "ERROR: project .venv が見つかりません: $PROJECT_PY" >&2
    exit 1
fi
if [ ! -f "$INIT_CKPT" ]; then
    echo "ERROR: S0-frozen init checkpoint が見つかりません: $INIT_CKPT" >&2
    exit 1
fi

cd "$RELDETR_DIR"
echo "=== S0-frozen′ (neck) Relation-DETR start $(date -Iseconds) ==="
echo "init: $INIT_CKPT"
echo "epochs=$RELDETR_NUM_EPOCHS batch_size=$RELDETR_BATCH_SIZE workers=$RELDETR_NUM_WORKERS lr=$RELDETR_LR"
echo "logs: $LOG_DIR"

next_exp_dir() {
    local seed="$1"
    local max=0
    local d base seq count
    shopt -s nullglob
    for d in "$PROJECT_DIR"/experiments/baselines/s0_frozen_*_${DESC}_seed"$seed"; do
        count="$(find "$d" -mindepth 1 -maxdepth 1 -print -quit)"
        if [ -z "$count" ]; then
            printf '%s' "$d"
            shopt -u nullglob
            return 0
        fi
    done
    for d in "$PROJECT_DIR"/experiments/baselines/s0_frozen_*; do
        base="$(basename "$d")"
        seq="$(echo "$base" | sed -n 's/^s0_frozen_\([0-9][0-9][0-9]\)_.*/\1/p')"
        if [ -n "$seq" ] && [ $((10#$seq)) -gt "$max" ]; then
            max=$((10#$seq))
        fi
    done
    shopt -u nullglob
    printf '%s/experiments/baselines/s0_frozen_%03d_%s_seed%s' \
        "$PROJECT_DIR" "$((max + 1))" "$DESC" "$seed"
}

launch_seed() {
    local seed="$1" gpu="$2"
    local workdir="/tmp/reldetr_work_s0_frozen_neck_seed${seed}_${STAMP}"
    local expdir
    expdir="$(next_exp_dir "$seed")"
    mkdir -p "$workdir" "$expdir"
    local logf="$LOG_DIR/s0_frozen_neck_seed${seed}_${STAMP}.log"
    local command_sh
    command_sh="cd $RELDETR_DIR && CUDA_VISIBLE_DEVICES=$gpu RELDETR_OUTPUT_DIR=$workdir RELDETR_EVIDENCE_DIR=$workdir RELDETR_S0FROZEN_INIT=$INIT_CKPT RELDETR_NUM_EPOCHS=$RELDETR_NUM_EPOCHS RELDETR_BATCH_SIZE=$RELDETR_BATCH_SIZE RELDETR_NUM_WORKERS=$RELDETR_NUM_WORKERS RELDETR_LR=$RELDETR_LR $REL_VENV/bin/accelerate launch --num_processes 1 main.py --config-file configs/train_config_egosurgery_s0_frozen_neck.py --seed $seed --mixed-precision fp16"

    echo "--- launch seed=$seed gpu=$gpu workdir=$workdir expdir=$expdir log=$logf ---"
    (
        set -euo pipefail
        trap 'echo "ERROR: seed=$seed line ${LINENO} rc=$?" >&2' ERR
        echo "[seed=$seed] start $(date -Iseconds) gpu=$gpu workdir=$workdir"
        export CUDA_HOME
        export CUDA_VISIBLE_DEVICES="$gpu"
        export RELDETR_OUTPUT_DIR="$workdir"
        export RELDETR_EVIDENCE_DIR="$workdir"
        export RELDETR_S0FROZEN_INIT="$INIT_CKPT"
        export RELDETR_NUM_EPOCHS RELDETR_BATCH_SIZE RELDETR_NUM_WORKERS RELDETR_LR
        echo "[seed=$seed] running accelerate: $(date -Iseconds)"
        set +e
        "$REL_VENV/bin/accelerate" launch --num_processes 1 main.py \
            --config-file configs/train_config_egosurgery_s0_frozen_neck.py \
            --seed "$seed" --mixed-precision fp16
        train_rc=$?
        set -e
        echo "[seed=$seed] accelerate exited rc=$train_rc $(date -Iseconds)"
        if [ "$train_rc" -ne 0 ]; then
            exit "$train_rc"
        fi
        "$PROJECT_PY" "$PROJECT_DIR/scripts/post_process_relation_detr.py" \
            --train-dir "$workdir" \
            --exp-dir "$expdir" \
            --command-sh "$command_sh" \
            --seed "$seed" \
            --description "$DESC" \
            --detector "Relation-DETR S0-frozen+neck" \
            --world-size 1 \
            --per-process-batch-size "$RELDETR_BATCH_SIZE" \
            --server-name "$SERVER_NAME" \
            --step "S0_frozen_neck" \
            --init-note "S0-frozen′ init: Relation-DETR seed42 frozen backbone + COCO-init transformer/head + 共有 C5 線形 neck (trainable, zero-init, 1x1 2048->2048 residual). Backbone frozen freeze_indices=(0,1,2,3); trainable = neck/transformer/heads + c5_neck. trainable_total=29,435,040 (base 25,238,688 + c5_neck 4,196,352). ②特徴レベル系統の Δ_detection 分母。" \
            --skip-external-loggers
        echo "S0_FROZEN_NECK_SEED_COMPLETED seed=$seed expdir=$expdir $(date -Iseconds)"
    ) > "$logf" 2>&1 &
    LAST_PID=$!
    LAST_LOG="$logf"
}

wait_wave() {
    local rc=0
    local pid
    for pid in "$@"; do
        if ! wait "$pid"; then
            echo "WARN: seed job pid=$pid failed" >&2
            rc=1
        fi
    done
    return "$rc"
}

PIDS=()
launch_seed 42 0; PIDS+=("$LAST_PID")
launch_seed 123 1; PIDS+=("$LAST_PID")
wait_wave "${PIDS[@]}"

PIDS=()
launch_seed 456 0; PIDS+=("$LAST_PID")
wait_wave "${PIDS[@]}"

echo "S0_FROZEN_NECK_COMPLETED $(date -Iseconds)"
echo "=== S0-frozen′ (neck) Relation-DETR completed ==="
