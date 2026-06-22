#!/usr/bin/env bash
# ============================================================================
# load_env.sh — 暗号化された .env.gpg を復号して現在のシェルに環境変数をロードする。
#
# 公開リポに **平文 .env は置かない**。暗号文 .env.gpg のみ commit し、各マシンは
# パスフレーズ（別経路で配布・gitに入れない）で復号する。これで W&B / Notion の
# 認証がどのマシンでも揃い、実験が自動で追跡・記録される。
#
# 使い方（**source** すること。現在のシェルに env を入れるため）:
#   source scripts/load_env.sh
#
# 前提:
#   - パスフレーズファイル: 既定 ~/.config/egosurgery/env-passphrase（umask 077 で作成）。
#     環境変数 EGOSURGERY_ENV_PASSPHRASE_FILE で変更可。
#   - .env.gpg がリポに存在（scripts/encrypt_env.sh で生成・commit 済み）。
# ============================================================================
_egosurgery_load_env() {
  local root pf
  root="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")/.." && pwd)"
  pf="${EGOSURGERY_ENV_PASSPHRASE_FILE:-$HOME/.config/egosurgery/env-passphrase}"

  if [ ! -f "$root/.env.gpg" ]; then
    echo "[load_env] $root/.env.gpg が無い。先に scripts/encrypt_env.sh で暗号化・commit してください。" >&2
    return 1
  fi
  if [ ! -f "$pf" ]; then
    echo "[load_env] パスフレーズが無い: $pf" >&2
    echo "           作成例: mkdir -p ~/.config/egosurgery && (umask 077; printf '%s' 'YOUR_PASSPHRASE' > $pf)" >&2
    return 1
  fi
  if ! gpg --batch --quiet --decrypt --passphrase-file "$pf" "$root/.env.gpg" > "$root/.env" 2>/dev/null; then
    echo "[load_env] 復号失敗（パスフレーズ不一致 or .env.gpg 破損）。" >&2
    rm -f "$root/.env"
    return 1
  fi
  set -a
  # shellcheck disable=SC1091
  . "$root/.env"
  set +a
  echo "[load_env] .env をロード（WANDB_API_KEY=$([ -n "${WANDB_API_KEY:-}" ] && echo set || echo unset) / NOTION_API_KEY=$([ -n "${NOTION_API_KEY:-}" ] && echo set || echo unset)）"
}
_egosurgery_load_env
