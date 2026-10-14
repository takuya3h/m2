#!/usr/bin/env bash
# ============================================================================
# restore_relation_detr_source.sh — third_party/Relation-DETR のソースを復元する
#
# third_party/ は git にも Syncthing にも乗らず、checkpoints だけが置かれたホストがある
# （docs/third_party_sync_design_2026-08-05.md）。上流を clone し、
# third_party_snapshot/<host>/Relation-DETR/ の patch と tarball を当てて復元する。
#
# 🔴 どのホストの版を正とするかは研究上の判断である（同じ上流 commit でも中身が違う。
#    efros 35 / lecun 25 / philip 8 件）。既定の efros は最も広い版というだけで、
#    スナップショットは 2026-08-02 時点のもの。それ以降の追加分は含まない。
#
# 既存ファイルは上書きしない（checkpoints / data をそのまま残す）。
#
# 使い方:
#   bash scripts/restore_relation_detr_source.sh [snapshot_host] [dest]
#     snapshot_host: efros（既定）/ lecun / philip
#     dest:          既定 third_party/Relation-DETR（版の比較用に別の場所へも出せる）
# ============================================================================
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

HOST="${1:-efros}"
DEST="${2:-third_party/Relation-DETR}"
UPSTREAM="https://github.com/xiuqhou/Relation-DETR.git"
COMMIT="b485955c72452788240600da6d0f0b8cc49f33c7"   # 3 ホストの snapshot が共通に記録する上流 commit
SNAP="third_party_snapshot/${HOST}/Relation-DETR"

PATCH="$(ls "$SNAP"/*upstream_mods.patch 2>/dev/null | head -1 || true)"
TARBALL="$(ls "$SNAP"/*project_files.tar.gz 2>/dev/null | head -1 || true)"
if [ -z "$PATCH" ] || [ -z "$TARBALL" ]; then
  echo "[ERROR] $SNAP に patch と tarball が揃っていません（上流 commit を記録できたのは efros / lecun / philip）。" >&2
  exit 1
fi
if [ -f "$DEST/main.py" ]; then
  echo "[restore-reldetr] $DEST には既にソースがあります。何もしません。"
  exit 0
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[restore-reldetr] 上流 $COMMIT を取得（snapshot: $HOST）"
git clone --quiet "$UPSTREAM" "$TMP/src"
git -C "$TMP/src" checkout --quiet "$COMMIT"
git -C "$TMP/src" apply --check "$PROJECT_DIR/$PATCH"
git -C "$TMP/src" apply "$PROJECT_DIR/$PATCH"
tar xzf "$TARBALL" -C "$TMP/src"

mkdir -p "$DEST"
rsync -a --ignore-existing "$TMP/src/" "$DEST/"

echo "[restore-reldetr] 完了: $DEST"
echo "  上流 commit: $(git -C "$DEST" rev-parse HEAD)"
echo "  上流への改変: $(git -C "$DEST" diff --name-only | wc -l) 件 / .py: $(find "$DEST" -name '*.py' -not -path '*/third_party/*' | wc -l) 件"
