#!/usr/bin/env python3
"""task_release.py — 契約の終わりに同期の抑止（`.sync-pause`）を外す。

    make task-release TASK=T-YYYY-MM-DD-slug END=complete
    make task-release TASK=T-YYYY-MM-DD-slug END=abort REASON="中止の理由"
    # または  python scripts/task_release.py T-YYYY-MM-DD-slug --end complete

`scripts/task_start.sh` が置いた目印（中身は所有の記録 `task_id=...`）を、**その契約が
終わったときだけ**外す。外し忘れるとそのホストだけ自動同期が止まったままになり、
早く外しすぎると契約の実行中に `m2-sync.sh` が作業分岐へ統合と push を行う。

終わり方は二つ。

- `complete`: 完了。次の前提を**すべて**満たすときだけ外す
    1. 現在の分岐がこの契約の分岐（`feat/<slug>`）である
    2. 追跡下に未 commit の変更が無い
    3. 遠隔に分岐が在り、その先頭が HEAD と一致する
    4. phase0 向けの PR が在る（開いているか、統合済み）
    5. `tasks/<task_id>/RESULT.md` と `result.yaml` が HEAD に含まれる
- `abort`: 中止。理由（`--reason`）を必須とし、前提 1〜5 は見ない

どちらの終わり方でも、目印の所有者がこの契約であることと、目印の位置が `m2-sync.sh` の
読む `$M2DIR` 直下であることを先に確かめる。**人が手で置いた目印（中身なし）は外さない。**

前提が**欠けている**ことと、照会の失敗などで**確かめられない**ことは区別して表示する。
どちらでも外さない。

外し方は削除を優先し、削除が拒まれたら無視される名前（`.sync-pause.released.<task_id>`）
へ移す。外した後に目印が存在しないことを確かめて終える。

この道具は commit、push、統合、stash、分岐の切り替え、目印以外の削除を行わない。
遠隔は `git ls-remote` と `gh pr list` で参照するだけで、参照（refs）を書き換えない。

結果は終了コードと一行の状態表示（`task-release: <状態> ...`）で返す。`make` 経由では
失敗が make 自身の終了コード（2）に潰れるため、**状態表示を見ること。**

| 終了コード | 状態 | 意味 |
|---:|---|---|
| 0 | `RELEASED` | 外した（`method=removed` か `method=moved:<名前>`） |
| 10 | `ABSENT` | 目印が元から無い。何もしていない（失敗ではない） |
| 2 | `USAGE` | 使い方の誤り（識別子の形式、終わり方、中止の理由が無い） |
| 20 | `OWNER_MISMATCH` | 目印の所有者が別の契約 |
| 21 | `OWNER_UNREADABLE` | 目印の所有者を読めない（中身が無い・形式が違う） |
| 22 | `POSITION_MISMATCH` | repo の最上位が `m2-sync.sh` の読む `$M2DIR` と違う |
| 30 | `PREREQ_MISSING` | 完了の前提が欠けている（欠けた前提を名指しする） |
| 31 | `PREREQ_UNKNOWN` | 完了の前提を確かめられない（照会の失敗） |
| 40 | `RELEASE_FAILED` | 削除も移動もできなかった、または外した後も目印が在る |

試験のために `TASK_RELEASE_M2DIR`（`$M2DIR` の差し替え）と `TASK_RELEASE_GH`（`gh` の差し替え）を読む。
**設定しなければ `m2-sync.sh` と同じ位置に解決し、PATH の `gh` を使う。**

出所: T-2026-10-07-pause-release-tool-digest-relocate
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

MARKER_NAME = ".sync-pause"
TASK_ID_RE = re.compile(r"^T-[0-9]{4}-[0-9]{2}-[0-9]{2}-([a-z0-9-]{3,60})$")  # task_start.sh と同じ
BASE_BRANCH = "phase0"

EXIT = {
    "RELEASED": 0,
    "USAGE": 2,
    "ABSENT": 10,
    "OWNER_MISMATCH": 20,
    "OWNER_UNREADABLE": 21,
    "POSITION_MISMATCH": 22,
    "PREREQ_MISSING": 30,
    "PREREQ_UNKNOWN": 31,
    "RELEASE_FAILED": 40,
}


class Unknown(Exception):
    """前提を確かめられなかった（照会の失敗）。欠けていることとは区別する。"""


@dataclass
class Outcome:
    status: str
    detail: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    @property
    def code(self) -> int:
        return EXIT[self.status]

    def line(self, task_id: str) -> str:
        parts = [f"task-release: {self.status}", f"task={task_id or '-'}"]
        parts += [f"{k}={v}" for k, v in self.extra.items()]
        if self.detail:
            parts.append(f"— {self.detail}")
        return " ".join(parts)


def resolve_m2dir(home: Path) -> Path:
    """`scripts/sync/m2-sync.sh:10`、`:14` と同じ規則で `$M2DIR` を解決する。"""
    m2dir = home / "slocal2" / "m2" if (home / "slocal2").is_dir() else home / "slocal" / "m2"
    if not (home / "slocal2").is_dir() and not (home / "slocal").is_dir() and (home / "local" / "m2").is_dir():
        m2dir = home / "local" / "m2"
    return m2dir


def _m2dir() -> Path:
    override = os.environ.get("TASK_RELEASE_M2DIR")
    return Path(override) if override else resolve_m2dir(Path.home())


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    # 読むだけの git が index を書き直さないようにする（stat 情報の更新を含めて）。
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True)


def _git(cwd: Path, *args: str) -> str:
    proc = _run(["git", *args], cwd)
    if proc.returncode != 0:
        raise Unknown(f"git {' '.join(args)} が失敗した（exit {proc.returncode}）")
    return proc.stdout


def read_owner(marker: Path) -> str | None:
    """目印の所有者（task_id）を返す。読めなければ None。"""
    try:
        text = marker.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    for line in text.splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() == "task_id" and value.strip():
            return value.strip()
    return None


def check_prerequisites(repo: Path, task_id: str, branch: str) -> tuple[list[str], list[str]]:
    """完了の前提を確かめる。（欠けた前提, 確かめられなかった前提）を返す。"""
    missing: list[str] = []
    unknown: list[str] = []

    def probe(name: str, fn) -> None:
        try:
            problem = fn()
        except Unknown as exc:
            unknown.append(f"{name}（{exc}）")
            return
        if problem:
            missing.append(f"{name}（{problem}）")

    def on_branch() -> str | None:
        current = _git(repo, "branch", "--show-current").strip()
        return None if current == branch else f"現在の分岐は {current or '(detached)'}"

    def tracked_clean() -> str | None:
        changes = _git(repo, "status", "--porcelain", "--untracked-files=no").splitlines()
        return None if not changes else f"追跡下の未 commit の変更が {len(changes)} 件"

    def pushed() -> str | None:
        head = _git(repo, "rev-parse", "HEAD").strip()
        out = _git(repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}").split()
        if not out:
            return "遠隔に分岐が無い"
        return None if out[0] == head else "遠隔の先頭が HEAD と違う（送っていない commit がある）"

    def pr_exists() -> str | None:
        gh = os.environ.get("TASK_RELEASE_GH", "gh")
        try:
            proc = _run([gh, "pr", "list", "--head", branch, "--base", BASE_BRANCH, "--state", "all",
                         "--json", "number,state"], repo)
        except OSError as exc:
            raise Unknown(f"gh を起動できない: {exc.__class__.__name__}") from exc
        if proc.returncode != 0:
            raise Unknown(f"gh pr list が失敗した（exit {proc.returncode}）")
        try:
            prs = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise Unknown("gh pr list の応答を読めない") from exc
        ok = [p for p in prs if p.get("state") in ("OPEN", "MERGED")]
        return None if ok else f"{BASE_BRANCH} 向けの開いた PR も統合済みの PR も無い"

    def reported() -> str | None:
        lacking = []
        for name in ("RESULT.md", "result.yaml"):
            path = f"tasks/{task_id}/{name}"
            if not _git(repo, "ls-tree", "--name-only", "HEAD", "--", path).strip():
                lacking.append(name)
        return None if not lacking else f"HEAD に {', '.join(lacking)} が無い"

    probe("1 分岐", on_branch)
    probe("2 未 commit", tracked_clean)
    probe("3 遠隔", pushed)
    probe("4 PR", pr_exists)
    probe("5 報告", reported)
    return missing, unknown


def remove_marker(marker: Path, task_id: str) -> Outcome:
    """削除を優先し、拒まれたら無視される名前へ移す。外れたことを実在で確かめる。"""
    method = "removed"
    try:
        os.remove(marker)
    except OSError:
        moved = marker.with_name(f"{MARKER_NAME}.released.{task_id}")
        try:
            os.replace(marker, moved)
        except OSError as exc:
            return Outcome("RELEASE_FAILED", f"削除も移動もできなかった（{exc.__class__.__name__}）")
        method = f"moved:{moved.name}"
    if os.path.lexists(marker):
        return Outcome("RELEASE_FAILED", "外した後も目印が存在する")
    return Outcome("RELEASED", "目印が存在しないことを確かめた", {"method": method})


def release(task_id: str, end: str, reason: str | None, cwd: Path) -> Outcome:
    m = TASK_ID_RE.match(task_id or "")
    if not m:
        return Outcome("USAGE", "識別子は T-YYYY-MM-DD-slug（slug は小文字英数とハイフン、3〜60 文字）")
    if end not in ("complete", "abort"):
        return Outcome("USAGE", "終わり方は complete か abort")
    if end == "abort" and not (reason or "").strip():
        return Outcome("USAGE", "中止（abort）には理由（--reason / REASON=）が要る")
    branch = f"feat/{m.group(1)}"

    try:
        repo = Path(_git(cwd, "rev-parse", "--show-toplevel").strip())
    except Unknown as exc:
        return Outcome("PREREQ_UNKNOWN", f"repo の最上位を特定できない: {exc}")
    m2dir = _m2dir()
    if os.path.realpath(repo) != os.path.realpath(m2dir):
        return Outcome("POSITION_MISMATCH", f"repo の最上位 {repo} は m2-sync.sh の読む $M2DIR {m2dir} と違う")

    marker = m2dir / MARKER_NAME
    if not os.path.lexists(marker):
        return Outcome("ABSENT", f"{marker} は元から無い。何もしていない")

    owner = read_owner(marker)
    if owner is None:
        return Outcome("OWNER_UNREADABLE", "目印の所有者を読めない（人が手で置いた目印か、旧い task_start.sh が置いた目印）。外さない")
    if owner != task_id:
        return Outcome("OWNER_MISMATCH", f"目印の所有者は {owner}。外さない")

    if end == "complete":
        missing, unknown = check_prerequisites(repo, task_id, branch)
        if missing:
            detail = "欠けている: " + "; ".join(missing)
            if unknown:
                detail += " / 確かめられない: " + "; ".join(unknown)
            return Outcome("PREREQ_MISSING", detail + "。外さない")
        if unknown:
            return Outcome("PREREQ_UNKNOWN", "確かめられない: " + "; ".join(unknown) + "。外さない")

    outcome = remove_marker(marker, task_id)
    outcome.extra = {"end": end, **outcome.extra}
    if end == "abort":
        outcome.extra["reason"] = json.dumps(reason.strip(), ensure_ascii=False)
    return outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="契約の終わりに同期の抑止（.sync-pause）を外す。")
    parser.add_argument("task_id", nargs="?", default="")
    parser.add_argument("--end", default="", help="complete（完了）か abort（中止）")
    parser.add_argument("--reason", default=None, help="中止の理由（abort では必須）")
    args = parser.parse_args(argv)

    outcome = release(args.task_id, args.end, args.reason, Path.cwd())
    print(outcome.line(args.task_id))
    return outcome.code


if __name__ == "__main__":
    raise SystemExit(main())
