#!/usr/bin/env bash
# 非公式 T-2026-11-09-grasp-roitoken-transition-pilot、案 5 の追加（利用者の依頼 2026-11-09）の Task D（G3）。
#  D-1 既定の挙動: 起点（129e79b0）の版と TW を足した版で GA 旗なし・D1-L1 の identity と GA の 1 epoch の試走を比べる
#      （run は experiments/phase1/grasprt_chk2_dp{old,new}_*）
#  D-1b 案 3 の RT が変わらない: 学習済みの RT の 1 本（layer4-roi_geo-K16 の pred_CF）を TW を足した版で同じ命令で回し直す
#      （run は experiments/phase1/grasprt_chk2_rt_*）
#  D-2・D-3 TW の W1・W2・W3 × 形 a・b × L 8・32 の identity（8 腕）
#  D-4 TW の W2 の 1 epoch の試走（腕に数えない）
#   bash run_d2_check.sh <GPU>
set -uo pipefail
GPU=$1
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-09-grasp-roitoken-transition-pilot
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
OUT=$S/d2
GT=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/inputs/probe_signals
PRED=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/A
mkdir -p "$OUT"
cd "$M"
sha256sum "$S/check/old/stage2pilot/dp_train.py" "$S/check/old/stage2pilot/dp_model.py" scripts/stage2pilot/dp_train.py \
  scripts/stage2pilot/dp_model.py > "$OUT/code_sha256.txt"
# shellcheck disable=SC1091
source .venv/bin/activate
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
export PYTHONPATH=$M/src:$M/scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
G=(--grasp-signal-dir "$GT" --grasp-pred-dir "$PRED" --grasp-no-flag)
for V in old new; do
  P=scripts/stage2pilot/dp_train.py
  [ $V = old ] && P=$S/check/old/stage2pilot/dp_train.py
  python "$P" identity --type GA --arms empty gt pred_noCF shuffle "${G[@]}" --task-id "$TASK" \
    --out "$OUT/identity_GA_$V.json" > "$OUT/identity_GA_$V.log" 2>&1
  echo "[d1] identity GA $V rc=$?"
  python "$P" identity --type D1-L1 --task-id "$TASK" --out "$OUT/identity_D1-L1_$V.json" > "$OUT/identity_D1-L1_$V.log" 2>&1
  echo "[d1] identity D1-L1 $V rc=$?"
  python "$P" train --type GA --arm gt --seed 42 --fixed-epochs 1 --smoke "${G[@]}" --task-id "$TASK" \
    --exp-prefix "grasprt_chk2_dp$V" > "$OUT/train_GA_$V.log" 2>&1
  echo "[d1] train GA $V rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_GA_$V.log")"
done
python scripts/stage2pilot/dp_train.py train --type RT --rt-dir "$S" --rt-layer layer4 --rt-content roi_geo --rt-k 16 --arm pred_CF \
  --seed 42 --fixed-epochs 4 --task-id "$TASK" --exp-prefix grasprt_chk2_rt > "$OUT/train_RT_repeat.log" 2>&1
echo "[d1b] train RT repeat rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_RT_repeat.log")"
for W in W1 W2 W3; do for F in a b; do for L in 8 32; do
  python scripts/stage2pilot/dp_train.py identity --type TW --tw-dir "$S" --tw-form $F --tw-L $L --tw-k 64 --scope $W \
    --arms empty t1 pred_CF perm union shuffle gt gtpred_CF --task-id "$TASK" --out "$OUT/identity_TW_${W}_${F}_L$L.json" \
    > "$OUT/identity_TW_${W}_${F}_L$L.log" 2>&1
  echo "[d2] identity TW $W $F L$L rc=$?"
done; done; done
python scripts/stage2pilot/dp_train.py train --type TW --tw-dir "$S" --tw-form b --tw-L 32 --tw-k 64 --scope W2 --arm pred_CF \
  --seed 42 --fixed-epochs 1 --smoke --task-id "$TASK" --exp-prefix grasprt_chk2_tw > "$OUT/train_TW_smoke.log" 2>&1
echo "[d4] train TW W2 smoke rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_TW_smoke.log")"
