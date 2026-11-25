"""完了判定 i・j: 読んだファイルの一覧（reads.jsonl）の検査（非公式 T-2026-11-22-dtower-class-error-breakdown）。

    .venv/bin/python .../check_reads.py [--reads <一覧>] [--inject <名前>] [--rehash] [--out <json>]

- i: 一覧の中の test の予測と注釈（eval_test.*、instances_test.json、per_class_ap_test.json、test_access.json）の件数。
  --inject は一覧の写しに名前を一つ足して数える（空振りでないことの確認）
- j: --rehash で、一覧の各ファイルの今の sha256 を、一覧に最初に記録した sha256 と比べる
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def test_entries(rows: list[dict]) -> list[str]:
    """検出の test の予測と注釈。0 件でなければならない。"""
    return sorted({r["path"] for r in rows if C.TEST_FILE.match(Path(r["path"]).name)})


def manifest_test_reads(rows: list[dict]) -> list[str]:
    """工程のマニフェストの test.json を読んだ目的（利用者の判断 2026-11-22 で Fold B〜E の (e) にだけ許した）。"""
    return sorted({r.get("purpose", "") for r in rows
                   if Path(r["path"]).name == "test.json" and Path(r["path"]).parent == C.MANIFEST.resolve()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reads", default=str(C.READS))
    ap.add_argument("--inject", default=None)
    ap.add_argument("--rehash", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    rows = [json.loads(x) for x in Path(a.reads).read_text().splitlines() if x.strip()]
    if a.inject:
        rows = rows + [{"path": a.inject, "sha256": "", "kind": "injected"}]
    first = {}
    for r in rows:
        first.setdefault(r["path"], r)
    mt = manifest_test_reads(rows)
    out = {"rows": len(rows), "files": len(first), "test_files": test_entries(rows),
           "manifest_test_json_purposes": mt, "manifest_test_json_for_fold_A": [p for p in mt if "Fold A" in p],
           "by_kind": {k: sum(1 for r in first.values() if r.get("kind") == k) for k in sorted({r.get("kind") for r in first.values()})}}
    if a.rehash:
        changed = [p for p, r in first.items() if r.get("kind") != "injected" and C.sha256(p) != r["sha256"]]
        out["rehash_changed"] = changed
        # 同じ経路を二度以上読んだときに sha256 が食い違っていないか
        out["inconsistent_within_log"] = sorted({r["path"] for r in rows if r.get("sha256") and r["sha256"] != first[r["path"]]["sha256"]})
    if a.out:
        C.write_json(a.out, out)
    print(json.dumps({k: (v if k != "test_files" else v) for k, v in out.items()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
