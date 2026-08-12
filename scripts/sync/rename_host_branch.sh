#!/usr/bin/env bash
# rename_host_branch.sh: ホストの定位置ブランチを exp/<logical-host> へ安全に移行する。
# 新しい遠隔参照を先に作り、その存在を確認してから局所分岐を改名する。
set -euo pipefail

usage() {
  echo "usage: bash scripts/sync/rename_host_branch.sh [--dry-run] <logical-host>" >&2
}

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
  shift
fi
logical_host="${1:-}"
if [ -z "$logical_host" ] || [ "$#" -ne 1 ]; then
  usage
  exit 2
fi

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if ! new_branch=$(bash "$SCRIPT_DIR/new_experiment_branch.sh" --dry-run "$logical_host"); then
  exit 2
fi

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [ -z "$ROOT" ]; then
  echo "error: Git repository 内で実行してください" >&2
  exit 1
fi
cd "$ROOT"

if [ -n "$(git status --porcelain)" ]; then
  echo "error: 作業ツリーが汚れています。commit または stash 後に再実行してください" >&2
  exit 1
fi

current_branch=$(git symbolic-ref --quiet --short HEAD 2>/dev/null || true)
if [ -z "$current_branch" ]; then
  echo "error: detached HEAD では分岐名を変更できません" >&2
  exit 1
fi
if [ "$current_branch" = "$new_branch" ]; then
  echo "already canonical: ${new_branch}"
  exit 0
fi
if git show-ref --verify --quiet "refs/heads/${new_branch}"; then
  echo "error: 局所分岐が既に存在します: ${new_branch}" >&2
  exit 1
fi
if ! git remote get-url origin >/dev/null 2>&1; then
  echo "error: remote origin がありません" >&2
  exit 1
fi

case_only=0
current_folded=$(printf '%s' "$current_branch" | tr '[:upper:]' '[:lower:]')
if [ "$current_folded" = "$new_branch" ]; then
  case_only=1
fi
intermediate="${new_branch}-case-rename-tmp"
if [ "$case_only" -eq 1 ] && git show-ref --verify --quiet "refs/heads/${intermediate}"; then
  echo "error: 大文字小文字改名用の一時分岐が既に存在します: ${intermediate}" >&2
  exit 1
fi

echo "current: ${current_branch}"
echo "target:  ${new_branch}"
if [ "$DRY_RUN" -eq 1 ]; then
  echo "[dry-run 1/3] git push -u origin HEAD:refs/heads/${new_branch}"
  echo "[dry-run 2/3] git fetch origin ${new_branch}:refs/remotes/origin/${new_branch}"
  if [ "$case_only" -eq 1 ]; then
    echo "[dry-run 3/3] git branch -m ${intermediate}; git branch -m ${new_branch}"
  else
    echo "[dry-run 3/3] git branch -m ${new_branch}"
  fi
  echo "old remote remains: origin/${current_branch}"
  exit 0
fi

echo "[1/3] 新しい遠隔参照を作成"
git push -u origin "HEAD:refs/heads/${new_branch}"

echo "[2/3] m2-sync が参照する remote-tracking ref を確認"
git fetch origin "${new_branch}:refs/remotes/origin/${new_branch}"
if ! git rev-parse --verify --quiet "refs/remotes/origin/${new_branch}" >/dev/null; then
  echo "error: origin/${new_branch} を確認できません。局所分岐は変更していません" >&2
  exit 1
fi

echo "[3/3] 局所分岐を改名"
if [ "$case_only" -eq 1 ]; then
  git branch -m "$intermediate"
  if ! git branch -m "$new_branch"; then
    git branch -m "$current_branch" 2>/dev/null || true
    echo "error: 大文字小文字のみの改名に失敗しました" >&2
    exit 1
  fi
else
  git branch -m "$new_branch"
fi

actual_branch=$(git symbolic-ref --quiet --short HEAD)
upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)
if [ "$actual_branch" != "$new_branch" ] || [ "$upstream" != "origin/${new_branch}" ]; then
  echo "error: 移行後の前提が不一致です: branch=${actual_branch} upstream=${upstream:-none}" >&2
  exit 1
fi
if ! git rev-parse --verify --quiet "refs/remotes/origin/${new_branch}" >/dev/null; then
  echo "error: m2-sync 用の origin/${new_branch} がありません" >&2
  exit 1
fi

echo "complete: ${current_branch} -> ${new_branch}"
echo "verified: origin/${new_branch} exists before and after local rename"
echo "old remote was not deleted: origin/${current_branch}"
