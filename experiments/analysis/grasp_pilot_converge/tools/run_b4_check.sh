#!/usr/bin/env bash
# 非公式 T-2026-11-09-grasp-pilot-converge、Task B-4（既定の挙動と恒等性）。腕に数えない run は experiments/phase1/grasprc_chk_*。
#  1 起点（26722ffd）の版と --converge を足した版で、GA 旗なし（空・予測-noCF・入れ替え）と D1-L1 の identity、GA 予測-noCF の
#    1 epoch の試走（--fixed-epochs 1 --smoke）を比べる（compare_default.py）
#  2 --fixed-epochs の経路の RT・TW が変わらない: 前の予備の run と同じ命令（識別子と接頭辞だけ違う）を本契約の版で回し直す（compare_repeat.py）
#  3 恒等性: RT 8 設定 × 7 腕、TW 12 件 × 8 腕（W1・W2・W3）、GA 3 腕（学習前の出力が塔単独と一致、出力射影を N(0, 0.05²) で変わる）
#  4 収束規則の試走: GA 空の --converge（学習率が optimizer の群で落ちることを history で見る）
#   bash run_b4_check.sh <GPU>
set -uo pipefail
GPU=$1
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-09-grasp-pilot-converge
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
P=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-grasp-roitoken-transition-pilot
OUT=$S/b4check
GT=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/inputs/probe_signals
PRED=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/A
mkdir -p "$OUT"
cd "$M"
sha256sum "$S/check/old/stage2pilot/dp_train.py" scripts/stage2pilot/dp_train.py scripts/stage2pilot/dp_model.py > "$OUT/code_sha256.txt"
# shellcheck disable=SC1091
source .venv/bin/activate
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
mkdir -p "$WANDB_DIR"
export PYTHONPATH=$M/src:$M/scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
G=(--grasp-signal-dir "$GT" --grasp-pred-dir "$PRED" --grasp-no-flag)
for V in old new; do
  PY=scripts/stage2pilot/dp_train.py
  [ $V = old ] && PY=$S/check/old/stage2pilot/dp_train.py
  python "$PY" identity --type GA --arms empty pred_noCF shuffle "${G[@]}" --task-id "$TASK" --out "$OUT/identity_GA_$V.json" > "$OUT/identity_GA_$V.log" 2>&1
  echo "[b4-1] identity GA $V rc=$?"
  python "$PY" identity --type D1-L1 --task-id "$TASK" --out "$OUT/identity_D1-L1_$V.json" > "$OUT/identity_D1-L1_$V.log" 2>&1
  echo "[b4-1] identity D1-L1 $V rc=$?"
  python "$PY" train --type GA --arm pred_noCF --seed 42 --fixed-epochs 1 --smoke "${G[@]}" --task-id "$TASK" \
    --exp-prefix "grasprc_chk_dp$V" > "$OUT/train_GA_$V.log" 2>&1
  echo "[b4-1] train GA $V rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_GA_$V.log")"
done
python scripts/stage2pilot/dp_train.py train --type RT --rt-dir "$P" --rt-layer layer4 --rt-content roi_geo --rt-k 16 --arm pred_CF \
  --seed 42 --fixed-epochs 4 --task-id "$TASK" --exp-prefix grasprc_chk_rt > "$OUT/train_RT_repeat.log" 2>&1
echo "[b4-2] RT repeat rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_RT_repeat.log")"
python scripts/stage2pilot/dp_train.py train --type TW --tw-dir "$P" --tw-form b --tw-L 8 --tw-k 64 --scope W2 --arm pred_CF \
  --seed 42 --fixed-epochs 4 --task-id "$TASK" --exp-prefix grasprc_chk_tw > "$OUT/train_TW_repeat.log" 2>&1
echo "[b4-2] TW repeat rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_TW_repeat.log")"
for L in layer4 layer3; do for CT in roi_geo roi; do for K in 16 64; do
  python scripts/stage2pilot/dp_train.py identity --type RT --rt-dir "$P" --rt-layer $L --rt-content $CT --rt-k $K \
    --arms empty pred_CF geo union shuffle gt gtpred_CF --task-id "$TASK" --out "$OUT/identity_RT_${L}_${CT}_K$K.json" \
    > "$OUT/identity_RT_${L}_${CT}_K$K.log" 2>&1
  echo "[b4-3] identity RT $L $CT K$K rc=$?"
done; done; done
for W in W1 W2 W3; do for F in a b; do for L in 8 32; do
  python scripts/stage2pilot/dp_train.py identity --type TW --tw-dir "$P" --tw-form $F --tw-L $L --tw-k 64 --scope $W \
    --arms empty t1 pred_CF perm union shuffle gt gtpred_CF --task-id "$TASK" --out "$OUT/identity_TW_${W}_${F}_L$L.json" \
    > "$OUT/identity_TW_${W}_${F}_L$L.log" 2>&1
  echo "[b4-3] identity TW $W $F L$L rc=$?"
done; done; done
python scripts/stage2pilot/dp_train.py train --type GA --arm empty --seed 42 --converge "${G[@]}" --task-id "$TASK" \
  --exp-prefix grasprc_chk_conv > "$OUT/train_GA_converge.log" 2>&1
echo "[b4-4] GA converge rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_GA_converge.log")"
