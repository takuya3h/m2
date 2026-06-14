#!/bin/bash
# safe_gpu_cleanup.sh — GPU上のプロセスを「列挙→明示確認→PID直接kill」で安全に止める。
#
# 背景(lessons.md D1): 「残骸掃除」のつもりで pkill -f <広域パターン> を投下し、
# 走行中の別実験(DI-MaskDINO seed42)を誤って SIGKILL した事故の再発防止。
#
# 設計:
#   - デフォルトは DRY-RUN: GPU上の全プロセス(PID/メモリ/コマンド)を列挙するだけ。何も殺さない。
#   - 実際に kill するには、止めたい PID を明示引数で渡す: safe_gpu_cleanup.sh --kill <PID> [<PID>...]
#   - pkill -f の広域パターンは一切使わない。nvidia-smi が示す PID のみ対象。
#
# 使い方:
#   bash scripts/safe_gpu_cleanup.sh            # 列挙のみ(何が走っているか確認)
#   bash scripts/safe_gpu_cleanup.sh --kill 12345 12346   # 指定PIDのみkill→解放待ち
set -uo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"

# 稼働中(TRAINING/EVALUATING/STALLED)の学習に属する PID 集合を返す。
# train_status.py が唯一の正規判定 (nvidia-smi の PID 表示や mtime 単独では誤診する→誤診#1再発防止)。
_live_pids() {
    "$PROJ/.venv/bin/python" "$PROJ/scripts/train_status.py" --scan --interval 6 --json 2>/dev/null \
      | "$PROJ/.venv/bin/python" -c $'import sys,json\ntry:\n rows=json.load(sys.stdin)\nexcept Exception:\n rows=[]\nfor r in rows:\n if r.get("state") in ("TRAINING","EVALUATING","STALLED"):\n  for p in (r.get("procs") or []): print(p)' 2>/dev/null
}

_list() {
    echo "=== GPU 上のプロセス (これが実体。pgrep数値より信頼できる) ==="
    local pids
    pids="$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader 2>/dev/null)"
    if [ -z "$pids" ]; then
        echo "  (GPU上にプロセスなし)"
    else
        while IFS=',' read -r pid mem; do
            pid="$(echo "$pid" | tr -d ' ')"
            mem="$(echo "$mem" | tr -d ' ')"
            local cmd="(GONE: zombie GPU mem)"
            if [ -d "/proc/$pid" ]; then
                cmd="$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null | cut -c1-90)"
            fi
            echo "  PID=$pid mem=$mem  cmd=$cmd"
        done <<< "$pids"
    fi
    echo "=== GPU メモリ ==="
    nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.free --format=csv,noheader 2>/dev/null
}

if [ "${1:-}" != "--kill" ]; then
    _list
    echo ""
    echo "DRY-RUN: 何も kill していません。止めるには上記 PID を確認の上で:"
    echo "  bash scripts/safe_gpu_cleanup.sh --kill <PID> [<PID>...]"
    exit 0
fi

shift
FORCE=0
PIDS=()
for a in "$@"; do
    if [ "$a" = "--force" ]; then FORCE=1; else PIDS+=("$a"); fi
done
if [ "${#PIDS[@]}" -eq 0 ]; then
    echo "ERROR: --kill には止める PID を 1 つ以上指定してください (広域 pkill は使わない方針)。"
    _list
    exit 1
fi

# 誤診#1再発防止ゲート: 指定 PID が「稼働中の学習」に属するなら --force 無しでは拒否。
echo "=== 稼働中学習ゲート (train_status.py で判定中, ~6s) ==="
LIVE="$(_live_pids)"
BLOCKED=()
for pid in "${PIDS[@]}"; do
    if printf '%s\n' "$LIVE" | grep -qx "$pid"; then BLOCKED+=("$pid"); fi
done
if [ "${#BLOCKED[@]}" -gt 0 ] && [ "$FORCE" -ne 1 ]; then
    echo "❌ 中止: 指定 PID ${BLOCKED[*]} は稼働中の学習プロセスです。"
    echo "   稼働中の実験を kill するのは禁止 (誤診#1: 走行中seedを誤killした事故の再発防止)。"
    echo "   本当に止める確信があるときのみ --force を付けてください。"
    "$PROJ/.venv/bin/python" "$PROJ/scripts/train_status.py" --scan --interval 6
    exit 3
fi
[ "$FORCE" -eq 1 ] && [ "${#BLOCKED[@]}" -gt 0 ] && echo "⚠️ --force 指定: 稼働中 ${BLOCKED[*]} も kill します。"

echo "=== kill 前の状態 ==="
_list
echo ""
echo "=== 指定 PID を kill: ${PIDS[*]} ==="
for pid in "${PIDS[@]}"; do
    if [ -d "/proc/$pid" ]; then
        kill -9 "$pid" 2>/dev/null && echo "  kill -9 $pid 送信" || echo "  WARN: $pid kill 失敗"
    else
        echo "  $pid は既に存在しない (skip)"
    fi
done

echo "=== GPU メモリ解放を待機 (最大 300s, ゾンビメモリはドライバ回収待ち) ==="
waited=0
while [ "$waited" -lt 300 ]; do
    sleep 10
    waited=$((waited + 10))
    free0="$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ' ')"
    echo "  ${waited}s: GPU0 used=${free0}MiB"
    [ "$free0" -lt 3000 ] && { echo "  解放完了"; break; }
done
echo "=== 最終状態 ==="
_list
