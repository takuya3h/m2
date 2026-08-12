#!/usr/bin/env bash
# setup_host_autosync.sh — 実験成果 auto-sync を「このホスト」で有効化する per-host セットアップ（冪等）。
#
# 背景: 自動同期のコード(git_autosync/finalize/CI workflow)は phase0 経由で配布されるが、
#   push 認証(deploy key)は .git/config = git 非配布。よって各ホストで本スクリプトの実行が要る。
#   keeper は phase0 の ref を進めるだけ(作業ツリー不変)なので、コード有効化にも git merge phase0 が要る。
#
# 安全設計（未プッシュ/未マージの作業があるホスト向け）:
#   既定実行は deploy key 設定(B-D)だけ = push も merge も working-tree 変更も起きない安全操作。
#   コード有効化(E: git merge phase0)は **--activate 指定時だけ**。
#   有効化すると、次の実験完了時に git_autosync が `git push HEAD:exp/<host>` を実行し、
#   **そのブランチの未プッシュ・コミットが丸ごと public origin に載る**（public リポ）。
#   git_autosync の秘密スキャンは新規証跡 dir のみ対象で履歴は見ないため、
#   --activate では有効化前に「未プッシュ履歴の秘密スキャン」をゲートとして自動実行し、
#   秘密様パターンを検出したら中止する。
#
# フェーズ（各独立・失敗しても続行。E のみ --activate 時）:
#   A. サーバー名解決（SERVERNAME 優先。hostname=aolab の ilya/philip 衝突を弾く）
#   B. deploy key 生成（このホスト上・秘密鍵は外に出さない）＋ .git/config の push 経路設定
#   C. GitHub へ deploy key 登録（gh 認証があれば自動／無ければ公開鍵と手順を表示）
#   D. 疎通確認（ssh -T が "Hi takuya3h/m2!" を返すか＝scoped な deploy key 経路か）
#   E. コード有効化（未プッシュ履歴の秘密スキャン → exp/* で git merge phase0）※--activate 時のみ
#
# 影響範囲: ~/.ssh/id_<host>deploy（新規鍵・既存があれば再利用）, このリポの .git/config
#   （remote.origin.pushurl / core.sshCommand）, GitHub リポの deploy key（登録時）,
#   --activate 時のみ exp ブランチ（phase0 マージ）。
# 戻し方:  rm ~/.ssh/id_<host>deploy*  /  git config --unset core.sshCommand  /
#   git remote set-url --push origin <元URL>  /  GitHub Settings>Deploy keys で削除  /  git merge --abort。
#
# 配布: keeper.sh 同様、初回は各ホストへ手動配布（scp）してから実行する。
# 使い方:
#   bash scripts/sync/setup_host_autosync.sh            # deploy key 設定のみ（安全・merge/push なし）
#   bash scripts/sync/setup_host_autosync.sh --activate # 上記 + 秘密スキャン + git merge phase0（有効化）
#   bash scripts/sync/setup_host_autosync.sh --verify   # 疎通確認のみ（「Hi takuya3h/m2!」なら OK）
#   SERVERNAME=philip bash scripts/sync/setup_host_autosync.sh   # ★ ilya/philip は hostname=aolab 衝突のため名前を明示
set -uo pipefail

REPO_SLUG="takuya3h/m2"
PUSH_SSH_URL="git@github.com:${REPO_SLUG}.git"
MODE="${1:-}"

# 次の push で初めて公開されるコミット群に対する秘密スキャン用パターン。
SECRET_RE='ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|gh[ousr]_[A-Za-z0-9]{30,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY|xox[baprs]-[A-Za-z0-9-]{10,}|secret_[A-Za-z0-9]{40,}|AIza[A-Za-z0-9_-]{30,}'

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$ROOT" ] || { echo "ERROR: git リポジトリ内で実行してください"; exit 1; }
cd "$ROOT" || exit 1

# --- モード判定 -------------------------------------------------------------- #
ACTIVATE=0
case "$MODE" in
  "")          : ;;                       # 既定: deploy key 設定のみ
  "--activate") ACTIVATE=1 ;;             # + コード有効化(E)
  "--verify")   : ;;                      # 疎通のみ（下で処理）
  *) echo "ERROR: 不明なオプション '$MODE'（--activate / --verify のみ）"; exit 1 ;;
esac

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
echo "== host=${SERVER}  key=${KEY}  deploy-key=${TITLE}  mode=${MODE:-setup-only} =="

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

# 次の push で初めて公開される（=どの remote にも無い）コミットの追加内容に秘密が無いか。
scan_unpushed_secrets() {
  echo "== 未プッシュ履歴の秘密スキャン（public push 前ゲート）=="
  local commits; commits="$(git rev-list HEAD --not --remotes 2>/dev/null || true)"
  if [ -z "$commits" ]; then
    echo "  未プッシュ・コミットなし（スキャン対象なし）"; return 0
  fi
  local n; n="$(printf '%s\n' "$commits" | grep -c .)"
  echo "  対象: 未プッシュ ${n} コミット"
  local hits
  hits="$(git log -p --no-color HEAD --not --remotes 2>/dev/null | grep -E '^\+' | grep -Ec "$SECRET_RE" || true)"
  if [ "${hits:-0}" -gt 0 ]; then
    echo "  ⚠ 秘密様パターンを ${hits} 箇所検出。public への漏洩防止のため有効化を中止します。"
    echo "    詳細:   git log -p HEAD --not --remotes | grep -nE '$SECRET_RE'"
    echo "    対処後: 該当を履歴から除去 → 再度 --activate。誤検知と判断するなら手動 'git merge phase0' で有効化可。"
    return 1
  fi
  echo "  OK: 秘密様パターンなし"; return 0
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

# --- E. コード有効化（--activate 時のみ）------------------------------------- #
if [ "$ACTIVATE" != 1 ]; then
  echo "== E. コード有効化 (git merge phase0) は SKIP（--activate 未指定・安全既定）=="
  echo "  deploy key 設定のみ完了。push も merge も working-tree 変更も起きていません。"
  echo "  auto-sync を有効化する準備ができたら（各ホストの区切りの良いタイミングで）:"
  echo "    1) 進行中の作業を commit / stash（作業ツリーをクリーンに）"
  echo "    2) bash scripts/sync/setup_host_autosync.sh --activate"
  echo "  ※有効化後の初回実験で、そのブランチの未プッシュ・コミットが public origin に push されます。"
  exit 0
fi

echo "== E. コード有効化 (git merge phase0) =="
CUR="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
case "$CUR" in
  exp/*)
    if ! git diff --quiet || ! git diff --cached --quiet; then
      echo "  WARN: 未コミット変更あり → commit/stash 後に再度 --activate（安全のため merge skip）"
    elif ! scan_unpushed_secrets; then
      echo "  → 有効化を中止しました（deploy key 設定は完了済み）。"
    else
      git fetch origin phase0:phase0 2>&1 | tail -1
      if git merge --no-edit phase0; then
        echo "  OK: phase0 反映済（git_autosync/finalize/CI workflow 有効化）"
        echo "  次の実験完了で自動 commit+push+ドラフトPR が発火します（初回 push でこのブランチ全体が公開）。"
      else
        git merge --abort 2>/dev/null || true
        echo "  CONFLICT → 中断(abort 済)。手動で 'git merge phase0' 解決、"
        echo "            または 'bash scripts/sync/new_experiment_branch.sh <logical-host>' で作り直し"
      fi
    fi
    ;;
  *)
    echo "  WARN: 現在 '$CUR' は exp/* ではありません → auto-sync は guard#2 で skip されます。"
    echo "        'bash scripts/sync/new_experiment_branch.sh <logical-host>' で exp/* ブランチへ移ってから運用してください。"
    ;;
esac

echo "== 完了。停止したいときは EGOSURGERY_AUTOSYNC=0 を export =="
