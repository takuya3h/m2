"""Notion「実験Run台帳」DB への自動投稿モジュール。

学習が完了した実験フォルダのメタデータ (metrics.json / per_class_ap.json /
git_commit.txt / server.txt / 環境変数 $SERVERNAME / Hydra 経由の eval_recipe)
を読み取り、Notion DB に completed 行として作成する。

設計方針:
    - 失敗時は学習プロセスを止めない (warn のみ)。台帳の不調が
      Δ 基準点となる実験を巻き込まないこと。
    - DDP rank>=1 では呼ばれない (ExperimentManager が rank=0 のみ保持)。
    - 依存追加なし。requests のみ使用 (mmcv 経由で既に入っている)。
    - 環境変数経由で設定を受け取る:
        * NOTION_API_KEY        (必須) Notion Integration トークン
        * NOTION_DB_ID          (必須) 実験Run台帳 data source ID
        * NOTION_SERVER_OPTION  (推奨) Server select の値 (例: "philip (RTX 6000 Ada)")
        * SERVERNAME            (任意) $SERVERNAME 環境変数 (本プロジェクト慣習)

冪等性:
    同名タイトル (Name) の行が DB に既に存在すれば update (Status / Result /
    Finished のみ書き換え)、無ければ新規作成。Notion API 側で title 検索する。
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

NOTION_VERSION = "2022-06-28"
_API_BASE = "https://api.notion.com/v1"


def log_experiment_to_notion(
    exp_dir: Path | str,
    *,
    status: str = "completed",
    step: str = "S0",
    tier: str = "must",
    primary_metric: str = "tool bbox mAP / AP_50 / AP_75 / AP_rare / AP_common (COCO bbox @ IoU=0.5:0.95)",
    extra_result_text: str | None = None,
) -> dict | None:
    """実験フォルダの内容を Notion 実験Run台帳に投稿する。

    Args:
        exp_dir: 完了した実験フォルダ。metrics.json / per_class_ap.json /
            git_commit.txt / server.txt が揃っている前提。
        status: "completed" / "running" / "failed" / "archived" のいずれか。
        step: "S0" / "S1" / ... select オプション名と一致させること。
        tier: "must" / "effort" / "cut".
        primary_metric: Primary Metric テキスト列の値。
        extra_result_text: Result 列の末尾に追記する自由テキスト。

    Returns:
        Notion 側のレスポンス dict、または失敗時 None。

    Notes:
        失敗してもこの関数は例外を上に流さない。学習を巻き込まないため。
    """
    try:
        return _log_impl(
            Path(exp_dir),
            status=status,
            step=step,
            tier=tier,
            primary_metric=primary_metric,
            extra_result_text=extra_result_text,
        )
    except Exception as exc:  # noqa: BLE001 — Notion 失敗で学習を巻き込まない
        logger.warning("Notion logging skipped: %s", exc)
        return None


def _log_impl(
    exp_dir: Path,
    *,
    status: str,
    step: str,
    tier: str,
    primary_metric: str,
    extra_result_text: str | None,
) -> dict | None:
    api_key = os.environ.get("NOTION_API_KEY", "").strip()
    db_id = os.environ.get("NOTION_DB_ID", "").strip()
    if not api_key or not db_id:
        logger.info(
            "Notion logging disabled (NOTION_API_KEY or NOTION_DB_ID not set)"
        )
        return None

    import requests

    name = exp_dir.name
    metrics = _read_json(exp_dir / "metrics.json")
    eval_recipe = metrics.get("eval_recipe") if isinstance(metrics, dict) else {}
    commit = _read_text(exp_dir / "git_commit.txt").strip()
    server_name = (
        os.environ.get("SERVERNAME")
        or _read_text(exp_dir / "server.txt").strip()
        or "unknown"
    )
    server_option = os.environ.get("NOTION_SERVER_OPTION", "").strip() or None

    result_text = _format_result(metrics, extra_result_text)
    eval_recipe_text = _format_eval_recipe(eval_recipe)
    gpu_config_text = _format_gpu_config(server_name)
    started_iso, finished_iso = _resolve_started_finished(exp_dir, status)
    seed = _parse_seed_from_name(name)

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

    existing_page_id = _find_existing_page(db_id, name, headers)
    if existing_page_id:
        return _update_page(
            existing_page_id,
            headers=headers,
            status=status,
            result_text=result_text,
            eval_recipe_text=eval_recipe_text,
            gpu_config_text=gpu_config_text,
            finished_iso=finished_iso,
        )

    return _create_page(
        db_id,
        headers=headers,
        name=name,
        status=status,
        step=step,
        tier=tier,
        server_option=server_option,
        seed=seed,
        started_iso=started_iso,
        finished_iso=finished_iso,
        primary_metric=primary_metric,
        result_text=result_text,
        eval_recipe_text=eval_recipe_text,
        gpu_config_text=gpu_config_text,
        commit=commit,
        exp_dir=exp_dir,
    )


# ----------------------------------------------------------------------------
# Notion API: query / create / update
# ----------------------------------------------------------------------------

def _find_existing_page(db_id: str, name: str, headers: dict) -> str | None:
    """同名タイトル (Name) の page id を 1 件返す。無ければ None。"""
    import requests

    payload = {
        "filter": {"property": "Name", "title": {"equals": name}},
        "page_size": 1,
    }
    r = requests.post(
        f"{_API_BASE}/databases/{db_id}/query",
        headers=headers,
        data=json.dumps(payload),
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Notion query failed: {r.status_code} {r.text[:200]}")
    results = r.json().get("results") or []
    return results[0]["id"] if results else None


def _create_page(
    db_id: str,
    *,
    headers: dict,
    name: str,
    status: str,
    step: str,
    tier: str,
    server_option: str | None,
    seed: int | None,
    started_iso: str | None,
    finished_iso: str | None,
    primary_metric: str,
    result_text: str,
    eval_recipe_text: str,
    gpu_config_text: str,
    commit: str,
    exp_dir: Path,
) -> dict:
    import requests

    properties: dict[str, Any] = {
        "Name": {"title": [{"text": {"content": name}}]},
        "Status": {"select": {"name": status}},
        "Step": {"select": {"name": step}},
        "Tier": {"select": {"name": tier}},
        "Primary Metric": {"rich_text": [{"text": {"content": primary_metric}}]},
        "Result": {"rich_text": [{"text": {"content": result_text}}]},
        "Eval Recipe": {"rich_text": [{"text": {"content": eval_recipe_text}}]},
        "GPU Config": {"rich_text": [{"text": {"content": gpu_config_text}}]},
        "Commit": {"rich_text": [{"text": {"content": commit}}]},
        "Artifacts": {"url": f"file://{exp_dir.resolve()}"},
        "Decision Needed": {"checkbox": False},
    }
    if server_option:
        properties["Server"] = {"select": {"name": server_option}}
    if seed is not None:
        properties["Seed"] = {"number": seed}
    if started_iso:
        properties["Started"] = {"date": {"start": started_iso}}
    if finished_iso:
        properties["Finished"] = {"date": {"start": finished_iso}}

    payload = {
        "parent": {"database_id": db_id},
        "properties": properties,
    }
    r = requests.post(
        f"{_API_BASE}/pages", headers=headers, data=json.dumps(payload), timeout=30
    )
    if r.status_code != 200:
        raise RuntimeError(f"Notion create failed: {r.status_code} {r.text[:300]}")
    logger.info("Notion row created for %s", name)
    return r.json()


def _update_page(
    page_id: str,
    *,
    headers: dict,
    status: str,
    result_text: str,
    eval_recipe_text: str,
    gpu_config_text: str,
    finished_iso: str | None,
) -> dict:
    import requests

    properties: dict[str, Any] = {
        "Status": {"select": {"name": status}},
        "Result": {"rich_text": [{"text": {"content": result_text}}]},
        "Eval Recipe": {"rich_text": [{"text": {"content": eval_recipe_text}}]},
        "GPU Config": {"rich_text": [{"text": {"content": gpu_config_text}}]},
    }
    if finished_iso:
        properties["Finished"] = {"date": {"start": finished_iso}}

    payload = {"properties": properties}
    r = requests.patch(
        f"{_API_BASE}/pages/{page_id}",
        headers=headers,
        data=json.dumps(payload),
        timeout=30,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Notion update failed: {r.status_code} {r.text[:300]}")
    logger.info("Notion row updated for page %s (status=%s)", page_id, status)
    return r.json()


# ----------------------------------------------------------------------------
# 値整形ヘルパ
# ----------------------------------------------------------------------------

def _format_result(metrics: dict, extra: str | None) -> str:
    if not isinstance(metrics, dict) or not metrics.get("epoch"):
        base = "(metrics.json に best epoch なし — 進行中または失敗の可能性)"
    else:
        base = (
            f"mAP={metrics.get('val/mAP'):.3f}, "
            f"AP_50={metrics.get('val/mAP_50'):.3f}, "
            f"AP_75={metrics.get('val/mAP_75'):.3f}, "
            f"AP_rare={metrics.get('val/AP_rare'):.4f}, "
            f"AP_common={metrics.get('val/AP_common'):.4f} "
            f"@ epoch {metrics.get('epoch')} (best)"
        )
    if extra:
        base = f"{base}\n{extra}"
    return base


def _format_eval_recipe(recipe: dict) -> str:
    if not isinstance(recipe, dict) or not recipe:
        return "(eval_recipe が metrics.json に未記載)"
    tc = recipe.get("test_cfg", {})
    return (
        f"effective_bs={recipe.get('effective_batch_size')} "
        f"(gpu_count={recipe.get('gpu_count')} x per-gpu bs), "
        f"lr_scaling={recipe.get('lr_scaling')}; "
        f"test_cfg(score_thr={tc.get('score_thr')}, "
        f"max_per_img={tc.get('max_per_img')}, "
        f"nms_pre={tc.get('nms_pre')}, nms_iou={tc.get('nms_iou')}); "
        f"split(train {recipe.get('split_train_images')} / "
        f"val {recipe.get('split_val_images')} / "
        f"test {recipe.get('split_test_images')})"
    )


def _format_gpu_config(server_name: str) -> str:
    gpu_name = _detect_gpu_name() or "unknown GPU"
    gpu_count = _detect_gpu_count()
    return (
        f"DDP {gpu_count}GPU ({gpu_name} x{gpu_count}) on {server_name}, "
        "manual launcher (E plan, CUDA_VISIBLE_DEVICES per rank)"
    )


def _detect_gpu_name() -> str | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            line = out.stdout.strip().splitlines()[0].strip()
            # "NVIDIA RTX 6000 Ada Generation" -> "RTX 6000 Ada"
            return line.replace("NVIDIA ", "").replace(" Generation", "")
    except Exception:  # noqa: BLE001
        pass
    return None


def _detect_gpu_count() -> int:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--list-gpus"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0:
            return len([ln for ln in out.stdout.splitlines() if ln.strip()])
    except Exception:  # noqa: BLE001
        pass
    return 1


def _resolve_started_finished(
    exp_dir: Path, status: str
) -> tuple[str | None, str | None]:
    """exp_dir 配下のタイムスタンプから Started / Finished を推定する。

    Started: タイムスタンプ命名のサブディレクトリ (例: 20260525_155843) があれば
        その値、なければ exp_dir 自身の mtime。
    Finished: status=completed のときのみ、最終 epoch_*.pth の mtime。
    """
    started = None
    for sub in sorted(exp_dir.iterdir() if exp_dir.is_dir() else []):
        if sub.is_dir() and len(sub.name) == 15 and sub.name[8] == "_":
            try:
                started = datetime.strptime(sub.name, "%Y%m%d_%H%M%S")
                break
            except ValueError:
                continue
    if started is None and exp_dir.is_dir():
        started = datetime.fromtimestamp(exp_dir.stat().st_mtime)
    started_iso = (
        started.astimezone().isoformat(timespec="seconds") if started else None
    )

    finished_iso = None
    if status == "completed":
        pths = sorted(exp_dir.glob("epoch_*.pth"), key=lambda p: p.stat().st_mtime)
        if pths:
            finished_iso = (
                datetime.fromtimestamp(pths[-1].stat().st_mtime)
                .astimezone()
                .isoformat(timespec="seconds")
            )
        else:
            finished_iso = datetime.now(timezone.utc).astimezone().isoformat(
                timespec="seconds"
            )
    return started_iso, finished_iso


def _parse_seed_from_name(name: str) -> int | None:
    """フォルダ名末尾の seed{N} を抽出する (例: s0_001_maskdino_bbox_seed42 -> 42)。"""
    idx = name.rfind("seed")
    if idx < 0:
        return None
    tail = name[idx + 4:]
    digits = "".join(ch for ch in tail if ch.isdigit())
    return int(digits) if digits else None


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
