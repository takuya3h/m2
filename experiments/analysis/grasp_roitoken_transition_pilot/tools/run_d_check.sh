#!/usr/bin/env bash
# 非公式 T-2026-11-09-grasp-roitoken-transition-pilot、Task D（G3）。
#  D-1 既定の挙動: 起点（origin/phase0 129e79b0）の dp_train.py・dp_model.py（$S/check/old/stage2pilot/、common.py は本体への
#      シンボリックリンク）と変更後の版で、RT を使わない同じ命令を回して出力を比べる。腕に数えない。
#      identity: GA 旗なし（空・正解・予測-noCF・入れ替え。T-2026-11-05 の信号）、D1-L1（既定の腕）
#      train:    GA 旗なし 正解の 1 epoch の試走（--fixed-epochs 1 --smoke）。run は experiments/phase1/grasprt_chk_dp{old,new}_*
#  D-2・D-3 RT の 8 設定 × 7 腕の identity（学習前の出力が塔単独と一致、出力射影を N(0, 0.05²) にすると変わる）
#   bash run_d_check.sh <GPU>
set -uo pipefail
GPU=$1
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-09-grasp-roitoken-transition-pilot
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
OUT=$S/d
GT=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/inputs/probe_signals
PRED=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/signals/A
mkdir -p "$OUT"
cd "$M"
sha256sum "$S/check/old/stage2pilot/dp_train.py" "$S/check/old/stage2pilot/dp_model.py" scripts/stage2pilot/dp_train.py \
  scripts/stage2pilot/dp_model.py > "$OUT/code_sha256.txt"
# shellcheck disable=SC1091
source .venv/bin/activate
# W&B は手元だけ（SPEC §6-9）。資格情報は読み込まない。WANDB_API_KEY は tracking の有効化の判定だけに使う仮の値
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
mkdir -p "$WANDB_DIR"
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
    --exp-prefix "grasprt_chk_dp$V" > "$OUT/train_GA_$V.log" 2>&1
  echo "[d1] train GA $V rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_GA_$V.log")"
done
for L in layer4 layer3; do for CT in roi_geo roi; do for K in 16 64; do
  python scripts/stage2pilot/dp_train.py identity --type RT --rt-dir "$S" --rt-layer $L --rt-content $CT --rt-k $K \
    --arms empty pred_CF geo union shuffle gt gtpred_CF --task-id "$TASK" --out "$OUT/identity_RT_${L}_${CT}_K$K.json" \
    > "$OUT/identity_RT_${L}_${CT}_K$K.log" 2>&1
  echo "[d2] identity RT $L $CT K$K rc=$?"
done; done; done
python scripts/stage2pilot/dp_train.py train --type RT --rt-dir "$S" --rt-layer layer4 --rt-content roi_geo --rt-k 64 --arm gtpred_CF \
  --seed 42 --fixed-epochs 1 --smoke --task-id "$TASK" --exp-prefix grasprt_chk_rt > "$OUT/train_RT_smoke.log" 2>&1
echo "[d2] train RT smoke rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_RT_smoke.log")"
