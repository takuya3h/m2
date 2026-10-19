#!/usr/bin/env bash
# Task B-2: 塔単独の val を bengio で再現する（非公式 T-2026-10-19-stage2-pilot-four-new-types）。val だけ。test は評価しない。
# 工程塔は scripts/stage2pilot/repro_ptower.py（本体の .venv）、検出塔は scripts/stage2pilot/pd_eval.py --cfg plain
# （重ねの BODY の .venv-relation-detr。直しの契約の handoff_bengio.md §6 R5 と同じ形）。
# 対照: 工程は別の時間ヘッド（P20 seed42 の 036）、検出は別 seed（123）の checkpoint（直しの契約の run_repro.sh と同じ選び方）。
# 出力は本契約の置き場（版管理下の json と、版管理外の予測）。
set -uo pipefail
WT=/home/ubuntu/slocal2/m2-four
OV=/home/ubuntu/slocal2/s2fix-bengio-body
MAIN=/home/ubuntu/slocal2/m2
STORE=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types
R=$WT/experiments/analysis/stage2_pilot_four/repro
mkdir -p "$R" "$STORE/identity"
cd "$WT"
export PYTHONPATH=src:scripts
export PYTHONUTF8=1
(
  # shellcheck disable=SC1091
  source "$MAIN/.venv/bin/activate"
  CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/repro_ptower.py --out "$R/ptower_val.json" > "$R/ptower_val.log" 2>&1
  echo "ptower rc=$?"
  CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/repro_ptower.py \
    --head "$MAIN/experiments/phase1/stage1_ptower_20_036_P20_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42/checkpoints/best.pth" \
    --out "$R/ptower_val_control_p20seed42head.json" > "$R/ptower_val_control.log" 2>&1
  echo "ptower control rc=$?"
) &
(
  # shellcheck disable=SC1091
  source "$OV/.venv-relation-detr/bin/activate"
  export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A
  (cd "$OV/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
    > "$R/env_check_det.txt" 2>&1
  CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --save-preds "$STORE/identity/plain_val_preds.json.gz" --out "$R/dtower_val_seed42.json" > "$R/dtower_val_seed42.log" 2>&1
  echo "dtower rc=$?"
  CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" \
    --out "$R/dtower_val_control_seed123.json" > "$R/dtower_val_control_seed123.log" 2>&1
  echo "dtower control rc=$?"
) &
wait
