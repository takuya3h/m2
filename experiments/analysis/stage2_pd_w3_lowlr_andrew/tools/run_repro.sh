#!/usr/bin/env bash
# Task B-2: 検出塔の塔単独の val を andrew で再現する（非公式 T-2026-11-09-stage2-pd-w3-lowlr-andrew。前回 T-2026-11-01-stage2-w23-andrew の repro/run_repro.sh の写し。変えたのは置き場だけ）。val だけ。test は評価しない。
# 道具は four-new-types の run_repro_andrew.sh と同じ pd_eval.py --cfg plain（出力の json の task_id 欄は道具の固定値）。
# 対照: 別 seed（123）の checkpoint。塔単独の予測は本契約の版管理外の置き場へ（Task C の恒等性の基準）。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-09-stage2-pd-w3-lowlr-andrew
R=$M/experiments/analysis/stage2_pd_w3_lowlr_andrew/repro
mkdir -p "$R" "$S/identity"
cd "$M"
export PYTHONPATH=src:scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
(cd "$M/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$R/env_check_det.txt" 2>&1
(
  CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --save-preds "$S/identity/plain_val_preds.json.gz" --out "$R/dtower_val_seed42.json" > "$R/dtower_val_seed42.log" 2>&1
  echo "dtower rc=$?"
) &
(
  CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" \
    --out "$R/dtower_val_control_seed123.json" > "$R/dtower_val_control_seed123.log" 2>&1
  echo "dtower control rc=$?"
) &
wait
