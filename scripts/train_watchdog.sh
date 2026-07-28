#!/bin/bash
# train_watchdog.sh — 長時間 GPU 学習の死活監視 (Claude 非依存・常駐)。
#
# 背景: 学習は `nohup bash &` で Claude Code の外側で走るため、Claude Code の
#   Stop hook では学習プロセスの死を検知できない。本スクリプトは独立常駐し、
#   「異常停止」と「正常完走」をアラート JSON に記録する。Slack webhook URL が
#   環境変数 or .env にあれば直接 POST も行う (恒久通知)。Claude は別途このアラート
#   JSON を ScheduleWakeup で拾い、Slack MCP 通知や再開判断に使う。
#
# 異常停止の判定 (誤検知を避けるため複合条件):
#   - 完了 sentinel ($DONE_PATTERN) がログに出ていない、かつ
#   - GPU 使用率が連続 $STALL_CHECKS 回 (既定 3 回 x 60s = 3分) 0% (= 学習プロセス停止)、かつ
#   - 監視対象の学習プロセス ($PROC_PATTERN) が ps に存在しない
#   の 3 条件が同時成立で「異常停止」と判定する。
#
# 正常完走の判定:
#   - 完了 sentinel がログに出現 → "completed" アラートを 1 度だけ出して終了。
#
# 使い方:
#   PROGRESS_LOG=logs/sensex_codino_resume.log \
#   DONE_PATTERN="RESUME completed" \
#   PROC_PATTERN="train.py" \
#   ALERT_DIR=/tmp/train_alerts \
#   bash scripts/train_watchdog.sh
#
# 推奨: nohup + background。完了/異常で自動終了する。
set -uo pipefail

PROGRESS_LOG="${PROGRESS_LOG:?PROGRESS_LOG (launcher の進行ログ) を指定してください}"
DONE_PATTERN="${DONE_PATTERN:?DONE_PATTERN (完了 sentinel 文字列) を指定してください}"
PROC_PATTERN="${PROC_PATTERN:-train.py}"
ALERT_DIR="${ALERT_DIR:-/tmp/train_alerts}"
POLL_INTERVAL="${POLL_INTERVAL:-60}"      # 監視間隔 (秒)
STALL_CHECKS="${STALL_CHECKS:-3}"          # 連続何回 GPU 0% + プロセス無で異常判定するか
LABEL="${LABEL:-train}"                     # アラートの識別名
PROJECT_DIR="${PROJECT_DIR:-/home/ubuntu/slocal2/m2}"

mkdir -p "$ALERT_DIR"

# .env から SLACK_WEBHOOK_URL を読む (あれば)。秘密情報なので export はしない。
SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
if [ -z "$SLACK_WEBHOOK_URL" ] && [ -f "$PROJECT_DIR/.env" ]; then
    SLACK_WEBHOOK_URL="$(grep -E '^SLACK_WEBHOOK_URL=' "$PROJECT_DIR/.env" 2>/dev/null | head -1 | cut -d= -f2- | tr -d '"'"'"' ')"
fi

_now() { date -Iseconds; }

_gpu_util_sum() {
    # 全 GPU の utilization.gpu の合計を返す (数値)。取得失敗時は -1。
    local vals
    vals="$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null)" || { echo -1; return; }
    local sum=0
    while read -r v; do
        [ -n "$v" ] && sum=$((sum + v))
    done <<< "$vals"
    echo "$sum"
}

_proc_count() {
    ps aux 2>/dev/null | grep -E "$PROC_PATTERN" | grep -v grep | grep -v train_watchdog | wc -l
}

_write_alert() {
    local kind="$1" message="$2"
    local ts saflabel f
    ts="$(_now)"
    safelabel="$(echo "$LABEL" | tr -c 'A-Za-z0-9_-' '_')"
    f="$ALERT_DIR/${safelabel}_${kind}.json"
    cat > "$f" <<JSON
{
  "kind": "$kind",
  "label": "$LABEL",
  "message": "$message",
  "timestamp": "$ts",
  "progress_log": "$PROGRESS_LOG",
  "gpu_util_sum": $(_gpu_util_sum),
  "proc_count": $(_proc_count)
}
JSON
    echo "[$ts] watchdog: $kind — $message (alert: $f)"

    # Slack webhook があれば直接通知 (恒久・Claude 非依存)。
    if [ -n "$SLACK_WEBHOOK_URL" ]; then
        local payload
        payload="$(printf '{"text":"[egosurgery watchdog] %s: %s — %s"}' "$kind" "$LABEL" "$message")"
        curl -s -m 10 -X POST -H 'Content-Type: application/json' \
            -d "$payload" "$SLACK_WEBHOOK_URL" >/dev/null 2>&1 \
            && echo "  -> Slack webhook 通知済" \
            || echo "  -> Slack webhook 通知失敗 (URL/疎通要確認)"
    fi
}

echo "=== train_watchdog start $(_now) ==="
echo "  PROGRESS_LOG=$PROGRESS_LOG"
echo "  DONE_PATTERN=$DONE_PATTERN  PROC_PATTERN=$PROC_PATTERN"
echo "  POLL=${POLL_INTERVAL}s  STALL_CHECKS=$STALL_CHECKS  ALERT_DIR=$ALERT_DIR"
echo "  Slack webhook: $([ -n "$SLACK_WEBHOOK_URL" ] && echo "設定あり" || echo "未設定 (ローカルアラートのみ)")"

stall=0
while true; do
    sleep "$POLL_INTERVAL"

    # 1) 完了 sentinel チェック (最優先)。
    if [ -f "$PROGRESS_LOG" ] && grep -q "$DONE_PATTERN" "$PROGRESS_LOG" 2>/dev/null; then
        _write_alert "completed" "学習が完了 sentinel に到達しました。"
        echo "=== watchdog exit (completed) $(_now) ==="
        exit 0
    fi

    # 2) 異常停止チェック (複合条件)。
    gpu_sum="$(_gpu_util_sum)"
    procs="$(_proc_count)"
    if [ "$gpu_sum" = "0" ] && [ "$procs" -eq 0 ]; then
        stall=$((stall + 1))
        echo "[$(_now)] watchdog: stall 候補 ${stall}/${STALL_CHECKS} (gpu_sum=0, procs=0)"
        if [ "$stall" -ge "$STALL_CHECKS" ]; then
            _write_alert "stalled" "GPU 0% かつ学習プロセス消失が ${STALL_CHECKS} 回連続。完了 sentinel 未達のため異常停止と判定。"
            echo "=== watchdog exit (stalled) $(_now) ==="
            exit 1
        fi
    else
        # 回復したらカウンタをリセット (一時的な eval 間の谷を異常としない)。
        if [ "$stall" -ne 0 ]; then
            echo "[$(_now)] watchdog: 回復 (gpu_sum=$gpu_sum, procs=$procs) — stall リセット"
        fi
        stall=0
    fi
done
