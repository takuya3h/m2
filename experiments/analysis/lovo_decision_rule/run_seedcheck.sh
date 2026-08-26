#!/usr/bin/env bash
set -u
source /home/ubuntu/slocal2/m2/.venv/bin/activate
for tag in seed42_a seed42_b seed43; do
  case $tag in
    seed42_a|seed42_b) sd=42 ;;
    seed43) sd=43 ;;
  esac
  echo "=== $tag seed=$sd $(date '+%H:%M:%S')"
  python "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/replicate_lovo.py" docs/analysis_scripts/proxy_lovo_noise_testonly.py \
     --out "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/r2/seedcheck_${tag}.json" --dumper "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/dump_folds.py" --scaffold "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/lovo_scaffold" \
     --reps 6 --m 12 --seed $sd > "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/r2/seedcheck_${tag}.log" 2>&1
  echo "=== END $tag rc=$?"
done
echo "SEEDCHECK DONE $(date '+%H:%M:%S')"
