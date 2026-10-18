#!/usr/bin/env bash
# 工程の交差適合用の塔の記憶の見張り。<half> の cf_ptower.py が LIMIT MiB を超えたら、その python だけを止める（PD の run を巻き込まないため）。
# run_cf_ptower.sh <half> が居なくなったら終わる。
HALF="$1"; LIMIT="${2:-34000}"
while pgrep -f "run_cf_ptower.sh $HALF" > /dev/null; do
  for pid in $(pgrep -f "cf_ptower.py --half $HALF"); do
    mem=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits | awk -F', ' -v p=$pid '$1==p{print $2}')
    if [ -n "$mem" ] && [ "$mem" -gt "$LIMIT" ]; then
      echo "$(date -u '+%F %T UTC') pid=$pid mem=${mem}MiB > ${LIMIT}MiB のため止める"; kill -TERM "$pid"
    fi
  done
  sleep 2
done
echo "$(date -u '+%F %T UTC') run_cf_ptower.sh $HALF が終わったので見張りを終える"
