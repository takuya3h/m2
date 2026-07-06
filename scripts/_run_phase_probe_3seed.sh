#!/usr/bin/env bash
# 検出器 3-seed paired-σ 用 phase probe。検出器seed を軸に frozen vs augstrong を対比。
#   bash scripts/_run_phase_probe_3seed.sh <detector_seed> [phase_seed=42] [gpu=0]
# 各 detector_seed について S4/B2a/T1a × {frozen, aug} を phase_seed 固定で学習し、
# logs/phase3seed_results.tsv に "detseed method arm dir" を追記。集計は paired_sigma_3seed.py。
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH=src
[ -f .env ] && { set -a; source .env; set +a; }
PY=python3
DSEED="${1:?detector_seed (42/123/456)}"
PSEED="${2:-42}"
GPU="${3:-0}"
FRO="relation_detr_seed${DSEED}"
AUG="relation_detr_augstrong_seed${DSEED}"
RES="logs/phase3seed_results.tsv"
touch "$RES"

runone() { # <method> <arm> <src> <script...>
  local method="$1" arm="$2" src="$3"; shift 3
  local key="${method}_${arm}_det${DSEED}_p${PSEED}"
  echo "[$(date +%H:%M:%S)] probe $key (src=$src, gpu=$GPU)"
  local d
  d=$(RELDETR_FROZEN_TAG="$src" CUDA_VISIBLE_DEVICES=$GPU $PY "$@" --seed "$PSEED" \
        2>"logs/${key}.err" | tee "logs/${key}.log" \
        | grep -oE "evidence written -> .*" | tail -1 | sed 's/.*-> //')
  echo -e "${DSEED}\t${method}\t${arm}\t${d}" >> "$RES"
  echo "   -> $d"
}

runone S4  frozen "$FRO" scripts/train_s4_tecno.py
runone S4  aug    "$AUG" scripts/train_s4_tecno.py
runone B2a frozen "$FRO" scripts/train_b2a.py --tool-source pred
runone B2a aug    "$AUG" scripts/train_b2a.py --tool-source pred
runone T1a frozen "$FRO" scripts/train_t1a.py --description "t1a_3seed_det${DSEED}_frozen"
runone T1a aug    "$AUG" scripts/train_t1a.py --description "t1a_3seed_det${DSEED}_aug"
echo "[$(date +%H:%M:%S)] detector_seed=$DSEED probe 完了"
