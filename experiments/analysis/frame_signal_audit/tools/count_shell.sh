#!/usr/bin/env bash
# T-2026-10-14-frame-signal-audit Task B — 方法 B: シェルの道具で辿る（方法 A と読み口を変える）。
#
# 工程 CSV は cut、術具 COCO は grep -o で file_name、画像は find -L の実体、manifest は grep -o で
# "frame" を取り、sort -u / comm で集合差を取る。Python の csv/json 解釈を一切通さない。
# 中間物は repo の外（$WORK）に置き、出力は sets_by_clip_method_b.csv だけ。
#
# 使い方: bash experiments/analysis/frame_signal_audit/tools/count_shell.sh <WORK_DIR>
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
OUT="$ROOT/experiments/analysis/frame_signal_audit"
WORK="${1:?WORK_DIR}"
mkdir -p "$WORK"
cd "$ROOT"

# 1) 四つの集合をフレーム名の一覧にする（1 行 1 フレーム、形は VV_C_NNNN）
tail -q -n +2 data/annotations/egosurgery_phase/*.csv | cut -d, -f1 | grep -E '^[0-9]{2}_[0-9]+_[0-9]{4}$' | sort -u > "$WORK/phase.txt"
cat data/annotations/egosurgery_tool/instances_{train,val,test}.json \
  | grep -oE '"file_name": *"[^"]+"' | sed -E 's/.*\/([^/"]+)\.jpg"$/\1/' | sort -u > "$WORK/tool.txt"
find -L data/raw/ego/train data/raw/ego/val data/raw/ego/test "data/raw/ego/other(17~21)" -type f -name '*.jpg' -printf '%f\n' \
  | sed 's/\.jpg$//' | grep -E '^[0-9]{2}_[0-9]+_[0-9]{4}$' | sort -u > "$WORK/host.txt"
cat data/processed/phase_manifest/{train,val,test}.json | grep -oE '"frame": *"[^"]+"' | sed -E 's/.*"([^"]+)"$/\1/' | sort -u > "$WORK/m15.txt"
cat data/processed/stage1_features/p20_manifest/{train,val,test}.json | grep -oE '"frame": *"[^"]+"' | sed -E 's/.*"([^"]+)"$/\1/' | sort -u > "$WORK/m20.txt"

# 枠 0 個の画像: image_id ごとの注釈数を awk で数え、注釈の無い id の file_name を引く
: > "$WORK/zero.txt"
for s in train val test; do
  f=data/annotations/egosurgery_tool/instances_$s.json
  # images 配列の id と file_name を順に取り出す（id → file_name の対にする）
  grep -oE '"(id|file_name|image_id)": *("[^"]+"|[0-9]+)' "$f" > "$WORK/tok_$s.txt"
  # images の要素は "id" → "width" → "height" → "file_name" の順（instances_*.json の実物）。
  # 直前の "id" を file_name に結び付ける。annotations の "id" の後に file_name は来ない。
  awk -v out="$WORK/zero.txt" '
    BEGIN{FS=": *"}
    /^"id"/ { last=$2; next }
    /^"file_name"/ {gsub(/"/,"",$2); sub(/.*\//,"",$2); sub(/\.jpg$/,"",$2); name[last]=$2; next}
    /^"image_id"/ { cnt[$2]++ ; next }
    END { for (i in name) if (!(i in cnt)) print name[i] >> out }
  ' "$WORK/tok_$s.txt"
done
sort -u "$WORK/zero.txt" -o "$WORK/zero.txt"

# 2) 集合差（comm は sort 済みを要する）
d() { comm -23 "$WORK/$1.txt" "$WORK/$2.txt" > "$WORK/${1}_minus_${2}.txt"; }
d phase tool; d tool phase; d phase host; d host phase; d tool host; d host tool
d phase m15; d m15 phase; d phase m20; d m20 phase; d m15 tool; d tool m15; d m20 host; d host m20

# 3) 区間ごとに数える（区間 = 先頭 2 つの下線区切り）
count_by_clip() { cut -d_ -f1,2 "$WORK/$1.txt" | sort | uniq -c | awk '{print $2","$1}'; }
cols="phase tool host m15 m20 phase_minus_tool tool_minus_phase phase_minus_host host_minus_phase tool_minus_host host_minus_tool phase_minus_m15 m15_minus_phase phase_minus_m20 m20_minus_phase m15_minus_tool tool_minus_m15 m20_minus_host host_minus_m20 zero"
for c in $cols; do count_by_clip "$c" > "$WORK/cnt_$c.csv"; done
clips=$(cat "$WORK"/phase.txt "$WORK"/tool.txt "$WORK"/host.txt "$WORK"/m15.txt "$WORK"/m20.txt | cut -d_ -f1,2 | sort -u)
{
  echo "clip,$(echo $cols | tr ' ' ',')"
  for clip in $clips; do
    line="$clip"
    for c in $cols; do
      n=$(awk -F, -v k="$clip" '$1==k{print $2}' "$WORK/cnt_$c.csv"); line="$line,${n:-0}"
    done
    echo "$line"
  done
} > "$OUT/sets_by_clip_method_b.csv"
echo "totals: phase=$(wc -l < "$WORK/phase.txt") tool=$(wc -l < "$WORK/tool.txt") host=$(wc -l < "$WORK/host.txt") m15=$(wc -l < "$WORK/m15.txt") m20=$(wc -l < "$WORK/m20.txt") zero=$(wc -l < "$WORK/zero.txt") phase_minus_tool=$(wc -l < "$WORK/phase_minus_tool.txt") tool_minus_phase=$(wc -l < "$WORK/tool_minus_phase.txt")"
echo "written -> $OUT/sets_by_clip_method_b.csv"
