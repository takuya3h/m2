#!/usr/bin/env bash
# 学習中の GPU の使用の見張り（外部の使用の検出用）。60 秒ごとに全体の使用量・利用率・電力と、nvidia-smi の compute 一覧の件数を記録する。
# コンテナの中で外のプロセスが見えないため、本契約の run の想定の山（Task C の実測）を超えた増加で外部の使用を疑う。
S=/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-grasp-pilot-d-rerun
F=$S/logs/gpu_watch.csv
[ -s "$F" ] || echo "jst,gpu,memory_used_mib,util_pct,power_w" > "$F"
while true; do
  t=$(TZ=Asia/Tokyo date '+%F %T')
  nvidia-smi --query-gpu=index,memory.used,utilization.gpu,power.draw --format=csv,noheader,nounits | awk -F', ' -v t="$t" '{print t","$1","$2","$3","$4}' >> "$F"
  sleep 60
done
