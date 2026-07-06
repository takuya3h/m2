#!/usr/bin/env python
"""STEP D-aux 系統① 用 oracle hand-feature の生成（GT bbox → 手由来の低次元特徴）。

既存 `build_oracle_toolpresence.py`（tool 15-d one-hot）の **手版**。EgoSurgery-Tool の
19 クラス統合 COCO（tool 0-14 + hand 15-18）から **hand 4 クラス**（own/other × L/R）の
GT bbox を取り出し、B2a 系トレーナ（`train_haux.py`）へ注入する oracle 手特徴を作る。

  入力: data/annotations/egosurgery_tool_hand/instances_{train,val,test}.json（COCO 形式・19 cats）
        手 = category_id 15(Own L) / 16(Own R) / 17(Other L) / 18(Other R)
  出力: data/processed/oracle_handfeature/{split}_oraclehand_{type}.npz
        - frame_ids: image の file_name stem（GAP キャッシュと同じキー規約）
        - signal:    特徴タイプ別のベクトル

特徴タイプ（§2.2 の H-1〜H-3/H-5 に対応。0-index の手クラス順は own_L, own_R, other_L, other_R）:
  - presence (4-d): その frame に各手クラスが存在すれば 1.0（H-1 hand-presence の oracle）
  - count    (4-d): 各手クラスの検出個数（float・H-2 hand-count の oracle。two-hand 協調の粗指標）
  - geom     (16-d): 各手クラスにつき [cx, cy, w, h]（画像サイズで正規化・H-3 hand-geometry）。
                     同クラス複数 box は **最大面積**を採用、不在は 0 埋め。own/other・L/R は
                     スロット位置で表現（H-5 own/other 分離注入は train_haux 側で block 分割）。

注意:
  - **数値捏造をしない**（研究インテグリティ）: GT からの決定論的計算のみ。乱数なし。
  - 出力の frame_ids は GAP 特徴 npz と突合できる stem 形式（train_haux が KeyError で Fail Loud）。
  - 画像に width/height が無い場合は Fail Loud（正規化不能をダミーで埋めない）。

実行（本 sandbox でも GT だけで動く。.venv 不要・numpy のみ）:
  python scripts/build_oracle_handfeature.py
  python scripts/build_oracle_handfeature.py --types presence,geom
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

PROJ = Path(__file__).resolve().parents[1]
ANN_DIR = PROJ / "data" / "annotations" / "egosurgery_tool_hand"
OUT_DIR = PROJ / "data" / "processed" / "oracle_handfeature"

# 19 クラス統合 COCO における手 category_id → 0-index の手クラス順
HAND_CATIDS = [15, 16, 17, 18]
HAND_NAMES = ["Own hands left", "Own hands right", "Other hands left", "Other hands right"]
NUM_HANDS = len(HAND_CATIDS)  # 4
CATID_TO_HAND = {cid: i for i, cid in enumerate(HAND_CATIDS)}

FEATURE_TYPES = ("presence", "count", "geom")
GEOM_PER_HAND = 4  # [cx, cy, w, h]


def _load_coco(split: str) -> dict | None:
    ann_path = ANN_DIR / f"instances_{split}.json"
    if not ann_path.exists():
        print(f"  [SKIP] {ann_path.relative_to(PROJ)} 不在")
        return None
    return json.loads(ann_path.read_text())


def _index_by_image(coco: dict) -> tuple[list[int], dict[int, str], dict[int, tuple[float, float]]]:
    """image を登場順に固定し、id→frame_id(stem) と id→(W,H) を返す。"""
    image_ids: list[int] = []
    imgid_to_frame: dict[int, str] = {}
    imgid_to_wh: dict[int, tuple[float, float]] = {}
    for img in coco["images"]:
        iid = img["id"]
        image_ids.append(iid)
        imgid_to_frame[iid] = Path(img["file_name"]).stem
        w, h = img.get("width"), img.get("height")
        if not w or not h:
            raise ValueError(f"image id={iid} に width/height が無い（正規化不能・ダミー禁止）")
        imgid_to_wh[iid] = (float(w), float(h))
    return image_ids, imgid_to_frame, imgid_to_wh


def _hand_boxes_by_image(coco: dict) -> dict[int, list[tuple[int, list[float]]]]:
    """image_id → [(hand_idx, [x,y,w,h]), ...]（手 category のみ）。"""
    out: dict[int, list[tuple[int, list[float]]]] = {}
    for ann in coco["annotations"]:
        cid = int(ann["category_id"])
        if cid not in CATID_TO_HAND:
            continue
        out.setdefault(ann["image_id"], []).append((CATID_TO_HAND[cid], ann["bbox"]))
    return out


def _build_signals(
    feature_type: str,
    image_ids: list[int],
    imgid_to_wh: dict[int, tuple[float, float]],
    hand_boxes: dict[int, list[tuple[int, list[float]]]],
) -> np.ndarray:
    if feature_type == "presence":
        dim = NUM_HANDS
    elif feature_type == "count":
        dim = NUM_HANDS
    elif feature_type == "geom":
        dim = NUM_HANDS * GEOM_PER_HAND
    else:
        raise ValueError(f"未知の feature_type: {feature_type}")

    rows = np.zeros((len(image_ids), dim), dtype=np.float32)
    for i, iid in enumerate(image_ids):
        boxes = hand_boxes.get(iid, [])
        if feature_type == "presence":
            for hidx, _ in boxes:
                rows[i, hidx] = 1.0
        elif feature_type == "count":
            for hidx, _ in boxes:
                rows[i, hidx] += 1.0
        elif feature_type == "geom":
            W, H = imgid_to_wh[iid]
            # 手クラスごとに最大面積 box を採用（複数手の重なりに決定論的に対応）
            best: dict[int, tuple[float, list[float]]] = {}
            for hidx, bbox in boxes:
                x, y, w, h = bbox
                area = max(w, 0.0) * max(h, 0.0)
                if hidx not in best or area > best[hidx][0]:
                    best[hidx] = (area, bbox)
            for hidx, (_, bbox) in best.items():
                x, y, w, h = bbox
                cx = (x + w / 2.0) / W
                cy = (y + h / 2.0) / H
                base = hidx * GEOM_PER_HAND
                rows[i, base + 0] = cx
                rows[i, base + 1] = cy
                rows[i, base + 2] = w / W
                rows[i, base + 3] = h / H
    return rows


def build_for_split(split: str, types: list[str]) -> None:
    coco = _load_coco(split)
    if coco is None:
        return
    # 手 category が期待通り存在するか検証（Fail Loud）
    present_catids = {int(c["id"]) for c in coco["categories"]}
    missing = [cid for cid in HAND_CATIDS if cid not in present_catids]
    if missing:
        raise ValueError(f"[{split}] 手 category_id {missing} が annotation に不在。手 GT を確認せよ。")

    image_ids, imgid_to_frame, imgid_to_wh = _index_by_image(coco)
    hand_boxes = _hand_boxes_by_image(coco)
    frame_ids = np.array([imgid_to_frame[iid] for iid in image_ids])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n_with_hand = sum(1 for iid in image_ids if hand_boxes.get(iid))
    print(f"  [{split}] {len(image_ids):>5} frames（手ありframe {n_with_hand}）")
    for ftype in types:
        signal = _build_signals(ftype, image_ids, imgid_to_wh, hand_boxes)
        out_path = OUT_DIR / f"{split}_oraclehand_{ftype}.npz"
        np.savez(out_path, frame_ids=frame_ids, signal=signal)
        # 検証用サマリ（捏造でない実測値）
        if ftype == "presence":
            rate = signal.mean(0)  # クラス別出現率
            stat = "presence rate " + "/".join(f"{HAND_NAMES[k].split()[0][:2]}{HAND_NAMES[k].split()[-1][0]}={rate[k]:.2f}"
                                                for k in range(NUM_HANDS))
        elif ftype == "count":
            stat = f"hands/frame mean={signal.sum(1).mean():.2f} max={int(signal.sum(1).max())}"
        else:
            nz = (np.abs(signal).reshape(len(image_ids), NUM_HANDS, GEOM_PER_HAND).sum(-1) > 0).mean(0)
            stat = "geom fill rate " + "/".join(f"{nz[k]:.2f}" for k in range(NUM_HANDS))
        print(f"      → {out_path.name:40s} shape={signal.shape}  {stat}")


def main() -> None:
    ap = argparse.ArgumentParser(description="oracle hand-feature 生成（GT bbox → presence/count/geom）。")
    ap.add_argument("--types", type=str, default="presence,count,geom",
                    help=f"生成する特徴タイプ（カンマ区切り）。既定=全て。選択肢: {','.join(FEATURE_TYPES)}")
    args = ap.parse_args()
    types = [t.strip() for t in args.types.split(",") if t.strip()]
    bad = [t for t in types if t not in FEATURE_TYPES]
    if bad:
        raise SystemExit(f"未知の feature_type: {bad}（選択肢: {FEATURE_TYPES}）")

    print("=== oracle hand-feature 生成 (GT bbox → 手特徴) ===")
    print(f"    手クラス 0-index: {list(enumerate(HAND_NAMES))}")
    print(f"    生成タイプ: {types}")
    for split in ("train", "val", "test"):
        build_for_split(split, types)
    print("=== 完了。train_haux.py の --hand-source oracle 入力として使用可能 ===")


if __name__ == "__main__":
    main()
