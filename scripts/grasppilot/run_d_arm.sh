#!/usr/bin/env bash
# 非公式 T-2026-11-01-grasp-pilot-d — 案 D の腕を 1 本起動する（bengio、GPU 1 枚）。
#
#   CUDA_VISIBLE_DEVICES=<g> bash scripts/grasppilot/run_d_arm.sh <腕> [port]
#
# 腕: none（補助損失なし、重み 0）、gteach（G を教師、0.3）、shuf（入れ替えた教師、0.3）、
#     smoke（試走。一本目の正解の q、0.3、train 8 枚・val 4 枚・12 epoch）、
#     smoke_nococo（対照。COCO の重みの経路を存在しない経路にして 1 epoch）
# 3 腕で同じもの: コード（$S/code の写し）、学習設定、起動の引数。違うのは GRASP_AUX_WEIGHT と GRASP_TARGETS だけ。
# 処方: 記録の検出塔と同じ設定（d_train_config.py）を、GPU 1 枚・batch 2・勾配を 2 回ためる形で回す（SPEC §3.1）。
set -uo pipefail
ARM=${1:?arm}
PORT=${2:-29811}
M=/home/ubuntu/slocal2/m2
OV=/home/ubuntu/slocal2/s2fix-bengio-body
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-grasp-pilot-d
TASK=T-2026-11-01-grasp-pilot-d
SRC=$M/scripts/grasppilot
CODE=$S/code/$(cat "$SRC/grasp_aux_d.py" "$SRC/d_model_config.py" "$SRC/d_train_config.py" | sha256sum | cut -c1-16)
EPOCHS=15
ANN=$OV/data/annotations/egosurgery_tool_folds/A
COCO=$OV/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth
case "$ARM" in
  none)   W=0.0; Q="";                                   RUN=grasppilot3_d_none_ep15_seed42 ;;
  gteach) W=0.3; Q=$S/targets/q_G_train.npz;             RUN=grasppilot3_d_gteach_ep15_seed42 ;;
  shuf)   W=0.3; Q=$S/targets/q_G_shuf_train.npz;        RUN=grasppilot3_d_shuf_ep15_seed42 ;;
  smoke|smoke2)  W=0.3; Q=$S/targets/trial_q_probe_gt_train.npz; RUN=grasppilot3_d_$ARM; EPOCHS=12; ANN=$S/smoke_ann ;;
  smoke_nococo) W=0.3; Q=$S/targets/trial_q_probe_gt_train.npz; RUN=grasppilot3_d_smoke_nococo; EPOCHS=1; ANN=$S/smoke_ann
                COCO=/nonexistent/relation_detr_resnet50_800_1333_coco_1x.pth ;;
  *) echo "unknown arm $ARM"; exit 2 ;;
esac
R=$M/experiments/phase1/$RUN
WORK=$S/work/$RUN
if [ -e "$R/start.txt" ] || [ -e "$WORK/checkpoints" ]; then echo "既に在る: $R / $WORK"; exit 3; fi
if [ -n "$Q" ] && [ ! -f "$Q" ]; then echo "標的が無い: $Q"; exit 4; fi
mkdir -p "$R" "$WORK"
# コードの写し（中身の要約値ごとの置き場。同じ中身なら同じ写しを使い、写しは変えない）
if [ ! -d "$CODE" ]; then
  mkdir -p "$CODE"
  cp "$SRC/grasp_aux_d.py" "$SRC/d_model_config.py" "$SRC/d_train_config.py" "$CODE/"
  chmod a-w "$CODE"/*.py
fi
(cd "$CODE" && sha256sum grasp_aux_d.py d_model_config.py d_train_config.py) > "$R/code_sha256.txt"
if [ "${ARM#smoke}" != "$ARM" ] && [ ! -d "$S/smoke_ann" ]; then
  "$M/.venv/bin/python" - "$OV" "$S/smoke_ann" <<'EOF'
import json, sys
from pathlib import Path
src = Path(sys.argv[1]) / "data/annotations/egosurgery_tool_folds/A"
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
for part, n in (("train", 8), ("val", 4)):
    d = json.loads((src / f"instances_{part}.json").read_text())
    has = sorted({a["image_id"] for a in d["annotations"]})[::max(1, len({a["image_id"] for a in d["annotations"]}) // n)][:n]
    keep = set(has)
    d["images"] = [im for im in d["images"] if im["id"] in keep]
    d["annotations"] = [a for a in d["annotations"] if a["image_id"] in keep]
    (out / f"instances_{part}.json").write_text(json.dumps(d))
    print(part, len(d["images"]), len(d["annotations"]))
EOF
fi
# shellcheck disable=SC1091
source "$OV/.venv-relation-detr/bin/activate"
export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$ANN \
  RELDETR_OUTPUT_DIR=$WORK RELDETR_COCO_CKPT=$COCO GRASP_D_CODE=$CODE \
  GRASP_AUX_WEIGHT=$W GRASP_TARGETS=$Q GRASP_STEPLOG=$WORK/grasp_steplog.jsonl GRASP_SWAP_ON_FLIP=1 \
  PYTHONDONTWRITEBYTECODE=1
[ "$ARM" = smoke_nococo ] && export GRASP_ALLOW_MISSING_COCO=1
ARGS=(--config-file "$CODE/d_train_config.py" --seed 42 --mixed-precision fp16 --accumulate-steps 2 --max-epochs "$EPOCHS")
{
  echo "#!/usr/bin/env bash"
  echo "# 非公式（$TASK）。案 D の腕 $ARM。自動生成: この run を起動した命令の記録"
  echo "cd $OV/third_party/Relation-DETR"
  for v in CUDA_VISIBLE_DEVICES CUDA_HOME EGO_BODY EGO_ROOT EGO_ANN_DIR RELDETR_OUTPUT_DIR RELDETR_COCO_CKPT GRASP_D_CODE GRASP_AUX_WEIGHT GRASP_TARGETS GRASP_STEPLOG GRASP_SWAP_ON_FLIP GRASP_ALLOW_MISSING_COCO; do
    [ -n "${!v+x}" ] && echo "export $v=${!v}"
  done
  echo "accelerate launch --num_processes 1 --main_process_port $PORT main.py ${ARGS[*]}"
} > "$R/command.sh"
cat > "$R/config.yaml" <<EOF
task_id: $TASK
unofficial: true
run_name: $RUN
arm: $ARM
aux_weight: $W
targets: "${Q}"
targets_sha256: "$( [ -n "$Q" ] && sha256sum "$Q" | cut -d' ' -f1 )"
swap_lr_on_flip: true
seed: 42
max_epochs: $EPOCHS
gpus: 1
batch_size_per_gpu: 2
accumulate_steps: 2
effective_batch_size: 4
mixed_precision: fp16
lr: 0.0001
lr_schedule: "MultiStepLR milestones [10] gamma 0.1（記録の低下 epoch 9 の後と同じ位置）。収束規則は使わない。最後の状態を使う"
weight_decay: 0.0001
max_norm: 0.1
transforms: presets.detr
init: COCO 1x（$COCO）
fold: A
fold_test_videos: "04,05,07"
fold_val_videos: "09,10"
annotations: $ANN
relation_detr: $OV/third_party/Relation-DETR（重ねの BODY。andrew と同じ中身）
code: $CODE
work_dir: $WORK
entrypoint: third_party/Relation-DETR/main.py（accelerate launch --num_processes 1）
EOF
git -C "$M" rev-parse HEAD > "$R/git_commit.txt"
hostname > "$R/server.txt"
nvidia-smi --query-gpu=index,name,power.limit --format=csv > "$R/gpu_at_start.txt"
(cd "$OV/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") > "$R/env_check.txt" 2>&1
date -u '+%F %T UTC' > "$R/start.txt"
cd "$OV/third_party/Relation-DETR" || exit 5
accelerate launch --num_processes 1 --main_process_port "$PORT" main.py "${ARGS[@]}" > "$WORK/stdout.log" 2>&1
RC=$?
echo $RC > "$R/exit_code.txt"
date -u '+%F %T UTC' > "$R/end.txt"
exit $RC
