#!/usr/bin/env python
"""B2b 工程→検出（Tier-0 ①片方向 pipeline・training-free phase-prior re-scoring）。

「工程文脈を検出の prior に」する Tier-0 下限。**学習ゼロ**で、凍結検出器の予測 score を
凍結 S4 の per-frame phase 事後 ＋ 学習集合の P(tool|phase) で再重み付けし、Δ_detection を測る:

    new_score(det of class t in frame f) = score × ( Σ_p π_f[p]·P(t|phase=p) )^α

P(t|phase=p) は **train の検出アノテ（frame に tool t が在るか）× phase manifest（frame の phase）**
から推定（EDA で術具×工程は準決定的）。val の phase は凍結 S4 の予測事後（phase_context cache）。
COCO mAP を baseline(元 score) と rescored で比較 → **Δ_detection=(rescored − baseline)**（同一検出器・同一eval）。

実行（.venv-relation-detr, cwd=third_party/Relation-DETR）:
  source ../../.venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda
  python ../../scripts/run_b2b_rescore.py --alpha 1.0 --limit 0
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

BODY = Path("/home/ubuntu/slocal2/m2")
RELDETR = BODY / "third_party" / "Relation-DETR"
sys.path.insert(0, str(RELDETR))
import os  # noqa: E402

os.chdir(RELDETR)

MANIFEST_DIR = BODY / "data/processed/phase_manifest"
PHASECTX_DIR = BODY / "data/processed/phase_context/relation_detr_seed42"
ANN_DIR = BODY / "data/annotations/egosurgery_tool"
EGO_ROOT = str(BODY / "data/raw/ego")
MODEL_CFG = str(RELDETR / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")
CKPT = str(RELDETR / "checkpoints/incoming/seed42/best_ap.pth")
NUM_TOOLS = 15
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
NUM_PHASES = len(VOCAB)


def phase_by_frame(split: str) -> dict:
    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    return {fr["frame"]: fr["label"] for clip in man["clips"] for fr in clip["frames"]}


def tool_prior_from_train() -> np.ndarray:
    """P(tool t | phase p) を train から推定（frame に tool t が在る割合）。(P,T)。"""
    ann = json.loads((ANN_DIR / "instances_train.json").read_text())
    id2frame = {im["id"]: Path(im["file_name"]).stem for im in ann["images"]}
    tools_in_frame = defaultdict(set)
    for a in ann["annotations"]:
        c = int(a["category_id"])
        if c < NUM_TOOLS:
            tools_in_frame[id2frame[a["image_id"]]].add(c)
    ph = phase_by_frame("train")
    cnt = np.zeros((NUM_PHASES, NUM_TOOLS), dtype=np.float64)
    pcnt = np.zeros(NUM_PHASES, dtype=np.float64)
    for frame, p in ph.items():
        pcnt[p] += 1
        for t in tools_in_frame.get(frame, ()):  # 在った tool のみ加算
            cnt[p, t] += 1
    prior = cnt / np.clip(pcnt[:, None], 1, None)   # P(t|p) ∈ [0,1]
    return prior.astype(np.float32)


def load_val_phasectx() -> dict:
    d = np.load(PHASECTX_DIR / "val_phasectx.npz")
    ctx = d["ctx"]
    return {str(fid): ctx[i] for i, fid in enumerate(d["frame_ids"])}


def main():
    ap = argparse.ArgumentParser(description="B2b training-free phase-prior re-scoring (phase->det).")
    ap.add_argument("--alpha", type=float, default=1.0, help="prior の効き具合（0=baseline）")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    device = torch.device(args.device if torch.cuda.is_available() else "cpu")

    from datasets.coco import CocoDetection
    from torch.utils import data
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset
    from util.collate_fn import collate_fn
    from util.lazy_load import Config
    from util.utils import load_checkpoint, load_state_dict

    model = Config(MODEL_CFG).model.eval()
    ck = load_checkpoint(CKPT)
    if isinstance(ck, dict) and "model" in ck:
        ck = ck["model"]
    load_state_dict(model, ck)
    model.to(device)
    for p in model.parameters():
        p.requires_grad_(False)

    prior = tool_prior_from_train()              # (P,T)
    ctx_by_frame = load_val_phasectx()           # frame -> (P,)
    ds = CocoDetection(img_folder=EGO_ROOT, ann_file=f"{ANN_DIR}/instances_val.json", train=False)
    loader = data.DataLoader(ds, 1, shuffle=False, num_workers=4, collate_fn=collate_fn)
    coco = get_coco_api_from_dataset(ds)
    ev_base = CocoEvaluator(coco, ["bbox"])
    ev_resc = CocoEvaluator(coco, ["bbox"])

    miss = 0
    for i, (images, targets) in enumerate(loader):
        if args.limit and i >= args.limit:
            break
        with torch.no_grad(), torch.autocast(device_type="cuda", dtype=torch.float16,
                                             enabled=(device.type == "cuda")):
            out = model([img.to(device) for img in images])
        for t, o in zip(targets, out):
            frame = Path(coco.imgs[int(t["image_id"])]["file_name"]).stem
            o = {k: v.detach().cpu() for k, v in o.items()}
            ev_base.update({int(t["image_id"]): o})
            ctx = ctx_by_frame.get(frame)
            if ctx is None:
                miss += 1
                ev_resc.update({int(t["image_id"]): o})
                continue
            ptool = torch.from_numpy(ctx @ prior)          # (T,) = Σ_p π_p·P(t|p)
            labels = o["labels"].clamp(max=NUM_TOOLS - 1)
            factor = ptool[labels].clamp(min=1e-6) ** args.alpha
            ro = {**o, "scores": o["scores"] * factor}
            ev_resc.update({int(t["image_id"]): ro})

    import contextlib
    import io
    res = {}
    for tag, ev in (("baseline", ev_base), ("rescored", ev_resc)):
        ev.synchronize_between_processes()
        ev.accumulate()
        with contextlib.redirect_stdout(io.StringIO()):
            ev.summarize()
        res[tag] = float(ev.coco_eval["bbox"].stats[0])
    delta = res["rescored"] - res["baseline"]
    print(f"[b2b] alpha={args.alpha} miss_ctx={miss} "
          f"mAP baseline={res['baseline']:.4f} rescored={res['rescored']:.4f} "
          f"Δ_detection={delta:+.4f}")
    out_dir = BODY / "experiments/transfer"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"b2b_rescore_alpha{args.alpha}.json").write_text(json.dumps(
        {"alpha": args.alpha, "mAP_baseline": res["baseline"], "mAP_rescored": res["rescored"],
         "delta_detection": delta, "miss_ctx": miss,
         "method": "training_free_phase_prior_rescore", "denominator": "frozen (=S0-frozen, same eval)"},
        indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
