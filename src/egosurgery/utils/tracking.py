"""W&B 追跡の薄いラッパ（任意・graceful no-op）。

CLAUDE.md「W&B で必ず全実験を追跡」を、認証や wandb 導入の有無に依らず安全に満たすための入口。
- WANDB_API_KEY 未設定、または wandb 未導入なら **no-op**（学習を止めない）。
- 設定があれば run を開始し、per-epoch メトリクスを log する。
- `source scripts/load_env.sh` で .env.gpg を復号すると認証が揃い、自動で追跡が有効になる。

使い方:
    from egosurgery.utils import tracking
    tracking.init("s4_phase_baseline_seed42", config=cfg, group="S4")
    ...
    tracking.log({"val/phase_accuracy": acc, "train/loss": loss}, step=epoch)
    ...
    tracking.finish()
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)
_run: Any = None


def enabled() -> bool:
    return bool(os.environ.get("WANDB_API_KEY", "").strip())


def init(name: str, *, config: dict | None = None, group: str | None = None,
         job_type: str | None = None) -> Any:
    """W&B run を開始（認証/導入が無ければ no-op で None を返す）。"""
    global _run
    if not enabled():
        logger.info("wandb 追跡 skip（WANDB_API_KEY 未設定）。source scripts/load_env.sh で有効化。")
        return None
    try:
        import wandb
    except Exception:  # noqa: BLE001 — 該当 venv に wandb 未導入
        logger.info("wandb 未導入 → 追跡 skip（pip install wandb で有効化）")
        return None
    try:
        _run = wandb.init(
            project=os.environ.get("WANDB_PROJECT", "egosurgery_multitask"),
            entity=os.environ.get("WANDB_ENTITY") or None,
            name=name, group=group, job_type=job_type,
            config=config or {}, reinit=True,
        )
        return _run
    except Exception as exc:  # noqa: BLE001
        logger.warning("wandb.init 失敗 → 追跡 skip: %s", exc)
        _run = None
        return None


def log(metrics: dict, *, step: int | None = None) -> None:
    if _run is None:
        return
    try:
        import wandb
        wandb.log(metrics, step=step)
    except Exception as exc:  # noqa: BLE001
        logger.debug("wandb.log skip: %s", exc)


def finish() -> None:
    global _run
    if _run is None:
        return
    try:
        import wandb
        wandb.finish()
    except Exception:  # noqa: BLE001
        pass
    _run = None
