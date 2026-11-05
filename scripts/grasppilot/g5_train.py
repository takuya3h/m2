"""把持塔 G（5 クラス、左右反転でラベルを入れ替える）の学習（非公式 T-2026-11-05-grasp-tower-rebuild、Task C）。本体の .venv。

二本目の `g_train.py` を変えずに、その部品（`to_inputs`・`evaluate`・`collate`・`resize_shape`）を読んで使う派生。変えるのは次の三つだけ:
    1. 頭のクラス数 5（把持関係 5 クラス。`g5_build.py` の注釈）
    2. 左右反転（確率 0.5）のとき、ラベル 1 ↔ 2、3 ↔ 4 を入れ替える（5 は変えない）。`G5Flip`
    3. 収束規則: epoch ごとに val の 5 クラスの mask mAP を測り、最良（厳密に上回ったら更新）が 4 epoch 更新されなければ打ち切る。
       上限 36。学習率は下げない（二本目の利用者の決定 2026-11-01 の規則を学習の繰り返しの中で行う）。最良の epoch の重みを使う
処方は二本目と同じ（mmdet の設定の optim_wrapper のまま、短辺 800・長辺 1333、batch 2、単精度、seed 42）。
欠落の印（loss_mask）の付いたフレームが学ぶフレームに入っていれば、学習を始めずに止める。W&B は offline に固定する。

    .venv/bin/python scripts/grasppilot/g5_train.py --run-dir <experiments/phase1/grasptower_G_...> --ckpt-dir <S/g/ckpt/...>
        --ann-dir <S/g/ann> --videos all|H1|H2 [--smoke]
"""
from __future__ import annotations

import argparse
import json
import os
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
from grasppilot import g_train as T  # noqa: E402
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-05-grasp-tower-rebuild"
NUM_CLASSES = 5
HALVES = T.HALVES
SWAP0 = np.array([1, 0, 3, 2, 4], np.int64)   # 0 始まりのラベルの入れ替え（左手 ↔ 右手、左手の器具 ↔ 右手の器具、両手はそのまま）
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
LOSS_MASK_DIR = PROJ / "data/annotations/egosurgery_hts/hand_tool_seg/loss_mask"
# COCO の重み: bengio には一本目の保存先の写しが無いので、andrew から本契約の保存先へ写したもの（sha256 は T.WEIGHT_SHA256 で照合）。
# 一本目・二本目の保存先には書き込まない（SPEC §7-2）
COCO_W = STORE / "inputs/coco" / B.MMDET_W.name


class G5Flip(T.G38):
    """二本目の `G38` と同じ取り出しで、左右反転のときにラベルを入れ替える。

    swap=False は二本目の経路（反転してもラベルを入れ替えない）の写しで、対照に使う。
    force_flip が True / False なら乱数を引かずにその値で反転する（検査用）。None なら学習と同じく確率 0.5。
    """

    def __init__(self, coco, train, seed=42, swap=True, force_flip=None):
        super().__init__(coco, train, seed)
        self.swap = swap
        self.force_flip = force_flip

    def __getitem__(self, i):
        from grasppilot.grasp_signals import decode
        im = self.images[i]
        h, w = im["height"], im["width"]
        nh, nw, r = T.resize_shape(h, w)
        img = Image.open(PROJ / im["file_name"]).convert("RGB").resize((nw, nh), Image.BILINEAR)
        arr = np.asarray(img)
        out = {"image_id": im["id"], "stem": im["stem"], "ori": (h, w), "size": (nh, nw), "scale": r}
        if not self.train:
            return arr, out, None
        flip = bool(torch.rand(1).item() < 0.5) if self.force_flip is None else bool(self.force_flip)
        masks, labels = [], []
        for a in self.by.get(im["id"], []):
            m = Image.fromarray(decode(a["segmentation"], h, w).astype(np.uint8)).resize((nw, nh), Image.NEAREST)
            m = np.asarray(m)
            if m.any():
                masks.append(m)
                labels.append(a["category_id"] - 1)
        labels = np.array(labels, np.int64)
        if flip:
            arr = arr[:, ::-1].copy()
            masks = [m[:, ::-1].copy() for m in masks]
            if self.swap and len(labels):
                labels = SWAP0[labels]
        out["flipped"] = flip
        masks = np.stack(masks) if masks else np.zeros((0, nh, nw), np.uint8)
        return arr, out, (masks, labels)


def patch_msda_bf16():
    """bf16 の自動混合精度で、変形注意（mmcv の ms_deform_attn）だけを fp32 で計算する（利用者の決定 2026-11-06、選択肢 1）。

    mmcv 2.1.0 の `ms_deform_attn_forward_cuda` は bf16 の実装を持たない（`not implemented for 'BFloat16'`）。
    仮想環境と third_party を変えずに、mmcv の `MultiScaleDeformableAttention.forward` が名前で引く
    `MultiScaleDeformableAttnFunction` を、入力の value が bf16 のときだけ fp32 に変換して呼び、出力を bf16 に戻す包みに差し替える。
    value が bf16 でなければ元の関数をそのまま呼ぶ（fp32・fp16 の経路は変わらない）。この過程の中だけに効く。二度呼んでも一度だけ差し替える。
    """
    from mmcv.ops import multi_scale_deform_attn as M
    if getattr(M.MultiScaleDeformableAttnFunction, "_grasptower_bf16_fp32", False):
        return M.MultiScaleDeformableAttnFunction
    orig = M.MultiScaleDeformableAttnFunction

    class MSDAFp32ForBf16:
        _grasptower_bf16_fp32 = True
        original = orig

        @staticmethod
        def apply(value, spatial_shapes, level_start_index, sampling_locations, attention_weights, im2col_step):
            if value.dtype != torch.bfloat16:
                return orig.apply(value, spatial_shapes, level_start_index, sampling_locations, attention_weights, im2col_step)
            out = orig.apply(value.float(), spatial_shapes, level_start_index, sampling_locations.float(),
                             attention_weights.float(), im2col_step)
            return out.to(torch.bfloat16)

    M.MultiScaleDeformableAttnFunction = MSDAFp32ForBf16
    return MSDAFp32ForBf16


def loss_mask_stems():
    return set().union(*[set((LOSS_MASK_DIR / f"{p}.txt").read_text().split()) for p in ("train", "val")])


def stale_since_best(history):
    """epoch 0（学習前）を除いた記録から、最良の値・その epoch・最良の後の epoch 数。改善 = 最良を厳密に上回る。"""
    best, best_epoch, stale = -1.0, None, 0
    for r in history:
        if r["epoch"] == 0:
            continue
        if r["segm_mAP"] > best:
            best, best_epoch, stale = r["segm_mAP"], r["epoch"], 0
        else:
            stale += 1
    return best, best_epoch, stale


def build_model():
    model, cfg = B.mmdet_model(num_classes=NUM_CLASSES)
    wcheck = B.verify_weight(COCO_W, T.WEIGHT_SHA256)
    if not wcheck["ok"]:
        raise RuntimeError(f"COCO の重みの要約値が違う: {wcheck}")
    st = torch.load(COCO_W, map_location="cpu")["state_dict"]
    own = model.state_dict()
    keepw = {k: v for k, v in st.items() if k in own and own[k].shape == v.shape}
    skipped = sorted(k for k in st if k in own and own[k].shape != st[k].shape)
    absent = sorted(k for k in st if k not in own)
    missing, _ = model.load_state_dict(keepw, strict=False)
    rep = {"checkpoint": str(COCO_W), "sha256": wcheck["sha256"], "n_checkpoint": len(st), "loaded": len(keepw),
           "skipped_shape": skipped, "absent_in_model": absent, "model_params_not_loaded": sorted(missing)}
    return model, cfg, rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--ann-dir", required=True)
    ap.add_argument("--videos", choices=("all", "H1", "H2"), required=True)
    ap.add_argument("--max-epochs", type=int, default=36)
    ap.add_argument("--patience", type=int, default=4)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--smoke", action="store_true", help="数歩と val の数枚で通るかだけ見る")
    ap.add_argument("--smoke-steps", type=int, default=20)
    ap.add_argument("--smoke-val", type=int, default=10)
    a = ap.parse_args()

    os.environ["WANDB_MODE"] = "offline"                     # SPEC §7-11
    os.environ.setdefault("WANDB_DIR", str(STORE / "wandb"))
    Path(os.environ["WANDB_DIR"]).mkdir(parents=True, exist_ok=True)
    run, ckpt = Path(a.run_dir), Path(a.ckpt_dir)
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    from mmengine.optim import build_optim_wrapper

    from egosurgery.utils import tracking

    ann = Path(a.ann_dir)
    tr_path, va_path = ann / "g5_train.json", ann / "g5_val.json"
    tr = json.loads(tr_path.read_text())
    if a.videos != "all":
        keep = set(HALVES[a.videos])
        tr["images"] = [im for im in tr["images"] if im["video"] in keep]
        ids = {im["id"] for im in tr["images"]}
        tr["annotations"] = [x for x in tr["annotations"] if x["image_id"] in ids]
    va = json.loads(va_path.read_text())
    train_videos = C.assert_no_test([im["stem"] for im in tr["images"]], "G5 train")
    val_videos = C.assert_no_test([im["stem"] for im in va["images"]], "G5 val")
    lm = loss_mask_stems()
    lm_hit = sorted({im["stem"] for im in tr["images"] + va["images"]} & lm)
    if lm_hit:                                               # SPEC §3.1: 印の付いたフレームを学習の対象から外す
        raise RuntimeError(f"欠落の印の付いたフレームが学ぶフレームに {len(lm_hit)} 件ある（{lm_hit[:3]}）。学習を始めない")
    if {c["id"] for c in tr["categories"]} != set(range(1, NUM_CLASSES + 1)):
        raise RuntimeError(f"注釈のクラスが 5 クラスでない: {tr['categories']}")
    (run / "logs").mkdir(parents=True, exist_ok=True)
    ckpt.mkdir(parents=True, exist_ok=True)

    model, cfg, load_report = build_model()
    optim = build_optim_wrapper(model, cfg.optim_wrapper)

    g = torch.Generator()
    g.manual_seed(a.seed)
    train_loader = torch.utils.data.DataLoader(G5Flip(tr, True), batch_size=2, shuffle=True, num_workers=a.workers,
                                               collate_fn=T.collate, generator=g, persistent_workers=True,
                                               pin_memory=False, drop_last=True)  # nosemgrep
    val_loader = torch.utils.data.DataLoader(G5Flip(va, False), batch_size=2, shuffle=False, num_workers=a.workers,
                                             collate_fn=T.collate, pin_memory=False)  # nosemgrep
    name = run.name
    config = {"task_id": TASK, "unofficial": True, "run": name, "videos": a.videos, "train_videos": train_videos,
              "val_videos": val_videos, "train_frames": len(tr["images"]), "train_instances": len(tr["annotations"]),
              "val_frames": len(va["images"]), "classes": NUM_CLASSES,
              "class_names": [c["name"] for c in sorted(tr["categories"], key=lambda c: c["id"])],
              "ann_sha256": {"train": T.sha(tr_path), "val": T.sha(va_path)}, "loss_mask_frames_in_data": 0,
              "model": "mmdet Mask2Former R50 (mask2former_r50_8xb2-lsj-50e_coco)", "init": load_report,
              "input": f"短辺 {T.SHORT}・長辺 {T.LONG} まで（双線形）、学習は左右反転 0.5 でラベル 1↔2・3↔4 を入れ替える、"
                       "batch_augments なし、32 の倍数へ詰める",
              "flip_label_swap": {"1": 2, "2": 1, "3": 4, "4": 3, "5": 5},
              "batch": 2, "optim_wrapper": json.loads(json.dumps(cfg.optim_wrapper.to_dict(), default=str)),
              "amp": "none", "max_epochs": a.max_epochs, "patience": a.patience, "lr_decay": None,
              "selection": "val の 5 クラスの mask mAP（pycocotools segm、元の解像度、上位 100）。頭が 5 クラスなので segm_mAP と grasp5_mAP は同じ量。"
                           "改善 = 最良を厳密に上回る",
              "stop_rule": f"最良が {a.patience} epoch 更新されなければ打ち切り、上限 {a.max_epochs}、学習率は下げない（学習の繰り返しの中で判定）",
              "seed": a.seed, "smoke": a.smoke, "wandb_mode": os.environ["WANDB_MODE"],
              "git_commit": T.git("rev-parse", "HEAD"), "code_sha256": {p: T.sha(PROJ / p) for p in (
                  "scripts/grasppilot/g5_train.py", "scripts/grasppilot/g_train.py", "scripts/grasppilot/g_bench.py",
                  "scripts/grasppilot/g5_build.py")},
              "host": os.uname().nodename, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
    C.write_json(run / "config.json", config)
    (run / "command.sh").write_text("#!/usr/bin/env bash\n" + " ".join(map(str, [sys.executable] + sys.argv)) + "\n")
    (run / "git_commit.txt").write_text(config["git_commit"] + "\n")
    (run / "start.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    tracking.init(name, config=config, group="grasptower_G")
    print(json.dumps({k: config[k] for k in ("train_videos", "train_frames", "val_frames")}), "init", load_report["loaded"],
          "/", load_report["n_checkpoint"], "skipped", load_report["skipped_shape"], flush=True)

    limit = a.smoke_val if a.smoke else None
    history = []
    pre = T.evaluate(model, val_loader, va_path, limit=limit)
    history.append({"epoch": 0, "lr": max(gr["lr"] for gr in optim.optimizer.param_groups), **pre})
    C.write_json(run / "logs/history.json", history)
    print(f"[G5] epoch=0 (学習前) segm_mAP={pre['segm_mAP']:.4f}", flush=True)
    tracking.log({"val/segm_mAP": pre["segm_mAP"]}, step=0)
    best, best_epoch, stopped_at = -1.0, None, None
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    epoch = 0
    for epoch in range(1, a.max_epochs + 1):
        model.train()
        t0, tot, n = time.monotonic(), 0.0, 0
        for step, batch in enumerate(train_loader, start=1):
            inputs, samples = T.to_inputs(model, batch, training=True)
            with optim.optim_context(model):
                losses = model.loss(inputs, samples)
            loss, _ = model.parse_losses(losses)
            if not torch.isfinite(loss):
                raise RuntimeError(f"非数の損失 epoch {epoch} step {step}")
            optim.update_params(loss)
            tot += float(loss)
            n += 1
            if step % 200 == 0 or step == 1:
                el = time.monotonic() - t0
                print(f"[G5] ep{epoch} {step}/{len(train_loader)} loss={tot / n:.4f} {el / step:.3f}s/step", flush=True)
            if a.smoke and step >= a.smoke_steps:
                break
        train_s = time.monotonic() - t0
        val = T.evaluate(model, val_loader, va_path, limit=limit)
        lr = max(gr["lr"] for gr in optim.optimizer.param_groups)
        improved = val["segm_mAP"] > best
        if improved:
            best, best_epoch = val["segm_mAP"], epoch
            torch.save({"state_dict": model.state_dict(), "epoch": epoch, "task_id": TASK, "num_classes": NUM_CLASSES},
                       ckpt / "best.pth")
        rec = {"epoch": epoch, "lr": lr, "lr_backbone": min(gr["lr"] for gr in optim.optimizer.param_groups),
               "train_loss": tot / max(n, 1), "train_steps": n, "train_seconds": train_s, "improved": improved,
               "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()), **val}
        history.append(rec)
        _, _, stale = stale_since_best(history)
        rec["stale"] = stale
        C.write_json(run / "logs/history.json", history)
        tracking.log({"train/loss": rec["train_loss"], "val/segm_mAP": val["segm_mAP"], "lr": lr}, step=epoch)
        print(f"[G5] epoch={epoch} lr={lr:g} loss={rec['train_loss']:.4f} segm_mAP={val['segm_mAP']:.4f} stale={stale} "
              f"train {train_s:.0f}s eval {val.get('infer_seconds', 0) + val.get('eval_seconds', 0):.0f}s", flush=True)
        if stale >= a.patience:
            stopped_at = epoch
            break
        if a.smoke and epoch >= 1:
            break
    torch.save({"state_dict": model.state_dict(), "epoch": epoch, "task_id": TASK, "num_classes": NUM_CLASSES}, ckpt / "last.pth")
    best_rec = next(h for h in history if h["epoch"] == best_epoch)
    metrics = {"task_id": TASK, "unofficial": True, "run": name, "videos": a.videos, "best_epoch": best_epoch,
               "best_segm_mAP": best, "pre_segm_mAP": pre["segm_mAP"], "epochs_completed": epoch,
               "early_stopped_epoch": stopped_at, "reached_epoch_cap": stopped_at is None and epoch == a.max_epochs,
               "elapsed_seconds": time.monotonic() - started, "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()),
               "coco_weights_loaded": load_report["loaded"], "coco_weights_total": load_report["n_checkpoint"],
               "best_ckpt": str(ckpt / "best.pth"), "best_ckpt_sha256": T.sha(ckpt / "best.pth"),
               "last_ckpt_sha256": T.sha(ckpt / "last.pth")}
    C.write_json(run / "metrics.json", metrics)
    C.write_json(run / "per_class_ap.json", best_rec["per_class_ap"])
    (run / "notes.md").write_text(
        f"# {name}（非公式 {TASK}）\n\n把持塔 G（Mask2Former R50、把持関係 5 クラス、反転でラベルを入れ替える）、"
        f"学ぶ動画 {train_videos}、val {val_videos}。\n最良 epoch {best_epoch}: 5 クラスの segm mAP {best:.4f}。"
        f"学習前 {pre['segm_mAP']:.4f}。\n回した epoch {epoch}、打ち切り {stopped_at}。二本目 T-2026-11-01-grasp-pilot-g の G を置き換える。\n")
    (run / "end.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    tracking.finish()
    print("[G5] DONE", json.dumps(metrics, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
