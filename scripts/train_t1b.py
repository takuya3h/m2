#!/usr/bin/env python
"""T1b Phase→Det トレーナー（MT4MTL-KD-style §4.6 双方向の Phase→Det 半分・①予測相互作用 L3）。

凍結 S4 工程モデルの per-frame 事後分布（phase context, 9-d）を条件に、Relation-DETR の C5 を
**FiLM 注入**して検出を学習する。**s0_016（=S0-frozen seed42）から warm-start**し、FiLM は
zero-init=恒等なので warm-start 直後は S0-frozen と一致 → fine-tune で phase 変調を学習する。
Δ_detection=(T1b − S0-frozen 0.7051)。§4.6 の注入効果分離のため `--zero-ctx`（context を 0 に
固定した同スケジュール fine-tune）対照を用意する。

注入機構（§4.6・プロトコルは共通、差分は注入のみ→清潔な ablation）:
  --inject film      : C5 を FiLM 変調（§4.6 下限・既定。RelationDETRPhaseFiLM）
  --inject ca        : decoder cross-attention に c_phase token を注入（§4.6 primary。RelationDETRPhaseCrossAttn）

学習対象（warm-start fine-tune の範囲）:
  --trainable film   : 注入層(phase_*)のみ学習（最速・最純粋な注入効果。検出器は凍結）
  --trainable all    : 注入層 + 検出器全体を fine-tune（容量大・対照必須）

入力:
  data/processed/phase_context/relation_detr_seed42/{split}_phasectx.npz（frame_ids, ctx=(N,9)）
  検出: data/annotations/egosurgery_tool/instances_{train,val}.json + data/raw/ego
  warm-start init: data/external/weights/relation_detr_s0frozen_init_seed42.pth（= s0_016）

実行（.venv-relation-detr, cwd=third_party/Relation-DETR）:
  source .venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda-11.8
  python /abs/scripts/train_t1b.py --seed 42 --epochs 6
  python /abs/scripts/train_t1b.py --smoke           # 数 step・warm-start mAP 検証
  python /abs/scripts/train_t1b.py --zero-ctx ...     # §4.6 対照（注入効果分離）
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch

BODY = Path("/home/ubuntu/slocal2/m2")
RELDETR = BODY / "third_party" / "Relation-DETR"
sys.path.insert(0, str(RELDETR))
os.chdir(RELDETR)

PHASECTX_DIR = BODY / "data/processed/phase_context/relation_detr_seed42"
S0FROZEN_INIT = BODY / "data/external/weights/relation_detr_s0frozen_init_seed42.pth"
EGO_ROOT = os.environ.get("EGO_ROOT", str(BODY / "data/raw/ego"))
ANN_DIR = os.environ.get("EGO_ANN_DIR", str(BODY / "data/annotations/egosurgery_tool"))
MODEL_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b.py"
MODEL_CFG_CA = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_ca.py"
NUM_PHASES = 9


def load_phase_ctx(split: str) -> dict:
    """frame_id -> ctx(9,) float32。検出 image_id とは file_name の stem で突き合わせる。"""
    d = np.load(PHASECTX_DIR / f"{split}_phasectx.npz")
    ctx_all = d["ctx"]
    return {str(fid): ctx_all[i].astype(np.float32) for i, fid in enumerate(d["frame_ids"])}


def build_imgid_to_ctx(coco, ctx_by_frame: dict):
    """coco.imgs[image_id].file_name の stem を frame_id とみなし image_id->ctx を作る。

    欠落（検出 frame に phase ctx 無し）は zero ctx（=恒等 FiLM）で fail-safe。件数を返す。
    """
    imgid_to_ctx, miss = {}, 0
    for image_id, info in coco.imgs.items():
        fid = Path(info["file_name"]).stem
        ctx = ctx_by_frame.get(fid)
        if ctx is None:
            ctx = np.zeros(NUM_PHASES, dtype=np.float32)
            miss += 1
        imgid_to_ctx[image_id] = ctx
    return imgid_to_ctx, miss


def build_det_loader(train: bool):
    from datasets.coco import CocoDetection
    from torch.utils import data
    from transforms import presets
    from util.collate_fn import collate_fn
    from util.group_by_aspect_ratio import (
        GroupedBatchSampler,
        create_aspect_ratio_groups,
    )

    ann = "instances_train.json" if train else "instances_val.json"
    ds = CocoDetection(img_folder=EGO_ROOT, ann_file=f"{ANN_DIR}/{ann}",
                       transforms=presets.detr if train else None, train=train)
    params = dict(num_workers=4, collate_fn=collate_fn, pin_memory=True)
    if train:
        group_ids = create_aspect_ratio_groups(ds, k=3)
        bs = GroupedBatchSampler(data.RandomSampler(ds), group_ids, 2)
        return data.DataLoader(ds, batch_sampler=bs, **params)
    return data.DataLoader(ds, 1, shuffle=False, **params)


def detector_ckpt(seed: int) -> Path:
    """seed 対応の **学習済み 15クラス検出器**（s0_016/017/018 = warm-start 元・分母 S0-frozen 源）。

    注意: data/external/weights/relation_detr_s0frozen_init_seed42.pth は COCO(91class)初期化で
    別物（B1 が 12ep 学習する出発点）。T1b は収束済み検出器から warm-start するのでこちらを使う。
    """
    return RELDETR / f"checkpoints/incoming/seed{seed}/best_ap.pth"


def build_model(device, seed: int, model_cfg: str = MODEL_CFG):
    from util.lazy_load import Config
    from util.utils import load_checkpoint, load_state_dict
    model = Config(model_cfg).model
    ck = detector_ckpt(seed)
    if not ck.exists():
        raise FileNotFoundError(f"学習済み検出器 ckpt が無い: {ck}（s0_01{{6,7,8}} を転送せよ）")
    ckpt = load_checkpoint(str(ck))
    if isinstance(ckpt, dict) and "model" in ckpt:
        ckpt = ckpt["model"]
    load_state_dict(model, ckpt)  # phase_film は missing → zero-init 維持（=恒等）
    print(f"[t1b] warm-start from {ck}")
    return model.to(device)


def register_classes(model, det_loader):
    from util.misc import encode_labels
    coco = det_loader.dataset.coco
    cat_ids = list(range(max(coco.cats.keys()) + 1))
    classes = tuple(coco.cats.get(c, {"name": "none"})["name"] for c in cat_ids)
    model.register_buffer("_classes_", torch.tensor(encode_labels(classes)))


def ctx_for_targets(targets, imgid_to_ctx, device, zero_ctx: bool):
    """det バッチの targets（image_id 付き）→ (B,9) phase context。zero_ctx 対照は 0。"""
    B = len(targets)
    if zero_ctx:
        return torch.zeros(B, NUM_PHASES, device=device)
    rows = [imgid_to_ctx.get(int(t["image_id"]), np.zeros(NUM_PHASES, dtype=np.float32))
            for t in targets]
    return torch.from_numpy(np.stack(rows)).to(device)


@torch.no_grad()
def eval_detection(model, loader, imgid_to_ctx, device, zero_ctx, limit=None):
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset
    model.eval()
    coco = get_coco_api_from_dataset(loader.dataset)
    evaluator = CocoEvaluator(coco, ["bbox"])
    for i, (images, targets) in enumerate(loader):
        if limit is not None and i >= limit:
            break
        images = [img.to(device) for img in images]
        model.set_phase_context(ctx_for_targets(targets, imgid_to_ctx, device, zero_ctx))
        outputs = model(images)
        outputs = [{k: v.to("cpu") for k, v in t.items()} for t in outputs]
        evaluator.update({t["image_id"]: o for t, o in zip(targets, outputs)})
    evaluator.synchronize_between_processes()
    evaluator.accumulate()
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        evaluator.summarize()
    bbox = evaluator.coco_eval["bbox"]
    cat_names = [c["name"] for c in coco.loadCats(coco.getCatIds())]
    prec = bbox.eval["precision"]
    per_class = {}
    for ci, name in enumerate(cat_names):
        vals = prec[:, :, ci, 0, 2]
        vals = vals[vals > -1]
        per_class[name] = float(vals.mean()) if vals.size else float("nan")
    return float(bbox.stats[0]), per_class


def set_trainable(model, mode: str):
    """warm-start fine-tune の範囲。film=注入層(phase_*)のみ学習（残り凍結）/ all=全 fine-tune。

    注入層は FiLM の ``phase_film.*`` / CA の ``phase_embed|phase_attn|phase_norm.*`` を ``phase`` で一括選択
    （base 検出器に ``phase`` を含む param は無いので film/ca どちらでも安全）。
    """
    if mode == "film":
        for name, p in model.named_parameters():
            p.requires_grad_("phase" in name)
    # mode == "all" は config の freeze_indices(backbone) 以外すべて学習（既定の requires_grad）。


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    det_train = build_det_loader(train=True)
    det_val = build_det_loader(train=False)
    model_cfg = MODEL_CFG_CA if args.inject == "ca" else MODEL_CFG
    model = build_model(device, args.seed, model_cfg)
    register_classes(model, det_train)
    set_trainable(model, args.trainable)

    ctx_tr = build_imgid_to_ctx(det_train.dataset.coco, load_phase_ctx("train"))
    ctx_va = build_imgid_to_ctx(det_val.dataset.coco, load_phase_ctx("val"))
    imgid_to_ctx_tr, miss_tr = ctx_tr
    imgid_to_ctx_va, miss_va = ctx_va

    from optimizer import param_dict
    groups = param_dict.finetune_t1b(model, lr=args.lr, film_lr=args.film_lr)
    opt = torch.optim.AdamW(groups, lr=args.lr, weight_decay=1e-4, betas=(0.9, 0.999))
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=[max(args.epochs - 2, 1)], gamma=0.1)

    det_steps_per_ep = len(det_train)
    if args.smoke:
        args.epochs = 1
        det_steps_cap = 6
    else:
        det_steps_cap = None

    work = Path(os.environ.get("T1B_WORK_DIR",
                f"/tmp/t1b_work_{'zeroctx' if args.zero_ctx else args.trainable}_seed{args.seed}"))
    work.mkdir(parents=True, exist_ok=True)
    n_phase = sum(p.numel() for n, p in model.named_parameters() if p.requires_grad and "phase" in n)
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[t1b] seed={args.seed} inject={args.inject} trainable={args.trainable} zero_ctx={args.zero_ctx} "
          f"det_steps/ep={det_steps_per_ep} phase_params={n_phase} total_trainable={n_train} "
          f"miss_ctx(tr/va)={miss_tr}/{miss_va} work={work}", flush=True)

    # warm-start 健全性: 学習前 mAP（FiLM zero-init 恒等 → S0-frozen 水準のはず）
    init_map, _ = eval_detection(model, det_val, imgid_to_ctx_va, device, args.zero_ctx,
                                 limit=20 if args.smoke else None)
    print(f"[t1b] warm-start init mAP={init_map:.4f} (S0-frozen 水準なら warm-start+恒等 OK)", flush=True)
    if args.assert_init_map is not None and abs(init_map - args.assert_init_map) > args.assert_init_tol:
        print(f"[t1b][PREFLIGHT-FAIL] init mAP={init_map:.4f} != "
              f"{args.assert_init_map}±{args.assert_init_tol} → warm-start/zero-init恒等が壊れている。"
              f"中断（設定ドリフト・捏造防止）。", flush=True)
        sys.exit(3)

    phase_named = [(n, p) for n, p in model.named_parameters() if "phase" in n]
    phase_grad_seen = False
    best = {"mAP": init_map, "epoch": -1, "per_class_coco_map": {}}
    for epoch in range(args.epochs):
        model.train()
        from util.collate_fn import DataPrefetcher
        prefetcher = DataPrefetcher(det_train, device)
        n_steps = det_steps_cap or det_steps_per_ep
        ep_start = time.perf_counter()
        for step in range(n_steps):
            batch = prefetcher.next()
            if batch is None:
                break
            images, targets = batch
            model.set_phase_context(ctx_for_targets(targets, imgid_to_ctx_tr, device, args.zero_ctx))
            loss_dict = model(images, targets)
            loss = sum(loss_dict.values())
            opt.zero_grad()
            loss.backward()
            if not phase_grad_seen and any(
                    p.grad is not None and p.grad.abs().sum() > 0 for _, p in phase_named):
                phase_grad_seen = True
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 0.1)
            opt.step()
            if step % args.print_freq == 0:
                rate = (step + 1) / max(time.perf_counter() - ep_start, 1e-6)
                eta = (det_steps_per_ep - step) / max(rate, 1e-6) / 60
                print(f"[t1b][ep{epoch} {step}/{det_steps_per_ep}] L={float(loss):.3f} "
                      f"{rate:.1f}it/s eta_ep={eta:.0f}m", flush=True)
            if not math.isfinite(float(loss)):
                print("[t1b] loss not finite, stop")
                sys.exit(1)
        sched.step()

        mAP, per_class = eval_detection(model, det_val, imgid_to_ctx_va, device, args.zero_ctx,
                                        limit=20 if args.smoke else None)
        print(f"[t1b][ep{epoch}] val mAP={mAP:.4f}", flush=True)
        if mAP > best["mAP"]:
            best = {"mAP": mAP, "epoch": epoch, "per_class_coco_map": per_class}
            torch.save({"model": model.state_dict(), "epoch": epoch, "seed": args.seed},
                       work / "best_t1b.pth")

    result = {
        "seed": args.seed, "inject": args.inject, "trainable": args.trainable, "zero_ctx": args.zero_ctx,
        "epochs": args.epochs, "lr": args.lr, "film_lr": args.film_lr,
        "init_mAP": init_map, "best_epoch": best["epoch"], "mAP": best["mAP"],
        "per_class_coco_map": best.get("per_class_coco_map", {}),
        "denominator": "S0-frozen 0.7051±0.0052", "delta_note": "Δ_detection=(T1b − S0-frozen)",
    }
    (work / "t1b_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[t1b] DONE best@ep{best['epoch']} mAP={best['mAP']:.4f} (init {init_map:.4f}) -> {work}")
    if args.smoke:
        ok = phase_grad_seen and (init_map > 0.5)  # 注入層に勾配 + warm-start mAP 健全
        print(f"[t1b][smoke] phase_grad={phase_grad_seen} init_mAP={init_map:.4f} "
              f"=> {'PASS' if ok else 'FAIL'}")
        sys.exit(0 if ok else 2)


def parse_args():
    p = argparse.ArgumentParser(description="T1b Phase->Det FiLM trainer (warm-start fine-tune).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--film-lr", type=float, default=5e-4)
    p.add_argument("--trainable", choices=["film", "all"], default="all")
    p.add_argument("--inject", choices=["film", "ca"], default="film",
                   help="phase 注入機構: film(§4.6下限・C5 FiLM) / ca(§4.6 primary・decoder cross-attn)")
    p.add_argument("--zero-ctx", action="store_true", help="§4.6 対照: phase context を 0 固定で fine-tune")
    p.add_argument("--print-freq", type=int, default=200)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--assert-init-map", type=float, default=None,
                   help="warm-start init mAP がこの値±tol から外れたら中断（恒等性・ドリフト検査）")
    p.add_argument("--assert-init-tol", type=float, default=0.02)
    return p.parse_args()


if __name__ == "__main__":
    main()
