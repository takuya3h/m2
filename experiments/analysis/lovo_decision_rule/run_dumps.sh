#!/usr/bin/env bash
# 既存の LOVO スクリプトを順に走らせ、fold ごとの素の値を取り出す。読み取り専用。
set -u
cd /home/ubuntu/slocal2/m2
source .venv/bin/activate
D=experiments/analysis/lovo_decision_rule
for s in gap_vs_presence recommended noise_structure noise_testonly signal_form \
         denoise_variants capacity_control prune_by_entropy prune_ubiquitous \
         capacity_of_head capacity_of_head_denoise receptive_field_prune \
         receptive_field_denoise prune_across_sources flicker_scaling; do
  f=docs/analysis_scripts/proxy_lovo_${s}.py
  [ -f "$f" ] || { echo "MISSING $f"; continue; }
  echo "=== START $s $(date '+%H:%M:%S')"
  python $D/dump_folds.py "$f" --out $D/folds/${s}.json --log $D/logs/${s}.log \
      > $D/logs/${s}.harness.log 2>&1
  echo "=== END   $s rc=$? $(date '+%H:%M:%S')"
done
echo "ALL DONE $(date '+%H:%M:%S')"
