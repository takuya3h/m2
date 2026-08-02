#!/usr/bin/env python
"""Hand-mask→Det トレーナー（L2 oracle_hand2det 4ch / L1a oracle_hti2det 5ch の機構検証）。

**本番学習ではなく合成マスクでの機構検証専用**。凍結検出器（s0_016/017/018 = warm-start 元）から
warm-start し、手 mask を C5 に **zero-init 1x1 conv の加算残差**として注入する（train_t1b.py の
FiLM 注入点＝C5 と同一スロット、機構は残差加算に限定）。実データの手 mask は待たず、ランダム
矩形/楕円などの **合成手 mask** で forward/backward と全ガードを検証する。

L2 と L1a は同一機構で、入力チャネルだけ切替える（機構を変えると交絡）:
  --hand-channels 4 : 手クラス4ch prior map のみ（Tier0 = 手 mask のみ = 安全・L2）
  --hand-channels 5 : ＋把持フラグ1ch（Tier1 = 手側属性 bool = 安全・L1a）
Tier2（接触 hand∩tool）は未実装、Tier3（tool mask/bbox/class）は禁止（model 側で強制・混入不可）。

学習対象（warm-start fine-tune の範囲）:
  --trainable film : 注入層(hand_prior.*)のみ学習（検出器凍結・最純粋な注入効果）
  --trainable all  : 注入層 + 検出器 fine-tune（容量大・絶対劣化を伴い early-stop 前提）

対照:
  --zero-ctx : 注入テンソルを 0 に固定（zero-init 恒等ガード / 配線検証の 0 対照）。

成果物（永続・実験規約と同一）: experiments/hand2det_dev/<run_name>/
  checkpoints/best_hand2det.pth / predictions/{split}_{inj|ctrl}_{ep-1,best}.json.gz
  logs/val_metrics_by_epoch.json / config.yaml / command.sh / git_commit.txt
  metrics.json / per_class_ap.json / hand2det_result.json / server.txt

実行（.venv-relation-detr, cwd=third_party/Relation-DETR）:
  source .venv-relation-detr/bin/activate && export CUDA_HOME=/usr/local/cuda-11.8
  python /abs/scripts/train_hand2det.py --seed 42 --hand-channels 4 --trainable film --epochs 1
  python /abs/scripts/train_hand2det.py --seed 42 --hand-channels 5 --trainable all  --epochs 1
  python /abs/scripts/train_hand2det.py --seed 42 --epochs 0                # init 恒等検証用
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

BODY = Path(os.environ.get("EGO_BODY", Path(__file__).resolve().parents[1]))
RELDETR = BODY / "third_party" / "Relation-DETR"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(RELDETR))

# 手 mask のチャネル数は config が env で読む（4ch=L2 / 5ch=L1a を機構不変で切替）。
# build_model（Config 読込）より前に必ず設定する。CLI で上書きするので既定は入れ得るが、
# main() 内で args.hand_channels を再設定してから build_model する。
os.environ.setdefault("HAND2DET_HAND_CHANNELS", "4")

import run_artifacts as ra  # noqa: E402  (sys.path 追加後に import する必要がある)
# train_t1b の phase 非依存ヘルパ（loader / warm-start build / class 登録）を再利用する。
from train_t1b import (  # noqa: E402
    build_det_loader,
    build_model,
    detector_ckpt,
    register_classes,
)

MODEL_CFG_HAND2DET = "configs/relation_detr/relation_detr_resnet50_egosurgery_hand2det.py"

# 合成手 mask のキャンバス解像度（module 側で C5 stride 1/32 へ downsample される）。
SYNTH_HW = (128, 128)


def synth_hand_masks(targets, hand_channels: int, device, zero: bool = False) -> torch.Tensor:
    """**合成**手 mask (B, C_hand, Hs, Ws) を生成する（実 GT 手 mask は使わない）。

    ch0..3: ランダム矩形/楕円の手クラス prior。ch4（5ch 時）: per-hand 把持フラグ（0/1 定数）。
    image_id をシードに決定論生成（inj run の再現性・--epochs 0 の同一性を担保）。
    ``zero=True`` は 0 テンソル（zero-init 恒等ガード / 配線検証の 0 対照）。

    ★ tool 由来情報は一切生成・混入しない（手側チャネルのみ）。model 側 Tier3 GUARD と併せ二重保証。
    """
    B = len(targets)
    Hs, Ws = SYNTH_HW
    if zero:
        return torch.zeros(B, hand_channels, Hs, Ws, dtype=torch.float32, device=device)
    arr = np.zeros((B, hand_channels, Hs, Ws), dtype=np.float32)
    yy, xx = np.mgrid[0:Hs, 0:Ws]
    for b, t in enumerate(targets):
        seed = int(t["image_id"]) & 0x7FFFFFFF
        r = np.random.default_rng(seed)
        for c in range(4):  # 4 手クラス prior チャネル
            cy = int(r.integers(Hs // 4, 3 * Hs // 4))
            cx = int(r.integers(Ws // 4, 3 * Ws // 4))
            if r.integers(0, 2) == 0:  # 矩形
                h2 = int(r.integers(6, Hs // 3))
                w2 = int(r.integers(6, Ws // 3))
                arr[b, c, max(0, cy - h2):cy + h2, max(0, cx - w2):cx + w2] = 1.0
            else:  # 楕円
                ry = int(r.integers(6, Hs // 3))
                rx = int(r.integers(6, Ws // 3))
                arr[b, c][((yy - cy) / ry) ** 2 + ((xx - cx) / rx) ** 2 <= 1.0] = 1.0
        if hand_channels == 5:
            arr[b, 4, :, :] = float(r.integers(0, 2))  # per-hand 把持フラグ（bool broadcast）
    return torch.from_numpy(arr).to(device)


# ---------------------------------------------------------------------------
# 実データ経路（L2）: raw02（正本・タスク1で tool 整合性・完全性ともに勝利）の手 bbox を
# 4ch prior map に**矩形ラスタライズ**して注入する。手 bbox のみ＝手側局在信号（tool 非リーク）。
# 座標: val loader は transforms=None＝元解像度(1920×1080)なので、元画像正規化座標で描けば
# module 側の area-interp で C5 空間に整合する（raw02 画像は全て同寸・padding 無し）。
# ★本実験はまだ回さない（恒等/配線ガードの実データ再実行のみ）。5ch(L1a/HTI)はリークのため非対応。
# ---------------------------------------------------------------------------
RAW02_DIR = str(BODY / "data/raw/OpenSurgery_Dataset/02_hand/json_per_video")
IMG_W, IMG_H = 1920, 1080
RAW02_CAT_TO_CH = {1: 0, 2: 1, 3: 2, 4: 3}  # raw02 手カテゴリ(1-4) → prior チャネル(0-3)
_RAW02_INDEX = None      # {stem: [(ch, [x,y,w,h]), ...]}
_IMGID2STEM = None       # {image_id: stem}
_HAND_SOURCE = "synth"   # "synth"(既定) / "real"(raw02)


def set_hand_source(src: str) -> None:
    global _HAND_SOURCE
    _HAND_SOURCE = src


def _stem(fn: str) -> str:
    return os.path.splitext(os.path.basename(fn))[0]


def _load_raw02_index():
    global _RAW02_INDEX
    if _RAW02_INDEX is not None:
        return _RAW02_INDEX
    import glob as _glob
    idx: dict[str, list] = {}
    for f in _glob.glob(f"{RAW02_DIR}/*/*.json"):
        d = json.load(open(f))
        m = {im["id"]: _stem(im["file_name"]) for im in d["images"]}
        for a in d["annotations"]:
            ch = RAW02_CAT_TO_CH.get(a["category_id"])
            if ch is None:
                continue
            idx.setdefault(m[a["image_id"]], []).append((ch, a["bbox"]))
    _RAW02_INDEX = idx
    return idx


def _load_imgid2stem():
    """検出 image_id → frame stem（ANN_DIR の COCO から。targets の image_id と整合）。"""
    global _IMGID2STEM
    if _IMGID2STEM is not None:
        return _IMGID2STEM
    ann_dir = os.environ.get("EGO_ANN_DIR", str(BODY / "data/annotations/egosurgery_tool"))
    m: dict[int, str] = {}
    for split in ("train", "val"):
        p = f"{ann_dir}/instances_{split}.json"
        if os.path.exists(p):
            d = json.load(open(p))
            for im in d["images"]:
                m[int(im["id"])] = _stem(im["file_name"])
    _IMGID2STEM = m
    return m


def real_hand_masks(targets, hand_channels: int, device, zero: bool = False) -> torch.Tensor:
    """raw02 手 bbox を 4ch prior map (B,4,Hs,Ws) に矩形ラスタライズ（元画像正規化座標）。

    手 bbox のみを描く＝tool 情報は一切通さない（Tier3 境界を実データ経路でも維持）。
    raw02 に手が無いフレーム（例 03_3 や official-split の非交差分）は全ゼロ prior（手不在）。
    """
    B = len(targets)
    Hs, Ws = SYNTH_HW
    if zero or hand_channels != 4:
        # zero 対照。hand_channels!=4 は L2(4ch) 専用のため 0（5ch=L1a はリークで非対応）。
        return torch.zeros(B, 4, Hs, Ws, dtype=torch.float32, device=device)
    idx = _load_raw02_index()
    id2stem = _load_imgid2stem()
    arr = np.zeros((B, 4, Hs, Ws), dtype=np.float32)
    for b, t in enumerate(targets):
        stem = id2stem.get(int(t["image_id"]))
        for ch, (x, y, w, h) in idx.get(stem, []):
            x0 = int(max(0, min(Ws, round(x / IMG_W * Ws))))
            x1 = int(max(0, min(Ws, round((x + w) / IMG_W * Ws))))
            y0 = int(max(0, min(Hs, round(y / IMG_H * Hs))))
            y1 = int(max(0, min(Hs, round((y + h) / IMG_H * Hs))))
            arr[b, ch, y0:max(y0 + 1, y1), x0:max(x0 + 1, x1)] = 1.0
    return torch.from_numpy(arr).to(device)


def hand_prior_tensor(targets, hand_channels: int, device, zero: bool = False) -> torch.Tensor:
    """注入 prior の生成をソースで切替（synth=合成 / real=raw02 手 bbox）。呼出側は本関数のみ使う。"""
    if _HAND_SOURCE == "real":
        return real_hand_masks(targets, hand_channels, device, zero=zero)
    return synth_hand_masks(targets, hand_channels, device, zero=zero)


def set_trainable(model, mode: str) -> None:
    """warm-start fine-tune の範囲。film=注入層(hand_prior.*)のみ学習 / all=全 fine-tune。

    注入層は zero-init の新規 module（base 検出器に ``hand_prior`` を含む param は無い）ので
    ``hand_prior`` で一括選択して安全。all は config の freeze_indices(backbone) 以外を学習。
    """
    if mode == "film":
        for name, p in model.named_parameters():
            p.requires_grad_("hand_prior" in name)
    # mode == "all" は既定 requires_grad（backbone 凍結・残り学習）。


@torch.no_grad()
def eval_detection(model, loader, hand_channels, device, zero_ctx, limit=None,
                   collect_predictions=False):
    """val 検出評価（train_t1b.eval_detection の hand-mask 版）。

    合成手 mask を set_hand_prior でセットして forward。eval recipe（score_thr 0.0/NMS 無/
    top-k=300）は config の postprocessor 準拠で不変。
    """
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset
    model.eval()
    coco = get_coco_api_from_dataset(loader.dataset)
    evaluator = CocoEvaluator(coco, ["bbox"])
    for i, (images, targets) in enumerate(loader):
        if limit is not None and i >= limit:
            break
        images = [img.to(device) for img in images]
        model.set_hand_prior(hand_prior_tensor(targets, hand_channels, device, zero=zero_ctx))
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
    if not collect_predictions:
        return float(bbox.stats[0]), per_class
    preds = {
        "results": evaluator.predictions["bbox"],
        "image_ids": sorted({int(i) for i in evaluator.img_ids}),
    }
    return float(bbox.stats[0]), per_class, preds


def main():
    args = parse_args()
    # L1a(5ch/HTI 把持フラグ)は既定で拒否。HTI は GT 術具 bbox の決定論的関数=リーク
    # (EgoSurgery-HTS arXiv:2503.18755)。L2(4ch・手 mask のみ=手 bbox 由来で術具非リーク)で進める。
    if args.hand_channels == 5 and not args.allow_leaky_hti:
        raise SystemExit(
            "[hand2det] 5ch(L1a/HTI 把持フラグ)は無効化されています: HTI は GT 術具 bbox の"
            "決定論的関数=リーク(arXiv:2503.18755)。4ch(L2)で実行してください。"
            "機構検証の再現目的でのみ --allow-leaky-hti を付けて許可できます。")
    set_hand_source(args.hand_source)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    # 手 mask チャネル数を config が読む env に確定させてから build_model する。
    os.environ["HAND2DET_HAND_CHANNELS"] = str(args.hand_channels)

    det_train = build_det_loader(train=True)
    det_val = build_det_loader(train=False)
    model = build_model(device, args.seed, MODEL_CFG_HAND2DET)
    register_classes(model, det_train)
    set_trainable(model, args.trainable)

    from optimizer import param_dict
    groups = param_dict.finetune_hand2det(model, lr=args.lr, inject_lr=args.inject_lr)
    opt = torch.optim.AdamW(groups, lr=args.lr, weight_decay=1e-4, betas=(0.9, 0.999))
    sched = torch.optim.lr_scheduler.MultiStepLR(opt, milestones=[max(args.epochs - 2, 1)], gamma=0.1)

    det_steps_per_ep = len(det_train)
    if args.smoke:
        args.epochs = max(args.epochs, 1)
        det_steps_cap = 6
    else:
        det_steps_cap = None

    variant = "ctrl" if args.zero_ctx else "inj"
    run_name = (args.run_name or os.environ.get("HAND2DET_RUN_NAME")
                or f"hand2det_{args.hand_channels}ch_{args.trainable}_{variant}_seed{args.seed}")
    # 既定の保存先は experiments/hand2det_dev/<run_name>（別タスクの analysis 領域には書かない）。
    default_work = str(BODY / "experiments" / "hand2det_dev" / run_name)
    work = ra.resolve_run_dir(run_name, work_dir=os.environ.get("HAND2DET_WORK_DIR", default_work))
    ra.ensure_layout(work)
    save_preds = not args.no_save_predictions
    compress_preds = not args.predictions_no_gzip
    n_inject = sum(p.numel() for n, p in model.named_parameters()
                   if p.requires_grad and "hand_prior" in n)
    n_train = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"[hand2det] seed={args.seed} hand_ch={args.hand_channels} trainable={args.trainable} "
          f"zero_ctx={args.zero_ctx} det_steps/ep={det_steps_per_ep} inject_params={n_inject} "
          f"total_trainable={n_train} work={work}", flush=True)
    ra.write_evidence(work, config={
        "run_name": run_name, "variant": variant, "seed": args.seed,
        "hand_channels": args.hand_channels, "tier": ("Tier0/L2" if args.hand_channels == 4
                                                      else "Tier1/L1a"),
        "trainable": args.trainable, "zero_ctx": bool(args.zero_ctx), "epochs": args.epochs,
        "lr": args.lr, "inject_lr": args.inject_lr, "model_cfg": MODEL_CFG_HAND2DET,
        "smoke": bool(args.smoke), "synth_mask": True, "synth_hw": list(SYNTH_HW),
        "warm_start_ckpt": str(detector_ckpt(args.seed)),
        "injection": "C5 zero-init 1x1 conv 残差（RelationDETRHandPrior.hand_prior）",
        "leak_boundary": "Tier0/1 のみ（手 mask ＋把持フラグ）。Tier2/3(接触・tool) 禁止・混入不可",
        "eval": {"split": "val", "topk": ra.EVAL_TOPK,
                 "note": "eval recipe = score_thr 0.0 / NMS 無 / top-k 300（config 準拠・不変）"},
    })

    # warm-start 健全性: 学習前 mAP（zero-init 恒等 → S0-frozen 水準のはず）
    init_map, init_per_class, init_preds = eval_detection(
        model, det_val, args.hand_channels, device, args.zero_ctx,
        limit=20 if args.smoke else None, collect_predictions=True)
    init_pred_path = None
    if save_preds:
        init_pred_path = ra.save_predictions(
            work, init_preds["results"], split="val", tag=variant, epoch=-1,
            compress=compress_preds)
        ra.save_eval_meta(work, {
            "split": "val", "ann_file": f"{os.environ.get('EGO_ANN_DIR', str(BODY / 'data/annotations/egosurgery_tool'))}/instances_val.json",
            "image_ids": init_preds["image_ids"], "topk": ra.EVAL_TOPK,
            "select_box_nums_for_evaluation": 300, "score_thr": 0.0,
            "limit": 20 if args.smoke else None,
        })
    print(f"[hand2det] warm-start init mAP={init_map:.4f} (zero-init 恒等 → S0-frozen 水準なら OK)",
          flush=True)
    if args.assert_init_map is not None and abs(init_map - args.assert_init_map) > args.assert_init_tol:
        print(f"[hand2det][PREFLIGHT-FAIL] init mAP={init_map:.4f} != "
              f"{args.assert_init_map}±{args.assert_init_tol} → warm-start/zero-init 恒等が壊れている。"
              f"中断（設定ドリフト・捏造防止）。", flush=True)
        sys.exit(3)

    inject_named = [(n, p) for n, p in model.named_parameters() if "hand_prior" in n]
    inject_grad_seen = False
    best = {"mAP": init_map, "epoch": -1, "per_class_coco_map": {}}
    per_epoch = [{"epoch": -1, "mAP": init_map, "per_class_coco_map": init_per_class}]
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
            model.set_hand_prior(hand_prior_tensor(targets, args.hand_channels, device, zero=args.zero_ctx))
            loss_dict = model(images, targets)
            loss = sum(loss_dict.values())
            opt.zero_grad()
            loss.backward()
            if not inject_grad_seen and any(
                    p.grad is not None and p.grad.abs().sum() > 0 for _, p in inject_named):
                inject_grad_seen = True
            torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], 0.1)
            opt.step()
            if step % args.print_freq == 0:
                rate = (step + 1) / max(time.perf_counter() - ep_start, 1e-6)
                eta = (det_steps_per_ep - step) / max(rate, 1e-6) / 60
                print(f"[hand2det][ep{epoch} {step}/{det_steps_per_ep}] L={float(loss):.3f} "
                      f"{rate:.1f}it/s eta_ep={eta:.0f}m", flush=True)
            if not math.isfinite(float(loss)):
                print("[hand2det] loss not finite, stop")
                sys.exit(1)
        sched.step()

        mAP, per_class, preds = eval_detection(
            model, det_val, args.hand_channels, device, args.zero_ctx,
            limit=20 if args.smoke else None, collect_predictions=True)
        print(f"[hand2det][ep{epoch}] val mAP={mAP:.4f}", flush=True)
        per_epoch.append({"epoch": epoch, "mAP": mAP, "per_class_coco_map": per_class})
        if save_preds and args.save_predictions_all:
            ra.save_predictions(work, preds["results"], split="val", tag=variant, epoch=epoch,
                                compress=compress_preds)
        if mAP > best["mAP"]:
            best = {"mAP": mAP, "epoch": epoch, "per_class_coco_map": per_class}
            torch.save({"model": model.state_dict(), "epoch": epoch, "seed": args.seed},
                       ra.checkpoints_dir(work) / "best_hand2det.pth")
            if save_preds:
                ra.save_predictions(work, preds["results"], split="val", tag=variant, best=True,
                                    compress=compress_preds)

    best_is_init = best["epoch"] == -1
    if save_preds and best_is_init:
        ra.save_predictions(work, init_preds["results"], split="val", tag=variant, best=True,
                            compress=compress_preds)

    final_eval = per_epoch[-1]
    result = {
        "seed": args.seed, "hand_channels": args.hand_channels, "trainable": args.trainable,
        "zero_ctx": args.zero_ctx, "epochs": args.epochs, "lr": args.lr, "inject_lr": args.inject_lr,
        "init_mAP": init_map, "best_epoch": best["epoch"], "mAP": best["mAP"],
        "per_class_coco_map": best.get("per_class_coco_map", {}),
        "init_per_class_coco_map": init_per_class,
        "final_epoch": final_eval["epoch"], "final_mAP": final_eval["mAP"],
        "final_per_class_coco_map": final_eval["per_class_coco_map"],
        "per_epoch_eval": per_epoch, "inject_grad_seen": inject_grad_seen,
        "best_is_init": best_is_init, "run_dir": str(work),
        "note": "合成手 mask による機構検証（本番学習ではない）",
    }
    (work / "hand2det_result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))

    epoch_log = {
        "run_name": run_name, "variant": variant, "split": "val",
        "seed": args.seed, "hand_channels": args.hand_channels, "trainable": args.trainable,
        "zero_ctx": bool(args.zero_ctx), "epochs": args.epochs,
        "init": {"epoch": -1, "mAP": init_map, "per_class_coco_map": init_per_class},
        "init_predictions_sha256": (
            ra.predictions_sha256(init_pred_path) if init_pred_path else None),
        "init_predictions_file": (init_pred_path.name if init_pred_path else None),
        "best_epoch": best["epoch"], "best_mAP": best["mAP"], "best_is_init": best_is_init,
        "best_checkpoint": (None if best_is_init
                            else str(ra.checkpoints_dir(work) / "best_hand2det.pth")),
        "final_epoch": final_eval["epoch"], "final_mAP": final_eval["mAP"],
        "epochs_eval": per_epoch,
    }
    ra.save_epoch_log(work, epoch_log)
    ra.write_metrics(work, {
        "mAP": best["mAP"], "init_mAP": init_map, "epoch": best["epoch"],
        "final_mAP": final_eval["mAP"], "final_epoch": final_eval["epoch"],
        "delta_detection": best["mAP"] - init_map, "best_is_init": best_is_init,
        "inject_grad_seen": inject_grad_seen, "artifacts": ra.artifact_paths(work),
    })
    ra.write_per_class_ap(work, best.get("per_class_coco_map", {}))
    print(f"[hand2det] DONE best@ep{best['epoch']} mAP={best['mAP']:.4f} (init {init_map:.4f}) "
          f"inject_grad={inject_grad_seen} -> {work}")
    if args.smoke:
        ok = inject_grad_seen and (init_map > 0.5)
        print(f"[hand2det][smoke] inject_grad={inject_grad_seen} init_mAP={init_map:.4f} "
              f"=> {'PASS' if ok else 'FAIL'}")
        sys.exit(0 if ok else 2)


def parse_args():
    p = argparse.ArgumentParser(description="Hand-mask->Det trainer (合成マスク機構検証).")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--hand-channels", type=int, choices=[4, 5], default=4,
                   help="4=L2(手 mask のみ・Tier0) / 5=L1a(＋把持フラグ・Tier1・既定無効)")
    p.add_argument("--hand-source", choices=["synth", "real"], default="synth",
                   help="注入 prior の生成源: synth(合成・既定) / real(raw02 手 bbox・L2 実データ配線)")
    p.add_argument("--allow-leaky-hti", action="store_true",
                   help="5ch(L1a/HTI 把持フラグ)を明示許可（機構検証の再現のみ）。"
                        "HTI は GT 術具 bbox の決定論的関数=リーク(EgoSurgery-HTS arXiv:2503.18755)のため本実験では使用禁止。")
    p.add_argument("--lr", type=float, default=1e-4)
    p.add_argument("--inject-lr", type=float, default=5e-4)
    p.add_argument("--trainable", choices=["film", "all"], default="film",
                   help="film=注入層(hand_prior)のみ学習 / all=注入層+検出器 fine-tune")
    p.add_argument("--zero-ctx", action="store_true",
                   help="注入テンソルを 0 に固定（zero-init 恒等ガード / 配線検証の 0 対照）")
    p.add_argument("--run-name", default=None,
                   help="保存先 experiments/hand2det_dev/<run_name>/。省略時は自動命名")
    p.add_argument("--no-save-predictions", action="store_true")
    p.add_argument("--save-predictions-all", action="store_true")
    p.add_argument("--predictions-no-gzip", action="store_true")
    p.add_argument("--print-freq", type=int, default=200)
    p.add_argument("--smoke", action="store_true")
    p.add_argument("--assert-init-map", type=float, default=None,
                   help="warm-start init mAP がこの値±tol から外れたら中断（恒等性・ドリフト検査）")
    p.add_argument("--assert-init-tol", type=float, default=0.02)
    return p.parse_args()


if __name__ == "__main__":
    main()
