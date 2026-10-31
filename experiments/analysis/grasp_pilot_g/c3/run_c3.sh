#!/usr/bin/env bash
# 直した C3 の検査器で HTS の候補（egosurgery_hts の hand_seg・hand_tool_seg）の受け入れを測り直す（非公式 T-2026-11-01-grasp-pilot-g、Task B）
# 出力は本契約の出力先。experiments/audit/l0_hts_acceptance/ の既存のファイルは上書きしない
set -u
cd "$(dirname "$0")/../../../.."
OUT=${1:-experiments/analysis/grasp_pilot_g/c3/acceptance_report.json}
HAND=${HAND:-data/annotations/egosurgery_hts/hand_seg}
TOOLHAND=${TOOLHAND:-data/annotations/egosurgery_hts/hand_tool_seg}
.venv-relation-detr/bin/python scripts/audit_l0_hts_acceptance.py \
  --hand-dir "$HAND" --hand-prefix= --hand-splits train,val,test,extra \
  --toolhand-dir "$TOOLHAND" --toolhand-prefix= --out "$OUT"
