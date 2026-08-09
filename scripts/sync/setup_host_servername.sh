#!/usr/bin/env bash
# setup_host_servername.sh — 論理サーバー名 SERVERNAME を「このホスト」へ注入する per-host セットアップ（冪等）。
#
# 背景: resolve_server_name() (src/egosurgery/utils/server_name.py) は
#   SERVERNAME → EGOSURGERY_SERVER_NAME → cfg.logging.server_name → socket.gethostname()
#   の順で解決する。最後の砦の gethostname() はコンテナ環境で衝突する:
#   ilya と philip はいずれも "aolab" を返すため実サーバーを特定できず、
#   harvest_runindex.py の HOST_ALIASES は "aolab" を host=null へ落とす（推測しない設計）。
#   実測: runindex/index.csv の 10 行が host_raw=aolab / host=(空) になっている。
#   これを塞ぐには各ホストで SERVERNAME を「論理名」として明示するしかない。
#
# なぜ ~/.zshenv が主経路か（実測にもとづく）:
#   ログインシェルは zsh。zsh は ~/.zshenv を **対話・非対話・ログイン・スクリプトの全形態で
#   無条件に読む**。bash にはこれに相当する利用者ファイルが無い（~/.bashrc は非対話で早期 return、
#   ~/.profile はログインシェル限定）。学習は対話シェルから起動されるとは限らないため、
#   全形態を覆える ~/.zshenv を主経路に据え、bash 経路は補助として ~/.profile と ~/.bashrc に置く。
#
#   実測マトリクス（env -i で親からの継承を断って測定）:
#     zsh  -c  (非対話・非ログイン)  → ~/.zshenv が読まれる    ✓
#     zsh  -ic (対話)                → ~/.zshenv が読まれる    ✓
#     zsh  -lc (ログイン)            → ~/.zshenv が読まれる    ✓
#     bash -lc (ログイン)            → ~/.profile が読まれる   ✓
#     bash -ic (対話)                → ~/.bashrc が読まれる    ✓
#     bash -c  (非対話・非ログイン)  → どの利用者ファイルも読まれない  ✗（下記の既知の限界）
#
# 既知の限界: `env -i bash -c` は利用者ファイルでは覆えない。BASH_ENV は それ自体が環境変数のため
#   clean env からは鶏卵問題になる。覆うなら /etc/environment（PAM 経由・要 root・システム全体）
#   か、起動側での明示 export が要る。本スクリプトは root 権限を要求しないため対象外とする。
#
# 影響範囲: ~/.zshenv, ~/.profile, ~/.bashrc へ標識付きブロックを追記するだけ。
#   既存行は書き換えない。リポジトリ内のファイルには一切触れない。
# 戻し方: 各ファイルから "# >>> egosurgery SERVERNAME >>>" 〜 "# <<< egosurgery SERVERNAME <<<"
#   の 3 行を削除する。
#
# 使い方:
#   bash scripts/sync/setup_host_servername.sh bengio             # 適用
#   bash scripts/sync/setup_host_servername.sh --dry-run bengio   # 空実行（何も書かない）
#   bash scripts/sync/setup_host_servername.sh --verify           # 現在の解決結果の確認のみ
set -uo pipefail

BEGIN_MARK="# >>> egosurgery SERVERNAME >>>"
END_MARK="# <<< egosurgery SERVERNAME <<<"

# 主経路 ~/.zshenv を先頭に置く。順序は「全形態を覆う順」。
TARGETS=("$HOME/.zshenv" "$HOME/.profile" "$HOME/.bashrc")

DRY_RUN=0
VERIFY_ONLY=0
NAME=""
NAME_GIVEN=0

# --- 引数解析（--dry-run は任意の位置を許す） -------------------------------- #
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --verify)  VERIFY_ONLY=1 ;;
    --*)       echo "ERROR: 不明なオプション '$arg'（--dry-run / --verify のみ）" >&2; exit 2 ;;
    *)         NAME="$arg"; NAME_GIVEN=1 ;;
  esac
done

# --- 現在の解決結果を表示する（--verify） ------------------------------------ #
if [ "$VERIFY_ONLY" -eq 1 ]; then
  echo "== 現在の解決結果 =="
  echo "  SERVERNAME             = [${SERVERNAME:-未設定}]"
  echo "  EGOSURGERY_SERVER_NAME = [${EGOSURGERY_SERVER_NAME:-未設定}]"
  echo "  hostname               = [$(hostname)]"
  echo "== シェル形態別（env -i で継承を断って測定） =="
  for spec in "zsh -c:非対話" "zsh -ic:対話" "bash -lc:ログイン" "bash -ic:対話" "bash -c:非対話"; do
    sh_cmd="${spec%%:*}"; label="${spec##*:}"
    printf "  %-10s %-8s [%s]\n" "$sh_cmd" "$label" "$(probe_shell "$sh_cmd")"
  done
  exit 0
fi

# --- シェル形態別プローブ（センチネルで値だけを取り出す） -------------------- #
# 対話シェル (-i) は /etc/bash.bashrc の案内文を stdout に混ぜる。生の出力を値として
# 比較すると、機能は正しいのに検査だけが落ちる。センチネルで囲って抽出する。
probe_shell() {
  local sh_cmd="$1" out
  # shellcheck disable=SC2086
  out="$(env -i HOME="$HOME" $sh_cmd 'printf "__SN__%s__SN__" "${SERVERNAME:-未設定}"' 2>/dev/null)" || {
    printf '(起動失敗)'; return 0; }
  if [[ "$out" =~ __SN__(.*)__SN__ ]]; then
    printf '%s' "${BASH_REMATCH[1]}"
  else
    printf '(取得失敗)'
  fi
}

# --- 論理名の妥当性検査 ------------------------------------------------------ #
if [ "$NAME_GIVEN" -eq 0 ] || [ -z "$NAME" ]; then
  echo "ERROR: 論理名が空です。小文字英数とハイフンで 2〜20 文字を指定してください。" >&2
  echo "       例: bash scripts/sync/setup_host_servername.sh bengio" >&2
  exit 2
fi

# 小文字英数とハイフンのみ、2〜20 文字。先頭・末尾のハイフンは許さない。
# fullmatch 相当にするため前後をアンカーで固定する（部分一致で通さない）。
if ! printf '%s' "$NAME" | grep -qE '^[a-z0-9]([a-z0-9-]{0,18}[a-z0-9])$'; then
  echo "ERROR: 論理名 '$NAME' は規則に合いません。" >&2
  echo "       規則: 小文字英数とハイフンのみ / 2〜20 文字 / 先頭と末尾はハイフン以外" >&2
  exit 2
fi

echo "== 論理名: ${NAME}  mode=$([ "$DRY_RUN" -eq 1 ] && echo dry-run || echo apply) =="

# --- 既存値の検出（衝突なら上書きせず終了） ---------------------------------- #
# ファイル内の最後の `export SERVERNAME=...` の値を取り出す。引用符は剥がす。
read_declared() {
  local f="$1"
  [ -f "$f" ] || return 1
  local line
  line="$(grep -E '^[[:space:]]*export[[:space:]]+SERVERNAME=' "$f" 2>/dev/null | tail -1)" || true
  [ -n "$line" ] || return 1
  local v="${line#*=}"
  v="${v%\"}"; v="${v#\"}"; v="${v%\'}"; v="${v#\'}"
  printf '%s' "$v"
}

CONFLICT=0
# 実行中の環境に別名が入っていないか
if [ -n "${SERVERNAME:-}" ] && [ "${SERVERNAME}" != "$NAME" ]; then
  echo "  ⚠ 現在の環境に別の値が設定されています: SERVERNAME=[${SERVERNAME}] ≠ [${NAME}]" >&2
  CONFLICT=1
fi
for f in "${TARGETS[@]}"; do
  if cur="$(read_declared "$f")"; then
    if [ "$cur" != "$NAME" ]; then
      echo "  ⚠ ${f} に別の値が宣言されています: [${cur}] ≠ [${NAME}]" >&2
      CONFLICT=1
    fi
  fi
done
if [ "$CONFLICT" -eq 1 ]; then
  echo "ERROR: 既存の値と異なるため、上書きせず終了します。" >&2
  echo "       改名するなら既存の宣言を手で除いてから再実行してください。" >&2
  exit 1
fi

# --- 追記（ファイルごとに冪等） ---------------------------------------------- #
CHANGED=0
for f in "${TARGETS[@]}"; do
  if cur="$(read_declared "$f")" && [ "$cur" = "$NAME" ]; then
    echo "  skip   ${f}（既に同じ値が宣言済み）"
    continue
  fi
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "  would  ${f} へ追記する"
    CHANGED=1
    continue
  fi
  # 対象が無ければ新規作成する。既存行は書き換えない（追記のみ）。
  {
    printf '\n%s\n' "$BEGIN_MARK"
    printf 'export SERVERNAME=%s\n' "$NAME"
    printf '%s\n' "$END_MARK"
  } >> "$f" || { echo "ERROR: ${f} へ書けません" >&2; exit 1; }
  echo "  append ${f}"
  CHANGED=1
done

if [ "$DRY_RUN" -eq 1 ]; then
  echo "== 空実行のため何も書いていません（変更予定: $([ "$CHANGED" -eq 1 ] && echo あり || echo なし)）=="
  exit 0
fi
[ "$CHANGED" -eq 1 ] || echo "  変更なし（全ての対象が既に同じ値）"

# --- 適用後の確認（実際に読めるか） ------------------------------------------ #
echo "== 適用後の確認（env -i で継承を断って測定） =="
FAILED=0
for spec in "zsh -c:非対話" "zsh -ic:対話" "zsh -lc:ログイン" "bash -lc:ログイン" "bash -ic:対話"; do
  sh_cmd="${spec%%:*}"; label="${spec##*:}"
  val="$(probe_shell "$sh_cmd")"
  if [ "$val" = "$NAME" ]; then
    printf "  OK   %-10s %-8s [%s]\n" "$sh_cmd" "$label" "$val"
  else
    printf "  NG   %-10s %-8s [%s]\n" "$sh_cmd" "$label" "$val"
    FAILED=1
  fi
done
# 既知の限界。覆えないことを黙らせず毎回表示する。
nb="$(probe_shell "bash -c")"
printf "  --   %-10s %-8s [%s]  ← 既知の限界（利用者ファイルでは覆えない）\n" "bash -c" "非対話" "$nb"

if [ "$FAILED" -eq 1 ]; then
  echo "ERROR: 一部のシェル形態で読めませんでした。上の NG を確認してください。" >&2
  exit 1
fi
echo "== 完了。新しいシェルを開くか 'exec \$SHELL' で反映されます =="
