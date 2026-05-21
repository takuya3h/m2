"""git commit hash を取得・保存するユーティリティ。

各実験フォルダに ``git_commit.txt`` を残し、
「どのコード状態で出た結果か」を後から完全に再構成できるようにする。
"""

from __future__ import annotations

import subprocess
from pathlib import Path

NOT_A_GIT_REPO = "NOT_A_GIT_REPO"


def get_git_commit() -> str:
    """現在の HEAD の commit hash を返す。

    Returns:
        ``git rev-parse HEAD`` の出力。git リポジトリでない場合や
        git が利用できない場合は ``"NOT_A_GIT_REPO"``。
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return NOT_A_GIT_REPO


def save_git_commit(path: Path) -> None:
    """現在の commit hash をファイルに書き出す。

    Args:
        path: 書き出し先ファイルパス（例: ``{exp_dir}/git_commit.txt``）。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(get_git_commit() + "\n", encoding="utf-8")
