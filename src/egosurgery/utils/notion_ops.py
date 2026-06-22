"""M2研究運用ハブの管理 DB への REST 書き込みヘルパ（意思決定/失敗知見/プロンプト）。

`notion_logger.py`（実験Run台帳の自動投稿）の HTTP パターンを共有し、運用ループの
「結果記録以外」の自動化を担う:
    - log_decision : 意思決定ログ（方針変更）
    - log_lesson   : 失敗知見・教訓（再発防止）
    - save_prompt  : プロンプトライブラリ（再利用プロンプトの登録）

設計方針（notion_logger と統一）:
    - 認証は環境変数のみ: NOTION_API_KEY（必須・.env）。DB ID は configs/notion.yaml
      （非秘密）または NOTION_DB_<KEY> 環境変数で上書き。
    - 失敗しても例外を上に流さない（warn のみ）。研究フローを巻き込まない。
    - 冪等: 同名 Name があれば update、無ければ create。
    - 依存追加なし（requests / yaml は既存依存）。

token の Notion Integration に対象 DB を share しておくこと。
"""
from __future__ import annotations

import datetime as _dt
import logging
import os
from pathlib import Path
from typing import Any

from egosurgery.utils.notion_logger import (
    _API_BASE,
    NOTION_VERSION,
    _find_existing_page,
)

logger = logging.getLogger(__name__)
_REGISTRY_PATH = Path(__file__).resolve().parents[3] / "configs" / "notion.yaml"
_registry_cache: dict | None = None


def _registry() -> dict:
    global _registry_cache
    if _registry_cache is None:
        try:
            import yaml
            _registry_cache = yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8")) or {}
        except Exception as exc:  # noqa: BLE001
            logger.warning("notion registry 読み込み失敗 (%s)", exc)
            _registry_cache = {}
    return _registry_cache


def _db_id(key: str) -> str | None:
    """DB ID を解決する。NOTION_DB_<KEY> 環境変数 > configs/notion.yaml。"""
    env = os.environ.get(f"NOTION_DB_{key.upper()}", "").strip()
    if env:
        return env
    return (_registry().get("databases", {}) or {}).get(key)


def _headers() -> dict | None:
    api_key = os.environ.get("NOTION_API_KEY", "").strip()
    if not api_key:
        logger.info("Notion ops disabled (NOTION_API_KEY 未設定)")
        return None
    return {"Authorization": f"Bearer {api_key}", "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json"}


def _today() -> str:
    return _dt.date.today().isoformat()


# -- プロパティ整形（Notion API 形式）-------------------------------------- #
def _text(v: str) -> dict:
    return {"rich_text": [{"text": {"content": str(v)[:1900]}}]}


def _title(v: str) -> dict:
    return {"title": [{"text": {"content": str(v)[:200]}}]}


def _select(v: str | None) -> dict | None:
    return {"select": {"name": v}} if v else None


def _multi(vs) -> dict | None:
    vs = [s for s in (vs or []) if s]
    return {"multi_select": [{"name": s} for s in vs]} if vs else None


def _date(v: str | None) -> dict | None:
    return {"date": {"start": v}} if v else None


def _url(v: str | None) -> dict | None:
    return {"url": v} if v else None


def _upsert(db_key: str, name: str, properties: dict) -> dict | None:
    """db_key の DB に Name=name で upsert（同名あれば PATCH、無ければ POST）。"""
    headers = _headers()
    db_id = _db_id(db_key)
    if headers is None or not db_id:
        if headers is not None:
            logger.warning("notion: DB id 未解決 (%s)", db_key)
        return None
    try:
        import requests
        props = {k: v for k, v in properties.items() if v is not None}
        page_id = _find_existing_page(db_id, name, headers)
        if page_id:
            r = requests.patch(f"{_API_BASE}/pages/{page_id}", headers=headers,
                               json={"properties": props}, timeout=30)
        else:
            r = requests.post(f"{_API_BASE}/pages", headers=headers,
                              json={"parent": {"database_id": db_id}, "properties": props}, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"{r.status_code} {r.text[:300]}")
        logger.info("notion %s: %s (%s)", db_key, name, "updated" if page_id else "created")
        return r.json()
    except Exception as exc:  # noqa: BLE001 — フローを巻き込まない
        logger.warning("notion %s 投稿 skip (%s): %s", db_key, name, exc)
        return None


# -- 公開 API -------------------------------------------------------------- #
def log_decision(name: str, *, rationale: str, type_: str = "method", impact: str = "medium",
                 status: str = "active", related_steps: list[str] | None = None,
                 revisit_trigger: str = "", changed_docs: str = "", source: str = "",
                 date: str | None = None) -> dict | None:
    """意思決定ログに記録。type_∈{method,operation,data,scope,hardware} / impact∈{high,medium,low}。"""
    props: dict[str, Any] = {
        "Name": _title(name), "Type": _select(type_), "Impact": _select(impact),
        "Status": _select(status), "Rationale": _text(rationale),
        "Related Steps": _multi(related_steps), "Revisit Trigger": _text(revisit_trigger),
        "Changed Documents": _text(changed_docs), "Source": _url(source),
        "Date": _date(date or _today()),
    }
    return _upsert("decision_log", name, props)


def log_lesson(name: str, *, category: str, severity: str = "P2", status: str = "open",
               symptom: str = "", root_cause: str = "", prevention: str = "",
               related_steps: list[str] | None = None, evidence: str = "",
               date: str | None = None) -> dict | None:
    """失敗知見・教訓に記録。category∈{data,evaluation,training,implementation,process} / severity∈{P0..P3}。"""
    props: dict[str, Any] = {
        "Name": _title(name), "Category": _select(category), "Severity": _select(severity),
        "Status": _select(status), "Symptom": _text(symptom), "Root Cause": _text(root_cause),
        "Prevention": _text(prevention), "Related Steps": _multi(related_steps),
        "Evidence": _url(evidence), "Date": _date(date or _today()),
    }
    return _upsert("lessons", name, props)


def save_prompt(name: str, *, prompt_file: str = "", target: str = "Claude Code CLI",
                related_step: str | None = None, status: str = "ready", version: str = "",
                input_pack: str = "", output_contract: str = "",
                last_used: str | None = None) -> dict | None:
    """プロンプトライブラリに登録。target∈{Claude chat,Claude Code CLI,Codex,human checklist}。"""
    props: dict[str, Any] = {
        "Name": _title(name), "Prompt File": _url(prompt_file), "Target": _select(target),
        "Related Step": _select(related_step), "Status": _select(status),
        "Version": _text(version), "Input Pack": _text(input_pack),
        "Output Contract": _text(output_contract), "Last Used": _date(last_used or _today()),
    }
    return _upsert("prompt_library", name, props)
