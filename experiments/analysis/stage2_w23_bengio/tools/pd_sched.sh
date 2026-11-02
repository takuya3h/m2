#!/usr/bin/env bash
# 非公式 T-2026-11-01-stage2-w23-bengio、Task D。PD の残りの run を「GPU 1 枚に run 3 本まで」で回す待ち行列。
#
# 07:0x JST に P3 の W3 の入れ替えが GPU の記憶の不足で止まった（W3 は学習中 1 本 約 13.5 GiB、4 本は 47.4 GiB に載らない）。
# 利用者の決定（2026-11-02 07:1x JST）: 枠が空き次第回す。pd_queue.sh の列の親を止め、残りをこの待ち行列だけで回す。
# 数えるのは GPU ごとの run の起動台本（scripts/w23/run_pd_w23_bengio.sh。学習前の評価・学習・確定のすべての間いる）で、
# GPU は /proc/<pid>/environ の CUDA_VISIBLE_DEVICES から読む。
#
#   bash pd_sched.sh "<型> <腕> <W>" ...       並べた順に、空いた GPU（run が 3 本未満）で始める
set -uo pipefail
CODE=/home/ubuntu/slocal2/m2
MAX=3
cd "$CODE"

count_on() {   # GPU $1 の run の起動台本の数
  local n=0 pid g
  for pid in $(pgrep -f "^bash scripts/w23/run_pd_w23_bengio.sh "); do
    g=$(tr '\0' '\n' < "/proc/$pid/environ" 2>/dev/null | sed -n 's/^CUDA_VISIBLE_DEVICES=//p')
    [ "$g" = "$1" ] && n=$((n + 1))
  done
  echo "$n"
}

for spec in "$@"; do
  read -r T ARM W <<< "$spec"
  while true; do
    c0=$(count_on 0); c1=$(count_on 1)
    if [ "$c0" -lt "$MAX" ] || [ "$c1" -lt "$MAX" ]; then
      sleep 60                                   # 確定の直後のゆらぎを避けて、もう一度数える
      c0=$(count_on 0); c1=$(count_on 1)
      if [ "$c0" -le "$c1" ] && [ "$c0" -lt "$MAX" ]; then G=0; break; fi
      if [ "$c1" -lt "$MAX" ]; then G=1; break; fi
    fi
    sleep 30
  done
  echo "[pd_sched] $(TZ=Asia/Tokyo date '+%F %T JST') start $T $ARM $W gpu=$G (gpu0=$c0 gpu1=$c1)"
  ( CUDA_VISIBLE_DEVICES=$G bash scripts/w23/run_pd_w23_bengio.sh "$T" "$ARM" "$W"
    echo "[pd_sched] $(TZ=Asia/Tokyo date '+%F %T JST') end $T $ARM $W rc=$?" ) &
  sleep 20
done
wait
echo "[pd_sched] $(TZ=Asia/Tokyo date '+%F %T JST') all done"
