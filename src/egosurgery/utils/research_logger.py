"""研究記録の単一ファサード `ResearchLogger`（auto_logging_implementation.md §5.1）。

既存 `notion_ops` / `notion_logger` を薄くラップし、**全記録をここを通す**ことで二重投稿を構造的に
防ぐ。冪等性は 2 層:
  1. ローカルマーカー `.notion_sync.json`（`idempotency` モジュール）= API 呼び出し回避
  2. Notion 側の Name 一致 upsert（`notion_logger._find_existing_page` / `notion_ops._upsert`）

Fail-open（§2 鉄則 4）: NOTION_API_KEY 未設定や REST 例外で **例外を投げず None を返す**。
マーカーは書かない（未投稿として残り、後続スイープで再試行される）。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .idempotency import (
    content_hash,
    is_block_posted,
    is_run_posted,
    load_marker,
    mark_block_posted,
    mark_run_posted,
)

logger = logging.getLogger(__name__)


class ResearchLogger:
    """各実験フォルダに紐付くファサード。trainer は `run_logging()` 経由で使う。

    Args:
        cfg: Hydra DictConfig もしくは dict（experiment.step などの参照に使う）。
        manager: `ExperimentManager`（exp_dir / metrics.json / config.yaml の在処）。
                 None 可（standalone 経路で manager が無い場合の fail-open）。
    """

    def __init__(self, cfg: Any = None, manager: Any = None) -> None:
        self.cfg = cfg
        self.manager = manager
        self.exp_dir: Path | None = (
            Path(manager.exp_dir) if manager is not None else None
        )

    # ---- run 記録（自動・人手ゼロ） ---------------------------------------------
    def log_run(
        self,
        *,
        status: str = "completed",
        step: str | None = None,
        tier: str = "must",
        primary_metric: str | None = None,
        extra_result_text: str | None = None,
    ) -> str | None:
        """実験Run台帳へ冪等 upsert。投稿成功なら page id、失敗/skip なら None。

        マーカー `.notion_sync.json` に run_ledger_page が既にあれば API 呼び出しを skip。
        """
        if self.exp_dir is None:
            logger.warning(
                "ResearchLogger.log_run: exp_dir is None (manager 未設定) → skip"
            )
            return None
        if is_run_posted(self.exp_dir):
            return load_marker(self.exp_dir).get("run_ledger_page")

        # 空 metrics を "completed" として確定投稿しない。ExperimentManager は setup 時に
        # 空 {} を書くため、進行中/失敗の run をスイープが拾うと「完了・metrics 空」で投稿し、
        # さらに marker で固定してしまう（efros で実際に発生）。metrics が揃えば次回スイープで
        # 正しく upsert される。running 等の明示ステータスはそのまま許可。
        if status == "completed":
            import json

            mp = self.exp_dir / "metrics.json"
            try:
                _m = json.loads(mp.read_text()) if mp.exists() else {}
            except Exception:  # noqa: BLE001
                _m = {}
            if not _m:
                logger.info(
                    "log_run: metrics.json 空/欠落 → completed 投稿を skip (%s)",
                    self.exp_dir.name,
                )
                return None

        # cfg から step を補完（指定が無い場合）。defaults は notion_logger 側。
        if step is None and self.cfg is not None:
            try:
                step = (
                    self.cfg.get("experiment", {}).get("step")
                    if isinstance(self.cfg, dict)
                    else getattr(getattr(self.cfg, "experiment", None), "step", None)
                )
            except Exception:  # noqa: BLE001
                step = None

        # notion_logger に委譲（既存 API、Server 列 fallback 等のロジックを再利用）。
        kwargs: dict[str, Any] = {"status": status, "tier": tier}
        if step is not None:
            kwargs["step"] = step
        if primary_metric is not None:
            kwargs["primary_metric"] = primary_metric
        if extra_result_text is not None:
            kwargs["extra_result_text"] = extra_result_text

        try:
            from .notion_logger import log_experiment_to_notion

            result = log_experiment_to_notion(self.exp_dir, **kwargs)
        except Exception as exc:  # noqa: BLE001 - fail-open
            logger.warning("ResearchLogger.log_run: REST exception %s → fail-open", exc)
            return None

        if isinstance(result, dict) and result.get("id"):
            page_id = result["id"]
            mark_run_posted(self.exp_dir, page_id)
            return page_id
        return None

    # ---- decision / lesson / prompt（半自動、人間 notes.md → 投稿） ----------
    def log_decision(self, decision: dict) -> str | None:
        """意思決定ログへ冪等 upsert。decision = parsed notes block dict."""
        if not decision.get("title"):
            return None
        h = content_hash(
            decision.get("title", ""),
            decision.get("date", ""),
            decision.get("body", ""),
        )
        if self.exp_dir and is_block_posted(self.exp_dir, "decisions", h):
            return None
        try:
            from .notion_ops import log_decision

            kwargs = {
                "rationale": decision.get("body", "") or decision.get("rationale", ""),
                "type_": decision.get("type", "method"),
                "impact": decision.get("impact", "medium"),
                "status": decision.get("status", "active"),
                "related_steps": decision.get("related_steps")
                or decision.get("affects_steps"),
                "revisit_trigger": decision.get("revisit_trigger", ""),
                "changed_docs": decision.get("affects", "")
                or decision.get("changed_docs", ""),
                "source": decision.get("source", ""),
            }
            if decision.get("date"):
                kwargs["date"] = decision["date"]
            result = log_decision(decision["title"], **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ResearchLogger.log_decision: REST exception %s → fail-open", exc
            )
            return None
        if isinstance(result, dict) and result.get("id"):
            if self.exp_dir:
                mark_block_posted(self.exp_dir, "decisions", h)
            return result["id"]
        return None

    def log_lesson(self, lesson: dict) -> str | None:
        """失敗知見・教訓へ冪等 upsert。lesson = parsed notes block dict."""
        if not lesson.get("title"):
            return None
        h = content_hash(
            lesson.get("title", ""),
            lesson.get("date", ""),
            lesson.get("body", ""),
        )
        if self.exp_dir and is_block_posted(self.exp_dir, "lessons", h):
            return None
        try:
            from .notion_ops import log_lesson

            kwargs = {
                "category": lesson.get("category", "implementation"),
                "severity": lesson.get("severity", "P2"),
                "status": lesson.get("status", "open"),
                "symptom": lesson.get("symptom", "") or lesson.get("body", ""),
                "root_cause": lesson.get("root_cause", ""),
                "prevention": lesson.get("prevention", "")
                or lesson.get("recurrence_guard", ""),
                "related_steps": lesson.get("related_steps")
                or lesson.get("affects_steps"),
                "evidence": lesson.get("evidence", ""),
            }
            if lesson.get("date"):
                kwargs["date"] = lesson["date"]
            result = log_lesson(lesson["title"], **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ResearchLogger.log_lesson: REST exception %s → fail-open", exc
            )
            return None
        if isinstance(result, dict) and result.get("id"):
            if self.exp_dir:
                mark_block_posted(self.exp_dir, "lessons", h)
            return result["id"]
        return None

    def save_prompt(self, name: str, body: str, **kwargs: Any) -> str | None:
        """プロンプトライブラリへ保存（冪等は notion_ops 側の Name 一致 upsert に委任）。"""
        h = content_hash(name, body)
        if self.exp_dir and is_block_posted(self.exp_dir, "prompts", h):
            return None
        try:
            from .notion_ops import save_prompt

            result = save_prompt(name, **kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "ResearchLogger.save_prompt: REST exception %s → fail-open", exc
            )
            return None
        if isinstance(result, dict) and result.get("id"):
            if self.exp_dir:
                mark_block_posted(self.exp_dir, "prompts", h)
            return result["id"]
        return None

    # ---- マスター昇格関連（自動マージしない・ドラフトのみ） ----------------
    def draft_state_update(self) -> str:
        """『現在の研究状態』page 更新用ドラフト文を生成（投稿しない）。

        現状の metrics.json の主要数値 + notes.md の最新ブロックから生成。
        実際の更新は人間が確認してから MCP/REST で行う。
        """
        if self.exp_dir is None:
            return ""
        from datetime import date

        lines = [f"# {date.today().isoformat()} 更新ドラフト（人間確認後にマージ）", ""]
        metrics_path = self.exp_dir / "metrics.json"
        if metrics_path.exists():
            import json

            try:
                m = json.loads(metrics_path.read_text())
                for k in (
                    "phase_accuracy",
                    "phase_macro_f1",
                    "mAP",
                    "AP_50",
                    "AP_rare",
                ):
                    if k in m:
                        lines.append(f"- {k}: {m[k]}")
            except Exception:  # noqa: BLE001
                pass
        notes_path = self.exp_dir / "notes.md"
        if notes_path.exists():
            lines.append("")
            lines.append("## notes.md 抜粋")
            lines.append(notes_path.read_text(encoding="utf-8")[:500])
        return "\n".join(lines)

    def stage_master_diff(self, entry: str) -> None:
        """進捗反映スナップショット page へ追記する『適用待ち差分』をローカルに stage する。

        実投稿は週次 draft_master_update.py が拾う。ここでは exp_dir/master_diff.md に追記のみ。
        """
        if self.exp_dir is None:
            return
        from datetime import date

        diff_path = self.exp_dir / "master_diff.md"
        with diff_path.open("a", encoding="utf-8") as f:
            f.write(f"\n## {date.today().isoformat()}\n{entry}\n")
