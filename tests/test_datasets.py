"""データパイプライン（datasets/）の統合テスト。

実際の EgoSurgery データが無くてもテストが通るよう、``tmp_path`` に
小さなダミー画像とダミー COCO JSON を生成して検証する。

実行方法:
    PYTHONPATH=src pytest tests/test_datasets.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

# PYTHONPATH=src を付け忘れても import できるよう src/ を通す。
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from egosurgery.datasets.constants import TOOL_CLASSES, TOOL_NAME_TO_ID  # noqa: E402

_IMG_W, _IMG_H = 96, 96


# ---------------------------------------------------------------------- #
# ダミーデータ生成ヘルパ
# ---------------------------------------------------------------------- #
def _make_dummy_dataset(
    root: Path,
    num_images: int = 10,
    rare_class: str = "Skewer",
    common_class: str = "Tweezers",
) -> tuple[Path, Path]:
    """ダミー画像 + COCO JSON を生成する。

    common_class は全画像に、rare_class は 1 画像にのみ出現させ、
    長尾分布を再現する。

    Returns:
        ``(ann_file, img_dir)``。
    """
    img_dir = root / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    images, annotations = [], []
    ann_id = 0
    common_id = TOOL_NAME_TO_ID[common_class]
    rare_id = TOOL_NAME_TO_ID[rare_class]

    for img_idx in range(num_images):
        file_name = f"img_{img_idx:03d}.jpg"
        pixels = np.random.randint(0, 255, (_IMG_H, _IMG_W, 3), dtype=np.uint8)
        cv2.imwrite(str(img_dir / file_name), pixels)
        images.append(
            {"id": img_idx, "file_name": file_name, "width": _IMG_W, "height": _IMG_H}
        )

        # common クラスは全画像に 1 つ。
        annotations.append(
            {
                "id": ann_id, "image_id": img_idx, "category_id": common_id,
                "bbox": [10, 10, 20, 20], "area": 400, "iscrowd": 0,
            }
        )
        ann_id += 1
        # rare クラスは最初の 1 画像のみ。
        if img_idx == 0:
            annotations.append(
                {
                    "id": ann_id, "image_id": img_idx, "category_id": rare_id,
                    "bbox": [50, 50, 15, 15], "area": 225, "iscrowd": 0,
                }
            )
            ann_id += 1

    coco = {
        "images": images,
        "annotations": annotations,
        "categories": [dict(c) for c in TOOL_CLASSES],
    }
    ann_file = root / "instances.json"
    ann_file.write_text(json.dumps(coco), encoding="utf-8")
    return ann_file, img_dir


# ---------------------------------------------------------------------- #
# 1. データセットの読み込み
# ---------------------------------------------------------------------- #
def test_ego_dataset_loads(tmp_path):
    """COCO アノテーションからデータセットが正しく読み込めること。"""
    from egosurgery.datasets.ego_dataset import EgoSurgeryToolDataset

    ann_file, img_dir = _make_dummy_dataset(tmp_path, num_images=8)
    dataset = EgoSurgeryToolDataset(ann_file=ann_file, img_dir=img_dir)

    assert len(dataset) == 8


# ---------------------------------------------------------------------- #
# 2. __getitem__ の出力 shape
# ---------------------------------------------------------------------- #
def test_ego_dataset_returns_correct_shape(tmp_path):
    """__getitem__ が正しい shape の image と target を返すこと。"""
    from egosurgery.datasets.ego_dataset import EgoSurgeryToolDataset
    from egosurgery.datasets.transforms import get_val_transforms

    ann_file, img_dir = _make_dummy_dataset(tmp_path, num_images=5)
    dataset = EgoSurgeryToolDataset(
        ann_file=ann_file, img_dir=img_dir, transforms=get_val_transforms(128)
    )
    image, target = dataset[0]

    assert image.shape == (3, 128, 128)
    assert target["boxes"].ndim == 2 and target["boxes"].shape[1] == 4
    assert target["boxes"].shape[0] == target["labels"].shape[0]
    assert "image_id" in target and "area" in target and "iscrowd" in target


# ---------------------------------------------------------------------- #
# 3. augmentation 後の bbox が画像内に収まる
# ---------------------------------------------------------------------- #
def test_train_transforms_bbox_preserved(tmp_path):
    """train augmentation 後も bbox が画像境界内に収まること。"""
    from egosurgery.datasets.transforms import get_train_transforms

    img_size = 128
    transform = get_train_transforms(img_size)
    image = np.random.randint(0, 255, (_IMG_H, _IMG_W, 3), dtype=np.uint8)
    bboxes = [[10, 10, 40, 40], [50, 50, 80, 80]]
    labels = [1, 4]

    out = transform(image=image, bboxes=bboxes, labels=labels)

    assert out["image"].shape == (3, img_size, img_size)
    for x1, y1, x2, y2 in out["bboxes"]:
        assert 0 <= x1 <= img_size and 0 <= x2 <= img_size
        assert 0 <= y1 <= img_size and 0 <= y2 <= img_size
        assert x2 >= x1 and y2 >= y1


# ---------------------------------------------------------------------- #
# 4. Copy-Paste がインスタンスを追加する
# ---------------------------------------------------------------------- #
def test_copypaste_adds_instances(tmp_path):
    """Copy-Paste 後に target の bbox 数が増えること。"""
    from egosurgery.datasets.copypaste import BBoxCopyPaste

    # crop バンクを作成（rare クラス Skewer に crop を 3 枚）。
    bank_dir = tmp_path / "bank"
    skewer_dir = bank_dir / "Skewer"
    skewer_dir.mkdir(parents=True)
    for i in range(3):
        crop = np.random.randint(0, 255, (16, 16, 3), dtype=np.uint8)
        cv2.imwrite(str(skewer_dir / f"crop_{i}.jpg"), crop)

    cp = BBoxCopyPaste(
        bank_dir=bank_dir,
        rare_classes=["Skewer"],
        paste_prob=1.0,
        max_paste_per_image=3,
        seed=0,
    )
    image = np.random.randint(0, 255, (_IMG_H, _IMG_W, 3), dtype=np.uint8)
    target = {"boxes": np.array([[5, 5, 15, 15]], dtype=np.float32), "labels": [1]}

    _, new_target = cp(image, target)

    assert len(new_target["boxes"]) > 1
    assert len(new_target["labels"]) == len(new_target["boxes"])


# ---------------------------------------------------------------------- #
# 4b. Copy-Paste の対象が Skewer / Syringe のみで Forceps を含まない
#     【§v2 訂正 / 2026/05/24】Forceps 12.21% は稀少ではない
# ---------------------------------------------------------------------- #
def test_copypaste_targets_only_skewer_syringe(tmp_path):
    """Copy-Paste 後に追加される label が Skewer / Syringe のみで、
    Forceps を含まないことを確認する。"""
    from egosurgery.datasets.constants import RARE_CLASSES, TOOL_NAME_TO_ID
    from egosurgery.datasets.copypaste import BBoxCopyPaste

    # 1. constants の RARE_CLASSES が Skewer / Syringe のみであること（不変条件）。
    assert set(RARE_CLASSES) == {"Skewer", "Syringe"}, (
        f"RARE_CLASSES に Forceps 等が混入: {RARE_CLASSES}"
    )

    # 2. crop バンクに Skewer / Syringe の crop を用意する。
    bank_dir = tmp_path / "bank"
    for class_name in ("Skewer", "Syringe"):
        cls_dir = bank_dir / class_name
        cls_dir.mkdir(parents=True)
        for i in range(3):
            crop = np.random.randint(0, 255, (16, 16, 3), dtype=np.uint8)
            cv2.imwrite(str(cls_dir / f"crop_{i}.jpg"), crop)

    # 3. rare_classes を省略すると default の RARE_CLASSES が使われる。
    cp = BBoxCopyPaste(
        bank_dir=bank_dir,
        paste_prob=1.0,
        max_paste_per_image=5,
        seed=0,
    )
    # 4. 何枚かの画像に適用し、追加された label が Skewer / Syringe のみで
    #    Forceps (id=2) が混入しないことを確認する。
    forceps_id = TOOL_NAME_TO_ID["Forceps"]
    allowed_ids = {TOOL_NAME_TO_ID[n] for n in RARE_CLASSES}
    n_pasted = 0
    for _ in range(20):
        image = np.random.randint(0, 255, (_IMG_H, _IMG_W, 3), dtype=np.uint8)
        target = {"boxes": np.array([[5, 5, 15, 15]], dtype=np.float32), "labels": [1]}
        _, new_target = cp(image, target)
        # 元の 1 件を超えて追加された label を抽出する。
        extra = list(new_target["labels"])[1:]
        for lbl in extra:
            assert lbl != forceps_id, "Forceps が Copy-Paste 対象になっている"
            assert lbl in allowed_ids, f"許可外クラス {lbl} が追加された"
            n_pasted += 1
    assert n_pasted > 0, "Copy-Paste で 1 件も追加されなかった（テスト前提崩壊）"


# ---------------------------------------------------------------------- #
# 5. RFS が稀少クラスを oversample する
# ---------------------------------------------------------------------- #
def test_rfs_sampler_oversamples_rare(tmp_path):
    """RFS で稀少クラスの repeat factor > 1、高頻度クラスは = 1 であること。"""
    from egosurgery.datasets.ego_dataset import EgoSurgeryToolDataset
    from egosurgery.datasets.samplers import RepeatFactorSampler

    ann_file, img_dir = _make_dummy_dataset(tmp_path, num_images=10)
    dataset = EgoSurgeryToolDataset(ann_file=ann_file, img_dir=img_dir)

    # ダミーデータ規模（10 枚）に合わせ閾値を選ぶ:
    # Skewer は 1/10 画像 (f=0.1)、Tweezers は 10/10 (f=1.0)。
    sampler = RepeatFactorSampler(dataset, repeat_thresh=0.5)

    rare_id = TOOL_NAME_TO_ID["Skewer"]
    common_id = TOOL_NAME_TO_ID["Tweezers"]
    assert sampler.category_repeat_factors[rare_id] > 1.0
    assert sampler.category_repeat_factors[common_id] == pytest.approx(1.0)
    # 稀少クラスを含む画像 0 の repeat factor も 1 を超える。
    assert sampler.repeat_factors[0] > 1.0


# ---------------------------------------------------------------------- #
# 6. DataModule が train/val の DataLoader を返す
# ---------------------------------------------------------------------- #
def test_datamodule_creates_loaders(tmp_path):
    """DataModule が train/val の DataLoader を生成し、1 バッチ取り出せること。"""
    from omegaconf import OmegaConf
    from torch.utils.data import DataLoader

    from egosurgery.datasets.datamodule import EgoSurgeryDataModule

    ann_file, img_dir = _make_dummy_dataset(tmp_path, num_images=6)
    cfg = OmegaConf.create(
        {
            "data": {
                "img_size": 128,
                "batch_size": 2,
                "num_workers": 0,
                "include_hand": False,
                "include_phase": False,
                "use_copypaste": False,
                "use_rfs": True,
                "repeat_thresh": 0.5,
                "train": {"ann_file": str(ann_file), "img_dir": str(img_dir)},
                "val": {"ann_file": str(ann_file), "img_dir": str(img_dir)},
            }
        }
    )

    dm = EgoSurgeryDataModule(cfg)
    dm.setup()
    train_loader = dm.train_dataloader()
    val_loader = dm.val_dataloader()

    assert isinstance(train_loader, DataLoader)
    assert isinstance(val_loader, DataLoader)

    images, targets = next(iter(val_loader))
    assert images.shape[1:] == (3, 128, 128)
    assert len(targets) == images.shape[0]
