#!/usr/bin/env bash
# 検出器 3-seed paired-σ 用 phase probe（phase-seed 多点平均でノイズ除去）。
#   bash scripts/_run_phase_probe_3seed.sh <detector_seed> [gpu=0] [ps_list="42 123 456"]
# 各 detector_seed について S4/B2a/T1a × {frozen, aug} を phase-seed 複数点で学習し、
# logs/phase3seed_results.tsv に "detseed phaseseed method arm dir" を追記。
# 集計 paired_sigma_3seed.py が phase-seed を平均 → 検出器seed で paired-σ。
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH=src
[ -f .env ] && { set -a; source .env; set +a; }
PY=python3
DSEED="${1:?detector_seed (42/123/456)}"
GPU="${2:-0}"
PS_LIST="${3:-42 123 456}"
FRO="relation_detr_seed${DSEED}"
AUG="relation_detr_augstrong_seed${DSEED}"
RES="logs/phase3seed_results.tsv"
touch "$RES"

runone() { # <phase_seed> <method> <arm> <src> <script...>
  local ps="$1" method="$2" arm="$3" src="$4"; shift 4
  local key="${method}_${arm}_det${DSEED}_p${ps}"
  echo "[$(date +%H:%M:%S)] probe $key (src=$src, gpu=$GPU)"
  local d
  d=$(RELDETR_FROZEN_TAG="$src" CUDA_VISIBLE_DEVICES=$GPU $PY "$@" --seed "$ps" \
        2>"logs/${key}.err" | tee "logs/${key}.log" \
        | grep -oE "evidence written -> .*" | tail -1 | sed 's/.*-> //')
  echo -e "${DSEED}\t${ps}\t${method}\t${arm}\t${d}" >> "$RES"
  echo "   -> $d"
}

for PS in $PS_LIST; do
  echo "=== detector_seed=$DSEED  phase_seed=$PS ==="
  runone "$PS" S4  frozen "$FRO" scripts/train_s4_tecno.py
  runone "$PS" S4  aug    "$AUG" scripts/train_s4_tecno.py
  runone "$PS" B2a frozen "$FRO" scripts/train_b2a.py --tool-source pred
  runone "$PS" B2a aug    "$AUG" scripts/train_b2a.py --tool-source pred
  runone "$PS" T1a frozen "$FRO" scripts/train_t1a.py --description "t1a_3seed_det${DSEED}_p${PS}_frozen"
  runone "$PS" T1a aug    "$AUG" scripts/train_t1a.py --description "t1a_3seed_det${DSEED}_p${PS}_aug"
done
echo "[$(date +%H:%M:%S)] detector_seed=$DSEED probe 完了（phase_seeds: $PS_LIST）"
