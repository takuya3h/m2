"""Repeat Factor Sampling (RFS)。

LVIS (Gupta+ CVPR 2019) の Repeat Factor Sampling を検出データセットに
適用する。稀少クラスを含む画像をエポック内で複数回サンプリングし、
長尾分布の学習を底上げする。

アルゴリズム:
    1. カテゴリ c の画像頻度 f_c = (c を含む画像数) / (全画像数)
    2. カテゴリ repeat factor  r_c = max(1, sqrt(t / f_c))
    3. 画像 repeat factor      r_i = max_{c in image} r_c
    4. エポック内で画像 i を floor(r_i) 回 + 確率 frac(r_i) で 1 回追加

使い方:
    sampler = RepeatFactorSampler(dataset, repeat_thresh=0.001)
    loader = DataLoader(dataset, sampler=sampler, batch_size=4)
"""

from __future__ import annotations

import math

import torch
from torch.utils.data import Sampler


class RepeatFactorSampler(Sampler):
    """LVIS 準拠の Repeat Factor Sampler。"""

    def __init__(
        self,
        dataset,
        repeat_thresh: float = 0.001,
        shuffle: bool = True,
        seed: int = 0,
    ) -> None:
        """
        Args:
            dataset: ``get_cat_ids(idx) -> list[int]`` を持つデータセット。
            repeat_thresh: 閾値 t。``f_c < t`` のカテゴリが oversample される。
            shuffle: エポックごとにインデックスをシャッフルするか。
            seed: 乱数シード。
        """
        self.dataset = dataset
        self.repeat_thresh = float(repeat_thresh)
        self.shuffle = shuffle
        self.seed = int(seed)
        self._epoch = 0

        self._cat_ids_per_image = self._collect_cat_ids()
        # カテゴリ別 repeat factor（テスト・解析用に公開する）。
        self.category_repeat_factors = self._compute_category_repeat_factors()
        # 画像別 repeat factor。
        self.repeat_factors = self._compute_image_repeat_factors()
        self._num_samples = int(round(sum(self.repeat_factors)))

    # ------------------------------------------------------------------ #
    # Sampler プロトコル
    # ------------------------------------------------------------------ #
    def __iter__(self):
        generator = torch.Generator()
        generator.manual_seed(self.seed + self._epoch)

        indices: list[int] = []
        for image_idx, factor in enumerate(self.repeat_factors):
            repeats = int(math.floor(factor))
            # 小数部は確率的に切り上げる（stochastic rounding）。
            if torch.rand(1, generator=generator).item() < (factor - repeats):
                repeats += 1
            indices.extend([image_idx] * repeats)

        if self.shuffle:
            perm = torch.randperm(len(indices), generator=generator).tolist()
            indices = [indices[p] for p in perm]
        return iter(indices)

    def __len__(self) -> int:
        return self._num_samples

    def set_epoch(self, epoch: int) -> None:
        """エポック番号を設定する（シャッフルの再現性のため）。"""
        self._epoch = int(epoch)

    # ------------------------------------------------------------------ #
    # 内部計算
    # ------------------------------------------------------------------ #
    def _collect_cat_ids(self) -> list[list[int]]:
        """各画像に出現するカテゴリ ID のリストを集める。"""
        if hasattr(self.dataset, "get_cat_ids"):
            return [
                list(self.dataset.get_cat_ids(i)) for i in range(len(self.dataset))
            ]
        # フォールバック: dataset の各要素がカテゴリ ID のリストである場合。
        return [list(item) for item in self.dataset]

    def _compute_category_repeat_factors(self) -> dict[int, float]:
        """カテゴリ別 repeat factor r_c = max(1, sqrt(t / f_c)) を計算する。"""
        num_images = max(len(self._cat_ids_per_image), 1)

        image_count: dict[int, int] = {}
        for cat_ids in self._cat_ids_per_image:
            for cat_id in set(cat_ids):
                image_count[cat_id] = image_count.get(cat_id, 0) + 1

        repeat_factors: dict[int, float] = {}
        for cat_id, count in image_count.items():
            freq = count / num_images
            repeat_factors[cat_id] = max(1.0, math.sqrt(self.repeat_thresh / freq))
        return repeat_factors

    def _compute_image_repeat_factors(self) -> list[float]:
        """画像別 repeat factor r_i = max_{c in image} r_c を計算する。"""
        factors: list[float] = []
        for cat_ids in self._cat_ids_per_image:
            unique = set(cat_ids)
            if unique:
                factors.append(
                    max(self.category_repeat_factors[c] for c in unique)
                )
            else:
                # アノテーションの無い画像は等倍。
                factors.append(1.0)
        return factors
