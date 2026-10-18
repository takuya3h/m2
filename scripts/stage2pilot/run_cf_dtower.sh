#!/usr/bin/env bash
# 検出の交差適合用の塔を一本学ぶ（非公式 T-2026-10-18-stage2-pilot-folda、Task E-3/E-4）。
#
#   scripts/stage2pilot/run_cf_dtower.sh <半分: H1|H2|H1smoke> <port> [max_epochs]
#
# 処方は確定塔 D*-COCO 折り A seed 42 と同じ（configs/train_config_egosurgery_seed42.py、COCO の公開の重みから、
# fp16、2 プロセス、--convergence-schedule --max-epochs 36。scripts/run_stage1_dtower.sh と同じ起動の形）。
# 変えるのは train の注釈（動画単位で H1 だけ / H2 だけ）と出力先だけ。val は折り A の val。
# andrew は GPU 間 P2P の all_reduce が止まるため NCCL_P2P_DISABLE=1 を足す（計算は変わらない）。
# 大きな成果物（checkpoint）は版管理と同期の外（STORE）に置き、証跡だけを experiments/baselines/ に置く。
set -euo pipefail
HALF="$1"; PORT="$2"; MAXEP="${3:-36}"
BODY=/home/ubuntu/slocal2/m2
TASK=T-2026-10-18-stage2-pilot-folda
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
ANN=$S/ann_cf/$HALF
RUN=stage2pilot_cf_dcoco_${HALF}_seed42
DIR=$BODY/experiments/baselines/$RUN
OUT=$S/cf_dtower/$RUN/work
CFG=configs/train_config_egosurgery_seed42.py
[ -f "$ANN/instances_train.json" ] || { echo "注釈が無い: $ANN" >&2; exit 2; }
[ -e "$ANN/instances_test.json" ] && { echo "test の注釈を置かない: $ANN" >&2; exit 2; }
[ -e "$DIR" ] && { echo "既に在る: $DIR" >&2; exit 4; }
mkdir -p "$DIR" "$OUT"
cat > "$DIR/command.sh" <<CMD
#!/usr/bin/env bash
# 自動生成: この run を起動したコマンドの記録（非公式 ${TASK} / 半分 ${HALF} / seed 42）
cd third_party/Relation-DETR
export EGO_ANN_DIR=${ANN}
export RELDETR_OUTPUT_DIR=${OUT}
export CUDA_HOME=/usr/local/cuda
export NCCL_P2P_DISABLE=1
accelerate launch --num_processes 2 --main_process_port ${PORT} main.py \\
    --config-file ${CFG} --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs ${MAXEP}
CMD
chmod +x "$DIR/command.sh"
git -C "$BODY" rev-parse HEAD > "$DIR/git_commit.txt"
hostname > "$DIR/server.txt"
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$DIR/start.txt"
nvidia-smi --query-compute-apps=pid,used_memory --format=csv > "$DIR/gpu_at_start.txt"
cd "$BODY/third_party/Relation-DETR"
# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export EGO_ROOT=$BODY/data/raw/ego EGO_ANN_DIR=$ANN RELDETR_OUTPUT_DIR=$OUT CUDA_HOME=/usr/local/cuda NCCL_P2P_DISABLE=1
set +e
accelerate launch --num_processes 2 --main_process_port "$PORT" main.py \
    --config-file "$CFG" --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs "$MAXEP" \
    >> "$DIR/train.log" 2>&1
RC=$?
set -e
date -u '+%Y-%m-%d %H:%M:%S UTC' > "$DIR/end.txt"
echo "$RC" > "$DIR/exit_code.txt"
[ -f "$OUT/convergence.json" ] && cp "$OUT/convergence.json" "$DIR/"
echo "[run_cf_dtower] $RUN rc=$RC"
exit $RC
