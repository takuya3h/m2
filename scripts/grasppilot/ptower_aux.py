"""案 C: 工程塔を補助損失つきで学び直す（非公式 T-2026-11-01-grasp-pilot-g、Task F）。既定の挙動と third_party を変えない派生。

記録の工程塔（`STORE/efros_ptower` の stage1_ptower_20_005・008・009、`scripts/stage1_ptower_20.py` の P15 = 三周目の関数）と同じ部品を呼ぶ:
`stage1_ptower_r3.build_backbone`（R50、COCO の初期化、stem 凍結）・`FoldFrames`（短辺 800、学習は反転）・`frame_predictions`・`frame_accuracy`、
時間ヘッドは `stage1_ptower.build_model`・`run_video`・`evaluate`。違いは次だけ:

- 補助の頭: GAP の特徴（2048）から 48 の線形。手（左手・右手・両手）ごとの 16 値に softmax を掛け、標的 t との交差エントロピーを 3 つの手で平均
- 損失 = 工程の交差エントロピー + w × 補助損失（G を教師・入れ替えた教師は w = 0.3、補助損失なしは w = 0 で、標的は一様の 1/16）
- 長さ: fine-tune は記録と同じ 21 epoch を止めずに回し、記録と同じく 17 epoch 目の後に学習率 × 0.1（記録は 18 epoch 目から 1e-5）。最後の状態を使う
- 特徴の取り出しは折り A の train と val のフレームだけ（記録は全動画。本契約は test を通さない）
- 時間ヘッドは記録の処方（TeCNO C、8 層、平滑化 0.3、lr 5e-4・wd 0.01、warmup 2、cosine の予定は 50 epoch）で 18 epoch 回し、最後の状態を使う
- test のマニフェストを開かない（train と val のマニフェストだけ読む）

    python scripts/grasppilot/ptower_aux.py finetune --arm noaux|teacher|shuffled [--targets t_train.npz] --run-dir D --ckpt-dir D
    python scripts/grasppilot/ptower_aux.py check --steps 4                # 重み 0 の経路と頭の無い経路の損失の一致
    python scripts/grasppilot/ptower_aux.py extract --ckpt last.pth --out feat.npz
    python scripts/grasppilot/ptower_aux.py head --features feat.npz --run-dir D
    python scripts/grasppilot/ptower_aux.py auxval --ckpt last.pth --targets t_val.npz --out aux_val.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from torch import nn
from torch.utils.data import DataLoader

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
sys.path.insert(0, str(PROJ / "src"))
import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402
from stage2pilot import common as C  # noqa: E402

TASK = "T-2026-11-01-grasp-pilot-g"
RECORD = C.EFROS / "experiments/phase1"
FT_RECORD = RECORD / "stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42"
HEAD_RECORD = RECORD / "stage1_ptower_20_009_P15_C_L8_w0.3_h30_foldA_coco_lr0.0001_seed42"
HANDS, VALUES = 3, 16
AUX_DIM = HANDS * VALUES
FT_EPOCHS, FT_LOWER_AFTER = 21, 17       # 記録: 21 epoch 回し、17 epoch 目の後に学習率を下げた（finetune_history.json）
HEAD_EPOCHS = 18                         # 記録: 時間ヘッドは 18 epoch 回した（epochs 50 の予定の途中で止まった）
ARM_WEIGHT = {"noaux": 0.0, "teacher": 0.3, "shuffled": 0.3}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git_head():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJ, capture_output=True, text=True).stdout.strip()


def clips_train_val():
    """train と val のマニフェストの clip（test は開かない）。"""
    clips = []
    for part in ("train", "val"):
        clips.extend(json.loads((C.MANIFEST_DIR / f"{part}.json").read_text())["clips"])
    return clips


def load_cfg(record_dir):
    from omegaconf import OmegaConf
    return OmegaConf.load(record_dir / "config.yaml")


def gap(model, x):
    """torchvision の ResNet の forward を fc の手前（GAP の後の 2048）まで。"""
    x = model.maxpool(model.relu(model.bn1(model.conv1(x))))
    x = model.layer4(model.layer3(model.layer2(model.layer1(x))))
    return torch.flatten(model.avgpool(x), 1)


def aux_loss(logits48, target48):
    """手ごとに 16 値の softmax と標的の交差エントロピー（標的は確率）を 3 つの手で平均。"""
    lp = F.log_softmax(logits48.view(-1, HANDS, VALUES), dim=2)
    t = target48.view(-1, HANDS, VALUES)
    return -(t * lp).sum(2).mean()


def load_targets(path):
    with np.load(path) as z:
        return {str(f): t for f, t in zip(z["frame_ids"], z["t"])}


def build(device, seed):
    torch.manual_seed(seed)
    names = list(json.loads((C.MANIFEST_DIR / "phase_vocab.json").read_text()))
    model, source, digest = r3.build_backbone(len(names), device, "coco")
    head = nn.Linear(2048, AUX_DIM).to(device)
    return model, head, names, source, digest


def finetune(a):
    cfg = load_cfg(FT_RECORD)
    base.deterministic(a.seed)
    device = "cuda"
    split = C.fold_a()
    clips = clips_train_val()
    train_set = r3.FoldFrames(clips, split["train"], train=True)
    val_set = r3.FoldFrames(clips, split["val"], train=False)
    train_videos = C.assert_no_test([f["frame"] for f in train_set.frames], "ptower_aux train")
    val_videos = C.assert_no_test([f["frame"] for f in val_set.frames], "ptower_aux val")
    model, head, names, source, digest = build(device, a.seed)
    weight = ARM_WEIGHT[a.arm]
    if a.arm == "noaux":
        targets, tsha = None, None
    else:
        targets, tsha = load_targets(a.targets), sha(a.targets)
        missing = [f["frame"] for f in train_set.frames if f["frame"] not in targets]
        if missing:
            raise RuntimeError(f"標的の無い train のフレーム {len(missing)} 件（例 {missing[:3]}）")
    uniform = torch.full((AUX_DIM,), 1.0 / VALUES)
    run, ckpt = Path(a.run_dir), Path(a.ckpt_dir)
    (run / "logs").mkdir(parents=True, exist_ok=True)
    ckpt.mkdir(parents=True, exist_ok=True)
    loaders = {
        "train": DataLoader(train_set, batch_size=cfg.ft_batch_size, shuffle=True, num_workers=a.workers,
                            pin_memory=True),  # nosemgrep
        "val": DataLoader(val_set, batch_size=cfg.ft_batch_size, shuffle=False, num_workers=a.workers,
                          pin_memory=True),  # nosemgrep
    }
    params = [p for p in model.parameters() if p.requires_grad] + list(head.parameters())
    optimizer = torch.optim.AdamW(params, lr=cfg.ft_lr, weight_decay=cfg.ft_weight_decay)
    ce = nn.CrossEntropyLoss()
    accum = int(cfg.ft_accum_steps)
    from egosurgery.utils import tracking
    config = {"task_id": TASK, "unofficial": True, "run": run.name, "arm": a.arm, "aux_weight": weight,
              "targets": str(a.targets) if a.targets else "一様 1/16（重み 0）", "targets_sha256": tsha,
              "record_finetune": str(FT_RECORD), "init": source, "backbone_init_sha256": digest,
              "ft_batch_size": int(cfg.ft_batch_size), "ft_accum_steps": accum, "ft_lr": float(cfg.ft_lr),
              "ft_weight_decay": float(cfg.ft_weight_decay), "epochs": a.epochs, "lr_lower_after_epoch": FT_LOWER_AFTER,
              "lr_decay": float(cfg.ft_lr_decay), "selection": "最後の状態（選ばない）", "precision": "fp32",
              "train_videos": train_videos, "val_videos": val_videos, "train_frames": len(train_set),
              "val_frames": len(val_set), "seed": a.seed, "git_commit": git_head(),
              "code_sha256": {"ptower_aux.py": sha(Path(__file__)), "stage1_ptower_r3.py": sha(PROJ / "scripts/stage1_ptower_r3.py"),
                              "stage1_ptower.py": sha(PROJ / "scripts/stage1_ptower.py")},
              "host": os.uname().nodename, "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES")}
    C.write_json(run / "config.json", config)
    (run / "command.sh").write_text("#!/usr/bin/env bash\n" + " ".join([sys.executable] + sys.argv) + "\n")
    (run / "git_commit.txt").write_text(config["git_commit"] + "\n")
    (run / "start.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    tracking.init(run.name, config=config, group="grasppilot2_C")
    history = []
    torch.cuda.reset_peak_memory_stats()
    started = time.monotonic()
    for epoch in range(1, a.epochs + 1):
        r3.stem_eval(model)
        head.train()
        sums = {"phase": 0.0, "aux": 0.0, "total": 0.0}
        gap_abs = {"max": 0.0, "min": float("inf")}
        seen = 0
        optimizer.zero_grad(set_to_none=True)
        steps = len(loaders["train"])
        t0 = time.monotonic()
        for step, (images, y, fids) in enumerate(loaders["train"], start=1):
            images = images.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            f = gap(model, images)
            lp = ce(model.fc(f), y)
            tgt = (uniform.expand(len(fids), -1) if targets is None
                   else torch.from_numpy(np.stack([targets[x] for x in fids])).float()).to(device)
            la = aux_loss(head(f), tgt)
            loss = lp + weight * la
            if not torch.isfinite(loss):
                raise RuntimeError(f"非数の損失 epoch {epoch} step {step}")
            (loss / accum).backward()
            if step % accum == 0 or step == steps:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
            d = float((loss - lp).abs())
            gap_abs["max"], gap_abs["min"] = max(gap_abs["max"], d), min(gap_abs["min"], d)
            n = y.numel()
            sums["phase"] += float(lp) * n
            sums["aux"] += float(la) * n
            sums["total"] += float(loss) * n
            seen += n
            if a.max_steps and step >= a.max_steps:
                break
        train_s = time.monotonic() - t0
        preds, labels, ids = r3.frame_predictions(model, loaders["val"], device)
        val = r3.frame_accuracy(preds, labels, ids, names)
        lr = optimizer.param_groups[0]["lr"]
        rec = {"epoch": epoch, "lr": lr, "train_phase_loss": sums["phase"] / seen, "train_aux_loss": sums["aux"] / seen,
               "train_total_loss": sums["total"] / seen, "total_minus_phase_abs_max": gap_abs["max"],
               "total_minus_phase_abs_min": gap_abs["min"], "val_accuracy": val["phase_accuracy"],
               "val_macro_f1": val["phase_macro_f1"], "train_seconds": train_s,
               "peak_alloc_bytes": int(torch.cuda.max_memory_allocated())}
        history.append(rec)
        C.write_json(run / "logs/history.json", history)
        tracking.log({"train/phase_loss": rec["train_phase_loss"], "train/aux_loss": rec["train_aux_loss"],
                      "val/accuracy": rec["val_accuracy"], "lr": lr}, step=epoch)
        print(f"[C] epoch={epoch} lr={lr:g} phase={rec['train_phase_loss']:.4f} aux={rec['train_aux_loss']:.4f} "
              f"|total-phase| max={gap_abs['max']:.3g} val_acc={rec['val_accuracy']:.4f} {train_s:.0f}s", flush=True)
        if epoch == FT_LOWER_AFTER:
            for group in optimizer.param_groups:
                group["lr"] *= float(cfg.ft_lr_decay)
    torch.save({"model": model.state_dict(), "aux_head": head.state_dict(), "epoch": epoch, "arm": a.arm, "task_id": TASK},
               ckpt / "last.pth")
    metrics = {"task_id": TASK, "unofficial": True, "run": run.name, "arm": a.arm, "epochs_completed": epoch,
               "last_val_accuracy": history[-1]["val_accuracy"], "elapsed_seconds": time.monotonic() - started,
               "peak_alloc_bytes": int(torch.cuda.max_memory_allocated()), "last_ckpt": str(ckpt / "last.pth"),
               "last_ckpt_sha256": sha(ckpt / "last.pth")}
    C.write_json(run / "metrics_finetune.json", metrics)
    (run / "end_finetune.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    tracking.finish()
    print("[C] FINETUNE_DONE", json.dumps(metrics, ensure_ascii=False), flush=True)


def check(a):
    """補助損失の重み 0 の経路が、頭の無い経路（r3.finetune と同じ損失）と同じ損失と同じ更新になることを数歩で見る。"""
    cfg = load_cfg(FT_RECORD)
    device = "cuda"
    split = C.fold_a()
    ds = r3.FoldFrames(clips_train_val(), split["train"], train=False)
    batches = [next(iter(DataLoader(torch.utils.data.Subset(ds, list(range(i * 4, i * 4 + 4))), batch_size=4)))
               for i in range(a.steps)]
    out = {}
    for path in ("plain", "aux0"):
        base.deterministic(a.seed)
        model, head, *_ = build(device, a.seed)
        params = [p for p in model.parameters() if p.requires_grad] + (list(head.parameters()) if path == "aux0" else [])
        opt = torch.optim.AdamW(params, lr=cfg.ft_lr, weight_decay=cfg.ft_weight_decay)
        r3.stem_eval(model)
        losses = []
        for images, y, fids in batches:
            images, y = images.to(device), y.to(device)
            if path == "plain":
                loss = nn.functional.cross_entropy(model(images), y)
            else:
                f = gap(model, images)
                lp = nn.functional.cross_entropy(model.fc(f), y)
                loss = lp + 0.0 * aux_loss(head(f), torch.full((len(fids), AUX_DIM), 1 / VALUES, device=device))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            losses.append(float(loss))
        out[path] = {"losses": losses, "layer4_sum": float(model.layer4[-1].conv3.weight.double().sum()),
                     "fc_sum": float(model.fc.weight.double().sum())}
    out["max_abs_loss_diff"] = max(abs(x - y) for x, y in zip(out["plain"]["losses"], out["aux0"]["losses"]))
    out["layer4_diff"] = abs(out["plain"]["layer4_sum"] - out["aux0"]["layer4_sum"])
    out["fc_diff"] = abs(out["plain"]["fc_sum"] - out["aux0"]["fc_sum"])
    C.write_json(a.out, out)
    print(json.dumps(out, indent=1))


@torch.no_grad()
def extract(a):
    device = "cuda"
    split = C.fold_a()
    clips = clips_train_val()
    every = r3.FoldFrames(clips, split["train"] + split["val"], train=False)
    videos = C.assert_no_test([f["frame"] for f in every.frames], "ptower_aux extract")
    loader = DataLoader(every, batch_size=16, shuffle=False, num_workers=a.workers, pin_memory=True)  # nosemgrep
    model, head, names, source, _ = build(device, 42)
    state = torch.load(a.ckpt, map_location="cpu")
    model.load_state_dict(state["model"])
    model.fc = nn.Identity()
    model.eval().requires_grad_(False)
    t0 = time.monotonic()
    arrays, ids = [], []
    for images, _, fid in loader:
        arrays.append(model(images.to(device, non_blocking=True)).cpu().numpy())
        ids.extend(fid)
    feats = np.concatenate(arrays)
    assert feats.shape == (len(every), 2048) and np.isfinite(feats).all()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, frame_ids=np.asarray(ids), features=feats)
    report = {"task_id": TASK, "checkpoint": str(a.ckpt), "checkpoint_sha256": sha(a.ckpt), "frames": len(ids),
              "videos": videos, "feature_sha256": hashlib.sha256(feats.tobytes()).hexdigest(), "cache_sha256": sha(out),
              "elapsed_seconds": time.monotonic() - t0}
    C.write_json(out.with_suffix(".json"), report)
    print(json.dumps(report), flush=True)


def head_data(features):
    """時間ヘッドの入力（動画ごと、`stage1_ptower.load_fold` と同じ並び = clip の番号順、clip の中はマニフェストの順）。"""
    with np.load(features) as z:
        by = {str(f): i for i, f in enumerate(z["frame_ids"])}
        feats = z["features"]
    split = C.fold_a()
    data = {}
    for part in ("train", "val"):
        data[part] = [(v, np.stack([feats[by[f]] for f in fr]), y) for v, fr, y in C.phase_sequences(split[part])]
    return split, data


def head(a):
    cfg = load_cfg(HEAD_RECORD)
    cfg.device = "cuda"
    base.deterministic(a.seed)
    split, data = head_data(a.features)
    names = list(json.loads((C.MANIFEST_DIR / "phase_vocab.json").read_text()))
    counts = np.bincount(np.concatenate([y for _, _, y in data["train"]]), minlength=len(names))
    weights = np.divide(1.0, counts, out=np.zeros(len(counts)), where=counts > 0)
    weights /= weights[weights > 0].mean()
    model = base.build_model(cfg, len(names)).to(cfg.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    warm = torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=0.5, total_iters=cfg.warmup_epochs)
    cosine = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs - cfg.warmup_epochs)
    scheduler = torch.optim.lr_scheduler.SequentialLR(optimizer, [warm, cosine], [cfg.warmup_epochs])
    ce = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=cfg.device))
    run = Path(a.run_dir)
    (run / "logs").mkdir(parents=True, exist_ok=True)
    history = []
    t0 = time.monotonic()
    for epoch in range(1, a.epochs + 1):
        model.train()
        random.shuffle(data["train"])
        total = 0.0
        for _, x, y in data["train"]:
            outs = base.run_video(model, cfg, x, None, cfg.device)
            labels = torch.from_numpy(y).to(cfg.device)
            loss = sum(ce(o[0].T, labels) for o in outs)
            for o in outs:
                logp = F.log_softmax(o, dim=1)
                loss = loss + cfg.smoothing_weight * F.mse_loss(
                    logp[:, :, 1:], logp[:, :, :-1].detach(), reduction="none").clamp(max=16).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total += loss.item()
        val = base.evaluate(model, data["val"], cfg.device, names, cfg, {})
        history.append({"epoch": epoch, "train_loss": total / len(data["train"]), "lr": optimizer.param_groups[0]["lr"],
                        "val_jaccard": val["phase_jaccard"], "val_accuracy": val["phase_accuracy"]})
        print(f"[C-head] epoch={epoch} val_jaccard={val['phase_jaccard']:.6f} accuracy={val['phase_accuracy']:.6f}", flush=True)
        scheduler.step()
    torch.save({"model": model.state_dict(), "epoch": epoch, "task_id": TASK}, run / "head_last.pth")
    model.eval()
    probs, per_video = {}, {}
    with torch.no_grad():
        for v, x, y in sorted(data["val"]):
            p = torch.softmax(base.run_video(model, cfg, x, None, cfg.device)[-1][0], 0).T.cpu().numpy()
            probs[v] = p
            one = base.evaluate(model, [(v, x, y)], cfg.device, names, cfg, {})
            per_video[v] = {"jaccard": one["phase_jaccard"], "accuracy": one["phase_accuracy"]}
    np.savez(run / "val_probs_last.npz", **probs)
    res = {"task_id": TASK, "unofficial": True, "features": str(a.features), "features_sha256": sha(a.features),
           "record_head": str(HEAD_RECORD), "epochs": epoch, "phase_jaccard": val["phase_jaccard"],
           "phase_accuracy": val["phase_accuracy"], "per_class_jaccard": val["phase_per_class_jaccard"],
           "per_video": per_video, "class_weights": weights.tolist(), "history": history,
           "elapsed_seconds": time.monotonic() - t0, "head_sha256": sha(run / "head_last.pth")}
    C.write_json(run / "metrics_head.json", res)
    print("[C-head] DONE", json.dumps({k: res[k] for k in ("phase_jaccard", "phase_accuracy", "per_video")}), flush=True)


@torch.no_grad()
def auxval(a):
    """補助の頭の val の当たり具合: 手ごとの t との交差エントロピー（Task F-4）。"""
    device = "cuda"
    split = C.fold_a()
    ds = r3.FoldFrames(clips_train_val(), split["val"], train=False)
    loader = DataLoader(ds, batch_size=16, shuffle=False, num_workers=a.workers)  # nosemgrep
    model, head, *_ = build(device, 42)
    state = torch.load(a.ckpt, map_location="cpu")
    model.load_state_dict(state["model"])
    head.load_state_dict(state["aux_head"])
    model.eval()
    head.eval()
    targets = load_targets(a.targets)
    sums, n = np.zeros(HANDS), 0
    uni = np.zeros(HANDS)
    for images, _, fids in loader:
        lp = F.log_softmax(head(gap(model, images.to(device))).view(-1, HANDS, VALUES), 2)
        t = torch.from_numpy(np.stack([targets[x] for x in fids])).float().to(device).view(-1, HANDS, VALUES)
        sums += (-(t * lp).sum(2)).sum(0).cpu().numpy()
        uni += (-(t * np.log(1 / VALUES)).sum(2)).sum(0).cpu().numpy()
        n += len(fids)
    res = {"ckpt": str(a.ckpt), "targets": str(a.targets), "targets_sha256": sha(a.targets), "frames": n,
           "ce_per_hand": dict(zip(("left", "right", "both"), (sums / n).tolist())),
           "ce_uniform_per_hand": dict(zip(("left", "right", "both"), (uni / n).tolist()))}
    C.write_json(a.out, res)
    print(json.dumps(res), flush=True)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("finetune")
    p.add_argument("--arm", choices=tuple(ARM_WEIGHT), required=True)
    p.add_argument("--targets")
    p.add_argument("--run-dir", required=True)
    p.add_argument("--ckpt-dir", required=True)
    p.add_argument("--epochs", type=int, default=FT_EPOCHS)
    p.add_argument("--max-steps", type=int, default=0, help="試走用。0 なら全歩")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--seed", type=int, default=42)
    p = sub.add_parser("check")
    p.add_argument("--steps", type=int, default=4)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", required=True)
    p = sub.add_parser("extract")
    p.add_argument("--ckpt", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=4)
    p = sub.add_parser("head")
    p.add_argument("--features", required=True)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--epochs", type=int, default=HEAD_EPOCHS)
    p.add_argument("--seed", type=int, default=42)
    p = sub.add_parser("auxval")
    p.add_argument("--ckpt", required=True)
    p.add_argument("--targets", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    {"finetune": finetune, "check": check, "extract": extract, "head": head, "auxval": auxval}[a.cmd](a)


if __name__ == "__main__":
    main()
