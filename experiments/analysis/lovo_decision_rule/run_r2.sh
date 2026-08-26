#!/usr/bin/env bash
set -u
W=/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work
S=/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/lovo_scaffold
source /home/ubuntu/slocal2/m2/.venv/bin/activate
for s in presence gap_vs_presence recommended noise_structure noise_testonly \
         signal_form denoise_variants capacity_control prune_by_entropy prune_ubiquitous; do
  echo "=== START $s $(date '+%H:%M:%S')"
  python "$W/replicate_lovo.py" docs/analysis_scripts/proxy_lovo_${s}.py \
     --out "$W/r2/${s}.json" --dumper "$W/dump_folds.py" --scaffold "$S" \
     --reps 24 --m 12 --seed 42 > "$W/r2/${s}.log" 2>&1
  echo "=== END   $s rc=$? $(date '+%H:%M:%S')"
done
echo "R2 ALL DONE $(date '+%H:%M:%S')"
