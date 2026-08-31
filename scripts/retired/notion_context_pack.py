#!/usr/bin/env python
"""指定 step の「コンテキストパック」を Notion 運用ハブから組成する（REST・本体 .venv）。

M2研究計画（マスター長文）を毎回読まずにコンテキストを削減するための入口。指定 step に
関連する **意思決定ログ / 失敗知見・教訓 / プロンプトライブラリ / 実験手順書** の行だけを
台帳から引き、compact なテキストに整形して出力する（運用ハブ §運用ループ 2 に対応）。

narrative な「現在の研究状態」ページは Claude が MCP で直接 fetch する（CLAUDE.md 参照）。
本スクリプトは **構造化 DB 行**の抽出に特化（REST・MCP 不要・headless 可）。

認証: NOTION_API_KEY（必須）。DB ID は configs/notion.yaml。

実行:
  set -a; source .env; set +a
  .venv/bin/python scripts/notion_context_pack.py --step S0
  .venv/bin/python scripts/notion_context_pack.py --step B --limit 8
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.utils.notion_ops import _db_id, _headers  # noqa: E402

_API = "https://api.notion.com/v1"


def _plain(prop: dict) -> str:
    """Notion property 値 → プレーン文字列。"""
    if not isinstance(prop, dict):
        return ""
    t = prop.get("type")
    if t == "title":
        return "".join(x.get("plain_text", "") for x in prop.get("title", []))
    if t == "rich_text":
        return "".join(x.get("plain_text", "") for x in prop.get("rich_text", []))
    if t == "select":
        return (prop.get("select") or {}).get("name", "") if prop.get("select") else ""
    if t == "multi_select":
        return "/".join(o.get("name", "") for o in prop.get("multi_select", []))
    if t == "url":
        return prop.get("url") or ""
    if t == "date":
        return (prop.get("date") or {}).get("start", "") if prop.get("date") else ""
    return ""


def _query(db_key: str, step: str, step_prop: str, multi: bool, limit: int) -> list[dict]:
    headers = _headers()
    db_id = _db_id(db_key)
    if headers is None or not db_id:
        return []
    import requests
    cond = ({"property": step_prop, "multi_select": {"contains": step}} if multi
            else {"property": step_prop, "select": {"equals": step}})
    try:
        r = requests.post(f"{_API}/databases/{db_id}/query", headers=headers,
                          json={"filter": cond, "page_size": limit}, timeout=30)
        if r.status_code != 200:
            print(f"[ctx] {db_key} query失敗: {r.status_code} {r.text[:120]}")
            return []
        return r.json().get("results", [])
    except Exception as exc:  # noqa: BLE001
        print(f"[ctx] {db_key} skip: {exc}")
        return []


def _show(title: str, rows: list[dict], fields: list[str]):
    print(f"\n=== {title} ({len(rows)}) ===")
    for pg in rows:
        p = pg.get("properties", {})
        name = _plain(p.get("Name", {})) or "(no name)"
        extras = " | ".join(f"{f}={_plain(p.get(f, {}))}" for f in fields if _plain(p.get(f, {})))
        print(f"- {name}" + (f"  [{extras}]" if extras else ""))


def main():
    ap = argparse.ArgumentParser(description="Notion 運用ハブから step 別コンテキストパックを組成。")
    ap.add_argument("--step", required=True, help="例 S0 / S4 / B（Related Steps に含まれる行を抽出）")
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    if _headers() is None:
        print("[ctx] NOTION_API_KEY 未設定。`set -a; source .env; set +a` 後に再実行。")
        return
    print(f"# コンテキストパック step={args.step}（構造化DB行のみ・narrativeは現在の研究状態をMCPで）")
    _show("意思決定ログ", _query("decision_log", args.step, "Related Steps", True, args.limit),
          ["Type", "Impact", "Status", "Rationale"])
    _show("失敗知見・教訓", _query("lessons", args.step, "Related Steps", True, args.limit),
          ["Severity", "Category", "Status", "Prevention"])
    _show("プロンプトライブラリ", _query("prompt_library", args.step, "Related Step", False, args.limit),
          ["Target", "Status", "Prompt File"])
    _show("実験手順書", _query("procedure_docs", args.step, "Related Steps", True, args.limit),
          ["Status"])
    print("\n[ctx] 次: 現在の研究状態ページを MCP fetch（configs/notion.yaml pages.current_state）。")


if __name__ == "__main__":
    main()
