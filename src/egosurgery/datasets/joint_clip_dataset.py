"""統合（検出 bbox + 工程 phase）clip データセット（STEP B / B0-1）。

``scripts/build_joint_manifest.py`` が作る ``data/processed/joint_manifest/{split}.json``
を読み、**1 item = 1 clip（時系列順フレーム列）**を返す。STEP B 確定事項（2026-06-18）の
「結合学習の batch 単位 = clip（内部で per-frame 検出を回す）」に対応する。

設計方針:
    - 画像は**パスのみ**返し、テンソル化・backbone forward は trainer 側（env 依存。
      結合モデルは .venv-relation-detr で Relation-DETR backbone をオンザフライ forward）に
      委ねる。これにより本データセットは Relation-DETR 非依存で本体 .venv で単体テストできる。
    - 検出 GT（boxes/tool_labels）と工程 GT（phase_labels）を 1 clip にまとめて返す。
    - ``gap_cache_path`` を渡すと凍結 GAP 特徴（①予測レベル系統 / sanity 用）も添付する。

使い方:
    ds = JointClipDataset("data/processed/joint_manifest/train.json")
    clip = ds[0]   # {"clip_id","frame_ids","image_paths","boxes","tool_labels","phase_labels"}
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

_PROJ = Path(__file__).resolve().parents[3]


class JointClipDataset(Dataset):
    """1 split 分の統合 manifest を clip 単位で返すデータセット。

    Args:
        manifest_path: ``joint_manifest/{split}.json`` のパス。
        proj_root: ``image_path`` の相対解決に使うルート（既定 = リポジトリルート）。
        box_format: ``"xyxy"``（既定）か ``"xywh"``。manifest は COCO xywh で保持し、
            ``"xyxy"`` 指定時に ``[x, y, x+w, y+h]`` へ変換して返す。
        gap_cache_path: 指定時、凍結 GAP npz（``frame_ids``/``features``）を読み、
            clip ごとに ``(T, 2048)`` 特徴を ``"gap"`` キーで添付する。全 frame_id が
            キャッシュに存在しなければ ``KeyError``。
    """

    def __init__(
        self,
        manifest_path: str | Path,
        proj_root: str | Path = _PROJ,
        box_format: str = "xyxy",
        gap_cache_path: str | Path | None = None,
    ) -> None:
        super().__init__()
        if box_format not in ("xyxy", "xywh"):
            raise ValueError(f"box_format は 'xyxy' か 'xywh': {box_format!r}")
        self.proj_root = Path(proj_root)
        self.box_format = box_format
        man = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        self.split = man.get("split")
        self.clips = man["clips"]

        self._gap_by_frame: dict[str, np.ndarray] | None = None
        if gap_cache_path is not None:
            d = np.load(gap_cache_path)
            feats_all = d["features"]                       # (N, 2048)。一度だけ取り出す
            frame_ids = [str(f) for f in d["frame_ids"]]
            self._gap_by_frame = {fid: feats_all[i] for i, fid in enumerate(frame_ids)}

    def __len__(self) -> int:
        return len(self.clips)

    def _boxes_tensor(self, boxes: list[list[float]]) -> torch.Tensor:
        if not boxes:
            return torch.zeros((0, 4), dtype=torch.float32)
        t = torch.tensor(boxes, dtype=torch.float32)        # (N, 4) xywh
        if self.box_format == "xyxy":
            t = t.clone()
            t[:, 2] = t[:, 0] + t[:, 2]
            t[:, 3] = t[:, 1] + t[:, 3]
        return t

    def __getitem__(self, idx: int) -> dict:
        clip = self.clips[idx]
        frames = clip["frames"]
        frame_ids = [f["frame"] for f in frames]
        item = {
            "clip_id": clip["clip_id"],
            "video": clip["video"],
            "frame_ids": frame_ids,
            "image_paths": [str(self.proj_root / f["image_path"]) for f in frames],
            "boxes": [self._boxes_tensor(f["boxes"]) for f in frames],
            "tool_labels": [torch.tensor(f["tool_labels"], dtype=torch.long) for f in frames],
            "phase_labels": torch.tensor([f["phase_label"] for f in frames], dtype=torch.long),
        }
        if self._gap_by_frame is not None:
            gap = np.stack([self._gap_by_frame[fid] for fid in frame_ids]).astype(np.float32)
            item["gap"] = torch.from_numpy(gap)             # (T, 2048)
        return item


def collate_joint_clips(batch: list[dict]) -> list[dict]:
    """clip-as-batch（既定 batch_size=1）。clip ごとに長さが異なるため list で返す。"""
    return list(batch)
