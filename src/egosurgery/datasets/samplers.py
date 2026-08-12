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


class DistributedRepeatFactorSampler(Sampler):
    """RFS と ``DistributedSampler`` を統合した DDP 対応 sampler（§13.2 (b)(ii)）。

    通常の RFS で生成したエポック単位の index 列を rank 間で重複なく分割する。
    これにより RFS の oversample 効果（稀少クラス画像を複数回サンプリング）と
    DDP の rank 分割（各 rank が異なる subset を学習）を 1 つの sampler で
    両立させる。

    使い方:
        sampler = DistributedRepeatFactorSampler(
            dataset, repeat_thresh=0.001,
            num_replicas=world_size, rank=rank,
        )
        loader = DataLoader(dataset, sampler=sampler, batch_size=per_gpu_bs)

    Notes:
        単一 GPU 時に DDP と同じ呼び出し側コードで動かしたい場合は、
        ``num_replicas=1, rank=0`` を渡せば通常の RFS と等価になる。
        各 epoch の最初に ``set_epoch(epoch)`` を呼ぶこと（標準
        ``DistributedSampler`` と同じ規約）。
    """

    def __init__(
        self,
        dataset,
        repeat_thresh: float = 0.001,
        num_replicas: int = 1,
        rank: int = 0,
        shuffle: bool = True,
        seed: int = 0,
        drop_last: bool = False,
    ) -> None:
        if num_replicas < 1:
            raise ValueError(f"num_replicas は 1 以上である必要があります: {num_replicas}")
        if not 0 <= rank < num_replicas:
            raise ValueError(f"rank は [0, {num_replicas}) の範囲: {rank}")
        # RFS 本体をコンポジションで保持。set_epoch を委譲する。
        self._rfs = RepeatFactorSampler(
            dataset,
            repeat_thresh=repeat_thresh,
            shuffle=shuffle,
            seed=seed,
        )
        self.num_replicas = int(num_replicas)
        self.rank = int(rank)
        self.drop_last = bool(drop_last)
        self._epoch = 0

        # 1 rank 当たりのサンプル数。drop_last=False の場合は端数を切り上げ、
        # __iter__ で頭から padding して全 rank の長さを揃える（DistributedSampler と同規約）。
        total = len(self._rfs)
        if self.drop_last:
            self._num_samples = total // self.num_replicas
        else:
            self._num_samples = math.ceil(total / self.num_replicas)
        self.total_size = self._num_samples * self.num_replicas

    # ------------------------------------------------------------------ #
    # Sampler プロトコル
    # ------------------------------------------------------------------ #
    def __iter__(self):
        # RFS が epoch ごとに違う順序で index を返すので、毎エポック再列挙する。
        self._rfs.set_epoch(self._epoch)
        indices = list(self._rfs)

        if not self.drop_last:
            # padding（不足分を頭から繰り返して total_size に揃える）。
            padding = self.total_size - len(indices)
            if padding > 0:
                indices = indices + indices[:padding]
        else:
            indices = indices[: self.total_size]

        # rank ごとに stride で分割（DistributedSampler と同じ方式）。
        indices = indices[self.rank : self.total_size : self.num_replicas]
        assert len(indices) == self._num_samples
        return iter(indices)

    def __len__(self) -> int:
        return self._num_samples

    def set_epoch(self, epoch: int) -> None:
        """エポック番号を設定する（DistributedSampler と同規約）。"""
        self._epoch = int(epoch)
        self._rfs.set_epoch(epoch)
