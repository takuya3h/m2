#!/usr/bin/env bash
# Task D-4/D-5（PD）: 型ごとの恒等性（零初期化で塔単独と同じ出力）と陽性対照（界面を零でない値にすると変わる）。
# 非公式 T-2026-10-18-stage2-pilot-folda。GPU は CUDA_VISIBLE_DEVICES で渡す。
set -uo pipefail
BODY=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-18-stage2-pilot-folda
I=$BODY/experiments/analysis/stage2_pilot_folda/identity
cd "$BODY"
source .venv-relation-detr/bin/activate
export CUDA_HOME=/usr/local/cuda EGO_ANN_DIR=$BODY/data/annotations/egosurgery_tool_folds/A EGO_ROOT=$BODY/data/raw/ego
REF=$S/identity/plain_val_preds.json.gz
P0=$S/signals/final/P0_val.npz
GP=$S/arms/PD/gtpred_noCF_val.npz
TABLE=$I/../signals/p2f_table.json
run() { # 名前 cfg 信号 追加引数...
  local name=$1 cfg=$2 sig=$3; shift 3
  python scripts/stage2pilot/pd_eval.py --cfg configs/stage2pilot/$cfg.py --signal-val $sig --ref-preds $REF \
    --out $I/pd_$name.json "$@" > $I/pd_$name.log 2>&1
  echo "$name rc=$? $(tail -1 $I/pd_$name.log | cut -c1-400)"
}
for cfg in pd_film_d9 pd_clsbias_lin_d9 pd_query_d9 pd_film_d18 pd_clsbias_lin_d18 pd_query_d18; do
  case $cfg in *d18) sig=$GP ;; *) sig=$P0 ;; esac
  run ${cfg#pd_}_identity $cfg $sig
  run ${cfg#pd_}_positive $cfg $sig --perturb
done
run clsbias_fix_d9_identity pd_clsbias_fix_d9 $P0
run clsbias_fix_d9_positive pd_clsbias_fix_d9 $P0 --fixed-table $TABLE
