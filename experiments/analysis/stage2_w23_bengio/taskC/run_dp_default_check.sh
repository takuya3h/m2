#!/usr/bin/env bash
# 非公式 T-2026-11-01-stage2-w23-bengio、Task C-1（既定の挙動が変わらない）。起点（392cf287）の dp_train.py と
# 変更後の dp_train.py で、--scope を渡さない同じ命令を回して出力を比べる。腕に数えない。
#   identity: D1-L1（予測-noCF・正解）、TH（ゲートを持つ型）
#   train:    D1-L1 正解と TH 正解の 1 epoch の試走（--fixed-epochs 1 --smoke）。run は experiments/phase1/w23b_chk_dp{old,new}_*
#
#   bash run_dp_default_check.sh <GPU>
set -uo pipefail
GPU=$1
CODE=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio
OUT=$CODE/experiments/analysis/stage2_w23_bengio/taskC/dp_default
TASK=T-2026-11-01-stage2-w23-bengio
mkdir -p "$OUT" "$S/check"
cd "$CODE"
git show 392cf287615b45f76829c7fa7f4e5cb39d4444c5:scripts/stage2pilot/dp_train.py > "$S/check/dp_train_old.py"
sha256sum "$S/check/dp_train_old.py" scripts/stage2pilot/dp_train.py > "$OUT/code_sha256.txt"
# shellcheck disable=SC1091
source .venv/bin/activate
# W&B は手元だけに記録する（契約 §7.10 は外部への送信を task-report に限る。利用者の決定 2026-11-02、三本目と同じ形）。
# 資格情報は読み込まない。WANDB_API_KEY は tracking の有効化の判定だけに使う仮の値（offline では送らない）
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$S/wandb WANDB_SILENT=true
mkdir -p "$WANDB_DIR"
export PYTHONPATH=src:scripts PYTHONUTF8=1 CUDA_VISIBLE_DEVICES=$GPU
for V in old new; do
  P=scripts/stage2pilot/dp_train.py
  [ $V = old ] && P=$S/check/dp_train_old.py
  for T in D1-L1 TH; do
    python "$P" identity --type "$T" --task-id "$TASK" --out "$OUT/identity_${T}_$V.json" > "$OUT/identity_${T}_$V.log" 2>&1
    echo "[default] identity $T $V rc=$?"
    python "$P" train --type "$T" --arm gt --seed 42 --fixed-epochs 1 --smoke --task-id "$TASK" \
      --exp-prefix "w23b_chk_dp$V" > "$OUT/train_${T}_$V.log" 2>&1
    echo "[default] train $T $V rc=$? $(grep DP_RUN_COMPLETE "$OUT/train_${T}_$V.log")"
  done
done
