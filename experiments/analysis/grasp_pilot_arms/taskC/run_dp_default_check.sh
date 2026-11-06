#!/usr/bin/env bash
# 非公式 T-2026-11-06-grasp-pilot-arms、Task C-3（既定の挙動が変わらない）。起点（origin/phase0 046a5183）の dp_train.py と
# 変更後の dp_train.py で、--grasp-no-flag を渡さない同じ命令を回して出力を比べる。腕に数えない。
# T-2026-11-01-stage2-w23-bengio の run_dp_default_check.sh と同じ形で、型を GA（旗あり 30 次元。二本目の信号）と D1-L1 にした。
#   identity: GA（空・正解・予測-noCF・入れ替え）、D1-L1（既定の腕）
#   train:    GA 正解の 1 epoch の試走（--fixed-epochs 1 --smoke）。run は experiments/phase1/grasparms_chk_dp{old,new}_*
#   bash run_dp_default_check.sh <GPU>
set -uo pipefail
GPU=$1
M=/home/ubuntu/slocal2/m2
TASK=T-2026-11-06-grasp-pilot-arms
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
OUT=$M/experiments/analysis/grasp_pilot_arms/taskC/dp_default
GT=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-05-grasp-tower-rebuild/inputs/probe_signals
PRED2=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-g/signals/A   # 二本目の旗ありの予測の g（読むだけ）
mkdir -p "$OUT" "$S/check"
cd "$M"
git show 046a51839cc240b9d6a6e542f7dd27f1f9e8ef2b:scripts/stage2pilot/dp_train.py > "$S/check/dp_train_old.py"
sha256sum "$S/check/dp_train_old.py" scripts/stage2pilot/dp_train.py > "$OUT/code_sha256.txt"
# shellcheck disable=SC1091
source .venv/bin/activate
# W&B は手元だけ（SPEC §7-10）。資格情報は読み込まない。WANDB_API_KEY は tracking の有効化の判定だけに使う仮の値
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
mkdir -p "$WANDB_DIR"
export PYTHONPATH=src:scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES=$GPU
G=(--grasp-signal-dir "$GT" --grasp-pred-dir "$PRED2")
for V in old new; do
  P=scripts/stage2pilot/dp_train.py
  [ $V = old ] && P=$S/check/dp_train_old.py
  python "$P" identity --type GA --arms empty gt pred_noCF shuffle "${G[@]}" --task-id "$TASK" \
    --out "$OUT/identity_GA_$V.json" > "$OUT/identity_GA_$V.log" 2>&1
  echo "[default] identity GA $V rc=$?"
  python "$P" identity --type D1-L1 --task-id "$TASK" --out "$OUT/identity_D1-L1_$V.json" > "$OUT/identity_D1-L1_$V.log" 2>&1
  echo "[default] identity D1-L1 $V rc=$?"
  python "$P" train --type GA --arm gt --seed 42 --fixed-epochs 1 --smoke "${G[@]}" --task-id "$TASK" \
    --exp-prefix "grasparms_chk_dp$V" > "$OUT/train_GA_$V.log" 2>&1
  echo "[default] train GA $V rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_GA_$V.log")"
done
