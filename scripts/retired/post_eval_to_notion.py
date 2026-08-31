#!/usr/bin/env python
"""eval-only 再評価結果を Notion 実験Run台帳へ投稿する。

ExperimentManager を経由しない eval-only re-eval (mmdet test.py / detrex --eval-only /
accelerate test.py) の結果を、実験フォルダの存在なしに直接 Notion へ post する。

対応する log format:
  - mmdet3: 「test/bbox_mAP: 0.452 test/AP_rare: 0.535 ...」1行 kv (queue1)
  - mmdet2: 「OrderedDict([('bbox_mAP', 0.495), ...])」(queue2 Sensex)
  - detectron2: 「copypaste: 51.04,68.40,56.09,...」%-scale (queue3 AlignDETR)
  - accelerate: 「Average Precision (AP) @[...] = 0.506」複数行 (queue3 Rel-DETR)

Notion 側の同名 page は upsert (存在すれば properties を更新)。
NOTION_API_KEY / NOTION_DB_ID が未設定なら no-op。

CLI 例:
  python scripts/post_eval_to_notion.py \
    --name s0_001_maskdino_bbox_seed42_reeval_score_thr_0 \
    --step S0 --seed 42 --tier effort \
    --recipe "test-split score_thr=0.0 NMS-free (test_cfg.nms.iou_threshold=1.0)" \
    --log-path experiments/baselines/s0_001_maskdino_bbox_seed42/predictions/reeval_score_thr_0/eval.log \
    --log-format mmdet3
    (--server は省略可。NOTION_SERVER_OPTION → SERVERNAME → hostname の順で自動解決される。
     egosurgery.utils.server_name.resolve_server_name と同じ優先順位。)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import requests

PROJ = Path(__file__).resolve().parents[1]


# ---------------------------- log parsers ---------------------------------- #
def _parse_mmdet3(log: str) -> dict:
    """mmdet 3.x test.py 出力: 1 行の test/xxx: 数値 の羅列。"""
    out: dict = {}
    for key, alias in (
        ("test/bbox_mAP", "bbox_mAP"),
        ("test/bbox_mAP_50", "bbox_mAP_50"),
        ("test/bbox_mAP_75", "bbox_mAP_75"),
        ("test/AP_rare", "AP_rare"),
        ("test/AP_common", "AP_common"),
        ("test/tool_mAP", "tool_mAP"),
    ):
        m = re.search(rf"{re.escape(key)}: (-?\d+\.\d+)", log)
        if m:
            out[alias] = float(m.group(1))
    # per-class precision (mmdet3 では test/<Class>_precision)
    per_class: dict = {}
    for m in re.finditer(r"test/([A-Za-z ]+)_precision: (-?\d+\.\d+)", log):
        per_class[m.group(1).strip()] = float(m.group(2))
    if per_class:
        out["per_class"] = per_class
    return out


def _parse_mmdet2(log: str) -> dict:
    """mmdet 2.x + bbox 評価器出力: OrderedDict([('bbox_mAP', 0.495), ...])"""
    out: dict = {}
    m = re.search(r"OrderedDict\(\[(.*?)\]\)", log, re.S)
    if not m:
        return out
    body = m.group(1)
    for k, v in re.findall(r"'([A-Za-z_\d]+)',\s*(-?\d+\.\d+)", body):
        out[k] = float(v)
    return out


def _parse_detectron2(log: str) -> dict:
    """detrex/detectron2: copypaste: AP,AP50,AP75,APs,APm,APl (%-scale)"""
    out: dict = {}
    m = re.search(r"copypaste: (-?[\d.nan]+),(-?[\d.nan]+),(-?[\d.nan]+),", log)
    if m:
        # %-scale → 0-1
        def _to01(s: str) -> float:
            try:
                return float(s) / 100.0
            except ValueError:
                return float("nan")

        out["bbox_mAP"] = _to01(m.group(1))
        out["bbox_mAP_50"] = _to01(m.group(2))
        out["bbox_mAP_75"] = _to01(m.group(3))
    # per-class from OrderedDict('AP-<Class>', xx.x) — detrex 標準
    per_class: dict = {}
    for name, v in re.findall(r"'AP-([^']+)',\s*(-?\d+\.\d+)", log):
        try:
            per_class[name] = float(v) / 100.0
        except ValueError:
            pass
    if per_class:
        out["per_class"] = per_class
    return out


def _parse_accelerate(log: str) -> dict:
    """Rel-DETR test.py (accelerate): 「Average Precision (AP) @[ IoU=0.50:0.95 | area=all | maxDets=100 ] = 0.506」"""
    out: dict = {}
    m = re.search(
        r"Average Precision  \(AP\) @\[ IoU=0\.50:0\.95 \| area=\s*all \| maxDets= ?100 ?\] = (-?\d+\.\d+)",
        log,
    )
    if m:
        out["bbox_mAP"] = float(m.group(1))
    m = re.search(
        r"Average Precision  \(AP\) @\[ IoU=0\.50\s+\| area=\s*all \| maxDets= ?100 ?\] = (-?\d+\.\d+)",
        log,
    )
    if m:
        out["bbox_mAP_50"] = float(m.group(1))
    m = re.search(
        r"Average Precision  \(AP\) @\[ IoU=0\.75\s+\| area=\s*all \| maxDets= ?100 ?\] = (-?\d+\.\d+)",
        log,
    )
    if m:
        out["bbox_mAP_75"] = float(m.group(1))
    return out


PARSERS = {
    "mmdet3": _parse_mmdet3,
    "mmdet2": _parse_mmdet2,
    "detectron2": _parse_detectron2,
    "accelerate": _parse_accelerate,
}


def _autodetect_format(log_text: str) -> str:
    """log 冒頭～末尾から eval framework を推定。曖昧なら 'mmdet3' fallback。"""
    if "test/bbox_mAP" in log_text or "mmengine - INFO - Epoch(test)" in log_text:
        return "mmdet3"
    if "d2.evaluation" in log_text or re.search(r"copypaste: [\d.]+,[\d.]+", log_text):
        return "detectron2"
    if "det.util.utils" in log_text or "Test:  [   0/" in log_text:
        return "accelerate"
    if "OrderedDict([('bbox_mAP'" in log_text:
        return "mmdet2"
    return "mmdet3"


# ---------------------------- Notion API ----------------------------------- #
def _find_existing(db_id: str, name: str, headers: dict) -> Optional[str]:
    r = requests.post(
        f"https://api.notion.com/v1/databases/{db_id}/query",
        headers=headers,
        json={"filter": {"property": "Name", "title": {"equals": name}}, "page_size": 1},
        timeout=30,
    )
    r.raise_for_status()
    results = r.json().get("results", [])
    return results[0]["id"] if results else None


def _build_result_text(metrics: dict) -> str:
    def g(k):
        return metrics.get(k)

    parts: list[str] = []
    if g("bbox_mAP") is not None:
        parts.append(f"bbox_mAP={g('bbox_mAP'):.4f}")
    if g("bbox_mAP_50") is not None:
        parts.append(f"AP50={g('bbox_mAP_50'):.4f}")
    if g("bbox_mAP_75") is not None:
        parts.append(f"AP75={g('bbox_mAP_75'):.4f}")
    if g("AP_rare") is not None:
        parts.append(f"AP_rare={g('AP_rare'):.4f}")
    if g("AP_common") is not None:
        parts.append(f"AP_common={g('AP_common'):.4f}")
    return " / ".join(parts) if parts else "no metrics parsed"


def _build_props(
    *,
    name: str,
    step: str,
    seed: int,
    tier: str,
    recipe: str,
    server: str,
    metrics: dict,
    started: str,
    finished: str,
    commit: str,
    artifacts: Optional[str],
) -> dict:
    """Notion page properties dict."""
    props = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Step": {"select": {"name": step}},
        "Seed": {"number": seed},
        "Tier": {"select": {"name": tier}},
        "Status": {"select": {"name": "completed"}},
        "Eval Recipe": {"rich_text": [{"text": {"content": recipe}}]},
        "Primary Metric": {"rich_text": [{"text": {"content": "test bbox mAP / AP_50 / AP_75 / AP_rare / AP_common"}}]},
        "Result": {"rich_text": [{"text": {"content": _build_result_text(metrics)}}]},
        "Started": {"date": {"start": started}},
        "Finished": {"date": {"start": finished}},
        "Commit": {"rich_text": [{"text": {"content": commit[:80]}}]},
    }
    if server:
        props["Server"] = {"select": {"name": server}}
    if artifacts:
        props["Artifacts"] = {"url": artifacts}
    return props


def _log_prefix() -> str:
    return "[post_eval] "


def _resolve_server_option() -> str:
    """egosurgery.utils.server_name.resolve_server_name と同じ優先順位で解決する。

    OS hostname はコンテナ由来の名前 (例: "aolab") を返すことがあり、実際の
    物理サーバー名と一致しない場合がある。SERVERNAME (shell rc で export)
    が正の情報源で、NOTION_SERVER_OPTION はさらに Notion 表示用の別名
    (例: "philip (RTX 6000 Ada)") を明示する。
    """
    notion_opt = os.environ.get("NOTION_SERVER_OPTION", "").strip()
    if notion_opt:
        return notion_opt
    server_name = (
        os.environ.get("SERVERNAME", "").strip()
        or os.environ.get("EGOSURGERY_SERVER_NAME", "").strip()
    )
    if server_name:
        return server_name
    return socket.gethostname().split(".")[0].lower()


def post_eval(
    *,
    name: str,
    step: str,
    seed: int,
    tier: str,
    recipe: str,
    server: str,
    metrics: dict,
    started: str,
    finished: str,
    commit: str,
    artifacts: Optional[str] = None,
) -> dict | None:
    api_key = os.environ.get("NOTION_API_KEY", "").strip()
    db_id = os.environ.get("NOTION_DB_ID", "").strip()
    if not api_key or not db_id:
        print(f"{_log_prefix()}skip {name}: NOTION_API_KEY/NOTION_DB_ID unset")
        return None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }
    props = _build_props(
        name=name, step=step, seed=seed, tier=tier, recipe=recipe,
        server=server, metrics=metrics, started=started, finished=finished,
        commit=commit, artifacts=artifacts,
    )
    existing = _find_existing(db_id, name, headers)
    if existing:
        r = requests.patch(
            f"https://api.notion.com/v1/pages/{existing}",
            headers=headers, json={"properties": props}, timeout=30,
        )
    else:
        r = requests.post(
            "https://api.notion.com/v1/pages",
            headers=headers,
            json={
                "parent": {"database_id": db_id},
                "properties": props,
            },
            timeout=30,
        )
    if r.status_code >= 400:
        print(f"{_log_prefix()}FAIL {name}: {r.status_code} {r.text[:200]}")
        return None
    action = "updated" if existing else "created"
    print(f"{_log_prefix()}{action} {name}: {_build_result_text(metrics)}")
    return r.json()


# ---------------------------- CLI ----------------------------------------- #
def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=PROJ, text=True)
            .strip()
        )
    except Exception:  # noqa: BLE001
        return ""


def _mtime_iso(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .isoformat(timespec="seconds")
    )


def _cli() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--name", required=True)
    p.add_argument("--step", default="S0")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--tier", default="effort")
    p.add_argument("--recipe", required=True)
    p.add_argument("--log-path", required=True)
    p.add_argument("--log-format", default="auto",
                   choices=list(PARSERS.keys()) + ["auto"],
                   help="log parser; auto = 内容から自動判定 (default)")
    p.add_argument(
        "--server", default=None,
        help="未指定なら NOTION_SERVER_OPTION → SERVERNAME → hostname の順で自動解決",
    )
    p.add_argument("--artifacts", default=None)
    args = p.parse_args()

    log_path = Path(args.log_path)
    if not log_path.exists():
        print(f"{_log_prefix()}log not found: {log_path}", file=sys.stderr)
        sys.exit(2)
    log_text = log_path.read_text(errors="replace")
    fmt = args.log_format
    if fmt == "auto":
        fmt = _autodetect_format(log_text)
        print(f"{_log_prefix()}auto-detected log-format={fmt}")
    metrics = PARSERS[fmt](log_text)
    started = finished = _mtime_iso(log_path)
    commit = _git_commit()
    server = args.server or _resolve_server_option()
    post_eval(
        name=args.name, step=args.step, seed=args.seed, tier=args.tier,
        recipe=args.recipe, server=server, metrics=metrics,
        started=started, finished=finished, commit=commit, artifacts=args.artifacts,
    )


# --- 退役（2026-09-01, T-2026-09-01-notion-retire-scripts-and-speccheck）------ #
# 本スクリプトは旧データベース群へ自前で REST を呼んで書いていた。旧 DB は
# 2026-08-31 に凍結し、**CLI が Notion に触れるのは配布台帳だけになった。**
# 識別子を NOTION_DB_ID 環境変数や登録簿から自前で解決するため、登録簿の退役
# だけでは止まらない。**入口で止める。** 全行の写しは docs/archive/notion/db/ にある。
RETIRED_SINCE = "2026-09-01"


def _retired_notice() -> int:
    """呼ばれたら投稿せず退役の旨を出して終える。**無言で成功したことにしない。**"""
    import sys as _sys
    print(
        f"[retired] {__file__} は {RETIRED_SINCE} に退役した。Notion へ投稿しない。"
        " 旧データベースの内容は docs/archive/notion/db/ の写しを読む。",
        file=_sys.stderr,
    )
    return 3

if __name__ == "__main__":
    raise SystemExit(_retired_notice())
