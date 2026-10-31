"""案 B の地図の幾何の対応の確認（非公式 T-2026-10-31-grasp-pilot-probe、Task D-3）。

train の画像から seed 42 で 200 枚を選び、学習時の変換（presets.detr、SanitizeBoundingBox を含む）を通した画像と地図で、
器具の 3 チャネル（左手・右手・両手が扱う器具）の質量のうち、変換後の正解の枠の和集合に入る割合を測る。
    対応: 変換後の地図そのもの
    対照: 変換後の地図を左右に反転させたもの（同じ標本、同じ変換）
    変換前: 変換を掛けない画像と地図
加えて評価時の経路（変換なしの val の画像 50 枚を検出器の eval_transform と詰め物に通し、C5 の格子へ縮めた地図）で、
C5 の格子に写した枠の和集合に入る質量の割合を、対応と左右反転の対照で測る（pd_grasp_model.reduce_maps をそのまま使う）。

    EGO_ROOT=... EGO_ANN_DIR=... python scripts/grasppilot/geom_check.py --out <json>     （.venv-relation-detr）
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np
import torch

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
import train_t1b as t1b  # noqa: E402  (cwd を third_party/Relation-DETR へ移す)

from grasppilot import grasp_signals as G  # noqa: E402
from grasppilot.pd_grasp import make_dataset_class  # noqa: E402
from stage2pilot import common as C  # noqa: E402


def inside_ratio(gmap, boxes_xyxy):
    """gmap (5, H, W) の器具の 3 チャネルの質量のうち、枠の和集合に入る割合。質量が 0 なら None。"""
    tool = gmap[:3].float().sum(0)
    tot = float(tool.sum())
    if tot <= 0:
        return None
    h, w = tool.shape
    u = torch.zeros((h, w), dtype=torch.bool)
    for x0, y0, x1, y1 in boxes_xyxy.tolist():
        u[max(0, int(np.floor(y0))):min(h, int(np.ceil(y1))), max(0, int(np.floor(x0))):min(w, int(np.ceil(x1)))] = True
    return float(tool[u].sum()) / tot


def summarize(v):
    v = [x for x in v if x is not None]
    return {"n": len(v), "mean": float(np.mean(v)) if v else None, "median": float(np.median(v)) if v else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--n-eval", type=int, default=50)
    a = ap.parse_args()
    from transforms import presets
    cls = make_dataset_class()
    index = G.HTSIndex(("train", "val"))
    tr = cls(img_folder=t1b.EGO_ROOT, ann_file=f"{t1b.ANN_DIR}/instances_train.json", transforms=presets.detr,
             train=True, mode="gt", index=index)
    raw = cls(img_folder=t1b.EGO_ROOT, ann_file=f"{t1b.ANN_DIR}/instances_train.json", transforms=None,
              train=True, mode="gt", index=index)
    rng = random.Random(42)
    items = sorted(rng.sample(range(len(tr)), a.n))
    random.seed(42)
    torch.manual_seed(42)
    rows = []
    for it in items:
        img, tgt = tr[it]
        img0, tgt0 = raw[it]
        gm, b = tgt["grasp_map"], tgt["boxes"]
        assert gm.shape[-2:] == img.shape[-2:], (gm.shape, img.shape)
        rows.append({"item": it, "stem": tr.stem(tgt["image_id"]), "size": list(img.shape[-2:]),
                     "size_before": list(img0.shape[-2:]), "n_boxes": int(len(b)),
                     "matched": inside_ratio(gm, b), "flipped": inside_ratio(gm.flip(-1), b),
                     "before": inside_ratio(tgt0["grasp_map"], tgt0["boxes"]),
                     "before_flipped": inside_ratio(tgt0["grasp_map"].flip(-1), tgt0["boxes"]),
                     "channel_mass": tgt["grasp_map"].flatten(1).sum(1).tolist()})
    stems = [r["stem"] for r in rows]
    videos = C.assert_no_test(stems, "geom_check/train")
    # 評価時の経路: 検出器の eval_transform と詰め物、C5 への縮小（モデルの関数をそのまま使う）
    from util.lazy_load import Config
    model = Config(str(PROJ / "configs/stage2pilot/pd_graspmap_d5.py")).model.eval()
    va = cls(img_folder=t1b.EGO_ROOT, ann_file=f"{t1b.ANN_DIR}/instances_val.json", transforms=None,
             train=False, mode="gt", index=index)
    ev_items = sorted(random.Random(42).sample(range(len(va)), a.n_eval))
    ev = []
    for it in ev_items:
        img, tgt = va[it]
        images = model.preprocess_image([img])
        hp, wp = images.tensors.shape[-2:]
        assert hp % 32 == 0 and wp % 32 == 0
        model.set_grasp_maps([tgt["grasp_map"]])
        r = model.reduce_maps(images, (hp // 32, wp // 32))[0]
        model.set_grasp_maps([tgt["grasp_map"].flip(-1)])
        rf = model.reduce_maps(images, (hp // 32, wp // 32))[0]
        h, w = images.image_sizes[0]
        s = torch.tensor([w / img.shape[-1], h / img.shape[-2]] * 2) / 32.0
        b = tgt["boxes"] * s
        ev.append({"stem": va.stem(tgt["image_id"]), "resized": [int(h), int(w)], "padded": [int(hp), int(wp)],
                   "matched": inside_ratio(r, b), "flipped": inside_ratio(rf, b),
                   "mass_ratio_reduced_over_full": float(r[:3].sum() * 32 * 32 / max(1.0, float(
                       torch.nn.functional.interpolate(tgt["grasp_map"][None].float(), size=(int(h), int(w)),
                                                       mode="nearest")[0, :3].sum())))})
    ev_videos = C.assert_no_test([r["stem"] for r in ev], "geom_check/val")
    res = {"task_id": "T-2026-10-31-grasp-pilot-probe", "unofficial": True, "n": a.n, "seed": 42,
           "train_videos": videos, "val_videos": ev_videos,
           "train_transformed": {"matched": summarize([r["matched"] for r in rows]),
                                 "flipped_control": summarize([r["flipped"] for r in rows])},
           "train_before": {"matched": summarize([r["before"] for r in rows]),
                            "flipped_control": summarize([r["before_flipped"] for r in rows])},
           "n_sizes_changed": int(sum(r["size"] != r["size_before"] for r in rows)),
           "eval_path_c5": {"matched": summarize([r["matched"] for r in ev]),
                            "flipped_control": summarize([r["flipped"] for r in ev]),
                            "mass_ratio_reduced_over_full": summarize([r["mass_ratio_reduced_over_full"] for r in ev])},
           "rows": rows, "eval_rows": ev}
    C.write_json(a.out, res)
    print(json.dumps({k: res[k] for k in ("train_transformed", "train_before", "n_sizes_changed", "eval_path_c5")},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
