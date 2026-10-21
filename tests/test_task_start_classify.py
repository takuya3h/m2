"""task_start.sh が作業ツリーの汚れを起点と比べて分類すること（SPEC §5.1）と、巻き戻しが実行前へ戻すこと。

隔離した場（一時ディレクトリの git repo）で実物のスクリプトを走らせる。作り方は
`tests/test_task_start_pause_owner.py` と同じで、取り込みの段（`make task-notion`）は Makefile ごと
差し替え、環境変数 `FAIL_NOTION` で失敗させる。**対照は各行に両方向で置く。**

場の形: 起点 `origin/phase0` は `p0/same.txt` と `p0/other.txt` を追跡する。作業の分岐 `orig` は
その一つ前の commit で、二つを追跡しない。手元に同じ経路のファイルを置いて分類を見る。

出所: T-2026-10-21-ops-taskstart-resume-folds-val（Task B、完了判定 b・c）
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
CLASSIFY = REPO_ROOT / "scripts" / "task_start_classify.py"
# 直す前の task-start（§3.2 の再現に使う）。直した commit より前の phase0 の版。
PRE_FIX_COMMIT = "3cb3db070eb0735b974933223e1fb8eb4dfb262b"
TASK_ID = "T-2026-10-21-sample-classify"
BRANCH = "feat/sample-classify"
SAME = "p0/same.txt"
OTHER = "p0/other.txt"
SAME_BODY = "phase0 の中身\n"

pytestmark = pytest.mark.skipif(shutil.which("git") is None or shutil.which("make") is None,
                                reason="git と make が要る")

GIT_ENV = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True,
                          env={**os.environ, **GIT_ENV})


@pytest.fixture
def sandbox(tmp_path: Path) -> Path:
    origin = tmp_path / "origin.git"
    work = tmp_path / "work"
    _git(tmp_path, "init", "-q", "--bare", "-b", "phase0", str(origin))
    _git(tmp_path, "clone", "-q", str(origin), str(work))
    _git(work, "checkout", "-q", "-b", "phase0")
    (work / "scripts").mkdir()
    shutil.copy2(SCRIPT, work / "scripts" / "task_start.sh")
    shutil.copy2(CLASSIFY, work / "scripts" / "task_start_classify.py")
    (work / "Makefile").write_text("task-notion:\n\t@test -z \"$$FAIL_NOTION\"\n", encoding="utf-8")
    (work / ".gitignore").write_text(".sync-pause*\n", encoding="utf-8")
    _git(work, "add", ".")
    _git(work, "commit", "-q", "-m", "init")
    _git(work, "branch", "orig")
    (work / "p0").mkdir()
    (work / SAME).write_text(SAME_BODY, encoding="utf-8")
    (work / OTHER).write_text("もう一つ\n", encoding="utf-8")
    _git(work, "add", "p0")
    _git(work, "commit", "-q", "-m", "phase0 adds p0")
    _git(work, "push", "-q", "origin", "phase0")
    _git(work, "checkout", "-q", "orig")
    assert not (work / "p0").exists()
    (work / "p0").mkdir()
    return work


def _run(work: Path, fail_notion: bool = False, script: str = "scripts/task_start.sh") -> subprocess.CompletedProcess:
    env = {**os.environ, "VIRTUAL_ENV": "/nonexistent-venv", "NOTION_API_KEY": "placeholder-not-a-key"}
    env.pop("FAIL_NOTION", None)
    if fail_notion:
        env["FAIL_NOTION"] = "1"
    return subprocess.run(["bash", script, TASK_ID], cwd=work, env=env, capture_output=True, text=True)


def _ignore(work: Path, *paths: str) -> None:
    with (work / ".git" / "info" / "exclude").open("a", encoding="utf-8") as f:
        f.writelines(f"/{p}\n" for p in paths)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _state(work: Path) -> dict:
    """作業ツリー・索引・除外の一覧・分岐・目印の要約値。**読み取りだけ**（write-tree を使わない）。"""
    files = {}
    for path in sorted(work.rglob("*")):
        rel = path.relative_to(work).as_posix()
        if rel == ".git" or rel.startswith(".git/") or not path.is_file():
            continue
        files[rel] = (_sha(path), path.stat().st_ino)
    marker = work / ".sync-pause"
    return {
        "branch": _git(work, "branch", "--show-current").stdout.strip(),
        "branches": _git(work, "branch", "--list").stdout,
        "index": hashlib.sha256(_git(work, "ls-files", "-s").stdout.encode()).hexdigest(),
        "exclude": _sha(work / ".git" / "info" / "exclude"),
        "marker": _sha(marker) if marker.exists() else None,
        "files": files,
    }


def _passed(proc: subprocess.CompletedProcess, work: Path) -> None:
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "[task-start] 分類: 通す" in proc.stdout
    assert _git(work, "branch", "--show-current").stdout.strip() == BRANCH


def _stopped(proc: subprocess.CompletedProcess, work: Path, before: dict, cls: str, path: str) -> None:
    assert proc.returncode == 3, proc.stdout + proc.stderr
    assert "[task-start] 分類: 止める" in proc.stdout
    assert f"止めた理由 [{cls}] {path}" in proc.stdout
    assert _state(work) == before  # 作業ツリー・索引・分岐・目印が前と同じ


# --- §5.1 の各行。陽性（止まる）と陰性（通る）を対で置く ----------------------

def test_row1_tracked_change_stops(sandbox: Path) -> None:
    (sandbox / "Makefile").write_text("changed\n", encoding="utf-8")
    before = _state(sandbox)
    proc = _run(sandbox)
    assert proc.returncode == 3
    assert "追跡下の変更: 1 件" in proc.stdout
    assert _state(sandbox) == before


def test_row1_control_clean_tree_passes(sandbox: Path) -> None:
    _passed(_run(sandbox), sandbox)


def test_row2_untracked_same_content_passes_unchanged(sandbox: Path) -> None:
    (sandbox / SAME).write_text(SAME_BODY, encoding="utf-8")
    before = _state(sandbox)["files"][SAME]
    proc = _run(sandbox)
    _passed(proc, sandbox)
    assert "未追跡・起点に在り中身が同じ: 1 件（通す）" in proc.stdout
    assert _state(sandbox)["files"][SAME] == before  # 中身も inode も同じ（書き直されていない）
    assert _git(sandbox, "status", "--porcelain").stdout == ""


def test_row3_untracked_one_char_different_stops(sandbox: Path) -> None:
    """row2 の陽性対照。一文字変えると止まる。"""
    (sandbox / SAME).write_text(SAME_BODY.replace("中身", "中味"), encoding="utf-8")
    before = _state(sandbox)
    _stopped(_run(sandbox), sandbox, before, "未追跡・起点に在り中身が違う", SAME)


def test_row4_untracked_absent_from_base_stops(sandbox: Path) -> None:
    (sandbox / "p0" / "new.txt").write_text("起点に無い\n", encoding="utf-8")
    before = _state(sandbox)
    proc = _run(sandbox)
    _stopped(proc, sandbox, before, "未追跡・起点に無い", "p0/new.txt")
    assert "無視の一覧（.git/info/exclude）に足せば" in proc.stdout


def test_row5_ignored_same_content_passes_unchanged(sandbox: Path) -> None:
    (sandbox / SAME).write_text(SAME_BODY, encoding="utf-8")
    _ignore(sandbox, SAME)
    before = _state(sandbox)
    proc = _run(sandbox)
    _passed(proc, sandbox)
    assert "無視・起点に在り中身が同じ: 1 件（通す）" in proc.stdout
    assert _state(sandbox)["files"][SAME] == before["files"][SAME]
    assert _state(sandbox)["exclude"] == before["exclude"]


def test_row6_ignored_different_content_stops(sandbox: Path) -> None:
    """row5 の陽性対照。**黙って上書きさせない。**"""
    (sandbox / SAME).write_text("手元で変えた中身\n", encoding="utf-8")
    _ignore(sandbox, SAME)
    before = _state(sandbox)
    _stopped(_run(sandbox), sandbox, before, "無視・起点に在り中身が違う", SAME)


def test_row7_ignored_absent_from_base_is_untouched(sandbox: Path) -> None:
    (sandbox / "p0" / "local.txt").write_text("起点に無い\n", encoding="utf-8")
    _ignore(sandbox, "p0/local.txt")
    before = _state(sandbox)["files"]["p0/local.txt"]
    proc = _run(sandbox)
    _passed(proc, sandbox)
    assert "無視・起点に無い: 数えない（触れない）" in proc.stdout
    assert _state(sandbox)["files"]["p0/local.txt"] == before


def test_row7_control_unignored_same_file_stops(sandbox: Path) -> None:
    """row7 の陽性対照。無視を外すと「未追跡・起点に無い」で止まる。"""
    (sandbox / "p0" / "local.txt").write_text("起点に無い\n", encoding="utf-8")
    before = _state(sandbox)
    _stopped(_run(sandbox), sandbox, before, "未追跡・起点に無い", "p0/local.txt")


def test_marker_classes_are_unchanged(sandbox: Path) -> None:
    """抑止の目印は無視されていて起点に無い。今と同じく触れない（実行前から在れば残す）。"""
    marker = sandbox / ".sync-pause"
    marker.write_text("hand-placed\n", encoding="utf-8")
    before = _sha(marker)
    proc = _run(sandbox)
    _passed(proc, sandbox)
    assert _sha(marker) == before
    assert "実行前から存在するため触れません" in proc.stdout


def test_classifier_alone_is_read_only_and_matches_task_start(sandbox: Path) -> None:
    """スキルが読む読み取りだけの分類が、task-start の分類と同じ行を出し、何も変えない。"""
    (sandbox / SAME).write_text(SAME_BODY, encoding="utf-8")
    (sandbox / OTHER).write_text("違う\n", encoding="utf-8")
    _ignore(sandbox, OTHER)
    _git(sandbox, "fetch", "-q", "origin")
    before = _state(sandbox)
    alone = subprocess.run(["python3", "scripts/task_start_classify.py"], cwd=sandbox,
                           capture_output=True, text=True)
    assert alone.returncode == 3
    assert _state(sandbox) == before
    proc = _run(sandbox)
    lines = alone.stdout.splitlines()
    assert lines and lines == [ln for ln in proc.stdout.splitlines() if ln in lines]


# --- 巻き戻し（完了判定 c） --------------------------------------------------

def _adoptable(work: Path) -> None:
    """未追跡・同じ と 無視・同じ を一件ずつ置く。"""
    (work / SAME).write_text(SAME_BODY, encoding="utf-8")
    (work / OTHER).write_text("もう一つ\n", encoding="utf-8")
    _ignore(work, OTHER)


def test_failed_import_after_adoption_restores_everything(sandbox: Path) -> None:
    _adoptable(sandbox)
    before = _state(sandbox)
    proc = _run(sandbox, fail_notion=True)
    assert proc.returncode == 4, proc.stdout + proc.stderr
    assert "実行前の状態へ戻しました" in proc.stderr
    assert _state(sandbox) == before  # 作業ツリー（中身と inode）・索引・除外・分岐・目印


def test_failed_checkout_after_adoption_restores_index(sandbox: Path) -> None:
    """載せた後に切り替えが拒まれても、索引と作業ツリーは前と同じ。

    skip-worktree の印つきで変更のあるファイルは status に出ず、切り替えで拒まれる（§3.2 の 3 行目）。
    """
    (sandbox / "Makefile").write_text("task-notion:\n\t@true\n# local\n", encoding="utf-8")
    _git(sandbox, "update-index", "--skip-worktree", "Makefile")
    # 起点の Makefile を変え、切り替えで書き直しが要るようにする
    clone = sandbox.parent / "other"
    _git(sandbox.parent, "clone", "-q", "-b", "phase0", str(sandbox.parent / "origin.git"), str(clone))
    (clone / "Makefile").write_text("task-notion:\n\t@true\n# upstream\n", encoding="utf-8")
    _git(clone, "commit", "-q", "-am", "upstream makefile")
    _git(clone, "push", "-q", "origin", "phase0")
    _adoptable(sandbox)
    before = _state(sandbox)
    proc = _run(sandbox)
    assert proc.returncode == 4, proc.stdout + proc.stderr
    assert "分岐を作成できませんでした" in proc.stderr
    assert _state(sandbox) == before


def test_rollback_without_unadopt_is_detected(sandbox: Path) -> None:
    """陽性対照。巻き戻しから「索引から外す」を除いた写しでは、試験が差を検出する。

    写しは作業ツリーの外に置く（中に置くと未追跡として分類で止まる）。
    """
    text = SCRIPT.read_text(encoding="utf-8")
    mutated = text.replace("        { unadopt \\\n", "        { true \\\n")
    assert mutated != text
    copy = sandbox.parent / "task_start_mutated.sh"
    copy.write_text(mutated, encoding="utf-8")
    _adoptable(sandbox)
    before = _state(sandbox)
    proc = _run(sandbox, fail_notion=True, script=str(copy))
    assert proc.returncode == 4
    assert _state(sandbox) != before


# --- §3.2 の再現。直す前の task-start と git そのもの -------------------------

def _pre_fix_script(work: Path) -> str:
    """直す前の版を作業ツリーの外に置く（中に置くと直す前の版自身が汚れとして止まる）。"""
    proc = subprocess.run(["git", "show", f"{PRE_FIX_COMMIT}:scripts/task_start.sh"], cwd=REPO_ROOT,
                          capture_output=True)
    if proc.returncode != 0:
        pytest.skip(f"直す前の版 {PRE_FIX_COMMIT[:8]} を読めない（浅い複製など）")
    copy = work.parent / "task_start_prefix.sh"
    copy.write_bytes(proc.stdout)
    return str(copy)


def test_git_refuses_unignored_untracked_in_the_way(sandbox: Path) -> None:
    """§3.2 の 1 行目。中身が同じでも拒む（§3.1）。違っても拒む。"""
    _git(sandbox, "fetch", "-q", "origin")
    for body in (SAME_BODY, "違う\n"):
        (sandbox / SAME).write_text(body, encoding="utf-8")
        proc = _git(sandbox, "checkout", "-q", "-b", "probe", "origin/phase0", check=False)
        assert proc.returncode != 0
        assert "would be overwritten" in proc.stderr


def test_pre_fix_task_start_silently_overwrites_ignored_file(sandbox: Path) -> None:
    """§3.2 の 2 行目を直す前の task-start で再現する。直した後は止まる（row6）。"""
    script = _pre_fix_script(sandbox)
    (sandbox / SAME).write_text("手元で変えた中身\n", encoding="utf-8")
    _ignore(sandbox, SAME)
    proc = _run(sandbox, script=script)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert (sandbox / SAME).read_text(encoding="utf-8") == SAME_BODY  # 黙って起点の版になった


def test_pre_fix_task_start_is_refused_on_skip_worktree_change(sandbox: Path) -> None:
    """§3.2 の 3 行目。status に出ない変更は切り替えで拒まれ、終了コード 4 で巻き戻る。"""
    script = _pre_fix_script(sandbox)
    clone = sandbox.parent / "other"
    _git(sandbox.parent, "clone", "-q", "-b", "phase0", str(sandbox.parent / "origin.git"), str(clone))
    (clone / "Makefile").write_text("task-notion:\n\t@true\n# upstream\n", encoding="utf-8")
    _git(clone, "commit", "-q", "-am", "upstream makefile")
    _git(clone, "push", "-q", "origin", "phase0")
    (sandbox / "Makefile").write_text("task-notion:\n\t@true\n# local\n", encoding="utf-8")
    _git(sandbox, "update-index", "--skip-worktree", "Makefile")
    before = _state(sandbox)
    proc = _run(sandbox, script=script)
    assert proc.returncode == 4, proc.stdout + proc.stderr
    assert _state(sandbox) == before
    # 直した後も同じ（§5.1 の外。挙動を変えない）
    proc = _run(sandbox)
    assert proc.returncode == 4
    assert _state(sandbox) == before


def test_pre_fix_task_start_stops_on_any_untracked(sandbox: Path) -> None:
    """直す前は、起点と同じ中身の未追跡でも汚れとして止まった（直した後は row2 で通る）。"""
    script = _pre_fix_script(sandbox)
    (sandbox / SAME).write_text(SAME_BODY, encoding="utf-8")
    proc = _run(sandbox, script=script)
    assert proc.returncode == 3
