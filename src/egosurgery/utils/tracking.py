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

import json
import logging
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)
_run: Any = None

# 実験フォルダへ置く W&B run 識別子の証跡。既存の証跡（server.txt / git_commit.txt /
# metrics.json）と同じく run ディレクトリ直下のフラットファイルに揃える。単値ではなく
# id / url / project / entity の組なので JSON にする。
RUN_IDENTITY_FILE = "wandb_run.json"


def enabled() -> bool:
    return bool(os.environ.get("WANDB_API_KEY", "").strip())


def init(name: str, *, config: dict | None = None, group: str | None = None,
         job_type: str | None = None, exp_dir: "str | Path | None" = None) -> Any:
    """W&B run を開始（認証/導入が無ければ no-op で None を返す）。

    Args:
        exp_dir: 渡された場合、run 開始に成功したときだけ
            :data:`RUN_IDENTITY_FILE` を書き、証跡と外部記録を結ぶ。
            no-op のときは何も書かない（空ファイルも作らない）。
    """
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
        if exp_dir is not None:
            record_run_identity(exp_dir)
        return _run
    except Exception as exc:  # noqa: BLE001
        logger.warning("wandb.init 失敗 → 追跡 skip: %s", exc)
        _run = None
        return None


def record_run_identity(exp_dir: "str | Path") -> bool:
    """外部記録が有効なとき、run の識別子と参照先を証跡へ書く。

    証跡と W&B を後から機械的に辿れるようにするための対応付け。遡っての紐付けは
    行わない（今後の run から結ばれる）。

    Args:
        exp_dir: 実験フォルダ。``RUN_IDENTITY_FILE`` をこの直下へ置く。

    Returns:
        書いたら ``True``、書かなかったら ``False``。

    Notes:
        - run が無い（``WANDB_API_KEY`` 未設定 / wandb 未導入 / init 失敗）ときは
          **何も書かない**。空の JSON も作らない。索引側は「ファイルが無い＝空欄」
          として扱うため、空ファイルを置くと空欄と区別できなくなる。
        - 書くのは id / url / project / entity / name だけで、**資格情報は書かない**。
        - 失敗しても例外を投げない。外部サービスが落ちていても学習は続くべきである。
    """
    if _run is None:
        return False
    try:
        info: dict[str, str] = {}
        for key, attr in (
            ("run_id", "id"),
            ("run_url", "url"),
            ("project", "project"),
            ("entity", "entity"),
            ("run_name", "name"),
        ):
            value = getattr(_run, attr, None)
            if value:
                info[key] = str(value)
        # 識別子が取れないなら書かない。中途半端な証跡は空欄より紛らわしい。
        if not info.get("run_id"):
            logger.warning("wandb run id を取得できず → 識別子の証跡は書かない")
            return False
        path = Path(exp_dir) / RUN_IDENTITY_FILE
        path.write_text(
            json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        return True
    except Exception as exc:  # noqa: BLE001 — 追跡の失敗で学習を止めない
        logger.warning("wandb run 識別子の記録に失敗 → skip（学習は継続）: %s", exc)
        return False


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
