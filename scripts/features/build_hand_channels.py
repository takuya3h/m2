#!/usr/bin/env python3
"""S4: 手チャネル（presence / handROI bbox 2cls・4cls / handROI mask 2cls）を 1 パスで作る。

G-2 の `build_roi_channels.py` と**同一手続き**に揃える:
  - 特徴マップ: 検出器 neck level0（stride 8）、D = 256（実測して記録）
  - box 内の全画素平均 = bboxROI
  - mask は GT box に IoU >= 0.5 で幾何マッチし、box 内かつ mask==1 の画素平均 = maskROI
  - **mask 無しは bbox にフォールバック**（= その box では maskROI = bboxROI）
  - 未検出クラスはゼロベクトルで埋め、ゼロ率を記録
  - 座標変換は `model.eval_transform` の出力形状を**実測**して使う（再計算しない）

手のクラス体系（S4-1 の実測に基づく。事前登録 prereg/s4_hand_prediction.md）:
  bbox 4cls : Own hands left / Own hands right / Other hands left / Other hands right
  bbox 2cls : 上記のうち Own hands left / right（mask と揃えるため）
  mask 2cls : First Person's Left Hand / First Person's Right Hand
              （handtool_seg_5cls の cat 1,2。**"Other hands" の mask は存在しない**）

★ 必ず `source .venv-relation-detr/bin/activate` してから実行する。
  activate しないと MSDeformAttn の CUDA 拡張が黙ってフォールバックし数値が変わる。

Usage:
    source .venv-relation-detr/bin/activate
    python scripts/features/build_hand_channels.py --split val --out $OUT
    python scripts/features/build_hand_channels.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import warnings
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

PROJ = Path(__file__).resolve().parents[2]
REPO = PROJ / "third_party" / "Relation-DETR"
MANIFEST_DIR = PROJ / "data/processed/phase_manifest"
HTS = PROJ / "data/annotations/egosurgery_hts"
CKPT = REPO / "checkpoints/incoming/seed42/best_ap.pth"
MODEL_CFG = REPO / "configs/relation_detr/relation_detr_resnet50_egosurgery.py"

NECK_LEVEL = 0
IOU_THR = 0.5

# 手 bbox 4 クラス（data/annotations/egosurgery_hts/hand_bbox の category id 順）
HAND_BBOX_4 = ["Own hands left", "Own hands right", "Other hands left", "Other hands right"]
# mask と揃える 2 クラス（First Person = Own）
HAND_BBOX_2 = ["Own hands left", "Own hands right"]
# 手 mask 2 クラス（handtool_seg_5cls の cat 1,2）
MASK_HAND_ID2NAME = {1: "Own hands left", 2: "Own hands right"}


def env_guard() -> dict:
    """ninja / CUDA / MSDeformAttn 拡張のロードを検証する。1 つでも欠けたら異常終了。"""
    import torch

    assert shutil.which("ninja") is not None, (
        "ninja が PATH にありません。`source .venv-relation-detr/bin/activate` してください。"
        "activate しないと MSDeformAttn の CUDA 拡張が黙ってフォールバックし数値が変わります。")
    assert torch.cuda.is_available(), "CUDA unavailable"
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        import models.bricks.ms_deform_attn as msda  # noqa: F401
        bad = [str(x.message) for x in w
               if "Failed to load MultiScaleDeformableAttention" in str(x.message)]
    assert not bad, f"MSDeformAttn CUDA 拡張のロードに失敗: {bad}"
    assert getattr(msda, "_C", None) is not None, "msda._C が None (拡張が使われていない)"
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJ,
                            capture_output=True, text=True).stdout.strip()
    return {
        "torch": torch.__version__, "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0), "cudnn": torch.backends.cudnn.version(),
        "commit": commit, "host": os.uname().nodename,
        "msdeformattn_extension_loaded": True, "ninja": shutil.which("ninja"),
    }


_RESIZE_CACHE: dict = {}


def resized_hw(model, img, oh, ow):
    """EvalResize 適用後の (H, W) を **実測**して返す（再計算しない）。"""
    key = (oh, ow)
    if key not in _RESIZE_CACHE:
        et = getattr(model, "eval_transform", None)
        _RESIZE_CACHE[key] = (oh, ow) if et is None else tuple(
            int(x) for x in et(img).shape[-2:])
    return _RESIZE_CACHE[key]


def rect_iou(a, b) -> float:
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    u = aw * ah + bw * bh - inter
    return inter / u if u > 0 else 0.0


def load_hand_boxes(split: str):
    """手 GT box。{frame_stem: [(bbox, class_name)]}"""
    p = HTS / f"hand_bbox/by_split/{split}.json"
    d = json.loads(p.read_text())
    cm = {c["id"]: c["name"] for c in d["categories"]}
    id2s = {im["id"]: Path(im["file_name"]).stem for im in d["images"]}
    out = defaultdict(list)
    for a in d["annotations"]:
        if a["image_id"] in id2s:
            out[id2s[a["image_id"]]].append(([float(x) for x in a["bbox"]],
                                             cm[a["category_id"]]))
    return dict(out)


def load_hand_masks(split: str):
    """手 mask の RLE。{frame_stem: [(rect, rle, class_name)]}  cat 1,2 のみ。"""
    from pycocotools import mask as mu
    p = HTS / f"handtool_seg_5cls/by_split/{split}_toolhand_withmask.json"
    d = json.loads(p.read_text())
    id2 = {im["id"]: (Path(im["file_name"]).stem, im["height"], im["width"])
           for im in d["images"]}
    out = defaultdict(list)
    for a in d["annotations"]:
        if a["category_id"] not in MASK_HAND_ID2NAME:
            continue
        if a["image_id"] not in id2 or not a.get("segmentation"):
            continue
        stem, h, w = id2[a["image_id"]]
        s = a["segmentation"]
        if isinstance(s, dict):
            c = s["counts"]
            rle = {"size": s["size"], "counts": c.encode() if isinstance(c, str) else c}
        else:
            rle = mu.merge(mu.frPyObjects(s, h, w))
        out[stem].append((mu.toBbox(rle).astype(float), rle,
                          MASK_HAND_ID2NAME[a["category_id"]]))
    return dict(out)


def self_test() -> int:
    ok = True
    # padding 規則（G-2 の self-test と同一の既知値）
    rh, rw = 749, 1333
    ph, pw = ((rh + 31) // 32) * 32, ((rw + 31) // 32) * 32
    if (ph, pw) != (768, 1344):
        print(f"  [FAIL] padding 規則: ({ph},{pw})"); ok = False
    else:
        print("  [OK]   padding 規則が実測を再現 (749x1333 -> 768x1344)")
    # クラス体系（S4-1 の実測と一致すること）
    hb = json.loads((HTS / "hand_bbox/by_split/val.json").read_text())
    names = [c["name"] for c in sorted(hb["categories"], key=lambda x: x["id"])]
    if names != HAND_BBOX_4:
        print(f"  [FAIL] 手 bbox のクラスが想定と違う: {names}"); ok = False
    else:
        print(f"  [OK]   手 bbox 4 クラス = {names}")
    hm = json.loads((HTS / "handtool_seg_5cls/by_split/val_toolhand_withmask.json").read_text())
    hand_cats = {c["id"]: c["name"] for c in hm["categories"] if c["id"] in MASK_HAND_ID2NAME}
    if len(hand_cats) != 2:
        print(f"  [FAIL] 手 mask の手クラスが 2 個でない: {hand_cats}"); ok = False
    else:
        print(f"  [OK]   手 mask 2 クラス = {list(hand_cats.values())} "
              f"（'Other hands' の mask は存在しない）")
    if HAND_BBOX_2 != [MASK_HAND_ID2NAME[1], MASK_HAND_ID2NAME[2]]:
        print("  [FAIL] 2cls の対応づけが不整合"); ok = False
    else:
        print(f"  [OK]   2cls の対応づけ: bbox {HAND_BBOX_2} <-> mask cat 1,2")
    # rect_iou の既知値
    if abs(rect_iou([0, 0, 10, 10], [0, 0, 10, 10]) - 1.0) > 1e-12 or \
       abs(rect_iou([0, 0, 10, 10], [10, 0, 10, 10])) > 1e-12:
        print("  [FAIL] rect_iou"); ok = False
    else:
        print("  [OK]   rect_iou の既知値 (同一=1.0 / 隣接=0.0)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["train", "val", "test"])
    ap.add_argument("--out", help="出力ルート ($OUT)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not (args.split and args.out):
        ap.error("--split と --out が必要 (または --self-test)")

    env = env_guard()
    print(f"[guard] OK {env}", flush=True)

    import torch
    from pycocotools import mask as mu
    from torchvision.io import ImageReadMode, read_image
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from util.lazy_load import Config
    from util.utils import load_checkpoint, load_state_dict

    model = Config(str(MODEL_CFG)).model.eval()
    ck = load_checkpoint(str(CKPT))
    if isinstance(ck, dict) and "model" in ck:
        ck = ck["model"]
    load_state_dict(model, ck)
    model.cuda()
    for p in model.parameters():
        p.requires_grad_(False)

    cap = {}
    model.neck.register_forward_hook(lambda m, i, o: cap.update(neck=o))

    boxes_all = load_hand_boxes(args.split)
    masks_all = load_hand_masks(args.split)
    man = json.loads((MANIFEST_DIR / f"{args.split}.json").read_text())
    frames = [fr for clip in man["clips"] for fr in clip["frames"]]
    if args.limit:
        frames = frames[:args.limit]

    ids = []
    out_p, out_b2, out_b4, out_m2 = [], [], [], []
    D = None
    n_box = n_fb = 0
    fb_by_class = Counter(); tot_by_class = Counter()
    same_bbox_mask = 0
    n_frames_with_mask = 0

    for k, fr in enumerate(frames):
        stem = fr["frame"]
        img = read_image(str(PROJ / fr["image_path"]), ImageReadMode.RGB)
        oh, ow = int(img.shape[1]), int(img.shape[2])
        cap.clear()
        with torch.no_grad(), torch.autocast("cuda", torch.float16):
            model([img.cuda()])
        feat = cap["neck"][NECK_LEVEL][0].float()
        D = int(feat.shape[0])
        Hf, Wf = int(feat.shape[1]), int(feat.shape[2])
        rh, rw = resized_hw(model, img, oh, ow)
        scale_y, scale_x = rh / oh, rw / ow
        ph, pw = ((rh + 31) // 32) * 32, ((rw + 31) // 32) * 32
        sy, sx = ph / Hf, pw / Wf
        fnp = feat.cpu().numpy()

        acc4 = {c: {"bbox": np.zeros(D, np.float64), "n": 0} for c in HAND_BBOX_4}
        acc2 = {c: {"bbox": np.zeros(D, np.float64), "mask": np.zeros(D, np.float64), "n": 0}
                for c in HAND_BBOX_2}
        presence = np.zeros(len(HAND_BBOX_4), np.float32)

        mlist = masks_all.get(stem, [])
        if mlist:
            n_frames_with_mask += 1
        used = set()

        for bbox, cname in boxes_all.get(stem, []):
            if cname not in HAND_BBOX_4:
                continue
            presence[HAND_BBOX_4.index(cname)] = 1.0
            fx0 = max(0, int(np.floor(bbox[0] * scale_x / sx)))
            fy0 = max(0, int(np.floor(bbox[1] * scale_y / sy)))
            fx1 = min(Wf, int(np.ceil((bbox[0] + bbox[2]) * scale_x / sx)))
            fy1 = min(Hf, int(np.ceil((bbox[1] + bbox[3]) * scale_y / sy)))
            if fx1 <= fx0 or fy1 <= fy0:
                continue
            patch = fnp[:, fy0:fy1, fx0:fx1]
            hh, ww = patch.shape[1], patch.shape[2]
            v_bbox = patch.reshape(D, -1).mean(axis=1)
            acc4[cname]["bbox"] += v_bbox; acc4[cname]["n"] += 1

            if cname not in HAND_BBOX_2:
                continue                      # Other hands は 2cls / mask 側に無い
            n_box += 1; tot_by_class[cname] += 1

            best, bi = 0.0, -1
            for j, (mrect, _rle, _mc) in enumerate(mlist):
                if j in used:
                    continue
                v = rect_iou(mrect, bbox)
                if v > best:
                    best, bi = v, j
            sel = np.zeros((hh, ww), dtype=bool)
            if bi >= 0 and best >= IOU_THR:
                used.add(bi)
                m_full = mu.decode(mlist[bi][1])
                yy = ((np.arange(fy0, fy1) + 0.5) * sy / scale_y).astype(int)
                xx = ((np.arange(fx0, fx1) + 0.5) * sx / scale_x).astype(int)
                yy = np.clip(yy, 0, m_full.shape[0] - 1)
                xx = np.clip(xx, 0, m_full.shape[1] - 1)
                sel = m_full[np.ix_(yy, xx)].astype(bool)

            if sel.any():
                v_mask = patch.reshape(D, -1)[:, sel.reshape(-1)].mean(axis=1)
            else:
                v_mask = v_bbox               # mask 無し -> bbox フォールバック
                n_fb += 1; fb_by_class[cname] += 1; same_bbox_mask += 1
            acc2[cname]["bbox"] += v_bbox; acc2[cname]["mask"] += v_mask
            acc2[cname]["n"] += 1

        vb4 = np.zeros(len(HAND_BBOX_4) * D, np.float32)
        for i, c in enumerate(HAND_BBOX_4):
            if acc4[c]["n"]:
                vb4[i * D:(i + 1) * D] = acc4[c]["bbox"] / acc4[c]["n"]
        vb2 = np.zeros(len(HAND_BBOX_2) * D, np.float32)
        vm2 = np.zeros(len(HAND_BBOX_2) * D, np.float32)
        for i, c in enumerate(HAND_BBOX_2):
            if acc2[c]["n"]:
                vb2[i * D:(i + 1) * D] = acc2[c]["bbox"] / acc2[c]["n"]
                vm2[i * D:(i + 1) * D] = acc2[c]["mask"] / acc2[c]["n"]

        ids.append(stem); out_p.append(presence)
        out_b2.append(vb2); out_b4.append(vb4); out_m2.append(vm2)
        if (k + 1) % 500 == 0:
            print(f"  {k+1}/{len(frames)} frames", flush=True)

    outdir = Path(args.out) / "features"
    outdir.mkdir(parents=True, exist_ok=True)
    arr = {
        "handPresence": np.stack(out_p),
        "handROIbbox2": np.stack(out_b2),
        "handROIbbox4": np.stack(out_b4),
        "handROImask2": np.stack(out_m2),
    }
    ncls = {"handPresence": len(HAND_BBOX_4), "handROIbbox2": len(HAND_BBOX_2),
            "handROIbbox4": len(HAND_BBOX_4), "handROImask2": len(HAND_BBOX_2)}
    zero_rate = {}
    for name, a in arr.items():
        np.savez(outdir / f"{args.split}_{name}.npz",
                 frame_ids=np.asarray(ids), roi=a)
        if name == "handPresence":
            zero_rate[name] = float((a == 0).all(axis=1).mean())
        else:
            sl = a.reshape(a.shape[0], ncls[name], D)
            zero_rate[name] = float((np.linalg.norm(sl, axis=2) == 0).mean())
        print(f"  saved {args.split}_{name}.npz {a.shape}  zero_rate={zero_rate[name]:.4f}")

    stats = {
        "split": args.split, "env": env, "D": D, "neck_level": NECK_LEVEL,
        "n_frames": len(ids),
        "hand_bbox_classes_4": HAND_BBOX_4, "hand_bbox_classes_2": HAND_BBOX_2,
        "mask_hand_classes_2": list(MASK_HAND_ID2NAME.values()),
        "n_frames_with_any_hand_mask": n_frames_with_mask,
        "frame_cov_hand_mask": n_frames_with_mask / len(ids) if ids else None,
        "n_boxes_2cls": n_box, "n_fallback_boxes_2cls": n_fb,
        "fallback_rate_2cls": n_fb / n_box if n_box else None,
        "fallback_by_class": dict(fb_by_class), "total_by_class": dict(tot_by_class),
        "zero_rate": zero_rate,
        "sanity": {"n_boxes_where_mask_equals_bbox": same_bbox_mask,
                   "matches_fallback_count": same_bbox_mask == n_fb},
        "denominators": {
            "fallback_rate_2cls": "分母 = 2cls（Own hands left/right）の手 GT box 総数",
            "frame_cov_hand_mask": "分母 = この split の manifest フレーム数",
        },
        "coordinate_mapping": {
            "eval_resize": "model.eval_transform の出力形状を実測 (再計算しない)",
            "padding": "size_divisible=32、右下パディングのため原点は不変",
        },
    }
    (Path(args.out) / "json").mkdir(parents=True, exist_ok=True)
    with open(Path(args.out) / "json" / f"s4_hand_stats_{args.split}.json", "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\n[{args.split}] D={D} frames={len(ids)} "
          f"mask有フレーム={n_frames_with_mask} ({stats['frame_cov_hand_mask']:.4f}) "
          f"2cls boxes={n_box} fallback={n_fb} ({stats['fallback_rate_2cls']:.4f}) "
          f"一致={stats['sanity']['matches_fallback_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
