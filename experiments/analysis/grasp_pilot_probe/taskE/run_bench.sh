#!/usr/bin/env bash
# 非公式 T-2026-10-31-grasp-pilot-probe、Task E-1・E-3 の計測。案 B の学習と GPU を分けて測る（--shared の印）。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
R=$M/experiments/analysis/grasp_pilot_probe/taskE
cd "$M"
export PYTHONPATH=src:scripts PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1
( CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/grasppilot/g_bench.py bench --cand mmdet --shared --out "$R/e1_bench_mmdet.json" > "$R/e1_bench_mmdet.log" 2>&1; echo "mmdet rc=$?"
  CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/grasppilot/tower_bench.py ptower --shared --out "$R/e3_bench_ptower.json" > "$R/e3_bench_ptower.log" 2>&1; echo "ptower rc=$?" ) &
( CUDA_VISIBLE_DEVICES=1 .venv/bin/python scripts/grasppilot/g_bench.py bench --cand hf --shared --out "$R/e1_bench_hf.json" > "$R/e1_bench_hf.log" 2>&1; echo "hf rc=$?"
  ( source "$M/.venv-relation-detr/bin/activate"
    export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
    CUDA_VISIBLE_DEVICES=1 python scripts/grasppilot/tower_bench.py dtower --shared --out "$R/e3_bench_dtower.json" > "$R/e3_bench_dtower.log" 2>&1; echo "dtower rc=$?" ) ) &
wait
