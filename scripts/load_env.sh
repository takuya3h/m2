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
# 基点はこのスクリプト自身の場所から決める。**関数の外で解決すること。**
# zsh は既定で FUNCTION_ARGZERO が有効なため、関数の内側では $0 が関数名になる。
# その結果 dirname が "." に落ち、repo ではなくカレントディレクトリの 1 つ上を指す
# （2026-08-10 実測: zsh の関数内で $0=_egosurgery_load_env / BASH_SOURCE=未定義 →
#  基点が /home/ubuntu/slocal2 になり .env.gpg に到達しなかった）。
# ファイルの最上位なら zsh の $0 も bash の BASH_SOURCE[0] もスクリプトの場所を指す。
_egosurgery_env_self="${BASH_SOURCE[0]:-$0}"

_egosurgery_load_env() {
  local root pf tmp
  root="$(cd "$(dirname "${_egosurgery_env_self}")/.." && pwd)"
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
  # 🔴 復号は**一時ファイルへ**書き、平文 .env は上書きしない。
  #    平文 .env へ直接リダイレクトしていた頃は 2 つの壊れ方があった（2026-08-10 実測）:
  #    (a) .env に加えた編集が読み込みのたびに消える。
  #    (b) リダイレクトが gpg より先に走るため、復号に失敗すると .env が空になり、
  #        続く rm で消える。パスフレーズを 1 度間違えるだけで平文が失われる。
  #    復号先そのものを .env から変える案は採れない。scripts/run_*.sh 等 34 箇所が
  #    `[ -f .env ] && source .env` で平文を読んでおり、すべて fail-open のため
  #    無言で資格情報が載らなくなる（過去に s0_010-012 で同じ事故がある。
  #    docs/notion_run_ledger_auto_post.md）。よって **置き場は変えず、扱いを変える。**
  tmp="$root/.env.tmp.$$"
  ( umask 077; : > "$tmp" ) || return 1
  if ! gpg --batch --quiet --decrypt --passphrase-file "$pf" "$root/.env.gpg" > "$tmp" 2>/dev/null; then
    echo "[load_env] 復号失敗（パスフレーズ不一致 or .env.gpg 破損）。" >&2
    rm -f "$tmp"
    return 1
  fi
  if [ ! -f "$root/.env" ]; then
    mv "$tmp" "$root/.env"
  elif cmp -s "$tmp" "$root/.env"; then
    rm -f "$tmp"
  else
    # 平文が暗号文と食い違う。**編集を消さない。** 黙って上書きすると、
    # 鍵を更新した側と編集した側のどちらの意図も失われる。両方の直し方を示す。
    rm -f "$tmp"
    echo "[load_env] 警告: 平文 .env が .env.gpg と異なる。編集を保持し、上書きしない。" >&2
    echo "           暗号文の内容に更新する: rm $root/.env してから再実行" >&2
    echo "           手元の編集を正とする  : bash scripts/encrypt_env.sh で再暗号化" >&2
  fi
  set -a
  # shellcheck disable=SC1091
  . "$root/.env"
  set +a
  echo "[load_env] .env をロード（WANDB_API_KEY=$([ -n "${WANDB_API_KEY:-}" ] && echo set || echo unset) / NOTION_API_KEY=$([ -n "${NOTION_API_KEY:-}" ] && echo set || echo unset)）"
}
_egosurgery_load_env
unset _egosurgery_env_self
