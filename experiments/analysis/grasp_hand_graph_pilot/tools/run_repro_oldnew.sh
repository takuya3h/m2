#!/usr/bin/env bash
# 既定の挙動の確かめの補助（非公式 T-2026-11-20-grasp-hand-graph-pilot、Task C、SPEC §2）。
# andrew には W3・収束規則の前回の run が無い（前回は bengio で、材料も andrew に無い）。そこで起点 origin/phase0 の
# dp_train.py・dp_model.py の写しと今の版を、同じ入力（andrew に在る D2 の材料）・同じ引数で回して記録を比べる。
# 界面の重みは --task-id の下に書かれるので、両方とも --task-id grasp_hand_graph/repro_cmp にして $S/grasp_hand_graph/ の下へ置く。
set -eu
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
O=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph
OLD=$O/repro/old
rm -rf "$OLD" && mkdir -p "$OLD/stage2pilot"
# 変えた 2 ファイルだけ起点の版を写す。変えていない部品（common・shuffle_signals・__init__）は repo のものへの記号リンク
# （common.ROOT は Path(__file__).resolve() で repo の根になる）。変えていないことは git diff origin/phase0 が空で示す
for f in dp_train.py dp_model.py; do
  git show "origin/phase0:scripts/stage2pilot/$f" > "$OLD/stage2pilot/$f"
done
for f in __init__.py common.py shuffle_signals.py; do
  ln -s "$PWD/scripts/stage2pilot/$f" "$OLD/stage2pilot/$f"
done
git --no-pager diff --stat origin/phase0 -- scripts/stage2pilot/common.py scripts/stage2pilot/shuffle_signals.py scripts/stage2pilot/__init__.py > "$O/repro/unchanged_parts_diff.txt"
sha256sum "$OLD/stage2pilot/dp_train.py" "$OLD/stage2pilot/dp_model.py" scripts/stage2pilot/dp_train.py scripts/stage2pilot/dp_model.py > "$O/repro/code_sha256.txt"
export WANDB_MODE=offline WANDB_API_KEY=offline-placeholder WANDB_DIR=$O/wandb WANDB_SILENT=true
export PYTHONPATH=src:scripts
ARGS="train --type D2 --arm pred_noCF --scope W3 --seed 42 --converge --task-id grasp_hand_graph/repro_cmp"
CUDA_VISIBLE_DEVICES=1 python "$OLD/stage2pilot/dp_train.py" $ARGS --exp-prefix grasp_hand_graph_cmp_old > "$O/repro/cmp_old.log" 2>&1
CUDA_VISIBLE_DEVICES=1 python scripts/stage2pilot/dp_train.py $ARGS --exp-prefix grasp_hand_graph_cmp_new > "$O/repro/cmp_new.log" 2>&1
tail -1 "$O/repro/cmp_old.log" "$O/repro/cmp_new.log"
