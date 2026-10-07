"""task_start.sh が置く同期の抑止に所有の記録が入ることと、既存の振る舞いが変わらないこと。

隔離した場（一時ディレクトリの git repo）で実物のスクリプトを走らせる。取り込みの段
（`make task-notion`）は Makefile ごと差し替え、環境変数 `FAIL_NOTION` で失敗させる。
実物の `$M2DIR` の目印には触れない。

出所: T-2026-10-07-pause-release-tool-digest-relocate（R1、R2）
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "task_start.sh"
TASK_ID = "T-2026-10-07-sample-owner"
BRANCH = "feat/sample-owner"

pytestmark = pytest.mark.skipif(shutil.which("git") is None or shutil.which("make") is None,
                                reason="git と make が要る")


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    """phase0 だけを持つ偽の origin と、その複製（作業の場）を作る。"""
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", "-b", "phase0", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(work))
    _git(work, "checkout", "-q", "-b", "phase0")
    (work / "scripts").mkdir()
    shutil.copy2(SCRIPT, work / "scripts" / "task_start.sh")
    (work / "Makefile").write_text("task-notion:\n\t@test -z \"$$FAIL_NOTION\"\n", encoding="utf-8")
    (work / ".gitignore").write_text(".sync-pause*\n", encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
    _git(work, "push", "-q", "origin", "phase0")
    return work


def _run(work: Path, task_id: str = TASK_ID, fail_notion: bool = False) -> subprocess.CompletedProcess:
    env = {**os.environ, "VIRTUAL_ENV": "/nonexistent-venv", "NOTION_API_KEY": "placeholder-not-a-key"}
    env.pop("FAIL_NOTION", None)
    if fail_notion:
        env["FAIL_NOTION"] = "1"
    return subprocess.run(["bash", "scripts/task_start.sh", task_id], cwd=work, env=env,
                          capture_output=True, text=True)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_new_marker_records_owner(sandbox: Path) -> None:
    proc = _run(sandbox)
    assert proc.returncode == 0, proc.stderr
    marker = sandbox / ".sync-pause"
    assert marker.read_text(encoding="utf-8") == f"task_id={TASK_ID}\nbranch={BRANCH}\n"
    assert _git(sandbox, "branch", "--show-current").strip() == BRANCH


def test_existing_marker_is_left_untouched(sandbox: Path) -> None:
    marker = sandbox / ".sync-pause"
    marker.write_bytes(b"hand-placed\x00arbitrary content\n")
    before = _sha(marker)
    proc = _run(sandbox)
    assert proc.returncode == 0, proc.stderr
    assert _sha(marker) == before
    assert "実行前から存在するため触れません" in proc.stdout


def test_failed_import_removes_only_own_marker(sandbox: Path) -> None:
    proc = _run(sandbox, fail_notion=True)
    assert proc.returncode == 4
    assert not (sandbox / ".sync-pause").exists()
    assert _git(sandbox, "branch", "--show-current").strip() == "phase0"
    assert _git(sandbox, "branch", "--list", BRANCH).strip() == ""


def test_failed_import_keeps_existing_marker(sandbox: Path) -> None:
    marker = sandbox / ".sync-pause"
    marker.write_text("task_id=T-2026-01-01-other\nbranch=feat/other\n", encoding="utf-8")
    before = _sha(marker)
    proc = _run(sandbox, fail_notion=True)
    assert proc.returncode == 4
    assert _sha(marker) == before


@pytest.mark.parametrize(
    ("task_id", "setup", "code"),
    [
        ("", None, 2),
        ("not-a-task-id", None, 2),
        (TASK_ID, "dirty", 3),
        (TASK_ID, "branch_exists", 3),
    ],
)
def test_exit_codes_unchanged(sandbox: Path, task_id: str, setup: str | None, code: int) -> None:
    if setup == "dirty":
        (sandbox / "Makefile").write_text("changed\n", encoding="utf-8")
    elif setup == "branch_exists":
        _git(sandbox, "branch", BRANCH)
    proc = _run(sandbox, task_id=task_id)
    assert proc.returncode == code
    assert not (sandbox / ".sync-pause").exists()
