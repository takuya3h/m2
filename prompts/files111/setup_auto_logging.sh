#!/usr/bin/env bash
# =============================================================================
# setup_auto_logging.sh
#   研究記録の全面自動化（Notion連携）を Claude Code に実装させるための
#   「前提チェック → ブリーフ配置 → Claude Code 起動コマンド提示」スクリプト。
#
#   使い方:
#     1) 本スクリプトと auto_logging_implementation.md をリポジトリのルートに置く
#     2) bash setup_auto_logging.sh            # 既定: 前提チェックのみ（安全）
#        bash setup_auto_logging.sh --run      # 前提チェック後、Claude Code を起動
#
#   設計方針:
#     - 既定では「何も壊さない」。チェックと推奨コマンドの提示のみ。
#     - 自動記録は REST 経由（.env のトークン）。MCP は使わない。
#     - .env が無い/トークン未設定でも fail-open（実装は no-op で進む想定）。
# =============================================================================
set -euo pipefail

BRIEF="prompts/auto_logging_implementation.md"
SRC_BRIEF="auto_logging_implementation.md"   # 同梱物（ルート直下に置いた場合）
RUN=0
[[ "${1:-}" == "--run" ]] && RUN=1

c_red()  { printf '\033[31m%s\033[0m\n' "$*"; }
c_grn()  { printf '\033[32m%s\033[0m\n' "$*"; }
c_ylw()  { printf '\033[33m%s\033[0m\n' "$*"; }
c_bld()  { printf '\033[1m%s\033[0m\n' "$*"; }

fail=0
note() { c_ylw "  - $*"; }
ok()   { c_grn "  [OK] $*"; }
bad()  { c_red "  [要対応] $*"; fail=1; }

c_bld "=== 0. 実行場所の確認 ==="
if [[ -f "pyproject.toml" && -d "src/egosurgery" ]]; then
  ok "リポジトリルートで実行されています。"
else
  bad "リポジトリルート（pyproject.toml と src/egosurgery/ がある場所）で実行してください。"
fi

c_bld "=== 1. 実装ブリーフの配置 ==="
mkdir -p prompts
if [[ -f "$BRIEF" ]]; then
  ok "$BRIEF は既に存在します。"
elif [[ -f "$SRC_BRIEF" ]]; then
  cp "$SRC_BRIEF" "$BRIEF"
  ok "$SRC_BRIEF を $BRIEF へ配置しました。"
else
  bad "$SRC_BRIEF（同梱の実装ブリーフ）が見つかりません。ルートに置いてから再実行してください。"
fi

c_bld "=== 2. Notion 連携の前提（REST 経由・秘密は .env） ==="
if [[ -f ".env" ]]; then
  ok ".env が存在します。"
  if grep -qE '^NOTION_API_KEY=.+' .env 2>/dev/null; then
    ok "NOTION_API_KEY が設定済み（自動記録が有効化されます）。"
  else
    note "NOTION_API_KEY が未設定です。→ 実装は no-op（fail-open）で進みますが、記録は飛びません。"
    note "  有効化するには .env に NOTION_API_KEY=secret_xxx を設定してください。"
  fi
else
  note ".env がありません。cp .env.example .env で作成し、NOTION_API_KEY を設定すると自動記録が有効になります。"
fi

if [[ -f "configs/notion.yaml" ]]; then
  ok "configs/notion.yaml（非秘密 ID レジストリ）が存在します。"
else
  note "configs/notion.yaml が見つかりません。ブリーフ §4 の ID 表を元に作成対象です（Claude Code が追記）。"
fi

# .env がうっかり追跡されていないか（秘密混入の早期検知）
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  if git ls-files --error-unmatch .env >/dev/null 2>&1; then
    bad ".env が Git 追跡対象です。直ちに 'git rm --cached .env' し .gitignore に追加してください。"
  else
    ok ".env は Git 追跡外です。"
  fi
fi

c_bld "=== 3. Python から既存 Notion ヘルパが見えるか（任意） ==="
PY="${PYTHON:-python}"
if PYTHONPATH=src "$PY" - <<'PYEOF' 2>/dev/null
import importlib.util as u
for m in ("egosurgery.utils.notion_ops", "egosurgery.utils.notion_logger", "egosurgery.utils.experiment_manager"):
    assert u.find_spec(m) is not None, m
print("ok")
PYEOF
then
  ok "notion_ops / notion_logger / experiment_manager を import 可能。"
else
  note "既存ヘルパの import を確認できませんでした（venv 未有効化の可能性）。source .venv/bin/activate 後に再確認を推奨。"
fi

echo
if [[ $fail -ne 0 ]]; then
  c_red "▲ 未対応項目があります。上の [要対応] を解消してから --run してください。"
  exit 1
fi
c_grn "▲ 前提チェックは良好です。"

echo
c_bld "=== 4. Claude Code への投入（実装の起動） ==="
cat <<'EOF'
このブリーフは「Claude Code に実装させる指示書」です。以下のいずれかで投入してください。

 (A) 対話セッションで投入（推奨・各マイルストーンを目視確認しながら）:
     claude
     > prompts/auto_logging_implementation.md の手順どおりに、Milestone A から順に実装して。
     >   各マイルストーン後に受け入れ基準(§9)を実行し、緑になってから次へ進んで。

 (B) ファイルを直接渡す:
     claude < prompts/auto_logging_implementation.md

 (C) 1コマンドで指示文を渡す:
     claude -p "prompts/auto_logging_implementation.md に従い Milestone A→D を実装。各段階で §9 を実行。"

  ※ フラグはご利用の Claude Code バージョンに合わせて調整してください。
  ※ 重要: 自動記録は REST 経由で実装させること（MCP Notion ツールは無人実行で承認待ちになります）。
EOF

if [[ $RUN -eq 1 ]]; then
  echo
  if command -v claude >/dev/null 2>&1; then
    c_bld "--run 指定: Claude Code を起動します（方式 C）。"
    claude -p "prompts/auto_logging_implementation.md に従い、Milestone A から順に実装してください。各マイルストーン後に §9 の受け入れ基準を実行し、緑になってから次へ進んでください。自動記録は必ず REST 経由（.env のトークン）で実装し、MCP Notion ツールは使わないでください。"
  else
    c_red "claude コマンドが見つかりません。Claude Code をインストール後、上記 (A)〜(C) を手動で実行してください。"
    exit 127
  fi
fi
