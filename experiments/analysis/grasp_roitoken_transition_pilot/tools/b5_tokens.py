"""Task B-4 の続き（T-2026-11-09-grasp-roitoken-transition-pilot）。案 3 のトークンの ROI の中身を作る。本体の .venv。学習しない。

各フレームの工程塔の空間特徴（b3_pmaps の layer4 2048×25×45 と layer3 1024×50×89、fp16）から、b4_boxes の枠で
ROI-Align（torchvision.ops.roi_align、7×7、aligned=True、sampling_ratio=2）して 7×7 の平均を取る。枠の座標は地図（270×480）
→ P の入力（x × 1422/480、y × 800/270）→ 特徴（spatial_scale 1/32・1/16）。無い枠は 0（界面で学ぶ空トークンに置き換える）。

    源  pred    G の予測の枠 5 個（train は pred_CF、val は確定）
        gt      正解の把持（HTS）の枠 5 個
        union   器具の和集合の枠 1 個（G の予測から）
        shuffle 目録の mapping で持ってきた別のフレームの G の予測の枠 5 個で、このフレームの特徴を切り出す

対照: 画像全体の枠の ROI の平均と地図の空間平均の相対 L2（近い）、別のフレームの地図の空間平均との相対 L2（遠い）。

    .venv/bin/python b5_tokens.py --part val --layer layer4 --feat-dir <S>/feat --box-dir <S>/b4 --out-dir <S>/tok
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torchvision.ops import roi_align

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
from stage2pilot import common as C  # noqa: E402

SCALE = {"layer4": 1 / 32, "layer3": 1 / 16}
SX, SY = 1422 / 480, 800 / 270
CHUNK = 64


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["train", "val"], required=True)
    ap.add_argument("--layer", choices=["layer4", "layer3"], required=True)
    ap.add_argument("--feat-dir", required=True)
    ap.add_argument("--box-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    feat = np.load(Path(a.feat_dir) / f"p_{a.layer}_{a.part}.npy", mmap_mode="r")
    fids = np.load(Path(a.feat_dir) / f"frame_ids_{a.part}.npy")
    bids = np.load(Path(a.box_dir) / f"frame_ids_{a.part}.npy")
    assert (fids == bids).all()
    C.assert_no_test([str(f) for f in fids], "b5_tokens")
    n, ch = feat.shape[0], feat.shape[1]
    pred = np.load(Path(a.box_dir) / f"boxes_pred_{a.part}.npz")
    gt = np.load(Path(a.box_dir) / f"boxes_gt_{a.part}.npz")
    sidx = np.load(Path(a.box_dir) / f"shuffle_idx_{a.part}.npy")
    srcs = {"pred": (pred["box"], pred["present"]), "gt": (gt["box"], gt["present"]),
            "union": (pred["ubox"], pred["upresent"]), "shuffle": (pred["box"][sidx], pred["present"][sidx])}
    res = {k: np.zeros((n, b.shape[1], ch), np.float16) for k, (b, _) in srcs.items()}
    full_rel, other_rel = [], []
    t0 = time.monotonic()
    for s in range(0, n, CHUNK):
        x = torch.from_numpy(np.asarray(feat[s:s + CHUNK])).cuda().float()
        b = x.shape[0]
        for key, (box, pres) in srcs.items():
            bx = torch.from_numpy(box[s:s + b]).cuda().clone()
            bx[..., [0, 2]] *= SX
            bx[..., [1, 3]] *= SY
            k = bx.shape[1]
            idx = torch.arange(b, device="cuda").repeat_interleave(k)[:, None].float()
            rois = torch.cat([idx, bx.reshape(-1, 4)], 1)
            r = roi_align(x, rois, output_size=7, spatial_scale=SCALE[a.layer], sampling_ratio=2, aligned=True)
            v = r.mean((2, 3)).reshape(b, k, ch)
            v = v * torch.from_numpy(pres[s:s + b]).cuda()[..., None]
            res[key][s:s + b] = v.half().cpu().numpy()
        if s % 1024 == 0:
            whole = torch.tensor([[float(i), 0, 0, 1422, 800] for i in range(b)], device="cuda")
            r = roi_align(x, whole, output_size=7, spatial_scale=SCALE[a.layer], sampling_ratio=2, aligned=True).mean((2, 3))
            m = x.mean((2, 3))
            full_rel += (torch.linalg.norm(r - m, dim=1) / torch.linalg.norm(m, dim=1)).tolist()
            other_rel += (torch.linalg.norm(r[1:] - m[:-1], dim=1) / torch.linalg.norm(m[:-1], dim=1)).tolist()
    files = {}
    for key, v in res.items():
        p = out / f"tok_{key}_{a.layer}_{a.part}.npy"
        np.save(p, v)
        files[key] = {"path": str(p), "shape": list(v.shape), "sha256": C.sha256(p),
                      "nonzero_tokens": int((np.abs(v).sum(-1) > 0).sum()),
                      "present_tokens": int(srcs[key][1].sum())}
    rec = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "part": a.part, "layer": a.layer, "frames": n,
           "channels": ch, "roi_align": {"output_size": 7, "spatial_scale": SCALE[a.layer], "sampling_ratio": 2,
                                         "aligned": True, "pool": "7×7 の平均"},
           "box_to_input": {"x": SX, "y": SY}, "files": files, "seconds": time.monotonic() - t0,
           "control_whole_box_vs_mapmean_rel_l2": {"n": len(full_rel), "max": max(full_rel), "median": float(np.median(full_rel))},
           "control_whole_box_vs_other_frame_rel_l2": {"n": len(other_rel), "min": min(other_rel),
                                                      "median": float(np.median(other_rel))}}
    C.write_json(out / f"b5_record_{a.layer}_{a.part}.json", rec)
    print(json.dumps(rec, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
