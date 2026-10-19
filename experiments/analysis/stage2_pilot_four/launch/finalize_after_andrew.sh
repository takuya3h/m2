#!/usr/bin/env bash
# Task E-5・F（bengio）: andrew の decoder-xattn の 6 本が push された後に、統合・照合・集計・検査を一続きで回す
# （非公式 T-2026-10-19-stage2-pilot-four-new-types）。andrew は読むだけ。止まる条件に当たれば、そこで止まって理由を出す。
#   1. andrew の分岐を fetch し、本分岐との差が新しいファイルだけで、6 本の run がそろっていることを確かめて merge --no-ff
#   2. 照合（完了判定 j）に要る 6 本の val の予測（版管理外）を andrew から同じ run の置き場へ写し、sha256 を照合
#   3. aggregate_four.py（REPORT.md・report.json）、test_audit_four.py（と --inject 04）、試験、禁止領域の検査
# 回す前に andrew の audit_andrew.md の S10 を読む（台本は S10 の節が在ることだけを確かめる）
set -uo pipefail
WT=/home/ubuntu/slocal2/m2-four
AW=/home/ubuntu/slocal2/m2-four-andrew
TASK=T-2026-10-19-stage2-pilot-four-new-types
BR=feat/stage2-pilot-four-new-types-andrew
OUT=$WT/experiments/analysis/stage2_pilot_four/final
mkdir -p "$OUT"
cd "$WT"
stop() { echo "[finalize] 停止: $*"; exit 1; }
echo "[finalize] start $(TZ=Asia/Tokyo date '+%H:%M:%S JST')"

# 1. 統合
git fetch origin "$BR" || stop "fetch に失敗"
git --no-pager diff --name-status HEAD...origin/$BR > "$OUT/andrew_diff_name_status.txt"
NONA=$(grep -c -v -E '^A\s' "$OUT/andrew_diff_name_status.txt")
[ "$NONA" = 0 ] || stop "andrew の分岐に新しいファイル以外の変更が $NONA 件（$OUT/andrew_diff_name_status.txt）"
for a in empty pred_noCF gt pred_CF gtpred_CF shuffle; do
  git cat-file -e "origin/$BR:experiments/phase1/stage2four_pd_DX_${a}_ep4_seed42/stage2four_metrics.json" 2>/dev/null \
    || stop "andrew の分岐に DX $a の stage2four_metrics.json が無い"
done
git cat-file -e "origin/$BR:tasks/$TASK/audit_andrew.md" || stop "audit_andrew.md が無い"
git --no-pager show "origin/$BR:tasks/$TASK/audit_andrew.md" > "$OUT/audit_andrew_at_merge.md"
grep -q -E "^## S10" "$OUT/audit_andrew_at_merge.md" || stop "audit_andrew.md に S10 の節が無い（andrew の確認が終わっていない）"
while [ -e /home/ubuntu/slocal2/m2/.git/worktrees/m2-four/index.lock ]; do sleep 1; done
git merge --no-ff --no-edit "origin/$BR" -m "Merge $BR: andrew の decoder-xattn の 6 本と監査記録" || stop "merge に失敗"
git --no-pager log --oneline -1 > "$OUT/merge_commit.txt"

# 2. 予測の写しと照合
: > "$OUT/dx_predictions_sha256.txt"
for a in empty pred_noCF gt pred_CF gtpred_CF shuffle; do
  R=experiments/phase1/stage2four_pd_DX_${a}_ep4_seed42
  mkdir -p "$WT/$R/predictions"
  rsync -a --ignore-existing "andrew:$AW/$R/predictions/" "$WT/$R/predictions/" || stop "DX $a の予測を写せない"
  for f in "$WT/$R/predictions/"*.json.gz; do
    b=$(basename "$f")
    l=$(sha256sum "$f" | cut -d' ' -f1)
    r=$(ssh -o BatchMode=yes andrew "sha256sum $AW/$R/predictions/$b" | cut -d' ' -f1)
    echo "$R/predictions/$b $l $r $([ "$l" = "$r" ] && echo same || echo DIFF)" >> "$OUT/dx_predictions_sha256.txt"
  done
done
grep -q DIFF "$OUT/dx_predictions_sha256.txt" && stop "予測の sha256 が andrew と食い違う（$OUT/dx_predictions_sha256.txt）"

# 3. 集計・検査
# shellcheck disable=SC1091
source /home/ubuntu/slocal2/m2/.venv/bin/activate
export PYTHONPATH=src:scripts PYTHONUTF8=1 EGO_ANN_DIR=/home/ubuntu/slocal2/s2fix-bengio-body/data/annotations/egosurgery_tool_folds/A
A=$WT/experiments/analysis/stage2_pilot_four
python scripts/stage2pilot/aggregate_four.py --out-json "$A/report.json" --out-md "$A/REPORT.md" \
  --head "$A/report_head.md" --tail "$A/report_tail.md" > "$OUT/aggregate.log" 2>&1; echo "[finalize] aggregate rc=$? $(tail -1 "$OUT/aggregate.log")"
python scripts/stage2pilot/test_audit_four.py --out "$A/test_audit/test_audit_final.json" > "$OUT/test_audit.log" 2>&1
echo "[finalize] test_audit rc=$? $(tail -1 "$OUT/test_audit.log")"
python scripts/stage2pilot/test_audit_four.py --inject 04 --out "$A/test_audit/test_audit_final_inject04.json" > "$OUT/test_audit_inject.log" 2>&1
echo "[finalize] test_audit inject rc=$? $(tail -1 "$OUT/test_audit_inject.log")"
CUDA_VISIBLE_DEVICES="" PYTHONPATH=src python -m pytest -q -p no:cacheprovider -rfE --continue-on-collection-errors > "$OUT/pytest_end.txt" 2>&1
echo "[finalize] pytest rc=$? $(grep -E 'passed|failed' "$OUT/pytest_end.txt" | tail -1)"
make forbidden-check TASK=$TASK > "$OUT/forbidden_check.json" 2>&1; echo "[finalize] forbidden-check rc=$?"
# 契約の検証（make task-validate）は、result.yaml の試験の件数と commit を埋めてから手で回す
echo "[finalize] end $(TZ=Asia/Tokyo date '+%H:%M:%S JST')"
