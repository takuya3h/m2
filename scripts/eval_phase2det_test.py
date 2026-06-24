#!/usr/bin/env python
"""test split での phase→det 検出評価（per-class AP・§9 の決定的検証）。

既存の収束済み検出器を **test split**（instances_test.json, 4265枚）で COCO 評価し、overall mAP と
per-class AP を出す。phase→det 注入（T1b-FiLM / T1b-CA）が、rare∧工程特異術具の検出を test で
変えるか（val は rare 術具の実例が希少 → test の方が信頼できる）を確かめる。

評価対象（abs path・cwd=RELDETR でも壊れない）:
  s0_frozen      : 注入なしベースライン（warm-start 元の S0-frozen 検出器）
  t1b_film_inj   : FiLM 注入（test phase context あり）
  t1b_film_ctrl  : FiLM 対照（zero context）
  t1b_ca_inj     : CA 注入（test phase context あり）

実行（.venv-relation-detr）:
  CUDA_VISIBLE_DEVICES=0 python scripts/eval_phase2det_test.py --models s0_frozen,t1b_film_inj
  CUDA_VISIBLE_DEVICES=1 python scripts/eval_phase2det_test.py --models t1b_film_ctrl,t1b_ca_inj
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path

import torch

BODY = Path("/home/ubuntu/slocal2/m2")
RELDETR = BODY / "third_party" / "Relation-DETR"
sys.path.insert(0, str(RELDETR))
sys.path.insert(0, str(BODY / "scripts"))
os.chdir(RELDETR)

from train_t1b import NUM_PHASES, build_imgid_to_ctx, ctx_for_targets, load_phase_ctx  # noqa: E402

ANN = str(BODY / "data/annotations/egosurgery_tool")
EGO = str(BODY / "data/raw/ego")
OUT_DIR = BODY / "experiments/analysis/step_c_coupling_analysis"
BASE_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery.py"
T1B_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b.py"
CA_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_ca.py"

MODELS = {
    "s0_frozen": dict(cfg=BASE_CFG, ckpt=str(RELDETR / "checkpoints/incoming/seed42/best_ap.pth"), phase=None),
    "t1b_film_inj": dict(cfg=T1B_CFG, ckpt="/tmp/t1b_film_seed42/best_t1b.pth", phase="real"),
    "t1b_film_ctrl": dict(cfg=T1B_CFG, ckpt="/tmp/t1b_film_zeroctx_seed42/best_t1b.pth", phase="zero"),
    "t1b_ca_inj": dict(cfg=CA_CFG, ckpt=str(BODY / "transfer/t1b_ca_seed42/best_t1b.pth"), phase="real"),
}


def build_test_loader():
    from datasets.coco import CocoDetection
    from torch.utils import data
    from util.collate_fn import collate_fn

    ds = CocoDetection(img_folder=EGO, ann_file=f"{ANN}/instances_test.json", transforms=None, train=False)
    return data.DataLoader(ds, 1, shuffle=False, num_workers=4, collate_fn=collate_fn, pin_memory=True)


def load_model(cfg, ckpt, device):
    from util.lazy_load import Config
    from util.utils import load_checkpoint, load_state_dict

    model = Config(cfg).model
    ck = load_checkpoint(ckpt)
    if isinstance(ck, dict) and "model" in ck:
        ck = ck["model"]
    load_state_dict(model, ck)  # 非strict（不一致は警告のみ）
    return model.to(device).eval()


def register_classes(model, loader):
    from util.misc import encode_labels

    coco = loader.dataset.coco
    cat_ids = list(range(max(coco.cats.keys()) + 1))
    classes = tuple(coco.cats.get(c, {"name": "none"})["name"] for c in cat_ids)
    model.register_buffer("_classes_", torch.tensor(encode_labels(classes)))


@torch.no_grad()
def evaluate(model, loader, imgid_to_ctx, device, phase_mode):
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset

    coco = get_coco_api_from_dataset(loader.dataset)
    ev = CocoEvaluator(coco, ["bbox"])
    has_phase = hasattr(model, "set_phase_context")
    for images, targets in loader:
        images = [img.to(device) for img in images]
        if has_phase:
            if phase_mode == "zero":
                ctx = torch.zeros(len(targets), NUM_PHASES, device=device)
            else:
                ctx = ctx_for_targets(targets, imgid_to_ctx, device, zero_ctx=False)
            model.set_phase_context(ctx)
        out = model(images)
        out = [{k: v.to("cpu") for k, v in t.items()} for t in out]
        ev.update({t["image_id"]: o for t, o in zip(targets, out)})
    ev.synchronize_between_processes()
    ev.accumulate()
    with contextlib.redirect_stdout(io.StringIO()):
        ev.summarize()
    bbox = ev.coco_eval["bbox"]
    names = [c["name"] for c in coco.loadCats(coco.getCatIds())]
    prec = bbox.eval["precision"]
    per = {}
    for ci, n in enumerate(names):
        v = prec[:, :, ci, 0, 2]
        v = v[v > -1]
        per[n] = float(v.mean()) if v.size else float("nan")
    return float(bbox.stats[0]), per


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True, help="カンマ区切り（MODELS のキー）")
    args = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    loader = build_test_loader()
    imgid_to_ctx, miss = build_imgid_to_ctx(loader.dataset.coco, load_phase_ctx("test"))
    print(f"[test-eval] test images={len(loader.dataset)} miss_ctx={miss}", flush=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for key in args.models.split(","):
        m = MODELS[key]
        if not Path(m["ckpt"]).exists():
            print(f"[test-eval] SKIP {key}: ckpt 無 {m['ckpt']}", flush=True)
            continue
        model = load_model(m["cfg"], m["ckpt"], device)
        register_classes(model, loader)
        mAP, per = evaluate(model, loader, imgid_to_ctx, device, m["phase"])
        res = {"model": key, "split": "test", "ckpt": m["ckpt"], "phase": m["phase"],
               "mAP": mAP, "per_class_ap": per}
        (OUT_DIR / f"test_eval_{key}.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
        print(f"[test-eval] {key}: test mAP={mAP:.4f} -> test_eval_{key}.json", flush=True)


if __name__ == "__main__":
    main()
