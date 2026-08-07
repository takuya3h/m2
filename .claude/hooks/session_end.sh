#!/usr/bin/env bash
# セッション終了時に、対話記録から機械的な要素を抽出して残す。
# 標準入力に session_id と transcript_path を含む JSON が渡される。
# 記録に失敗してもセッションの終了を妨げない。
set -u

ROOT="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || exit 0

INPUT="$(cat)"

# 第一の実装系。標準入力の JSON から記録のパスを読む。
printf '%s' "$INPUT" | "$PY" "$ROOT/tools/session_digest.py" --from-hook --root "$ROOT" >/dev/null 2>&1 || true

# 第二の実装系には登録の様式が判明していないため、ここで走査して補う。
"$PY" "$ROOT/tools/session_digest.py" --sweep-codex --root "$ROOT" >/dev/null 2>&1 || true

exit 0
