"""``egosurgery.utils.git_autosync`` の受け入れテスト（設計仕様 §4.1 / §7）。

対象: ``src/egosurgery/utils/git_autosync.py`` の
``commit_and_push_evidence()`` と ``AutoSyncResult``。

一時 git repo（``tmp_path``）+ bare remote を用いて、設計仕様 §7 のテスト戦略
(a)〜(h) を検証する:

    (a) exp/* 外ブランチ    → action="skipped"（正史を汚さない）
    (b) ``.env`` 混入        → action="aborted"（path denylist）
    (c) 内容に ghp_ トークン → action="aborted"（content secret-scan）
    (d) exp_dir 外の変更     → stage しない（``add -A`` 禁止）
    (e) commit メッセージ    → provenance 形式（機械 trailer・Claude trailer 無し）
    (f) bare remote へ push  → action="pushed"
    (g) 差分なし             → action="skipped"（nothing to commit）
    (h) > 5 MB ファイル      → action="aborted"（size-guard）

純 stdlib + pytest のみ（設計仕様: 追加依存禁止）。git 環境変数
（``GIT_AUTHOR_*`` / ``GIT_COMMITTER_*``）と repo-local ``user.email`` /
``user.name`` を設定し commit を決定論化する。全 git 呼び出しは
``git -C <repo>`` で cwd 非依存にする。
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from egosurgery.utils.git_autosync import AutoSyncResult, commit_and_push_evidence

# --------------------------------------------------------------------------- #
# 定数
# --------------------------------------------------------------------------- #
EXP_BRANCH = "exp/efros-test-theme"
SERVER = "efros-test"

# commit_and_push_evidence に渡す meta（設計仕様 §4.1 の provenance 用キー）。
META = {
    "category": "transfer",
    "step": "t1b",
    "description": "clsbias-test",
    "seed": 42,
    "exp_id": "t1b_test_001",
    "metric_name": "mAP",
    "metric_value": 0.5,
}


# --------------------------------------------------------------------------- #
# git helper（subprocess で init/config。全て ``git -C <repo>``）
# --------------------------------------------------------------------------- #
def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    """``git -C <repo> <args>`` を実行して CompletedProcess を返す。"""
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise AssertionError(
            f"git -C {repo} {' '.join(args)} failed ({proc.returncode}): {proc.stderr}"
        )
    return proc


def _head(repo: Path) -> str:
    """現在の HEAD commit hash。"""
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _files_in_head(repo: Path) -> list[str]:
    """HEAD コミットが変更したファイル一覧（repo 相対）。"""
    out = _git(repo, "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD").stdout
    return [line for line in out.splitlines() if line]


def _bare_has_ref(bare: Path, branch: str) -> bool:
    """bare remote が ``refs/heads/<branch>`` を持つか。"""
    proc = _git(bare, "rev-parse", f"refs/heads/{branch}", check=False)
    return proc.returncode == 0


def _init_repo(tmp_path: Path, *, commit_exp: bool = False) -> tuple[Path, Path, Path]:
    """作業 repo + bare remote + 証跡 exp_dir を構築して返す。

    - ``exp/*`` ブランチ（``EXP_BRANCH``）を現在ブランチにする。
    - deploy-key シグナル（repo-local ``core.sshCommand``）を構成（guard #3 を満たす）。
    - origin は bare remote へのローカルパス（実 push が SSH 無しで成立する）。
    - ``commit_exp=True`` のとき exp_dir を先にコミット（差分なしケース用）。

    Returns:
        ``(repo, bare, exp_dir)``。
    """
    bare = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", str(bare)], check=True, capture_output=True)

    repo = tmp_path / "work"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "autosync@test.local")
    _git(repo, "config", "user.name", "autosync-test")
    # guard #3: repo-local core.sshCommand を deploy-key push 構成のシグナルとして置く。
    # origin はローカルパスなので実 push で ssh は呼ばれない（このコマンドは未使用）。
    _git(
        repo,
        "config",
        "core.sshCommand",
        "ssh -i /home/ubuntu/.ssh/id_m2deploy -o IdentitiesOnly=yes",
    )
    _git(repo, "remote", "add", "origin", str(bare))

    # 初期コミット（exp_dir 外の tracked ファイル。(d) の add -A 検出に使う）。
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-qm", "init")
    # phase0（exp 外の幹）を経由してから exp/* ブランチへ。
    _git(repo, "checkout", "-q", "-b", "phase0")
    _git(repo, "checkout", "-q", "-b", EXP_BRANCH)

    exp_dir = repo / "experiments" / "transfer" / "t1b_test_001"
    exp_dir.mkdir(parents=True)
    (exp_dir / "metrics.json").write_text(json.dumps({"mAP": 0.5}), encoding="utf-8")
    (exp_dir / "config.yaml").write_text("model: test\n", encoding="utf-8")
    (exp_dir / "notes.md").write_text("# notes\n", encoding="utf-8")

    if commit_exp:
        _git(repo, "add", "--", "experiments/transfer/t1b_test_001")
        _git(repo, "commit", "-qm", "seed exp evidence")

    return repo, bare, exp_dir


@pytest.fixture(autouse=True)
def _deterministic_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """commit を決定論化し、テストをホスト状態から隔離する。

    - ``GIT_AUTHOR_*`` / ``GIT_COMMITTER_*``: 著者・日付を固定（module の git
      subprocess は os.environ を継承するのでここで設定する）。
    - ``SERVERNAME``: provenance の ``Sync-Source`` を決定論化
      （``resolve_server_name`` が最優先で参照）。
    - 継承しうる ``GIT_DIR`` / ``GIT_WORK_TREE`` を除去して tmp repo を汚さない。
    """
    monkeypatch.setenv("GIT_AUTHOR_NAME", "autosync-test")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "autosync@test.local")
    monkeypatch.setenv("GIT_AUTHOR_DATE", "2026-07-10T00:00:00 +0000")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "autosync-test")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "autosync@test.local")
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-07-10T00:00:00 +0000")
    monkeypatch.setenv("SERVERNAME", SERVER)
    monkeypatch.delenv("EGOSURGERY_SERVER_NAME", raising=False)
    monkeypatch.delenv("GIT_DIR", raising=False)
    monkeypatch.delenv("GIT_WORK_TREE", raising=False)
    # host が GIT_SSH_COMMAND を export していると guard #3 が env 経由で常時成立して
    # しまい退行を隠す。全テストで隔離し、guard #3 の判定を repo-local 構成に限定する。
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)


# --------------------------------------------------------------------------- #
# (a) exp/* 外ブランチ → skipped
# --------------------------------------------------------------------------- #
def test_non_exp_branch_is_skipped(tmp_path: Path) -> None:
    """phase0（exp/* 以外）では正史を汚さないよう no-op（skipped）."""
    repo, bare, exp_dir = _init_repo(tmp_path)
    _git(repo, "checkout", "-q", "phase0")  # 現在ブランチを exp/* 外へ
    head_before = _head(repo)

    res = commit_and_push_evidence(
        exp_dir,
        meta=META,
        repo_root=repo,
        alert_log=tmp_path / "sync-alerts.log",
    )

    assert res.action == "skipped"
    assert res.commit is None
    assert res.staged == []
    assert _head(repo) == head_before  # 新規 commit 無し
    assert not _bare_has_ref(bare, "phase0")  # push もされない


# --------------------------------------------------------------------------- #
# (b) .env 混入 → aborted（path denylist）
# --------------------------------------------------------------------------- #
def test_dotenv_in_evidence_aborts(tmp_path: Path) -> None:
    """exp_dir に ``.env`` があれば path denylist で abort（commit/push しない）."""
    repo, bare, exp_dir = _init_repo(tmp_path)
    (exp_dir / ".env").write_text("SOME_SETTING=1\n", encoding="utf-8")
    head_before = _head(repo)
    alert = tmp_path / "sync-alerts.log"

    res = commit_and_push_evidence(
        exp_dir, meta=META, repo_root=repo, alert_log=alert
    )

    assert res.action == "aborted"
    assert res.ok is False
    assert res.commit is None
    assert _head(repo) == head_before
    assert not _bare_has_ref(bare, EXP_BRANCH)
    # 失敗はアラートログに追記される（設計仕様 §4.1 / §6）。
    assert alert.exists() and alert.read_text(encoding="utf-8").strip() != ""


# --------------------------------------------------------------------------- #
# (c) 内容に ghp_ トークン → aborted（content secret-scan）
# --------------------------------------------------------------------------- #
def test_content_secret_ghp_token_aborts(tmp_path: Path) -> None:
    """テキスト内容に ``ghp_`` + 36 桁が現れると content-scan で abort.

    リテラルを連結で組み立て、テストソース自体を secret スキャナに
    引っかけない（マッチするのはディスク書き込み後の連続文字列のみ）。
    """
    repo, bare, exp_dir = _init_repo(tmp_path)
    token = "ghp_" + "A" * 36  # `ghp_[A-Za-z0-9]{36}` にマッチ
    (exp_dir / "leak.txt").write_text(f"token = {token}\n", encoding="utf-8")
    head_before = _head(repo)
    alert = tmp_path / "sync-alerts.log"

    res = commit_and_push_evidence(
        exp_dir, meta=META, repo_root=repo, alert_log=alert
    )

    assert res.action == "aborted"
    assert res.ok is False
    assert res.commit is None
    assert _head(repo) == head_before
    assert not _bare_has_ref(bare, EXP_BRANCH)
    assert alert.exists() and alert.read_text(encoding="utf-8").strip() != ""


# --------------------------------------------------------------------------- #
# (d) exp_dir 外の変更を stage しない（add -A 禁止）
# --------------------------------------------------------------------------- #
def test_does_not_stage_outside_exp_dir(tmp_path: Path) -> None:
    """exp_dir 外の tracked 変更・untracked ファイルを巻き込まない."""
    repo, _bare, exp_dir = _init_repo(tmp_path)
    # exp_dir 外の tracked ファイルを変更（add -A なら混入するはず）。
    (repo / "README.md").write_text("# test repo (locally modified)\n", encoding="utf-8")
    # exp_dir 外の untracked ファイルを作成。
    (repo / "OUTSIDE.txt").write_text("must not be committed\n", encoding="utf-8")

    res = commit_and_push_evidence(
        exp_dir,
        meta=META,
        repo_root=repo,
        push=False,  # stage 検証のみ（push 機構から分離）
        alert_log=tmp_path / "sync-alerts.log",
    )

    assert res.commit is not None
    # staged は exp_dir 配下のみ。外部ファイルは含まれない。
    assert res.staged, "exp_dir 配下のファイルが stage されるはず"
    assert all(
        p.startswith("experiments/transfer/t1b_test_001/") for p in res.staged
    ), f"exp_dir 外が stage された: {res.staged}"
    assert "README.md" not in res.staged
    assert "OUTSIDE.txt" not in res.staged

    # コミット内容も exp_dir 配下のみ。
    committed = _files_in_head(repo)
    assert committed and all(
        p.startswith("experiments/transfer/t1b_test_001/") for p in committed
    ), f"コミットに exp_dir 外が混入: {committed}"

    # 外部の変更は working tree に残る（コミットも stage もされていない）。
    # porcelain: " M" = worktree 変更・未 stage / "?? " = untracked。
    status = _git(repo, "status", "--porcelain").stdout
    assert " M README.md" in status  # 変更はあるが未 stage のまま
    assert "?? OUTSIDE.txt" in status


# --------------------------------------------------------------------------- #
# (e) commit メッセージが provenance 形式
# --------------------------------------------------------------------------- #
def test_commit_message_provenance_format(tmp_path: Path) -> None:
    """subject と機械 trailer が設計仕様 §4.1 の provenance 形式に一致する."""
    repo, _bare, exp_dir = _init_repo(tmp_path)

    res = commit_and_push_evidence(
        exp_dir,
        meta=META,
        repo_root=repo,
        push=False,
        alert_log=tmp_path / "sync-alerts.log",
    )
    assert res.commit is not None

    msg = _git(repo, "log", "-1", "--format=%B").stdout
    subject = msg.splitlines()[0]

    # subject: "{step}({description}): {metric_name}={metric_value} seed{seed} [auto-sync]"
    assert subject.startswith("t1b(clsbias-test):")
    assert "mAP=0.5" in subject
    assert "seed42" in subject
    assert "[auto-sync]" in subject

    # 機械 trailer（設計仕様 §4.1）。
    assert "Auto-committed by egosurgery finalize hook." in msg
    assert f"Sync-Source: {SERVER}" in msg
    assert "Experiment: transfer/t1b_test_001" in msg

    # 自動 commit は対話由来でない → Claude trailer は付けない。
    assert "Co-Authored-By" not in msg
    assert "Claude-Session" not in msg


def test_commit_message_without_metric(tmp_path: Path) -> None:
    """metric 欠落時は "{step}({description}): finalize seed{seed} [auto-sync]"."""
    repo, _bare, exp_dir = _init_repo(tmp_path)
    meta_no_metric = {
        "category": "transfer",
        "step": "t1b",
        "description": "clsbias-test",
        "seed": 42,
        "exp_id": "t1b_test_001",
    }

    res = commit_and_push_evidence(
        exp_dir,
        meta=meta_no_metric,
        repo_root=repo,
        push=False,
        alert_log=tmp_path / "sync-alerts.log",
    )
    assert res.commit is not None

    subject = _git(repo, "log", "-1", "--format=%B").stdout.splitlines()[0]
    assert subject.startswith("t1b(clsbias-test):")
    assert "finalize" in subject
    assert "seed42" in subject
    assert "[auto-sync]" in subject


# --------------------------------------------------------------------------- #
# (f) bare remote へ push 成功
# --------------------------------------------------------------------------- #
def test_push_to_bare_remote_succeeds(tmp_path: Path) -> None:
    """exp/* ブランチが bare remote へ push され action="pushed"."""
    repo, bare, exp_dir = _init_repo(tmp_path)

    res = commit_and_push_evidence(
        exp_dir,
        meta=META,
        repo_root=repo,
        push=True,
        alert_log=tmp_path / "sync-alerts.log",
    )

    assert isinstance(res, AutoSyncResult)
    assert res.action == "pushed"
    assert res.ok is True
    assert res.commit is not None
    assert res.branch == EXP_BRANCH

    # bare remote に同一 commit の exp/* ref が出来ている。
    assert _bare_has_ref(bare, EXP_BRANCH)
    remote_sha = _git(bare, "rev-parse", f"refs/heads/{EXP_BRANCH}").stdout.strip()
    assert remote_sha == _head(repo) == res.commit


# --------------------------------------------------------------------------- #
# (g) 差分なし → skipped
# --------------------------------------------------------------------------- #
def test_no_diff_is_skipped(tmp_path: Path) -> None:
    """exp_dir が既にコミット済みで差分ゼロなら no-op（skipped）."""
    repo, bare, exp_dir = _init_repo(tmp_path, commit_exp=True)
    head_before = _head(repo)

    res = commit_and_push_evidence(
        exp_dir,
        meta=META,
        repo_root=repo,
        alert_log=tmp_path / "sync-alerts.log",
    )

    assert res.action == "skipped"
    assert res.commit is None
    assert res.staged == []
    assert _head(repo) == head_before
    assert not _bare_has_ref(bare, EXP_BRANCH)


# --------------------------------------------------------------------------- #
# (h) > 5 MB ファイル → aborted（size-guard）
# --------------------------------------------------------------------------- #
def test_oversized_file_aborts(tmp_path: Path) -> None:
    """staged に > 5 MB のファイルがあれば size-guard で abort."""
    repo, bare, exp_dir = _init_repo(tmp_path)
    (exp_dir / "big.bin").write_bytes(b"\0" * (6 * 1024 * 1024))  # 6 MB
    head_before = _head(repo)
    alert = tmp_path / "sync-alerts.log"

    res = commit_and_push_evidence(
        exp_dir, meta=META, repo_root=repo, alert_log=alert
    )

    assert res.action == "aborted"
    assert res.ok is False
    assert res.commit is None
    assert _head(repo) == head_before
    assert not _bare_has_ref(bare, EXP_BRANCH)
    assert alert.exists() and alert.read_text(encoding="utf-8").strip() != ""


# --------------------------------------------------------------------------- #
# ガード#3 の負テスト: deploy key 未構成 → skipped（push しない）
# --------------------------------------------------------------------------- #
def test_deploy_key_not_configured_is_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """deploy key（``core.sshCommand`` / ``pushurl`` / ``GIT_SSH_COMMAND``）未構成なら no-op。

    「サーバーに push cred を過剰配置させない」安全モデルの根幹。構成が無い間は
    commit も push もしない（skipped）。このガードが退行すると未構成ホストで
    勝手に push しうるため、負テストで固定する。
    """
    repo, bare, exp_dir = _init_repo(tmp_path)
    _git(repo, "config", "--unset", "core.sshCommand")  # guard #3 のシグナルを外す
    monkeypatch.delenv("GIT_SSH_COMMAND", raising=False)
    head_before = _head(repo)

    res = commit_and_push_evidence(
        exp_dir, meta=META, repo_root=repo, alert_log=tmp_path / "sync-alerts.log"
    )

    assert res.action == "skipped"
    assert res.commit is None
    assert _head(repo) == head_before
    assert not _bare_has_ref(bare, EXP_BRANCH)


# --------------------------------------------------------------------------- #
# 回帰: content-scan 上限 == size-guard 上限。(1MB, 5MB] のテキスト内トークンも abort
# --------------------------------------------------------------------------- #
def test_content_secret_in_multi_mb_file_aborts(tmp_path: Path) -> None:
    """~2MB のテキスト（旧バイパス窓）に ``ghp_`` トークンが載っても abort。

    content-scan 上限を 1MB に絞ると (1MB, 5MB] のテキストがトークンを載せた時に
    content-scan をすり抜け size-guard も通過し public repo へ漏れる窓が開く
    （敵対的レビューで実機再現済み）。上限を size-guard と同値にした修正の回帰。
    """
    repo, bare, exp_dir = _init_repo(tmp_path)
    token = "ghp_" + "B" * 36  # `ghp_[A-Za-z0-9]{36}` にマッチ
    padding = "x" * (2 * 1024 * 1024)  # ~2 MB（1MB 超・5MB 以下＝旧バイパス窓）
    (exp_dir / "trace.log").write_text(
        f"{padding}\ntoken = {token}\n", encoding="utf-8"
    )
    head_before = _head(repo)
    alert = tmp_path / "sync-alerts.log"

    res = commit_and_push_evidence(
        exp_dir, meta=META, repo_root=repo, alert_log=alert
    )

    assert res.action == "aborted"
    assert res.ok is False
    assert res.commit is None
    assert _head(repo) == head_before
    assert not _bare_has_ref(bare, EXP_BRANCH)
    assert alert.exists() and alert.read_text(encoding="utf-8").strip() != ""
