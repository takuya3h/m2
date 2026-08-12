#!/usr/bin/env python
"""マスター昇格ドラフタ（auto_logging_implementation.md §5.6・Milestone D）。

直近 N 日間の意思決定・主要 run を集約し、**ドラフトのみ**生成する:
  (a) M2 研究計画 §0 「変更履歴」エントリ草案
  (b) 「進捗反映スナップショット」page への追記ブロック草案

**マスター §0 を無人で書かない**（人間がレビューしてマージ）。出力は stdout と
オプションで `--write-snapshot` 指定時のみ Notion 進捗反映スナップショット page に追記。

実行:
  python scripts/draft_master_update.py --dry-run                  # stdout に草案表示
  python scripts/draft_master_update.py --days 7                   # 直近 7 日
  python scripts/draft_master_update.py --write-snapshot           # 進捗 page へ追記（要 NOTION_API_KEY）

設計:
- 数値は実測値のみ（捏造禁止）。`experiments/**/metrics.json` から実 mAP/acc を読む
- 意思決定は Notion 意思決定ログ DB を read-only で query（最新 N 件）
- §0 草案はテンプレ通り。**本文の散文は人間が書く**（推測で埋めない）
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

DAYS_DEFAULT = 7


def _recent_run_dirs(since: dt.date) -> list[Path]:
    """直近 since 以降に mtime 更新された run dir を返す。"""
    dirs: list[Path] = []
    for sub in ("baselines", "transfer", "phase0", "phase1", "final"):
        base = PROJ / "experiments" / sub
        if not base.is_dir():
            continue
        for d in base.iterdir():
            if not d.is_dir():
                continue
            if dt.date.fromtimestamp(d.stat().st_mtime) >= since:
                dirs.append(d)
    return sorted(dirs, key=lambda p: p.stat().st_mtime)


def _summarize_run(run_dir: Path) -> dict:
    """run dir から主要数値と config を抽出（無ければ None / 空欄）。"""
    metrics_path = run_dir / "metrics.json"
    summary: dict = {
        "name": run_dir.name,
        "mtime": dt.date.fromtimestamp(run_dir.stat().st_mtime).isoformat(),
    }
    if metrics_path.exists():
        try:
            m = json.loads(metrics_path.read_text())
            for k in ("mAP", "AP_50", "AP_rare", "phase_accuracy", "phase_macro_f1"):
                if k in m:
                    summary[k] = m[k]
        except Exception:  # noqa: BLE001
            pass
    return summary


def _recent_decisions(since: dt.date, limit: int = 20) -> list[dict]:
    """Notion 意思決定ログ DB から直近 since 以降のエントリを取得（fail-open）。"""
    api_key = os.environ.get("NOTION_API_KEY", "").strip()
    if not api_key:
        return []
    try:
        import requests
        import yaml

        cfg = yaml.safe_load((PROJ / "configs" / "notion.yaml").read_text())
        db_id = cfg["databases"]["decision_log"]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
        }
        body = {
            "filter": {
                "property": "Date",
                "date": {"on_or_after": since.isoformat()},
            },
            "sorts": [{"property": "Date", "direction": "descending"}],
            "page_size": limit,
        }
        r = requests.post(
            f"https://api.notion.com/v1/databases/{db_id}/query",
            headers=headers,
            json=body,
            timeout=30,
        )
        if r.status_code != 200:
            return []
        out: list[dict] = []
        for p in r.json().get("results", []):
            props = p.get("properties", {})
            name_arr = props.get("Name", {}).get("title", [])
            name = name_arr[0]["text"]["content"] if name_arr else "(no title)"
            status = (props.get("Status", {}).get("select") or {}).get("name", "")
            impact = (props.get("Impact", {}).get("select") or {}).get("name", "")
            date_val = (props.get("Date", {}).get("date") or {}).get("start", "")
            out.append(
                {
                    "name": name,
                    "status": status,
                    "impact": impact,
                    "date": date_val,
                    "id": p["id"],
                }
            )
        return out
    except Exception:  # noqa: BLE001
        return []


def build_master_diff(since: dt.date) -> str:
    """§0 「変更履歴」エントリ + 進捗スナップショット追記用ブロックをドラフト生成。"""
    today = dt.date.today()
    runs = _recent_run_dirs(since)
    decisions = _recent_decisions(since)

    lines: list[str] = []
    lines.append(f"# {today.isoformat()} マスター昇格ドラフト（人間レビュー後マージ）")
    lines.append("")
    lines.append("## §0 変更履歴エントリ草案（マスター冒頭に追記）")
    lines.append("")
    lines.append(
        f"- **{today.isoformat()}** : 直近 {(today - since).days} 日間で "
        f"{len(decisions)} 件の意思決定 / {len(runs)} 件の run を反映"
    )
    lines.append("")
    lines.append("## 進捗反映スナップショット page への追記ブロック草案")
    lines.append("")
    lines.append(
        f"### {today.isoformat()} スナップショット（since={since.isoformat()}）"
    )
    lines.append("")
    if decisions:
        lines.append("#### 意思決定（直近）")
        for d in decisions[:10]:
            lines.append(
                f"- [{d['date']}] **{d['name']}** ({d['status']}, impact={d['impact']})"
            )
        lines.append("")
    if runs:
        lines.append("#### 主要 run（実測値・捏造ゼロ）")
        for r in runs[:20]:
            s = _summarize_run(r)
            line = f"- `{s['name']}` ({s['mtime']})"
            metrics = [f"{k}={v}" for k, v in s.items() if k not in ("name", "mtime")]
            if metrics:
                line += " — " + ", ".join(metrics)
            lines.append(line)
        lines.append("")
    lines.append("---")
    lines.append(
        "**マージ手順**: 上記 §0 エントリを M2研究計画マスターページ §0 冒頭に **手動で**追記する。"
    )
    lines.append("散文の追加は人間がレビューしてから（自動マージしない・§2 鉄則）。")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="マスター昇格ドラフタ（無人マージしない）")
    ap.add_argument(
        "--days", type=int, default=DAYS_DEFAULT, help="直近何日間を対象にするか"
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="stdout に表示するだけ（既定で安全）。--write-snapshot 指定時は対比的に false 化",
    )
    ap.add_argument(
        "--write-snapshot",
        action="store_true",
        help="進捗反映スナップショット page へ追記（REST, 未指定なら表示のみ）",
    )
    args = ap.parse_args()
    since = dt.date.today() - dt.timedelta(days=args.days)
    draft = build_master_diff(since)
    print(draft)

    if args.write_snapshot:
        api_key = os.environ.get("NOTION_API_KEY", "").strip()
        if not api_key:
            print("\n[draft] NOTION_API_KEY 未設定 → 追記 skip（fail-open）")
            return
        try:
            import requests
            import yaml

            cfg = yaml.safe_load((PROJ / "configs" / "notion.yaml").read_text())
            page_id = (
                cfg["pages"].get("progress_snapshot")
                or "388ee4d4-7777-81da-a260-e764de73bfb0"
            )
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
            }
            # 進捗 page の children に paragraph block を append
            blocks = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {"type": "text", "text": {"content": draft[:1900]}}
                        ],
                    },
                }
            ]
            r = requests.patch(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=headers,
                json={"children": blocks},
                timeout=30,
            )
            if r.status_code == 200:
                print(
                    f"\n[draft] 進捗スナップショット page へ追記成功 (page_id={page_id})"
                )
            else:
                print(f"\n[draft] 追記失敗 HTTP {r.status_code}: {r.text[:200]}")
        except Exception as exc:  # noqa: BLE001
            print(f"\n[draft] 追記例外 {exc} → fail-open")


if __name__ == "__main__":
    main()
