#!/usr/bin/env bash
# 検出塔の塔単独の val を andrew で再現する（非公式 T-2026-10-19-stage2-pilot-four-new-types。工程から検出の
# decoder-xattn を andrew で回す前の準備）。val だけ。test は評価しない。
# run_repro_bengio.sh の検出塔の部分を andrew の環境に合わせた: andrew には重ねの BODY が無いので、BODY は
# main の作業場所（third_party/Relation-DETR・.venv-relation-detr・data・checkpoint を読むだけ）、台本は worktree の
# pd_eval.py。PYTHONDONTWRITEBYTECODE=1 で main の third_party に .pyc を書かない。
# 対照: 別 seed（123）の checkpoint（直しの契約の run_repro.sh・bengio の台本と同じ選び方）。
# 出力は本契約の置き場（worktree の版管理下の json と、andrew の版管理外の予測）。
set -uo pipefail
WT=/home/ubuntu/slocal2/m2-four-andrew
MAIN=/home/ubuntu/slocal2/m2
STORE=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types
R=$WT/experiments/analysis/stage2_pilot_four/repro
mkdir -p "$R" "$STORE/identity"
cd "$WT"
export PYTHONPATH=src:scripts
export PYTHONUTF8=1
export PYTHONDONTWRITEBYTECODE=1
# shellcheck disable=SC1091
source "$MAIN/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$MAIN EGO_ROOT=$MAIN/data/raw/ego EGO_ANN_DIR=$MAIN/data/annotations/egosurgery_tool_folds/A
(cd "$MAIN/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") \
  > "$R/env_check_det_andrew.txt" 2>&1
(
  CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$MAIN/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
    --save-preds "$STORE/identity/plain_val_preds.json.gz" --out "$R/dtower_val_seed42_andrew.json" > "$R/dtower_val_seed42_andrew.log" 2>&1
  echo "dtower rc=$?"
) &
(
  CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/pd_eval.py --cfg plain \
    --det-ckpt "$MAIN/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" \
    --out "$R/dtower_val_control_seed123_andrew.json" > "$R/dtower_val_control_seed123_andrew.log" 2>&1
  echo "dtower control rc=$?"
) &
wait
