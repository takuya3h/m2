#!/bin/bash
# ============================================================================
# run_s0.sh — S0: 術具検出ベースライン（§2.5(a) 基準点）
#
# 実検出器（VarifocalNet / DINO）を COCO 事前学習重みから EgoSurgery-Tool へ
# fine-tune する。3 seeds × 2 detector = 6 実験。搭載 2 GPU へ振り分けて並列実行。
#
#   - "Mask DINO" 枠: dino-4scale_r50（mmdet は Mask DINO 本体を同梱しないため、
#     bbox-only S0 で最も近い実検出器 DINO を使用。詳細は各 notes.md 参照）
#   - VarifocalNet: vfnet_r50_fpn_1x_coco（完了判定 #4 = mAP >= 45.8 の対象）
#
# 実験フォルダは完了判定 #2 の命名順に採番される:
#   s0_001 maskdino seed42 / s0_002 seed123 / s0_003 seed456
#   s0_004 varifocanet seed42 / s0_005 seed123 / s0_006 seed456
# 2 GPU 時は 3 波 × 2 実験で実行し、波内で 25 秒スタガーを入れて
# ExperimentManager の連番採番を JOBS 配列順に固定する。
#
# 本番: bash scripts/run_s0.sh
# スモーク（内蔵 SimpleDetectionHead・小データ・1 epoch）:
#   S0_EXTRA_ARGS="train.real_detector=false model.backbone=dinov2_vits14_reg \
#     data.limit=16 data.img_size=224 data.num_workers=0 train.epochs=1 \
#     train.freeze_backbone=true logging.wandb_enabled=false" bash scripts/run_s0.sh
# ============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
export PYTHONPATH=src

# プロジェクト .venv を有効化（CLAUDE.md: コード実行前に必須）。
# torch 2.1.2+cu118 と mmcv/mmdet の CUDA 拡張はこの venv の site-packages
# にのみ整合する。素の `python`（pyenv グローバル）では mmcv の C 拡張が
# ABI 不一致で ImportError になるため、ここで必ず有効化する。
VENV="$PROJECT_DIR/.venv"
if [ ! -x "$VENV/bin/python" ]; then
    echo "ERROR: .venv が見つかりません ($VENV)。README の推奨セットアップを参照。" >&2
    exit 1
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
echo "venv: $(command -v python)"

EXTRA_ARGS="${S0_EXTRA_ARGS:-}"
WEIGHTS_DIR="data/external/weights"

echo "=== S0: Tool detection baseline (real detectors via mmdet) ==="
echo "Goal: Establish §2.5(a) baseline. VarifocalNet target mAP >= 45.8"

# --- COCO 事前学習重みの取得（無ければダウンロード） ----------------------- #
mkdir -p "$WEIGHTS_DIR"
VFNET_URL="https://download.openmmlab.com/mmdetection/v2.0/vfnet/vfnet_r50_fpn_1x_coco/vfnet_r50_fpn_1x_coco_20201027-38db6f58.pth"
DINO_URL="https://download.openmmlab.com/mmdetection/v3.0/dino/dino-4scale_r50_8xb2-12e_coco/dino-4scale_r50_8xb2-12e_coco_20221202_182705-55b2bba2.pth"
[ -f "$WEIGHTS_DIR/vfnet_r50_fpn_1x_coco.pth" ] || \
    curl -sL -o "$WEIGHTS_DIR/vfnet_r50_fpn_1x_coco.pth" "$VFNET_URL"
[ -f "$WEIGHTS_DIR/dino-4scale_r50_8xb2-12e_coco.pth" ] || \
    curl -sL -o "$WEIGHTS_DIR/dino-4scale_r50_8xb2-12e_coco.pth" "$DINO_URL"

# --- 利用可能 GPU 数を取得（無ければ 1 とみなす） -------------------------- #
NUM_GPUS="$(python -c 'import torch;print(torch.cuda.device_count())' 2>/dev/null || echo 1)"
[ "$NUM_GPUS" -ge 1 ] || NUM_GPUS=1
echo "Detected GPUs: ${NUM_GPUS}"

# 1 実験を実行する。引数: gpu_id detection_head seed description
run_one() {
    local gpu="$1" head="$2" seed="$3" desc="$4"
    echo "--- [GPU ${gpu}] ${head} seed=${seed} ---"
    CUDA_VISIBLE_DEVICES="${gpu}" python -m egosurgery.train \
        stage=s0_tool_baseline \
        model.detection_head="${head}" \
        seed="${seed}" \
        experiment.description="${desc}" \
        train.real_detector=true \
        logging.wandb_enabled=true \
        ${EXTRA_ARGS}
}

# 6 実験を完了判定 #2 の命名順（maskdino ×3 -> varifocanet ×3）で列挙。
JOBS=(
    "mask_dino   42  maskdino_bbox"
    "mask_dino   123 maskdino_bbox"
    "mask_dino   456 maskdino_bbox"
    "varifocanet 42  varifocanet_bbox"
    "varifocanet 123 varifocanet_bbox"
    "varifocanet 456 varifocanet_bbox"
)

if [ "$NUM_GPUS" -ge 2 ]; then
    # 3 波 × 2 実験。波内は GPU0 を先行起動し 25 秒後に GPU1 を起動して、
    # ExperimentManager の連番が JOBS 順（s0_001..s0_006）になるよう固定する。
    for wave in 0 1 2; do
        i0=$((wave * 2))
        i1=$((wave * 2 + 1))
        echo "=== Wave $((wave + 1))/3 ==="
        read -r h s d <<< "${JOBS[$i0]}"
        run_one 0 "$h" "$s" "$d" &
        P0=$!
        sleep 25
        read -r h s d <<< "${JOBS[$i1]}"
        run_one 1 "$h" "$s" "$d" &
        P1=$!
        wait "$P0" || echo "WARN: GPU0 wave $((wave + 1)) job failed (exit $?)"
        wait "$P1" || echo "WARN: GPU1 wave $((wave + 1)) job failed (exit $?)"
    done
else
    # 単一 GPU: 6 実験を JOBS 順に逐次実行。
    for job in "${JOBS[@]}"; do
        read -r h s d <<< "$job"
        run_one 0 "$h" "$s" "$d" || echo "WARN: job '${job}' failed (exit $?)"
        sleep 5
    done
fi

echo "=== S0 completed ==="
echo "Check: experiments/baselines/s0_001_maskdino_bbox_seed42 ~ s0_006_varifocanet_bbox_seed456"
echo "Judgment #6: Compare DINO vs VarifocalNet AP_rare. If diff > 3pt, consider Co-DETR."
