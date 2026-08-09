from __future__ import annotations

import os
import subprocess
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "sync" / "new_experiment_branch.sh"


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["HOME"] = str(tmp_path)
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_accepts_lowercase_host_name(tmp_path: Path) -> None:
    result = _run(tmp_path, "--dry-run", "bengio")
    assert result.returncode == 0, result.stderr
    assert "exp/bengio" in result.stdout


def test_rejects_uppercase(tmp_path: Path) -> None:
    result = _run(tmp_path, "--dry-run", "Bengio")
    assert result.returncode != 0
    assert "小文字英数" in result.stderr


def test_rejects_name_with_date(tmp_path: Path) -> None:
    result = _run(tmp_path, "--dry-run", "bengio-wip-20260703")
    assert result.returncode != 0
    assert "日付" in result.stderr or "作業状態" in result.stderr


def test_rejects_too_short(tmp_path: Path) -> None:
    result = _run(tmp_path, "--dry-run", "a")
    assert result.returncode != 0
    assert "2文字以上" in result.stderr


def test_generated_name_keeps_prefix(tmp_path: Path) -> None:
    result = _run(tmp_path, "--dry-run", "lecun")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().endswith("exp/lecun")
