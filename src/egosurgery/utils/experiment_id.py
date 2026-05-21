"""実験 ID の生成ユーティリティ。

命名規則: ``{step}_{seq:03d}_{description}_seed{seed}``

例:
    generate_experiment_id("experiments/baselines", "s0", "maskdino_bbox", 42)
    -> "s0_001_maskdino_bbox_seed42"   (初回)
    -> "s0_002_maskdino_bbox_seed42"   (2 回目。同じ step の既存フォルダがある場合)

連番は「``base_dir`` 配下の既存フォルダのうち同一 step を持つものを走査し、
その最大連番 + 1」で決定する。フォルダ構造そのものを唯一の真実とするため、
別途カウンタファイルを持たない。

``experiment_manager.ExperimentManager`` から呼び出される。
"""

from __future__ import annotations

import re
from pathlib import Path


def next_sequence(base_dir: str | Path, step: str) -> int:
    """``base_dir`` 配下で同一 step を持つフォルダの次の連番を返す。

    Args:
        base_dir: 走査対象ディレクトリ（例: ``experiments/baselines``）。
        step: ステップ識別子（例: ``s0`` / ``a1``）。

    Returns:
        次に使うべき連番（既存が無ければ 1）。
    """
    base = Path(base_dir)
    if not base.exists():
        return 1

    pattern = re.compile(rf"^{re.escape(step)}_(\d{{3}})_")
    max_seq = 0
    for child in base.iterdir():
        if not child.is_dir():
            continue
        match = pattern.match(child.name)
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return max_seq + 1


def generate_experiment_id(
    base_dir: str | Path,
    step: str,
    description: str,
    seed: int,
) -> str:
    """連番付き実験 ID を生成する。

    Args:
        base_dir: 連番採番の走査対象（例: ``experiments/baselines``）。
        step: ステップ識別子（例: ``s0`` / ``a1``）。
        description: 実験内容の短い説明（例: ``maskdino_bbox``）。
        seed: 乱数シード。

    Returns:
        ``{step}_{seq:03d}_{description}_seed{seed}`` 形式の実験 ID。
    """
    seq = next_sequence(base_dir, step)
    return f"{step}_{seq:03d}_{description}_seed{seed}"
