#!/usr/bin/env bash
# 一時ドライバ: GPU1 で audit(4/5ch) → identity(4/5ch) → all 1epoch を順に実行。
set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"; cd "$ROOT"
export CUDA_HOME=/usr/local/cuda-11.8
export PATH="$ROOT/.venv-relation-detr/bin:$PATH"
export CUDA_VISIBLE_DEVICES=1
PY="$ROOT/.venv-relation-detr/bin/python"

echo "### audit 4ch ###"; "$PY" scripts/audit_l2_hand2det_l0.py --hand-channels 4 --seed 42 > logs/hand2det_audit_4ch.log 2>&1; echo "audit4 rc=$?"
echo "### audit 5ch ###"; "$PY" scripts/audit_l2_hand2det_l0.py --hand-channels 5 --seed 42 > logs/hand2det_audit_5ch.log 2>&1; echo "audit5 rc=$?"
echo "### identity 4ch ###"; HAND2DET_CH=4 HAND2DET_GPU=1 bash scripts/verify_hand2det_init_identity.sh > logs/hand2det_identity_4ch_run.log 2>&1; echo "id4 rc=$?"
echo "### identity 5ch ###"; HAND2DET_CH=5 HAND2DET_GPU=1 bash scripts/verify_hand2det_init_identity.sh > logs/hand2det_identity_5ch_run.log 2>&1; echo "id5 rc=$?"
echo "### train all 1epoch ###"; "$PY" scripts/train_hand2det.py --seed 42 --hand-channels 4 --trainable all --epochs 1 --run-name hand2det_1ep_4ch_all_seed42 > logs/hand2det_1ep_all.log 2>&1; echo "all rc=$?"
echo "### CHAIN DONE ###"
