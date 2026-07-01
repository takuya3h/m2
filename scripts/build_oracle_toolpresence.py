#!/usr/bin/env python
"""§18.4 L2-3 用 oracle tool-presence の生成（GT bbox から one-hot 15-d）。

既存の B2a 入力（凍結検出器の予測 tool-presence 15-d）の **真値版** を作る:
  - 入力: data/annotations/egosurgery_tool/instances_{train,val,test}.json (COCO 形式)
  - 出力: data/processed/oracle_toolpresence/{train,val,test}_oracletool.npz
    - frame_ids: 検出 image の file_name の stem
    - signal: (N, 15) one-hot（その frame に存在する tool class は 1.0、それ以外 0.0）

L2-3 で T1a / B2a に oracle tool-presence を注入し、改善の **上限**を測る。
oracle でも改善が頭打ちなら、現状 T1a の +0.0497 は info 上限近くで効いている。
oracle で大幅改善するなら、検出器の予測精度がボトルネック（推定改善の余地）。

実行:
  .venv/bin/python scripts/build_oracle_toolpresence.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

PROJ = Path(__file__).resolve().parents[1]
ANN_DIR = PROJ / "data" / "annotations" / "egosurgery_tool"
OUT_DIR = PROJ / "data" / "processed" / "oracle_toolpresence"
NUM_TOOLS = 15


def build_for_split(split: str) -> None:
    ann_path = ANN_DIR / f"instances_{split}.json"
    if not ann_path.exists():
        print(f"  [SKIP] {ann_path} 不在")
        return
    coco = json.loads(ann_path.read_text())
    # image_id -> file_name stem (frame_id)
    imgid_to_frame: dict[int, str] = {}
    for img in coco["images"]:
        imgid_to_frame[img["id"]] = Path(img["file_name"]).stem

    # image_id -> set of category_id（その frame に存在する tool クラス）
    imgid_to_classes: dict[int, set[int]] = {iid: set() for iid in imgid_to_frame}
    for ann in coco["annotations"]:
        iid = ann["image_id"]
        if iid in imgid_to_classes:
            imgid_to_classes[iid].add(int(ann["category_id"]))

    # カテゴリ id を 0-indexed に正規化（既存 B2a 入力と整合）
    cat_ids = sorted(c["id"] for c in coco["categories"])
    catid_to_idx = {cid: i for i, cid in enumerate(cat_ids)}
    if len(cat_ids) != NUM_TOOLS:
        raise ValueError(f"category 数が {NUM_TOOLS} と異なる: {len(cat_ids)}")

    frame_ids: list[str] = []
    signals: list[np.ndarray] = []
    for iid, frame in imgid_to_frame.items():
        v = np.zeros(NUM_TOOLS, dtype=np.float32)
        for cid in imgid_to_classes[iid]:
            v[catid_to_idx[cid]] = 1.0
        frame_ids.append(frame)
        signals.append(v)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{split}_oracletool.npz"
    np.savez(out_path, frame_ids=np.array(frame_ids), signal=np.stack(signals))
    print(
        f"  {split}: {len(frame_ids):>5} frames, "
        f"signal shape={np.stack(signals).shape}, "
        f"tools/frame mean={np.stack(signals).sum(1).mean():.2f}, "
        f"saved → {out_path.relative_to(PROJ)}"
    )


def main() -> None:
    print(f"=== oracle tool-presence 生成 (GT bbox → one-hot 15-d) ===")
    for split in ("train", "val", "test"):
        build_for_split(split)
    print(f"=== 完了。L2-3 trainer 入力として使用可能 ===")


if __name__ == "__main__":
    main()
