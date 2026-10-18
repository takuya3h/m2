#!/usr/bin/env bash
# Task D-5 / 完了判定 k（PD）: 空の腕の陰性対照（非公式 T-2026-10-18-stage2-pilot-folda）。
# 空の腕で学んだ重み（best_t1b.pth）を読み、(1) 零の信号で評価して run 自身の最良の予測と一致することを確かめ、
# (2) 零の代わりに確定塔の予測 P0 の val を入れて (1) との出力の差の最大を出す。
#
#   scripts/stage2pilot/run_pd_negctl.sh <型: P1-W1|P1-W2|P2L|P3>    GPU は CUDA_VISIBLE_DEVICES で渡す
set -uo pipefail
TYPE="$1"
BODY=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
O=$BODY/experiments/analysis/stage2_pilot_folda/negctl
case "$TYPE" in
  P1-W1|P1-W2) IFACE=film ;;
  P2L) IFACE=clsbias_lin ;;
  P3) IFACE=query ;;
  *) echo "型が不明: $TYPE" >&2; exit 2 ;;
esac
RUN=stage2pilot_pd_${TYPE}_empty_seed42
W=$BODY/experiments/phase1/$RUN
CK=$S/pd_ckpt/$RUN/best_t1b.pth
[ -f "$CK" ] || { echo "空の腕の重みが無い: $CK" >&2; exit 3; }
mkdir -p "$O" "$S/negctl"
cd "$BODY"
# shellcheck disable=SC1091
source .venv-relation-detr/bin/activate
export CUDA_HOME=/usr/local/cuda EGO_ANN_DIR=$BODY/data/annotations/egosurgery_tool_folds/A EGO_ROOT=$BODY/data/raw/ego
CFG=configs/stage2pilot/pd_${IFACE}_d9.py
python scripts/stage2pilot/pd_eval.py --cfg "$CFG" --iface-state "$CK" --zero-ctx \
  --ref-preds "$W/predictions/val_ctrl_best.json.gz" --save-preds "$S/negctl/${TYPE}_zero.json.gz" \
  --out "$O/${TYPE}_zero.json" > "$O/${TYPE}_zero.log" 2>&1
echo "[negctl] $TYPE zero rc=$?"
python scripts/stage2pilot/pd_eval.py --cfg "$CFG" --iface-state "$CK" --signal-val "$S/signals/final/P0_val.npz" \
  --ref-preds "$S/negctl/${TYPE}_zero.json.gz" --out "$O/${TYPE}_pred.json" > "$O/${TYPE}_pred.log" 2>&1
echo "[negctl] $TYPE pred rc=$?"
