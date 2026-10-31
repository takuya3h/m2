"""検出塔の decoder の特徴の取り出し（非公式 T-2026-10-31-grasp-pilot-probe、Task C-5）。.venv-relation-detr で動かす。

凍結した D*（塔単独の構成）を評価の経路（増強なし、検出器の eval_transform）で train と val の画像に当て、
正解の枠ごとに、上位 300 の出力のうち IoU が最大でかつ 0.5 以上の出力の query の、decoder の最終層の出力（256 次元）を取る。
    decoder の最終層の出力 = 最終層のクラスのヘッド transformer.decoder.class_head[-1] の入力（decoder の norm を当てた query）。
                            前向きのフックで取る（third_party は変えない）
    上位 300 の各出力の query の番号 = 後処理（PostProcess）と同じ torch.topk を pred_logits に当て直して得る
                            （同じ演算なので出力の並びと一致する。一致を score で確かめる）
正解の枠は xq_missed.kept_gt の規則（iscrowd 0、幅と高さが正）。対応の無い枠は matched = False で残す（probe が除く）。

    python scripts/grasppilot/extract_decfeat.py --split train --shard 0/2 --out <npz>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import torch

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
import train_t1b as t1b  # noqa: E402

from stage2pilot import common as C  # noqa: E402
from stage2pilot.xq_missed import iou_xywh, kept_gt  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True, choices=("train", "val"))
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from datasets.coco import CocoDetection
    from torch.utils import data
    from util.collate_fn import collate_fn
    device = torch.device("cuda")
    torch.manual_seed(0)
    ann_file = f"{t1b.ANN_DIR}/instances_{a.split}.json"
    ds = CocoDetection(img_folder=t1b.EGO_ROOT, ann_file=ann_file, transforms=None, train=False)
    i, n = (int(x) for x in a.shard.split("/"))
    ds.ids = [x for k, x in enumerate(ds.ids) if k % n == i]
    stems_all = {x: Path(ds.coco.imgs[x]["file_name"]).stem for x in ds.ids}
    videos = C.assert_no_test(stems_all.values(), f"extract_decfeat/{a.split}")
    loader = data.DataLoader(ds, 1, shuffle=False, num_workers=4, collate_fn=collate_fn, pin_memory=True)  # nosemgrep
    cfg = str(t1b.RELDETR / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")
    model = t1b.build_model(device, 42, cfg, ckpt_override=str(C.DET_CKPT)).eval()
    t1b.register_classes(model, loader)
    cap = {}
    last = model.transformer.decoder.class_head[-1]
    h1 = last.register_forward_hook(lambda m, inp, out: cap.__setitem__("feat", inp[0].detach()))
    h2 = model.postprocessor.register_forward_pre_hook(lambda m, args: cap.__setitem__("logits", args[0]["pred_logits"].detach()))
    raw = json.loads(Path(ann_file).read_text())
    gt = kept_gt({"images": {im["id"]: im for im in raw["images"]}, "annotations": raw["annotations"]})
    rows = {"ann_ids": [], "cats": [], "stems": [], "matched": [], "iou": [], "score": [], "query": [], "feat": []}
    score_check = 0.0
    with torch.no_grad():
        for images, targets in loader:
            images = [im.to(device) for im in images]
            out = model(images)[0]
            logits, feat = cap["logits"][0], cap["feat"][0]                 # (900, 15), (900, 256)
            vals, idx = torch.topk(logits.sigmoid().view(1, -1), model.postprocessor.select_box_nums_for_evaluation, dim=1)
            q = torch.div(idx[0], logits.shape[1], rounding_mode="trunc")
            score_check = max(score_check, float((vals[0] - out["scores"]).abs().max()))
            boxes = out["boxes"].cpu().numpy()
            dxywh = np.c_[boxes[:, :2], boxes[:, 2:] - boxes[:, :2]]
            img_id = int(targets[0]["image_id"])
            for aid, c, b in gt[img_id]:
                iou = iou_xywh(np.array([b], float), dxywh)[0]
                j = int(iou.argmax())
                ok = bool(iou[j] >= 0.5)
                rows["ann_ids"].append(aid); rows["cats"].append(c); rows["stems"].append(stems_all[img_id])
                rows["matched"].append(ok); rows["iou"].append(float(iou[j])); rows["score"].append(float(out["scores"][j]))
                rows["query"].append(int(q[j]))
                rows["feat"].append(feat[q[j]].float().cpu().numpy().astype(np.float16))
    h1.remove(); h2.remove()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    np.savez(a.out, **{k: np.array(v) for k, v in rows.items()}, videos=np.array(videos),
             score_check_max_abs=np.array(score_check))
    print(json.dumps({"split": a.split, "shard": a.shard, "images": len(ds.ids), "boxes": len(rows["ann_ids"]),
                      "unmatched": int(len(rows["matched"]) - sum(rows["matched"])), "score_check_max_abs": score_check,
                      "videos": videos}))


if __name__ == "__main__":
    main()
