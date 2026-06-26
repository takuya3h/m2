"""冪等記録のためのマーカー読み書き + content hash（§6 キー設計）。

各実験フォルダに `.notion_sync.json` を置き、投稿済の Notion page id / decision hash /
lesson hash を保存する。`.gitignore` 対象（同期状態であり証跡ではない）。

スキーマ:
    {
      "run_ledger_page": "<notion page id>",   # 実験Run台帳の page id（未投稿なら欠落）
      "decisions": ["<sha1 hash>", ...],        # notes.md の decision ブロックの投稿済 hash
      "lessons":   ["<sha1 hash>", ...],        # 同 lesson
      "prompts":   ["<sha1 hash>", ...],        # 同 prompt
    }
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

MARKER_FILENAME = ".notion_sync.json"


def content_hash(*parts: str) -> str:
    """複数の文字列を改行で結合して SHA1 hash を返す。decision/lesson の重複検出に使う。"""
    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()


def marker_path(run_dir: Path | str) -> Path:
    return Path(run_dir) / MARKER_FILENAME


def load_marker(run_dir: Path | str) -> dict:
    """マーカーを読む。存在しない or 壊れていれば空 dict を返す（fail-open）。"""
    p = marker_path(run_dir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_marker(run_dir: Path | str, marker: dict) -> None:
    """マーカーを atomic に書き出す（一時ファイル → rename）。"""
    p = marker_path(run_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(marker, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(p)


def is_run_posted(run_dir: Path | str) -> bool:
    """実験Run台帳に既投稿か。マーカーの run_ledger_page を見るだけで Notion クエリしない。"""
    return bool(load_marker(run_dir).get("run_ledger_page"))


def mark_run_posted(run_dir: Path | str, page_id: str) -> None:
    """Run台帳投稿成功時にマーカーを更新する。"""
    marker = load_marker(run_dir)
    marker["run_ledger_page"] = page_id
    save_marker(run_dir, marker)


def is_block_posted(run_dir: Path | str, block_type: str, block_hash: str) -> bool:
    """decision/lesson/prompt の hash が既投稿リストにあるか。"""
    marker = load_marker(run_dir)
    return block_hash in (marker.get(block_type) or [])


def mark_block_posted(run_dir: Path | str, block_type: str, block_hash: str) -> None:
    """投稿成功時に block_type のリストに hash を追加（重複なし）。"""
    marker = load_marker(run_dir)
    lst = marker.setdefault(block_type, [])
    if block_hash not in lst:
        lst.append(block_hash)
        save_marker(run_dir, marker)
