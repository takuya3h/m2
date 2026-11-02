#!/usr/bin/env bash
# 非公式 T-2026-11-01-stage2-w23-bengio、§8 の h。禁止の場所で、契約の開始（task-start、2026-11-02 00:20 JST）より後に
# 中身が変わったファイルを更新時刻で列挙する（開始時に要約値を取っていないため、更新時刻で代える。audit.md の Task E）。
# Python の __pycache__ は import で作られるため別に数える。陽性対照として、本契約の置き場（書いてよい場所）でも同じ探し方をする。
#
#   bash write_audit.sh <出力の置き場>
set -uo pipefail
OUT=$1
mkdir -p "$OUT"
START="2026-11-01 15:20:00 UTC"
M=/home/ubuntu/slocal2/m2
OV=/home/ubuntu/slocal2/s2fix-bengio-body
ST=/home/ubuntu/slocal2/stage2pilot_store
scan() {   # 名前 経路 [find の除外]...
  local name=$1 path=$2; shift 2
  local all py
  all=$(find "$path" -newermt "$START" -type f "$@" -not -path '*/__pycache__/*' 2>/dev/null | sort)
  py=$(find "$path" -newermt "$START" -type f -path '*/__pycache__/*' 2>/dev/null | wc -l)
  printf '%s\n' "$all" | sed '/^$/d' > "$OUT/changed_${name}.txt"
  echo "$name changed=$(sed '/^$/d' "$OUT/changed_${name}.txt" | wc -l) pycache=$py path=$path"
}
{
  echo "start: $START"
  for s in "$ST"/*/; do
    n=$(basename "$s"); [ "$n" = T-2026-11-01-stage2-w23-bengio ] && continue
    scan "store_$n" "$s"
  done
  scan data_raw "$M/data/raw"
  scan data_external "$M/data/external"
  scan data_annotations "$M/data/annotations"
  scan third_party_main "$M/third_party"
  scan third_party_overlay "$OV/third_party"
  scan venv_main "$M/.venv"
  scan venv_reldetr "$M/.venv-relation-detr"
  scan baselines "$M/experiments/baselines"
  scan phase1_other "$M/experiments/phase1" -not -path '*/w23b_*'
  scan analysis_other "$M/experiments/analysis" -not -path '*/stage2_w23_bengio/*'
  scan tasks_other "$M/tasks" -not -path '*/T-2026-11-01-stage2-w23-bengio/*' -not -path '*/inbox.d/T-2026-11-01-stage2-w23-bengio.md'
  scan runindex "$M/runindex"
  echo "--- 陽性対照（本契約の置き場。変わっているはず）"
  scan positive_phase1_w23b "$M/experiments/phase1" -path '*/w23b_*'
  scan positive_store "$ST/T-2026-11-01-stage2-w23-bengio"
} | tee "$OUT/write_audit_summary.txt"
