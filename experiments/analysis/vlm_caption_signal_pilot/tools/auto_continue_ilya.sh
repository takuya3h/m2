#!/usr/bin/env bash
# ilya 上で稼働中の W1 パイプライン（PID 指定）完了を待ち、
# W1 途中版を commit/push してから自動で W3（14 本）を実行し、完了後に W3 途中版を commit/push する。
set -euo pipefail
W1_PID="${1:-51167}"
M=/home/ubuntu/slocal2/m2
S=/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot
LOG=$S/task_f/auto_continue_ilya.log
mkdir -p "$S/task_f"

log() { printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S JST' -d '+9 hours' 2>/dev/null || date -u '+%Y-%m-%d %H:%M:%S UTC')" "$*" | tee -a "$LOG"; }

log "Watching ilya W1 pipeline PID=$W1_PID ..."
while kill -0 "$W1_PID" 2>/dev/null; do
  sleep 60
done
log "W1 pipeline PID=$W1_PID exited. Checking W1 completion..."

cd "$M"
# W1 の全 15 本が exit_code=0 で揃っているか確認（未完があれば補完実行）
PYTHONUTF8=1 PYTHONPATH=src:scripts .venv/bin/python experiments/analysis/vlm_caption_signal_pilot/tools/run_v2t_stage.py --w W1 --workers-per-gpu 2 --include-ep4-check >> "$LOG" 2>&1
PYTHONUTF8=1 PYTHONPATH=src:scripts .venv/bin/python experiments/analysis/vlm_caption_signal_pilot/tools/v2t_ep4_compare.py >> "$LOG" 2>&1
PYTHONUTF8=1 PYTHONPATH=src:scripts .venv/bin/python experiments/analysis/vlm_caption_signal_pilot/tools/aggregate_report.py \
  --stage-label "V→T W1 完了時点（途中版）" \
  --out-md experiments/analysis/vlm_caption_signal_pilot/REPORT.md \
  --out-csv experiments/analysis/vlm_caption_signal_pilot/diffs.csv \
  --out-json "$S/summary_v2t_W1.json" >> "$LOG" 2>&1

log "Committing and pushing W1 interim report..."
git add tasks/T-2026-11-26-vlm-caption-signal-pilot/ experiments/analysis/vlm_caption_signal_pilot/ experiments/phase1/vlm_caption_signal_pilot_* >> "$LOG" 2>&1 || true
if ! git diff --cached --quiet; then
  git commit -m "feat(vlm-pilot): V→T W1 完了・途中集計を更新（T-2026-11-26-vlm-caption-signal-pilot）" >> "$LOG" 2>&1
  git push git@github.com:takuya3h/m2.git feat/vlm-caption-signal-pilot >> "$LOG" 2>&1 || log "WARN: git push failed (non-fatal)"
fi

log "Starting ilya V->T W3 (14 runs, workers-per-gpu=2)..."
PYTHONUTF8=1 PYTHONPATH=src:scripts .venv/bin/python experiments/analysis/vlm_caption_signal_pilot/tools/run_v2t_stage.py --w W3 --workers-per-gpu 2 >> "$LOG" 2>&1
PYTHONUTF8=1 PYTHONPATH=src:scripts .venv/bin/python experiments/analysis/vlm_caption_signal_pilot/tools/aggregate_report.py \
  --stage-label "V→T W1・W3 完了時点（途中版）" \
  --out-md experiments/analysis/vlm_caption_signal_pilot/REPORT.md \
  --out-csv experiments/analysis/vlm_caption_signal_pilot/diffs.csv \
  --out-json "$S/summary_v2t_W3.json" >> "$LOG" 2>&1

log "Committing and pushing W3 interim report..."
git add tasks/T-2026-11-26-vlm-caption-signal-pilot/ experiments/analysis/vlm_caption_signal_pilot/ experiments/phase1/vlm_caption_signal_pilot_* >> "$LOG" 2>&1 || true
if ! git diff --cached --quiet; then
  git commit -m "feat(vlm-pilot): V→T W3 完了・途中集計を更新（T-2026-11-26-vlm-caption-signal-pilot）" >> "$LOG" 2>&1
  git push git@github.com:takuya3h/m2.git feat/vlm-caption-signal-pilot >> "$LOG" 2>&1 || log "WARN: git push failed (non-fatal)"
fi

log "ALL ILYA V->T JOBS (W1 + W3) COMPLETED!"
