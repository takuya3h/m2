"""実験成果（層1=git 追跡ドキュメント）の自動 git 同期（機械層のみ）。

設計仕様 ``docs/superpowers/specs/2026-07-10-experiment-git-autosync-design.md``
§4.1 の厳密実装。実験完了時にその実験の **証跡ディレクトリだけ** を
provenance 付きで自動 commit + push（``exp/*`` ブランチ）する。push を検知した
CI が phase0 へのドラフト PR を起票し、**merge は人手**というゲートを残す。

制約（本モジュールの不変条件）:
    - **純 stdlib のみ**（third-party import 禁止）。フックは学習プロセスの
      interpreter で動くため、efros に ``.venv`` 無し・多 venv 環境でも確実に
      import できる必要がある。使用モジュールは ``subprocess`` / ``pathlib`` /
      ``re`` / ``os`` / ``dataclasses`` と、タイムスタンプ用の ``time``
      （いずれも標準ライブラリで venv 非依存）のみ。
    - **全 git 呼び出しは ``git -C <repo_root>``**。``train_t1b.py`` 等が
      ``os.chdir`` する副作用に耐えるため cwd を明示する。
    - **学習ループに例外を漏らさない**（fail-safe）。全経路で
      :class:`AutoSyncResult` を返し、失敗は ``~/claude-sync/sync-alerts.log``
      に追記（Syncthing で全台伝播）する。

使い方（ExperimentManager 非経由の ad-hoc スクリプトからの直呼び）::

    from egosurgery.utils.git_autosync import commit_and_push_evidence
    res = commit_and_push_evidence(exp_dir, meta={...}, extra_paths=["docs/experiment_log.md"])
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

# 秘密検出しきい値・上限。
_MAX_STAGED_BYTES = 5 * 1024 * 1024      # size-guard: staged 単一ファイル上限（>5MB で abort）
# content scan: size-guard 上限と**同値**。≤5MB のテキストは全て走査する。
# （1MB 等に下げると (1MB, 5MB] のテキストにライブ形式トークンが載った時、
#  content-scan をすり抜け size-guard も通過して public repo へ漏れる窓が開く。実機再現済み）
_MAX_CONTENT_SCAN_BYTES = _MAX_STAGED_BYTES
_DEFAULT_ALERT_LOG = "~/claude-sync/sync-alerts.log"

# content scan 正規表現（public repo ゆえ必須）。ラベルはアラート用（値自体は記録しない）。
_SECRET_CONTENT_PATTERNS = [
    ("github-token-classic", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("github-pat-fine-grained", re.compile(r"github_pat_[A-Za-z0-9_]{22,}")),
    ("private-key-block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws-access-key-id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("service-api-key", re.compile(r"(NOTION|WANDB|OPENAI|ANTHROPIC)_API_KEY\s*[=:]\s*\S")),
]


@dataclass
class AutoSyncResult:
    """自動同期の結果。

    Attributes:
        ok: 正常（``pushed`` / 意図的 skip / 意図的 commit-only）なら ``True``。
            abort / push 失敗 / 予期せぬ例外は ``False``。
        action: ``"pushed"`` | ``"skipped"`` | ``"committed_no_push"`` | ``"aborted"``。
        reason: 人間可読の理由（skip / abort / 失敗の説明）。
        branch: 現在のブランチ（判明していれば）。
        commit: 生成した commit hash（あれば）。
        staged: stage したファイル（repo 相対）の一覧。
    """

    ok: bool
    action: str
    reason: str
    branch: str | None
    commit: str | None
    staged: list[str]


def commit_and_push_evidence(
    exp_dir: str | Path,
    *,
    meta: dict | None = None,
    repo_root: str | Path | None = None,
    extra_paths: list[str] | None = None,
    push: bool = True,
    alert_log: str | Path | None = None,
) -> AutoSyncResult:
    """実験の証跡ディレクトリだけを provenance 付きで自動 commit + push する。

    ガード（いずれか偽なら ``action="skipped"`` で no-op・例外なし）:
        1. ``repo_root`` が git repo で、``exp_dir`` がその配下。
        2. 現ブランチが ``exp/*``（``phase0`` / ``master`` / detached では skip）。
        3. deploy key push が構成済み（repo-local ``remote.origin.pushurl`` /
           ``core.sshCommand``、または ``GIT_SSH_COMMAND`` 環境変数）。
        4. stage 差分が空でない。

    secret-scan（path denylist + content 正規表現）や size-guard（>5MB）に
    掛かった場合は ``action="aborted"`` で commit せず、アラートを追記する。

    Args:
        exp_dir: 証跡ディレクトリ。
        meta: provenance 用メタ（``category`` / ``step`` / ``description`` /
            ``seed`` / ``exp_id`` / ``metric_name`` / ``metric_value``）。
        repo_root: 省略時は ``exp_dir`` から ``git rev-parse --show-toplevel``。
        extra_paths: 追加 stage（repo 相対。例: ``["docs/experiment_log.md"]``）。
        push: ``False`` なら commit のみで push しない。
        alert_log: 失敗アラートの追記先。省略時 ``~/claude-sync/sync-alerts.log``。

    Returns:
        :class:`AutoSyncResult`。**いかなる例外も送出しない**。
    """
    try:
        return _commit_and_push_evidence_impl(
            exp_dir,
            meta=meta,
            repo_root=repo_root,
            extra_paths=extra_paths,
            push=push,
            alert_log=alert_log,
        )
    except Exception as exc:  # 予期せぬ失敗も学習ループに漏らさない。
        reason = f"unexpected error: {exc!r}"
        _write_alert(alert_log, f"git_autosync aborted: {reason} (exp_dir={exp_dir})")
        return AutoSyncResult(
            ok=False, action="aborted", reason=reason, branch=None, commit=None, staged=[]
        )


# --------------------------------------------------------------------------- #
# 実装本体
# --------------------------------------------------------------------------- #
def _commit_and_push_evidence_impl(
    exp_dir: str | Path,
    *,
    meta: dict | None,
    repo_root: str | Path | None,
    extra_paths: list[str] | None,
    push: bool,
    alert_log: str | Path | None,
) -> AutoSyncResult:
    meta = meta or {}

    if exp_dir is None:
        return _skipped("exp_dir is None")

    exp_path = Path(exp_dir).resolve()
    if not exp_path.exists():
        return _skipped(f"exp_dir does not exist: {exp_path}")

    # --- ガード 1: repo 内であること -------------------------------------- #
    if repo_root is None:
        rc, out, _ = _run_git(exp_path, ["rev-parse", "--show-toplevel"])
        if rc != 0 or not out.strip():
            return _skipped("exp_dir is not inside a git repository")
        root = Path(out.strip()).resolve()
    else:
        root = Path(repo_root).resolve()
        rc, out, _ = _run_git(root, ["rev-parse", "--show-toplevel"])
        if rc != 0 or not out.strip():
            return _skipped(f"repo_root is not a git repository: {root}")
        root = Path(out.strip()).resolve()

    try:
        exp_rel = exp_path.relative_to(root).as_posix()
    except ValueError:
        return _skipped("exp_dir is not under repo_root")
    if exp_rel in ("", "."):
        # exp_dir == repo_root。リポジトリ全体を stage するのは surgical 方針違反。
        return _skipped("exp_dir equals repo_root; refusing to stage entire repository")

    # --- ガード 2: exp/* ブランチであること ------------------------------ #
    rc, out, _ = _run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    branch = out.strip() if rc == 0 else ""
    if not branch or branch == "HEAD" or not branch.startswith("exp/"):
        return _skipped(f"current branch is not exp/* (branch={branch or 'detached'})")

    # --- ガード 3: deploy key push が構成済みであること ------------------- #
    if not _deploy_key_configured(root):
        return _skipped("deploy key push not configured (pushurl/core.sshCommand/GIT_SSH_COMMAND)")

    # --- stage: exp_dir 限定（add -A 禁止）------------------------------- #
    pathspecs = _build_pathspecs(root, exp_rel, extra_paths)
    rc, _out, err = _run_git(root, ["add", "--"] + pathspecs)
    if rc != 0:
        reason = f"git add failed: {_redact(err.strip())}"
        _write_alert(alert_log, f"git_autosync aborted: {reason} (exp_dir={exp_path})")
        return AutoSyncResult(
            ok=False, action="aborted", reason=reason, branch=branch, commit=None, staged=[]
        )

    staged = _staged_files(root, pathspecs)

    # --- ガード 4: stage 差分が空なら skip ------------------------------- #
    if not staged:
        return AutoSyncResult(
            ok=True, action="skipped", reason="nothing to commit", branch=branch,
            commit=None, staged=[],
        )

    # --- secret-scan（path denylist）------------------------------------- #
    for rel in staged:
        if _is_denylisted_path(rel):
            _unstage(root, pathspecs)
            reason = f"secret path denylisted: {rel}"
            _write_alert(alert_log, f"git_autosync aborted: {reason} (exp_dir={exp_path})")
            return AutoSyncResult(
                ok=False, action="aborted", reason=reason, branch=branch,
                commit=None, staged=staged,
            )

    # --- secret-scan（content 正規表現）--------------------------------- #
    for rel in staged:
        hit = _scan_file_content(root / rel)
        if hit is not None:
            _unstage(root, pathspecs)
            reason = f"secret content match ({hit}) in: {rel}"
            _write_alert(alert_log, f"git_autosync aborted: {reason} (exp_dir={exp_path})")
            return AutoSyncResult(
                ok=False, action="aborted", reason=reason, branch=branch,
                commit=None, staged=staged,
            )

    # --- size-guard（gitignore 漏れの安全網・>5MB で abort）------------- #
    for rel in staged:
        try:
            size = (root / rel).stat().st_size
        except OSError:
            continue
        if size > _MAX_STAGED_BYTES:
            _unstage(root, pathspecs)
            reason = f"staged file exceeds size limit (>5MB): {rel} ({size} bytes)"
            _write_alert(alert_log, f"git_autosync aborted: {reason} (exp_dir={exp_path})")
            return AutoSyncResult(
                ok=False, action="aborted", reason=reason, branch=branch,
                commit=None, staged=staged,
            )

    # --- commit（provenance・機械 trailer）------------------------------ #
    message = _build_commit_message(meta, exp_rel, _server_name())
    rc, _out, err = _run_git(root, ["commit", "-m", message, "--"] + pathspecs)
    if rc != 0:
        reason = f"git commit failed: {_redact(err.strip())}"
        _write_alert(alert_log, f"git_autosync aborted: {reason} (exp_dir={exp_path})")
        return AutoSyncResult(
            ok=False, action="aborted", reason=reason, branch=branch, commit=None, staged=staged
        )
    rc, out, _ = _run_git(root, ["rev-parse", "HEAD"])
    commit_hash = out.strip() if rc == 0 else None

    # --- push（非 fast-forward は force しない）-------------------------- #
    if not push:
        return AutoSyncResult(
            ok=True, action="committed_no_push", reason="push disabled by caller (commit only)",
            branch=branch, commit=commit_hash, staged=staged,
        )

    rc, _out, err = _run_git(root, ["push", "origin", f"HEAD:refs/heads/{branch}"])
    if rc == 0:
        return AutoSyncResult(
            ok=True, action="pushed", reason="pushed to exp/* branch",
            branch=branch, commit=commit_hash, staged=staged,
        )

    # push 失敗（非 ff 等）→ force せず人手へ。
    reason = f"push failed (not force-pushed): {_redact(err.strip())}"
    _write_alert(alert_log, f"git_autosync committed_no_push: {reason} (exp_dir={exp_path})")
    return AutoSyncResult(
        ok=False, action="committed_no_push", reason=reason,
        branch=branch, commit=commit_hash, staged=staged,
    )


# --------------------------------------------------------------------------- #
# ヘルパ
# --------------------------------------------------------------------------- #
def _run_git(repo_root: Path, args: list[str]) -> tuple[int, str, str]:
    """``git -C <repo_root> <args>`` を実行し ``(returncode, stdout, stderr)`` を返す。"""
    cmd = ["git", "-C", str(repo_root)] + list(args)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True)
        return proc.returncode, proc.stdout, proc.stderr
    except FileNotFoundError:
        return 127, "", "git executable not found"


def _skipped(reason: str) -> AutoSyncResult:
    """ガード不成立の no-op（正常）。アラートは出さない。"""
    return AutoSyncResult(
        ok=True, action="skipped", reason=reason, branch=None, commit=None, staged=[]
    )


def _deploy_key_configured(repo_root: Path) -> bool:
    """deploy key push が構成済みか（pushurl / core.sshCommand / GIT_SSH_COMMAND）。"""
    if (os.environ.get("GIT_SSH_COMMAND") or "").strip():
        return True
    for key in ("remote.origin.pushurl", "core.sshCommand"):
        rc, out, _ = _run_git(repo_root, ["config", "--local", "--get", key])
        if rc == 0 and out.strip():
            return True
    return False


def _build_pathspecs(
    repo_root: Path, exp_rel: str, extra_paths: list[str] | None
) -> list[str]:
    """stage 対象の repo 相対 pathspec を組む（exp_dir + 有効な extra_paths）。"""
    pathspecs = [exp_rel]
    for raw in extra_paths or []:
        try:
            candidate = Path(raw)
            full = candidate if candidate.is_absolute() else (repo_root / candidate)
            full = full.resolve()
            rel = full.relative_to(repo_root).as_posix()
        except (ValueError, OSError):
            continue
        if not rel or rel in (".",):
            continue
        if rel in pathspecs:
            continue
        if (repo_root / rel).exists():
            pathspecs.append(rel)
    return pathspecs


def _staged_files(repo_root: Path, pathspecs: list[str]) -> list[str]:
    """指定 pathspec に限定した staged ファイル（repo 相対）の一覧。"""
    rc, out, _ = _run_git(
        repo_root, ["diff", "--cached", "--name-only", "--"] + pathspecs
    )
    if rc != 0:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _unstage(repo_root: Path, pathspecs: list[str]) -> None:
    """abort 時に自 pathspec を index から外す（best-effort・失敗は無視）。"""
    _run_git(repo_root, ["reset", "-q", "--"] + pathspecs)


def _is_denylisted_path(rel_path: str) -> bool:
    """path denylist（.env 等の秘密ファイル）に該当するか。basename 判定。"""
    name = os.path.basename(rel_path)
    lower = name.lower()
    if name == ".env":
        return True
    if name.startswith(".env."):
        # .env.gpg / .env.example は除外、それ以外の .env.* は拒否。
        return name not in (".env.gpg", ".env.example")
    if lower.endswith(".key") or lower.endswith(".pem"):
        return True
    if lower.startswith("id_rsa") or lower.startswith("id_ed25519"):
        return True
    if "passphrase" in lower:
        return True
    return False


def _scan_file_content(path: Path) -> str | None:
    """テキストファイル（~1MB 以下）に秘密パターンがあればラベルを返す。

    値そのものは返さない（漏洩防止）。バイナリ・巨大ファイルは走査対象外。
    """
    try:
        size = path.stat().st_size
    except OSError:
        return None
    if size > _MAX_CONTENT_SCAN_BYTES:
        return None
    try:
        data = path.read_bytes()
    except OSError:
        return None
    text = data.decode("utf-8", errors="ignore")
    for label, pattern in _SECRET_CONTENT_PATTERNS:
        if pattern.search(text):
            return label
    return None


def _server_name() -> str:
    """Sync-Source 用のサーバー名（``$(hostname)`` 直用禁止）。"""
    try:
        from egosurgery.utils.server_name import resolve_server_name

        return resolve_server_name()
    except Exception:
        env = os.environ.get("SERVERNAME") or os.environ.get("EGOSURGERY_SERVER_NAME")
        return (env or "unknown").strip().lower()


def _format_metric_value(value) -> str:
    """metric 値を commit メッセージ用に整形する。"""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def _build_commit_message(meta: dict, exp_rel: str, server_name: str) -> str:
    """provenance commit メッセージを組む（機械 trailer・Claude trailer 無し）。"""
    fallback = Path(exp_rel).name
    step = str(meta.get("step") or "exp")
    description = str(meta.get("description") or fallback)
    seed = meta.get("seed")
    seed_token = f"seed{seed}" if seed is not None else "seedNA"

    metric_name = meta.get("metric_name")
    metric_value = meta.get("metric_value")
    if metric_name is not None and metric_value is not None:
        subject = (
            f"{step}({description}): {metric_name}="
            f"{_format_metric_value(metric_value)} {seed_token} [auto-sync]"
        )
    else:
        subject = f"{step}({description}): finalize {seed_token} [auto-sync]"

    category = str(meta.get("category") or "experiments")
    exp_id = str(meta.get("exp_id") or fallback)
    body = (
        "Auto-committed by egosurgery finalize hook.\n"
        f"Sync-Source: {server_name}\n"
        f"Experiment: {category}/{exp_id}"
    )
    return f"{subject}\n\n{body}"


def _redact(text: str) -> str:
    """アラート/reason に remote URL 内の資格情報（``https://user:token@...``）を残さない。

    通常は deploy key(ssh) 運用で URL にトークンは載らないが、万一 https+token の
    pushurl が構成された環境で push が失敗した場合に git stderr 経由で漏れるのを防ぐ。
    """
    return re.sub(r"(https?://)[^@\s/]+@", r"\1***@", text)


def _write_alert(alert_log: str | Path | None, message: str) -> None:
    """失敗アラートを追記する（Syncthing で全台伝播）。失敗しても送出しない。"""
    try:
        target = Path(alert_log) if alert_log else Path(os.path.expanduser(_DEFAULT_ALERT_LOG))
        target.parent.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] [{_server_name()}] {message}\n")
    except Exception:
        # アラート追記の失敗自体も学習ループに漏らさない。
        pass
