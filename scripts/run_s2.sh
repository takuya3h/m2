#!/bin/bash
# ============================================================================
# run_s2.sh — S2: Tool + Hand detection（19 クラス）
#
# S0 で学習した best Mask DINO チェックポイントから 19 クラスへ fine-tune する
# （bbox_head は size mismatch で自動再初期化、backbone / neck / encoder /
# decoder は転移）。3 seeds、2 GPU 並列実行。
#
# 前提:
#   1) scripts/build_tool_hand_coco.py で
#      data/annotations/egosurgery_tool_hand/instances_*.json を生成済み
#   2) experiments/baselines/s0_001_maskdino_bbox_seed42/best_val_mAP_epoch_*.pth
#      が存在する（S0 完走済み）
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

EXTRA_ARGS="${S2_EXTRA_ARGS:-}"

# --- S0 best checkpoint の解決（Mask DINO seed42） -------------------------- #
S0_BEST=$(ls -1 experiments/baselines/s0_001_maskdino_bbox_seed42/best_val_mAP_epoch_*.pth 2>/dev/null | tail -1)
if [ -z "$S0_BEST" ]; then
    echo "ERROR: S0 best checkpoint が見つかりません" >&2
    echo "  期待パス: experiments/baselines/s0_001_maskdino_bbox_seed42/best_val_mAP_epoch_*.pth" >&2
    exit 1
fi
echo "S0 best (Mask DINO seed42): $S0_BEST"

# --- 統合 COCO の事前生成チェック ------------------------------------------ #
if [ ! -f data/annotations/egosurgery_tool_hand/instances_train.json ]; then
    echo "merged COCO 未生成 → build_tool_hand_coco.py を実行"
    python scripts/build_tool_hand_coco.py
fi

NUM_GPUS="$(python -c 'import torch;print(torch.cuda.device_count())' 2>/dev/null || echo 1)"
echo "Detected GPUs: ${NUM_GPUS}"

echo "=== S2: Tool+Hand detection (Mask DINO 19-cls, fine-tune from S0) ==="
echo "Goal: hand mAP > 65, tool mAP ≈ S0 mAP (±1pt)"

run_one() {
    local gpu="$1" head="$2" seed="$3" desc="$4"
    echo "--- [GPU ${gpu}] ${head} seed=${seed} ---"
    CUDA_VISIBLE_DEVICES="${gpu}" python -m egosurgery.train \
        stage=s2_hand \
        model.detection_head="${head}" \
        seed="${seed}" \
        experiment.description="${desc}" \
        train.real_detector=true \
        train.load_from="${S0_BEST}" \
        logging.wandb_enabled=true \
        ${EXTRA_ARGS}
}

# S2 は spec §1.2 通り Mask DINO 1 detector × 3 seeds で実施。
JOBS=(
    "mask_dino 42  hand_detection"
    "mask_dino 123 hand_detection"
    "mask_dino 456 hand_detection"
)

if [ "$NUM_GPUS" -ge 2 ]; then
    # 2 GPU で 2 並列 → 1 残り、を 2 波で実行。
    read -r h s d <<< "${JOBS[0]}"
    run_one 0 "$h" "$s" "$d" &
    P0=$!
    sleep 25
    read -r h s d <<< "${JOBS[1]}"
    run_one 1 "$h" "$s" "$d" &
    P1=$!
    wait "$P0" || echo "WARN: GPU0 job1 failed"
    wait "$P1" || echo "WARN: GPU1 job2 failed"

    read -r h s d <<< "${JOBS[2]}"
    run_one 0 "$h" "$s" "$d" || echo "WARN: job3 failed"
else
    for job in "${JOBS[@]}"; do
        read -r h s d <<< "$job"
        run_one 0 "$h" "$s" "$d" || echo "WARN: job '${job}' failed"
        sleep 5
    done
fi

echo "=== S2 completed ==="
echo "Check: experiments/phase0/s2_001_hand_detection_seed42 ~ s2_003_*"
