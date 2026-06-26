"""Trainer の `run()` を 1 行で包む context manager（auto_logging_implementation.md §5.2）。

使い方:
    from egosurgery.utils.run_logging import run_logging

    manager = ExperimentManager(...)
    manager.setup(cfg)
    with run_logging(cfg, manager, step="s0", primary_metric="...") as rlog:
        train(...)              # 学習・評価ループ
        # 異常終了でも atexit で投稿が走る（ベストエフォート）
        # 正常終了時は finally 経由で同じパス（マーカーで二重投稿は防ぐ）

設計:
- ResearchLogger を生成し、yield する
- 正常終了時は finally で log_run()
- 異常終了時は atexit で fallback（プロセス終了時に呼ばれる）
- マーカーで二重起動を防ぐ（_flush の posted フラグ + .notion_sync.json）
- fail-open: 例外を投げない（学習を止めない）
"""

from __future__ import annotations

import atexit
import logging
from contextlib import contextmanager
from typing import Any, Iterator

from .research_logger import ResearchLogger

logger = logging.getLogger(__name__)


@contextmanager
def run_logging(
    cfg: Any = None,
    manager: Any = None,
    *,
    step: str | None = None,
    tier: str = "must",
    primary_metric: str | None = None,
    extra_result_text: str | None = None,
) -> Iterator[ResearchLogger]:
    """`with run_logging(cfg, manager) as rlog:` で trainer の run() を包む。

    異常終了でも atexit で投稿を試みる（マーカーで二重投稿は防ぐ）。
    """
    rlog = ResearchLogger(cfg, manager)
    posted = {"done": False}

    def _flush() -> None:
        if posted["done"]:
            return
        try:
            rlog.log_run(
                status="completed",
                step=step,
                tier=tier,
                primary_metric=primary_metric,
                extra_result_text=extra_result_text,
            )
        except Exception as exc:  # noqa: BLE001 - fail-open
            logger.warning("run_logging._flush: exception %s → fail-open", exc)
        finally:
            posted["done"] = True

    atexit.register(_flush)
    try:
        yield rlog
    finally:
        _flush()
