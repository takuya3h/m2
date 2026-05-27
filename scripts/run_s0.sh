#!/bin/bash
# ============================================================================
# run_s0.sh — S0: 術具検出ベースライン（§2.5(a) 基準点）— DDP 2 GPU 版
#
# 【§8.0・§14 実行サーバー方針】
#   本来は RTX 6000 Ada ×1（Δ 基準点専用）。RTX 6000 Ada 未配備期間は
#   bengio（RTX A6000 ×2）の DDP 2 GPU で実行する。§14 の方針変更により、
#   S0 全モデル（VFNet・Mask DINO・Co-DETR）を DDP 2 GPU で統一する。
#
#   §8.0 暫定運用の 6 条件:
#     (1) 同一 Δ 比較群は同一サーバーで測定 → bengio で統一
#     (2) eval_recipe.server_name と server.txt にサーバー名を記録
#     (3) RTX 6000 Ada 配備後の再測定の必要性を Notion §14 に明記
#     (4) DDP 使用時は S0 内の全モデルを同一 GPU 構成（2 GPU）で揃える
#     (5) effective batch size を eval_recipe に記録（_build_eval_recipe）
#     (6) lr 線形スケーリングの適用を config に明記（train.lr_scaling_mode）
#
# 【§15.4 A strict 3 条件】
#   - データ split: 論文公式（train 9657 / val 1515 / test 4265）
#   - test_cfg: locked-down（score_thr=1e-8, max_per_img=300）
#   - eval_recipe: metrics.json に併記（gpu_count=2, effective_batch_size 込み）
#
# 実 SOTA を確実に再現するため、内部は mmdet 3.x の Runner を使う。Runner は
# torchrun 起動時に dist 初期化と MMDistributedDataParallel ラップを自動で行う。
# SyncBatchNorm 変換も mmdet 側が DDP 文脈で自動適用する（§13.2 (b)(iv)）。
#
#   - VarifocalNet: vfnet_r50_fpn_1x_coco（完了判定 #4 = mAP >= 45.8）
#   - "Mask DINO" 枠: dino-4scale_r50（mmdet は Mask DINO 本体を同梱せず代替）
#   - Co-DETR: co_dino_5scale_r50（§13.2 S0・§9 #6 判断ポイント用、長尾対照）
#
# 実験フォルダは命名順で採番される:
#   s0_001..s0_003: Mask DINO 枠 ×3 seeds
#   s0_004..s0_006: VarifocalNet ×3 seeds
#   s0_007..s0_009: Co-DETR ×3 seeds  ← §13.2 S0「Mask DINO・VFNet・Co-DETR を準備」
#
# 本番: bash scripts/run_s0.sh
# スモーク（小データ・1 epoch・単一 GPU 互換）:
#   NPROC=1 S0_EXTRA_ARGS="train.real_detector=false ..." bash scripts/run_s0.sh
#
# 旧 split（_wrong_split_8_2_3）・進行中・完了済みの単一 GPU S0 学習結果は
# §14 の通り Δ 基準点には使わない。本スクリプトで全 9 実験を DDP 2 GPU で再学習する。
# ============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"
export PYTHONPATH=src

# プロジェクト .venv を有効化。
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

echo "=== S0: Tool detection baseline (DDP 2 GPU via torchrun) ==="
echo "Goal: VarifocalNet mAP >= 45.8 (公式 split・locked-down test_cfg・DDP 2 GPU)"

# --- COCO 事前学習重みの取得（無ければダウンロード） --- #
mkdir -p "$WEIGHTS_DIR"
VFNET_URL="https://download.openmmlab.com/mmdetection/v2.0/vfnet/vfnet_r50_fpn_1x_coco/vfnet_r50_fpn_1x_coco_20201027-38db6f58.pth"
DINO_URL="https://download.openmmlab.com/mmdetection/v3.0/dino/dino-4scale_r50_8xb2-12e_coco/dino-4scale_r50_8xb2-12e_coco_20221202_182705-55b2bba2.pth"
# Co-DETR の公式重み（projects/CO-DETR、5-scale R50）。
CODETR_URL="https://download.openmmlab.com/mmdetection/v3.0/codetr/co_dino_5scale_r50_lsj_8xb2_1x_coco/co_dino_5scale_r50_lsj_8xb2_1x_coco-69a72d67.pth"
[ -f "$WEIGHTS_DIR/vfnet_r50_fpn_1x_coco.pth" ] || \
    curl -sL -o "$WEIGHTS_DIR/vfnet_r50_fpn_1x_coco.pth" "$VFNET_URL"
[ -f "$WEIGHTS_DIR/dino-4scale_r50_8xb2-12e_coco.pth" ] || \
    curl -sL -o "$WEIGHTS_DIR/dino-4scale_r50_8xb2-12e_coco.pth" "$DINO_URL"
# Co-DETR 重みは Δ 基準点での比較に必要（無ければ警告のみ・学習側で落ちる）。
[ -f "$WEIGHTS_DIR/co_dino_5scale_r50_1x_coco.pth" ] || {
    echo "INFO: Co-DETR 事前学習重みを取得します..."
    curl -sL -o "$WEIGHTS_DIR/co_dino_5scale_r50_1x_coco.pth" "$CODETR_URL" || {
        echo "WARN: Co-DETR 重みの取得に失敗。s0_007..s0_009 は失敗する可能性。"
    }
}

# --- DDP パラメータ --- #
# bengio = RTX A6000 ×2。NPROC は単一 GPU スモークで 1 に上書き可。
NPROC="${NPROC:-2}"
PER_GPU_BS="${PER_GPU_BS:-2}"          # effective bs = NPROC × PER_GPU_BS
LR_SCALING_MODE="${LR_SCALING_MODE:-linear}"
EPOCHS="${EPOCHS:-12}"
SEEDS=(42 123 456)

# 利用可能 GPU 数の確認（NPROC を超えるか確認）。
NUM_GPUS="$(python -c 'import torch;print(torch.cuda.device_count())' 2>/dev/null || echo 1)"
echo "Available GPUs: ${NUM_GPUS} / Requested NPROC: ${NPROC}"
if [ "$NUM_GPUS" -lt "$NPROC" ]; then
    echo "WARN: 要求 NPROC=${NPROC} > 利用可能 GPU=${NUM_GPUS}。NPROC を ${NUM_GPUS} に下げます。"
    NPROC="$NUM_GPUS"
fi

# 1 実験を「手動 launcher」で起動する（torchrun を使わない）。
#
# torchrun は LOCAL_RANK を env で各 worker に渡すだけで、worker 側は親の
# CUDA_VISIBLE_DEVICES（=全 GPU）を継承する。本プロジェクトの環境では
# torch.cuda.set_device(local_rank) が期待通り効かず、両 worker が GPU 0 に
# 集中する事象が観測された。
#
# そこで本スクリプトは各 rank を**個別プロセスで起動**し、CUDA_VISIBLE_DEVICES
# を rank ごとに別 GPU に固定する。各 rank からは「自分の GPU が cuda:0」と
# 見えるため、torch.cuda.set_device(0) が確実に効く。
# WORLD_SIZE/RANK/MASTER_ADDR/MASTER_PORT は env で手動指定し、
# torch.distributed が dist.init_process_group(backend='nccl') で集合する。
#
# 引数: detection_head seed seed_idx det_idx desc
run_ddp() {
    local head="$1" seed="$2" seed_idx="$3" det_idx="$4" desc="$5"
    # MASTER_PORT を seed/detector ごとにユニーク化（§13.2 (c) ポート競合回避）。
    local port=$((29500 + seed_idx * 3 + det_idx))
    echo "--- [DDP NPROC=${NPROC} via manual launcher] ${head} seed=${seed} (port=${port}) ---"

    # 各 rank の stdout/stderr は /tmp/s0_<head>_seed<seed>_rank<r>.log へ
    # 分離。本番のメインログにはサマリのみ出す。
    local logdir="/tmp/s0_logs"
    mkdir -p "$logdir"
    local pids=()

    # rank 0 .. NPROC-1 を順次起動（NPROC=1 のときは rank 0 のみ）
    for ((r=0; r<NPROC; r++)); do
        local logf="${logdir}/${head}_seed${seed}_rank${r}.log"
        # 各 rank は CUDA_VISIBLE_DEVICES=r で 1 GPU だけ見える状態。
        # その rank 内では cuda:0 が物理 GPU r になる。
        CUDA_VISIBLE_DEVICES="${r}" \
        WORLD_SIZE="${NPROC}" \
        RANK="${r}" \
        LOCAL_RANK=0 \
        MASTER_ADDR=127.0.0.1 \
        MASTER_PORT="${port}" \
        python -m egosurgery.train \
            stage=s0_tool_baseline \
            model.detection_head="${head}" \
            seed="${seed}" \
            experiment.description="${desc}" \
            train.real_detector=true \
            train.epochs="${EPOCHS}" \
            train.batch_size="${PER_GPU_BS}" \
            train.lr_scaling_mode="${LR_SCALING_MODE}" \
            logging.wandb_enabled=true \
            ${EXTRA_ARGS} \
            > "${logf}" 2>&1 &
        pids+=($!)
    done

    # 全 rank の完了を待つ。1 つでも失敗したら全体失敗扱い。
    local rc=0
    for pid in "${pids[@]}"; do
        if ! wait "$pid"; then
            rc=$?
            echo "WARN: rank pid=${pid} exited with $rc"
        fi
    done
    return $rc
}

# === 全 9 実験の順次実行 === #
# DDP では 1 実験が両 GPU を占有するため、ジョブ並列はせず逐次実行する
# （§8.0 条件 (1)(4): 同一 GPU 構成での測定統一）。
JOBS=(
    "mask_dino    maskdino_bbox    0"  # det_idx=0
    "varifocanet  varifocanet_bbox 1"  # det_idx=1
    "codetr       codetr_bbox      2"  # det_idx=2: §13.2 S0・§9 #6 用
)

for job in "${JOBS[@]}"; do
    read -r head desc det_idx <<< "$job"
    seed_idx=0
    for seed in "${SEEDS[@]}"; do
        run_ddp "$head" "$seed" "$seed_idx" "$det_idx" "$desc" || \
            echo "WARN: ${head} seed=${seed} failed (exit $?)"
        seed_idx=$((seed_idx + 1))
        sleep 5
    done
done

echo ""
echo "=== S0 completed ==="
echo "Check experiments/baselines/s0_001..s0_009 (Mask DINO ×3 + VFNet ×3 + Co-DETR ×3)"
echo "全 metrics.json の eval_recipe.gpu_count == ${NPROC} を確認してください（§8.0 条件 (4)(5)）"
echo "Judgment #6 (Mask DINO vs Co-DETR の APr 比較):"
echo "  python scripts/compare_judge6.py"
