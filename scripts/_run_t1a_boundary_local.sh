#!/usr/bin/env bash
# T1a-Boundary ローカル実行（efros・system python3・GAP/region キャッシュは lecun 由来）。
# 各 seed で「T1a base（同env・paired 分母）」と「T1a-Boundary」を同一 wave で対に走らせる。
# ExperimentManager が採番し証跡を残す（Notion 自動投稿は .env 認証時のみ・fail-open）。
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH=src
[ -f .env ] && { set -a; source .env; set +a; }
mkdir -p logs
PY=python3
T1A="scripts/train_t1a.py"
BD="scripts/train_t1a_boundary.py"

run1() { local gpu="$1" log="$2"; shift 2
  echo "[$(date +%H:%M:%S)] START gpu$gpu $log :: $*"
  CUDA_VISIBLE_DEVICES="$gpu" $PY "$@" > "logs/$log.log" 2>&1
  echo "[$(date +%H:%M:%S)] DONE  gpu$gpu $log (rc=$?)"
}

for S in 42 123 456; do
  # gpu0 = T1a base（同env 分母, 独立 description で lecun dir と混同回避）
  run1 0 "t1a_base_env_seed$S" "$T1A" --description t1a_base_env --seed "$S" &
  pa=$!
  sleep 4  # ExperimentManager の seq 採番競合（並列 setup レース）回避
  # gpu1 = T1a-Boundary
  run1 1 "t1a_boundary_seed$S" "$BD" --seed "$S" &
  pb=$!
  wait "$pa"; wait "$pb"
done
echo "[$(date +%H:%M:%S)] T1a-Boundary 3-seed（base+boundary）完了"
