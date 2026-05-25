"""学習用 augmentation と評価用 preprocessing。

augmentation（学習時の汎化目的の確率的変換）と preprocessing（評価時の
決定的なリサイズ・正規化）を明確に分離する。両者とも bbox を同時に
変換するため、albumentations の ``BboxParams`` を共有する。

使い方:
    train_tfm = get_train_transforms(img_size=518)
    val_tfm = get_val_transforms(img_size=518)

    transformed = train_tfm(image=img_np, bboxes=boxes_xyxy, labels=labels)
    # transformed["image"]  : Tensor (3, H, W)
    # transformed["bboxes"] : list[(x1, y1, x2, y2)]  画像内にクリップ済み
    # transformed["labels"] : list[int]
"""

from __future__ import annotations

import albumentations as A
import numpy as np
from albumentations.pytorch import ToTensorV2

# ImageNet 統計（DINOv2 backbone の事前学習に整合）。
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


class ArtificialGlovesAugmentation(A.ImageOnlyTransform):
    """手袋色（青/紫/緑系の医療手袋色相）を画像全体に薄く乗せる augmentation。

    RoHan 系の Artificial Gloves augmentation の簡易実装。手袋着用シーンの
    分布シフトを学習時に擬似的に作り、S2 hand 検出のドメインロバスト化に
    寄与する。HSV 空間で色相シフト + saturation 持ち上げの組合せ。
    bbox には影響しない（ImageOnlyTransform）。

    Args:
        hue_shift_range: HSV の hue 加算範囲（OpenCV では 0-179）。
            既定 (90, 130) は青〜紫の医療手袋色域。
        sat_boost_range: saturation 乗算範囲。
        intensity: オーバーレイ強度（元画像との線形ブレンド比、0-1）。
        p: 適用確率（既定 0.3、v2 仕様）。
    """

    def __init__(
        self,
        hue_shift_range: tuple[int, int] = (90, 130),
        sat_boost_range: tuple[float, float] = (1.1, 1.4),
        intensity: float = 0.25,
        p: float = 0.3,
    ) -> None:
        super().__init__(p=p)
        self.hue_shift_range = hue_shift_range
        self.sat_boost_range = sat_boost_range
        self.intensity = float(intensity)

    def apply(self, img: np.ndarray, **params) -> np.ndarray:  # type: ignore[override]
        import cv2

        if img.dtype != np.uint8:
            return img
        rng = np.random.default_rng()
        hue_shift = int(rng.integers(self.hue_shift_range[0], self.hue_shift_range[1] + 1))
        sat_boost = float(rng.uniform(*self.sat_boost_range))
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV).astype(np.int16)
        hsv[..., 0] = (hsv[..., 0] + hue_shift) % 180
        hsv[..., 1] = np.clip(hsv[..., 1] * sat_boost, 0, 255)
        tinted = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        return cv2.addWeighted(img, 1.0 - self.intensity, tinted, self.intensity, 0)

    def get_transform_init_args_names(self):
        return ("hue_shift_range", "sat_boost_range", "intensity")


class BloodSplatterAugmentation(A.ImageOnlyTransform):
    """血液テクスチャ（暗赤色の小斑点）を画像上にランダム配置する augmentation。

    術中の血液付着シーンへの外観ロバスト性を学習時に持たせる目的。
    bbox には影響しない（ImageOnlyTransform）。

    Args:
        num_splatters: 1 画像あたりの斑点数の範囲。
        radius_range: 各斑点の半径ピクセル範囲。
        color: RGB の暗赤色（既定 (140, 20, 20)）。
        alpha_range: 斑点の透明度（0-1）の範囲。
        p: 適用確率（既定 0.2、v2 仕様）。
    """

    def __init__(
        self,
        num_splatters: tuple[int, int] = (5, 25),
        radius_range: tuple[int, int] = (2, 12),
        color: tuple[int, int, int] = (140, 20, 20),
        alpha_range: tuple[float, float] = (0.4, 0.8),
        p: float = 0.2,
    ) -> None:
        super().__init__(p=p)
        self.num_splatters = num_splatters
        self.radius_range = radius_range
        self.color = color
        self.alpha_range = alpha_range

    def apply(self, img: np.ndarray, **params) -> np.ndarray:  # type: ignore[override]
        import cv2

        if img.dtype != np.uint8:
            return img
        rng = np.random.default_rng()
        h, w = img.shape[:2]
        n = int(rng.integers(self.num_splatters[0], self.num_splatters[1] + 1))
        out = img.copy()
        for _ in range(n):
            cx = int(rng.integers(0, w))
            cy = int(rng.integers(0, h))
            r = int(rng.integers(self.radius_range[0], self.radius_range[1] + 1))
            alpha = float(rng.uniform(*self.alpha_range))
            overlay = out.copy()
            cv2.circle(overlay, (cx, cy), r, self.color, thickness=-1)
            out = cv2.addWeighted(overlay, alpha, out, 1.0 - alpha, 0)
        return out

    def get_transform_init_args_names(self):
        return ("num_splatters", "radius_range", "color", "alpha_range")


def _bbox_params() -> A.BboxParams:
    """学習・評価で共有する bbox 変換設定。

    ``format="pascal_voc"`` は絶対座標の xyxy。``clip=True`` により
    変換後の bbox は常に画像境界内へクリップされる。
    """
    return A.BboxParams(
        format="pascal_voc",
        label_fields=["labels"],
        min_visibility=0.0,
        min_area=0.0,
        clip=True,
    )


def get_train_transforms(img_size: int = 518) -> A.Compose:
    """学習用 augmentation パイプラインを返す。

    open surgery 特有の照明変動（無影灯反射・色温度差）に対応するため、
    色系の augmentation を強めに設定している。

    Args:
        img_size: 出力画像の一辺（既定 518 = DINOv2 ViT/14 の 37 patch）。

    Returns:
        ``albumentations.Compose``。
    """
    return A.Compose(
        [
            A.RandomResizedCrop(
                size=(img_size, img_size),
                scale=(0.8, 1.0),
                ratio=(0.75, 1.3333),
                p=1.0,
            ),
            A.HorizontalFlip(p=0.5),
            # open surgery の照明変動対策（色温度・露出のばらつき）。
            A.ColorJitter(
                brightness=0.3, contrast=0.3, saturation=0.2, hue=0.1, p=0.8
            ),
            # 無影灯反射によるハイライト対策。
            A.RandomBrightnessContrast(p=0.3),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ],
        bbox_params=_bbox_params(),
    )


def get_val_transforms(img_size: int = 518) -> A.Compose:
    """評価用 preprocessing パイプラインを返す（決定的）。

    Args:
        img_size: 出力画像の一辺。

    Returns:
        ``albumentations.Compose``（Resize + Normalize のみ）。
    """
    return A.Compose(
        [
            A.Resize(height=img_size, width=img_size),
            A.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            ToTensorV2(),
        ],
        bbox_params=_bbox_params(),
    )
