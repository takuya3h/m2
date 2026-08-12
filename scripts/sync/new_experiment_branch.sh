#!/bin/bash
# new_experiment_branch.sh: ホストの定位置ブランチを phase0 から作成する小ヘルパ。
# 使い方: bash scripts/sync/new_experiment_branch.sh [--dry-run] <logical-host>
# - logical-host は小文字英数とハイフンのみ、2〜20文字。
# - exp/<logical-host> を phase0 を基点に作成する。
# - 既存の同名ブランチは上書きしない（見つかればエラーで停止）。
# - M2DIR は keeper.sh と同じ解決（slocal2 優先 → slocal）。
set -euo pipefail

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  shift
fi

logical_host="${1:-}"
if [ -z "$logical_host" ] || [ "$#" -ne 1 ]; then
  echo "usage: bash scripts/sync/new_experiment_branch.sh [--dry-run] <logical-host>" >&2
  exit 2
fi

name_length=${#logical_host}
if [ "$name_length" -lt 2 ] || [ "$name_length" -gt 20 ]; then
  echo "error: logical-host は2文字以上20文字以下にしてください: ${logical_host}" >&2
  exit 2
fi
case "$logical_host" in
  *[!a-z0-9-]*)
    echo "error: logical-host は小文字英数とハイフンのみ使用できます: ${logical_host}" >&2
    exit 2
    ;;
esac
case "-${logical_host}-" in
  *-wip-*)
    echo "error: logical-host に作業状態を表す語 wip は使用できません: ${logical_host}" >&2
    exit 2
    ;;
esac
if [[ "$logical_host" =~ [0-9]{8} ]]; then
  echo "error: logical-host に8桁の日付は使用できません: ${logical_host}" >&2
  exit 2
fi

branch="exp/${logical_host}"
if [ "$DRY_RUN" -eq 1 ]; then
  printf '%s\n' "$branch"
  exit 0
fi

M2DIR=$([ -d ~/slocal2 ] && echo ~/slocal2/m2 || echo ~/slocal/m2)

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
