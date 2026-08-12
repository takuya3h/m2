#!/usr/bin/env python3
"""禁止領域へ触れた変更を、生成物を除いて列挙する。

契約は「証跡と正本のある場所を変更しない」ことを求める一方、投影と集約結果の
**生成**は求める。生成物は禁止領域の内側（`context/auto/`）にあるため、素朴に
「差分が空であること」を要求すると**指示どおり実行すると必ず判定を破る**。

この道具は生成物を除外したうえで検査する。除外する場所は生成器の実装から取る。
手で書いた一覧を持つと、生成物が増えたときに検査が古くなるためである。

生成物への手編集はこの検査では捕まらない。**再生成との差分で捕まる。**

    make taskindex-check
    make inbox-check

使い方:

    python tools/check_forbidden.py                    # 起点は origin/phase0
    python tools/check_forbidden.py --base <commit>    # 起点を指定する
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "origin/phase0"

# 証跡と正本のある場所。契約が個別に広げる場合は --base とは別に運用で足す。
FORBIDDEN_PREFIXES = (
    "runindex/",
    "context/auto/",
    "experiments/",
    "transfer/",
    "data/",
)
FORBIDDEN_FILES = (
    "context/conventions.md",
    "tools/harvest_runindex.py",
    "tools/build_context.py",
)


@dataclass(frozen=True)
class Violation:
    path: str
    reason: str


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def generated_locations() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """生成器の実装から、生成物の場所を取る。

    Returns:
        (ディレクトリの接頭辞, ファイルの相対パス) の対。いずれも repo 相対。

    Raises:
        RuntimeError: 生成器を読み込めない、または場所を取れない場合。
            **一覧を推測で作らない。** 取れなければ失敗させる。
    """
    tools_dir = str(REPO_ROOT / "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    try:
        import build_context
        import build_inbox
        import build_taskindex
    except ImportError as exc:  # pragma: no cover - 実装が欠けた場合のみ
        raise RuntimeError(f"生成器を読み込めない: {exc}") from exc

    directories = set()
    for module in (build_taskindex, build_context):
        auto_dir = getattr(module, "AUTO_DIR", None)
        if auto_dir is None:
            raise RuntimeError(f"{module.__name__} に AUTO_DIR が無い")
        directories.add(f"{Path(auto_dir).relative_to(REPO_ROOT).as_posix()}/")

    inbox_file = getattr(build_inbox, "INBOX_FILE", None)
    if inbox_file is None:
        raise RuntimeError("build_inbox に INBOX_FILE が無い")
    files = {Path(inbox_file).relative_to(REPO_ROOT).as_posix()}

    return tuple(sorted(directories)), tuple(sorted(files))


def changed_paths(base: str) -> list[str]:
    """起点との差分と、追跡外のファイルを合わせて返す。

    Raises:
        RuntimeError: 起点が解決できない、または差分が取れない場合。
    """
    resolved = _git(["rev-parse", "--verify", "--quiet", f"{base}^{{commit}}"])
    if resolved.returncode != 0 or not resolved.stdout.strip():
        raise RuntimeError(f"起点を解決できない: {base}")

    diff = _git(["diff", "--name-only", base])
    if diff.returncode != 0:
        raise RuntimeError(f"差分を取れない: {diff.stderr.strip()}")

    untracked = _git(["ls-files", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        raise RuntimeError(f"追跡外の一覧を取れない: {untracked.stderr.strip()}")

    paths = {line for line in diff.stdout.splitlines() if line}
    paths.update(line for line in untracked.stdout.splitlines() if line)
    return sorted(paths)


def is_generated(path: str, directories: tuple[str, ...], files: tuple[str, ...]) -> bool:
    return path in files or path.startswith(directories)


def classify(path: str) -> str | None:
    """禁止領域に該当するなら理由を返す。該当しなければ None。"""
    for prefix in FORBIDDEN_PREFIXES:
        if path.startswith(prefix):
            return f"禁止領域 {prefix} の内側"
    if path in FORBIDDEN_FILES:
        return f"禁止されたファイル {path}"
    return None


def check(base: str) -> dict:
    directories, files = generated_locations()
    paths = changed_paths(base)

    excluded = [p for p in paths if is_generated(p, directories, files)]
    checked = [p for p in paths if p not in set(excluded)]
    violations = [
        Violation(path=p, reason=reason)
        for p in checked
        if (reason := classify(p)) is not None
    ]
    return {
        "status": "fail" if violations else "pass",
        "base": base,
        "changed": len(paths),
        "checked": len(checked),
        "excluded": len(excluded),
        "excluded_paths": excluded,
        "generated_directories": list(directories),
        "generated_files": list(files),
        "violations": [asdict(item) for item in violations],
        "errors": [],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="禁止領域へ触れた変更を検査する。")
    parser.add_argument(
        "--base",
        default=DEFAULT_BASE,
        help=f"差分の起点。既定は {DEFAULT_BASE}。",
    )
    args = parser.parse_args(argv)

    try:
        payload = check(args.base)
    except RuntimeError as exc:
        payload = {
            "status": "fail",
            "base": args.base,
            "changed": 0,
            "checked": 0,
            "excluded": 0,
            "excluded_paths": [],
            "generated_directories": [],
            "generated_files": [],
            "violations": [],
            "errors": [str(exc)],
        }
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 2

    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 1 if payload["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
