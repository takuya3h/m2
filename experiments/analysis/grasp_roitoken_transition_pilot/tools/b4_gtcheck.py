"""Task B-4・G2 の確かめ（T-2026-11-09-grasp-roitoken-transition-pilot）。本体の .venv。学習しない。

b4_boxes.py の記録は、正解の地図の統計（鍵 gt）を後の枠の統計で上書きした（実行者の誤り）。地図はそのままに、ここで測り直す:
  - 注釈のあるフレームの数、注釈の無いフレーム = loss_mask の一覧か、地図の sha256
  - 正解の地図が注釈と一致する: 注釈のあるフレームから seed 42 で 200 フレームを選び、注釈を独立に復号して同じ規則
    （クラスごとの和集合 → 4×4 の平均 → round(割合 × 255)）で作り直した地図と、保存した地図が完全に一致するか
  - 対照: 作り直した地図を一つ隣のフレームの保存した地図と比べると一致しない

    .venv/bin/python b4_gtcheck.py --box-dir <S>/b4 --out <S>/b4/b4_gtcheck.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402

HTS = ROOT / "data/annotations/egosurgery_hts/hand_tool_seg"
CAT_TO_CH = {3: 0, 4: 1, 5: 2, 1: 3, 2: 4}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from pycocotools import mask as mask_utils
    out = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "parts": {}}
    for part in ("train", "val"):
        frames = [str(f) for f in np.load(Path(a.box_dir) / f"frame_ids_{part}.npy")]
        C.assert_no_test(frames, "b4_gtcheck")
        has = np.load(Path(a.box_dir) / f"has_gt_{part}.npy")
        path = Path(a.box_dir) / f"gt_{part}_m.npy"
        maps = np.load(path, mmap_mode="r")
        ann = json.loads((HTS / f"{part}.json").read_text())
        by_stem = {Path(im["file_name"]).stem: im for im in ann["images"]}
        anns = {}
        for x in ann["annotations"]:
            anns.setdefault(x["image_id"], []).append(x)
        loss_mask = set((HTS / "loss_mask" / f"{part}.txt").read_text().split())
        no_gt = sorted(f for f, h in zip(frames, has) if not h)
        rng = np.random.default_rng(42)
        cand = np.where(has)[0]
        pick = np.sort(rng.choice(cand, size=min(200, len(cand)), replace=False))
        same = other = 0
        zero_rows_ok = bool(all(not np.asarray(maps[i]).any() for i in np.where(~has)[0]))
        for i in pick:
            im = by_stem[frames[i]]
            full = np.zeros((5, 1080, 1920), bool)
            for x in anns.get(im["id"], []):
                full[CAT_TO_CH[x["category_id"]]] |= mask_utils.decode(x["segmentation"]).astype(bool)
            m = np.round(full.reshape(5, 270, 4, 480, 4).mean(axis=(2, 4)) * 255).clip(0, 255).astype(np.uint8)
            same += int(np.array_equal(m, maps[i]))
            j = i + 1 if i + 1 < len(frames) else i - 1
            other += int(np.array_equal(m, maps[j]))
        out["parts"][part] = {"frames": len(frames), "with_gt": int(has.sum()), "without_gt": int((~has).sum()),
                              "without_gt_equals_loss_mask_in_frames": no_gt == sorted(f for f in frames if f in loss_mask),
                              "loss_mask_in_frames": int(sum(f in loss_mask for f in frames)),
                              "without_gt_maps_all_zero": zero_rows_ok,
                              "maps": str(path), "maps_shape": list(maps.shape), "maps_sha256": C.sha256(path),
                              "redecode_sample": int(len(pick)), "redecode_equal": same,
                              "control_neighbor_equal": other}
        print(part, json.dumps(out["parts"][part], ensure_ascii=False), flush=True)
    C.write_json(a.out, out)


if __name__ == "__main__":
    main()
