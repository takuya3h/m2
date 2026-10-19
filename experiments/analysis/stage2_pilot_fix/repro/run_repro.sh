#!/usr/bin/env bash
# Task B-3: 塔単独の val を andrew で再現する（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）。val だけ。test は評価しない。
# 工程塔は scripts/stage2pilot/repro_ptower.py、検出塔は前回の eval_dtower_val.sh（読んで実行するだけ。出力は本契約の置き場）。
# 対照: 工程は別の時間ヘッド（P20 seed42 の 036）、検出は別 seed（123）の checkpoint。
set -uo pipefail
BODY=/home/ubuntu/slocal2/m2
R=$BODY/experiments/analysis/stage2_pilot_fix/repro
EV=$BODY/experiments/analysis/stage2_pilot_folda/repro/eval_dtower_val.sh
cd "$BODY"
export PYTHONPATH=src:scripts
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/stage2pilot/repro_ptower.py --out "$R/ptower_val.json" > "$R/ptower_val.log" 2>&1
echo "ptower rc=$?"
CUDA_VISIBLE_DEVICES=0 .venv/bin/python scripts/stage2pilot/repro_ptower.py \
  --head experiments/phase1/stage1_ptower_20_036_P20_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42/checkpoints/best.pth \
  --out "$R/ptower_val_control_p20seed42head.json" > "$R/ptower_val_control.log" 2>&1
echo "ptower control rc=$?"
bash "$EV" "$BODY/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed42/work/best_ap.pth" "$R/dtower_val_seed42.json" 29761 \
  > "$R/dtower_val_seed42.log" 2>&1
echo "dtower rc=$?"
bash "$EV" "$BODY/experiments/baselines/stage1_dtower_r2/dcoco_foldA_seed123/work/best_ap.pth" "$R/dtower_val_control_seed123.json" 29762 \
  > "$R/dtower_val_control_seed123.log" 2>&1
echo "dtower control rc=$?"
# 群の AP（conventions#det_groups。評価集合に出現しないクラスは除いて記録）と前回の値との差
.venv/bin/python - "$R" <<'EOF'
import json, math, sys
from pathlib import Path
sys.path.insert(0, "scripts")
from stage2pilot import det_metrics as M
R = Path(sys.argv[1])
REC = {"AP": 0.7273450248398429, "target_AP": 0.7950748008550899, "control_AP": 0.6726631817581498}
old = json.loads(Path("experiments/analysis/stage2_pilot_folda/repro/dtower_val_seed42.json").read_text())["per_class_ap"]
groups = M.read_groups()
for name in ("dtower_val_seed42", "dtower_val_control_seed123"):
    d = json.loads((R / f"{name}.json").read_text())
    pc = d["per_class_ap"]
    out = {"AP": d["AP"]}
    for g, cls in groups.items():
        used = [pc[c] for c in cls if pc.get(c) is not None and not math.isnan(pc[c])]
        out[f"{g}_AP"] = sum(used) / len(used) if used else None
        out[f"{g}_missing"] = [c for c in cls if pc.get(c) is None or math.isnan(pc[c])]
    out.update({f"diff_{k}_vs_record": out[k] - REC[k] for k in ("AP",) } | {
        "diff_target_vs_record": out["target_AP"] - REC["target_AP"],
        "diff_control_vs_record": out["control_AP"] - REC["control_AP"],
        "per_class_identical_to_previous_repro": pc == old})
    (R / f"{name}_groups.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(name, out)
EOF
