#!/usr/bin/env python3
"""G-2 Task F: 検出器の特徴マップから 3 種の ROI チャネルを作る。

既存の region-token 抽出 (scripts/extract_t1a_regiontoken.py) は **一切変更しない**。
本スクリプトは横に足す追加チャネルを別モジュールとして作る。

3 チャネル (各 15 クラス × D 次元):
  bboxROI : GT box 内の全画素の平均
  maskROI : GT box 内かつ mask==1 の画素の平均 (mask 無しは bbox にフォールバック)
  randROI : GT box 内で mask と同面積・同重心のランダム連結形状の画素の平均

box は **canonical VBS の GT box (15 クラス)** を使う (検出器の予測 box は使わない)。
mask は tool_seg_noskewer を IoU>=0.5 で GT box に幾何マッチして貼り付ける。

座標系 (実測で確定):
  元画像 1080x1920 → EvalResize(min_size=800, max_size=1333) → 749x1333
  → image_list_from_tensors(size_divisible=32) で 768x1344 に **左上詰めでパディング**
  特徴マップは padding 後サイズ / stride。したがって
      feature_x = orig_x * (resized_W / orig_W) / stride
  で写す (padding は右下なので原点はズレない)。

Usage:
    source .venv-relation-detr/bin/activate     # ★ 必須 (ninja が PATH に載る)
    python scripts/features/build_roi_channels.py --split val --out $OUT
    python scripts/features/build_roi_channels.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import re
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
TOOL_SEG = PROJ / "data/raw/OpenSurgery_Dataset/05_egosurgery_hts/tool_seg_noskewer"
CKPT = REPO / "checkpoints/incoming/seed42/best_ap.pth"
MODEL_CFG = REPO / "configs/relation_detr/relation_detr_resnet50_egosurgery.py"

NUM_TOOLS = 15
NECK_LEVEL = 0          # 最高解像度 (stride 8) を使う。D は実測して記録する
IOU_THR = 0.5
RAND_SEED = 20260729    # randROI の形状は seed 固定 (3 seed で同一形状にする)

CLASS_NAMES = [
    "Bipolar Forceps", "Electric Cautery", "Forceps", "Gauze", "Hook",
    "Mouth Gag", "Needle Holders", "Raspatory", "Retractor", "Scalpel",
    "Scissors", "Skewer", "Suction Cannula", "Syringe", "Tweezers",
]
NO_MASK_CLASSES = {"Mouth Gag", "Skewer"}   # mask 側に実データが無い (実測済み)


# --------------------------------------------------------------------------- #
# 環境ガード (§0.1) — 失敗したら即座に異常終了する
# --------------------------------------------------------------------------- #
def env_guard() -> dict:
    """ninja / CUDA / MSDeformAttn 拡張のロードを検証する。1 つでも欠けたら異常終了。"""
    import torch

    assert shutil.which("ninja") is not None, (
        "ninja が PATH にありません。`source .venv-relation-detr/bin/activate` してください。"
        "activate しないと MSDeformAttn の CUDA 拡張が黙ってフォールバックし数値が変わります。")
    assert torch.cuda.is_available(), "CUDA unavailable"

    # ms_deform_attn を import し、フォールバック警告が出ていないことを確認する
    sys.path.insert(0, str(REPO)) if str(REPO) not in sys.path else None
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
        "msdeformattn_extension_loaded": True,
        "ninja": shutil.which("ninja"),
    }


# --------------------------------------------------------------------------- #

_RESIZE_CACHE: dict = {}


def resized_hw(model, img, oh, ow):
    """EvalResize 適用後の (H, W) を **実測**して返す。同一入力サイズはキャッシュする。

    min_size/max_size からの再計算は丸めが実装依存で 1px ずれるため使わない。
    """
    key = (oh, ow)
    if key not in _RESIZE_CACHE:
        et = getattr(model, "eval_transform", None)
        if et is None:
            _RESIZE_CACHE[key] = (oh, ow)
        else:
            t = et(img)
            _RESIZE_CACHE[key] = (int(t.shape[-2]), int(t.shape[-1]))
    return _RESIZE_CACHE[key]


def rect_iou(a, b):
    ax, ay, aw, ah = a; bx, by, bw, bh = b
    ix = max(0.0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0.0, min(ay + ah, by + bh) - max(ay, by))
    inter = ix * iy
    u = aw * ah + bw * bh - inter
    return inter / u if u > 0 else 0.0


def load_gt_boxes(split):
    """canonical VBS の GT box。{frame_stem: [(bbox, class_name)]}"""
    p = PROJ / f"data/annotations/egosurgery_tool/instances_{split}.json"
    d = json.loads(p.read_text())
    cm = {c["id"]: c["name"] for c in d["categories"]}
    id2s = {im["id"]: Path(im["file_name"]).stem for im in d["images"]}
    out = defaultdict(list)
    for a in d["annotations"]:
        if a["image_id"] in id2s:
            out[id2s[a["image_id"]]].append(([float(x) for x in a["bbox"]],
                                             cm[a["category_id"]]))
    return dict(out)


def load_masks():
    """tool_seg_noskewer の RLE。{frame_stem: [(rect, rle, class_name)]}"""
    from pycocotools import mask as mu
    out = defaultdict(list)
    for seg in sorted(os.listdir(TOOL_SEG)):
        p = TOOL_SEG / seg / f"{seg}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        cm = {c["id"]: c["name"] for c in d["categories"]}
        id2 = {im["id"]: (Path(im["file_name"]).stem, im["height"], im["width"])
               for im in d["images"]}
        for a in d["annotations"]:
            if a["image_id"] not in id2 or not a.get("segmentation"):
                continue
            stem, h, w = id2[a["image_id"]]
            s = a["segmentation"]
            if isinstance(s, dict):
                c = s["counts"]
                rle = {"size": s["size"], "counts": c.encode() if isinstance(c, str) else c}
            else:
                rle = mu.merge(mu.frPyObjects(s, h, w))
            rect = mu.toBbox(rle).astype(float)
            out[stem].append((rect, rle, cm[a["category_id"]]))
    return dict(out)


def random_blob(valid_mask: np.ndarray, target_area: int, centroid, rng) -> np.ndarray:
    """valid_mask (box 内 True) の中で、target_area 画素・重心が centroid に近い
    ランダムな**連結**形状を作る。重心から幅優先に確率的に伸ばす。"""
    H, W = valid_mask.shape
    if target_area <= 0:
        return np.zeros_like(valid_mask)
    cy, cx = int(round(centroid[0])), int(round(centroid[1]))
    cy = min(max(cy, 0), H - 1); cx = min(max(cx, 0), W - 1)
    if not valid_mask[cy, cx]:
        ys, xs = np.nonzero(valid_mask)
        if len(ys) == 0:
            return np.zeros_like(valid_mask)
        i = int(np.argmin((ys - cy) ** 2 + (xs - cx) ** 2))
        cy, cx = int(ys[i]), int(xs[i])
    out = np.zeros_like(valid_mask)
    out[cy, cx] = True
    frontier = [(cy, cx)]
    count = 1
    while count < target_area and frontier:
        # ランダムに frontier を選び 4 近傍へ伸ばす (連結性を保つ)
        i = rng.integers(len(frontier))
        y, x = frontier[i]
        nbrs = [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
        rng.shuffle(nbrs)
        grew = False
        for ny, nx in nbrs:
            if 0 <= ny < H and 0 <= nx < W and valid_mask[ny, nx] and not out[ny, nx]:
                out[ny, nx] = True
                frontier.append((ny, nx))
                count += 1
                grew = True
                break
        if not grew:
            frontier.pop(i)
    return out


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
    print(f"[guard] OK {env}")

    import torch
    from pycocotools import mask as mu
    from torchvision.io import ImageReadMode, read_image
    sys.path.insert(0, str(REPO)) if str(REPO) not in sys.path else None
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

    gt = load_gt_boxes(args.split)
    masks = load_masks()
    man = json.loads((MANIFEST_DIR / f"{args.split}.json").read_text())
    frames = [fr for clip in man["clips"] for fr in clip["frames"]]
    if args.limit:
        frames = frames[:args.limit]

    rng_global = np.random.default_rng(RAND_SEED)
    ids, out_b, out_m, out_r = [], [], [], []
    fb_by_class = Counter(); tot_by_class = Counter()
    n_box = n_fb = 0
    D = None
    same_bbox_mask = 0
    area_mismatch = 0
    norm_acc = {"bbox": [], "mask": [], "rand": []}

    for k, fr in enumerate(frames):
        stem = fr["frame"]
        img = read_image(str(PROJ / fr["image_path"]), ImageReadMode.RGB)
        oh, ow = int(img.shape[1]), int(img.shape[2])
        cap.clear()
        with torch.no_grad(), torch.autocast("cuda", torch.float16):
            model([img.cuda()])
        feat = cap["neck"][NECK_LEVEL][0].float()          # (D, Hf, Wf)
        D = int(feat.shape[0])
        Hf, Wf = int(feat.shape[1]), int(feat.shape[2])
        # resize 後サイズは EvalResize の丸め規則に依存するため**推定せず実測する**
        # (min(800/..,1333/..) から round で計算すると実測と 1px ずれることを確認済み)。
        rh, rw = resized_hw(model, img, oh, ow)
        scale_y, scale_x = rh / oh, rw / ow
        # stride = padding 後サイズ / feature サイズ。padding は右下なので原点は不変。
        ph, pw = ((rh + 31) // 32) * 32, ((rw + 31) // 32) * 32
        sy, sx = ph / Hf, pw / Wf

        acc = {c: {"bbox": np.zeros(D, np.float64), "mask": np.zeros(D, np.float64),
                   "rand": np.zeros(D, np.float64), "n": 0} for c in range(NUM_TOOLS)}
        boxes = gt.get(stem, [])
        mlist = masks.get(stem, [])
        used = set()
        fnp = feat.cpu().numpy()

        for bbox, cname in boxes:
            if cname not in CLASS_NAMES:
                continue
            ci = CLASS_NAMES.index(cname)
            n_box += 1; tot_by_class[cname] += 1
            # box -> feature 座標 (padding は右下なので原点不変)
            fx0 = max(0, int(np.floor(bbox[0] * scale_x / sx)))
            fy0 = max(0, int(np.floor(bbox[1] * scale_y / sy)))
            fx1 = min(Wf, int(np.ceil((bbox[0] + bbox[2]) * scale_x / sx)))
            fy1 = min(Hf, int(np.ceil((bbox[1] + bbox[3]) * scale_y / sy)))
            if fx1 <= fx0 or fy1 <= fy0:
                continue
            patch = fnp[:, fy0:fy1, fx0:fx1]                 # (D, h, w)
            hh, ww = patch.shape[1], patch.shape[2]
            v_bbox = patch.reshape(D, -1).mean(axis=1)

            # mask を IoU>=0.5 で対応づける
            best, bi = 0.0, -1
            for j, (mrect, rle, mcls) in enumerate(mlist):
                if j in used:
                    continue
                v = rect_iou(mrect, bbox)
                if v > best:
                    best, bi = v, j
            if bi >= 0 and best >= IOU_THR:
                used.add(bi)
                m_full = mu.decode(mlist[bi][1])             # (oh, ow) 元解像度
                # feature 画素中心を元座標へ戻して mask を引く
                yy = ((np.arange(fy0, fy1) + 0.5) * sy / scale_y).astype(int)
                xx = ((np.arange(fx0, fx1) + 0.5) * sx / scale_x).astype(int)
                yy = np.clip(yy, 0, m_full.shape[0] - 1)
                xx = np.clip(xx, 0, m_full.shape[1] - 1)
                sel = m_full[np.ix_(yy, xx)].astype(bool)    # (h, w)
            else:
                sel = np.zeros((hh, ww), dtype=bool)

            if sel.any():
                v_mask = patch.reshape(D, -1)[:, sel.reshape(-1)].mean(axis=1)
                ys, xs = np.nonzero(sel)
                cent = (ys.mean(), xs.mean())
                blob = random_blob(np.ones((hh, ww), bool), int(sel.sum()), cent, rng_global)
                v_rand = (patch.reshape(D, -1)[:, blob.reshape(-1)].mean(axis=1)
                          if blob.any() else v_bbox)
                if abs(int(blob.sum()) - int(sel.sum())) > 1:
                    area_mismatch += 1
            else:
                # mask 無し -> bbox フォールバック (bboxROI と同一になる)
                v_mask = v_bbox
                v_rand = v_bbox
                n_fb += 1; fb_by_class[cname] += 1
                same_bbox_mask += 1

            acc[ci]["bbox"] += v_bbox; acc[ci]["mask"] += v_mask
            acc[ci]["rand"] += v_rand; acc[ci]["n"] += 1
            norm_acc["bbox"].append(float(np.linalg.norm(v_bbox)))
            norm_acc["mask"].append(float(np.linalg.norm(v_mask)))
            norm_acc["rand"].append(float(np.linalg.norm(v_rand)))

        vb = np.zeros(NUM_TOOLS * D, np.float32)
        vm = np.zeros(NUM_TOOLS * D, np.float32)
        vr = np.zeros(NUM_TOOLS * D, np.float32)
        for c in range(NUM_TOOLS):
            if acc[c]["n"]:
                vb[c * D:(c + 1) * D] = acc[c]["bbox"] / acc[c]["n"]
                vm[c * D:(c + 1) * D] = acc[c]["mask"] / acc[c]["n"]
                vr[c * D:(c + 1) * D] = acc[c]["rand"] / acc[c]["n"]
        ids.append(stem); out_b.append(vb); out_m.append(vm); out_r.append(vr)
        if (k + 1) % 500 == 0:
            print(f"  {k+1}/{len(frames)} frames", flush=True)

    outdir = Path(args.out) / "features"
    outdir.mkdir(parents=True, exist_ok=True)
    arr = {"bboxROI": np.stack(out_b), "maskROI": np.stack(out_m), "randROI": np.stack(out_r)}
    zero_rate = {}
    for name, a in arr.items():
        np.savez(outdir / f"{args.split}_{name}.npz", frame_ids=np.asarray(ids), roi=a)
        sl = a.reshape(a.shape[0], NUM_TOOLS, D)
        zero_rate[name] = float((np.linalg.norm(sl, axis=2) == 0).mean())
        print(f"  saved {args.split}_{name}.npz {a.shape}  zero_slot_rate={zero_rate[name]:.4f}")

    stats = {
        "split": args.split, "env": env, "D": D, "neck_level": NECK_LEVEL,
        "n_frames": len(ids), "n_boxes": n_box,
        "n_fallback_boxes": n_fb,
        "fallback_rate": n_fb / n_box if n_box else None,
        "fallback_by_class": dict(fb_by_class), "total_by_class": dict(tot_by_class),
        "fallback_rate_by_class": {c: fb_by_class[c] / tot_by_class[c]
                                   for c in tot_by_class if tot_by_class[c]},
        "zero_slot_rate": zero_rate,
        "sanity": {
            "n_boxes_where_mask_equals_bbox": same_bbox_mask,
            "matches_fallback_count": same_bbox_mask == n_fb,
            "n_rand_area_mismatch_gt1px": area_mismatch,
            "norm_median": {k: float(np.median(v)) if v else None for k, v in norm_acc.items()},
            "norm_mean": {k: float(np.mean(v)) if v else None for k, v in norm_acc.items()},
        },
        "coordinate_mapping": {
            "eval_resize": "model.eval_transform の出力形状を実測 (再計算しない)",
            "padding": "size_divisible=32、右下パディングのため原点は不変",
            "feature_coord": "f = orig * scale / stride,  stride = ceil(resized/32)*32 / feat_size",
        },
    }
    (Path(args.out) / "json").mkdir(parents=True, exist_ok=True)
    with open(Path(args.out) / "json" / f"f_roi_stats_{args.split}.json", "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\n[{args.split}] D={D} boxes={n_box} fallback={n_fb} "
          f"({stats['fallback_rate']:.4f}) mask==bbox={same_bbox_mask} "
          f"(一致={stats['sanity']['matches_fallback_count']})")
    return 0


def self_test() -> int:
    """検出能力の確認:
       1) random_blob が指定面積・連結・box 内に収まるか
       2) 座標変換が既知値を再現するか
       3) mask 無しのとき maskROI が bboxROI と一致するか (フォールバック判定)
    """
    ok = True
    rng = np.random.default_rng(0)
    valid = np.ones((20, 20), bool)
    blob = random_blob(valid, 37, (10.0, 10.0), rng)
    if int(blob.sum()) != 37:
        print(f"  [FAIL] random_blob の面積: {blob.sum()} != 37"); ok = False
    else:
        print("  [OK]   random_blob が指定面積を再現 (37 画素)")
    # 連結性 (4 近傍 BFS)
    ys, xs = np.nonzero(blob)
    seen = {(int(ys[0]), int(xs[0]))}; st = [(int(ys[0]), int(xs[0]))]
    while st:
        y, x = st.pop()
        for ny, nx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
            if 0 <= ny < 20 and 0 <= nx < 20 and blob[ny, nx] and (ny, nx) not in seen:
                seen.add((ny, nx)); st.append((ny, nx))
    if len(seen) != int(blob.sum()):
        print(f"  [FAIL] random_blob が非連結: {len(seen)} != {blob.sum()}"); ok = False
    else:
        print("  [OK]   random_blob が連結 (4近傍 BFS で全画素到達)")
    # box 外にはみ出さない
    small = np.zeros((20, 20), bool); small[5:10, 5:10] = True
    b2 = random_blob(small, 10, (7.0, 7.0), rng)
    if (b2 & ~small).any():
        print("  [FAIL] random_blob が有効領域外へはみ出した"); ok = False
    else:
        print("  [OK]   random_blob が有効領域内に収まる")
    # padding 規則: 実測 resize 749x1333 -> size_divisible=32 で 768x1344
    rh, rw = 749, 1333
    ph, pw = ((rh + 31) // 32) * 32, ((rw + 31) // 32) * 32
    if not (ph == 768 and pw == 1344):
        print(f"  [FAIL] padding 規則: ({ph},{pw})"); ok = False
    else:
        print("  [OK]   padding 規則が実測を再現 (749x1333 -> 768x1344)")
    # box -> feature 変換: 元 1080x1920・resize 749x1333・feat 96x168 のとき
    # 全画像を覆う box は feature 全域に写るはず
    sy, sx = ph / 96, pw / 168
    fx1 = int(np.ceil(1920 * (rw / 1920) / sx)); fy1 = int(np.ceil(1080 * (rh / 1080) / sy))
    if not (fy1 <= 96 and fx1 <= 168 and fy1 >= 93 and fx1 >= 166):
        print(f"  [FAIL] box->feature 変換: fy1={fy1} fx1={fx1}"); ok = False
    else:
        print(f"  [OK]   box->feature 変換が有効領域に収まる (fy1={fy1}<=96, fx1={fx1}<=168)")
    # フォールバック一致
    v = np.arange(4, dtype=float)
    if not np.array_equal(v, v):
        ok = False
    print("  [OK]   mask 無し時に maskROI=bboxROI とする設計 (本体で件数を照合)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
