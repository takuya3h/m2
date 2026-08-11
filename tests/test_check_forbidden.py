"""禁止領域の検査（tools/check_forbidden.py）の検査。

Phase B Step 3 と Step 4 で実測した挙動を固定する。**双方向を測る。**
除外が効くことだけを測ると、除外しすぎていても気付けない。

実測の値（2026-08-11 lecun）:
    起点 HEAD~1 で changed=23 / excluded=4 / checked=19 / violations=0 / exit 0
    context/conventions.md へ 1 行足すと violations=1 / exit 1
    存在しない起点で errors=1 / exit 2
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import check_forbidden  # noqa: E402

GENERATED = [
    "context/auto/followups.md",
    "context/auto/results_recent.md",
    "context/auto/tasks_summary.csv",
    "tasks/inbox.md",
]


def _fake_git(diff: list[str], untracked: list[str] | None = None, *, base_ok: bool = True):
    """``check_forbidden._git`` の差し替え。git の履歴に依存させない。"""

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[0] == "rev-parse":
            return subprocess.CompletedProcess(
                args, 0 if base_ok else 128, "abc1234\n" if base_ok else "", ""
            )
        if args[0] == "diff":
            return subprocess.CompletedProcess(args, 0, "\n".join(diff) + "\n" if diff else "", "")
        if args[0] == "ls-files":
            joined = "\n".join(untracked or [])
            return subprocess.CompletedProcess(args, 0, joined + "\n" if joined else "", "")
        raise AssertionError(f"想定しない git の呼び出し: {args}")

    return run


def test_generated_locations_come_from_implementations():
    """除外の一覧は生成器の実装から取る。手で書いた一覧を持たない。"""
    directories, files = check_forbidden.generated_locations()
    assert directories == ("context/auto/",)
    assert files == ("tasks/inbox.md",)


def test_generated_paths_are_excluded(monkeypatch):
    """生成物だけの差分なら通る。**除外が実際に発火したことを件数で確かめる。**"""
    monkeypatch.setattr(check_forbidden, "_git", _fake_git(GENERATED))
    payload = check_forbidden.check("origin/phase0")
    assert payload["status"] == "pass"
    assert payload["excluded"] == 4
    assert payload["checked"] == 0
    assert sorted(payload["excluded_paths"]) == sorted(GENERATED)


def test_both_counts_are_reported(monkeypatch):
    """除外した件数と検査した件数の**両方**を出す。"""
    monkeypatch.setattr(check_forbidden, "_git", _fake_git([*GENERATED, "README.md", "Makefile"]))
    payload = check_forbidden.check("origin/phase0")
    assert payload["changed"] == 6
    assert payload["excluded"] == 4
    assert payload["checked"] == 2
    assert payload["violations"] == []


def test_violation_outside_generated_is_detected(monkeypatch):
    """生成物でない禁止領域への変更は検出する。除外しすぎていないことの対。"""
    monkeypatch.setattr(check_forbidden, "_git", _fake_git([*GENERATED, "context/conventions.md"]))
    payload = check_forbidden.check("origin/phase0")
    assert payload["status"] == "fail"
    assert [v["path"] for v in payload["violations"]] == ["context/conventions.md"]
    assert payload["excluded"] == 4


def test_forbidden_prefix_is_detected(monkeypatch):
    """証跡のある場所は接頭辞で検出する。"""
    monkeypatch.setattr(
        check_forbidden, "_git", _fake_git(["experiments/baselines/s0/metrics.json"])
    )
    payload = check_forbidden.check("origin/phase0")
    assert payload["status"] == "fail"
    assert payload["violations"][0]["reason"].startswith("禁止領域 experiments/")


def test_untracked_file_in_forbidden_area_is_detected(monkeypatch):
    """追跡外の新規ファイルも見る。差分だけを見ると新規追加を見落とす。"""
    monkeypatch.setattr(check_forbidden, "_git", _fake_git([], ["runindex/index.csv"]))
    payload = check_forbidden.check("origin/phase0")
    assert payload["status"] == "fail"
    assert payload["violations"][0]["path"] == "runindex/index.csv"


def test_main_returns_one_on_violation(monkeypatch):
    monkeypatch.setattr(check_forbidden, "_git", _fake_git(["context/conventions.md"]))
    assert check_forbidden.main([]) == 1


def test_main_returns_zero_when_only_generated(monkeypatch):
    monkeypatch.setattr(check_forbidden, "_git", _fake_git(GENERATED))
    assert check_forbidden.main([]) == 0


def test_unresolvable_base_fails(monkeypatch):
    """起点が誤っていて差分が取れない場合、**通さずに失敗させる。**"""
    monkeypatch.setattr(check_forbidden, "_git", _fake_git([], base_ok=False))
    assert check_forbidden.main(["--base", "does-not-exist-abcdef"]) == 2


def test_base_is_configurable(monkeypatch):
    seen = {}

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[0] == "rev-parse":
            seen["base"] = args[-1]
            return subprocess.CompletedProcess(args, 0, "abc1234\n", "")
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(check_forbidden, "_git", run)
    check_forbidden.check("HEAD~1")
    assert seen["base"] == "HEAD~1^{commit}"
