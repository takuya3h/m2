"""DataModule: train / val / test の DataLoader を統合管理する。

config から データセット・transforms・サンプラ・Copy-Paste を組み立て、
学習側からは ``train_dataloader()`` 等を呼ぶだけで済むようにする。

期待する config 構造（OmegaConf）:
    data:
      img_size: 518
      batch_size: 4
      num_workers: 4
      include_hand: false
      include_phase: false
      use_copypaste: false
      use_rfs: false
      repeat_thresh: 0.001
      copypaste:
        bank_dir: data/processed/copypaste_bank/
        rare_classes: [Skewer, Syringe, Forceps]
        paste_prob: 0.5
        max_paste_per_image: 3
      train: {ann_file: ..., img_dir: ..., phase_ann_file: null}
      val:   {ann_file: ..., img_dir: ..., phase_ann_file: null}
      test:  {ann_file: ..., img_dir: ..., phase_ann_file: null}

使い方:
    dm = EgoSurgeryDataModule(cfg)
    dm.setup()
    train_loader = dm.train_dataloader()
    val_loader = dm.val_dataloader()
"""

from __future__ import annotations

import torch
from torch.utils.data import DataLoader, SequentialSampler

from egosurgery.datasets.constants import RARE_CLASSES
from egosurgery.datasets.copypaste import BBoxCopyPaste
from egosurgery.datasets.ego_dataset import EgoSurgeryToolDataset
from egosurgery.datasets.samplers import RepeatFactorSampler
from egosurgery.datasets.transforms import get_train_transforms, get_val_transforms


def detection_collate_fn(batch):
    """検出タスク用 collate。可変長 target はリストのまま束ねる。

    Args:
        batch: ``(image_tensor, target_dict)`` のリスト。

    Returns:
        ``(images, targets)``。``images`` は ``(B, 3, H, W)`` の Tensor、
        ``targets`` は dict のリスト。
    """
    images, targets = zip(*batch)
    return torch.stack(list(images), dim=0), list(targets)


class EgoSurgeryDataModule:
    """EgoSurgery 用の train/val/test DataLoader を管理するモジュール。"""

    def __init__(self, cfg) -> None:
        """
        Args:
            cfg: ``cfg.data.*`` を持つ OmegaConf 設定。
        """
        self.cfg = cfg
        self.train_dataset: EgoSurgeryToolDataset | None = None
        self.val_dataset: EgoSurgeryToolDataset | None = None
        self.test_dataset: EgoSurgeryToolDataset | None = None
        self._train_sampler: RepeatFactorSampler | None = None

    # ------------------------------------------------------------------ #
    # セットアップ
    # ------------------------------------------------------------------ #
    def setup(self, stage: str | None = None) -> None:
        """config からデータセット・サンプラを構築する。"""
        data = self.cfg.data
        img_size = int(data.get("img_size", 518))
        include_hand = bool(data.get("include_hand", False))
        include_phase = bool(data.get("include_phase", False))
        limit_raw = data.get("limit", None)
        limit = int(limit_raw) if limit_raw is not None else None

        copypaste = self._build_copypaste(data)

        train_cfg = data.get("train", None)
        if train_cfg is not None:
            self.train_dataset = EgoSurgeryToolDataset(
                ann_file=train_cfg["ann_file"],
                img_dir=train_cfg["img_dir"],
                transforms=get_train_transforms(img_size),
                include_hand=include_hand,
                include_phase=include_phase,
                phase_ann_file=train_cfg.get("phase_ann_file", None),
                copypaste=copypaste,
                limit=limit,
            )
            if bool(data.get("use_rfs", False)):
                self._train_sampler = RepeatFactorSampler(
                    self.train_dataset,
                    repeat_thresh=float(data.get("repeat_thresh", 0.001)),
                )

        val_cfg = data.get("val", None)
        if val_cfg is not None:
            self.val_dataset = EgoSurgeryToolDataset(
                ann_file=val_cfg["ann_file"],
                img_dir=val_cfg["img_dir"],
                transforms=get_val_transforms(img_size),
                include_hand=include_hand,
                include_phase=include_phase,
                phase_ann_file=val_cfg.get("phase_ann_file", None),
                limit=limit,
            )

        test_cfg = data.get("test", None)
        if test_cfg is not None:
            self.test_dataset = EgoSurgeryToolDataset(
                ann_file=test_cfg["ann_file"],
                img_dir=test_cfg["img_dir"],
                transforms=get_val_transforms(img_size),
                include_hand=include_hand,
                include_phase=include_phase,
                phase_ann_file=test_cfg.get("phase_ann_file", None),
                limit=limit,
            )

    # ------------------------------------------------------------------ #
    # DataLoader
    # ------------------------------------------------------------------ #
    def train_dataloader(self) -> DataLoader:
        """学習用 DataLoader（RFS sampler + Copy-Paste）を返す。"""
        if self.train_dataset is None:
            raise RuntimeError("setup() を先に呼び、train データを設定してください。")
        # RFS sampler 使用時は shuffle を指定できないため排他にする。
        return self._build_loader(
            self.train_dataset,
            sampler=self._train_sampler,
            shuffle=self._train_sampler is None,
            drop_last=True,
        )

    def val_dataloader(self) -> DataLoader:
        """評価用 DataLoader（SequentialSampler、augmentation なし）を返す。"""
        if self.val_dataset is None:
            raise RuntimeError("setup() を先に呼び、val データを設定してください。")
        return self._build_loader(
            self.val_dataset,
            sampler=SequentialSampler(self.val_dataset),
            shuffle=False,
            drop_last=False,
        )

    def test_dataloader(self) -> DataLoader:
        """テスト用 DataLoader（SequentialSampler）を返す。"""
        if self.test_dataset is None:
            raise RuntimeError("setup() を先に呼び、test データを設定してください。")
        return self._build_loader(
            self.test_dataset,
            sampler=SequentialSampler(self.test_dataset),
            shuffle=False,
            drop_last=False,
        )

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #
    def _build_loader(self, dataset, *, sampler, shuffle: bool, drop_last: bool):
        """DataLoader を組み立てる唯一の生成点。

        sampler と shuffle は DataLoader 上で排他なので、sampler 指定時は
        shuffle を渡さない。
        """
        data = self.cfg.data
        kwargs = dict(
            batch_size=int(data.get("batch_size", 4)),
            num_workers=int(data.get("num_workers", 0)),
            collate_fn=detection_collate_fn,
            pin_memory=True,
            drop_last=drop_last,
        )
        if sampler is not None:
            kwargs["sampler"] = sampler
        else:
            kwargs["shuffle"] = shuffle
        return DataLoader(dataset, **kwargs)  # nosemgrep

    @staticmethod
    def _build_copypaste(data) -> BBoxCopyPaste | None:
        """config から Copy-Paste augmentation を構築する（無効なら ``None``）。"""
        if not bool(data.get("use_copypaste", False)):
            return None
        cp = data.get("copypaste", {})
        return BBoxCopyPaste(
            bank_dir=cp["bank_dir"],
            rare_classes=list(cp.get("rare_classes", RARE_CLASSES)),
            paste_prob=float(cp.get("paste_prob", 0.5)),
            max_paste_per_image=int(cp.get("max_paste_per_image", 3)),
        )
