"""hand_tool_seg タスクの loss mask ローダ。

hand_tool_seg の生成パイプラインは Mouth Gag / Skewer / 器具なしフレームを
構造的に除外するため、tool split の一部フレーム (計 460 件) には
アノテーションが存在しない。これらのフレームで hand_tool_seg 損失を評価すると
常にゼロ / undefined になるため、Dataset レベルで除外する。

配置: data/annotations/egosurgery_hts/hand_tool_seg/loss_mask/
詳細: 同 README.md §4、docs/experiment_log.md (2026-07-31)
"""
from __future__ import annotations

from pathlib import Path

DEFAULT_ROOT = Path(
    "data/annotations/egosurgery_hts/hand_tool_seg/loss_mask"
)
_VALID_SPLITS = frozenset({"train", "val", "test"})


def load_loss_mask(split: str, root: Path | str | None = None) -> frozenset[str]:
    """指定 split の loss mask (skip 対象 stems) を frozenset で返す。

    Args:
        split: ``"train"`` / ``"val"`` / ``"test"``。
        root: loss_mask ディレクトリ。省略時は :data:`DEFAULT_ROOT`。

    Returns:
        skip すべきフレーム basename stem の frozenset
        （例: ``{"01_1_0124", "05_1_0300", ...}``）。ファイルが空なら空 set。

    Raises:
        ValueError: ``split`` が想定外。
        FileNotFoundError: loss_mask ファイルが存在しない。
    """
    if split not in _VALID_SPLITS:
        raise ValueError(f"unknown split: {split!r} (expected one of {_VALID_SPLITS})")
    r = Path(root) if root is not None else DEFAULT_ROOT
    p = r / f"{split}.txt"
    if not p.exists():
        raise FileNotFoundError(f"loss_mask not found: {p}")
    return frozenset(line.strip() for line in p.read_text().splitlines() if line.strip())
