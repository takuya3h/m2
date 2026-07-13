#!/usr/bin/env python
"""T1c 双方向 §4.6 パイロット（1-seed 先行）: det⇄phase 同時学習（frame 粒度・2-pass teacher-forced）。

①(camt-all: 可塑×広域CAでphase→det, Bipolar逆転) / ②(clsbias-PE: frozen×排他ゲート) を踏まえ、
**1つのモデルで det→phase と phase→det の両勾配を流す**最小 pilot。真の T1a は TeCNO 時系列だが、
pilot は frame 粒度に簡約（per-frame phase head）して「双方向結合の勾配基盤が両タスクを相互改善するか」を検証。

アーキ（surgery 不要・2-pass teacher-forced・循環回避）:
  warm-start = S0-frozen Relation-DETR seed42（camt 変種, phase_attn out_proj zero-init=恒等）。
  det→phase: forward hook で decoder 最終層 class_head[-1] の object-query 埋め込み R(B,Q,256)+logits(B,Q,15)
             を捕捉 → per-class score-gate で (B,3840) → PhaseHead(MLP) → 9工程 logits。
  phase→det: camt 注入（既存 set_phase_context((B,9))）。posterior は PhaseHead の online 出力。
  Pass1: set_phase_context(0) で model(images)（eval-path forward, grad 有）→ hook→R → PhaseHead → P_online → L_phase=CE。
  Pass2: set_phase_context(softmax(P_online).detach()) で model(images,targets) → L_det。
  L = L_det + λ·L_phase、backward 1回。shared backbone で双方向勾配。

対照（pilot）:
  --inject-online: pass2 で P_online 注入（phase→det on）。off なら zero-ctx（phase→det off）。
  --lambda-phase 0: phase 枝を切る（det-only）。>0: det→phase on。
  --trainable all: 検出器可塑（①で可塑性が結合を解くと確証）。film: 検出器凍結（det→phase off baseline）。
  det baseline は ① camt-all ctrl（zero-ctx, mAP 0.7110）を流用。phase baseline は --trainable film で本script。

実行（.venv-relation-detr, cwd 自動で RELDETR）:
  python scripts/train_t1c_bidir.py --seed 42 --smoke                 # 配線・恒等確認
  python scripts/train_t1c_bidir.py --seed 42 --epochs 6 --bidir      # pilot 本走（both on, 可塑）
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# train_t1b の scaffolding を再利用（import 時に os.chdir(RELDETR) 実行済＝本 script も RELDETR cwd 前提）。
sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_t1b as t1b  # noqa: E402  build_det_loader/build_model/eval_detection/ctx_for_targets/set_trainable/...

BODY = t1b.BODY
NUM_PHASES = t1b.NUM_PHASES          # 9
NUM_TOOLS = 15
EMBED_DIM = 256
JOINT_MANIFEST = BODY / "data/processed/joint_manifest"


# ----------------------------- phase ラベル -----------------------------
def load_frame_phase(split: str) -> dict:
    """joint_manifest/{split}.json → frame_id -> phase_label(int 0..8)。"""
    man = json.loads((JOINT_MANIFEST / f"{split}.json").read_text())
    out: dict[str, int] = {}
    for clip in man["clips"]:
        for fr in clip["frames"]:
            out[str(fr["frame"])] = int(fr["phase_label"])
    return out


def build_imgid_to_phase(coco, frame_phase: dict):
    """coco image_id -> phase_label(int)。欠落は -1（loss で無視）。件数を返す。"""
    imgid_to_phase, miss = {}, 0
    for image_id, info in coco.imgs.items():
        fid = Path(info["file_name"]).stem
        lbl = frame_phase.get(fid)
        if lbl is None:
            lbl = -1
            miss += 1
        imgid_to_phase[image_id] = int(lbl)
    return imgid_to_phase, miss


def phase_labels_for_targets(targets, imgid_to_phase, device):
    return torch.tensor([imgid_to_phase.get(int(t["image_id"]), -1) for t in targets],
                        dtype=torch.long, device=device)


# ----------------------------- region-token hook -----------------------------
class DecoderCapture:
    """decoder.class_head[-1] の forward hook。最終層 (region tokens, logits) を grad 保持で捕捉。

    extract_t1a_regiontoken.py と同機構だが detach しない（det→phase の勾配を流すため）。
    inputs[0]=(B,Q,256) object-query 埋め込み, output=(B,Q,15) per-query class logits。
    """

    def __init__(self):
        self.tokens = None
        self.logits = None

    def __call__(self, module, inputs, output):
        self.tokens = inputs[0]   # (B,Q,256) grad 有
        self.logits = output      # (B,Q,15)  grad 有

    def reset(self):
        self.tokens = self.logits = None


def region_batch(cap: DecoderCapture) -> torch.Tensor:
    """捕捉した (B,Q,256)/(B,Q,15) → クラス別 score-gate 256-d 連結 (B,3840)。grad 保持。

    scores=sigmoid(logits); 各クラス c: q*=argmax_q scores[b,q,c]; region[b,c]=scores[b,q*,c]·tokens[b,q*]。
    argmax は選択のみ（非微分）だが選択要素の値は微分可（max-pool 型）。
    """
    tokens, logits = cap.tokens, cap.logits          # (B,Q,256), (B,Q,15)
    B, Q, _ = tokens.shape
    scores = torch.sigmoid(logits.float())           # (B,Q,15)
    qstar = scores.argmax(dim=1)                     # (B,15) 各クラス最高スコアの query idx
    bidx = torch.arange(B, device=tokens.device).unsqueeze(1).expand(B, NUM_TOOLS)  # (B,15)
    cidx = torch.arange(NUM_TOOLS, device=tokens.device).unsqueeze(0).expand(B, NUM_TOOLS)  # (B,15)
    gate = scores[bidx, qstar, cidx].unsqueeze(-1)   # (B,15,1) score ゲート
    sel_tokens = tokens[bidx.reshape(-1), qstar.reshape(-1)].reshape(B, NUM_TOOLS, EMBED_DIM)  # (B,15,256)
    region = (gate * sel_tokens).reshape(B, NUM_TOOLS * EMBED_DIM)  # (B,3840)
    return region


class PhaseHead(nn.Module):
    """region token (3840) → 9 工程 logits（per-frame・時系列なし・pilot 簡約）。"""

    def __init__(self, in_dim=NUM_TOOLS * EMBED_DIM, hidden=256, num_phases=NUM_PHASES):
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(in_dim),
            nn.Linear(in_dim, hidden), nn.ReLU(inplace=True), nn.Dropout(0.1),
            nn.Linear(hidden, num_phases),
        )

    def forward(self, region):
        return self.net(region)


# ----------------------------- eval -----------------------------
@torch.no_grad()
def eval_phase(model, phase_head, cap, loader, imgid_to_phase, device, limit=None):
    """frame 粒度 phase 精度（online: region→PhaseHead→argmax）。zero-ctx forward で region 捕捉。"""
    model.eval()
    phase_head.eval()
    correct = total = 0
    for i, (images, targets) in enumerate(loader):
        if limit is not None and i >= limit:
            break
        images = [img.to(device) for img in images]
        y = phase_labels_for_targets(targets, imgid_to_phase, device)
        model.set_phase_context(torch.zeros(len(targets), NUM_PHASES, device=device))
        cap.reset()
        _ = model(images)
        if cap.tokens is None:
            continue
        logits = phase_head(region_batch(cap))       # (B,9)
        pred = logits.argmax(dim=1)
        valid = y >= 0
        correct += int((pred[valid] == y[valid]).sum())
        total += int(valid.sum())
    return (correct / total) if total else float("nan"), total


# ----------------------------- main -----------------------------
def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    import random
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    det_train = t1b.build_det_loader(train=True)
    det_val = t1b.build_det_loader(train=False)
    # phase→det 注入は camt 機構を使う（online posterior を set_phase_context で還流）。
    model = t1b.build_model(device, args.seed, t1b.MODEL_CFG_CAMT)
    t1b.register_classes(model, det_train)
    t1b.set_trainable(model, args.trainable)

    phase_head = PhaseHead().to(device)

    # region-token hook を最終層 class head に登録（Fail Loud: 形状検証）。
    head = model.transformer.decoder.class_head[-1]
    assert getattr(head, "in_features", None) == EMBED_DIM, f"class_head[-1] in={getattr(head,'in_features',None)}"
    assert getattr(head, "out_features", None) == NUM_TOOLS, f"class_head[-1] out={getattr(head,'out_features',None)}"
    cap = DecoderCapture()
    head.register_forward_hook(cap)

    # phase ラベル
    ip_tr, miss_tr = build_imgid_to_phase(det_train.dataset.coco, load_frame_phase("train"))
    ip_va, miss_va = build_imgid_to_phase(det_val.dataset.coco, load_frame_phase("val"))

    # v2 非対称: phase→det 注入に収束済 S4 事後（precomputed, ①で+0.61成立）を使う。
    # det→phase は依然 online phase head（zero-ctx clean region から予測）。online 低品質事後は注入しない。
    s4_ctx_tr = s4_ctx_va = None
    if args.phase2det_source == "s4":
        s4_ctx_tr, _ = t1b.build_imgid_to_ctx(det_train.dataset.coco, t1b.load_phase_ctx("train"))
        s4_ctx_va, _ = t1b.build_imgid_to_ctx(det_val.dataset.coco, t1b.load_phase_ctx("val"))

    # optimizer: 検出器 param（finetune_t1b の group）＋ phase_head。
    from optimizer import param_dict
    groups = param_dict.finetune_t1b(model, lr=args.lr, film_lr=args.film_lr)
    groups = groups + [{"params": phase_head.parameters(), "lr": args.phase_lr}]
    opt = torch.optim.AdamW(groups, lr=args.lr, weight_decay=1e-4, betas=(0.9, 0.999))
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=[max(args.epochs - 2, 1)], gamma=0.1)

    steps_per_ep = len(det_train)
    steps_cap = 6 if args.smoke else None
    if args.smoke:
        args.epochs = 1

    work = Path(os.environ.get("T1C_WORK_DIR", f"/tmp/t1c_bidir_seed{args.seed}"))
    work.mkdir(parents=True, exist_ok=True)
    n_det = sum(p.numel() for n, p in model.named_parameters() if p.requires_grad)
    n_ph = sum(p.numel() for p in phase_head.parameters())
    print(f"[t1c] seed={args.seed} inject={args.inject_online}/{args.phase2det_source} lambda_phase={args.lambda_phase} "
          f"trainable={args.trainable} steps/ep={steps_per_ep} det_trainable={n_det} phase_head={n_ph} "
          f"miss_phase(tr/va)={miss_tr}/{miss_va} work={work}", flush=True)

    # 恒等・健全ガード: warm-start det mAP（camt zero-init 恒等 → S0-frozen 水準）+ phase acc（fresh head ≈ chance）。
    init_map, init_per_class = t1b.eval_detection(model, det_val, {i: np.zeros(NUM_PHASES, np.float32)
                                                                   for i in det_val.dataset.coco.imgs},
                                                  device, zero_ctx=True,
                                                  limit=(8 if args.smoke else None))
    init_phase_acc, n_va = eval_phase(model, phase_head, cap, det_val, ip_va, device,
                                      limit=(8 if args.smoke else None))
    print(f"[t1c] warm-start init: det mAP={init_map:.4f} (band[0.65,0.78]) phase_acc={init_phase_acc:.4f} "
          f"(fresh head, val_n={n_va})", flush=True)
    if args.assert_init_map is not None and abs(init_map - args.assert_init_map) > args.assert_init_tol:
        print(f"[t1c] FATAL init mAP {init_map:.4f} != {args.assert_init_map} ±{args.assert_init_tol} → 恒等破れ/ckpt取違え")
        sys.exit(3)

    per_epoch = [{"epoch": -1, "det_mAP": init_map, "phase_acc": init_phase_acc,
                  "det_per_class_coco_map": init_per_class}]

    from util.collate_fn import DataPrefetcher
    for epoch in range(args.epochs):
        model.train()
        phase_head.train()
        t0 = time.time()
        prefetcher = DataPrefetcher(det_train, device)   # images+targets を device へ（train_t1b と同機構）
        n_steps = steps_cap or steps_per_ep
        for step in range(n_steps):
            batch = prefetcher.next()
            if batch is None:
                break
            images, targets = batch                      # 既に device 上
            y = phase_labels_for_targets(targets, ip_tr, device)

            # --- Pass1: eval-mode forward で clean region 捕捉 → PhaseHead → L_phase（det→phase） ---
            # RelationDETR.forward は train モードだと dn 生成で targets 必須＆dn/hybrid query が混入する。
            # eval モードなら targets 不要＆matching query のみ（extract_t1a と同条件）。grad は流れる。
            loss_phase = torch.zeros((), device=device)
            p_online = None
            if args.lambda_phase > 0 or args.inject_online:
                model.eval()
                phase_head.train()
                model.set_phase_context(torch.zeros(len(targets), NUM_PHASES, device=device))
                cap.reset()
                _ = model(images)                       # eval-path forward（targets 無, grad 有）
                region = region_batch(cap)              # (B,3840) grad 有
                ph_logits = phase_head(region)          # (B,9)
                p_online = F.softmax(ph_logits, dim=1)  # (B,9) 注入用 posterior
                valid = y >= 0
                if valid.any():
                    loss_phase = F.cross_entropy(ph_logits[valid], y[valid])
                model.train()                           # pass2 は train モード（dn/BN 更新）

            # --- Pass2: phase→det 注入 → L_det ---
            if args.inject_online:
                if args.phase2det_source == "s4":
                    ctx = t1b.ctx_for_targets(targets, s4_ctx_tr, device, zero_ctx=False)  # v2: 高品質 S4 事後
                elif p_online is not None:
                    ctx = p_online.detach()             # v1: online（teacher-forcing）
                else:
                    ctx = torch.zeros(len(targets), NUM_PHASES, device=device)
            else:
                ctx = torch.zeros(len(targets), NUM_PHASES, device=device)
            model.set_phase_context(ctx)
            loss_dict = model(images, targets)
            loss_det = sum(loss_dict.values())

            loss = loss_det + args.lambda_phase * loss_phase
            opt.zero_grad()
            loss.backward()
            if args.grad_clip > 0:
                torch.nn.utils.clip_grad_norm_(
                    [p for g in groups for p in g["params"]], args.grad_clip)
            opt.step()

            if step % 200 == 0:
                eta = (time.time() - t0) / max(step, 1) * (steps_per_ep - step) / 60
                print(f"[t1c][ep{epoch} {step}/{steps_per_ep}] L={float(loss):.3f} "
                      f"(det={float(loss_det):.3f} phase={float(loss_phase):.3f}) eta_ep={eta:.0f}m", flush=True)
            if not math.isfinite(float(loss)):
                print("[t1c] loss not finite, stop")
                sys.exit(4)
        sched.step()

        # det eval は phase→det 注入源に合わせる: v2=S4事後注入 / v1=online注入 / off=zero-ctx。
        if args.inject_online and args.phase2det_source == "s4":
            det_map, det_pc = t1b.eval_detection(model, det_val, s4_ctx_va, device, zero_ctx=False,
                                                 limit=(8 if args.smoke else None))
        elif args.inject_online:
            det_map, det_pc = eval_detection_online(model, phase_head, cap, det_val, device,
                                                    limit=(8 if args.smoke else None))
        else:
            det_map, det_pc = t1b.eval_detection(model, det_val, {i: np.zeros(NUM_PHASES, np.float32)
                                                                  for i in det_val.dataset.coco.imgs},
                                                 device, zero_ctx=True, limit=(8 if args.smoke else None))
        ph_acc, _ = eval_phase(model, phase_head, cap, det_val, ip_va, device,
                               limit=(8 if args.smoke else None))
        print(f"[t1c] ep{epoch} det mAP={det_map:.4f} phase_acc={ph_acc:.4f}", flush=True)
        per_epoch.append({"epoch": epoch, "det_mAP": det_map, "phase_acc": ph_acc,
                          "det_per_class_coco_map": det_pc})

    final = per_epoch[-1]
    result = {
        "seed": args.seed, "bidir_inject": args.inject_online, "phase2det_source": args.phase2det_source,
        "lambda_phase": args.lambda_phase, "trainable": args.trainable, "epochs": args.epochs,
        "init_det_mAP": init_map, "init_phase_acc": init_phase_acc,
        "init_det_per_class_coco_map": init_per_class,
        "final_epoch": final["epoch"], "final_det_mAP": final["det_mAP"],
        "final_phase_acc": final["phase_acc"], "final_det_per_class_coco_map": final["det_per_class_coco_map"],
        "per_epoch_eval": per_epoch,
    }
    (work / "t1c_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[t1c] DONE det mAP={final['det_mAP']:.4f} phase_acc={final['phase_acc']:.4f} "
          f"(init det={init_map:.4f} phase={init_phase_acc:.4f}) -> {work}", flush=True)


@torch.no_grad()
def eval_detection_online(model, phase_head, cap, loader, device, limit=None):
    """phase→det on の det 評価: 各 image で online posterior を注入して検出。COCO mAP+per_class。"""
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset
    model.eval(); phase_head.eval()
    coco = get_coco_api_from_dataset(loader.dataset)
    evaluator = CocoEvaluator(coco, ["bbox"])
    for i, (images, targets) in enumerate(loader):
        if limit is not None and i >= limit:
            break
        images = [img.to(device) for img in images]
        # pass1: zero-ctx で region → posterior
        model.set_phase_context(torch.zeros(len(targets), NUM_PHASES, device=device))
        cap.reset()
        _ = model(images)
        ctx = F.softmax(phase_head(region_batch(cap)), dim=1) if cap.tokens is not None \
            else torch.zeros(len(targets), NUM_PHASES, device=device)
        # pass2: 注入して検出
        model.set_phase_context(ctx)
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


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=6)
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--film-lr", type=float, default=5e-4)
    p.add_argument("--phase-lr", type=float, default=1e-3)
    p.add_argument("--lambda-phase", type=float, default=1.0, help="det→phase 損失重み。0 で det-only")
    p.add_argument("--inject-online", action="store_true", help="phase→det 注入 on（pass2）")
    p.add_argument("--phase2det-source", choices=["online", "s4"], default="online",
                   help="phase→det 注入源。online=phase head の online 事後（v1）/ s4=収束済S4 precomputed 事後（v2 非対称）")
    p.add_argument("--bidir", action="store_true", help="両方向 on の糖衣（--inject-online かつ lambda_phase>0）")
    p.add_argument("--trainable", choices=["film", "all"], default="all")
    p.add_argument("--grad-clip", type=float, default=0.1)
    p.add_argument("--assert-init-map", type=float, default=None)
    p.add_argument("--assert-init-tol", type=float, default=0.02)
    p.add_argument("--smoke", action="store_true")
    args = p.parse_args()
    if args.bidir:
        args.inject_online = True
        if args.lambda_phase <= 0:
            args.lambda_phase = 1.0
    return args


if __name__ == "__main__":
    main()
