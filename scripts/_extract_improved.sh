#!/usr/bin/env bash
# 改善検出器から phase 用特徴を再抽出（GAP / region-token / tool-presence × train/val/test）。
# 使い方: bash scripts/_extract_improved.sh <frozen_tag> <ckpt_abs_path>
#   例: bash scripts/_extract_improved.sh relation_detr_augstrong_seed42 \
#         /home/ubuntu/slocal/m2/experiments/detector_improve/augstrong_seed42/best_ap.pth
# 2 GPU に 2 ジョブずつ振り分け。region/toolpres は env 上書き、GAP は --checkpoint/--out で指定。
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
TAG="${1:?frozen_tag}"; CKPT="${2:?ckpt abs path}"
PY="$PWD/.venv-relation-detr/bin/python"
MC="$PWD/third_party/Relation-DETR/configs/relation_detr/relation_detr_resnet50_egosurgery.py"
export CUDA_HOME=/usr/local/cuda-11.8
export PATH="$PWD/.venv-relation-detr/bin:$PATH"
export RELDETR_EXTRACT_CKPT="$CKPT"
export RELDETR_FROZEN_TAG="$TAG"
mkdir -p logs "data/processed/stage1_features/$TAG"

dispatch() { # <gpu> <type:split>
  local gpu="$1" job="$2"; local typ="${job%%:*}" split="${job##*:}"
  local t0; t0=$(date +%H:%M:%S); echo "[$t0] START gpu$gpu $job"
  local log="logs/extract_${TAG}_${typ}_${split}.log"
  case "$typ" in
    gap) CUDA_VISIBLE_DEVICES="$gpu" $PY scripts/extract_stage1_features.py \
           --manifest "data/processed/phase_manifest/$split.json" --model-config "$MC" \
           --checkpoint "$CKPT" --out "data/processed/stage1_features/$TAG/${split}_gap.npz" > "$log" 2>&1 ;;
    region) CUDA_VISIBLE_DEVICES="$gpu" $PY scripts/extract_t1a_regiontoken.py --subset "$split" > "$log" 2>&1 ;;
    toolpres) CUDA_VISIBLE_DEVICES="$gpu" $PY scripts/extract_b2a_detsignal.py --subset "$split" > "$log" 2>&1 ;;
  esac
  echo "[$(date +%H:%M:%S)] DONE gpu$gpu $job (rc=$?)"
}

# 第3引数で抽出対象(type:split ...)を上書き可能。未指定なら全 feature×split。
if [ -n "${3:-}" ]; then
  read -ra JOBS <<< "$3"
else
  JOBS=( "gap:train" "region:train" "toolpres:train" \
         "gap:val" "region:val" "toolpres:val" \
         "gap:test" "region:test" "toolpres:test" )
fi
i=0
while [ $i -lt ${#JOBS[@]} ]; do
  dispatch 0 "${JOBS[$i]}" & pa=$!
  pb=""; jb="${JOBS[$((i+1))]:-}"; [ -n "$jb" ] && { dispatch 1 "$jb" & pb=$!; }
  wait "$pa"; [ -n "$pb" ] && wait "$pb"
  i=$((i+2))
done
echo "[$(date +%H:%M:%S)] 抽出完了 TAG=$TAG"
echo "=== 生成物 ==="
ls -la "data/processed/stage1_features/$TAG/" "data/processed/t1a_regiontoken/$TAG/" "data/processed/b2a_detsignal/$TAG/" 2>/dev/null