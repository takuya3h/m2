#!/usr/bin/env bash
# 追加 T1a ablation 2 種:
#   variant A: T1a per-tool Top3 joint mask (Bipolar/NH/Scalpel 同時 mask) 3-seed
#   variant B: T1a-RegionOnly + per-tool mask Top3 joint (RegionOnly での Top3 mask) 3-seed
# 合計 6 run、2 GPU 並列、約 1.5h
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
VENV="$ROOT/.venv/bin/python"
[ -f "$ROOT/.env" ] && { set -a; source "$ROOT/.env"; set +a; }

run_t1a_top3() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --mask-region-tool-dims 0,6,9 \
    --description t1a_region_mask_top3 \
    > "logs/t1a_top3_seed${seed}.log" 2>&1
}

run_t1a_ro_top3() {
  local seed="$1" gpu="$2"
  CUDA_VISIBLE_DEVICES="$gpu" "$VENV" scripts/train_t1a.py \
    --seed "$seed" --epochs 50 --region-only --mask-region-tool-dims 0,6,9 \
    --description t1a_region_only_mask_top3 \
    > "logs/t1a_ro_top3_seed${seed}.log" 2>&1
}

for S in 42 123 456; do
  echo "[seed $S] T1a-Top3(GPU0) + T1a-RO-Top3(GPU1) ..."
  run_t1a_top3 "$S" 0 & pa=$!
  run_t1a_ro_top3 "$S" 1 & pb=$!
  wait "$pa"; wait "$pb"
done
echo "================ 完了 ================"
for variant in t1a_top3 t1a_ro_top3; do
  for S in 42 123 456; do
    echo "-- ${variant} seed${S} --"
    tail -1 "logs/${variant}_seed${S}.log"
  done
done
