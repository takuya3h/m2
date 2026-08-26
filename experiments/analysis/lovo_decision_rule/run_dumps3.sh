#!/usr/bin/env bash
set -u
cd /home/ubuntu/slocal2/m2
source .venv/bin/activate
D=experiments/analysis/lovo_decision_rule
for s in capacity_of_head_denoise prune_across_sources flicker_scaling receptive_field_prune receptive_field_denoise; do
  echo "=== START $s $(date '+%H:%M:%S')"
  python "/tmp/claude-1000/-home-ubuntu-slocal2-m2/355a735a-216d-4427-9f55-9180cd932c09/scratchpad/work/dump_folds_loop.py" docs/analysis_scripts/proxy_lovo_${s}.py \
     --out $D/folds/${s}.json --log $D/logs/${s}.log > $D/logs/${s}.harness.log 2>&1
  echo "=== END   $s rc=$? $(date '+%H:%M:%S')"
done
echo "LOOP DUMPS DONE $(date '+%H:%M:%S')"
