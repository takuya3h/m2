#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# place_ego_images.sh
#   EgoSurgery 公式配布物の画像を data/raw/ego/{train,val,test}/<vid>/ に配置する。
#
#   - アノテーション(instances_*.json)は git 追跡済みのため対象外（clone 時点で存在）。
#   - 既定は symlink（高速・ディスク消費ゼロ。元データを正本として残す運用向け）。
#     --copy を付けると実コピー（rsync があれば差分コピー）。
#   - 動画ディレクトリ単位で配置し、追跡済みの .gitkeep は温存する（git 状態を汚さない）。
#   - 冪等: 既存の symlink は張り直し、既存の実ディレクトリは安全のためスキップ。
#
# 使い方（lecun でも aolab でも、リポジトリ直下から実行）:
#   bash scripts/place_ego_images.sh                 # symlink（既定）
#   bash scripts/place_ego_images.sh --copy          # 実コピー
#   EGO_SRC=/path/to/EgoSurgery/images/by_split \
#     bash scripts/place_ego_images.sh               # 元データ位置を上書き
# ---------------------------------------------------------------------------
set -euo pipefail

# リポジトリルート（このスクリプトの 1 つ上）
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SRC="${EGO_SRC:-/home/ubuntu/slocal2/EgoSurgery/images/by_split}"
DST="${EGO_DST:-$REPO_ROOT/data/raw/ego}"
MODE="symlink"   # symlink | copy

for arg in "$@"; do
  case "$arg" in
    --copy)     MODE="copy" ;;
    --symlink)  MODE="symlink" ;;
    --src=*)    SRC="${arg#*=}" ;;
    --dst=*)    DST="${arg#*=}" ;;
    -h|--help)
      echo "usage: $0 [--symlink|--copy] [--src=PATH] [--dst=PATH]"
      echo "  env: EGO_SRC, EGO_DST でも指定可"
      exit 0 ;;
    *) echo "ERROR: unknown arg: $arg" >&2; exit 2 ;;
  esac
done

echo "[place-ego] SRC = $SRC"
echo "[place-ego] DST = $DST"
echo "[place-ego] MODE= $MODE"
[ -d "$SRC" ] || { echo "ERROR: 元データが見つかりません: $SRC" >&2; exit 1; }

placed=0 skipped=0
for split in train val test; do
  s="$SRC/$split"
  d="$DST/$split"
  if [ ! -d "$s" ]; then
    echo "WARN: 元データに split が無いのでスキップ: $s"
    continue
  fi
  mkdir -p "$d"   # .gitkeep を残したまま split ディレクトリを保証

  # 動画ディレクトリのみを対象（.DS_Store 等のファイルは無視）
  while IFS= read -r viddir; do
    vid="$(basename "$viddir")"
    target="$d/$vid"

    # 既存の実ディレクトリは安全のため触らない（aolab 等で実コピー済みのケース）
    if [ -e "$target" ] && [ ! -L "$target" ]; then
      echo "  [$split] $vid : 既存の実ディレクトリ → スキップ"
      skipped=$((skipped+1))
      continue
    fi

    if [ "$MODE" = "symlink" ]; then
      ln -sfn "$viddir" "$target"
    else
      mkdir -p "$target"
      if command -v rsync >/dev/null 2>&1; then
        rsync -a "$viddir/" "$target/"
      else
        cp -rn "$viddir/." "$target/"
      fi
    fi
    njpg="$(find -L "$viddir" -type f -name '*.jpg' | wc -l)"
    echo "  [$split] $vid : $MODE ($njpg jpg)"
    placed=$((placed+1))
  done < <(find "$s" -mindepth 1 -maxdepth 1 -type d | sort)
done

echo "[place-ego] 配置=$placed 件 / スキップ=$skipped 件"

# 検証: jpg 枚数（symlink は -L で追従）
echo "[place-ego] 検証 (data/raw/ego 配下の jpg 枚数):"
for split in train val test; do
  n="$(find -L "$DST/$split" -type f -name '*.jpg' 2>/dev/null | wc -l)"
  printf "  %-5s : %s jpg\n" "$split" "$n"
done
echo "[place-ego] 期待値(論文準拠 split): train=9657  val=1515  test=4265"
echo "[place-ego] done."