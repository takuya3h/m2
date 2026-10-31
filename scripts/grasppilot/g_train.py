"""把持塔 G の学習（非公式 T-2026-11-01-grasp-pilot-g、Task C-3・C-4）。本体の .venv（mmdet 3.3.0・mmcv 2.1.0）を変えずに使う。

構造: mmdet の Mask2Former（R50、COCO instance、一本目と同じ重みのファイル。sha256 を照合）。頭のクラス数 38。
入力: 短辺 800（長辺 1333 まで、双線形）、学習は左右反転 0.5、batch 2。LSJ の 1024 への詰め物（batch_augments）は外す（一本目の計測と同じ）。
処方: mmdet の設定の optim_wrapper のまま（AdamW lr 1e-4・wd 0.05、backbone ×0.1、埋め込みと norm の減衰 0、勾配の L2 の切り 0.01）。
収束規則: epoch ごとに val の 38 クラスの mask mAP（pycocotools の segm、元の解像度）を測り、
    `stage1_ptower_r3.plateau_action`（塔の実装と同じ判定。改善 = 最良の値を厳密に上回る）で 4 epoch 停滞なら学習率 × 0.1、
    再び 4 epoch 停滞で打ち切り、上限 36。最良の epoch の重みを使う。把持関係 5 クラスの mask mAP（同じ評価のクラス別 AP の平均）も記録する。

    .venv/bin/python scripts/grasppilot/g_train.py --run-dir <experiments/phase1/grasppilot2_G_...> --ckpt-dir <S/g/ckpt/...>
        --ann-dir <S/g/ann> --videos all|H1|H2 [--smoke] [--amp none|fp16]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
from PIL import Image

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
sys.path.insert(0, str(PROJ / "src"))
from grasppilot import g_bench as B  # noqa: E402
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-01-grasp-pilot-g"
HALVES = {"H1": ["01", "06", "11", "12", "15"], "H2": ["02", "03", "08", "13", "14"]}
WEIGHT_SHA256 = "41b088b62838c986"     # 一本目の audit E-1 の値の先頭（ファイル名の 41b088b6 とも一致）
SHORT, LONG = 800, 1333
GRASP5 = [1, 2, 3, 4, 5]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def resize_shape(h, w):
    r = min(SHORT / min(h, w), LONG / max(h, w))
    return int(round(h * r)), int(round(w * r)), r


class G38(torch.utils.data.Dataset):
    """38 クラスの注釈の画像とインスタンス。学習は左右反転 0.5、マスクは最近傍で縮める。"""

    def __init__(self, coco, train, seed=42):
        self.images = coco["images"]
        self.train = train
        self.by = {}
        for a in coco["annotations"]:
            self.by.setdefault(a["image_id"], []).append(a)
        self.seed = seed

    def __len__(self):
        return len(self.images)

    def __getitem__(self, i):
        from grasppilot.grasp_signals import decode
        im = self.images[i]
        h, w = im["height"], im["width"]
        nh, nw, r = resize_shape(h, w)
        img = Image.open(PROJ / im["file_name"]).convert("RGB").resize((nw, nh), Image.BILINEAR)
        arr = np.asarray(img)
        out = {"image_id": im["id"], "stem": im["stem"], "ori": (h, w), "size": (nh, nw), "scale": r}
        if not self.train:
            return arr, out, None
        flip = bool(torch.rand(1).item() < 0.5)
        masks, labels = [], []
        for a in self.by.get(im["id"], []):
            m = Image.fromarray(decode(a["segmentation"], h, w).astype(np.uint8)).resize((nw, nh), Image.NEAREST)
            m = np.asarray(m)
            if m.any():
                masks.append(m)
                labels.append(a["category_id"] - 1)
        if flip:
            arr = arr[:, ::-1].copy()
            masks = [m[:, ::-1].copy() for m in masks]
        masks = np.stack(masks) if masks else np.zeros((0, nh, nw), np.uint8)
        return arr, out, (masks, np.array(labels, np.int64))


def collate(batch):
    return batch


def to_inputs(model, batch, training):
    from mmdet.structures import DetDataSample
    from mmdet.structures.mask import BitmapMasks
    from mmengine.structures import InstanceData
    tens, samples = [], []
    for arr, meta, tgt in batch:
        tens.append(torch.from_numpy(np.ascontiguousarray(arr)).permute(2, 0, 1).contiguous())
        nh, nw = meta["size"]
        oh, ow = meta["ori"]
        ds = DetDataSample(metainfo={"img_shape": (nh, nw), "ori_shape": (oh, ow) if not training else (nh, nw),
                                     "scale_factor": (meta["scale"], meta["scale"]), "img_id": meta["image_id"]})
        if tgt is not None:
            m, c = tgt
            gi = InstanceData()
            gi.labels = torch.from_numpy(c)
            gi.masks = BitmapMasks(m, nh, nw)
            boxes = []
            for mm in m:
                yy, xx = np.nonzero(mm)
                boxes.append([xx.min(), yy.min(), xx.max() + 1, yy.max() + 1])
            gi.bboxes = torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4)
            ds.gt_instances = gi
        samples.append(ds)
    data = model.data_preprocessor({"inputs": tens, "data_samples": samples}, training=training)
    return data["inputs"], data["data_samples"]


@torch.no_grad()
def evaluate(model, loader, gt_path, limit=None, score_min=0.0):
    """val の mask mAP（38 クラス）とクラス別 AP、把持関係 5 クラスの平均。元の解像度の RLE で pycocotools の segm 評価。"""
    from pycocotools import mask as mask_utils
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import (
        COCOeval as CocoEvaluator,  # 別名（semgrep の組み込み関数の誤検知を避ける）
    )
    model.eval()
    results, ids, n_pred = [], [], 0
    t0 = time.monotonic()
    for k, batch in enumerate(loader):
        if limit is not None and k >= limit:
            break
        inputs, samples = to_inputs(model, batch, training=False)
        preds = model.predict(inputs, samples, rescale=True)
        for p, (_, meta, _) in zip(preds, batch):
            ids.append(meta["image_id"])
            inst = p.pred_instances
            keep = inst.scores >= score_min
            masks = inst.masks[keep].cpu().numpy().astype(np.uint8)
            scores, labels = inst.scores[keep].cpu().numpy(), inst.labels[keep].cpu().numpy()
            if len(masks):
                rles = mask_utils.encode(np.asfortranarray(masks.transpose(1, 2, 0)))
                for rle, s, c in zip(rles, scores, labels):
                    rle["counts"] = rle["counts"].decode()
                    results.append({"image_id": meta["image_id"], "category_id": int(c) + 1, "segmentation": rle,
                                    "score": float(s)})
            n_pred += len(masks)
    infer_s = time.monotonic() - t0
    gt = COCO(str(gt_path))
    if not results:
        return {"segm_mAP": 0.0, "grasp5_mAP": 0.0, "per_class_ap": {}, "n_images": len(ids), "n_pred": 0}
    dt = gt.loadRes(results)
    ev = CocoEvaluator(gt, dt, "segm")
    ev.params.imgIds = ids
    ev.evaluate()
    ev.accumulate()
    ev.summarize()
    prec = ev.eval["precision"]          # [T, R, K, A, M]
    per = {}
    for k, cid in enumerate(ev.params.catIds):
        p = prec[:, :, k, 0, -1]
        per[gt.cats[cid]["name"]] = float(np.mean(p[p > -1])) if (p > -1).any() else None
    names = [gt.cats[c]["name"] for c in GRASP5]
    g5 = [per[n] for n in names if per[n] is not None]
    return {"segm_mAP": float(ev.stats[0]), "segm_mAP50": float(ev.stats[1]), "grasp5_mAP": float(np.mean(g5)),
            "per_class_ap": per, "n_images": len(ids), "n_pred": n_pred, "infer_seconds": infer_s,
            "eval_seconds": time.monotonic() - t0 - infer_s}


def git(*args):
    return subprocess.run(["git", *args], cwd=PROJ, capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--ann-dir", required=True)
    ap.add_argument("--videos", choices=("all", "H1", "H2"), required=True)
    ap.add_argument("--max-epochs", type=int, default=36)
    ap.add_argument("--patience", type=int, default=4)
    ap.add_argument("--lr-decay", type=float, default=0.1)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--amp", choices=("none", "fp16"), default="none")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--smoke", action="store_true", help="数歩と val の数枚で通るかだけ見る")
    ap.add_argument("--smoke-steps", type=int, default=20)
    ap.add_argument("--smoke-val", type=int, default=10)
    a = ap.parse_args()

    run, ckpt = Path(a.run_dir), Path(a.ckpt_dir)
    (run / "logs").mkdir(parents=True, exist_ok=True)
    ckpt.mkdir(parents=True, exist_ok=True)
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    from mmengine.optim import build_optim_wrapper
    from stage1_ptower_r3 import plateau_action

    from egosurgery.utils import tracking

    ann = Path(a.ann_dir)
    tr = json.loads((ann / "g38_train.json").read_text())
    if a.videos != "all":
        keep = set(HALVES[a.videos])
        tr["images"] = [im for im in tr["images"] if im["video"] in keep]
        ids = {im["id"] for im in tr["images"]}
        tr["annotations"] = [x for x in tr["annotations"] if x["image_id"] in ids]
    va_path = ann / "g38_val.json"
    va = json.loads(va_path.read_text())
    train_videos = C.assert_no_test([im["stem"] for im in tr["images"]], "G train")
    val_videos = C.assert_no_test([im["stem"] for im in va["images"]], "G val")

    model, cfg = B.mmdet_model(num_classes=38)
    wcheck = B.verify_weight(B.MMDET_W, WEIGHT_SHA256)
    if not wcheck["ok"]:
        raise RuntimeError(f"COCO の重みの要約値が違う: {wcheck}")
    st = torch.load(B.MMDET_W, map_location="cpu")["state_dict"]
    own = model.state_dict()
    keepw = {k: v for k, v in st.items() if k in own and own[k].shape == v.shape}
    skipped = sorted(k for k in st if k in own and own[k].shape != st[k].shape)
    absent = sorted(k for k in st if k not in own)
    missing, _ = model.load_state_dict(keepw, strict=False)
    load_report = {"checkpoint": str(B.MMDET_W), "sha256": wcheck["sha256"], "n_checkpoint": len(st), "loaded": len(keepw),
                   "skipped_shape": skipped, "absent_in_model": absent, "model_params_not_loaded": sorted(missing)}

    if a.amp == "fp16":
        cfg.optim_wrapper.type = "AmpOptimWrapper"
        cfg.optim_wrapper.loss_scale = "dynamic"
    optim = build_optim_wrapper(model, cfg.optim_wrapper)

    g = torch.Generator()
    g.manual_seed(a.seed)
    train_loader = torch.utils.data.DataLoader(G38(tr, True), batch_size=2, shuffle=True, num_workers=a.workers,
                                               collate_fn=collate, generator=g, persistent_workers=True,
                                               pin_memory=False, drop_last=True)  # nosemgrep
    val_loader = torch.utils.data.DataLoader(G38(va, False), batch_size=2, shuffle=False, num_workers=a.workers,
                                             collate_fn=collate, pin_memory=False)  # nosemgrep
    name = run.name
    config = {"task_id": TASK, "unofficial": True, "run": name, "videos": a.videos, "train_videos": train_videos,
              "val_videos": val_videos, "train_frames": len(tr["images"]), "train_instances": len(tr["annotations"]),
              "val_frames": len(va["images"]), "classes": 38, "ann_sha256": {"train": sha(ann / "g38_train.json"),
                                                                             "val": sha(va_path)},
              "model": "mmdet Mask2Former R50 (mask2former_r50_8xb2-lsj-50e_coco)", "init": load_report,
              "input": f"短辺 {SHORT}・長辺 {LONG} まで（双線形）、学習は左右反転 0.5、batch_augments なし、32 の倍数へ詰める",
              "batch": 2, "optim_wrapper": json.loads(json.dumps(cfg.optim_wrapper.to_dict(), default=str)),
              "amp": a.amp, "max_epochs": a.max_epochs, "patience": a.patience, "lr_decay": a.lr_decay,
              "selection": "val の 38 クラスの mask mAP（pycocotools segm、元の解像度、上位 100）。改善 = 最良を厳密に上回る",
              "plateau_rule": "scripts/stage1_ptower_r3.py の plateau_action", "seed": a.seed, "smoke": a.smoke,
              "git_commit": git("rev-parse", "HEAD"), "code_sha256": {p: sha(PROJ / p) for p in (
                  "scripts/grasppilot/g_train.py", "scripts/grasppilot/g_bench.py", "scripts/grasppilot/g38_build.py")},
              "host": os.uname().nodename, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
    C.write_json(run / "config.json", config)
    (run / "command.sh").write_text("#!/usr/bin/env bash\n" + " ".join(map(str, [sys.executable] + sys.argv)) + "\n")
    (run / "git_commit.txt").write_text(config["git_commit"] + "\n")
    (run / "start.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    tracking.init(name, config=config, group="grasppilot2_G")
    print(json.dumps({k: config[k] for k in ("train_videos", "train_frames", "val_frames")}), "init", load_report["loaded"],
          "/", load_report["n_checkpoint"], "skipped", skipped, flush=True)

    limit = a.smoke_val if a.smoke else None
    history = []
    pre = evaluate(model, val_loader, va_path, limit=limit)
    history.append({"epoch": 0, "lr": max(gr["lr"] for gr in optim.optimizer.param_groups), **{k: v for k, v in pre.items()}})
    print(f"[G] epoch=0 (学習前) segm_mAP={pre['segm_mAP']:.4f} grasp5={pre['grasp5_mAP']:.4f}", flush=True)
    tracking.log({"val/segm_mAP": pre["segm_mAP"], "val/grasp5_mAP": pre["grasp5_mAP"]}, step=0)
    best, best_epoch = -1.0, None
    stale, lowered, lowered_at, stopped_at = 0, False, None, None
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    epoch = 0
    for epoch in range(1, a.max_epochs + 1):
        model.train()
        t0, tot, n = time.monotonic(), 0.0, 0
        for step, batch in enumerate(train_loader, start=1):
            inputs, samples = to_inputs(model, batch, training=True)
            with optim.optim_context(model):
                losses = model.loss(inputs, samples)
            loss, log_vars = model.parse_losses(losses)
            if not torch.isfinite(loss):
                raise RuntimeError(f"非数の損失 epoch {epoch} step {step}")
            optim.update_params(loss)
            tot += float(loss)
            n += 1
            if step % 200 == 0 or step == 1:
                el = time.monotonic() - t0
                print(f"[G] ep{epoch} {step}/{len(train_loader)} loss={tot / n:.4f} {el / step:.3f}s/step", flush=True)
            if a.smoke and step >= a.smoke_steps:
                break
        train_s = time.monotonic() - t0
        val = evaluate(model, val_loader, va_path, limit=limit)
        lr = max(gr["lr"] for gr in optim.optimizer.param_groups)
        improved = val["segm_mAP"] > best
        if improved:
            best, best_epoch = val["segm_mAP"], epoch
            torch.save({"state_dict": model.state_dict(), "epoch": epoch, "task_id": TASK}, ckpt / "best.pth")
        action, stale, lowered = plateau_action(improved, stale, lowered, a.patience)
        rec = {"epoch": epoch, "lr": lr, "lr_backbone": min(gr["lr"] for gr in optim.optimizer.param_groups),
               "train_loss": tot / max(n, 1), "train_steps": n, "train_seconds": train_s, "improved": improved,
               "action": action, "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()), **val}
        history.append(rec)
        C.write_json(run / "logs/history.json", history)
        tracking.log({"train/loss": rec["train_loss"], "val/segm_mAP": val["segm_mAP"], "val/grasp5_mAP": val["grasp5_mAP"],
                      "lr": lr}, step=epoch)
        print(f"[G] epoch={epoch} lr={lr:g} loss={rec['train_loss']:.4f} segm_mAP={val['segm_mAP']:.4f} "
              f"grasp5={val['grasp5_mAP']:.4f} action={action} train {train_s:.0f}s eval "
              f"{val.get('infer_seconds', 0) + val.get('eval_seconds', 0):.0f}s", flush=True)
        if action == "lower":
            for gr in optim.optimizer.param_groups:
                gr["lr"] *= a.lr_decay
            lowered_at = epoch
        elif action == "stop":
            stopped_at = epoch
            break
        if a.smoke and epoch >= 1:
            break
    torch.save({"state_dict": model.state_dict(), "epoch": epoch, "task_id": TASK}, ckpt / "last.pth")
    best_rec = next(h for h in history if h["epoch"] == best_epoch)
    metrics = {"task_id": TASK, "unofficial": True, "run": name, "videos": a.videos, "best_epoch": best_epoch,
               "best_segm_mAP": best, "best_grasp5_mAP": best_rec["grasp5_mAP"], "pre_segm_mAP": pre["segm_mAP"],
               "pre_grasp5_mAP": pre["grasp5_mAP"], "epochs_completed": epoch, "lr_lowered_epoch": lowered_at,
               "early_stopped_epoch": stopped_at, "reached_epoch_cap": stopped_at is None and epoch == a.max_epochs,
               "elapsed_seconds": time.monotonic() - started, "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()),
               "best_ckpt": str(ckpt / "best.pth"), "best_ckpt_sha256": sha(ckpt / "best.pth"),
               "last_ckpt_sha256": sha(ckpt / "last.pth")}
    C.write_json(run / "metrics.json", metrics)
    C.write_json(run / "per_class_ap.json", best_rec["per_class_ap"])
    (run / "notes.md").write_text(
        f"# {name}（非公式 {TASK}）\n\n把持塔 G（Mask2Former R50、38 クラス）、学ぶ動画 {train_videos}、val {val_videos}。\n"
        f"最良 epoch {best_epoch}: segm mAP {best:.4f}、把持関係 5 クラス {best_rec['grasp5_mAP']:.4f}。"
        f"学習前 {pre['segm_mAP']:.4f} / {pre['grasp5_mAP']:.4f}。\n回した epoch {epoch}、学習率を下げた epoch {lowered_at}、"
        f"打ち切り {stopped_at}。\n")
    (run / "end.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    tracking.finish()
    print("[G] DONE", json.dumps(metrics, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
