#!/usr/bin/env bash
# 案 C の 1 腕（fine-tune → 特徴の取り出し → 時間ヘッド → 補助の頭の val）を起こす（非公式 T-2026-11-01-grasp-pilot-g、Task F）
#   bash scripts/grasppilot/run_c.sh noaux|teacher|shuffled <gpu> [t_train.npz] [t_val.npz]
set -u
cd "$(dirname "$0")/../.."
ARM=$1; GPU=$2; TT=${3:-}; TV=${4:-}
TASK=T-2026-11-01-grasp-pilot-g
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
NAME=grasppilot2_C_${ARM}_seed42
RUN=experiments/phase1/$NAME
CK=$S/ptower/$NAME
mkdir -p "$RUN" "$CK"
source scripts/load_env.sh >/dev/null 2>&1 || true
export CUDA_VISIBLE_DEVICES=$GPU PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True PYTHONPATH=src
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv > "$RUN/gpu_at_start.txt"
PY=.venv/bin/python
T=(); [ -n "$TT" ] && T=(--targets "$TT")
$PY scripts/grasppilot/ptower_aux.py finetune --arm "$ARM" "${T[@]}" --run-dir "$RUN" --ckpt-dir "$CK" > "$RUN/finetune.log" 2>&1 || { echo $? > "$RUN/exit_code.txt"; exit 1; }
$PY scripts/grasppilot/ptower_aux.py extract --ckpt "$CK/last.pth" --out "$CK/feat_trainval.npz" > "$RUN/extract.log" 2>&1 || { echo $? > "$RUN/exit_code.txt"; exit 1; }
$PY scripts/grasppilot/ptower_aux.py head --features "$CK/feat_trainval.npz" --run-dir "$RUN" > "$RUN/head.log" 2>&1 || { echo $? > "$RUN/exit_code.txt"; exit 1; }
if [ -n "$TV" ]; then
  $PY scripts/grasppilot/ptower_aux.py auxval --ckpt "$CK/last.pth" --targets "$TV" --out "$RUN/aux_val.json" > "$RUN/auxval.log" 2>&1 || { echo $? > "$RUN/exit_code.txt"; exit 1; }
fi
cp "$CK/feat_trainval.json" "$RUN/feature_audit.json"
echo 0 > "$RUN/exit_code.txt"
