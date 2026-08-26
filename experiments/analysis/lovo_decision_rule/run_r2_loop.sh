#!/usr/bin/env bash
set -u
source /home/ubuntu/slocal2/m2/.venv/bin/activate
for s in capacity_of_head capacity_of_head_denoise prune_across_sources flicker_scaling receptive_field_prune receptive_field_denoise; do
  echo "=== START $s $(date '+%H:%M:%S')"
  python "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/replicate_lovo.py" docs/analysis_scripts/proxy_lovo_${s}.py \
     --out "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/r2/${s}.json" --dumper "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/dump_folds_loop.py" --scaffold "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/lovo_scaffold" \
     --reps 12 --m 12 --seed 42 > "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/r2/${s}.log" 2>&1
  echo "=== END   $s rc=$? $(date '+%H:%M:%S')"
done
echo "R2 LOOP DONE $(date '+%H:%M:%S')"
