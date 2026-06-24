#!/usr/bin/env python
"""B1 素朴MTL 統合トレーナー（②特徴レベル結合・最初の結合手法 / 単GPU）。

凍結 backbone(Relation-DETR seed42) + 共有 C5 線形 neck に、検出損失と工程損失の勾配を
**同時に流す**素朴MTL（`L = w_d·L_det + w_p·L_phase`、or Kendall&Gal）。Δ_detection=(B1−S0-frozen′),
Δ_phase=(B1−S4′) を測り negative transfer を可視化する（研究計画 §8.1 Tier0「必須・最初」）。

設計（プラン承認 2026-06-20）:
- Round-robin: 検出は S0-frozen′ と同一の標準ローダ（全frame, bs2, 12ep 相当）で駆動。
  R step ごとに工程 clip を 1 本（凍結 GAP キャッシュ）回し、両損失を同一 c5_neck に流す。
- 単GPU（DDP の二枝勾配同期を回避、工程は S4′ の 1-GPU 構成と一致）。accelerate 非使用。
- 検出枝は親 forward（c5_neck.forward spatial）、工程枝は model.phase_loss（c5_neck.forward_vector）。
- best は検出 mAP で選択し、その同一 epoch の工程予測も確定 → 1 モデルから両 Δ（§4）。
- 工程の厳密指標（edit/seg-F1/jaccard）と証跡組成・Δ は本体 .venv の後処理に委譲
  （本トレーナーは .venv-relation-detr で動き egosurgery を import しないため）。ここでは
  検出 mAP・per_class と工程 frame 予測・両 eval_recipe を work_dir に出力する。

実行（.venv-relation-detr, cwd=third_party/Relation-DETR で ninja を PATH に）:
  source .venv-relation-detr/bin/activate   # ninja を PATH に載せる
  cd third_party/Relation-DETR
  B1_WEIGHTING=fixed CUDA_VISIBLE_DEVICES=0 python /abs/scripts/train_b1_mtl.py \
      --weighting fixed --seed 42 --epochs 12
  python /abs/scripts/train_b1_mtl.py --smoke   # 数 step・少 clip で疎通確認
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
# Relation-DETR の相対 import と CUDA 拡張ビルドのため cwd/sys.path を合わせる。
sys.path.insert(0, str(RELDETR))
os.chdir(RELDETR)

CACHE_DIR = BODY / "data/processed/stage1_features/relation_detr_seed42"
MANIFEST_DIR = BODY / "data/processed/phase_manifest"
S0FROZEN_INIT = BODY / "data/external/weights/relation_detr_s0frozen_init_seed42.pth"
EGO_ROOT = os.environ.get("EGO_ROOT", str(BODY / "data/raw/ego"))
ANN_DIR = os.environ.get("EGO_ANN_DIR", str(BODY / "data/annotations/egosurgery_tool"))
MODEL_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery_b1_mtl.py"


def load_phase_clips(split: str):
    """(clip_id, gap (2048,T) float32, labels (T,) int64) のリスト。train_s4_tecno と同形。"""
    d = np.load(CACHE_DIR / f"{split}_gap.npz")
    feats_all = d["features"]          # 一度だけ実体化（NpzFile 遅延ロードの OOM 回避）
    frame_ids = d["frame_ids"]
    by_frame = {str(fid): feats_all[i] for i, fid in enumerate(frame_ids)}
    man = json.loads((MANIFEST_DIR / f"{split}.json").read_text())
    clips = []
    for clip in man["clips"]:
        frames = clip["frames"]
        feats = np.stack([by_frame[fr["frame"]] for fr in frames]).astype(np.float32)  # (T,2048)
        labels = np.asarray([fr["label"] for fr in frames], dtype=np.int64)
        clips.append((clip["clip_id"], feats.T.copy(), labels))  # gap=(2048,T)
    return clips


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


def build_model(weighting: str, device):
    os.environ["B1_WEIGHTING"] = weighting
    from util.lazy_load import Config
    from util.utils import load_checkpoint, load_state_dict

    model = Config(MODEL_CFG).model
    # S0-frozen init（検出分母と同一 init）。c5_neck/phase_head は missing → zero/random 初期維持。
    ckpt = load_checkpoint(str(S0FROZEN_INIT))
    load_state_dict(model, ckpt)
    return model.to(device)


def register_classes(model, det_loader):
    from util.misc import encode_labels
    coco = det_loader.dataset.coco
    cat_ids = list(range(max(coco.cats.keys()) + 1))
    classes = tuple(coco.cats.get(c, {"name": "none"})["name"] for c in cat_ids)
    model.register_buffer("_classes_", torch.tensor(encode_labels(classes)))


def combined_loss(model, l_det, l_phase, args):
    """L = w_d·L_det + w_p·L_phase（fixed）or Kendall&Gal（uncertainty）。l_phase は None 可。"""
    if args.weighting == "uncertainty":
        total = torch.exp(-model.log_var_d) * l_det + model.log_var_d
        if l_phase is not None:
            total = total + torch.exp(-model.log_var_p) * l_phase + model.log_var_p
        return total
    total = args.w_det * l_det
    if l_phase is not None:
        total = total + args.w_phase * l_phase
    return total


@torch.no_grad()
def eval_detection(model, loader, device, limit=None):
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset
    model.eval()
    coco = get_coco_api_from_dataset(loader.dataset)
    evaluator = CocoEvaluator(coco, ["bbox"])
    for i, (images, targets) in enumerate(loader):
        if limit is not None and i >= limit:
            break
        images = [img.to(device) for img in images]
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
    return float(bbox.stats[0]), per_class  # mAP(IoU .50:.95), per-class COCO AP


@torch.no_grad()
def eval_phase(model, clips, device):
    """frame-accuracy（軽量・best 選択用）＋ 全 clip の予測列（厳密指標は本体後処理）。"""
    model.eval()
    correct = total = 0
    preds_out = {}
    for clip_id, gap, labels in clips:
        x = torch.from_numpy(gap).unsqueeze(0).to(device)  # (1,2048,T)
        logits = model.forward_phase(x)[-1]                # 最終ステージ (1,C,T)
        preds = logits[0].argmax(0).cpu().numpy()
        correct += int((preds == labels).sum())
        total += len(labels)
        preds_out[clip_id] = {"preds": preds.tolist(), "labels": labels.tolist()}
    return correct / max(total, 1), preds_out


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    det_train = build_det_loader(train=True)
    det_val = build_det_loader(train=False)
    train_clips = load_phase_clips("train")
    val_clips = load_phase_clips("val")
    model = build_model(args.weighting, device)
    register_classes(model, det_train)

    from optimizer import param_dict
    groups = param_dict.finetune_b1_mtl(model, lr=args.lr, phase_lr=args.phase_lr)
    opt = torch.optim.AdamW(groups, lr=args.lr, weight_decay=1e-4, betas=(0.9, 0.999))
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=[10], gamma=0.1)

    # step 比 R: 検出総 step / 工程総 step（既定は両分母を同時に満たす auto）。
    det_steps_per_ep = len(det_train)
    R = args.step_ratio if args.step_ratio > 0 else max(
        1, round(det_steps_per_ep * args.epochs / max(len(train_clips) * args.phase_epochs_equiv, 1)))
    if args.smoke:
        args.epochs = 1
        R = 2
        det_steps_cap = 6
        train_clips = train_clips[:4]
        val_clips = val_clips[:2]
    else:
        det_steps_cap = None

    work = Path(os.environ.get("B1_WORK_DIR", f"/tmp/b1_work_{args.weighting}_seed{args.seed}"))
    work.mkdir(parents=True, exist_ok=True)
    print(f"[b1] weighting={args.weighting} seed={args.seed} device={device} "
          f"det_steps/ep={det_steps_per_ep} phase_clips={len(train_clips)} R={R} work={work}")

    phase_iter = _cycle(train_clips)
    best = {"mAP": -1.0}
    grad_seen = {"det": False, "phase": False}  # smoke 用: 両枝が neck に勾配を流したか
    for epoch in range(args.epochs):
        model.train()
        warmup = None
        if epoch == 0:
            wi = min(1000, det_steps_per_ep - 1)
            warmup = torch.optim.lr_scheduler.LinearLR(opt, start_factor=1e-3, total_iters=max(wi, 1))
        from util.collate_fn import DataPrefetcher
        prefetcher = DataPrefetcher(det_train, device)
        n_steps = det_steps_cap or det_steps_per_ep
        ep_start = time.perf_counter()
        for step in range(n_steps):
            batch = prefetcher.next()
            if batch is None:  # ローダ枯渇（engine.py 同様に範囲で終端）
                break
            images, targets = batch
            loss_dict = model(images, targets)
            l_det = sum(loss_dict.values())
            do_phase = (step % R == 0)
            l_phase = None
            if do_phase:
                _cid, gap, labels = next(phase_iter)
                gx = torch.from_numpy(gap).unsqueeze(0).to(device)
                ly = torch.from_numpy(labels).to(device)
                l_phase = model.phase_loss(gx, ly)
            loss = combined_loss(model, l_det, l_phase, args)
            opt.zero_grad()
            loss.backward()
            if args.smoke:  # 両枝が共有 neck に勾配を流したか確認
                g = model.c5_neck.weight.grad
                if g is not None and g.abs().sum() > 0:
                    grad_seen["phase" if do_phase else "det"] = True
            torch.nn.utils.clip_grad_norm_(model.parameters(), 0.1)
            opt.step()
            if warmup is not None and step < warmup.total_iters:
                warmup.step()
            if step % args.print_freq == 0:
                lp = f"{float(l_phase):.3f}" if l_phase is not None else "-"
                rate = (step + 1) / max(time.perf_counter() - ep_start, 1e-6)
                eta = (det_steps_per_ep - step) / max(rate, 1e-6) / 60
                print(f"[b1][ep{epoch} {step}/{det_steps_per_ep}] L={float(loss):.3f} "
                      f"L_det={float(l_det):.3f} L_phase={lp} {rate:.1f}it/s eta_ep={eta:.0f}m",
                      flush=True)
            if not math.isfinite(float(loss)):
                print("[b1] loss not finite, stop")
                sys.exit(1)
        sched.step()

        mAP, per_class = eval_detection(model, det_val, device, limit=20 if args.smoke else None)
        pacc, ppreds = eval_phase(model, val_clips, device)
        print(f"[b1][ep{epoch}] val mAP={mAP:.4f} phase_acc={pacc:.4f}", flush=True)
        if mAP > best["mAP"]:
            best = {"mAP": mAP, "phase_acc": pacc, "epoch": epoch,
                    "per_class_coco_map": per_class}
            torch.save({"model": model.state_dict(), "epoch": epoch,
                        "weighting": args.weighting, "seed": args.seed},
                       work / "best_b1.pth")
            (work / "phase_val_preds.json").write_text(json.dumps(ppreds))

    # work_dir に生結果＋両 eval_recipe（dict のみ・Δは本体後処理）を出力
    result = {
        "weighting": args.weighting, "seed": args.seed, "epochs": args.epochs, "R": R,
        "w_det": args.w_det, "w_phase": args.w_phase, "phase_lr": args.phase_lr,
        "best_epoch": best.get("epoch"), "mAP": best.get("mAP"),
        "phase_frame_acc": best.get("phase_acc"),
        "per_class_coco_map": best.get("per_class_coco_map", {}),
    }
    if args.weighting == "uncertainty":
        result["sigma2_d"] = float(torch.exp(model.log_var_d))
        result["sigma2_p"] = float(torch.exp(model.log_var_p))
    (work / "b1_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[b1] DONE best@ep{best.get('epoch')} mAP={best.get('mAP'):.4f} "
          f"phase_acc={best.get('phase_acc'):.4f} -> {work}")
    if args.smoke:
        ok = grad_seen["det"] and grad_seen["phase"]
        print(f"[b1][smoke] neck grad from det={grad_seen['det']} phase={grad_seen['phase']} "
              f"=> {'PASS' if ok else 'FAIL'}")
        sys.exit(0 if ok else 2)


def _cycle(items):
    while True:
        for it in items:
            yield it


def parse_args():
    p = argparse.ArgumentParser(description="B1 naive-MTL joint trainer (det + phase, shared C5 neck).")
    p.add_argument("--weighting", choices=["fixed", "uncertainty"], default="fixed")
    p.add_argument("--w-det", type=float, default=1.0)
    p.add_argument("--w-phase", type=float, default=1.0)
    p.add_argument("--epochs", type=int, default=12)         # 検出 epoch（S0-frozen′ と一致）
    p.add_argument("--phase-epochs-equiv", type=int, default=50)  # 工程の目標露出（S4′ と一致）
    p.add_argument("--step-ratio", type=int, default=0)      # 0=auto（両分母を同時に満たす R）
    p.add_argument("--lr", type=float, default=1e-4)         # 検出主 LR（c5_neck もこの群）
    p.add_argument("--phase-lr", type=float, default=5e-4)   # 工程ヘッド LR（S4′ と一致）
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--print-freq", type=int, default=200)
    p.add_argument("--smoke", action="store_true")
    return p.parse_args()


if __name__ == "__main__":
    main()
