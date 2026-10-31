#!/usr/bin/env bash
# 非公式 T-2026-10-31-grasp-pilot-probe、Task B-3・B-4。材料の要約値の照合と、塔単独の val の andrew での再現。
# 対照: 工程は別の時間ヘッド（P20 seed 42）、検出は別 seed（123）の checkpoint。val だけ。test は評価しない。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe
R=$M/experiments/analysis/grasp_pilot_probe/repro
mkdir -p "$R" "$S/b"
cd "$M"
export PYTHONPATH=src:scripts PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda/efros_ptower
sha256sum "$OLD/data/processed/stage1_features/p15ctl_coco_lr0.0001_foldA_seed42/all_gap.npz" \
  "$OLD/experiments/phase1/stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42/checkpoints/best.pth" \
  "$OLD/experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42/checkpoints/best.pth" \
  "$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  "$M"/data/processed/phase_manifest/{phase_vocab,train,val}.json \
  "$M"/data/annotations/egosurgery_tool_folds/A/instances_{train,val}.json > "$R/b3_sha256.txt"
.venv/bin/python scripts/stage2pilot/repro_ptower.py --out "$R/ptower_val.json" > "$R/ptower_val.log" 2>&1; echo "ptower rc=$?"
.venv/bin/python scripts/stage2pilot/repro_ptower.py \
  --head "$M/experiments/phase1/stage1_ptower_20_036_P20_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42/checkpoints/best.pth" \
  --out "$R/ptower_val_control_p20head.json" > "$R/ptower_val_control.log" 2>&1; echo "ptower control rc=$?"
# shellcheck disable=SC1091
source "$M/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$M EGO_ROOT=$M/data/raw/ego EGO_ANN_DIR=$M/data/annotations/egosurgery_tool_folds/A
(cd "$M/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") > "$R/env_check_det.txt" 2>&1
( CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --save-preds "$S/b/plain_val_preds.json.gz" --out "$R/dtower_val_seed42.json" > "$R/dtower_val_seed42.log" 2>&1; echo "dtower rc=$?" ) &
( CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$M/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" \
    --out "$R/dtower_val_control_seed123.json" > "$R/dtower_val_control_seed123.log" 2>&1; echo "dtower control rc=$?" ) &
wait
