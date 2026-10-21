#!/usr/bin/env bash
# Task D (T-2026-10-19-dlsta-tower-feasibility): run the detector tower's recipe for a fixed
# number of iterations on a given GPU pair, then stop it. Nothing under the repo is written:
# the run directory is $SCRATCH/D/<name>.
#
#   dtower_probe.sh <name> <gpus e.g. 1,2> <port> <config-file> <iters> [ENV=VAL ...]
#
# main.py's arguments are those of the second round's command.sh (only the port differs).
# Host paths the config would otherwise take from andrew's layout (~/slocal2/m2) are given
# as environment variables: EGO_ROOT and RELDETR_COCO_CKPT.
set -uo pipefail
NAME="$1"; GPUS="$2"; PORT="$3"; CFG="$4"; ITERS="$5"; shift 5
BODY="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SCRATCH="${SCRATCH:-$HOME/m2-scratch/dlsta_tower_feasibility}"
OUT="$SCRATCH/D/$NAME"
TOOLS="$BODY/experiments/analysis/dlsta_tower_feasibility/tools"
mkdir -p "$OUT/work" "$OUT/memprobe" "$OUT/evidence"

{
  echo "name=$NAME gpus=$GPUS port=$PORT cfg=$CFG iters=$ITERS extra_env=$*"
  echo "start_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  echo "--- gpu before"; python3 "$TOOLS/../gpu_procs.py"
} > "$OUT/probe.txt"

nvidia-smi -i "$GPUS" --query-gpu=timestamp,index,memory.used --format=csv,noheader,nounits -lms 500 \
  > "$OUT/nvsmi.csv" 2>&1 &
SAMPLER=$!

cd "$BODY/third_party/Relation-DETR"
# shellcheck disable=SC1091
source "$BODY/.venv-relation-detr/bin/activate"
export CUDA_VISIBLE_DEVICES="$GPUS"
export EGO_ANN_DIR="$BODY/data/annotations/egosurgery_tool_folds/A"
export RELDETR_OUTPUT_DIR="$OUT/work"
export RELDETR_EVIDENCE_DIR="$OUT/evidence"
export CUDA_HOME=/usr/local/cuda
export EGO_ROOT="$BODY/data/raw/ego"
export RELDETR_COCO_CKPT="$BODY/data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"
export MEMPROBE_DIR="$OUT/memprobe"
for kv in "$@"; do export "$kv"; done

CMD=(accelerate launch --num_processes 2 --main_process_port "$PORT" "$TOOLS/memprobe_main.py"
     --config-file "$CFG" --seed 42 --mixed-precision fp16 --convergence-schedule --max-epochs 36)
echo "command: ${CMD[*]}" >> "$OUT/probe.txt"
setsid "${CMD[@]}" > "$OUT/stdout.log" 2>&1 &
LEADER=$!
T0=$(date +%s)
STATUS=timeout
while true; do
  if ! kill -0 "$LEADER" 2>/dev/null; then STATUS=exited; break; fi
  if grep -q -E "\]  \[${ITERS}/" "$OUT/work/training.log" 2>/dev/null; then STATUS=reached; break; fi
  if [ $(( $(date +%s) - T0 )) -gt "${PROBE_TIMEOUT:-3600}" ]; then break; fi
  sleep 5
done
sleep 3   # let the memory thread write once more
kill -TERM -- "-$LEADER" 2>/dev/null; sleep 10; kill -KILL -- "-$LEADER" 2>/dev/null
wait "$LEADER" 2>/dev/null; RC=$?
kill "$SAMPLER" 2>/dev/null; wait "$SAMPLER" 2>/dev/null
{
  echo "status=$STATUS leader_rc=$RC end_utc=$(date -u '+%Y-%m-%dT%H:%M:%SZ') wall_s=$(( $(date +%s) - T0 ))"
  echo "--- gpu after"; python3 "$TOOLS/../gpu_procs.py"
} >> "$OUT/probe.txt"
echo "$NAME $STATUS"
