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
from albumentations.pytorch import ToTensorV2

# ImageNet 統計（DINOv2 backbone の事前学習に整合）。
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


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
