#!/bin/bash
# eval_and_post.sh — 任意 eval command + Notion 自動 post。
#
# ExperimentManager を経由しない eval-only re-eval で毎回この wrapper を使えば、
# 完了時に Notion 実験Run台帳へ自動投稿される。
#
# 使い方:
#   scripts/eval_and_post.sh \
#     --name <notion-run-name> \
#     --seed <int> \
#     [--step S0] [--tier effort] \
#     [--recipe "recipe text"] \
#     [--server aolab] \
#     --log-path <path/to/eval.log> \
#     -- <実 eval コマンド (log は --log-path に redirect される)>
#
# 例:
#   scripts/eval_and_post.sh \
#     --name s0_042_stabledino_seed42_reeval --seed 42 --tier must \
#     --recipe "test-split score_thr=0.0 NMS-free" \
#     --log-path /tmp/stabledino_seed42_eval.log \
#     -- CUDA_VISIBLE_DEVICES=0 PYTHONPATH=src \
#        .venv/bin/python /path/to/eval_wrapper.py cfg.py ckpt.pth \
#        --out preds.pkl --cfg-options model.test_cfg.score_thr=0.0
#
# log-format は auto 検出 (mmdet3 / mmdet2 / detectron2 / accelerate)。

set +e
REPO=$(cd "$(dirname "$0")/.." && pwd)
NAME=""
SEED=""
STEP="S0"
TIER="effort"
RECIPE=""
SERVER=""
LOG=""
POST_ONLY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME=$2; shift 2 ;;
    --seed) SEED=$2; shift 2 ;;
    --step) STEP=$2; shift 2 ;;
    --tier) TIER=$2; shift 2 ;;
    --recipe) RECIPE=$2; shift 2 ;;
    --server) SERVER=$2; shift 2 ;;
    --log-path) LOG=$2; shift 2 ;;
    --post-only) POST_ONLY=1; shift ;;
    --) shift; break ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$NAME" || -z "$SEED" || -z "$LOG" ]]; then
  echo "usage: eval_and_post.sh --name X --seed N --log-path PATH [--step S0] [--tier effort] [--recipe TEXT] [--server aolab] [--post-only] -- CMD..." >&2
  exit 2
fi

mkdir -p "$(dirname "$LOG")"

if [[ $POST_ONLY -eq 0 ]]; then
  echo "[eval_and_post] START $NAME (log -> $LOG)"
  # 与えられた eval コマンドを実行 (残余の $@)
  "$@" > "$LOG" 2>&1
  RC=$?
  echo "[eval_and_post] eval rc=$RC"
  if [[ $RC -ne 0 ]]; then
    echo "[eval_and_post] SKIP post — eval failed. tail:" >&2
    tail -20 "$LOG" >&2
    exit $RC
  fi
fi

# Notion 投稿 (rc=0 の場合のみ)
ARGS=(--name "$NAME" --seed "$SEED" --step "$STEP" --tier "$TIER" --log-path "$LOG")
[[ -n "$RECIPE" ]] && ARGS+=(--recipe "$RECIPE")
[[ -n "$SERVER" ]] && ARGS+=(--server "$SERVER")

"$REPO/.venv/bin/python" "$REPO/scripts/post_eval_to_notion.py" "${ARGS[@]}"
