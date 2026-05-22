#!/usr/bin/env python3
"""PostToolUse フック: 編集された Python ファイルを ruff で軽量チェックする。

`src/egosurgery/` または `tests/` 配下の `.py` が Edit/Write された直後に走り、
ruff の指摘があれば additionalContext として返す（非ブロッキング・助言のみ）。
ruff が venv に無い場合や対象外ファイルの場合は静かに終了する。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    file_path = str(payload.get("tool_input", {}).get("file_path", ""))
    if not file_path.endswith(".py"):
        return
    if "src/egosurgery" not in file_path and "/tests/" not in file_path:
        return

    project_dir = Path(__file__).resolve().parents[2]
    ruff = project_dir / ".venv" / "bin" / "ruff"
    if not ruff.exists() or not Path(file_path).exists():
        return

    result = subprocess.run(
        [str(ruff), "check", "--quiet", file_path],
        capture_output=True,
        text=True,
    )
    findings = (result.stdout + result.stderr).strip()
    if not findings:
        return

    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"ruff の指摘（{Path(file_path).name}）— 必要に応じて修正:\n"
                        f"{findings}"
                    ),
                }
            }
        )
    )


if __name__ == "__main__":
    main()
