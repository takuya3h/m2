#!/usr/bin/env bash
# ============================================================================
# encrypt_env.sh — 平文 .env を gpg 対称暗号で .env.gpg にして git 管理可能にする。
#
# .env を編集したら毎回これを実行 → .env.gpg を commit/push（暗号文なので公開リポでも安全）。
# **平文 .env は絶対に commit しない**（.gitignore 済み）。鍵をローテーションしたら
# .env を更新 → 再実行 → commit、で全マシンに伝播する。
#
# 使い方:
#   bash scripts/encrypt_env.sh
#   git add .env.gpg && git commit -m "chore(secrets): rotate encrypted env" && git push
#
# 前提:
#   - パスフレーズ: 既定 ~/.config/egosurgery/env-passphrase（全マシンで同一・別経路配布）。
#     初回作成例:
#       mkdir -p ~/.config/egosurgery
#       (umask 077; printf '%s' 'STRONG_PASSPHRASE' > ~/.config/egosurgery/env-passphrase)
# ============================================================================
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PF="${EGOSURGERY_ENV_PASSPHRASE_FILE:-$HOME/.config/egosurgery/env-passphrase}"

[ -f .env ] || { echo "[encrypt_env] .env が無い（.env.example を元に作成）"; exit 1; }
[ -f "$PF" ] || { echo "[encrypt_env] パスフレーズが無い: $PF（上記コメントの手順で作成）"; exit 1; }

gpg --batch --yes --symmetric --cipher-algo AES256 --passphrase-file "$PF" -o .env.gpg .env
echo "[encrypt_env] .env -> .env.gpg（$(stat -c%s .env.gpg)B）。次: git add .env.gpg && git commit && git push"
echo "[encrypt_env] 注意: 平文 .env は commit しないこと（.gitignore 済み）。"
