#!/usr/bin/env bash
# H1・H2 の G が終わったら、交差適合の信号の推論 → 案 C の train の標的 → 案 C の教師・入れ替えた教師の腕を起こす
# （非公式 T-2026-11-01-grasp-pilot-g、Task D・F。確認の間隔の分の待ちを無くすための自動化）
set -u
cd "$(dirname "$0")/../.."
TASK=T-2026-11-01-grasp-pilot-g
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
P1=experiments/phase1
LOG=$S/logs/pipeline_after_H.log
log() { echo "$(TZ=Asia/Tokyo date '+%F %T JST') $*" >> "$LOG"; }
wait_run() { until [ -f "$P1/$1/exit_code.txt" ]; do sleep 60; done; [ "$(cat "$P1/$1/exit_code.txt")" = 0 ] || { log "$1 rc=$(cat "$P1/$1/exit_code.txt") 止める"; exit 1; }; }
free_gpu() {  # 空き記憶（MiB）が $1 以上の GPU のうち最も空いているもの。無ければ空
  nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits | awk -F', ' -v need="$1" '$2>=need {print $2, $1}' | sort -rn | head -1 | awk '{print $2}'
}
wait_gpu() { local g; until g=$(free_gpu "$1"); [ -n "$g" ]; do sleep 60; done; echo "$g"; }
log "待ち始め"
wait_run grasppilot2_G_H1_seed42
wait_run grasppilot2_G_H2_seed42
log "H1・H2 終了"
source scripts/load_env.sh >/dev/null 2>&1 || true
export PYTHONPATH=src
mkdir -p "$S/signals/raw"
H1V=01,06,11,12,15; H2V=02,03,08,13,14
G1=$(wait_gpu 9000); CUDA_VISIBLE_DEVICES=$G1 .venv/bin/python scripts/grasppilot/g_signals.py infer --ckpt "$S/g/ckpt/grasppilot2_G_H1_seed42/best.pth" \
  --g H1 --part train --videos $H2V --out "$S/signals/raw/H1_on_H2" > "$S/logs/infer_H1_on_H2.log" 2>&1 &
P_A=$!; log "H1 の G → H2 の動画 GPU $G1"; sleep 90
G2=$(wait_gpu 9000); CUDA_VISIBLE_DEVICES=$G2 .venv/bin/python scripts/grasppilot/g_signals.py infer --ckpt "$S/g/ckpt/grasppilot2_G_H2_seed42/best.pth" \
  --g H2 --part train --videos $H1V --out "$S/signals/raw/H2_on_H1" > "$S/logs/infer_H2_on_H1.log" 2>&1 &
P_B=$!; log "H2 の G → H1 の動画 GPU $G2"
wait $P_A || { log "infer H1_on_H2 失敗"; exit 1; }
wait $P_B || { log "infer H2_on_H1 失敗"; exit 1; }
log "交差適合の推論 終了"
.venv/bin/python scripts/grasppilot/g_signals.py assemble-c --raw "$S/signals/raw" --out "$S/signals" \
  --g-run "$P1/grasppilot2_G_H1_seed42/config.json" "$P1/grasppilot2_G_H2_seed42/config.json" > "$S/logs/assemble_c.log" 2>&1 \
  || { log "assemble-c 失敗"; exit 1; }
log "案 C の train の標的 作成"
for ARM in teacher shuffled; do
  G=$(wait_gpu 31000)
  nohup bash scripts/grasppilot/run_c.sh "$ARM" "$G" "$S/signals/C/t_${ARM}_train.npz" > "$S/logs/run_C_$ARM.out" 2>&1 &
  log "案 C $ARM を GPU $G で起動"
  sleep 180
done
log "終わり"
