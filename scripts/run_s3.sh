#!/bin/bash
# ============================================================================
# run_s3.sh — S3: 手術工程（phase）認識の弱ベースライン
#
# frozen ResNet50 + PhaseHead で frame-by-frame の 9 クラス分類を学習する。
# 検出器とは独立しているため Δ(S3-S2) tool mAP は構造的に 0（spec §2.3 #2）。
# 3 seeds × 1 設定 = 3 実験を 2 GPU で並列実行。
# ============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
export PYTHONPATH=src

VENV="$PROJECT_DIR/.venv"
if [ ! -x "$VENV/bin/python" ]; then
    echo "ERROR: .venv が見つかりません" >&2; exit 1
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"

EXTRA_ARGS="${S3_EXTRA_ARGS:-}"
NUM_GPUS="$(python -c 'import torch;print(torch.cuda.device_count())' 2>/dev/null || echo 1)"
echo "Detected GPUs: ${NUM_GPUS}"
echo "=== S3: Phase frame-by-frame (frozen ResNet50 + PhaseHead) ==="

run_one() {
    local gpu="$1" seed="$2" desc="$3"
    echo "--- [GPU ${gpu}] phase seed=${seed} ---"
    CUDA_VISIBLE_DEVICES="${gpu}" python -m egosurgery.train \
        stage=s3_phase_frame \
        seed="${seed}" \
        experiment.description="${desc}" \
        logging.wandb_enabled=true \
        ${EXTRA_ARGS}
}

JOBS=(
    "42  phase_frame"
    "123 phase_frame"
    "456 phase_frame"
)

if [ "$NUM_GPUS" -ge 2 ]; then
    read -r s d <<< "${JOBS[0]}"
    run_one 0 "$s" "$d" &
    P0=$!
    sleep 10
    read -r s d <<< "${JOBS[1]}"
    run_one 1 "$s" "$d" &
    P1=$!
    wait "$P0" || echo "WARN: GPU0 job1 failed"
    wait "$P1" || echo "WARN: GPU1 job2 failed"

    read -r s d <<< "${JOBS[2]}"
    run_one 0 "$s" "$d" || echo "WARN: job3 failed"
else
    for job in "${JOBS[@]}"; do
        read -r s d <<< "$job"
        run_one 0 "$s" "$d" || echo "WARN: job '${job}' failed"
        sleep 5
    done
fi

echo "=== S3 completed ==="
echo "Check: experiments/phase0/s3_001_phase_frame_seed42 ~ s3_003_*"
