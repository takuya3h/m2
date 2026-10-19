#!/usr/bin/env python
"""extra-queries の見落としの集合と K1 の数え上げ（非公式 T-2026-10-19-stage2-pilot-four-new-types、SPEC §3.2・§3.6、Task C-4）。

見落とし（利用者の決定: 字面どおり）: 各画像で、凍結した D* の評価の後処理の出力（上位 300、確信度の下限なし、NMS なし）のうち、
同じクラスで IoU 0.5 以上の検出が一つも無い正解の box。確信度がどれほど低い検出でも「覆う」に数える。
正解の box は ConvertCocoPolysToMask と同じ規則で学習に残るもの（iscrowd 0、幅と高さが正）。

    predict  D* の train の出力を作る（.venv-relation-detr。--shard i/n で画像を分ける）
    missed   出力と注釈から見落としを数え、集合（注釈の id）を書く（本体の .venv でも動く。numpy と json だけ）
    contrib  学習後の extra-queries の最終の上位 300 に入った追加の出力の数と、照合した見落としの数（Task F）
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np

STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-19-stage2-pilot-four-new-types")
TEST_VIDEOS = {"04", "05", "07"}


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cmd_predict(a):
    import sys

    import torch
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import train_t1b as t1b  # import 時に cwd を third_party/Relation-DETR へ移す
    from datasets.coco import CocoDetection
    from torch.utils import data
    from util.collate_fn import collate_fn
    device = torch.device("cuda")
    torch.manual_seed(0)
    ds = CocoDetection(img_folder=t1b.EGO_ROOT, ann_file=f"{t1b.ANN_DIR}/instances_{a.split}.json", transforms=None,
                       train=False)
    i, n = (int(x) for x in a.shard.split("/"))
    ds.ids = [x for k, x in enumerate(ds.ids) if k % n == i]
    videos = sorted({Path(ds.coco.imgs[x]["file_name"]).stem.split("_")[0] for x in ds.ids})
    assert not set(videos) & TEST_VIDEOS, videos
    loader = data.DataLoader(ds, 1, shuffle=False, num_workers=4, collate_fn=collate_fn, pin_memory=True)  # nosemgrep
    cfg = str(t1b.RELDETR / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")
    model = t1b.build_model(device, 42, cfg, ckpt_override=a.det_ckpt)
    t1b.register_classes(model, loader)
    model.set_phase_context = lambda ctx: None
    m_ap, _, preds = t1b.eval_detection(model, loader, {}, device, True, collect_predictions=True)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(a.out, "wt") as f:
        json.dump(preds["results"], f)
    meta = {"split": a.split, "shard": a.shard, "n_images": len(ds.ids), "videos": videos, "det_ckpt": a.det_ckpt,
            "det_ckpt_sha256": sha256(a.det_ckpt), "mAP_on_shard": m_ap, "n_results": len(preds["results"]),
            "out": a.out, "out_sha256": sha256(a.out)}
    Path(a.out + ".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(meta, ensure_ascii=False))


def kept_gt(coco):
    """学習に残る正解の box（ConvertCocoPolysToMask と同じ規則）を画像ごとに [(注釈 id, クラス, xywh)]。"""
    out = {}
    for img_id, img in coco["images"].items():
        out[img_id] = []
    for ann in coco["annotations"]:
        if ann.get("iscrowd", 0) != 0:
            continue
        img = coco["images"][ann["image_id"]]
        x0, y0, bw, bh = ann["bbox"]
        x1, y1 = min(max(x0 + bw, 0), img["width"]), min(max(y0 + bh, 0), img["height"])
        x0, y0 = min(max(x0, 0), img["width"]), min(max(y0, 0), img["height"])
        if y1 > y0 and x1 > x0:
            out[ann["image_id"]].append((ann["id"], ann["category_id"], (x0, y0, x1 - x0, y1 - y0)))
    return out


def iou_xywh(a, b):
    """a (N, 4)、b (M, 4) の xywh の IoU（N, M）。COCO の bbox の IoU と同じ定義。"""
    ax0, ay0, ax1, ay1 = a[:, 0], a[:, 1], a[:, 0] + a[:, 2], a[:, 1] + a[:, 3]
    bx0, by0, bx1, by1 = b[:, 0], b[:, 1], b[:, 0] + b[:, 2], b[:, 1] + b[:, 3]
    iw = np.clip(np.minimum(ax1[:, None], bx1[None]) - np.maximum(ax0[:, None], bx0[None]), 0, None)
    ih = np.clip(np.minimum(ay1[:, None], by1[None]) - np.maximum(ay0[:, None], by0[None]), 0, None)
    inter = iw * ih
    union = (a[:, 2] * a[:, 3])[:, None] + (b[:, 2] * b[:, 3])[None] - inter
    return np.where(union > 0, inter / union, 0.0)


def cover_scores(gt_by_img, results):
    """正解の box ごとに、同じクラスで IoU 0.5 以上の検出のスコアの最大（覆う検出が無ければ −1）。"""
    det = {}
    for r in results:
        det.setdefault(r["image_id"], []).append(r)
    rows = []
    for img_id, gts in gt_by_img.items():
        ds = det.get(img_id, [])
        for ann_id, cat, box in gts:
            same = [d for d in ds if d["category_id"] == cat]
            best = -1.0
            if same:
                iou = iou_xywh(np.array([box], float), np.array([d["bbox"] for d in same], float))[0]
                hit = [d["score"] for d, v in zip(same, iou) if v >= 0.5]
                best = max(hit) if hit else -1.0
            rows.append((img_id, ann_id, cat, best))
    return rows


def summarize(rows, cats, thresholds):
    n = len(rows)
    missed = [r for r in rows if r[3] < 0]
    per_class = {cats[c]: {"gt": sum(1 for r in rows if r[2] == c), "missed": sum(1 for r in missed if r[2] == c)}
                 for c in sorted(cats)}
    covered = np.array([r[3] for r in rows if r[3] >= 0])
    q = [0.0, 0.001, 0.01, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0]
    return {"n_gt": n, "n_missed": len(missed), "missed_fraction": len(missed) / n if n else None,
            "per_class": per_class,
            "missed_ann_ids": sorted(int(r[1]) for r in missed),
            "images_with_missed": len({r[0] for r in missed}),
            "cover_score_quantiles": {str(k): float(np.quantile(covered, k)) for k in q} if len(covered) else None,
            "missed_at_threshold": {str(t): int(sum(1 for r in rows if r[3] < t)) for t in thresholds},
            "missed_at_threshold_per_class": {str(t): {cats[c]: int(sum(1 for r in rows if r[3] < t and r[2] == c))
                                                       for c in sorted(cats)} for t in thresholds}}


def load_coco(path):
    d = json.loads(Path(path).read_text())
    return {"images": {i["id"]: i for i in d["images"]}, "annotations": d["annotations"],
            "cats": {c["id"]: c["name"] for c in d["categories"]}}


def load_results(paths):
    out = []
    for p in paths:
        with gzip.open(p, "rt") as f:
            out.extend(json.load(f))
    return out


def cmd_missed(a):
    coco = load_coco(a.ann)
    videos = sorted({Path(i["file_name"]).stem.split("_")[0] for i in coco["images"].values()})
    assert not set(videos) & TEST_VIDEOS, videos
    results = load_results(a.preds)
    img_ids = set(coco["images"])
    assert {r["image_id"] for r in results} <= img_ids
    per_img = {}
    for r in results:
        per_img[r["image_id"]] = per_img.get(r["image_id"], 0) + 1
    gt = kept_gt(coco)
    thresholds = [float(t) for t in a.thresholds.split(",")]
    s = summarize(cover_scores(gt, results), coco["cats"], thresholds)
    s.update({"definition": "同じクラスで IoU 0.5 以上の検出が上位 300（確信度の下限なし）に一つも無い正解の box",
              "ann": a.ann, "ann_sha256": sha256(a.ann), "videos": videos, "n_images": len(img_ids),
              "preds": [{"path": p, "sha256": sha256(p)} for p in a.preds], "n_results": len(results),
              "results_per_image": {"min": min(per_img.values()), "max": max(per_img.values())},
              "images_without_results": len(img_ids - set(per_img)), "thresholds": thresholds})
    if a.controls:
        s["controls"] = controls(gt, results, coco)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in s.items() if k not in ("missed_ann_ids", "missed_at_threshold_per_class")},
                     ensure_ascii=False)[:3000])


def controls(gt, results, coco):
    """完了判定 f の空振りでないことの確認（両方向）。"""
    rows = cover_scores(gt, results)
    det = {}
    for r in results:
        det.setdefault(r["image_id"], []).append(r)
    # (1) ある正解をただ一つの検出だけが覆っている画像を探し、その検出を消した写しで、その正解が見落としに数えられる
    target = None
    for img_id, ann_id, cat, best in rows:
        if best < 0:
            continue
        box = next(b for a_, c_, b in gt[img_id] if a_ == ann_id)
        cov = [d for d in det[img_id] if d["category_id"] == cat and
               iou_xywh(np.array([box], float), np.array([d["bbox"]], float))[0, 0] >= 0.5]
        if len(cov) == 1:
            target = (img_id, ann_id, cov[0])
            break
    removed = [r for r in results if r is not target[2]]
    rows_r = {(r[0], r[1]): r[3] for r in cover_scores({target[0]: gt[target[0]]}, removed)}
    # (2) 正解をそのまま検出（スコア 1）として足した写しで、見落としが 0 件になる
    added = results + [{"image_id": i, "category_id": c, "bbox": list(b), "score": 1.0}
                       for i, gts in gt.items() for _, c, b in gts]
    n_missed_added = sum(1 for r in cover_scores(gt, added) if r[3] < 0)
    return {"remove_sole_cover": {"image_id": int(target[0]), "ann_id": int(target[1]),
                                  "cover_before": next(r[3] for r in rows if r[1] == target[1]),
                                  "cover_after": rows_r[(target[0], target[1])],
                                  "counted_missed_after": rows_r[(target[0], target[1])] < 0},
            "add_gt_as_detections": {"n_missed": n_missed_added}}


def cmd_contrib(a):
    """学習後の extra-queries の寄与（SPEC §3.2 の記録）: 最終の上位 300 に入った追加の出力の数と、そのうち val の見落としの box に
    同じクラスで IoU 0.5 以上で当たったもの（照合した見落としの数）。pd_four_eval.py --save-preds の予測と from_extra の並びを読む。"""
    coco = load_coco(a.ann)
    miss = set(json.loads(Path(a.missed).read_text())["missed_ann_ids"])
    gt = kept_gt(coco)
    results = load_results([a.preds])
    with gzip.open(a.from_extra, "rt") as f:
        flags = json.load(f)
    by_img = {}
    for r in results:
        by_img.setdefault(r["image_id"], []).append(r)
    n_extra, n_extra_hit_missed, n_extra_hit_gt, matched_missed = 0, 0, 0, set()
    for img_id, rs in by_img.items():
        fe = flags[str(img_id)]
        assert len(fe) == len(rs), (img_id, len(fe), len(rs))
        extras = [r for r, f in zip(rs, fe) if f]           # 並びは後処理の上位 300 の順（score の降順）
        n_extra += len(extras)
        for r in extras:
            same = [(ann_id, box) for ann_id, cat, box in gt.get(img_id, []) if cat == r["category_id"]]
            if not same:
                continue
            iou = iou_xywh(np.array([r["bbox"]], float), np.array([b for _, b in same], float))[0]
            hits = [ann_id for (ann_id, _), v in zip(same, iou) if v >= 0.5]
            n_extra_hit_gt += bool(hits)
            hm = [h for h in hits if h in miss]
            n_extra_hit_missed += bool(hm)
            matched_missed.update(hm)
    out = {"preds": a.preds, "preds_sha256": sha256(a.preds), "n_images": len(by_img),
           "n_extra_in_top300": n_extra, "images_with_extra_in_top300": sum(any(flags[str(i)]) for i in by_img),
           "n_extra_matching_any_gt": n_extra_hit_gt, "n_extra_matching_missed": n_extra_hit_missed,
           "n_missed_val": len(miss), "n_missed_matched_by_extra": len(matched_missed)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(out, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("contrib")
    c.add_argument("--ann", required=True)
    c.add_argument("--preds", required=True)
    c.add_argument("--from-extra", required=True)
    c.add_argument("--missed", required=True)
    c.add_argument("--out", required=True)
    p = sub.add_parser("predict")
    p.add_argument("--split", default="train", choices=["train", "val"])
    p.add_argument("--shard", default="0/1")
    p.add_argument("--det-ckpt", required=True)
    p.add_argument("--out", required=True)
    m = sub.add_parser("missed")
    m.add_argument("--ann", required=True)
    m.add_argument("--preds", nargs="+", required=True)
    m.add_argument("--thresholds", default="0")
    m.add_argument("--controls", action="store_true")
    m.add_argument("--out", required=True)
    a = ap.parse_args()
    {"predict": cmd_predict, "missed": cmd_missed, "contrib": cmd_contrib}[a.cmd](a)


if __name__ == "__main__":
    main()
