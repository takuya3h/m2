#!/usr/bin/env python3
"""対話記録から機械的に取り出せる要素だけを抽出する。

**要約はしない。** 言語モデルによる要約は捏造を生むため、抽出のみを版管理へ入れる。
会話本文・thinking・モデルの応答・評価は一切含めない。

抽出後は必ず伏せ字を適用する。既定で伏せ、通す方を例外にする。
判断に迷うものは伏せる。伏せすぎて困ることはあるが、漏れると取り返しがつかない。

記録の形式は実測に基づく（2026-08-08、`~/.claude/projects/*/*.jsonl`）。

- 1 行 1 JSON。`type` は mode / attachment / user / assistant / system 等
- `assistant` 行の `message.content` は block の配列。block の `type` は
  thinking / text / tool_use
- `tool_use` は `name` と `input` を持つ。Bash は `input.command`、
  Edit / Write / Read は `input.file_path`
- 失敗は `user` 行の `tool_result` block の `is_error` が真であることで表れる
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DIGEST_DIRNAME = Path("docs") / "sessions" / "digest"

# 伏せ字の規則。既定で伏せ、通す方を例外にする。
_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    # 環境変数の代入。名前は残し値だけ伏せる。
    (re.compile(r"\b([A-Z][A-Z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL)[A-Z0-9_]*)\s*=\s*\S+"),
     r"\1=<redacted>"),
    # 鍵らしき接頭辞を持つ文字列。
    (re.compile(r"\b(sk|pk|ghp|gho|ghs|ghu|xox[abpsr])[-_][A-Za-z0-9_\-]{16,}"),
     r"\1-<redacted>"),
    # 長い十六進。先頭 4 文字だけ残す。commit の短縮形（7 文字前後）は残したいので
    # 32 文字以上に限る。
    (re.compile(r"\b([0-9a-fA-F]{4})[0-9a-fA-F]{28,}\b"), r"\1<redacted>"),
)

# 契約の識別子。様式が定まっているものだけを拾う。
_TASK_ID_RE = re.compile(r"\bT-\d{4}-\d{2}-\d{2}-[a-z0-9-]{3,60}")
# コマンド 1 件として残す最大の長さ。
# ヒアドキュメント（cat >> file <<'EOF' ...）はコマンド文字列に文書全体を含むため、
# そのまま残すと抽出物が文書の再掲になる（実測: 1 セッションで 176KB / 3351 行、
# 最長 3805 文字）。**要約はせず**、先頭だけを残して切り詰め、その事実を明示する。
_COMMAND_MAX = 200
# 入力に file_path を持つツール（実測で確認したもの）。
_PATH_KEYS = ("file_path", "notebook_path", "path")


def redact(text: str) -> str:
    """秘匿らしき文字列を伏せる。通常の文は 1 文字も変えない。"""
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def shorten_command(command: str) -> str:
    """コマンドを識別できる長さまで切り詰める。要約はしない。

    複数行のコマンドは先頭行で識別できれば足りる。切り詰めた場合はその旨を付す。
    """
    first, _, rest = command.strip().partition("\n")
    first = first.strip()
    truncated = bool(rest.strip())
    if len(first) > _COMMAND_MAX:
        first = first[:_COMMAND_MAX]
        truncated = True
    return f"{first} …（切り詰め）" if truncated else first


def _blocks(obj: dict) -> list:
    content = (obj.get("message") or {}).get("content")
    return content if isinstance(content, list) else []


def extract_exec_command(text: str) -> str | None:
    """第二の実装系の呼び出し文字列から実行コマンドを取り出す。

    実測（2026-08-08、`~/.codex/sessions/**/rollout-*.jsonl`）では、
    `payload.input` は次の形の JavaScript 断片である。

        const r = await tools.exec_command({cmd:"<コマンド>","workdir":"..."});

    `cmd:"` の直後から、エスケープを尊重して閉じ引用符までを取り、
    JSON として復号する。復号できなければ諦めて None を返す（推測で補完しない）。
    """
    marker = 'cmd:"'
    start = text.find(marker)
    if start < 0:
        return None
    index = start + len(marker) - 1  # 開き引用符を含める
    scan = index + 1
    while scan < len(text):
        char = text[scan]
        if char == "\\":
            scan += 2
            continue
        if char == '"':
            try:
                value = json.loads(text[index : scan + 1])
            except json.JSONDecodeError:
                return None
            return value if isinstance(value, str) and value.strip() else None
        scan += 1
    return None


def extract(lines) -> dict:
    """記録の各行から機械的な要素だけを集める。

    解析できない行は黙って飛ばす。抽出に失敗しても落ちない。
    """
    commands: list[str] = []
    files: list[str] = []
    errors: list[str] = []
    task_ids: list[str] = []
    session_id = ""
    stamps: list[str] = []

    for line in lines:
        line = (line or "").strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, TypeError):
            continue
        if not isinstance(obj, dict):
            continue

        payload = obj.get("payload")
        payload = payload if isinstance(payload, dict) else {}
        session_id = session_id or str(
            obj.get("sessionId") or obj.get("session_id") or payload.get("session_id") or ""
        )
        stamp = obj.get("timestamp")
        if isinstance(stamp, str) and stamp:
            stamps.append(stamp)

        kind = obj.get("type")
        if kind == "assistant":
            for block in _blocks(obj):
                # thinking と text は会話であり抽出対象ではない。
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                payload = block.get("input") or {}
                if not isinstance(payload, dict):
                    continue
                command = payload.get("command")
                if isinstance(command, str) and command.strip():
                    commands.append(shorten_command(command))
                    # 識別子は切り詰める前の全文から拾う。切り詰めで見落とさないため。
                    task_ids.extend(_TASK_ID_RE.findall(command))
                for key in _PATH_KEYS:
                    value = payload.get(key)
                    if isinstance(value, str) and value.strip():
                        files.append(value.strip())
                        task_ids.extend(_TASK_ID_RE.findall(value))
        elif kind == "user":
            for block in _blocks(obj):
                if not isinstance(block, dict) or block.get("type") != "tool_result":
                    continue
                if not block.get("is_error"):
                    continue
                body = block.get("content")
                if not isinstance(body, str):
                    body = json.dumps(body, ensure_ascii=False)
                errors.append(" ".join(body.split())[:200])
        elif kind == "response_item":
            # 第二の実装系。message / reasoning は会話であり抽出対象ではない。
            if payload.get("type") not in ("custom_tool_call", "function_call"):
                continue
            raw = payload.get("input")
            if not isinstance(raw, str):
                continue
            command = extract_exec_command(raw)
            if command:
                commands.append(shorten_command(command))
                task_ids.extend(_TASK_ID_RE.findall(command))

    def _uniq(values: list[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                out.append(value)
        return out

    return {
        "session_id": session_id,
        "started": min(stamps) if stamps else "",
        "ended": max(stamps) if stamps else "",
        "commands": _uniq(commands),
        "files": _uniq(files),
        "errors": _uniq(errors),
        "task_ids": _uniq(task_ids),
    }


def render(result: dict) -> str:
    """抽出結果を固定書式で書き出す。自由記述の要約は含めない。"""
    lines = [
        f"# session {result.get('session_id') or 'UNKNOWN'}",
        "",
        "対話記録から機械的に抽出した要素のみ。会話本文・所感・評価は含まない。",
        "",
        f"    started: {result.get('started') or 'UNKNOWN'}",
        f"    ended:   {result.get('ended') or 'UNKNOWN'}",
        "",
    ]
    for title, key in (
        ("契約の識別子", "task_ids"),
        ("実行されたコマンド", "commands"),
        ("編集または参照されたファイル", "files"),
        ("失敗したツール呼び出し", "errors"),
    ):
        values = result.get(key) or []
        lines.append(f"## {title}（{len(values)}）")
        lines.append("")
        if values:
            lines.extend(f"- `{redact(str(v))}`" for v in values)
        else:
            lines.append("（なし）")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _digest_path(root: Path, result: dict, key: str | None = None) -> Path:
    """出力先。壁時計は使わず、記録に含まれる時刻を使う。

    `key` は記録ごとに一意な識別子。省略時は `session_id` を使うが、
    **親子セッションは同じ `session_id` を報告する**（実測）ため、
    走査から呼ぶときは記録そのものに由来する一意な値を渡すこと。
    渡さないと別々の記録が同名の抽出物へ互いを上書きし、片方が静かに失われる。
    """
    started = result.get("started") or ""
    day = started[:10] if len(started) >= 10 else "unknown-date"
    name = key or result.get("session_id") or "unknown"
    return root / DIGEST_DIRNAME / f"{day}-{name.replace('/', '_')}.md"


def _read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


CODEX_SESSION_GLOB = ".codex/sessions/**/rollout-*.jsonl"


def sweep_codex(root: Path, home: Path | None = None) -> list[Path]:
    """第二の実装系の記録を走査し、まだ抽出していないものだけを書き出す。

    第二の実装系にも hook の仕組みはあるが、設定の様式が公開情報から判明しない。
    **推測で様式を仮定しない**ため、登録ではなく走査で補う。
    既に同じ内容の抽出物があれば書き直さない（冪等）。
    """
    base = home or Path.home()
    written: list[Path] = []
    for transcript in sorted(base.glob(CODEX_SESSION_GLOB)):
        result = extract(_read_lines(transcript))
        if not result["commands"] and not result["task_ids"]:
            continue  # 中身の無い記録は残さない
        # 記録のファイル名は構成上一意である。session_id は親子で重複するため使わない。
        key = transcript.stem
        if key.startswith("rollout-"):
            key = key[len("rollout-") :]
        # 記録名は日付で始まる。出力名も日付で始まるため重複を落とす。
        day = (result.get("started") or "")[:10]
        if day and key.startswith(f"{day}T"):
            key = key[len(day) + 1 :]
        out = _digest_path(root, result, key=key)
        text = render(result)
        if out.is_file() and out.read_text(encoding="utf-8") == text:
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        written.append(out)
    return written


def _transcript_from_stdin() -> str | None:
    """hook から渡される JSON を読む。jq に依存しない。"""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    value = payload.get("transcript_path")
    return value if isinstance(value, str) and value else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--transcript", help="対話記録のパス")
    parser.add_argument("--from-hook", action="store_true", help="標準入力の JSON から記録のパスを読む")
    parser.add_argument("--root", default=str(REPO_ROOT), help="出力先の基点")
    parser.add_argument("--stdout", action="store_true", help="ファイルへ書かず標準出力へ出す")
    parser.add_argument("--sweep-codex", action="store_true",
                        help="第二の実装系の記録を走査し、未抽出のものを書き出す")
    args = parser.parse_args()

    if args.sweep_codex:
        for path in sweep_codex(Path(args.root)):
            print(str(path))
        return 0

    transcript = args.transcript
    if args.from_hook:
        transcript = _transcript_from_stdin() or transcript
    if not transcript:
        print("対話記録のパスが分かりません", file=sys.stderr)
        return 1

    path = Path(transcript).expanduser()
    if not path.is_file():
        print(f"対話記録が見つかりません: {transcript}", file=sys.stderr)
        return 1

    result = extract(_read_lines(path))
    text = render(result)

    if args.stdout:
        try:
            sys.stdout.write(text)
            sys.stdout.flush()
        except BrokenPipeError:
            # `| head` のように読み手が先に閉じる使い方は普通にある。
            # 追い書きで再び例外が出ないよう、後片付けの経路も潰しておく。
            try:
                sys.stdout.close()
            except BrokenPipeError:
                pass
            os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        return 0

    out = _digest_path(Path(args.root), result)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
