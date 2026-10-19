#!/usr/bin/env bash
# Task E（bengio）: GPU 1 の 3 本目の枠で、検出から工程の 18 本 → K3 の GRU → extra-queries の入れ替えの腕を順に回す
# （非公式 T-2026-10-19-stage2-pilot-four-new-types。1 枚に 3 本まで: GPU 1 には extra-queries の予測-CF と正解予測-CF が別に載る）。
set -uo pipefail
WT=/home/ubuntu/slocal2/m2-four
Q=/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types/queues
export CUDA_VISIBLE_DEVICES=1
cd "$WT"
echo "[chain] dp start $(TZ=Asia/Tokyo date '+%H:%M:%S JST')"
SPECS=()
for T in LC TH TH-NG; do for A in empty pred_noCF gt pred_CF gtpred_CF shuffle; do SPECS+=("$T:$A"); done; done
bash scripts/stage2pilot/run_dp_four.sh "${SPECS[@]}"
echo "[chain] dp end $(TZ=Asia/Tokyo date '+%H:%M:%S JST')"
(
  # shellcheck disable=SC1091
  source /home/ubuntu/slocal2/m2/.venv/bin/activate
  # shellcheck disable=SC1091
  source scripts/load_env.sh > /dev/null 2>&1
  PYTHONPATH=src:scripts PYTHONUTF8=1 python scripts/stage2pilot/kill_four.py k3-train > "$Q/k3_train.log" 2>&1
  echo "[chain] k3 rc=$? $(grep -E 'K3_RUN_COMPLETE|Error' "$Q/k3_train.log" | tail -1)"
)
echo "[chain] eq shuffle start $(TZ=Asia/Tokyo date '+%H:%M:%S JST')"
S2FIX_BODY=/home/ubuntu/slocal2/s2fix-bengio-body S2FIX_CODE=$WT bash scripts/stage2pilot/run_pd_four.sh EQ shuffle
echo "[chain] eq shuffle rc=$? $(TZ=Asia/Tokyo date '+%H:%M:%S JST')"
