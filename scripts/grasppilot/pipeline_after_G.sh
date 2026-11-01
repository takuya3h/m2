#!/usr/bin/env bash
# 確定の G が終わったら、val と予測-noCF の信号の推論 → assemble → 案 B の予測の四腕・案 A の六腕・恒等性・案 C の補助の頭の val を起こす
# （非公式 T-2026-11-01-grasp-pilot-g、Task D・E・F-4。確認の間隔の分の待ちを無くすための自動化）
set -u
cd "$(dirname "$0")/../.."
TASK=T-2026-11-01-grasp-pilot-g
S=/home/ubuntu/slocal2/stage2pilot_store/$TASK
P1=experiments/phase1
LOG=$S/logs/pipeline_after_G.log
log() { echo "$(TZ=Asia/Tokyo date '+%F %T JST') $*" >> "$LOG"; }
free_gpu() { nvidia-smi --query-gpu=index,memory.free --format=csv,noheader,nounits | awk -F', ' -v need="$1" '$2>=need {print $2, $1}' | sort -rn | head -1 | awk '{print $2}'; }
wait_gpu() { local g; until g=$(free_gpu "$1"); [ -n "$g" ]; do sleep 60; done; echo "$g"; }
log "待ち始め"
until [ -f "$P1/grasppilot2_G_all_seed42/exit_code.txt" ]; do sleep 60; done
[ "$(cat $P1/grasppilot2_G_all_seed42/exit_code.txt)" = 0 ] || { log "確定の G rc=$(cat $P1/grasppilot2_G_all_seed42/exit_code.txt) 止める"; exit 1; }
log "確定の G 終了"
source scripts/load_env.sh >/dev/null 2>&1 || true
export PYTHONPATH=src
CK=$S/g/ckpt/grasppilot2_G_all_seed42/best.pth
R=$S/signals/raw
inf() {  # 名前 split 動画
  local g; g=$(wait_gpu 9000)
  CUDA_VISIBLE_DEVICES=$g .venv/bin/python scripts/grasppilot/g_signals.py infer --ckpt "$CK" --g all --part "$2" --videos "$3" \
    --out "$R/$1" > "$S/logs/infer_$1.log" 2>&1 &
  log "推論 $1 を GPU $g で起動"; sleep 90
}
inf all_val val 09,10;            PV=$!
inf all_train_a train 01,02,03,06,08; PA=$!
inf all_train_b train 11,12,13,14,15; PB=$!
wait $PV && wait $PA && wait $PB || { log "推論の失敗"; exit 1; }
.venv/bin/python scripts/grasppilot/g_signals.py merge --parts "$R/all_train_a" "$R/all_train_b" --out "$R/all_train" > "$S/logs/merge_all_train.log" 2>&1 || { log "merge 失敗"; exit 1; }
.venv/bin/python scripts/grasppilot/g_signals.py assemble --raw "$R" --out "$S/signals" \
  --g-run "$P1/grasppilot2_G_all_seed42/config.json" "$P1/grasppilot2_G_H1_seed42/config.json" "$P1/grasppilot2_G_H2_seed42/config.json" \
  > "$S/logs/assemble.log" 2>&1 || { log "assemble 失敗"; exit 1; }
log "assemble 終了"
for i in $(seq 1 60); do git add experiments/analysis/grasp_pilot_g/targets/D_manifest.json && git commit -q -m "docs(grasppilot): 案 D の目録に val の q（確定の G）を足す

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01Cv1YxnSzNtByYThFEJdQ1f" && break; sleep 0.5; done
git push -q origin feat/grasp-pilot-g && log "目録の val を push $(git rev-parse --short HEAD)"
# 案 B の予測の四腕（空き 9.5 GB 以上の GPU に一本ずつ）
for ARM in pred_noCF pred_CF gtpred_CF shuffle; do
  g=$(wait_gpu 9500)
  CUDA_VISIBLE_DEVICES=$g nohup bash scripts/grasppilot/run_pd_grasp2.sh "$ARM" > "$S/logs/run_B_$ARM.out" 2>&1 &
  log "案 B $ARM を GPU $g で起動"; sleep 150
done
# 案 A の六腕（1 本 1 秒前後）と恒等性
g=$(wait_gpu 3000); CUDA_VISIBLE_DEVICES=$g bash experiments/analysis/grasp_pilot_g/caseA/run_caseA.sh > "$S/logs/run_caseA.log" 2>&1; log "案 A 終了 GPU $g"
# 正解との比べ（val、CPU）
nice -n 10 .venv/bin/python scripts/grasppilot/g_signals.py compare --raw "$R/all_val" --part val \
  --out experiments/analysis/grasp_pilot_g/signals/d2_compare_all_val.json --workers 6 > "$S/logs/compare_all_val.log" 2>&1 &
nice -n 10 .venv/bin/python scripts/grasppilot/g_signals.py compare --raw "$R/H2_on_H1" --part train \
  --out experiments/analysis/grasp_pilot_g/signals/d2_compare_H2_on_H1_train.json --workers 6 > "$S/logs/compare_H2_on_H1.log" 2>&1 &
# 案 B の恒等性（評価 1 本約 5 GB）
g=$(wait_gpu 6000); bash experiments/analysis/grasp_pilot_g/caseB/run_caseB_identity.sh "$g" > "$S/logs/run_caseB_identity.log" 2>&1; log "案 B の恒等性 終了 GPU $g"
# 案 C の補助の頭の val（終わった腕から）
for ARM in noaux teacher shuffled; do
  until [ -f "$P1/grasppilot2_C_${ARM}_seed42/exit_code.txt" ]; do sleep 120; done
  g=$(wait_gpu 4000)
  CUDA_VISIBLE_DEVICES=$g .venv/bin/python scripts/grasppilot/ptower_aux.py auxval --ckpt "$S/ptower/grasppilot2_C_${ARM}_seed42/last.pth" \
    --targets "$S/signals/C/t_val.npz" --out "$P1/grasppilot2_C_${ARM}_seed42/aux_val.json" > "$S/logs/auxval_$ARM.log" 2>&1
  log "案 C $ARM の補助の頭の val rc=$?"
done
log "終わり"
