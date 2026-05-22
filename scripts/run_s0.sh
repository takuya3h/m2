#!/bin/bash
# S0: 術具検出ベースライン — §2.5(a) 基準点
# 3 seeds × 2 モデル (Mask DINO, VarifocalNet) = 6 実験
#
# 本番: bash scripts/run_s0.sh
# スモーク（小データ・1 epoch・CPU 可）:
#   S0_EXTRA_ARGS="model.backbone=dinov2_vits14_reg data.limit=16 \
#     data.img_size=224 data.batch_size=2 data.num_workers=0 \
#     train.epochs=1 train.freeze_backbone=true logging.wandb_enabled=false" \
#     bash scripts/run_s0.sh

set -euo pipefail

SEEDS=(42 123 456)
# 追加の Hydra override（スモーク実行などで上書きしたい場合に使用）。
EXTRA_ARGS="${S0_EXTRA_ARGS:-}"

echo "=== S0: Tool detection baseline ==="
echo "Goal: Establish §2.5(a) baseline. Must beat VarifocalNet SOTA mAP 45.8"

# --- Mask DINO × 3 seeds ---
for SEED in "${SEEDS[@]}"; do
    echo "--- Mask DINO, seed=${SEED} ---"
    PYTHONPATH=src python -m egosurgery.train \
        stage=s0_tool_baseline \
        model.detection_head=mask_dino \
        seed=${SEED} \
        experiment.description="maskdino_bbox" \
        logging.wandb_enabled=true \
        ${EXTRA_ARGS}
done

# --- VarifocalNet × 3 seeds ---
for SEED in "${SEEDS[@]}"; do
    echo "--- VarifocalNet, seed=${SEED} ---"
    PYTHONPATH=src python -m egosurgery.train \
        stage=s0_tool_baseline \
        model.detection_head=varifocanet \
        seed=${SEED} \
        experiment.description="varifocanet_bbox" \
        logging.wandb_enabled=true \
        ${EXTRA_ARGS}
done

echo "=== S0 completed ==="
echo "Check: experiments/baselines/s0_001_* ~ s0_006_*"
echo "Judgment #6: Compare Mask DINO vs VarifocalNet APr. If diff > 3pt, consider Co-DETR."
