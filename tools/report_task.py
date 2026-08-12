#!/usr/bin/env python3
"""完了報告を配布台帳へ送り返す。

    make task-report TASK=<task_id>

契約は台帳経由で即座に届いている。**同じ経路を逆向きに使う。**
投影（`context/auto/results_recent.md`）は後から振り返るには使えるが、索引の更新が
遅れるため完了直後の受け渡しには使えない。

取り込みの実装（`tools/fetch_task.py`）を**再利用する。複製しない。**
資格情報の読み方・行の特定・頁送りはすべて向こうにある。

本文は `code` ブロックへ置く。理由は推測ではなく実装から決めた。取り込み側の
`_scan_children` が読むのは `code` ブロックの `rich_text` だけであり、記法として
解釈されない。2026-08-12 の実測では 5364 バイトが往復で 1 バイトも変わっていない。

**報告のブロックには目印を付ける。** 目印が無いと、本文で配布された契約の行に報告を
足したとき、取り込み側が契約本文と報告を連結してしまう（`_scan_children` は
すべての `code` ブロックを連結する）。2026-08-11 時点の 4 行はいずれも添付のみで
実害は無いが、それは偶然であって設計ではない。

**外部へ送るのは一方向で取り消せない。** 送る前に秘匿を検査する。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fetch_task as F  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
TASKS_DIR = REPO_ROOT / "tasks"

# 報告のブロックの先頭に置く目印。契約本文と読み分けるために要る。
REPORT_SENTINEL = F.REPORT_SENTINEL

# Notion API の rich_text 1 要素あたりの上限。
# src/egosurgery/utils/notion_logger.py:337 の _RICH_TEXT_LIMIT と同じ値。
# tools/ からは egosurgery を import しない作りなので、値をここに置き直している。
RICH_TEXT_LIMIT = 2000

# 秘匿として扱う環境変数。**設定値は対象外。** 平易な識別子（プロジェクト名など）を
# 資格情報として扱うと偽陽性で送れなくなる。
SECRET_ENV_KEYS = ("NOTION_API_KEY", "WANDB_API_KEY")

# 外部サービスの鍵に多い接頭辞。値そのものが手元に無くても形で気付ける。
SECRET_PATTERNS = (
    ("Notion の内部鍵", re.compile(r"\b(?:secret_|ntn_)[A-Za-z0-9]{20,}")),
    ("鍵らしい代入", re.compile(
        r"\b[A-Za-z0-9_-]*(?:API[-_]?KEY|SECRET|TOKEN|PASSWORD|PASSPHRASE)"
        r"[A-Za-z0-9_-]*\s*[:=]\s*['\"]?\S{12,}",
        re.IGNORECASE,
    )),
)


class ReportError(RuntimeError):
    """送り返せない理由。**送る前に必ず理由を出して止まる。**"""


# --------------------------------------------------------------------------- #
# 秘匿の検査
# --------------------------------------------------------------------------- #
def scan_secrets(text: str, env: dict[str, str] | None = None) -> list[str]:
    """本文に秘匿らしき内容が無いかを調べ、**何に一致したか**を返す。

    **値そのものは返さない。** 返すのは種別と位置だけである。
    最も確実なのは「環境にある資格情報そのものが本文に現れるか」の直接照合であり、
    形による推測より先に見る。
    """
    env = os.environ if env is None else env
    findings: list[str] = []

    for key in SECRET_ENV_KEYS:
        value = (env.get(key) or "").strip()
        if len(value) < 12:
            continue  # 未設定か短すぎる値。照合すると偶然一致する
        if value in text:
            findings.append(f"環境の {key} の値そのものが本文に現れる")

    for label, pattern in SECRET_PATTERNS:
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            findings.append(f"{label}（{line} 行目・値は伏せる）")

    return findings


# --------------------------------------------------------------------------- #
# 報告の材料
# --------------------------------------------------------------------------- #
def load_report(task_id: str, tasks_dir: Path | None = None) -> tuple[str, dict]:
    """散文の報告と構造化された対を読む。

    判定と件数は**対から読む。散文から抽出しない。**
    対が無ければ送らずに失敗する。何を送ったかが後から確かめられなくなるためである。
    """
    tasks_dir = TASKS_DIR if tasks_dir is None else tasks_dir
    task_dir = tasks_dir / task_id
    body_path, pair_path = task_dir / "RESULT.md", task_dir / "result.yaml"
    if not body_path.is_file():
        raise ReportError(f"完了報告がありません: {body_path}")
    if not pair_path.is_file():
        raise ReportError(
            f"構造化された対がありません: {pair_path}。"
            "判定と件数は散文から抽出しないため、対が無い報告は送りません"
        )
    pair = yaml.safe_load(pair_path.read_text(encoding="utf-8")) or {}
    if pair.get("task_id") != task_id:
        raise ReportError(
            f"対の task_id が一致しません: {pair.get('task_id')!r} != {task_id!r}"
        )
    return body_path.read_text(encoding="utf-8"), pair


def _rich_text(text: str) -> list[dict]:
    """UTF-16 単位の上限ごとに切って rich_text の要素へ並べる。

    取得時は要素が連結されて返るため、**境界の位置を覚える必要はない**
    （2026-08-12 に 5364 バイト・3 分割で実測）。
    """
    chunks: list[str] = []
    current: list[str] = []
    units = 0
    for char in text:
        char_units = 2 if ord(char) > 0xFFFF else 1
        if current and units + char_units > RICH_TEXT_LIMIT:
            chunks.append("".join(current))
            current = []
            units = 0
        current.append(char)
        units += char_units
    if current or not chunks:
        chunks.append("".join(current))
    return [{"type": "text", "text": {"content": c}} for c in chunks]


# --------------------------------------------------------------------------- #
# 台帳への書き込み
# --------------------------------------------------------------------------- #
def _delete_existing_report_blocks(page_id: str) -> int:
    """既にある報告のブロックを消す。**二度送っても行が壊れないため。**

    追記を繰り返すと読めなくなる。契約本文のブロックには触れない。
    """
    removed = 0
    for block in list(F._iter_child_blocks(page_id)):
        if block.get("type") != "code":
            continue
        parts = "".join(
            item.get("plain_text", "") for item in (block["code"].get("rich_text") or [])
        )
        if parts.startswith(REPORT_SENTINEL):
            F._notion_call_method(
                "DELETE", f"{F.NOTION_API_BASE}/blocks/{block['id']}"
            )
            removed += 1
    return removed


def send_report(task_id: str, tasks_dir: Path | None = None, *, dry_run: bool = False) -> dict:
    """完了報告を台帳の該当行へ置き、状態の列を更新する。

    **送る前に秘匿を検査する。** 一致があれば送らずに止まる。
    """
    body, pair = load_report(task_id, tasks_dir)

    findings = scan_secrets(body)
    if findings:
        raise ReportError(
            "秘匿らしき内容が報告に含まれます。**送信しません。**\n  "
            + "\n  ".join(findings)
            + "\n本文を直してから送り直してください。検査を無効にしないこと"
        )

    digest = hashlib.sha256(body.encode()).hexdigest()
    payload = {
        "task_id": task_id,
        "verdict": pair.get("status"),
        "n_issuer_defects": len(pair.get("issuer_defects") or []),
        "report_sha256": digest,
        "report_bytes": len(body.encode()),
    }
    if dry_run:
        return payload

    if not os.environ.get("NOTION_API_KEY", "").strip():
        raise ReportError(
            "NOTION_API_KEY が未設定です。source scripts/load_env.sh を先に実行してください"
        )

    page = F.find_ledger_row(task_id)
    page_id = page["id"]

    payload["replaced_blocks"] = _delete_existing_report_blocks(page_id)
    F._notion_call_method(
        "PATCH",
        f"{F.NOTION_API_BASE}/blocks/{page_id}/children",
        {
            "children": [
                {
                    "object": "block",
                    "type": "code",
                    "code": {
                        "language": "plain text",
                        "rich_text": _rich_text(REPORT_SENTINEL + "\n" + body),
                    },
                }
            ]
        },
    )
    F._notion_call_method(
        "PATCH",
        f"{F.NOTION_API_BASE}/pages/{page_id}",
        {
            "properties": {
                "status": {"select": {"name": "done"}},
                "verdict": {"select": {"name": str(pair.get("status"))}},
                "completed_at": {"date": {"start": _completed_at()}},
                "n_issuer_defects": {"number": payload["n_issuer_defects"]},
                "report_sha256": {"rich_text": [{"type": "text", "text": {"content": digest}}]},
                "report_bytes": {"number": payload["report_bytes"]},
            }
        },
    )
    return payload


def _completed_at() -> str:
    """送った日時。**壁時計を使うのはここだけである。**

    台帳の列が日付を求めており、生成物ではないため冪等性の検査には影響しない。
    """
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def read_back(task_id: str) -> str:
    """台帳に置いた報告を読み戻す。**往復の照合に使う。**"""
    page = F.find_ledger_row(task_id)
    parts: list[str] = []
    for block in F._iter_child_blocks(page["id"]):
        if block.get("type") != "code":
            continue
        text = "".join(
            item.get("plain_text", "") for item in (block["code"].get("rich_text") or [])
        )
        if text.startswith(REPORT_SENTINEL):
            parts.append(text[len(REPORT_SENTINEL) + 1:])
    if not parts:
        raise ReportError(f"台帳に報告が見つかりません: {task_id}")
    return "".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("task_id", help="送り返す契約の識別子")
    ap.add_argument("--dry-run", action="store_true", help="送らずに検査だけ行う")
    ap.add_argument("--read-back", action="store_true", help="台帳の報告を読み戻して照合する")
    args = ap.parse_args()

    try:
        if args.read_back:
            body, _ = load_report(args.task_id)
            remote = read_back(args.task_id)
            local_d = hashlib.sha256(body.encode()).hexdigest()
            remote_d = hashlib.sha256(remote.encode()).hexdigest()
            print(f"手元の要約値: {local_d}")
            print(f"台帳の要約値: {remote_d}")
            print("一致" if local_d == remote_d else "★不一致")
            return 0 if local_d == remote_d else 1

        result = send_report(args.task_id, dry_run=args.dry_run)
    except ReportError as exc:
        print(f"[task-report] {exc}", file=sys.stderr)
        return 1
    except F.BundleError as exc:
        print(f"[task-report] {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print("[task-report] 検査のみ（送信していない）")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
