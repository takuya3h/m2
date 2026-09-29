"""常駐同期の抑止の目印が、版管理の除外と無関係に働くことの試験（完了判定 g）。

`.sync-pause.released`（解除のための退避先）が毎回未追跡として残っていたため
`.gitignore` の型を `.sync-pause*` に広げた。**git の追跡と、ファイルの実在の
検査は別である。** 実装が見るのは目印の実在だけなので、除外しても抑止は効く。
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync" / "m2-sync.sh"
MARKER = ".sync-pause"
RELEASED = ".sync-pause.released"


def _check_ignore(name: str) -> bool:
    result = subprocess.run(
        ["git", "check-ignore", "-q", name],
        cwd=REPO_ROOT, capture_output=True, text=True, check=False,
    )
    return result.returncode == 0


@pytest.mark.parametrize("name", [MARKER, RELEASED])
def test_pause_marker_and_its_released_form_are_ignored(name):
    assert _check_ignore(name), f"{name} が未追跡として残る"


def test_unrelated_name_is_not_ignored():
    """陽性対照。**常に真を返す壊れ方と区別する。**"""
    assert not _check_ignore(".sync-paus-control")


def test_pause_is_decided_by_file_existence_not_by_git():
    """抑止の判定が実在の検査であることを実装の行で示す。

    `[ -f "$M2DIR/.sync-pause" ]` はファイルの実在だけを見る。`git` にも
    追跡状態にも触れないため、`.gitignore` を広げても抑止は影響を受けない。
    """
    text = SYNC_SCRIPT.read_text(encoding="utf-8")
    assert '[ -f "$M2DIR/.sync-pause" ]' in text
    guard = next(line for line in text.splitlines() if '-f "$M2DIR/.sync-pause"' in line)
    assert "git" not in guard
