#!/usr/bin/env bash
# Task C-4（G3）: 入れ替えの腕の恒等性と陽性対照（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle）。
#   PD: 入れ替えた P0 を入れた零初期化の界面つき検出塔の val 出力が、塔単独（plain）と一致するか。界面の最後の層を
#       N(0, 0.05²) にすると変わるか（scripts/stage2pilot/pd_eval.py。P2F は表を入れない／入れる）
#   DP: 入れ替えた信号を入れた零初期化の界面つき時間ヘッドのロジットが塔単独と一致するか、最後の層を零でない値にすると変わるか
#       （scripts/stage2pilot/dp_train.py identity --arm shuffle）
#   GPU は CUDA_VISIBLE_DEVICES で渡す。
set -uo pipefail
BODY=/home/ubuntu/slocal2/m2
TASK=T-2026-10-19-stage2-pilot-fix-epoch4-shuffle
OLD=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
FIX=/home/ubuntu/slocal2/stage2pilot_store/$TASK
I=$BODY/experiments/analysis/stage2_pilot_fix/identity
SH=$FIX/signals/shuffle/P0_val.npz
TABLE=$BODY/experiments/analysis/stage2_pilot_folda/signals/p2f_table.json
mkdir -p "$FIX/identity"
cd "$BODY"
(
  source .venv-relation-detr/bin/activate
  export CUDA_HOME=/usr/local/cuda EGO_ANN_DIR=$BODY/data/annotations/egosurgery_tool_folds/A EGO_ROOT=$BODY/data/raw/ego
  REF=$FIX/identity/plain_val_preds.json.gz
  python scripts/stage2pilot/pd_eval.py --cfg plain --save-preds "$REF" --ref-preds "$OLD/identity/plain_val_preds.json.gz" \
    --out "$I/pd_plain.json" > "$I/pd_plain.log" 2>&1
  echo "plain rc=$? $(tail -1 "$I/pd_plain.log" | cut -c1-300)"
  run() { # 名前 cfg 追加引数...
    local name=$1 cfg=$2; shift 2
    python scripts/stage2pilot/pd_eval.py --cfg "configs/stage2pilot/$cfg.py" --signal-val "$SH" --ref-preds "$REF" \
      --out "$I/pd_$name.json" "$@" > "$I/pd_$name.log" 2>&1
    echo "$name rc=$? $(tail -1 "$I/pd_$name.log" | cut -c1-300)"
  }
  for cfg in pd_film_d9 pd_clsbias_lin_d9 pd_query_d9; do
    run "${cfg#pd_}_shuffle_identity" "$cfg"
    run "${cfg#pd_}_shuffle_positive" "$cfg" --perturb
  done
  run clsbias_fix_d9_shuffle_identity pd_clsbias_fix_d9
  run clsbias_fix_d9_shuffle_positive pd_clsbias_fix_d9 --fixed-table "$TABLE"
)
(
  source .venv/bin/activate
  export PYTHONPATH=src:scripts
  for t in D1-L1 D1-L2 D2 D3-L1 D3-L2; do
    EXTRA=()
    case "$t" in D3-*) EXTRA=(--inst-variant uq) ;; esac
    python scripts/stage2pilot/dp_train.py identity --type "$t" --arm shuffle --task-id "$TASK" "${EXTRA[@]}" \
      --out "$I/dp_${t}_shuffle.json" > "$I/dp_${t}_shuffle.log" 2>&1
    echo "dp $t rc=$?"
  done
)
