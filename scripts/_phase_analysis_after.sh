#!/usr/bin/env bash
# 検出器 driver（_detector_full_study.sh）完了を待ち、phase probe を自動実行する waiter。
# Method A 3-seed（det42/123/456）＋ hires C（det42）を、揃っている特徴だけ probe する。
# GPU は driver 占有中は使えないため、driver プロセス消滅を待ってから起動。
# 起動: nohup bash scripts/_phase_analysis_after.sh & （background）
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH=src
STATUS="logs/detector_study_status.tsv"
mark() { echo -e "$(date +%H:%M:%S)\t$1\t$2" >> "$STATUS"; }
log()  { echo "[$(date +%H:%M:%S)] $*" | tee -a logs/phase_analysis.log; }

log "waiter 起動: detector driver 完了を待機…"
# driver プロセスが消えるまで待つ（成功/失敗いずれでも解析へ進む）
while pgrep -f "_detector_full_study.sh" >/dev/null 2>&1; do sleep 300; done
log "detector driver 終了を検出 → phase 解析へ"
mark "PHASE_ANALYSIS" START

ready() { # <tag> : 必要 3 特徴(val)が揃っているか
  [ -f "data/processed/stage1_features/$1/val_gap.npz" ] \
  && [ -f "data/processed/t1a_regiontoken/$1/val_regiontoken.npz" ] \
  && [ -f "data/processed/b2a_detsignal/$1/val_toolpresence.npz" ]
}

# ---- Method A 3-seed paired-σ（det42/123/456）phase-seed 3点平均・冪等 ----
touch logs/phase3seed_results.tsv
for ds in 42 123 456; do
  n=$(awk -F'\t' -v s="$ds" '$1==s' logs/phase3seed_results.tsv 2>/dev/null | wc -l)
  if [ "$n" -ge 18 ]; then log "SKIP det$ds（既に完了 ${n}行・並走分を再利用）"; continue; fi
  if ready "relation_detr_seed${ds}" && ready "relation_detr_augstrong_seed${ds}"; then
    log "3-seed probe: detector_seed=$ds (phase-seed 3点平均)"
    bash scripts/_run_phase_probe_3seed.sh "$ds" 0 >> logs/phase_analysis.log 2>&1
  else
    log "SKIP detector_seed=$ds（特徴未整備）"
  fi
done
log "=== Method A 3-seed paired-σ 集計 ==="
python3 scripts/paired_sigma_3seed.py 2>&1 | tee logs/paired_sigma_summary.txt | tee -a logs/phase_analysis.log

# ---- hires C（det42）: frozen42 / augstrong42 / hires42 の 3 者比較 ----
if ready "relation_detr_augstrong_hires_seed42"; then
  log "=== hires C probe（frozen42 / augstrong42 / hires42）==="
  : > logs/hires_probe_results.tsv
  for tag in relation_detr_seed42 relation_detr_augstrong_seed42 relation_detr_augstrong_hires_seed42; do
    for spec in "S4:scripts/train_s4_tecno.py" \
                "B2a:scripts/train_b2a.py --tool-source pred" \
                "T1a:scripts/train_t1a.py --description hires_probe_${tag}"; do
      m="${spec%%:*}"; scr="${spec#*:}"
      d=$(RELDETR_FROZEN_TAG="$tag" CUDA_VISIBLE_DEVICES=0 python3 $scr --seed 42 \
            2>>logs/phase_analysis.log | grep -oE "evidence written -> .*" | tail -1 | sed 's/.*-> //')
      echo -e "${tag}\t${m}\t${d}" >> logs/hires_probe_results.tsv
      log "  hires $tag/$m -> $d"
    done
  done
else
  log "SKIP hires C（augstrong_hires_seed42 特徴未整備）"
fi

log "=== phase 解析 完了 ==="
mark "PHASE_ANALYSIS" DONE
