#!/usr/bin/env python
"""Notion の旧頁の見出し抽出と旧データベースの保全 export（読み取り専用）。

契約 T-2026-08-31-notion-legacy-toc-and-export の実装。**Notion へ一切書かない。**
使う endpoint は次の三つだけで、いずれも読み取りである
（`databases/query` は POST だが読み取りであり契約 §4 の禁止 1 が明示的に許す）。

    GET  /v1/blocks/{id}/children      頁のブロック（見出し抽出・本文取得）
    GET  /v1/databases/{id}            DB の retrieve（到達性）
    POST /v1/databases/{id}/query      DB の全行（頁送り）

既存の作法を踏襲する（`tools/fetch_task.py` と `src/egosurgery/utils/notion_logger.py`）:
API 版 2022-06-28 / urllib（新規パッケージを入れない）/ `start_cursor` と `has_more` の頁送り。
429 は `Retry-After` を見て待ち、回数を数えて返す。

    python docs/archive/notion/export_notion.py toc   --id <page_id> --out <path> [--page-size N]
    python docs/archive/notion/export_notion.py db    --key <KEY> --id <db_id> --outdir <dir> [--page-size N]
    python docs/archive/notion/export_notion.py probe --kind page|database --id <id>
    python docs/archive/notion/export_notion.py toc-fixture --in <json> --out <path>
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAX_RETRY = 5

HEADING = {"heading_1": "H1", "heading_2": "H2", "heading_3": "H3"}
# 子を持ちうる容器。ここは降りる。child_page / child_database へは降りない（題だけ記録）。
STOP_AT = {"child_page", "child_database"}

_retries = 0


def _headers() -> dict:
    key = os.environ.get("NOTION_API_KEY", "").strip()
    if not key:
        raise SystemExit("NOTION_API_KEY が未設定。source scripts/load_env.sh を先に実行する")
    return {"Authorization": f"Bearer {key}", "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"}


def call(method: str, url: str, body: dict | None = None) -> dict:
    """1 回の呼び出し。**HTTP を触るのはこの関数だけである。**

    資格情報は見出しにのみ載せ、例外にも応答にも載せない。
    """
    global _retries
    for attempt in range(MAX_RETRY):
        req = urllib.request.Request(  # noqa: S310
            url, method=method,
            data=json.dumps(body).encode() if body is not None else None,
            headers=_headers(),
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as res:
                return json.loads(res.read())
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < MAX_RETRY - 1:
                wait = float(exc.headers.get("Retry-After", "1") or 1)
                _retries += 1
                time.sleep(wait)
                continue
            detail = (exc.read() or b"").decode("utf-8", "replace")[:200]
            raise NotionError(f"HTTP {exc.code} {detail}") from exc
        except OSError as exc:
            # 読み取りタイムアウトは頁の大きさを小さくすると起きやすい（呼び出し回数が増える）。
            # 429 と同じく待って再試行する。回数は _retries に数える。
            if attempt < MAX_RETRY - 1:
                _retries += 1
                time.sleep(2 * (attempt + 1))
                continue
            raise NotionError(f"到達不能: {exc}") from exc
    raise NotionError("再試行の上限に達した")


class NotionError(RuntimeError):
    pass


def children(block_id: str, page_size: int = 100):
    """ブロックの子を頁送りで全件返す。"""
    cursor = None
    while True:
        url = f"{API_BASE}/blocks/{block_id}/children?page_size={page_size}"
        if cursor:
            url += f"&start_cursor={cursor}"
        chunk = call("GET", url)
        yield from chunk.get("results", [])
        if not chunk.get("has_more"):
            return
        cursor = chunk.get("next_cursor")


def rich_text(block: dict, kind: str) -> str:
    parts = block.get(kind, {}).get("rich_text", []) or []
    return "".join(p.get("plain_text", "") for p in parts).strip()


def walk_toc(block_id: str, page_size: int, depth: int = 0, out: list | None = None) -> list:
    """見出しと子頁・子 DB だけを集める。**本文の段落は集めない。**

    子を持つ容器（toggle / column / callout など）は降りる。
    `child_page` と `child_database` へは降りず、題と id だけ記録する。
    """
    if out is None:
        out = []
    for b in children(block_id, page_size):
        t = b.get("type", "")
        if t in HEADING:
            out.append({"depth": depth, "kind": HEADING[t], "text": rich_text(b, t), "id": b["id"]})
        elif t == "child_page":
            out.append({"depth": depth, "kind": "PAGE",
                        "text": b.get("child_page", {}).get("title", ""), "id": b["id"]})
            continue
        elif t == "child_database":
            out.append({"depth": depth, "kind": "DB",
                        "text": b.get("child_database", {}).get("title", ""), "id": b["id"]})
            continue
        if b.get("has_children") and t not in STOP_AT:
            # 見出し自身が toggle 化されている場合、その内側も見出しを持ちうる
            walk_toc(b["id"], page_size, depth + (1 if t in HEADING else 0), out)
    return out


def write_toc(rows: list, path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(f"{'  ' * r['depth']}{r['kind']}\t{r['text']}\t{r['id']}\n")


def flatten_prop(p: dict):
    """プロパティ 1 個を平坦化する。複合値は JSON 文字列にする。"""
    t = p.get("type", "")
    v = p.get(t)
    if t in ("title", "rich_text"):
        return "".join(x.get("plain_text", "") for x in (v or []))
    if t in ("number", "checkbox", "url", "email", "phone_number", "created_time",
             "last_edited_time"):
        return v
    if t == "select":
        return (v or {}).get("name", "")
    if t == "status":
        return (v or {}).get("name", "")
    if t == "multi_select":
        return ",".join(x.get("name", "") for x in (v or []))
    if t == "date":
        return json.dumps(v, ensure_ascii=False) if v else ""
    if t == "people":
        # 利用者オブジェクトは id だけに落とす（名前・連絡先を写さない）
        return ",".join(x.get("id", "") for x in (v or []))
    return json.dumps(v, ensure_ascii=False, default=str)


def body_blocks(page_id: str, page_size: int) -> list:
    """行の本文ブロック。子を持つ容器は降りる。child_page/child_database へは降りない。"""
    out = []

    def rec(bid: str, depth: int) -> None:
        for b in children(bid, page_size):
            t = b.get("type", "")
            out.append({"depth": depth, "type": t, "id": b["id"],
                        "text": rich_text(b, t) if isinstance(b.get(t), dict) else ""})
            if b.get("has_children") and t not in STOP_AT:
                rec(b["id"], depth + 1)

    rec(page_id, 0)
    return out


def export_db(key: str, db_id: str, outdir: str, page_size: int) -> dict:
    os.makedirs(outdir, exist_ok=True)
    rows, cursor = [], None
    while True:
        body = {"page_size": page_size}
        if cursor:
            body["start_cursor"] = cursor
        chunk = call("POST", f"{API_BASE}/databases/{db_id}/query", body)
        rows.extend(chunk.get("results", []))
        if not chunk.get("has_more"):
            break
        cursor = chunk.get("next_cursor")

    with open(f"{outdir}/raw.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n")

    cols: list[str] = []
    flat = []
    for r in rows:
        d = {"__id": r.get("id", ""), "__created_time": r.get("created_time", ""),
             "__last_edited_time": r.get("last_edited_time", "")}
        for name, p in (r.get("properties") or {}).items():
            d[name] = flatten_prop(p)
        flat.append(d)
        for k in d:
            if k not in cols:
                cols.append(k)
    with open(f"{outdir}/properties.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for d in flat:
            w.writerow(d)

    with open(f"{outdir}/bodies.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            blocks = body_blocks(r["id"], page_size)
            f.write(json.dumps({"page_id": r["id"], "n_blocks": len(blocks), "blocks": blocks},
                               ensure_ascii=False, sort_keys=True) + "\n")
    return {"key": key, "n_items": len(rows), "retries": _retries}


def main() -> None:
    ap = argparse.ArgumentParser(description="Notion 旧頁・旧 DB の読み取り専用 export")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("toc")
    p.add_argument("--id", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--page-size", type=int, default=100)

    p = sub.add_parser("db")
    p.add_argument("--key", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--outdir", required=True)
    p.add_argument("--page-size", type=int, default=100)

    p = sub.add_parser("probe")
    p.add_argument("--kind", choices=["page", "database"], required=True)
    p.add_argument("--id", required=True)

    p = sub.add_parser("toc-fixture")
    p.add_argument("--in", dest="src", required=True)
    p.add_argument("--out", required=True)

    a = ap.parse_args()
    if a.cmd == "toc":
        rows = walk_toc(a.id, a.page_size)
        write_toc(rows, a.out)
        print(json.dumps({"rows": len(rows), "retries": _retries}, ensure_ascii=False))
    elif a.cmd == "db":
        print(json.dumps(export_db(a.key, a.id, a.outdir, a.page_size), ensure_ascii=False))
    elif a.cmd == "probe":
        try:
            if a.kind == "database":
                r = call("GET", f"{API_BASE}/databases/{a.id}")
            else:
                r = call("GET", f"{API_BASE}/blocks/{a.id}/children?page_size=1")
            print(json.dumps({"status": "reachable", "object": r.get("object", ""),
                              "last_edited_time": r.get("last_edited_time", "")}, ensure_ascii=False))
        except NotionError as exc:
            print(json.dumps({"status": "unreachable", "error": str(exc)}, ensure_ascii=False))
            sys.exit(1)
    elif a.cmd == "toc-fixture":
        # ローカル JSON（children 応答の写し）に対して同じ抽出器を当てる対照用。
        fixture = json.loads(open(a.src, encoding="utf-8").read())
        rows = walk_fixture(fixture)
        write_toc(rows, a.out)
        print(json.dumps({"rows": len(rows)}, ensure_ascii=False))


def walk_fixture(nodes: list, depth: int = 0, out: list | None = None) -> list:
    """フィクスチャ用。`children` を呼ばず、入れ子は `__children` から読む。

    **判定の対象は walk_toc と同じ規則である**（見出しは拾う・段落は拾わない・
    child_page と child_database へは降りない）。
    """
    if out is None:
        out = []
    for b in nodes:
        t = b.get("type", "")
        if t in HEADING:
            out.append({"depth": depth, "kind": HEADING[t], "text": rich_text(b, t), "id": b["id"]})
        elif t == "child_page":
            out.append({"depth": depth, "kind": "PAGE",
                        "text": b.get("child_page", {}).get("title", ""), "id": b["id"]})
            continue
        elif t == "child_database":
            out.append({"depth": depth, "kind": "DB",
                        "text": b.get("child_database", {}).get("title", ""), "id": b["id"]})
            continue
        kids = b.get("__children")
        if kids and t not in STOP_AT:
            walk_fixture(kids, depth + (1 if t in HEADING else 0), out)
    return out


if __name__ == "__main__":
    main()
