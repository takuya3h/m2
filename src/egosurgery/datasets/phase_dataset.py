"""S3（手術工程認識）用の (画像, phase ラベル) データセット。

``data/annotations/egosurgery_phase/*.csv`` は動画ごとに ``Frame, Phase`` を持ち、
``Frame`` は ``<vidid>_<sess>_<fid>`` 形式の文字列で、画像は
``data/raw/ego/<split>/<vidid>/<vidid>_<sess>_<fid>.jpg`` に置かれる。

このモジュールは:
    1. CSV を走査して (frame_id, phase_label) ペアを集める
    2. ``data/raw/ego/{train,val,test}/<vidid>/`` を一度だけスキャンし
       frame_id -> 実ファイル絶対パスのマップを作る
    3. 各サンプルが属する split（train/val/test）はファイルパスから判定

これにより独立した phase 学習・評価データセットを提供する（mmdet パイプライン
や ``ego_dataset.py`` から疎結合）。

使い方:
    train_ds = PhaseImageDataset(
        phase_dir="data/annotations/egosurgery_phase",
        image_root="data/raw/ego",
        split="train",
        image_size=224,
    )
"""

from __future__ import annotations

import csv
from collections.abc import Iterable
from pathlib import Path

import torch
import torchvision.transforms.v2 as T
from PIL import Image
from torch.utils.data import Dataset

from egosurgery.datasets.constants import NUM_PHASE_CLASSES, PHASE_NAME_TO_ID


def _build_frame_index(image_root: Path) -> dict[str, tuple[str, Path]]:
    """``image_root`` 配下を走査し ``frame_id -> (split, file path)`` を返す。

    画像パスは ``{image_root}/{split}/{vidid}/{frame_id}.jpg`` を仮定する。
    """
    index: dict[str, tuple[str, Path]] = {}
    for split in ("train", "val", "test"):
        split_dir = image_root / split
        if not split_dir.is_dir():
            continue
        for vid_dir in split_dir.iterdir():
            if not vid_dir.is_dir():
                continue
            for img in vid_dir.iterdir():
                if img.suffix.lower() not in (".jpg", ".jpeg", ".png"):
                    continue
                frame_id = img.stem  # 例 "01_1_0001"
                index[frame_id] = (split, img)
    return index


def _load_phase_csv(csv_path: Path) -> list[tuple[str, str]]:
    """1 つの phase CSV を ``[(frame_id, phase_label_str), ...]`` で返す。"""
    rows: list[tuple[str, str]] = []
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            frame = row.get("Frame") or row.get("frame")
            phase = row.get("Phase") or row.get("phase")
            if not frame or not phase:
                continue
            rows.append((frame.strip(), phase.strip().lower()))
    return rows


def _default_transform(image_size: int, train: bool) -> T.Compose:
    """学習時は軽い augmentation、評価時は中央クロップで揃える。"""
    mean = (0.485, 0.456, 0.406)
    std = (0.229, 0.224, 0.225)
    if train:
        return T.Compose([
            T.Resize(int(image_size * 1.15), antialias=True),
            T.RandomResizedCrop(image_size, scale=(0.7, 1.0), antialias=True),
            T.RandomHorizontalFlip(),
            T.ToImage(),
            T.ToDtype(torch.float32, scale=True),
            T.Normalize(mean=mean, std=std),
        ])
    return T.Compose([
        T.Resize(int(image_size * 1.15), antialias=True),
        T.CenterCrop(image_size),
        T.ToImage(),
        T.ToDtype(torch.float32, scale=True),
        T.Normalize(mean=mean, std=std),
    ])


class PhaseImageDataset(Dataset):
    """1 split 分の (画像テンソル, phase ラベル, video_id) を返すデータセット。

    Args:
        phase_dir: phase CSV のディレクトリ（既定 ``data/annotations/egosurgery_phase``）。
        image_root: 画像ルート（既定 ``data/raw/ego``）。
        split: ``"train"`` / ``"val"`` / ``"test"`` のいずれか。
        image_size: 学習時のリサイズ後の正方サイズ（既定 224）。
        transform: 上書きしたい場合の torchvision v2 Compose（既定は ``_default_transform``）。
        phase_name_to_id: phase ラベル名 -> id の辞書（既定 ``PHASE_NAME_TO_ID``）。
    """

    def __init__(
        self,
        phase_dir: str | Path = "data/annotations/egosurgery_phase",
        image_root: str | Path = "data/raw/ego",
        split: str = "train",
        image_size: int = 224,
        transform: T.Compose | None = None,
        phase_name_to_id: dict | None = None,
    ) -> None:
        super().__init__()
        self.split = str(split)
        self.image_root = Path(image_root)
        self.phase_dir = Path(phase_dir)
        self.image_size = int(image_size)
        self.name_to_id = dict(phase_name_to_id or PHASE_NAME_TO_ID)
        self.transform = transform or _default_transform(self.image_size, train=(split == "train"))

        # 一度だけ画像インデックスを作る（高速化のため）。
        index = _build_frame_index(self.image_root)

        # phase CSV を走査して該当 split のみを残す。
        samples: list[tuple[Path, int, str]] = []  # (path, phase_id, video_id)
        skipped_no_image = 0
        skipped_unknown_phase = 0
        for csv_path in sorted(self.phase_dir.glob("*.csv")):
            for frame_id, phase_name in _load_phase_csv(csv_path):
                meta = index.get(frame_id)
                if meta is None:
                    skipped_no_image += 1
                    continue
                if meta[0] != self.split:
                    continue
                pid = self.name_to_id.get(phase_name)
                if pid is None:
                    skipped_unknown_phase += 1
                    continue
                # video_id = "<vidid>_<sess>"（CSV ファイル名の stem に対応）
                video_id = csv_path.stem
                samples.append((meta[1], int(pid), video_id))
        self.samples = samples
        # 統計情報（trainer が class weight を計算するために使える）。
        counts = [0] * NUM_PHASE_CLASSES
        for _, pid, _ in samples:
            counts[pid] += 1
        self.class_counts = counts

        if not samples:
            raise RuntimeError(
                f"PhaseImageDataset({split}) が空: "
                f"画像インデックス {len(index)} 件、CSV 走査結果 0 件。"
                f"画像ルート {self.image_root} / phase CSV ディレクトリ {self.phase_dir} を確認。"
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> dict:
        path, pid, video_id = self.samples[idx]
        img = Image.open(path).convert("RGB")
        tensor = self.transform(img)
        return {
            "image": tensor,
            "phase": torch.tensor(pid, dtype=torch.long),
            "video_id": video_id,
            "frame_id": path.stem,
        }

    def class_frequencies(self) -> list[float]:
        """学習データに基づく phase クラス頻度（合計 1）。"""
        total = sum(self.class_counts) or 1
        return [c / total for c in self.class_counts]


def collate_phase_batch(batch: Iterable[dict]) -> dict:
    """DataLoader の collate_fn: テンソルを stack、メタは list に集約する。"""
    batch = list(batch)
    return {
        "image": torch.stack([b["image"] for b in batch], dim=0),
        "phase": torch.stack([b["phase"] for b in batch], dim=0),
        "video_id": [b["video_id"] for b in batch],
        "frame_id": [b["frame_id"] for b in batch],
    }
