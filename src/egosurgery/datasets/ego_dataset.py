"""EgoSurgery-Tool のデータセットクラス。

COCO 形式の bbox アノテーションを読み込み、検出モデルが期待する
``(image, target)`` を返す。bbox は内部で COCO の ``xywh`` から
``xyxy`` へ変換し、以降の全経路で xyxy に統一する。

使い方:
    dataset = EgoSurgeryToolDataset(
        ann_file="data/annotations/egosurgery_tool/instances_train.json",
        img_dir="data/raw/ego/train/",
        transforms=get_train_transforms(),
        include_hand=False,     # S0 では False、S2 で True
        include_phase=False,    # S0 では False、S3 で True
        phase_ann_file=None,    # S3 以降で指定
    )
    image, target = dataset[0]
    # image : Tensor (3, H, W)
    # target: {"boxes": (N,4) xyxy, "labels": (N,), "image_id": int,
    #          "area": (N,), "iscrowd": (N,), ["phase": int]}
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np
import torch
from torch.utils.data import Dataset

from egosurgery.datasets.constants import RARE_CLASSES as _RARE_CLASSES
from egosurgery.datasets.constants import TOOL_CATEGORY_IDS


class EgoSurgeryToolDataset(Dataset):
    """EgoSurgery-Tool の COCO 形式 bbox データセット。

    Class attributes:
        RARE_CLASSES: 稀少クラス名のタプル（AP_rare / Copy-Paste 対象）。
            constants.RARE_CLASSES (Skewer / Syringe) の凍結スナップショット。
            §v2 訂正で Forceps (12.21%) は AP_common 側に分類。
    """

    RARE_CLASSES: tuple[str, ...] = tuple(_RARE_CLASSES)

    def __init__(
        self,
        ann_file: str | Path,
        img_dir: str | Path,
        transforms=None,
        include_hand: bool = False,
        include_phase: bool = False,
        phase_ann_file: str | Path | None = None,
        copypaste=None,
        limit: int | None = None,
    ) -> None:
        """
        Args:
            ann_file: COCO 形式アノテーション JSON のパス。
            img_dir: 画像が置かれたディレクトリ。
            transforms: albumentations の ``Compose``（``None`` 可）。
            include_hand: ``True`` で手 4 クラス（id 16-19）も含める。
            include_phase: ``True`` で target に手術工程ラベルを追加する。
            phase_ann_file: 工程アノテーション JSON（``include_phase`` 時）。
            copypaste: ``BBoxCopyPaste`` 等の callable（``None`` 可）。
                指定時は transforms の前段で Copy-Paste を適用する。
            limit: 指定時は先頭 ``limit`` 枚に画像を制限する（スモーク用）。
        """
        from pycocotools.coco import COCO

        self.ann_file = str(ann_file)
        self.img_dir = Path(img_dir)
        self.transforms = transforms
        self.include_hand = include_hand
        self.include_phase = include_phase
        self.copypaste = copypaste

        self.coco = COCO(self.ann_file)
        self.image_ids = sorted(self.coco.getImgIds())
        if limit is not None:
            self.image_ids = self.image_ids[: int(limit)]

        # include_hand=False のとき tool 15 クラスのみを残すフィルタ。
        # None は「フィルタしない＝全カテゴリを通す」を意味する。
        self.allowed_cat_ids: frozenset | None = (
            None if include_hand else TOOL_CATEGORY_IDS
        )

        self.phase_map: dict = {}
        if include_phase and phase_ann_file is not None:
            self.phase_map = self._load_phase_annotations(phase_ann_file)

    # ------------------------------------------------------------------ #
    # Dataset プロトコル
    # ------------------------------------------------------------------ #
    def __len__(self) -> int:
        return len(self.image_ids)

    def __getitem__(self, index: int):
        img_id = self.image_ids[index]
        img_info = self.coco.loadImgs(img_id)[0]
        image = self._read_image(img_info)

        boxes, labels, areas, iscrowd = [], [], [], []
        for ann in self.coco.loadAnns(self.coco.getAnnIds(imgIds=img_id)):
            cat_id = ann["category_id"]
            if self.allowed_cat_ids is not None and cat_id not in self.allowed_cat_ids:
                continue
            x, y, w, h = ann["bbox"]  # COCO は xywh
            boxes.append([x, y, x + w, y + h])  # -> xyxy
            labels.append(cat_id)
            areas.append(float(ann.get("area", w * h)))
            iscrowd.append(int(ann.get("iscrowd", 0)))

        # Copy-Paste は augmentation transforms の前段（生画像 + xyxy）で適用する。
        if self.copypaste is not None:
            cp_target = {
                "boxes": np.asarray(boxes, dtype=np.float32).reshape(-1, 4),
                "labels": np.asarray(labels, dtype=np.int64),
            }
            image, cp_target = self.copypaste(image, cp_target)
            boxes = [list(map(float, b)) for b in np.asarray(cp_target["boxes"]).reshape(-1, 4)]
            labels = [int(v) for v in np.asarray(cp_target["labels"]).reshape(-1)]
            areas = [(b[2] - b[0]) * (b[3] - b[1]) for b in boxes]
            iscrowd = [0] * len(boxes)

        image, boxes, labels, areas, iscrowd = self._apply_transforms(
            image, boxes, labels, areas, iscrowd
        )

        target = {
            "boxes": torch.as_tensor(boxes, dtype=torch.float32).reshape(-1, 4),
            "labels": torch.as_tensor(labels, dtype=torch.int64),
            "image_id": int(img_id),
            "area": torch.as_tensor(areas, dtype=torch.float32),
            "iscrowd": torch.as_tensor(iscrowd, dtype=torch.int64),
        }
        if self.include_phase:
            target["phase"] = self._lookup_phase(img_info)

        return image, target

    # ------------------------------------------------------------------ #
    # RFS サンプラ向けインターフェース
    # ------------------------------------------------------------------ #
    def get_cat_ids(self, index: int) -> list[int]:
        """画像 ``index`` に出現するカテゴリ ID のリストを返す。

        Repeat Factor Sampling がクラス頻度を集計するために用いる。
        """
        img_id = self.image_ids[index]
        cats = [
            ann["category_id"]
            for ann in self.coco.loadAnns(self.coco.getAnnIds(imgIds=img_id))
        ]
        if self.allowed_cat_ids is not None:
            cats = [c for c in cats if c in self.allowed_cat_ids]
        return cats

    # ------------------------------------------------------------------ #
    # 内部ヘルパ
    # ------------------------------------------------------------------ #
    def _read_image(self, img_info: dict) -> np.ndarray:
        """画像を RGB の ``np.ndarray (H, W, 3) uint8`` で読み込む。

        ファイルが存在しない / 0 バイト等で読めない場合は、COCO の
        ``width`` / ``height`` に基づく黒画像を返す（実体未配置の
        split でもパイプラインが落ちないようにするため）。
        """
        path = self.img_dir / img_info["file_name"]
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            height = int(img_info.get("height", 518))
            width = int(img_info.get("width", 518))
            return np.zeros((height, width, 3), dtype=np.uint8)
        return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    def _apply_transforms(self, image, boxes, labels, areas, iscrowd):
        """transforms を適用する。``None`` のときは手動でテンソル化する。"""
        if self.transforms is not None:
            out = self.transforms(image=image, bboxes=boxes, labels=labels)
            image = out["image"]
            new_boxes = [list(b) for b in out["bboxes"]]
            new_labels = list(out["labels"])
            # bbox がクリップ等で除外された場合は area/iscrowd も対応づける。
            # 件数が変わるため area/iscrowd は box から再計算する。
            areas = [
                (b[2] - b[0]) * (b[3] - b[1]) for b in new_boxes
            ]
            iscrowd = [0] * len(new_boxes)
            return image, new_boxes, new_labels, areas, iscrowd

        # transforms 未指定: HWC uint8 -> CHW float[0,1] テンソル。
        tensor = torch.from_numpy(image).permute(2, 0, 1).contiguous().float() / 255.0
        return tensor, boxes, labels, areas, iscrowd

    @staticmethod
    def _load_phase_annotations(phase_ann_file: str | Path) -> dict:
        """工程アノテーション JSON を ``(video_id, frame_id) -> phase`` に変換する。

        想定フォーマット: ``{"video_id": str, "frames": [{"frame_id": int,
        "phase": int}]}`` のオブジェクト、またはそのリスト。
        """
        data = json.loads(Path(phase_ann_file).read_text(encoding="utf-8"))
        records = data if isinstance(data, list) else [data]
        phase_map: dict = {}
        for record in records:
            video_id = str(record.get("video_id", ""))
            for frame in record.get("frames", []):
                phase_map[(video_id, int(frame["frame_id"]))] = int(frame["phase"])
        return phase_map

    def _lookup_phase(self, img_info: dict) -> int:
        """画像に対応する手術工程ラベルを返す（不明なら 0）。"""
        video_id = str(img_info.get("video_id", ""))
        frame_id = img_info.get("frame_id")
        if frame_id is not None:
            return self.phase_map.get((video_id, int(frame_id)), 0)
        return 0
