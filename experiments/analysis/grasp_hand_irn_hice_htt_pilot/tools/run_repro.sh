#!/usr/bin/env bash
# 既定の挙動と前回のグラフの型の挙動が変わらないこと（SPEC §2・§8 Task C）: 前回の run 2 本を、新しい型を使わずに本契約の識別子で回し直す
# （非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot）。比べは c_checks.py repro。
#   前回のグラフの型: grasp_hand_graph_arm_093_GR-W3-N30-L2_DGH_conv_seed42（andrew、収束規則、--save-last-probs）
#   型 TW の代わり:   stage2fix_dp_004_D1-L1_pred_noCF_ep4_seed42（andrew、--fixed-epochs 4。型 TW の材料が andrew に無い。audit A-9）
#   GPU=1 bash experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/run_repro.sh
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
O=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph
T=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt
TASK=T-2026-11-21-grasp-hand-irn-hice-htt-pilot
mkdir -p "$T/repro/logs" "$T/repro/dp_ckpt" "$T/wandb"
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$T/wandb WANDB_SILENT=true
CUDA_VISIBLE_DEVICES=${GPU:-1} python scripts/stage2pilot/dp_train.py train --type GR --gr-dir "$O" \
  --gr-N 30 --gr-L 2 --scope W3 --arm DGH --seed 42 --converge --task-id "$TASK" --exp-prefix grasp_hand_irn_hice_htt_repro_gr \
  --ckpt-dir "$T/repro/dp_ckpt" --save-last-probs > "$T/repro/logs/gr.log" 2>&1
echo "repro gr rc=$?"
CUDA_VISIBLE_DEVICES=${GPU:-1} python scripts/stage2pilot/dp_train.py train --type D1-L1 --arm pred_noCF --seed 42 --fixed-epochs 4 \
  --task-id "$TASK" --exp-prefix grasp_hand_irn_hice_htt_repro_tp --ckpt-dir "$T/repro/dp_ckpt" > "$T/repro/logs/tp.log" 2>&1
echo "repro tp rc=$?"
