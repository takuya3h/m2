#!/usr/bin/env python
"""統合（検出 bbox + 工程 phase）manifest ビルダー（STEP B / B0-1）。

STEP B の結合手法は 1 フレームに **tool bbox GT と phase ラベルの両方**を必要とする。
本スクリプトは既存の phase manifest（``data/processed/phase_manifest/{split}.json``,
clip 時系列順・存在フレームのみ・10/2/3 Tool subset split）を土台に、
``data/annotations/egosurgery_tool/instances_{split}.json`` の tool bbox GT を
**後付け**して統合 manifest を作る。

phase manifest から派生させる理由（設計上の核心）:
    ゼロから join すると clip/frame 集合が phase 側とズレ、GAP キャッシュ（S4 入力）や
    Δ_phase 分母との整合が崩れる。phase manifest を土台にすれば frame 集合が phase と
    **構造的に同一**になり、比較の三角形（同一土台）が保証される。

join キー:
    frame_id（例 ``01_1_0124``）= phase CSV の ``Frame`` = tool COCO の file_name basename。
    tool COCO ``category_id`` は 0..14 で ``constants.TOOL_CLASSES`` と一致（remap 不要）。
    bbox は COCO xywh のまま保存（消費側で変換）。

出力（``data/processed/joint_manifest/``）:
    - ``{split}.json``: {"split","num_clips","num_frames","num_boxes","clips":[
        {"clip_id","video","frames":[
            {"frame","image_path","phase","phase_label",
             "boxes":[[x,y,w,h]...],"tool_labels":[cat_id...]}...]}...]}
    - ``tool_categories.json``: {cat_id: name}（constants.TOOL_CLASSES と一致を検証して書く）

実行（本体 .venv・Relation-DETR 非依存）:
    .venv/bin/python scripts/build_joint_manifest.py
前提: scripts/build_phase_manifest.py を先に実行し phase manifest を作っておくこと。
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from egosurgery.datasets.constants import TOOL_ID_TO_NAME

PROJ = Path(__file__).resolve().parents[1]
TOOL_ANN_DIR = PROJ / "data" / "annotations" / "egosurgery_tool"
PHASE_MANIFEST_DIR = PROJ / "data" / "processed" / "phase_manifest"
OUT_DIR = PROJ / "data" / "processed" / "joint_manifest"


def _frame_id(file_name: str) -> str:
    """tool COCO の file_name を frame_id に変換（train/01/01_1_0124.jpg -> 01_1_0124）。"""
    return os.path.splitext(os.path.basename(file_name))[0]


def _load_tool_boxes(split: str) -> dict[str, list[tuple[list[float], int]]]:
    """frame_id -> [(bbox_xywh, category_id), ...] を返す（検出 GT）。"""
    path = TOOL_ANN_DIR / f"instances_{split}.json"
    d = json.loads(path.read_text(encoding="utf-8"))
    # tool COCO の categories が constants と一致することを検証（label 空間の取り違え防止）。
    cats = {c["id"]: c["name"] for c in d["categories"]}
    if cats != dict(TOOL_ID_TO_NAME):
        raise SystemExit(
            f"[{split}] tool COCO categories が constants.TOOL_CLASSES と不一致:\n"
            f"  coco={cats}\n  constants={dict(TOOL_ID_TO_NAME)}"
        )
    img2frame = {im["id"]: _frame_id(im["file_name"]) for im in d["images"]}
    frame_boxes: dict[str, list[tuple[list[float], int]]] = defaultdict(list)
    for a in d["annotations"]:
        fr = img2frame[a["image_id"]]
        box = [float(v) for v in a["bbox"]]  # COCO xywh
        frame_boxes[fr].append((box, int(a["category_id"])))
    # 0 ボックスの画像（術具非依存フレーム）も検出の負例として残すため、画像由来の frame も登録。
    for fr in img2frame.values():
        frame_boxes.setdefault(fr, [])
    return frame_boxes


def build() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # tool_categories.json（constants と一致を検証済の vocab）を残す。
    (OUT_DIR / "tool_categories.json").write_text(
        json.dumps({str(k): v for k, v in sorted(TOOL_ID_TO_NAME.items())},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary: dict[str, dict] = {}
    for split in ("train", "val", "test"):
        phase_manifest = PHASE_MANIFEST_DIR / f"{split}.json"
        if not phase_manifest.exists():
            raise SystemExit(
                f"phase manifest が無い: {phase_manifest}\n"
                f"先に scripts/build_phase_manifest.py を実行してください。"
            )
        man = json.loads(phase_manifest.read_text(encoding="utf-8"))
        frame_boxes = _load_tool_boxes(split)

        n_frames = n_boxes = n_missing_in_tool = n_empty = 0
        clips_out = []
        for clip in man["clips"]:
            frames_out = []
            for fr in clip["frames"]:                       # phase manifest の時系列順を維持
                frame = fr["frame"]
                if frame not in frame_boxes:
                    # phase にあるが tool COCO に無い frame（想定外。集合は同一のはず）。
                    n_missing_in_tool += 1
                boxes_labels = frame_boxes.get(frame, [])
                boxes = [bl[0] for bl in boxes_labels]
                labels = [bl[1] for bl in boxes_labels]
                if not boxes:
                    n_empty += 1
                n_boxes += len(boxes)
                frames_out.append({
                    "frame": frame,
                    "image_path": fr["image_path"],
                    "phase": fr["phase"],
                    "phase_label": fr["label"],
                    "boxes": boxes,
                    "tool_labels": labels,
                })
            if frames_out:
                clips_out.append({"clip_id": clip["clip_id"], "video": clip["video"],
                                  "frames": frames_out})
                n_frames += len(frames_out)

        out = {"split": split, "num_clips": len(clips_out), "num_frames": n_frames,
               "num_boxes": n_boxes, "clips": clips_out}
        (OUT_DIR / f"{split}.json").write_text(json.dumps(out, ensure_ascii=False),
                                               encoding="utf-8")
        summary[split] = {"clips": len(clips_out), "frames": n_frames, "boxes": n_boxes,
                          "empty_frames": n_empty, "missing_in_tool": n_missing_in_tool}

    print(f"tool vocab: {len(TOOL_ID_TO_NAME)} classes (id 0..{len(TOOL_ID_TO_NAME) - 1})")
    for split, s in summary.items():
        print(f"[{split}] clips={s['clips']}  frames={s['frames']}  boxes={s['boxes']}  "
              f"empty(0-tool)={s['empty_frames']}  missing_in_tool={s['missing_in_tool']}")
    print(f"written -> {OUT_DIR}")


if __name__ == "__main__":
    build()
