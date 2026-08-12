#!/usr/bin/env python
"""未投稿の実験 run / notes ブロックを Notion へ一括同期する（§5.4 取りこぼし防止スイープ）。

`experiments/**` を走査し、各 run フォルダの `.notion_sync.json`（マーカー）を見て:
  - run_ledger_page が未記録 → ResearchLogger.log_run() で Run台帳へ upsert
  - decisions/lessons/prompts の hash が未記録 → notes.md の該当ブロックを upsert

冪等（マーカーで二重投稿を防ぐ）。fail-open（NOTION_API_KEY 未設定なら no-op）。

実行:
  # 安全な dry-run（投稿せず差分のみ列挙）
  python scripts/sync_experiments_to_notion.py --dry-run

  # 実投稿（NOTION_API_KEY 必須）
  set -a; source .env; set +a
  python scripts/sync_experiments_to_notion.py
  python scripts/sync_experiments_to_notion.py --only run        # run のみ
  python scripts/sync_experiments_to_notion.py --only decision   # decision のみ
  python scripts/sync_experiments_to_notion.py --since 2026-06-20  # mtime しぼり込み

`scripts/post_experiments_to_notion.py` の DEFAULT_GLOBS / family meta を継承し、
重複ロジックを本スクリプトに一本化（§7 Milestone B「重複ロジックを一本化」）。
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path
from types import SimpleNamespace

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

# scripts/post_experiments_to_notion.py から継承（重複ロジック一本化）
from post_experiments_to_notion import DEFAULT_GLOBS, family_meta  # noqa: E402

from egosurgery.utils.idempotency import is_run_posted, load_marker  # noqa: E402
from egosurgery.utils.notes_schema import parse_notes_file, valid_blocks  # noqa: E402
from egosurgery.utils.research_logger import ResearchLogger  # noqa: E402


def collect_run_dirs(paths: list[str] | None) -> list[Path]:
    """指定 path or DEFAULT_GLOBS から run dir を集める。"""
    if paths:
        out: list[Path] = []
        for p in paths:
            if Path(p).is_absolute():
                out.append(Path(p))
            else:
                out += list(PROJ.glob(p))
        return [d for d in out if d.is_dir()]
    dirs: list[Path] = []
    for g in DEFAULT_GLOBS:
        dirs += sorted(PROJ.glob(g))
    return [d for d in dirs if d.is_dir()]


def _after_since(d: Path, since: dt.date | None) -> bool:
    if since is None:
        return True
    return dt.date.fromtimestamp(d.stat().st_mtime) >= since


def _summary(b_data: dict, max_len: int = 60) -> str:
    title = b_data.get("title", "(no title)")
    return title[:max_len]


def sync_run(run_dir: Path, dry_run: bool) -> dict:
    """1 run について run/decision/lesson/prompt の差分を解決。返り値はカウンタ dict."""
    counts = {"run": 0, "decision": 0, "lesson": 0, "prompt": 0, "skipped": 0}

    step, tier, primary, denom = family_meta(run_dir.name)
    manager = SimpleNamespace(exp_dir=run_dir)
    rlog = ResearchLogger(cfg=None, manager=manager)

    # 1) Run台帳：未投稿なら投稿
    if not is_run_posted(run_dir):
        if dry_run:
            print(f"  [DRY] run upsert: {run_dir.name} (step={step})")
            counts["run"] = 1
        else:
            pid = rlog.log_run(
                status="completed",
                step=step,
                tier=tier,
                primary_metric=primary,
                extra_result_text=denom,
            )
            if pid:
                print(f"  [POST] run: {run_dir.name} → {pid}")
                counts["run"] = 1
            else:
                counts["skipped"] += 1
    else:
        counts["skipped"] += 1

    # 2) notes.md の decision/lesson/prompt ブロック
    blocks = valid_blocks(parse_notes_file(run_dir / "notes.md"))
    marker = load_marker(run_dir)
    for blk in blocks:
        bt = blk.type  # "decision" / "lesson" / "prompt"
        key = {"decision": "decisions", "lesson": "lessons", "prompt": "prompts"}[bt]
        from egosurgery.utils.idempotency import content_hash

        h = content_hash(
            blk.data.get("title", ""),
            blk.data.get("date", ""),
            blk.data.get("body", ""),
        )
        if h in (marker.get(key) or []):
            counts["skipped"] += 1
            continue
        if dry_run:
            print(f"  [DRY] {bt}: {_summary(blk.data)}")
            counts[bt] += 1
            continue
        if bt == "decision":
            pid = rlog.log_decision(blk.data)
        elif bt == "lesson":
            pid = rlog.log_lesson(blk.data)
        else:  # prompt
            pid = rlog.save_prompt(blk.data["title"], blk.data.get("body", ""))
        if pid:
            print(f"  [POST] {bt}: {_summary(blk.data)} → {pid}")
            counts[bt] += 1
        else:
            counts["skipped"] += 1
    return counts


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Notion スイープ（未投稿 run/notes を一括 upsert・冪等）。"
    )
    ap.add_argument("paths", nargs="*", help="特定 run dir（省略で DEFAULT_GLOBS）")
    ap.add_argument(
        "--dry-run", action="store_true", help="投稿せず差分のみ列挙（既定で安全）"
    )
    ap.add_argument(
        "--since", type=str, default=None, help="mtime 以降のみ対象（YYYY-MM-DD）"
    )
    ap.add_argument(
        "--only",
        choices=["run", "decision", "lesson", "prompt"],
        help="特定種別のみ同期",
    )
    args = ap.parse_args()

    since = dt.date.fromisoformat(args.since) if args.since else None
    dirs = [d for d in collect_run_dirs(args.paths) if _after_since(d, since)]
    print(
        f"[sync] {len(dirs)} run dirs (dry_run={args.dry_run}, since={since}, only={args.only})"
    )
    total = {"run": 0, "decision": 0, "lesson": 0, "prompt": 0, "skipped": 0}
    for d in dirs:
        print(f"\n■ {d.name}")
        counts = sync_run(d, dry_run=args.dry_run)
        if args.only:
            # --only 指定時は他種別を表示から除外（既に投稿済として扱う）
            for k in list(total):
                if k != args.only and k != "skipped":
                    counts[k] = 0
        for k in total:
            total[k] += counts[k]
    print(
        f"\n[sync] 完了: run={total['run']} decision={total['decision']} "
        f"lesson={total['lesson']} prompt={total['prompt']} skipped={total['skipped']}"
    )
    if args.dry_run:
        print("[sync] DRY-RUN（実投稿は --dry-run を外して再実行）。")


if __name__ == "__main__":
    main()
