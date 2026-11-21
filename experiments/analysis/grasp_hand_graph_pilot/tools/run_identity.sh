#!/usr/bin/env bash
# 学習前の出力が全腕で塔単独と一致し、零初期化の出力射影を N(0, 0.05²) にすると変わること（陽性対照）を、
# 4 設定 × W1・W2・W3 × 8 腕で確かめる（非公式 T-2026-11-20-grasp-hand-graph-pilot、Task C、完了判定 g）。
#   bash experiments/analysis/grasp_hand_graph_pilot/tools/run_identity.sh
set -eu
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
O=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph
mkdir -p "$O/identity"
for SC in W1 W2 W3; do
  for ST in "10 1" "10 2" "30 1" "30 2"; do
    read -r N L <<< "$ST"
    CUDA_VISIBLE_DEVICES=${GPU:-0} python scripts/stage2pilot/dp_train.py identity --type GR --gr-dir "$O" --gr-N "$N" --gr-L "$L" \
      --scope "$SC" --arms empty D DG DH DGH DGH-U DGH-noCF DGH-GT --perturb-scale 0.05 \
      --task-id T-2026-11-20-grasp-hand-graph-pilot --out "$O/identity/GR_${SC}_N${N}_L${L}.json" > "$O/identity/GR_${SC}_N${N}_L${L}.log" 2>&1
    echo "identity $SC N$N L$L rc=$?"
  done
done
python - "$O/identity" <<'EOF'
import json, sys
from pathlib import Path
rows, bad = [], []
for p in sorted(Path(sys.argv[1]).glob("GR_*.json")):
    d = json.loads(p.read_text())
    for arm, v in d.items():
        if not isinstance(v, dict) or "identity_max_abs_logit_diff" not in v:
            continue
        ok = v["identity_max_abs_logit_diff"] == 0.0 and v["jaccard_equals_taskB"] and v["positive_max_abs_logit_diff"] > 0
        sc = v.get("scope_check", {})
        if sc and not (sc["equal"] and not sc["equal_with_one_outside_mixed"]):
            ok = False
        rows.append((p.stem, arm, v["identity_max_abs_logit_diff"], v["positive_max_abs_logit_diff"], ok))
        if not ok:
            bad.append((p.stem, arm))
print(json.dumps({"n": len(rows), "bad": bad, "identity_max": max(r[2] for r in rows), "positive_min": min(r[3] for r in rows)}))
(Path(sys.argv[1]) / "identity_summary.json").write_text(json.dumps({"rows": rows, "bad": bad}, ensure_ascii=False, indent=1))
EOF
