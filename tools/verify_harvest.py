#!/usr/bin/env python3
"""収穫の前後を **一つの命令で** 比較し、変わってよいものと変わってはならないものを分けて判定する。

なぜ要るか
----------
契約は長らく「既存行の変更が零件」を収穫の条件に置いていた。この条件が成立するのは
**run 単位の索引 `index.csv` だけ**である。集約表は、既存の群に新しい run が加われば
`n_runs` も `*_mean` も `*_pstd` も必ず書き換わる（実測: `n_runs>1` の群が 277 中 206）。
正常な収穫でも必ず失敗するため、契約は毎回 escalate するか手で目視するしかなかった。

判定の分け方
------------
  run 単位（index.csv）      : 追加のみ。削除零・既存行の変更零
  集約表（experiments,
          verdicts, per_class）: **既存の群の「判定に使う列」が不変**であること。
                                 集計値の列（mean/pstd/min/max/n など）は変わってよい

判定に使う列は `same_sign` `verdict` `agree` `reason` `n_seeds` を名前に含む列とする。
`experiments.csv` では `verdict_10_1` `delta_same_sign_<metric>` `delta_n_seeds_<metric>`
などが、`verdicts.csv` では同名の列がこれに当たる。**一覧を手で持たない。**
表が列を増やしても規則が古くならないためである。

使い方
------
    python tools/verify_harvest.py                     # 起点は HEAD（収穫前の commit）
    python tools/verify_harvest.py --base <commit>
    python tools/verify_harvest.py --json

終了コード: 判定に反しなければ 0、一つでも反すれば 1。
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "HEAD"

# 表ごとの主キー。**行の同一性はこれで決める。**
TABLES = {
    "runindex/index.csv": ("ledger_key",),
    "runindex/experiments.csv": ("experiment_id",),
    "runindex/verdicts.csv": ("experiment_id", "metric"),
    "runindex/per_class.csv": ("ledger_key", "per_class_kind", "per_class_metric", "class_name"),
}
# run 単位の表。既存行の変更を許さない。
RUN_LEVEL = ("runindex/index.csv",)

# 判定に使う列を見分ける手がかり。名前に含まれれば判定列とみなす。
JUDGEMENT_MARKERS = ("same_sign", "verdict", "agree", "reason", "n_seeds")


def is_judgement_column(name: str) -> bool:
    return any(marker in name for marker in JUDGEMENT_MARKERS)


def _git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], check=False, capture_output=True,
                          text=True, cwd=REPO_ROOT)


def read_at(base: str, path: str) -> list[dict[str, str]] | None:
    """起点の版の表を読む。起点に無ければ None（＝表そのものが新規）。"""
    shown = _git(["show", f"{base}:{path}"])
    if shown.returncode != 0:
        return None
    return list(csv.DictReader(io.StringIO(shown.stdout)))


def read_now(path: str) -> list[dict[str, str]] | None:
    full = REPO_ROOT / path
    if not full.exists():
        return None
    with open(full, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def keyed(rows: list[dict[str, str]], key: tuple[str, ...]) -> dict[tuple[str, ...], dict[str, str]]:
    return {tuple(row.get(k, "") for k in key): row for row in rows}


def compare(path: str, key: tuple[str, ...], before: list[dict[str, str]],
            after: list[dict[str, str]]) -> dict:
    """一つの表を比べる。**差分の全量を返す。** 判定は呼び手が行う。"""
    b, a = keyed(before, key), keyed(after, key)
    added = sorted(set(a) - set(b))
    removed = sorted(set(b) - set(a))

    changed_any: list[dict] = []
    changed_judgement: list[dict] = []
    for k in sorted(set(a) & set(b)):
        diffs = {
            col: {"before": b[k].get(col, ""), "after": a[k].get(col, "")}
            for col in sorted(set(b[k]) | set(a[k]))
            if b[k].get(col, "") != a[k].get(col, "")
        }
        if not diffs:
            continue
        entry = {"key": list(k), "columns": diffs}
        changed_any.append(entry)
        judged = {c: v for c, v in diffs.items() if is_judgement_column(c)}
        if judged:
            changed_judgement.append({"key": list(k), "columns": judged})

    run_level = path in RUN_LEVEL
    if run_level:
        ok = not removed and not changed_any
        rule = "run 単位: 追加のみ（削除零・既存行の変更零）"
    else:
        ok = not removed and not changed_judgement
        rule = "集約表: 削除零かつ既存の群の判定列が不変（集計値の列は変わってよい）"

    return {
        "table": path, "key": list(key), "rule": rule, "pass": ok,
        "rows_before": len(before), "rows_after": len(after),
        "added": [list(k) for k in added],
        "removed": [list(k) for k in removed],
        "changed_rows": len(changed_any),
        "changed_judgement": changed_judgement,
        "changed_all": changed_any,
    }


def verify(base: str) -> dict:
    results, errors = [], []
    for path, key in TABLES.items():
        before, after = read_at(base, path), read_now(path)
        if before is None and after is None:
            errors.append(f"{path} が起点にも手元にも無い")
            continue
        if after is None:
            errors.append(f"{path} が手元に無い（削除されている）")
            continue
        if before is None:
            results.append({"table": path, "key": list(key),
                            "rule": "起点に無い新規の表", "pass": True,
                            "rows_before": 0, "rows_after": len(after),
                            "added": [], "removed": [], "changed_rows": 0,
                            "changed_judgement": [], "changed_all": []})
            continue
        results.append(compare(path, key, before, after))
    ok = not errors and all(r["pass"] for r in results)
    return {"status": "pass" if ok else "fail", "base": base,
            "tables": results, "errors": errors}


def render(payload: dict) -> str:
    lines = [f"収穫の前後比較 — 起点 {payload['base']}", ""]
    for r in payload["tables"]:
        mark = "PASS" if r["pass"] else "FAIL"
        lines.append(f"{mark} {r['table']}  {r['rows_before']} -> {r['rows_after']} 行")
        lines.append(f"     規則: {r['rule']}")
        lines.append(f"     追加 {len(r['added'])} / 削除 {len(r['removed'])} / 既存行の変更 {r['changed_rows']}")
        if r["removed"]:
            lines.append(f"     削除された行: {r['removed']}")
        if r["changed_judgement"]:
            lines.append(f"     判定列が変わった行 {len(r['changed_judgement'])} 件:")
            for entry in r["changed_judgement"]:
                for col, v in entry["columns"].items():
                    lines.append(f"       {entry['key']} {col}: {v['before']!r} -> {v['after']!r}")
        elif r["changed_rows"] and r["table"] not in RUN_LEVEL:
            lines.append("     判定列の変更なし（集計値の列のみ変わった）")
        if r["table"] in RUN_LEVEL and r["changed_all"]:
            lines.append(f"     既存行が変わった行 {len(r['changed_all'])} 件:")
            for entry in r["changed_all"]:
                for col, v in entry["columns"].items():
                    lines.append(f"       {entry['key']} {col}: {v['before']!r} -> {v['after']!r}")
        lines.append("")
    for e in payload["errors"]:
        lines.append(f"ERROR {e}")
    lines.append(f"RESULT: {payload['status'].upper()}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="収穫の前後を比較する。")
    parser.add_argument("--base", default=DEFAULT_BASE,
                        help=f"収穫前の版。既定は {DEFAULT_BASE}。")
    parser.add_argument("--json", action="store_true", help="機械可読で出す。")
    args = parser.parse_args(argv)

    payload = verify(args.base)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True) if args.json
          else render(payload))
    return 0 if payload["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
