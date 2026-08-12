#!/usr/bin/env bash
# 検出器改善「フル」研究の直列ドライバ（Phase I: Method A 3-seed / Phase II: hires C）。
# 全 GPU ジョブは 2-GPU 直列。各ステップは artifact ガードで冪等・再開可能。
# 起動: bash scripts/_detector_full_study.sh   （background 推奨）
# 監視: cat logs/detector_study_status.tsv / tail -f logs/detector_study.log
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
PROJ="$PWD"
REPO="$PROJ/third_party/Relation-DETR"
ACC="$PROJ/.venv-relation-detr/bin/accelerate"
CFG_AUG="configs/train_config_egosurgery_seed42_augstrong.py"
CFG_HIRES="configs/train_config_egosurgery_seed42_augstrong_hires.py"
STATUS="$PROJ/logs/detector_study_status.tsv"
mkdir -p "$PROJ/logs"

# ---- 検出器学習の入力（ローカル・検証済み）----
export CUDA_HOME=/usr/local/cuda-11.8
export EGO_ROOT="$PROJ/data/raw/ego"
export EGO_ANN_DIR="$PROJ/data/annotations/egosurgery_tool"
export RELDETR_COCO_CKPT="$PROJ/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"

stamp() { date +%H:%M:%S; }
mark()  { echo -e "$(stamp)\t$1\t$2" >> "$STATUS"; }
log()   { echo "[$(stamp)] $*" | tee -a "$PROJ/logs/detector_study.log"; }

# train_augstrong <seed> <outdir> <config>  — seed42 と同一レシピ(fp32・2GPU・12ep)
train_augstrong() {
  local seed="$1" outdir="$2" cfg="$3"
  local guard="$outdir/best_ap.pth"
  if [ -f "$guard" ]; then log "SKIP train seed=$seed (exists: $guard)"; mark "train_s$seed" SKIP; return 0; fi
  log "START train augstrong seed=$seed cfg=$(basename "$cfg") -> $outdir"
  mark "train_s$seed" START
  ( cd "$REPO" && RELDETR_OUTPUT_DIR="$outdir" CUDA_VISIBLE_DEVICES=0,1 \
      "$ACC" launch --num_processes 2 main.py --config-file "$cfg" --seed "$seed" \
      ) > "$PROJ/logs/train_$(basename "$outdir").log" 2>&1
  local rc=$?
  if [ ! -f "$guard" ]; then log "FAIL train seed=$seed (rc=$rc, no best_ap.pth) — 中断"; mark "train_s$seed" "FAIL(rc=$rc)"; return 1; fi
  log "DONE train seed=$seed"; mark "train_s$seed" DONE; return 0
}

# extract <tag> <ckpt> [jobs]  — 特徴抽出（gap/region/toolpres × splits）
extract() {
  local tag="$1" ckpt="$2" jobs="${3:-}"
  log "START extract tag=$tag jobs='${jobs:-ALL}'"
  mark "extract_$tag" START
  bash scripts/_extract_improved.sh "$tag" "$ckpt" "$jobs" \
      > "$PROJ/logs/extract_${tag}_runner.log" 2>&1
  local rc=$?
  log "DONE extract tag=$tag (rc=$rc)"; mark "extract_$tag" "DONE(rc=$rc)"; return 0
}

: > "$STATUS"
log "=== 検出器フル研究 開始 ==="

# ===== Phase I: Method A (strong aug) 3-seed =====
# seed42 の arm を完成（frozen42 toolpres / augstrong42 test）
[ -f data/processed/b2a_detsignal/relation_detr_seed42/val_toolpresence.npz ] \
  || extract relation_detr_seed42 "$REPO/checkpoints/incoming/seed42/best_ap.pth" "toolpres:train toolpres:val toolpres:test"
[ -f data/processed/stage1_features/relation_detr_augstrong_seed42/test_gap.npz ] \
  || extract relation_detr_augstrong_seed42 "$PROJ/experiments/detector_improve/augstrong_seed42/best_ap.pth" "gap:test region:test toolpres:test"

# frozen 123/456（ckpt 既存 → 抽出のみ）
[ -f data/processed/b2a_detsignal/relation_detr_seed123/test_toolpresence.npz ] \
  || extract relation_detr_seed123 "$REPO/checkpoints/incoming/seed123/best_ap.pth"
[ -f data/processed/b2a_detsignal/relation_detr_seed456/test_toolpresence.npz ] \
  || extract relation_detr_seed456 "$REPO/checkpoints/incoming/seed456/best_ap.pth"

# augstrong 123（学習 → 抽出）
train_augstrong 123 "$PROJ/experiments/detector_improve/augstrong_seed123" "$CFG_AUG" || exit 1
extract relation_detr_augstrong_seed123 "$PROJ/experiments/detector_improve/augstrong_seed123/best_ap.pth"

# augstrong 456（学習 → 抽出）
train_augstrong 456 "$PROJ/experiments/detector_improve/augstrong_seed456" "$CFG_AUG" || exit 1
extract relation_detr_augstrong_seed456 "$PROJ/experiments/detector_improve/augstrong_seed456/best_ap.pth"

log "=== Phase I 完了（Method A 3-seed 特徴が揃った）==="
mark "PHASE_I" DONE

# ===== Phase II: Method C (strong aug + hi-res 1200/2000) seed42 =====
train_augstrong 42 "$PROJ/experiments/detector_improve/augstrong_hires_seed42" "$CFG_HIRES" || exit 1
extract relation_detr_augstrong_hires_seed42 "$PROJ/experiments/detector_improve/augstrong_hires_seed42/best_ap.pth"

log "=== Phase II 完了（hires C 特徴が揃った）==="
mark "PHASE_II" DONE
log "=== 検出器フル研究 全ステップ完了 ==="
mark "ALL" DONE
