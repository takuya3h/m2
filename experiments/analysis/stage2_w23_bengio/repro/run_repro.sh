#!/usr/bin/env bash
# 非公式 T-2026-11-01-stage2-w23-bengio、Task B-2。塔単独の val を bengio で再現する（val だけ。test は評価しない）。
# 検出塔: 三本目（T-2026-11-01-grasp-pilot-d）の B-1 と同じ経路（pd_eval.py --cfg plain、EGO_BODY=重ねの BODY）。
#         対照（SPEC §8-b）: 別 seed（123）の検出塔を同じ経路で評価し、標的群 AP の差が 0.005 を超えることを見る。
# 工程塔: scripts/stage2pilot/repro_ptower.py（写した特徴と時間ヘッド。本体の .venv）。
set -uo pipefail
M=/home/ubuntu/slocal2/m2
OV=/home/ubuntu/slocal2/s2fix-bengio-body
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-01-stage2-w23-bengio
R=$M/experiments/analysis/stage2_w23_bengio/repro
mkdir -p "$R" "$S/b"
cd "$M"
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1
sha256sum "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
  "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" \
  "$OV"/data/annotations/egosurgery_tool_folds/A/instances_{train,val}.json > "$R/b2_sha256.txt"
(
  # shellcheck disable=SC1091
  source "$OV/.venv-relation-detr/bin/activate"
  export CUDA_HOME=/usr/local/cuda EGO_BODY=$OV EGO_ROOT=$OV/data/raw/ego EGO_ANN_DIR=$OV/data/annotations/egosurgery_tool_folds/A
  (cd "$OV/third_party/Relation-DETR" && python -c "import torch, models.bricks.ms_deform_attn as m; print('[env] torch', torch.__version__, 'cuda', torch.cuda.is_available(), 'ms_deform_attn_ext', m._C is not None)") > "$R/env_check_det.txt" 2>&1
  ( CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/pd_eval.py --cfg plain \
      --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" \
      --save-preds "$S/b/plain_val_preds_seed42.json.gz" --out "$R/dtower_val_seed42.json" > "$R/dtower_val_seed42.log" 2>&1; echo "dtower rc=$?" ) &
  ( CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/pd_eval.py --cfg plain \
      --det-ckpt "$OV/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" \
      --save-preds "$S/b/plain_val_preds_seed123.json.gz" --out "$R/dtower_val_control_seed123.json" > "$R/dtower_val_control_seed123.log" 2>&1; echo "dtower control rc=$?" ) &
  wait
)
PYTHONPATH=src:scripts CUDA_VISIBLE_DEVICES=0 "$M/.venv/bin/python" scripts/stage2pilot/repro_ptower.py --out "$R/ptower_val.json" > "$R/ptower_val.log" 2>&1
echo "ptower rc=$?"
PYTHONPATH=src:scripts "$M/.venv/bin/python" - "$R" "$S" "$OV" <<'EOF' > "$R/b2_summary.json"
import json, sys
from pathlib import Path
sys.path.insert(0, "scripts")
from stage2pilot import det_metrics as D
R, S, OV = map(Path, sys.argv[1:4])
ann = OV / "data/annotations/egosurgery_tool_folds/A/instances_val.json"
REC = {"AP": 0.7273450, "target_AP": 0.7950748, "control_AP": 0.6726632}
out = {"record": REC, "record_source": "experiments/analysis/stage2_pilot_folda/REPORT.md §2（SPEC §2）"}
for seed in (42, 123):
    s = D.summary(ann, D.load_results(S / f"b/plain_val_preds_seed{seed}.json.gz"))
    row = {k: s[k] for k in ("AP", "AP50", "target_AP", "control_AP")}
    row["diff_AP"] = row["AP"] - REC["AP"]
    row["diff_target_AP"] = row["target_AP"] - REC["target_AP"]
    row["within_0.005"] = abs(row["diff_AP"]) <= 0.005 and abs(row["diff_target_AP"]) <= 0.005
    out[f"dtower_seed{seed}"] = row
pt = json.loads((R / "ptower_val.json").read_text())
out["ptower"] = {"phase_jaccard": pt.get("phase_jaccard"), "phase_accuracy": pt.get("phase_accuracy"),
                 "record_jaccard": 0.7762186, "record_accuracy": 0.8712871}
out["ptower"]["diff_jaccard"] = out["ptower"]["phase_jaccard"] - 0.7762186
out["ptower"]["within_0.005"] = abs(out["ptower"]["diff_jaccard"]) <= 0.005
print(json.dumps(out, ensure_ascii=False, indent=1))
EOF
echo "summary rc=$?"
