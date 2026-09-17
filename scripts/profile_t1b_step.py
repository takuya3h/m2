#!/usr/bin/env python
"""T1b（P→D 界面）の 1 step を要素へ分解して所要時間を測る。

契約 T-2026-09-17-frozen-feature-cache-timing の識別実験。
「1 run 約 4 時間の原因は、凍結した塔へ毎 epoch 画像を通し直していることか」を
**キャッシュを作る前に**判定するために要る量は、1 step の中で凍結 backbone の
順伝播が占める割合である。上限はこの割合から決まる（Amdahl）。

train_t1b.py の構築関数をそのまま再利用する。**処方は変えない**
（同じ config・同じ loader・同じ最適化器群・同じ seed）。

出力は JSON。数値は実測のみで、推定値は書かない。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_t1b as T  # noqa: E402  (chdir/sys.path を伴うため後置 import)


def sync() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--steps", type=int, default=60)
    p.add_argument("--eval-images", type=int, default=60)
    p.add_argument("--out", required=True)
    args = p.parse_args()

    device = torch.device("cuda")
    torch.manual_seed(args.seed)

    det_train = T.build_det_loader(train=True)
    det_val = T.build_det_loader(train=False)
    model = T.build_model(device, args.seed, T.MODEL_CFG)
    T.register_classes(model, det_train)
    T.set_trainable(model, "film")

    ctx_tr, _ = T.build_imgid_to_ctx(det_train.dataset.coco, T.load_phase_ctx("train"))
    ctx_va, _ = T.build_imgid_to_ctx(det_val.dataset.coco, T.load_phase_ctx("val"))

    from optimizer import param_dict
    groups = param_dict.finetune_t1b(model, lr=1e-4, film_lr=5e-4)
    opt = torch.optim.AdamW(groups, lr=1e-4, weight_decay=1e-4, betas=(0.9, 0.999))

    # 凍結 backbone の順伝播だけを計る。hook の中で同期するため、この分は
    # forward 全体の計測にも含まれる（入れ子。割合の計算はそれを前提にする）。
    bb = {"t": 0.0, "start": 0.0, "shapes": []}

    def pre_hook(_m, _inp):
        sync()
        bb["start"] = time.perf_counter()

    def post_hook(_m, _inp, out):
        sync()
        bb["t"] += time.perf_counter() - bb["start"]
        if isinstance(out, (list, tuple)):
            feats = out
        elif isinstance(out, dict):
            feats = list(out.values())
        else:
            feats = [out]
        bb["shapes"] = [tuple(f.shape) for f in feats if torch.is_tensor(f)]

    h1 = model.backbone.register_forward_pre_hook(pre_hook)
    h2 = model.backbone.register_forward_hook(post_hook)

    from util.collate_fn import DataPrefetcher
    model.train()
    prefetcher = DataPrefetcher(det_train, device)

    rec = []
    total_steps = args.warmup + args.steps
    img_hw = []
    feat_bytes = []
    for step in range(total_steps):
        sync()
        t0 = time.perf_counter()
        batch = prefetcher.next()
        sync()
        t1 = time.perf_counter()
        if batch is None:
            break
        images, targets = batch
        model.set_phase_context(T.ctx_for_targets(targets, ctx_tr, device, False))
        bb["t"] = 0.0
        loss_dict = model(images, targets)
        loss = sum(loss_dict.values())
        sync()
        t2 = time.perf_counter()
        opt.zero_grad()
        loss.backward()
        sync()
        t3 = time.perf_counter()
        torch.nn.utils.clip_grad_norm_(
            [q for q in model.parameters() if q.requires_grad], 0.1)
        opt.step()
        sync()
        t4 = time.perf_counter()

        if step >= args.warmup:
            rec.append({
                "data": t1 - t0, "forward": t2 - t1, "backbone": bb["t"],
                "backward": t3 - t2, "optim": t4 - t3, "step": t4 - t0,
            })
            img_hw.extend([tuple(im.shape) for im in images])
            nb = sum(int(torch.tensor(s).prod()) for s in bb["shapes"])
            feat_bytes.append({"batch": len(images), "elems": nb,
                               "shapes": [list(s) for s in bb["shapes"]]})

    h1.remove()
    h2.remove()

    # 評価 1 枚あたり（epoch 末に val 全件で回る分）。学習と別に計る。
    model.eval()
    ev = []
    with torch.no_grad():
        for i, (images, targets) in enumerate(det_val):
            if i >= args.eval_images:
                break
            images = [im.to(device) for im in images]
            model.set_phase_context(T.ctx_for_targets(targets, ctx_va, device, False))
            sync()
            e0 = time.perf_counter()
            model(images)
            sync()
            ev.append(time.perf_counter() - e0)

    def stat(xs):
        xs = sorted(xs)
        n = len(xs)
        return {"n": n, "sum": sum(xs), "mean": sum(xs) / n,
                "median": xs[n // 2], "min": xs[0], "max": xs[-1]}

    out = {
        "recipe": {"inject": "film", "trainable": "film", "seed": args.seed,
                   "model_cfg": T.MODEL_CFG, "batch_size": 2,
                   "steps_per_epoch": len(det_train),
                   "train_images": len(det_train.dataset),
                   "val_images": len(det_val.dataset)},
        "warmup": args.warmup, "measured_steps": len(rec),
        "per_step": {k: stat([r[k] for r in rec])
                     for k in ("data", "forward", "backbone", "backward", "optim", "step")},
        "eval_per_image": stat(ev),
        "backbone_out_shapes": feat_bytes[0]["shapes"] if feat_bytes else [],
        "feat_elems_per_batch": stat([f["elems"] for f in feat_bytes]),
        "input_shapes_sample": [list(s) for s in img_hw[:10]],
        "gpu": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
    }
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out["per_step"], indent=2, ensure_ascii=False))
    print("eval/枚:", json.dumps(out["eval_per_image"], ensure_ascii=False))


if __name__ == "__main__":
    main()
