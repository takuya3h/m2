#!/usr/bin/env bash
# Task D（bengio、GPU 1）: K2 と陽性対照、K3 の (2)(3)、終わった extra-queries の腕の寄与（非公式 T-2026-10-19-stage2-pilot-four-new-types）。
set -uo pipefail
WT=/home/ubuntu/slocal2/m2-four
K=$WT/experiments/analysis/stage2_pilot_four/kill
cd "$WT"
(
  # shellcheck disable=SC1091
  source /home/ubuntu/slocal2/m2/.venv/bin/activate
  export PYTHONPATH=src:scripts PYTHONUTF8=1 CUDA_VISIBLE_DEVICES=1
  python scripts/stage2pilot/kill_four.py k2 --out "$K/k2.json" > "$K/k2.log" 2>&1; echo "[kill] k2 rc=$?"
  python scripts/stage2pilot/kill_four.py k2 --control-onehot --out "$K/k2_control_onehot.json" > "$K/k2_control_onehot.log" 2>&1; echo "[kill] k2 control rc=$?"
  CK=$(ls /home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types/k3/stage2four_k3_002_*.pth)
  python scripts/stage2pilot/kill_four.py k3-eval --ckpt "$CK" --out "$K/k3.json" > "$K/k3.log" 2>&1; echo "[kill] k3 rc=$?"
)
bash "$WT/experiments/analysis/stage2_pilot_four/xq_contrib/run_xq_contrib.sh" 1 pred_CF
