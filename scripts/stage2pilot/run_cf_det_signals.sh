#!/usr/bin/env bash
# Task E-5（検出）: 交差適合用の検出塔に、学習に使っていない半分の動画にだけ信号を出させ、二本を合わせて
# train 10 本すべての交差適合版にする（非公式 T-2026-10-18-stage2-pilot-folda）。
#   H1 で学んだ塔 → H2 の動画、H2 で学んだ塔 → H1 の動画。作り方は確定塔（Task C）と同じ（extract_det_signals.py）。
#   GPU は CUDA_VISIBLE_DEVICES で渡す。
set -euo pipefail
BODY=/home/ubuntu/slocal2/m2
TASK=T-2026-10-18-stage2-pilot-folda
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
L=$BODY/experiments/analysis/stage2_pilot_folda/crossfit
cd "$BODY"
read -r H1 H2 < <(.venv/bin/python -c "
import json;c=json.load(open('$L/split.json'))['chosen'];print(','.join(c['H1']), ','.join(c['H2']))")
# shellcheck disable=SC1091
source .venv-relation-detr/bin/activate
export CUDA_HOME=/usr/local/cuda
for pair in "H1:$H2" "H2:$H1"; do
  HALF=${pair%%:*}; VIDEOS=${pair#*:}
  CK=$S/cf_dtower/stage2pilot_cf_dcoco_${HALF}_seed42/work/best_ap.pth
  [ -f "$CK" ] || { echo "checkpoint が無い: $CK" >&2; exit 2; }
  python scripts/stage2pilot/extract_det_signals.py --ckpt "$CK" --ann-dir data/annotations/egosurgery_tool_folds/A \
    --part train --videos "$VIDEOS" --out-dir "$S/signals/cf_det_from_$HALF" --k 11 --check-map \
    > "$L/extract_det_from_$HALF.log" 2>&1
  cp "$S/signals/cf_det_from_$HALF/record_train.json" "$L/record_det_from_$HALF.json"
done
deactivate
mkdir -p "$S/signals/cf"
for sig in D0 D0-RT D0-INST D0-INST-UQ; do
  .venv/bin/python scripts/stage2pilot/arm_signals.py merge \
    --inputs "$S/signals/cf_det_from_H1/${sig}_train.npz" "$S/signals/cf_det_from_H2/${sig}_train.npz" \
    --out "$S/signals/cf/${sig}_train.npz"
done
.venv/bin/python scripts/stage2pilot/time_check.py --signals-dir "$S/signals/cf" --parts train \
  --only D0,D0-RT,D0-INST,D0-INST-UQ --out "$L/time_alignment_cf_det.json"
echo "[cf_det_signals] 完了"
