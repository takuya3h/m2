#!/usr/bin/env bash
# Task E-2/E-5（工程）: 工程の交差適合用の塔を一本学び、学習に使っていない半分の動画にだけ P0 を出す
# （非公式 T-2026-10-18-stage2-pilot-folda）。
#
#   scripts/stage2pilot/run_cf_ptower.sh <H1|H2>      GPU は CUDA_VISIBLE_DEVICES で渡す
#   scripts/stage2pilot/run_cf_ptower.sh merge        二本の P0 を合わせ、PD の正解予測-CF の train の信号を組む
set -euo pipefail
WHAT="$1"
BODY=/home/ubuntu/slocal2/m2
TASK=T-2026-10-18-stage2-pilot-folda
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
L=$BODY/experiments/analysis/stage2_pilot_folda/crossfit
cd "$BODY"
# shellcheck disable=SC1091
source .venv/bin/activate
# shellcheck disable=SC1091
source scripts/load_env.sh > /dev/null 2>&1
export PYTHONPATH=src:scripts
if [ "$WHAT" = merge ]; then
  python scripts/stage2pilot/arm_signals.py merge --inputs "$S/signals/cf_phase_from_H1/P0_train.npz" \
    "$S/signals/cf_phase_from_H2/P0_train.npz" --out "$S/signals/cf/P0_train.npz"
  mkdir -p "$S/arms/PD"
  python scripts/stage2pilot/arm_signals.py concat --inputs "$S/signals/final/P-GT_train.npz" \
    "$S/signals/cf/P0_train.npz" --out "$S/arms/PD/gtpred_CF_train.npz"
  python scripts/stage2pilot/time_check.py --signals-dir "$S/signals/cf" --parts train --only P0 \
    --out "$L/time_alignment_cf_phase.json"
  exit 0
fi
HALF="$WHAT"
OTHER=$(python -c "
import json;c=json.load(open('$L/split.json'))['chosen'];print(','.join(c['H2' if '$HALF'=='H1' else 'H1']))")
LOG=$L/cf_ptower_$HALF.log
python scripts/stage2pilot/cf_ptower.py --half "$HALF" --action finetune --device cuda:0 >> "$LOG" 2>&1
FT=$(ls -d experiments/phase1/stage2pilot_cf_ptower_*_ft_coco_lr0.0001_foldA${HALF}_seed42 | tail -1)
python scripts/stage2pilot/cf_ptower.py --half "$HALF" --action extract --device cuda:0 \
  --checkpoint "$BODY/$FT/checkpoints/best.pth" >> "$LOG" 2>&1
python scripts/stage2pilot/cf_ptower.py --half "$HALF" --action train --device cuda:0 >> "$LOG" 2>&1
HEAD=$(ls -d experiments/phase1/stage2pilot_cf_ptower_*_P15_C_L8_w0.3_h30_foldA${HALF}_coco_lr0.0001_seed42 | tail -1)
python scripts/stage2pilot/phase_signals.py signals --head "$BODY/$HEAD/checkpoints/best.pth" \
  --cache "$S/cf_ptower/$HALF/all_gap.npz" --videos "$OTHER" --part train \
  --out-dir "$S/signals/cf_phase_from_$HALF" >> "$LOG" 2>&1
cp "$S/signals/cf_phase_from_$HALF/record_phase_train.json" "$L/record_phase_from_$HALF.json"
echo "[cf_ptower] $HALF 完了 ft=$FT head=$HEAD"
