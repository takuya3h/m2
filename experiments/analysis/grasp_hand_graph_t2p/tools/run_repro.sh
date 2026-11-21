#!/usr/bin/env bash
# 既定の挙動が変わらないこと（SPEC §2）: 前回のグラフの run 1 本と T→P の run 1 本を、新しい引数を渡さずに本契約の識別子で回し直す
# （非公式 T-2026-11-21-grasp-hand-graph-t2p-match、Task C）。比べは c_repro_compare.py。
#   前回のグラフ: grasp_hand_graph_arm_009_GR-W1-N10-L1_DGH-noCF_conv_seed42（andrew、収束規則、--save-last-probs）
#   T→P:         stage2fix_dp_004_D1-L1_pred_noCF_ep4_seed42（andrew、--fixed-epochs 4）
#   GPU=1 bash experiments/analysis/grasp_hand_graph_t2p/tools/run_repro.sh
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
T=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph_t2p
TASK=T-2026-11-21-grasp-hand-graph-t2p-match
mkdir -p "$T/repro/logs" "$T/repro/dp_ckpt" "$T/wandb"
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$T/wandb WANDB_SILENT=true
CUDA_VISIBLE_DEVICES=${GPU:-1} python scripts/stage2pilot/dp_train.py train --type GR --gr-dir /home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph \
  --gr-N 10 --gr-L 1 --scope W1 --arm DGH-noCF --seed 42 --converge --task-id "$TASK" --exp-prefix grasp_hand_graph_t2p_repro_gr \
  --ckpt-dir "$T/repro/dp_ckpt" --save-last-probs > "$T/repro/logs/gr.log" 2>&1
echo "repro gr rc=$?"
CUDA_VISIBLE_DEVICES=${GPU:-1} python scripts/stage2pilot/dp_train.py train --type D1-L1 --arm pred_noCF --seed 42 --fixed-epochs 4 \
  --task-id "$TASK" --exp-prefix grasp_hand_graph_t2p_repro_tp --ckpt-dir "$T/repro/dp_ckpt" > "$T/repro/logs/tp.log" 2>&1
echo "repro tp rc=$?"
