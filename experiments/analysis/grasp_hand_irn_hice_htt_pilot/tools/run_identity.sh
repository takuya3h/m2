#!/usr/bin/env bash
# 学習前の出力が全型・全腕・全設定・全 W で塔単独と一致し、零初期化の線形層（out の重みと bias）を N(0, 0.05²) にすると変わることを確かめる
# （非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、Task C、完了判定 e）。3 型 × 4 設定 × W1・W2・W3、各 8 腕。
#   GPU=0 bash experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/run_identity.sh
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
O=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph
T=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt
TASK=T-2026-11-21-grasp-hand-irn-hice-htt-pilot
mkdir -p "$T/identity"
ARMS="empty D DG DH DGH DGH-U DGH-noCF DGH-GT"
for TY in IRN HiCE HTT; do
  for SC in W1 W2 W3; do
    for ST in "10 1" "10 2" "30 1" "30 2"; do
      read -r N L <<< "$ST"
      # shellcheck disable=SC2086
      CUDA_VISIBLE_DEVICES=${GPU:-0} python scripts/stage2pilot/dp_train.py identity --type "$TY" --gr-dir "$O" --gr-N "$N" --gr-L "$L" \
        --scope "$SC" --arms $ARMS --perturb-scale 0.05 --task-id "$TASK" \
        --out "$T/identity/${TY}_${SC}_N${N}_L${L}.json" > "$T/identity/${TY}_${SC}_N${N}_L${L}.log" 2>&1
      echo "identity $TY $SC N$N L$L rc=$?"
    done
  done
done
