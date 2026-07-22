#!/usr/bin/env bash
# hires(Method C) の 3-way phase 比較（frozen42 / augstrong42 / hires42）。
# 各 tag × S4/B2a/T1a × phase-seed {42,123,456} を学習し logs/hires_probe_results.tsv へ
# "tag phaseseed method dir" を記録。集計は report_hires_probe.py（phase-seed 平均・3way）。
#   bash scripts/_run_hires_probe.sh [gpu=0]
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH=src
[ -f .env ] && { set -a; source .env; set +a; }
PY=python3
GPU="${1:-0}"
TAGS="relation_detr_seed42 relation_detr_augstrong_seed42 relation_detr_augstrong_hires_seed42"
PS_LIST="42 123 456"
RES="logs/hires_probe_results.tsv"
: > "$RES"

runone() { # <tag> <ps> <method> <script...>
  local tag="$1" ps="$2" method="$3"; shift 3
  local key="hires_${method}_${tag}_p${ps}"
  echo "[$(date +%H:%M:%S)] $key"
  local d
  d=$(RELDETR_FROZEN_TAG="$tag" CUDA_VISIBLE_DEVICES=$GPU $PY "$@" --seed "$ps" \
        2>"logs/${key}.err" | grep -oE "evidence written -> .*" | tail -1 | sed 's/.*-> //')
  echo -e "${tag}\t${ps}\t${method}\t${d}" >> "$RES"
}

for tag in $TAGS; do
  for ps in $PS_LIST; do
    runone "$tag" "$ps" S4  scripts/train_s4_tecno.py
    runone "$tag" "$ps" B2a scripts/train_b2a.py --tool-source pred
    runone "$tag" "$ps" T1a scripts/train_t1a.py --description "hires_${tag}_p${ps}"
  done
done
echo "[$(date +%H:%M:%S)] hires probe 完了（27 学習）"
