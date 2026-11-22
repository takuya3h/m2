#!/usr/bin/env bash
# 各型 1 本を数 epoch だけ回し、記憶と 1 epoch の時間を測る（非公式 T-2026-11-21-grasp-hand-irn-hice-htt-pilot、SPEC §6）。
# 腕は最も大きい組み合わせ（W3・N 30・L 2・DGH）。--fixed-epochs 3 --smoke（名前に _ep3_smoke。W2・W3 は --max-epochs と組めない）。GPU の使用量を 0.5 秒ごとに記録する。
#   GPU=1 bash experiments/analysis/grasp_hand_irn_hice_htt_pilot/tools/run_smoke.sh
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
O=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph
T=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_irn_hice_htt
TASK=T-2026-11-21-grasp-hand-irn-hice-htt-pilot
G=${GPU:-1}
mkdir -p "$T/smoke" "$T/smoke/dp_ckpt" "$T/wandb"
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$T/wandb WANDB_SILENT=true
for TY in IRN HiCE HTT; do
  ( while true; do nvidia-smi -i "$G" --query-gpu=memory.used --format=csv,noheader,nounits; sleep 0.5; done ) > "$T/smoke/${TY}_mem.txt" &
  MON=$!
  s=$(date +%s.%N)
  CUDA_VISIBLE_DEVICES=$G python scripts/stage2pilot/dp_train.py train --type "$TY" --gr-dir "$O" --gr-N 30 --gr-L 2 --scope W3 --arm DGH \
    --seed 42 --fixed-epochs 3 --smoke --task-id "$TASK" --exp-prefix grasp_hand_irn_hice_htt_smoke --ckpt-dir "$T/smoke/dp_ckpt" > "$T/smoke/${TY}.log" 2>&1
  rc=$?
  e=$(date +%s.%N)
  kill $MON
  echo "smoke $TY rc=$rc wall=$(python3 -c "print(round($e-$s,1))")s peak_mem_MiB=$(sort -n "$T/smoke/${TY}_mem.txt" | tail -1)"
done
