#!/usr/bin/env bash
# 非公式 T-2026-11-01-stage2-w23-bengio、Task D。PD の 16 本（利用者の決定 2026-11-02: P2L の W2・W3、P3 の W3、P1 の W3 の各 4 腕）を
# 8 本の列（GPU 2 枚 × 4）で回す。列 k は GPU k % 2 を使い、表の k 番目と k+8 番目を順に回す。既に在る run は台本が拒む（exit 4）。
#
#   bash pd_queue.sh <列>           1 本の列を回す（0〜7）
set -uo pipefail
LANE=$1
CODE=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio
SPECS=()
for TW in "P2L W2" "P2L W3" "P3 W3" "P1 W3"; do
  for ARM in empty pred_noCF gt shuffle; do
    read -r T W <<< "$TW"
    SPECS+=("$T $ARM $W")
  done
done
export CUDA_VISIBLE_DEVICES=$((LANE % 2))
cd "$CODE"
for k in "${!SPECS[@]}"; do
  [ $((k % 8)) = "$LANE" ] || continue
  read -r T ARM W <<< "${SPECS[$k]}"
  echo "[pd_queue $LANE] $(TZ=Asia/Tokyo date '+%F %T JST') start $T $ARM $W gpu=$CUDA_VISIBLE_DEVICES"
  bash scripts/w23/run_pd_w23_bengio.sh "$T" "$ARM" "$W"
  echo "[pd_queue $LANE] $(TZ=Asia/Tokyo date '+%F %T JST') end $T $ARM $W rc=$?"
done
