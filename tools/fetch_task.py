#!/usr/bin/env python3
"""外部で起票された契約を一操作で取り込む。

取得 → 一時ディレクトリへ展開 → tasks/ へ設置 → L1 と L2 の検証、までを行う。
**検証に失敗したら設置を巻き戻す。** 不完全な契約が tasks/ に残ると、以後
make task-validate が常時 FAIL するためである。

入力形式は区切り付きテキスト（バンドル）。契約の供給元がテキストを出力する面である
ことに合わせている。先頭行が形式と区切り文字を宣言する。

    #!TASK-BUNDLE v1 delim=<40 文字以上の区切り>
    <delim> FILE spec.yaml
    ...
    <delim> FILE SPEC.md
    ...
    <delim> END

区切りが本文と衝突した場合は構造が壊れるため、解析時に検出して失敗させる。
"""
from __future__ import annotations

import argparse
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / "tasks"

BUNDLE_MAGIC = "#!TASK-BUNDLE"
BUNDLE_VERSION = "v1"
MIN_DELIM_LEN = 40
_DELIM_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_HEADER_RE = re.compile(
    rf"^{re.escape(BUNDLE_MAGIC)}\s+(?P<version>v\d+)\s+delim=(?P<delim>\S+)\s*$"
)
# 取り込みを認めるファイル。契約そのものだけを受け取り、実行後の成果物は受け取らない。
ALLOWED_FILES = ("spec.yaml", "SPEC.md", "prereg.md")
REQUIRED_FILES = ("spec.yaml", "SPEC.md")
# ディレクトリ名に使うため、任意の文字列を受け入れてはならない。
# 🔴 終端は $ ではなく \Z を使う。Python の $ は**末尾の改行の直前にも一致する**ため、
#    "T-2026-08-03-x\n" のような値を通してしまう。改行入りの task_id は
#    make のレシピを分断し、別の契約を検証させたうえで exit 0 を返させる経路がある。
_TASK_ID_RE = re.compile(r"^T-\d{4}-\d{2}-\d{2}-[a-z0-9-]+\Z")
_URL_RE = re.compile(r"^https?://", re.I)


class BundleError(Exception):
    """バンドルの形式・内容が受け入れられないことを示す。"""


def parse_bundle(text: str) -> dict[str, str]:
    """バンドルを {ファイル名: 中身} へ分解する。

    構造が想定と違えば BundleError を送出する。区切りが本文と衝突した場合も
    構造違反として現れるため、ここで捕まえる。
    """
    lines = text.splitlines()
    header_index = next((i for i, line in enumerate(lines) if line.strip()), None)
    if header_index is None:
        raise BundleError("入力が空です")

    header = _HEADER_RE.match(lines[header_index].strip())
    if not header:
        raise BundleError(
            f"先頭行が {BUNDLE_MAGIC} {BUNDLE_VERSION} delim=<区切り> の形式ではありません"
        )
    if header.group("version") != BUNDLE_VERSION:
        raise BundleError(f"未対応のバンドル版です: {header.group('version')}")

    delim = header.group("delim")
    if len(delim) < MIN_DELIM_LEN:
        raise BundleError(f"区切りが短すぎます（{len(delim)} 文字、{MIN_DELIM_LEN} 文字以上が必要）")
    if not _DELIM_RE.match(delim):
        raise BundleError("区切りに使えない文字が含まれます（英数字とハイフンと下線のみ）")

    files: dict[str, list[str]] = {}
    current: str | None = None
    ended = False
    for line in lines[header_index + 1 :]:
        if not line.startswith(delim):
            if ended:
                if line.strip():
                    raise BundleError("END のあとに内容が続いています")
                continue
            if current is None:
                if line.strip():
                    raise BundleError("最初の FILE 標識より前に内容があります")
                continue
            files[current].append(line)
            continue

        marker = line[len(delim) :].strip()
        if ended:
            raise BundleError("END のあとに標識が続いています")
        if marker == "END":
            ended = True
            continue
        if not marker.startswith("FILE "):
            raise BundleError(f"解釈できない標識です: {marker!r}。区切りが本文と衝突した可能性があります")
        name = marker[len("FILE ") :].strip()
        if name not in ALLOWED_FILES:
            raise BundleError(f"受け取れないファイルです: {name!r}（許可: {', '.join(ALLOWED_FILES)}）")
        if name in files:
            raise BundleError(f"同じファイルが二度現れます: {name}")
        files[name] = []
        current = name

    if not ended:
        raise BundleError("END 標識がありません。入力が途中で切れている可能性があります")
    missing = [name for name in REQUIRED_FILES if name not in files]
    if missing:
        raise BundleError(f"必須のファイルがありません: {', '.join(missing)}")

    # 行頭の衝突は上の標識解釈で捕まるが、行の途中に現れた場合は構造が壊れないため
    # 素通りしてしまう。組み立て側 (pack_bundle) は本文中のどこにあっても拒否するので、
    # 解析側も同じ基準で拒否し、衝突した入力を受け入れない。
    for name, body in files.items():
        if any(delim in line for line in body):
            raise BundleError(f"区切りが {name} の本文と衝突しています")

    return {name: "\n".join(body).rstrip("\n") + "\n" for name, body in files.items()}


def task_id_from_spec(spec_text: str) -> str:
    """spec.yaml の meta.task_id を取り出し、ディレクトリ名として安全か検査する。"""
    try:
        data = yaml.safe_load(spec_text)
    except yaml.YAMLError as exc:
        raise BundleError(f"spec.yaml を解釈できません: {type(exc).__name__}") from exc
    if not isinstance(data, dict):
        raise BundleError("spec.yaml の内容が対応表ではありません")
    task_id = (data.get("meta") or {}).get("task_id")
    if not task_id or not isinstance(task_id, str):
        raise BundleError("spec.yaml に meta.task_id がありません")
    if not _TASK_ID_RE.match(task_id):
        raise BundleError(f"task_id の形式が規約に合いません: {task_id!r}")
    return task_id


def ensure_absent(task_id: str, tasks_dir: Path) -> None:
    """同名の契約が既にあれば失敗させる。上書きはしない。"""
    if (tasks_dir / task_id).exists():
        raise BundleError(f"同名の契約が既にあります: tasks/{task_id}（上書きしません）")


def pack_bundle(files: dict[str, str], delim: str | None = None) -> str:
    """{ファイル名: 中身} をバンドルへ組み立てる。

    区切りは本文と衝突しないことを確かめてから使う。衝突したら失敗させる。
    """
    for name in files:
        if name not in ALLOWED_FILES:
            raise BundleError(f"受け取れないファイルです: {name!r}")
    missing = [name for name in REQUIRED_FILES if name not in files]
    if missing:
        raise BundleError(f"必須のファイルがありません: {', '.join(missing)}")

    if delim is None:
        delim = secrets.token_hex(24)
    if len(delim) < MIN_DELIM_LEN or not _DELIM_RE.match(delim):
        raise BundleError("区切りが要件を満たしません")
    for name, body in files.items():
        if delim in body:
            raise BundleError(f"区切りが {name} の本文と衝突しています")

    parts = [f"{BUNDLE_MAGIC} {BUNDLE_VERSION} delim={delim}"]
    for name in ALLOWED_FILES:
        if name in files:
            parts.append(f"{delim} FILE {name}")
            parts.append(files[name].rstrip("\n"))
    parts.append(f"{delim} END")
    return "\n".join(parts) + "\n"


def read_source(src: str) -> str:
    """ローカルファイルまたは URL からバンドルを読む。"""
    if _URL_RE.match(src):
        with urllib.request.urlopen(src, timeout=60) as response:  # noqa: S310
            return response.read().decode("utf-8")
    path = Path(src).expanduser()
    if not path.is_file():
        raise BundleError(f"入力が見つかりません: {src}")
    return path.read_text(encoding="utf-8")


def _validate(task_id: str) -> tuple[int, str]:
    """設置した契約を make task-validate にかける。判定を複製しない。"""
    proc = subprocess.run(
        ["make", "task-validate", f"TASK={task_id}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def rollback(installed: Path) -> bool:
    """設置を巻き戻し、**本当に消えたことを確かめる**。

    消えたかどうかを見ずに「痕跡は残していません」と書いてはならない。
    消し切れなかった場合は、その事実と残った場所をそのまま報告する。
    """
    shutil.rmtree(installed, ignore_errors=True)
    if installed.exists():
        print(
            f"巻き戻しに失敗しました。手で確認してください: {installed}",
            file=sys.stderr,
        )
        return False
    return True


def _install_sigterm_handler() -> None:
    """SIGTERM を SystemExit へ変換し、巻き戻しの経路に載せる。

    既定では SIGTERM は例外を起こさずプロセスを終わらせるため、
    設置済みの契約が残ってしまう。
    """

    def _raise(_signum, _frame):
        raise SystemExit(143)

    try:
        signal.signal(signal.SIGTERM, _raise)
    except (ValueError, OSError):  # 主スレッド以外では登録できない
        pass


def fetch(src: str) -> int:
    try:
        text = read_source(src)
        files = parse_bundle(text)
        task_id = task_id_from_spec(files["spec.yaml"])
        ensure_absent(task_id, TASKS_DIR)
    except BundleError as exc:
        print(f"取り込みを中止しました: {exc}", file=sys.stderr)
        return 1

    _install_sigterm_handler()
    installed = TASKS_DIR / task_id
    # この run が作ったディレクトリだけを巻き戻す。既にあったものには触れない。
    owned = False
    try:
        # 一時ディレクトリは成否にかかわらず必ず消える。tasks/ へは検証の直前まで書かない。
        with tempfile.TemporaryDirectory(prefix=".task_fetch_") as tmp:
            staging = Path(tmp) / task_id
            staging.mkdir(parents=True)
            for name, body in files.items():
                (staging / name).write_text(body, encoding="utf-8")

            # 名前をアトミックに確保する。既にあれば FileExistsError になり、
            # **この run が作っていない**ディレクトリなので巻き戻しの対象にしない。
            # ensure_absent と copytree の間に横から作られた場合の取り違えを防ぐ。
            try:
                installed.mkdir(parents=True)
            except FileExistsError:
                print(
                    f"取り込みを中止しました: 同名の契約が既にあります: tasks/{task_id}（上書きしません）",
                    file=sys.stderr,
                )
                return 1
            owned = True
            shutil.copytree(staging, installed, dirs_exist_ok=True)

        code, output = _validate(task_id)
    # 🔴 Exception ではなく BaseException を捕まえる。Ctrl-C（KeyboardInterrupt）や
    #    SIGTERM（上で SystemExit へ変換）は Exception を継承しないため、
    #    Exception だけでは検証中の中断で設置が残る。
    except BaseException as exc:
        if owned:
            cleaned = rollback(installed)
        else:
            cleaned = True
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            print(
                f"中断されました。tasks/{task_id} は"
                + ("巻き戻しました" if cleaned else "巻き戻せませんでした"),
                file=sys.stderr,
            )
            raise
        print(f"取り込み中に失敗しました: {type(exc).__name__}: {exc}", file=sys.stderr)
        if cleaned:
            print(f"tasks/{task_id} は巻き戻しました（痕跡は残していません）", file=sys.stderr)
        return 1

    if code != 0:
        cleaned = rollback(installed)
        print(output.rstrip(), file=sys.stderr)
        if cleaned:
            print(
                f"検証に失敗したため tasks/{task_id} を巻き戻しました（痕跡は残していません）",
                file=sys.stderr,
            )
        else:
            print(f"検証に失敗しました: tasks/{task_id}", file=sys.stderr)
        return 1

    print(output.rstrip())
    print(f"\n取り込みました: tasks/{task_id}")
    print("次の操作:")
    print(f"    make task-preflight TASK={task_id}")
    print(f"    /task {task_id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", help="バンドルのパスまたは URL")
    parser.add_argument("--pack", help="この契約ディレクトリからバンドルを組み立てて標準出力へ書く")
    args = parser.parse_args()

    if args.pack:
        source_dir = Path(args.pack)
        if not source_dir.is_dir():
            print(f"契約ディレクトリが見つかりません: {args.pack}", file=sys.stderr)
            return 1
        files = {
            name: (source_dir / name).read_text(encoding="utf-8")
            for name in ALLOWED_FILES
            if (source_dir / name).is_file()
        }
        try:
            sys.stdout.write(pack_bundle(files))
        except BundleError as exc:
            print(f"組み立てに失敗しました: {exc}", file=sys.stderr)
            return 1
        return 0

    if not args.src:
        parser.error("--src または --pack が要ります")
    return fetch(args.src)


if __name__ == "__main__":
    sys.exit(main())
