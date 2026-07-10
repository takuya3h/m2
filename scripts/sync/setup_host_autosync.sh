#!/usr/bin/env bash
# setup_host_autosync.sh — 実験成果 auto-sync を「このホスト」で有効化する per-host セットアップ（冪等）。
#
# 背景: 自動同期のコード(git_autosync/finalize/CI workflow)は phase0 経由で配布されるが、
#   push 認証(deploy key)は .git/config = git 非配布。よって各ホストで本スクリプトの実行が要る。
#   keeper は phase0 の ref を進めるだけ(作業ツリー不変)なので、コード有効化にも git merge phase0 が要る。
#
# 何をするか（各フェーズ独立・失敗しても他フェーズは続行）:
#   A. サーバー名解決（SERVERNAME 優先。hostname=aolab の ilya/philip 衝突を弾く）
#   B. deploy key 生成（このホスト上・秘密鍵は外に出さない）＋ .git/config の push 経路設定
#   C. GitHub へ deploy key 登録（gh 認証があれば自動／無ければ公開鍵と手順を表示）
#   D. 疎通確認（ssh -T が "Hi takuya3h/m2!" を返すか＝scoped な deploy key 経路か）
#   E. コード有効化（exp/* ブランチで git merge phase0）
#
# 影響範囲: ~/.ssh/id_<host>deploy（新規鍵・既存があれば再利用）, このリポの .git/config
#   （remote.origin.pushurl / core.sshCommand）, GitHub リポの deploy key（登録時）, exp ブランチ（phase0 マージ）。
# 戻し方:  rm ~/.ssh/id_<host>deploy*  /  git config --unset core.sshCommand  /
#   git remote set-url --push origin <元URL>  /  GitHub Settings>Deploy keys で削除  /  git merge --abort。
#
# 配布: keeper.sh 同様、初回は各ホストへ手動配布（scp）してから実行する。
# 使い方:
#   bash scripts/sync/setup_host_autosync.sh            # セットアップ（冪等）
#   bash scripts/sync/setup_host_autosync.sh --verify   # 疎通確認のみ（登録後の再チェック）
#   SERVERNAME=philip bash scripts/sync/setup_host_autosync.sh   # hostname=aolab のホストは名前を明示
set -uo pipefail

REPO_SLUG="takuya3h/m2"
PUSH_SSH_URL="git@github.com:${REPO_SLUG}.git"
MODE="${1:-}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$ROOT" ] || { echo "ERROR: git リポジトリ内で実行してください"; exit 1; }
cd "$ROOT" || exit 1

# --- A. サーバー名解決 -------------------------------------------------------- #
SERVER="${SERVERNAME:-$(hostname)}"
if [ "$SERVER" = "aolab" ] && [ -z "${SERVERNAME:-}" ]; then
  echo "ERROR: hostname=aolab は ilya/philip で衝突します。SERVERNAME を明示して再実行してください:"
  echo "       SERVERNAME=philip bash scripts/sync/setup_host_autosync.sh"
  exit 1
fi
# 既存 core.sshCommand から鍵パスを流用（efros の手動構成 id_m2deploy 等に冪等追従）。無ければ host 別名。
EXIST_CMD="$(git config --local --get core.sshCommand 2>/dev/null || true)"
if [[ "$EXIST_CMD" =~ -i[[:space:]]+([^[:space:]]+) ]]; then
  KEY="${BASH_REMATCH[1]}"; KEY="${KEY/#\~/$HOME}"
else
  KEY="$HOME/.ssh/id_${SERVER}deploy"
fi
TITLE="deploy-${SERVER}"
SSH_OPTS=(-F /dev/null -i "$KEY" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new)
echo "== host=${SERVER}  key=${KEY}  deploy-key=${TITLE} =="

verify_conn() {
  echo "== 疎通確認 (ssh -T) =="
  [ -f "$KEY" ] || { echo "  NG: 鍵が存在しません: $KEY"; return 1; }
  local out; out="$(ssh "${SSH_OPTS[@]}" -T git@github.com 2>&1 || true)"
  echo "  > $out"
  if printf '%s' "$out" | grep -qF "Hi ${REPO_SLUG}!"; then
    echo "  OK: deploy key 経路（scoped push 可能）"; return 0
  fi
  echo "  NG: 'Hi ${REPO_SLUG}!' が出ていません（deploy key 未登録／ユーザー鍵が優先）"; return 1
}

if [ "$MODE" = "--verify" ]; then verify_conn; exit $?; fi

# --- B. deploy key 生成 + push 経路設定 --------------------------------------- #
echo "== B. deploy key 生成 + push 経路設定 =="
if [ -f "$KEY" ]; then
  echo "  鍵は既存（再利用）: $KEY"
else
  ssh-keygen -t ed25519 -N "" -C "$TITLE" -f "$KEY" || { echo "  ERROR: 鍵生成に失敗"; exit 1; }
  echo "  生成: $KEY"
fi
git remote set-url --push origin "$PUSH_SSH_URL"
git config core.sshCommand "ssh -F /dev/null -i ${KEY} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"
echo "  pushurl         = $(git config --local --get remote.origin.pushurl)"
echo "  core.sshCommand = $(git config --local --get core.sshCommand)"

# --- C. GitHub へ deploy key 登録 -------------------------------------------- #
echo "== C. GitHub へ deploy key 登録 =="
PUB="$(cat "${KEY}.pub")"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  if gh api "repos/${REPO_SLUG}/keys" --jq '.[].title' 2>/dev/null | grep -qx "$TITLE"; then
    echo "  既に登録済み（skip）: $TITLE"
  elif gh api "repos/${REPO_SLUG}/keys" -X POST -f "title=${TITLE}" -f "key=${PUB}" -F "read_only=false" >/dev/null 2>&1; then
    echo "  登録完了: $TITLE (write)"
  else
    echo "  自動登録に失敗。以下を手動登録してください（Settings>Deploy keys, Allow write ON）:"
    echo "  $PUB"
  fi
else
  echo "  gh 未認証 → 以下の公開鍵を手動登録してください（Settings>Deploy keys>Add, Allow write ON）:"
  echo "  $PUB"
  echo "  または gh 認証済みホスト(例: efros)で:"
  echo "    gh api repos/${REPO_SLUG}/keys -X POST -f title=${TITLE} -f key='<上の公開鍵>' -F read_only=false"
fi

# --- D. 疎通確認 -------------------------------------------------------------- #
verify_conn || echo "  → GitHub 登録後に: bash scripts/sync/setup_host_autosync.sh --verify で再確認してください"

# --- E. コード有効化（git merge phase0）-------------------------------------- #
echo "== E. コード有効化 (git merge phase0) =="
CUR="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
case "$CUR" in
  exp/*)
    if ! git diff --quiet || ! git diff --cached --quiet; then
      echo "  WARN: 未コミット変更あり → commit/stash 後に 'git merge phase0' を手動実行（merge skip）"
    else
      git fetch origin phase0:phase0 2>&1 | tail -1
      if git merge --no-edit phase0; then
        echo "  OK: phase0 反映済（git_autosync/finalize/CI workflow 有効化）"
      else
        git merge --abort 2>/dev/null || true
        echo "  CONFLICT → 中断(abort 済)。手動で 'git merge phase0' 解決、"
        echo "            または新規に 'git switch -c exp/${SERVER}-<theme> phase0' で作り直し"
      fi
    fi
    ;;
  *)
    echo "  WARN: 現在 '$CUR' は exp/* ではありません → auto-sync は guard#2 で skip されます。"
    echo "        'git switch -c exp/${SERVER}-<theme> phase0' などで exp/* ブランチに移ってから運用してください。"
    ;;
esac

echo "== 完了: exp/<host>-* ブランチで実験を完走すると 自動 commit+push+ドラフトPR が発火します。停止は EGOSURGERY_AUTOSYNC=0 =="
