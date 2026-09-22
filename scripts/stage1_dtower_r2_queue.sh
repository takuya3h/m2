#!/usr/bin/env bash
# Stage 1 検出塔の二周目の残り 13 run を、**常に 2 本だけ**同時に走らせて流す。
# 契約 T-2026-09-19-stage1-detector-towers-r2。
#
# 2 本が最適であることは一周目の実測で決めた（efros・A6000 2 枚）:
#   1 本 0.554 s/step / 2 本 約0.92 s/step / 3 本 約1.37 s/step。
# 3 本目は総処理量を増やさず per-run を遅くするだけなので採らない。
#
# **処方は一周目と学習の長さの決め方だけが違う。** どの run も --num_processes 2・
# per-GPU batch 2（実効 4）・fp16 で、上限 36 epoch・停滞 4 で lr を 1/10・再停滞で打ち切り。
#
# 使い方: scripts/stage1_dtower_r2_queue.sh <worker: a|b>
set -uo pipefail

BODY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKER="$1"
EXP_DIR="stage1_dtower_r2"
export DTOWER_EXP_DIR="$EXP_DIR"
export DTOWER_TASK_ID="T-2026-09-19-stage1-detector-towers-r2"
export DTOWER_EXTRA_ARGS="--convergence-schedule --max-epochs 36"

# 待ち行列。両塔を worker a と b へ分け、2 本同時になるようにしてある。
# Task B（imagenet A 42）は先に単独で回すのでここには無い。
case "$WORKER" in
  a) QUEUE=("coco A 42 29711" "coco A 456 29713" "coco B 42 29715" "coco D 42 29717" \
            "imagenet A 456 29719" "imagenet C 42 29721" "imagenet E 42 29723") ;;
  b) QUEUE=("coco A 123 29712" "coco C 42 29714" "coco E 42 29716" \
            "imagenet A 123 29718" "imagenet B 42 29720" "imagenet D 42 29722") ;;
  *) echo "[ERROR] worker は a か b" >&2; exit 2 ;;
esac

for item in "${QUEUE[@]}"; do
    # shellcheck disable=SC2086
    set -- $item
    TOWER="$1"; FOLD="$2"; SEED="$3"; PORT="$4"
    RUN="d${TOWER}_fold${FOLD}_seed${SEED}"
    DIR="$BODY/experiments/baselines/$EXP_DIR/$RUN"
    if [ -f "$DIR/done.txt" ]; then
        echo "[queue-$WORKER] 済み: $RUN"
        continue
    fi
    # 停止の合図があれば、そこで止める（走行中の run は殺さない）。
    if [ -f "$BODY/.stage1-r2-queue-stop" ]; then
        echo "[queue-$WORKER] 停止の合図を検知したため待ち行列を終える"
        break
    fi
    mkdir -p "$DIR"
    echo "[queue-$WORKER] 開始: $RUN (port $PORT) $(date -u '+%H:%M:%S UTC')"
    bash "$BODY/scripts/run_stage1_dtower.sh" "$TOWER" "$FOLD" "$SEED" "$PORT" \
        > "$BODY/experiments/baselines/$EXP_DIR/$RUN.boot.log" 2>&1
    rc=$?
    date -u '+%Y-%m-%d %H:%M:%S UTC' > "$DIR/end.txt"
    echo "rc=$rc" > "$DIR/done.txt"
    echo "[queue-$WORKER] 終了: $RUN rc=$rc $(date -u '+%H:%M:%S UTC')"
done
echo "[queue-$WORKER] 待ち行列を終えた $(date -u '+%H:%M:%S UTC')"
