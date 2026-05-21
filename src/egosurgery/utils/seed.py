"""再現性のための seed 固定ユーティリティ。

random, numpy, torch, cuda, cudnn の全乱数生成器を固定する。
このプロジェクトでは全実験で同一 seed（既定 42）を用い、
Δ 基準点の比較が乱数差ではなく設計差のみに帰着するよう保証する。
"""

from __future__ import annotations


def seed_everything(seed: int = 42) -> None:
    """全乱数生成器のシードを固定する。

    Args:
        seed: 固定するシード値。既定は 42。

    Notes:
        ``torch`` / ``numpy`` は関数内で遅延 import する。これにより
        これらが未インストールの環境でもモジュール import 自体は成功し、
        軽量な再現性検証（import チェック）が通る。
    """
    import os
    import random

    import numpy as np
    import torch

    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
