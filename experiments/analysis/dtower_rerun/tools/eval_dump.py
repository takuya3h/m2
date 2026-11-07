"""Run scripts/eval_relation_detr_map.py unchanged and keep what its evaluator already computed
(T-2026-11-07-dtower-rerun).

The evaluation script reports the overall COCO stats and per-class AP only. The prereg asks for the
val mAP of every video (§2.3) and for the test detections of the five videos that never enter a val
set (§2.4, pooled across the fold models afterwards by ``summarize.py``). This wrapper replaces
``util.engine.evaluate_acc`` with a function that calls the original and, on the main process,
reads the evaluator's gathered predictions (``CocoEvaluator.predictions["bbox"]`` after
``accumulate``, every image of the split) and writes:

- ``<prefix>.per_video.json``: per video the number of images, COCO stats and per-class AP, from a
  standard ``COCOeval`` on the evaluator's ground truth with the image ids of that video; plus the
  same computation over all images and its difference from the evaluator's own AP (a check that the
  recomputation is the evaluator's computation).
- ``<prefix>.detections.json.gz`` (unless ``EVAL_DUMP_DETECTIONS=0``): the images, categories and
  every detection (image id, category id, xywh box, score).

Nothing the evaluation computes or prints changes; the script's ``--out`` json is written as before.

    accelerate launch ... eval_dump.py --config ... --checkpoint ... --out ...   (the script's arguments)
    env: EVAL_DUMP_PREFIX=<path prefix>  [EVAL_DUMP_DETECTIONS=0]
"""
from __future__ import annotations

import contextlib
import copy
import gzip
import importlib.util
import io
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
REPO = ROOT / "third_party/Relation-DETR"
sys.path.insert(0, str(REPO))

import util.engine as engine  # noqa: E402
from pycocotools.cocoeval import COCOeval as CocoEvalStandard  # noqa: E402  (alias: semgrep hook)

spec = importlib.util.spec_from_file_location("eval_relation_detr_map", ROOT / "scripts/eval_relation_detr_map.py")
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)

PREFIX = os.environ["EVAL_DUMP_PREFIX"]
DETECTIONS = os.environ.get("EVAL_DUMP_DETECTIONS", "1") == "1"
original = engine.evaluate_acc


def video(file_name):
    return Path(str(file_name)).name[:2]


def standard(gt, dt, image_ids):
    ev = CocoEvalStandard(gt, dt, iouType="bbox")
    ev.params.imgIds = sorted(image_ids)
    with contextlib.redirect_stdout(io.StringIO()):
        ev.evaluate()
        ev.accumulate()
        ev.summarize()
    names = {c["id"]: c["name"] for c in gt.dataset["categories"]}
    per_class = {}
    for k, cid in enumerate(ev.params.catIds):
        p = ev.eval["precision"][:, :, k, 0, -1]
        p = p[p > -1]
        per_class[names.get(cid, str(cid))] = float(p.mean()) if p.size else None
    return {"images": len(image_ids), "stats": [float(v) for v in ev.stats], "AP": float(ev.stats[0]),
            "per_class_ap": per_class}


def dumped(model, data_loader, epoch, accelerator=None):
    result = original(model, data_loader, epoch, accelerator)
    if accelerator is not None and not accelerator.is_main_process:
        return result
    gt = result.coco_gt
    predictions = list(result.predictions["bbox"])
    evaluated = [int(i) for i in result.coco_eval["bbox"].params.imgIds]
    dt = gt.loadRes(copy.deepcopy(predictions)) if predictions else None
    by_video = {}
    for image_id in evaluated:
        by_video.setdefault(video(gt.imgs[image_id]["file_name"]), []).append(image_id)
    out = {"evaluator_AP": float(result.coco_eval["bbox"].stats[0]), "images": len(evaluated),
           "detections": len(predictions), "per_video": {}}
    if dt is not None:
        everything = standard(gt, dt, evaluated)
        out["recomputed_all"] = everything
        out["recomputed_minus_evaluator_AP"] = everything["AP"] - out["evaluator_AP"]
        for name in sorted(by_video):
            out["per_video"][name] = standard(gt, dt, by_video[name])
    Path(PREFIX + ".per_video.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    if DETECTIONS:
        payload = {"images": [{k: gt.imgs[i][k] for k in ("id", "file_name", "width", "height")} for i in evaluated],
                   "categories": gt.dataset["categories"],
                   "detections": [{"image_id": int(d["image_id"]), "category_id": int(d["category_id"]),
                                   "bbox": [float(v) for v in d["bbox"]], "score": float(d["score"])}
                                  for d in predictions if math.isfinite(float(d["score"]))]}
        with gzip.open(PREFIX + ".detections.json.gz", "wt") as handle:
            json.dump(payload, handle)
    print(f"[eval_dump] per-video AP for {len(out['per_video'])} videos -> {PREFIX}.per_video.json "
          f"(recomputed minus evaluator {out.get('recomputed_minus_evaluator_AP')})", flush=True)
    return result


engine.evaluate_acc = dumped

if __name__ == "__main__":
    evaluation.main()
