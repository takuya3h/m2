#!/usr/bin/env bash
# Stage 1 検出塔の残り run を、**常に 2 本だけ**同時に走らせて流す。
# 契約 T-2026-09-18-stage1-detector-towers。
#
# 2 本が最適であることは実測で決めた（efros・A6000 2 枚）:
#   1 本 0.554 s/step = 1.805 step/s / 2 本 約0.92 s/step = 2.17 step/s / 3 本 約1.37 s/step = 2.19 step/s
# 3 本目は総処理量を増やさず per-run を遅くするだけなので採らない。
#
# **処方は 1 本も変えない。** どの run も --num_processes 2・per-GPU batch 2（実効 4）・fp16 である。
#
# 使い方: scripts/stage1_dtower_queue.sh <worker: a|b>
set -uo pipefail

BODY="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKER="$1"

# 待ち行列。worker a と b で交互に分けてある（2 本同時になる）。
case "$WORKER" in
  a) QUEUE=("coco A 456 29531" "coco B 42 29551" "coco D 42 29571" "imagenet A 123 29591" "imagenet C 42 29611" "imagenet E 42 29631")
     WAIT_CFG="configs/train_config_egosurgery_seed42.py" ;;
  b) QUEUE=("imagenet A 42 29541" "coco C 42 29561" "coco E 42 29581" "imagenet A 456 29601" "imagenet B 42 29621" "imagenet D 42 29641")
     WAIT_CFG="configs/train_config_egosurgery_seed123.py" ;;
  *) echo "[ERROR] worker は a か b" >&2; exit 2 ;;
esac

# 走っている run を、**引数の完全一致**で数える（部分一致は使わない。conventions#issuer_cautions 6）。
running_with_config() {
    local cfg="$1" p args
    for p in $(nvidia-smi --query-compute-apps=pid --format=csv,noheader 2>/dev/null); do
        args=$(tr '\0' '\n' < "/proc/$p/cmdline" 2>/dev/null) || continue
        if printf '%s\n' "$args" | grep -qxF "$cfg"; then return 0; fi
    done
    return 1
}

# 先に走っている run の枠が空くまで待つ。
echo "[queue-$WORKER] 先行 run（$WAIT_CFG）の終了を待つ"
while running_with_config "$WAIT_CFG"; do sleep 60; done
echo "[queue-$WORKER] 枠が空いた。待ち行列を開始する"

for item in "${QUEUE[@]}"; do
    # shellcheck disable=SC2086
    set -- $item
    TOWER="$1"; FOLD="$2"; SEED="$3"; PORT="$4"
    RUN="d${TOWER}_fold${FOLD}_seed${SEED}"
    DIR="$BODY/experiments/baselines/stage1_dtower/$RUN"
    if [ -f "$DIR/done.txt" ]; then
        echo "[queue-$WORKER] 済み: $RUN"
        continue
    fi
    # 停止の合図があれば、そこで止める（走行中の run は殺さない）。
    if [ -f "$BODY/.stage1-queue-stop" ]; then
        echo "[queue-$WORKER] 停止の合図を検知したため待ち行列を終える"
        break
    fi
    echo "[queue-$WORKER] 開始: $RUN (port $PORT) $(date -u '+%H:%M:%S UTC')"
    bash "$BODY/scripts/run_stage1_dtower.sh" "$TOWER" "$FOLD" "$SEED" "$PORT" \
        > "$DIR.boot.log" 2>&1
    rc=$?
    date -u '+%Y-%m-%d %H:%M:%S UTC' > "$DIR/end.txt"
    echo "rc=$rc" > "$DIR/done.txt"
    echo "[queue-$WORKER] 終了: $RUN rc=$rc $(date -u '+%H:%M:%S UTC')"
done
echo "[queue-$WORKER] 待ち行列を終えた $(date -u '+%H:%M:%S UTC')"
