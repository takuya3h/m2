"""scripts/task_release.py が、外してよいときだけ同期の抑止を外すこと。

隔離した場（一時ディレクトリの bare な origin と複製）で実物の道具を走らせる。
`TASK_RELEASE_M2DIR` で `$M2DIR` を場へ向け、`TASK_RELEASE_GH` で `gh` を偽物に差し替える。
実物の `$M2DIR` の目印には触れない。

完了判定の対応: c 完了で外れる / d 前提の欠け / e 確かめられない / f 中止 / g 所有者 /
h 位置 / i 冪等 / j 削除の拒否 / k 副作用。

出所: T-2026-10-07-pause-release-tool-digest-relocate
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "scripts" / "task_release.py"
M2_SYNC = REPO_ROOT / "scripts" / "sync" / "m2-sync.sh"
TASK_ID = "T-2026-10-07-sample-release"
BRANCH = "feat/sample-release"

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git が要る")

FAKE_GH = """#!/bin/bash
case "${FAKE_GH_MODE:-open}" in
  open)   echo '[{"number":1,"state":"OPEN"}]' ;;
  merged) echo '[{"number":1,"state":"MERGED"}]' ;;
  closed) echo '[{"number":1,"state":"CLOSED"}]' ;;
  none)   echo '[]' ;;
  fail)   echo 'HTTP 502' >&2; exit 1 ;;
esac
"""


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def _commit(work: Path, message: str) -> None:
    _git(work, "add", "-A")
    _git(work, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message)


@pytest.fixture
def field(tmp_path: Path) -> dict:
    """完了の前提をすべて満たした場。目印はこの契約の所有。"""
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", "-b", "phase0", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(work))
    _git(work, "checkout", "-q", "-b", "phase0")
    (work / ".gitignore").write_text(".sync-pause*\n", encoding="utf-8")
    (work / "README.md").write_text("x\n", encoding="utf-8")
    _commit(work, "init")
    _git(work, "push", "-q", "origin", "phase0")
    _git(work, "checkout", "-q", "-b", BRANCH)
    task_dir = work / "tasks" / TASK_ID
    task_dir.mkdir(parents=True)
    (task_dir / "RESULT.md").write_text("# RESULT\n", encoding="utf-8")
    (task_dir / "result.yaml").write_text("status: pass\n", encoding="utf-8")
    _commit(work, "report")
    _git(work, "push", "-q", "-u", "origin", BRANCH)
    marker = work / ".sync-pause"
    marker.write_text(f"task_id={TASK_ID}\nbranch={BRANCH}\n", encoding="utf-8")
    gh = tmp_path / "gh"
    gh.write_text(FAKE_GH, encoding="utf-8")
    gh.chmod(0o755)
    return {"work": work, "marker": marker, "gh": gh, "origin": origin, "tmp": tmp_path}


def _release(f: dict, end: str = "complete", reason: str | None = None, *, task_id: str = TASK_ID,
             gh_mode: str = "open", m2dir: Path | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "TASK_RELEASE_M2DIR": str(m2dir or f["work"]), "TASK_RELEASE_GH": str(f["gh"]),
           "FAKE_GH_MODE": gh_mode}
    args = [sys.executable, str(TOOL), task_id, "--end", end]
    if reason is not None:
        args += ["--reason", reason]
    return subprocess.run(args, cwd=f["work"], env=env, capture_output=True, text=True)


def _status(proc: subprocess.CompletedProcess) -> str:
    lines = proc.stdout.strip().splitlines()
    assert len(lines) == 1, proc.stdout
    m = re.match(r"^task-release: (\S+) ", lines[0])
    assert m, lines[0]
    return m.group(1)


# --- c 完了で外れる / h 位置が一致する場 ------------------------------------------
def test_complete_releases_when_all_prerequisites_hold(field: dict) -> None:
    assert field["marker"].exists()
    proc = _release(field)
    assert (proc.returncode, _status(proc)) == (0, "RELEASED")
    assert "method=removed" in proc.stdout
    assert not os.path.lexists(field["marker"])


def test_complete_accepts_merged_pr(field: dict) -> None:
    proc = _release(field, gh_mode="merged")
    assert (proc.returncode, _status(proc)) == (0, "RELEASED")


# --- d 前提の欠け: 五通りで止まる前提がそれぞれ違う ---------------------------------
def _break_branch(f: dict) -> None:
    # 同じ commit の別の分岐へ移る。HEAD が変わらないので、ほかの前提は満たしたままになる。
    _git(f["work"], "checkout", "-q", "-b", "feat/another-task")


def _break_clean(f: dict) -> None:
    (f["work"] / "README.md").write_text("changed\n", encoding="utf-8")


def _break_pushed(f: dict) -> None:
    (f["work"] / "extra.txt").write_text("x\n", encoding="utf-8")
    _commit(f["work"], "not pushed")


def _break_report(f: dict) -> None:
    (f["work"] / "tasks" / TASK_ID / "RESULT.md").unlink()
    _commit(f["work"], "drop report")
    _git(f["work"], "push", "-q", "origin", BRANCH)


@pytest.mark.parametrize(
    ("breaker", "gh_mode", "named"),
    [
        (_break_branch, "open", "1 分岐"),
        (_break_clean, "open", "2 未 commit"),
        (_break_pushed, "open", "3 遠隔"),
        (None, "none", "4 PR"),
        (None, "closed", "4 PR"),
        (_break_report, "open", "5 報告"),
    ],
)
def test_each_missing_prerequisite_blocks_and_is_named(field: dict, breaker, gh_mode: str, named: str) -> None:
    if breaker:
        breaker(field)
    proc = _release(field, gh_mode=gh_mode)
    assert (proc.returncode, _status(proc)) == (30, "PREREQ_MISSING")
    names = set(re.findall(r"([1-5] [^（;]+)（", proc.stdout))
    assert names == {named}, proc.stdout
    assert field["marker"].exists()


def test_remote_branch_absent_is_missing(field: dict) -> None:
    _git(field["work"], "push", "-q", "origin", "--delete", BRANCH)
    proc = _release(field)
    assert (proc.returncode, _status(proc)) == (30, "PREREQ_MISSING")
    assert "遠隔に分岐が無い" in proc.stdout


# --- e 確かめられない: 欠けとは別の表示 ------------------------------------------
def test_pr_query_failure_is_unknown_not_missing(field: dict) -> None:
    proc = _release(field, gh_mode="fail")
    assert (proc.returncode, _status(proc)) == (31, "PREREQ_UNKNOWN")
    assert "確かめられない" in proc.stdout and "欠けている" not in proc.stdout
    assert field["marker"].exists()


def test_remote_query_failure_is_unknown(field: dict) -> None:
    _git(field["work"], "remote", "set-url", "origin", str(field["tmp"] / "no-such-origin.git"))
    proc = _release(field)
    assert (proc.returncode, _status(proc)) == (31, "PREREQ_UNKNOWN")
    assert "3 遠隔" in proc.stdout
    assert field["marker"].exists()


def test_missing_dominates_but_unknown_is_still_shown(field: dict) -> None:
    _break_branch(field)
    proc = _release(field, gh_mode="fail")
    assert (proc.returncode, _status(proc)) == (30, "PREREQ_MISSING")
    assert "確かめられない: 4 PR" in proc.stdout


# --- f 中止 -------------------------------------------------------------------
@pytest.mark.parametrize("reason", [None, "", "   "])
def test_abort_requires_reason(field: dict, reason: str | None) -> None:
    proc = _release(field, end="abort", reason=reason, gh_mode="none")
    assert (proc.returncode, _status(proc)) == (2, "USAGE")
    assert field["marker"].exists()


def test_abort_with_reason_releases_without_pr(field: dict) -> None:
    complete = _release(field, gh_mode="none")
    assert _status(complete) == "PREREQ_MISSING"
    proc = _release(field, end="abort", reason="契約を取り下げた", gh_mode="none")
    assert (proc.returncode, _status(proc)) == (0, "RELEASED")
    assert "end=abort" in proc.stdout and "契約を取り下げた" in proc.stdout
    assert not os.path.lexists(field["marker"])


# --- g 所有者 -----------------------------------------------------------------
@pytest.mark.parametrize("end,reason", [("complete", None), ("abort", "理由")])
@pytest.mark.parametrize(
    ("content", "status", "code"),
    [
        ("task_id=T-2026-01-01-other-task\nbranch=feat/other-task\n", "OWNER_MISMATCH", 20),
        ("", "OWNER_UNREADABLE", 21),
        ("hand placed\n", "OWNER_UNREADABLE", 21),
    ],
)
def test_foreign_or_unreadable_owner_is_kept(field: dict, end: str, reason, content: str, status: str, code: int) -> None:
    field["marker"].write_text(content, encoding="utf-8")
    before = hashlib.sha256(field["marker"].read_bytes()).hexdigest()
    proc = _release(field, end=end, reason=reason)
    assert (proc.returncode, _status(proc)) == (code, status)
    assert hashlib.sha256(field["marker"].read_bytes()).hexdigest() == before


# --- h 位置 -------------------------------------------------------------------
def test_position_mismatch_is_kept(field: dict) -> None:
    elsewhere = field["tmp"] / "elsewhere"
    elsewhere.mkdir()
    proc = _release(field, m2dir=elsewhere)
    assert (proc.returncode, _status(proc)) == (22, "POSITION_MISMATCH")
    assert field["marker"].exists()


# --- i 冪等 -------------------------------------------------------------------
def test_second_run_reports_absent(field: dict) -> None:
    first = _release(field)
    second = _release(field)
    assert (first.returncode, _status(first)) == (0, "RELEASED")
    assert (second.returncode, _status(second)) == (10, "ABSENT")


# --- j 削除の拒否 ---------------------------------------------------------------
def _load_tool():
    spec = importlib.util.spec_from_file_location("task_release", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules["task_release"] = module  # dataclass は定義先のモジュールを sys.modules から引く
    spec.loader.exec_module(module)
    return module


def test_denied_removal_moves_to_ignored_name(field: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _load_tool()

    def deny(path):
        raise PermissionError("removal denied")

    monkeypatch.setattr(tool.os, "remove", deny)
    monkeypatch.setenv("TASK_RELEASE_M2DIR", str(field["work"]))
    monkeypatch.setenv("TASK_RELEASE_GH", str(field["gh"]))
    monkeypatch.setenv("FAKE_GH_MODE", "open")
    outcome = tool.release(TASK_ID, "complete", None, field["work"])
    assert outcome.status == "RELEASED"
    assert outcome.extra["method"] == f"moved:.sync-pause.released.{TASK_ID}"
    assert not os.path.lexists(field["marker"])
    assert (field["work"] / f".sync-pause.released.{TASK_ID}").exists()
    assert _git(field["work"], "status", "--porcelain", "--untracked-files=all") == ""


def test_denied_removal_and_move_fails_loudly(field: dict, monkeypatch: pytest.MonkeyPatch) -> None:
    tool = _load_tool()

    def deny(*args):
        raise PermissionError("denied")

    monkeypatch.setattr(tool.os, "remove", deny)
    monkeypatch.setattr(tool.os, "replace", deny)
    monkeypatch.setenv("TASK_RELEASE_M2DIR", str(field["work"]))
    monkeypatch.setenv("TASK_RELEASE_GH", str(field["gh"]))
    outcome = tool.release(TASK_ID, "complete", None, field["work"])
    assert (outcome.status, outcome.code) == ("RELEASE_FAILED", 40)
    assert field["marker"].exists()


# --- k 副作用 -----------------------------------------------------------------
def _snapshot(work: Path) -> dict:
    refs = [r for r in _git(work, "for-each-ref", "--format=%(refname) %(objectname)").splitlines()
            if not r.startswith("refs/remotes/")]
    return {
        "HEAD": _git(work, "rev-parse", "HEAD"),
        "branch": _git(work, "branch", "--show-current"),
        "index": hashlib.sha256(_git(work, "ls-files", "-s").encode()).hexdigest(),
        "stash": _git(work, "stash", "list"),
        "refs": refs,
        "status": _git(work, "status", "--porcelain", "--untracked-files=all"),
    }


@pytest.mark.parametrize("gh_mode", ["open", "none"])
def test_tool_leaves_git_state_unchanged(field: dict, gh_mode: str) -> None:
    before = _snapshot(field["work"])
    _release(field, gh_mode=gh_mode)
    assert _snapshot(field["work"]) == before


def test_snapshot_detects_a_deliberate_change(field: dict) -> None:
    before = _snapshot(field["work"])
    _git(field["work"], "branch", "deliberate-change")
    assert _snapshot(field["work"]) != before


# --- 使い方 -------------------------------------------------------------------
@pytest.mark.parametrize(("task_id", "end"), [("", "complete"), ("bad-id", "complete"), (TASK_ID, ""), (TASK_ID, "done")])
def test_usage_errors(field: dict, task_id: str, end: str) -> None:
    proc = _release(field, end=end, task_id=task_id)
    assert (proc.returncode, _status(proc)) == (2, "USAGE")
    assert field["marker"].exists()


# --- R12: 差し替えを使わなければ m2-sync.sh と同じ位置に解決する --------------------
def _m2sync_resolution(home: Path) -> Path:
    """m2-sync.sh の M2DIR を決める行だけを取り出し、bash で評価する。"""
    lines = [ln for ln in M2_SYNC.read_text(encoding="utf-8").splitlines()
             if ln.startswith("M2DIR=") or ln.startswith("[ -d ~/slocal2 ] ||")]
    assert len(lines) == 2, lines
    script = "\n".join(lines) + '\nprintf %s "$M2DIR"\n'
    out = subprocess.run(["bash", "-c", script], env={**os.environ, "HOME": str(home)},
                         capture_output=True, text=True, check=True).stdout
    return Path(out)


@pytest.mark.parametrize("layout", [["slocal2"], ["slocal"], ["local/m2"], [], ["slocal2", "local/m2"], ["slocal", "local/m2"]])
def test_default_m2dir_matches_m2_sync(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, layout: list[str]) -> None:
    home = tmp_path / "home"
    home.mkdir()
    for d in layout:
        (home / d).mkdir(parents=True)
    tool = _load_tool()
    monkeypatch.delenv("TASK_RELEASE_M2DIR", raising=False)
    monkeypatch.setenv("HOME", str(home))
    assert tool._m2dir() == tool.resolve_m2dir(home) == _m2sync_resolution(home)
