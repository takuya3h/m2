#!/usr/bin/env bash
# GPU 空き待ち → 凍結源比較 Run 実行 chain (philip 上で走らせる想定)。
#
# 使い方 (philip で):
#   bash ~/slocal2/m2/scripts/run_when_gpu_free.sh &  # background で仕込む
#   # 別コンテナの学習が終わり GPU が解放されると、chain が自動起動する。
#
# 実行内容 (順次):
#   1. AlignDETR-S0-frozen seed42 学習 (12ep, 2GPU)
#   2. AlignDETR 版 特徴抽出 (train/val/test の GAP + region-token)
#   3. TeCNO 学習: 2 source × 3-seed × B2a/T1a = 12 run
#   4. Δ 集計 (per-phase paired-σ)
#
# GPU 空き判定: 両 GPU の memory_free >= FREE_THRESH_MB かつ util <= UTIL_THRESH_PCT で
#   持続 STABLE_COUNT 回 (POLL_INTERVAL 秒ごと) 満たしたら「空き」判定。
set -euo pipefail
trap 'echo "ERROR: $(basename "$0") line ${LINENO} rc=$?" >&2' ERR

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${GPU_WAITER_LOG_DIR:-/tmp/gpu_waiter_logs}"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d_%H%M%S)"
WAITER_LOG="$LOG_DIR/gpu_waiter_${STAMP}.log"

# --- GPU 空き判定 パラメータ (デフォルト値、環境変数で上書き可) ------------ #
FREE_THRESH_MB="${FREE_THRESH_MB:-40000}"     # 40GB 空きで学習可
UTIL_THRESH_PCT="${UTIL_THRESH_PCT:-15}"       # utilization <= 15%
POLL_INTERVAL="${POLL_INTERVAL:-60}"           # 60 秒ごと polling
STABLE_COUNT="${STABLE_COUNT:-3}"              # 3 回連続 (= 3 分安定) で空き判定
MAX_WAIT_HOURS="${MAX_WAIT_HOURS:-48}"         # 最大 48 時間待機 (これを超えると abort)

log() { echo "[$(date +%F_%T)] $*" | tee -a "$WAITER_LOG"; }

log "=== GPU waiter 起動 (project=$PROJECT_DIR) ==="
log "polling: interval=${POLL_INTERVAL}s, threshold: free>=${FREE_THRESH_MB}MB & util<=${UTIL_THRESH_PCT}%, stable_count=${STABLE_COUNT}"

is_gpu_free() {
  # 出力: "free_mb util_pct free_mb util_pct" (GPU0/1 の連結)
  local vals
  vals=$(nvidia-smi --query-gpu=memory.free,utilization.gpu --format=csv,noheader,nounits 2>/dev/null | tr ',\n' '  ')
  # 各 GPU の free_mb と util_pct を配列化
  read -ra arr <<< "$vals"
  local n=${#arr[@]}
  if (( n < 4 )); then
    return 1  # GPU が 2 枚未満だと判定不能
  fi
  # arr = (free0 util0 free1 util1 ...) 2GPU 想定
  local free0="${arr[0]}" util0="${arr[1]}" free1="${arr[2]}" util1="${arr[3]}"
  if (( free0 >= FREE_THRESH_MB && free1 >= FREE_THRESH_MB && util0 <= UTIL_THRESH_PCT && util1 <= UTIL_THRESH_PCT )); then
    return 0
  else
    return 1
  fi
}

wait_for_gpu() {
  local waited=0
  local stable=0
  local max_wait_sec=$(( MAX_WAIT_HOURS * 3600 ))
  while (( waited < max_wait_sec )); do
    if is_gpu_free; then
      stable=$(( stable + 1 ))
      log "GPU 空き検知 ($stable/$STABLE_COUNT). status: $(nvidia-smi --query-gpu=memory.free,utilization.gpu --format=csv,noheader)"
      if (( stable >= STABLE_COUNT )); then
        log "=== GPU 空き確定 (${STABLE_COUNT} 回連続) → 実行フェーズへ ==="
        return 0
      fi
    else
      if (( stable > 0 )); then
        log "GPU 使用再開、stable カウンタリセット. status: $(nvidia-smi --query-gpu=memory.free,utilization.gpu --format=csv,noheader)"
      fi
      stable=0
    fi
    sleep "$POLL_INTERVAL"
    waited=$(( waited + POLL_INTERVAL ))
    # 5 分ごとに待機状況ログ
    if (( waited % 300 == 0 )); then
      log "待機中 ${waited}s / max ${max_wait_sec}s. GPU: $(nvidia-smi --query-gpu=memory.free,utilization.gpu --format=csv,noheader | tr '\n' ' | ')"
    fi
  done
  log "ERROR: GPU 空き待ち MAX_WAIT_HOURS=${MAX_WAIT_HOURS}h を超過。abort。"
  return 1
}

# --- 実行 chain (Phase 1: AlignDETR-S0-frozen 学習) ---------------------- #
run_aligndetr_s0_frozen() {
  log "=== Phase 1: AlignDETR-S0-frozen 学習 (SEEDS=${SEEDS:-42}, 12ep) ==="
  SEEDS="${SEEDS:-42}" NUM_GPUS=2 bash "$PROJECT_DIR/scripts/run_s0_frozen_aligndetr.sh" 2>&1 | tee -a "$WAITER_LOG"
  log "=== Phase 1 完了 ==="
}

# --- 実行 chain (Phase 2: AlignDETR 特徴抽出) ---------------------------- #
run_aligndetr_extract() {
  log "=== Phase 2: AlignDETR 特徴抽出 (GAP + region-token, train/val/test) ==="
  local seed="${EXTRACT_SEED:-42}"
  local ckpt_dir
  # 最新の s0_frozen 出力を探す
  ckpt_dir=$(ls -td /tmp/aligndetr_s0frozen_seed${seed}_* 2>/dev/null | head -1)
  if [ -z "$ckpt_dir" ] || [ ! -f "$ckpt_dir/model_final.pth" ]; then
    log "ERROR: AlignDETR-S0-frozen ckpt が見つかりません: $ckpt_dir/model_final.pth"
    return 1
  fi
  local ckpt="$ckpt_dir/model_final.pth"
  local cfg="$PROJECT_DIR/third_party/detrex/projects/align_detr/configs/aligndetr_r50_4scale_12ep_egosurgery_s0_frozen.py"
  local out_gap_root="$PROJECT_DIR/data/processed/stage1_features/aligndetr_s0frozen_seed${seed}"
  local out_rt_root="$PROJECT_DIR/data/processed/t1a_regiontoken/aligndetr_s0frozen_seed${seed}"
  local d2py="$PROJECT_DIR/.venv-detectron2/bin/python"
  for split in train val test; do
    log "  extract GAP $split ..."
    "$d2py" "$PROJECT_DIR/scripts/extract_stage1_features_aligndetr.py" \
      --subset "$split" --config-file "$cfg" --checkpoint "$ckpt" \
      --out "$out_gap_root/${split}_gap.npz" 2>&1 | tee -a "$WAITER_LOG"
    log "  extract region-token $split ..."
    "$d2py" "$PROJECT_DIR/scripts/extract_t1a_regiontoken_aligndetr.py" \
      --subset "$split" --config-file "$cfg" --checkpoint "$ckpt" \
      --out "$out_rt_root/${split}_regiontoken.npz" 2>&1 | tee -a "$WAITER_LOG"
  done
  log "=== Phase 2 完了 ==="
}

# --- 実行 chain (Phase 3: TeCNO 学習 - T1a を 2 source × 3-seed = 6 run) ----- #
# 主要比較チャネル: T1a region-token (Notion 台帳 Primary Metric は det→phase Δ 特に hemostasis)。
# B2a-pred は AlignDETR 版 extract_b2a_detsignal_aligndetr.py 未実装のため今 scope 外。
# B2a-oracle は GT 由来で frozen source に非依存 (比較対象として不適切)。
# → T1a のみで 2 source 比較を実装。
run_tecno_training() {
  log "=== Phase 3: TeCNO T1a 学習 (6 run: 2 source × 3-seed) ==="
  local vpy="$PROJECT_DIR/.venv/bin/python"
  cd "$PROJECT_DIR"

  # Relation-DETR 側 (frozen_src = relation_detr_seed42)
  for seed in 42 123 456; do
    log "  T1a Relation-DETR seed=$seed ..."
    FROZEN_SRC=relation_detr_seed42 CUDA_VISIBLE_DEVICES=0 "$vpy" scripts/train_t1a.py \
      --seed "$seed" --epochs 50 \
      --description t1a_frozen_src_relationdetr \
      > "$LOG_DIR/tecno_t1a_relation_seed${seed}.log" 2>&1
  done

  # AlignDETR 側 (frozen_src = aligndetr_s0frozen_seed42)
  for seed in 42 123 456; do
    log "  T1a AlignDETR seed=$seed ..."
    FROZEN_SRC=aligndetr_s0frozen_seed42 CUDA_VISIBLE_DEVICES=0 "$vpy" scripts/train_t1a.py \
      --seed "$seed" --epochs 50 \
      --description t1a_frozen_src_aligndetr \
      > "$LOG_DIR/tecno_t1a_aligndetr_seed${seed}.log" 2>&1
  done
  log "=== Phase 3 完了 (T1a 6 run) ==="
}

# --- main ---
main() {
  wait_for_gpu
  run_aligndetr_s0_frozen
  run_aligndetr_extract
  run_tecno_training
  log "=== 全 chain 完了 ==="
}

main "$@"
