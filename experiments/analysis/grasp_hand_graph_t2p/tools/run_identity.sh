#!/usr/bin/env bash
# 学習前の出力が全腕で塔単独と一致し、零初期化の層を N(0, 0.05²) にすると変わること（陽性対照）を確かめる
# （非公式 T-2026-11-21-grasp-hand-graph-t2p-match、Task C、完了判定 f）。グラフ 17 腕 × 4 設定 × W1・W2・W3、T→P 4 型 × 3 腕 × W1・W2・W3。
#   GPU=0 bash experiments/analysis/grasp_hand_graph_t2p/tools/run_identity.sh
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
T=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph_t2p
TASK=T-2026-11-21-grasp-hand-graph-t2p-match
mkdir -p "$T/identity"
ARMS="empty D-noCF D-CF D-S DG-noCF DG-CF DG-S DH-noCF DH-CF DH-S DGH-noCF DGH-CF DGH-S DGH-U-noCF DGH-U-CF DGH-U-S DGH-GT"
for SC in W1 W2 W3; do
  for ST in "10 1" "10 2" "30 1" "30 2"; do
    read -r N L <<< "$ST"
    # shellcheck disable=SC2086
    CUDA_VISIBLE_DEVICES=${GPU:-0} python scripts/stage2pilot/dp_train.py identity --type GR --gr-dir "$T" --gr-N "$N" --gr-L "$L" \
      --scope "$SC" --arms $ARMS --perturb-scale 0.05 --task-id "$TASK" \
      --out "$T/identity/GR_${SC}_N${N}_L${L}.json" > "$T/identity/GR_${SC}_N${N}_L${L}.log" 2>&1
    echo "identity GR $SC N$N L$L rc=$?"
  done
  for TY in D1-L1 D1-L2 D2 D3-L2; do
    INST=literal; [ "$TY" = D3-L2 ] && INST=uq
    CUDA_VISIBLE_DEVICES=${GPU:-0} python scripts/stage2pilot/dp_train.py identity --type "$TY" --inst-variant "$INST" --scope "$SC" \
      --arms empty pred_noCF shuffle --perturb-scale 0.05 --task-id "$TASK" \
      --out "$T/identity/TP_${SC}_${TY}.json" > "$T/identity/TP_${SC}_${TY}.log" 2>&1
    echo "identity TP $SC $TY rc=$?"
  done
done
