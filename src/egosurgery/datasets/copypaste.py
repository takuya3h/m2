"""bbox-level Simple Copy-Paste augmentation。

稀少クラス（Skewer / Syringe）の術具を事前に切り出したバンクから、
学習画像へランダムに貼り付けてインスタンス数を水増しする。
mask は使わない（Phase-0 主経路）。

【2026/05/24 v2 訂正】貼り付け対象は Skewer / Syringe の 2 クラスのみ。
Forceps は出現割合 12.21% でトップ3頻出クラスのため対象から除外する。

使い方:
    cp = BBoxCopyPaste(
        bank_dir="data/processed/copypaste_bank/",
        rare_classes=["Skewer", "Syringe"],  # Forceps は含めない
        paste_prob=0.5,
        max_paste_per_image=3,
    )
    image, target = cp(image, target)
    # image  : np.ndarray (H, W, 3) uint8（RGB）
    # target : {"boxes": (N,4) xyxy, "labels": (N,)}  貼り付け分が追加される

将来拡張（研究計画 §3.3）: temporal-consistent copy-paste — 同一クリップ内で
時間的に整合した位置に貼り付ける手法が提案手法として予定されている。
本実装では frame 独立の簡易版に留め、``temporal_consistent`` フラグを
予約しておく（True 指定時は現状 NotImplementedError）。
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from egosurgery.datasets.constants import ALL_NAME_TO_ID

_IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".bmp")


def _iou(box: np.ndarray, boxes: np.ndarray) -> np.ndarray:
    """1 つの box と複数 boxes との IoU を返す（xyxy 形式）。"""
    if boxes.size == 0:
        return np.zeros((0,), dtype=np.float32)
    x1 = np.maximum(box[0], boxes[:, 0])
    y1 = np.maximum(box[1], boxes[:, 1])
    x2 = np.minimum(box[2], boxes[:, 2])
    y2 = np.minimum(box[3], boxes[:, 3])
    inter = np.clip(x2 - x1, 0, None) * np.clip(y2 - y1, 0, None)
    area = (box[2] - box[0]) * (box[3] - box[1])
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    union = area + areas - inter
    return np.where(union > 0, inter / union, 0.0).astype(np.float32)


class BBoxCopyPaste:
    """稀少クラス優先の bbox-level Copy-Paste augmentation。"""

    def __init__(
        self,
        bank_dir: str | Path,
        rare_classes: list[str] | None = None,
        paste_prob: float = 0.5,
        max_paste_per_image: int = 3,
        max_iou: float = 0.3,
        scale_range: tuple[float, float] = (0.6, 1.4),
        seed: int | None = None,
        temporal_consistent: bool = False,
    ) -> None:
        """
        Args:
            bank_dir: ``{bank_dir}/{class_name}/*.jpg`` の crop バンク。
            rare_classes: 貼り付け対象の稀少クラス名。省略時は
                :data:`~egosurgery.datasets.constants.RARE_CLASSES`
                （Skewer / Syringe）を使う。
            paste_prob: 画像ごとに Copy-Paste を適用する確率。
            max_paste_per_image: 1 画像あたりの最大貼り付け数。
            max_iou: 既存 bbox との IoU がこの値未満なら貼り付けを許可。
            scale_range: crop の拡縮率の範囲。
            seed: 乱数シード（``None`` で非決定的）。
            temporal_consistent: 将来拡張（研究計画 §3.3）の予約フラグ。
                現状は ``False`` のみサポート。``True`` 指定時は明示的に
                ``NotImplementedError`` を送出する。
        """
        if rare_classes is None:
            # 遅延 import で循環依存を避ける。
            from egosurgery.datasets.constants import RARE_CLASSES
            rare_classes = list(RARE_CLASSES)
        if temporal_consistent:
            raise NotImplementedError(
                "temporal_consistent=True は研究計画 §3.3 で予定されているが "
                "本実装では未対応（frame 独立の簡易版のみ）。"
            )
        self.bank_dir = Path(bank_dir)
        self.rare_classes = list(rare_classes)
        self.paste_prob = float(paste_prob)
        self.max_paste_per_image = int(max_paste_per_image)
        self.max_iou = float(max_iou)
        self.scale_range = scale_range
        self.temporal_consistent = bool(temporal_consistent)
        self.rng = np.random.default_rng(seed)

        # クラスごとに crop ファイル一覧を索引化する。
        self.bank: dict[str, list[Path]] = {}
        for class_name in self.rare_classes:
            class_dir = self.bank_dir / class_name
            if not class_dir.is_dir():
                continue
            crops = sorted(
                p for p in class_dir.iterdir()
                if p.suffix.lower() in _IMAGE_SUFFIXES
            )
            if crops:
                self.bank[class_name] = crops

    @property
    def is_empty(self) -> bool:
        """利用可能な crop が 1 つも無いとき ``True``。"""
        return len(self.bank) == 0

    def __call__(self, image: np.ndarray, target: dict):
        """画像に Copy-Paste を適用する。

        Args:
            image: ``(H, W, 3) uint8`` の RGB 画像。
            target: ``"boxes"``（xyxy）と ``"labels"`` を持つ辞書。

        Returns:
            更新された ``(image, target)``。バンクが空、または確率により
            適用しなかった場合は入力をそのまま返す。
        """
        boxes = np.asarray(target.get("boxes", []), dtype=np.float32).reshape(-1, 4)
        labels = list(np.asarray(target.get("labels", [])).reshape(-1).tolist())

        if self.is_empty or self.rng.random() >= self.paste_prob:
            return image, {**target, "boxes": boxes, "labels": labels}

        image = np.ascontiguousarray(image).copy()
        height, width = image.shape[:2]
        available = list(self.bank.keys())
        num_paste = int(self.rng.integers(1, self.max_paste_per_image + 1))

        for _ in range(num_paste):
            class_name = available[int(self.rng.integers(len(available)))]
            crop = self._load_crop(class_name)
            if crop is None:
                continue
            placement = self._sample_placement(crop, height, width, boxes)
            if placement is None:
                continue
            resized, (x1, y1, x2, y2) = placement
            image[y1:y2, x1:x2] = resized
            boxes = np.vstack([boxes, np.array([[x1, y1, x2, y2]], dtype=np.float32)])
            labels.append(ALL_NAME_TO_ID.get(class_name, 0))

        return image, {**target, "boxes": boxes, "labels": labels}

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #
    def _load_crop(self, class_name: str) -> np.ndarray | None:
        """指定クラスからランダムに 1 枚の crop を RGB で読み込む。"""
        paths = self.bank[class_name]
        path = paths[int(self.rng.integers(len(paths)))]
        crop = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if crop is None:
            return None
        return cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

    def _sample_placement(self, crop, height, width, boxes):
        """貼り付け位置を探索する。既存 bbox と重なりすぎたら諦める。

        Returns:
            ``(リサイズ済み crop, (x1, y1, x2, y2))`` または ``None``。
        """
        scale = self.rng.uniform(*self.scale_range)
        crop_h = max(1, min(int(crop.shape[0] * scale), height))
        crop_w = max(1, min(int(crop.shape[1] * scale), width))
        resized = cv2.resize(crop, (crop_w, crop_h), interpolation=cv2.INTER_LINEAR)

        # 数回ランダムに位置を試す。
        for _ in range(8):
            x1 = int(self.rng.integers(0, max(1, width - crop_w + 1)))
            y1 = int(self.rng.integers(0, max(1, height - crop_h + 1)))
            candidate = np.array(
                [x1, y1, x1 + crop_w, y1 + crop_h], dtype=np.float32
            )
            if _iou(candidate, boxes).max(initial=0.0) < self.max_iou:
                return resized, (x1, y1, x1 + crop_w, y1 + crop_h)
        return None
