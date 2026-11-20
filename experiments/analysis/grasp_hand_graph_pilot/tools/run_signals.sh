#!/usr/bin/env bash
# G3・H4 の信号（推論）と学習後の反転の整合（非公式 T-2026-11-20-grasp-hand-graph-pilot、Task C）。
# 塔ごとに確定・H1・H2 の 3 本の記録（metrics.json）がそろうのを待ち、その塔の G2 の部分（打ち切りで止まった・選んだ回が学習前を上回る）を
# 確かめてから推論する。G3 は GPU 0、H4 は GPU 1（学習中の塔と分け合う。推論は 1 本 8 GB 程度）。
#   train: 確定の塔を train 全体（noCF の腕）、H1 の塔を H2 の動画、H2 の塔を H1 の動画（交差適合）。val: 確定の塔
#   bash experiments/analysis/grasp_hand_graph_pilot/tools/run_signals.sh G3 0   （塔、GPU）
set -u
cd "$(dirname "$0")/../../../.."
source .venv/bin/activate
O=/home/ubuntu/slocal2/stage2pilot_store/grasp_hand_graph
T=$1
GPU=$2
RAW=$O/signals/raw
mkdir -p "$RAW" "$O/flip" "$O/logs"
EV=$O/logs/signals_events.log
for v in all H1 H2; do
  until [ -s "experiments/phase1/grasp_hand_graph_tower_${T}_${v}_seed42/metrics.json" ]; do sleep 60; done
done
python - "$T" <<'EOF' >> "$EV" 2>&1 || { echo "$(date '+%F %T %Z') $T G2 部分の外れ。推論しない" >> "$EV"; exit 3; }
import json, sys
t = sys.argv[1]
bad = []
for v in ("all", "H1", "H2"):
    m = json.load(open(f"experiments/phase1/grasp_hand_graph_tower_{t}_{v}_seed42/metrics.json"))
    ok = m["early_stopped_epoch"] is not None and not m["reached_epoch_cap"] and m["best_segm_mAP"] > m["pre_segm_mAP"]
    print(f"G2part {t}_{v} best={m['best_segm_mAP']:.4f} pre={m['pre_segm_mAP']:.4f} best_epoch={m['best_epoch']} stopped={m['early_stopped_epoch']} ok={ok}")
    bad += [] if ok else [v]
sys.exit(1 if bad else 0)
EOF
TRAIN=01,02,03,06,08,11,12,13,14,15
run() {   # 名前 重み 当てる塔 part 動画
  echo "$(date '+%F %T %Z') start $1" >> "$EV"
  CUDA_VISIBLE_DEVICES=$GPU python scripts/grasppilot/ghg_tower.py infer --tower "$T" --ckpt "$2" --g "$3" --part "$4" --videos "$5" \
    --out "$RAW/$1" > "$O/logs/infer_$1.log" 2>&1
  echo "$(date '+%F %T %Z') end $1 rc=$?" >> "$EV"
}
run "${T}_all_val" "$O/ckpt/${T}_all/best.pth" all val 09,10
run "${T}_H1_train" "$O/ckpt/${T}_H1/best.pth" H1 train 02,03,08,13,14
run "${T}_H2_train" "$O/ckpt/${T}_H2/best.pth" H2 train 01,06,11,12,15
run "${T}_all_train" "$O/ckpt/${T}_all/best.pth" all train $TRAIN
for L in final coco; do
  CK=$O/ckpt/${T}_all/best.pth
  [ $L = coco ] && CK=coco
  CUDA_VISIBLE_DEVICES=$GPU python scripts/grasppilot/ghg_tower.py flipmodel --tower "$T" --ann-dir "$O/ann" --ckpt "$CK" --label $L \
    --out "$O/flip/flipmodel_${T}_${L}.json" > "$O/logs/flipmodel_${T}_${L}.log" 2>&1
  echo "$(date '+%F %T %Z') flipmodel $T $L rc=$?" >> "$EV"
done
echo "$(date '+%F %T %Z') $T signals done" >> "$EV"
