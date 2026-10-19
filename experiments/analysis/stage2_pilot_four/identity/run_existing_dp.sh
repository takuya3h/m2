#!/usr/bin/env bash
# Task C-1・G3: 既存の DP の型の挙動が変わらないことの確認（非公式 T-2026-10-19-stage2-pilot-four-new-types）。
# 直しの契約の experiments/analysis/stage2_pilot_fix/identity/run_identity.sh の DP の部分と同じ命令（入れ替えの腕の恒等性と陽性対照）を、
# 本契約で変えた dp_train.py・dp_model.py で回し、直しの契約の dp_<型>_shuffle.json（andrew）と値を比べる。GPU は CUDA_VISIBLE_DEVICES。
set -uo pipefail
WT=/home/ubuntu/slocal2/m2-four
OUT=$WT/experiments/analysis/stage2_pilot_four/identity
cd "$WT"
# shellcheck disable=SC1091
source /home/ubuntu/slocal2/m2/.venv/bin/activate
export PYTHONPATH=src:scripts PYTHONUTF8=1
for t in D1-L1 D1-L2 D2 D3-L1 D3-L2; do
  EXTRA=()
  case "$t" in D3-*) EXTRA=(--inst-variant uq) ;; esac
  python scripts/stage2pilot/dp_train.py identity --type "$t" --arm shuffle --task-id T-2026-10-19-stage2-pilot-four-new-types \
    "${EXTRA[@]}" --out "$OUT/existing_dp_${t}_shuffle.json" > "$OUT/existing_dp_${t}_shuffle.log" 2>&1
  echo "existing dp $t rc=$?"
done
