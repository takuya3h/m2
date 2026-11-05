"""反転の経路の取り出しの対照（非公式 T-2026-11-05-grasp-tower-rebuild、Task B-3）。GPU は使わない。

同じフレームを反転なし・反転ありで取り出し、インスタンスごとに
    反転ありのマスク == 反転なしのマスクの左右反転、 反転ありのラベル == 入れ替え表[反転なしのラベル]
が成り立つかを数える。入れ替え表は 1↔2、3↔4、5 はそのまま。
    G5Flip（swap=True）     本契約の経路。成り立つはず
    G5Flip（swap=False）    入れ替えない写し。左右のラベルがあるフレームで外れるはず
    G38（二本目の経路そのもの） torch.rand を 0 に差し替えて反転を強制。外れるはず

    .venv/bin/python scripts/grasppilot/g5_flip_test.py --ann-dir <S/g/ann> --out <json> [--frames 24]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from unittest import mock

import numpy as np
import torch

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
sys.path.insert(0, str(PROJ / "src"))
from grasppilot import g5_train as G5  # noqa: E402
from grasppilot import g_train as T  # noqa: E402
from stage2pilot import common as C  # noqa: E402


def take(ds, i, flip):
    if isinstance(ds, G5.G5Flip):
        ds.force_flip = flip
        return ds[i]
    with mock.patch.object(torch, "rand", lambda *s, **k: torch.full(s, 0.0 if flip else 0.99)):
        return ds[i]


def compare(ds, i):
    a0, m0, (k0, l0) = take(ds, i, False)
    a1, m1, (k1, l1) = take(ds, i, True)
    img_ok = bool(np.array_equal(a1, a0[:, ::-1]))
    mask_ok = len(k0) == len(k1) and all(np.array_equal(x1, x0[:, ::-1]) for x0, x1 in zip(k0, k1))
    swap_ok = bool(np.array_equal(l1, G5.SWAP0[l0])) if len(l0) else True
    same = bool(np.array_equal(l1, l0))
    return {"stem": m0["stem"], "labels_noflip": (l0 + 1).tolist(), "labels_flip": (l1 + 1).tolist(),
            "image_flipped": img_ok, "masks_flipped": bool(mask_ok), "labels_swapped": swap_ok, "labels_unchanged": same}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ann-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=24)
    a = ap.parse_args()
    tr = json.loads((Path(a.ann_dir) / "g5_train.json").read_text())
    # 左右のラベル（1〜4）を持つフレームから選ぶ（入れ替えが見えるフレーム）
    cats = {}
    for x in tr["annotations"]:
        cats.setdefault(x["image_id"], set()).add(x["category_id"])
    pos = [j for j, im in enumerate(tr["images"]) if cats.get(im["id"], set()) & {1, 2, 3, 4}]
    picks = sorted(np.random.default_rng(42).choice(pos, a.frames, replace=False).tolist())
    paths = {"G5Flip_swap": G5.G5Flip(tr, True, swap=True), "G5Flip_noswap_copy": G5.G5Flip(tr, True, swap=False),
             "G38_second_path": T.G38(tr, True)}
    res = {"task_id": G5.TASK, "frames": len(picks), "paths": {}}
    for name, ds in paths.items():
        rows = [compare(ds, j) for j in picks]
        res["paths"][name] = {
            "image_flipped": sum(r["image_flipped"] for r in rows), "masks_flipped": sum(r["masks_flipped"] for r in rows),
            "labels_swapped": sum(r["labels_swapped"] for r in rows), "labels_unchanged": sum(r["labels_unchanged"] for r in rows),
            "examples": rows[:3]}
        print(name, {k: v for k, v in res["paths"][name].items() if k != "examples"}, flush=True)
    C.write_json(a.out, res)


if __name__ == "__main__":
    main()
