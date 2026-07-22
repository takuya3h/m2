#!/bin/bash
# new_experiment_branch.sh: 新しい実験用ブランチを phase0 から作成する小ヘルパ（設計仕様 §4.4）。
# 使い方: bash scripts/sync/new_experiment_branch.sh <theme>
# - server 名は SERVERNAME 環境変数（無ければ hostname）で解決する（$(hostname) 直用の
#   衝突回避: philip/ilya=aolab 等。resolve_server_name() と同じ発想）。
# - exp/<server>-<theme>-<YYYYMMDD> を phase0 を基点に作成する。
# - 既存の同名ブランチは上書きしない（見つかればエラーで停止）。
# - M2DIR は keeper.sh と同じ解決（slocal2 優先 → slocal）。
set -euo pipefail

M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)

theme="${1:-}"
if [ -z "$theme" ]; then
  echo "usage: bash scripts/sync/new_experiment_branch.sh <theme>" >&2
  exit 2
fi

# server 名解決: SERVERNAME を最優先、無ければ hostname（短縮・小文字化）。
server="${SERVERNAME:-$(hostname)}"
server=$(printf '%s' "$server" | cut -d. -f1 | tr '[:upper:]' '[:lower:]')

date_tag=$(date +%Y%m%d)
branch="exp/${server}-${theme}-${date_tag}"

# 基点ブランチ: 追跡済みの phase0（無ければ origin/phase0）。全 git 呼び出しは git -C <repo>。
if git -C "$M2DIR" rev-parse --verify --quiet phase0 >/dev/null; then
  base=phase0
elif git -C "$M2DIR" rev-parse --verify --quiet origin/phase0 >/dev/null; then
  base=origin/phase0
else
  echo "error: 基点ブランチ phase0 が見つかりません（$M2DIR）" >&2
  exit 1
fi

# 既存同名ブランチは上書きしない（fail loud）。
if git -C "$M2DIR" show-ref --verify --quiet "refs/heads/${branch}"; then
  echo "error: ブランチが既に存在します: ${branch}（上書きしません）" >&2
  exit 1
fi

git -C "$M2DIR" switch -c "$branch" "$base"
echo "created ${branch} (from ${base}) in ${M2DIR}"
