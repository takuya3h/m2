"""Phase-tower attribution diagnostics on the val videos outside the official test.

T-2026-10-04-ptower-attribution-val. Inference and gradients only: no training, no
weight change, no W&B. Each target video is read only by the tower of the fold that
holds it in val. The official test videos are never opened: manifests are read for
train/val only, the tool/hand GT for test is not read, and feature caches are
memory-mapped row by row so test rows are never materialized.

Large per-frame outputs go to ``OUT`` (outside the repo). Small tables go to
``experiments/analysis/ptower_attribution``.

Usage (one tower per process):
    python scripts/ptower_attribution.py baseline
    python scripts/ptower_attribution.py run --fold A --chain coco --device cuda:1
    python scripts/ptower_attribution.py positional --fold A --chain coco --device cuda:1
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import struct
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import yaml
from omegaconf import OmegaConf
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision.models import resnet50

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
from stage1_ptower_r3 import EVAL_TRANSFORM  # noqa: E402

TASK_ID = "T-2026-10-04-ptower-attribution-val"
OUT = Path(os.environ.get("PTOWER_ATTR_OUT", "/home/ubuntu/local/ptower_attribution_20261005"))
REPO_OUT = ROOT / "experiments/analysis/ptower_attribution"
RUNS = ROOT / "experiments/phase1"
MANIFEST = ROOT / "data/processed/phase_manifest"
GT_DIR = ROOT / "data/annotations/egosurgery_tool_hand"
HEADS = {"coco": "P15_C_L8_w0.3_h30_fold{fold}_coco_lr0.0001_seed42",
         "imagenet": "P15_B_L8_w0.0_h30_fold{fold}_imagenet_lr0.0001_seed42"}
# conventions#det_groups, matched by exact class name.
TARGET_GROUP = ("Skewer", "Bipolar Forceps", "Scalpel", "Syringe", "Raspatory")
NEGATIVE_GROUP = ("Gauze", "Mouth Gag", "Suction Cannula", "Tweezers")
WIDTH, HEIGHT = 1920, 1080
IN_H, IN_W = 800, 1422
REGIONS = ("tool_only", "hand_only", "both", "outside", "target_tools", "negative_tools")
CONDITIONS = ("none", "full") + REGIONS + tuple(f"ctrl_{r}" for r in REGIONS)
REPLACE_K = (1, 2, 4, 8, 16, 32, 64, 128, 256, 512, "all")
CONTROL_SHIFTS = 64
CONTROL_SEED = 20261005
CONTROL_STEP = 8  # shift search on an 8-px grid; the chosen shift is applied at full size


# ---------------------------------------------------------------- targets and folds
def official_test():
    return set((ROOT / "data/splits/ego_test.txt").read_text().split())


def target_folds():
    """{video: fold} for the val videos of each fold minus the official test."""
    table, test = base.folds(), official_test()
    result = {v: fold for fold, split in table.items() for v in split["val"] if v not in test}
    assert not set(result) & test
    return result


def check_targets(videos, test=None):
    """Raise if any video is an official test video (完了判定 a/k)."""
    test = official_test() if test is None else set(test)
    bad = sorted(set(videos) & test)
    if bad:
        raise ValueError(f"official test videos in target set: {bad}")
    return sorted(set(videos))


# ---------------------------------------------------------------- reading log
def log_read(kind, fold, chain, videos):
    """Append which videos entered which tower (完了判定 b/k)."""
    OUT.mkdir(parents=True, exist_ok=True)
    row = {"time": datetime.now(timezone.utc).isoformat(), "kind": kind, "fold": fold,
           "chain": chain, "videos": sorted(videos), "pid": os.getpid()}
    with (OUT / "reads.jsonl").open("a") as handle:
        handle.write(json.dumps(row) + "\n")


def reads_outside(rows, targets, plan):
    """Videos read outside the targets, or by a tower other than their own fold's.

    The single ``control_b`` row (完了判定 b's control) is the allowed exception.
    """
    bad = []
    for row in rows:
        if row["kind"] == "control_b":
            continue
        for video in row["videos"]:
            if video not in targets or plan.get(video) != row["fold"]:
                bad.append((row["kind"], row["fold"], row["chain"], video))
    return bad


# ---------------------------------------------------------------- materials
def tower_paths(fold, chain):
    head = glob.glob(str(RUNS / f"stage1_ptower_r3_*_{HEADS[chain].format(fold=fold)}"))
    feat = glob.glob(str(RUNS / f"stage1_ptower_r3_*_features_{chain}_lr0.0001_fold{fold}_seed42"))
    assert len(head) == 1 and len(feat) == 1, (head, feat)
    head, feat = Path(head[0]), Path(feat[0])
    head_cfg = yaml.safe_load((head / "config.yaml").read_text())
    feat_cfg = yaml.safe_load((feat / "config.yaml").read_text())
    return {"head_run": head, "feature_run": feat,
            "head_ckpt": head / "checkpoints/best.pth",
            "backbone_ckpt": ROOT / feat_cfg["checkpoint"],
            "cache": ROOT / head_cfg["cache"],
            "metrics": json.loads((head / "metrics.json").read_text())}


def phase_names():
    return list(json.loads((MANIFEST / "phase_vocab.json").read_text()))


def video_frames(videos):
    """{video: [frame dict]} in ``load_fold`` order. Reads the train/val manifests only."""
    videos = check_targets(videos)
    clips = []
    for split in ("train", "val"):
        clips.extend(json.loads((MANIFEST / f"{split}.json").read_text())["clips"])
    result = {}
    for video in videos:
        selected = sorted((c for c in clips if c["video"] == video),
                          key=lambda c: int(c["clip_id"].split("_")[1]))
        if not selected:
            raise ValueError(f"video {video} not in train/val manifests")
        result[video] = [f for c in selected for f in c["frames"]]
    return result


def cache_rows(path, frame_ids):
    """Rows of an uncompressed ``np.savez`` cache for ``frame_ids`` only (memory-mapped)."""
    with np.load(path) as cache:
        index = {str(fid): i for i, fid in enumerate(cache["frame_ids"])}
    with zipfile.ZipFile(path) as archive:
        info = archive.getinfo("features.npy")
    assert info.compress_type == zipfile.ZIP_STORED
    with open(path, "rb") as handle:
        handle.seek(info.header_offset)
        local = handle.read(30)
        name_len, extra_len = struct.unpack("<HH", local[26:30])
        handle.seek(info.header_offset + 30 + name_len + extra_len)
        version = np.lib.format.read_magic(handle)
        shape, fortran, dtype = np.lib.format._read_array_header(handle, version)
        offset = handle.tell()
    assert not fortran and len(shape) == 2
    table = np.memmap(path, dtype=dtype, mode="r", offset=offset, shape=shape)
    rows = np.asarray([index[f] for f in frame_ids])
    return np.array(table[rows])


def load_boxes(videos):
    """{frame: [box]} from the tool/hand GT. Val GT for 09/10, train GT otherwise."""
    videos = check_targets(videos)
    official_val = set((ROOT / "data/splits/ego_val.txt").read_text().split())
    result = {}
    for split in ("val", "train"):
        wanted = [v for v in videos if (v in official_val) == (split == "val")]
        if not wanted:
            continue
        gt = json.loads((GT_DIR / f"instances_{split}.json").read_text())
        cats = {c["id"]: c for c in gt["categories"]}
        images = {i["id"]: Path(i["file_name"]).stem for i in gt["images"]
                  if Path(i["file_name"]).stem[:2] in wanted}
        for stem in images.values():
            result.setdefault(stem, [])
        for a in gt["annotations"]:
            stem = images.get(a["image_id"])
            if stem is None:
                continue
            x, y, w, h = map(int, a["bbox"])
            c = cats[a["category_id"]]
            result[stem].append({"id": a["id"], "category": c["name"], "kind": c["supercategory"],
                                 "x": x, "y": y, "w": w, "h": h})
    return result


# ---------------------------------------------------------------- masks
def box_mask(boxes, keep=lambda b: True):
    mask = np.zeros((HEIGHT, WIDTH), dtype=bool)
    for b in boxes:
        if keep(b):
            mask[b["y"]:b["y"] + b["h"], b["x"]:b["x"] + b["w"]] = True
    return mask


def region_masks(boxes):
    """The four disjoint regions and the two tool groups, at 1920x1080."""
    tool = box_mask(boxes, lambda b: b["kind"] == "tool")
    hand = box_mask(boxes, lambda b: b["kind"] == "hand")
    return {"tool_only": tool & ~hand, "hand_only": hand & ~tool, "both": tool & hand,
            "outside": ~(tool | hand),
            "target_tools": box_mask(boxes, lambda b: b["category"] in TARGET_GROUP),
            "negative_tools": box_mask(boxes, lambda b: b["category"] in NEGATIVE_GROUP)}


def rolled_control(mask, union, seed):
    """Same-area control: the mask rolled on the torus, least overlap with ``union``.

    Returns (control, overlap fraction of the control's area, (dy, dx)).
    """
    if not mask.any():
        return np.zeros_like(mask), float("nan"), (0, 0)
    rng = np.random.default_rng(seed)
    small_m = mask[::CONTROL_STEP, ::CONTROL_STEP]
    small_u = union[::CONTROL_STEP, ::CONTROL_STEP]
    best = None
    for _ in range(CONTROL_SHIFTS):
        dy = int(rng.integers(0, small_m.shape[0]))
        dx = int(rng.integers(0, small_m.shape[1]))
        overlap = int((np.roll(small_m, (dy, dx), axis=(0, 1)) & small_u).sum())
        if best is None or overlap < best[0]:
            best = (overlap, dy, dx)
    shift = (best[1] * CONTROL_STEP, best[2] * CONTROL_STEP)
    control = np.roll(mask, shift, axis=(0, 1))
    return control, float((control & union).sum() / control.sum()), shift


_RY = ((np.arange(IN_H) + 0.5) * HEIGHT / IN_H).astype(int)
_RX = ((np.arange(IN_W) + 0.5) * WIDTH / IN_W).astype(int)


def to_input_grid(mask):
    """Nearest-neighbour 1920x1080 -> 1422x800."""
    return mask[_RY][:, _RX]


def condition_masks(boxes, seed):
    """{condition: bool mask at 1920x1080}, areas, control overlaps and shifts."""
    regions = region_masks(boxes)
    union = ~regions["outside"]
    masks = {"none": np.zeros((HEIGHT, WIDTH), dtype=bool),
             "full": np.ones((HEIGHT, WIDTH), dtype=bool), **regions}
    overlaps, shifts = {}, {}
    for i, name in enumerate(REGIONS):
        control, overlap, shift = rolled_control(regions[name], union, seed * 16 + i)
        masks[f"ctrl_{name}"], overlaps[name], shifts[name] = control, overlap, shift
    areas = {k: int(v.sum()) for k, v in masks.items()}
    return masks, areas, overlaps, shifts


# ---------------------------------------------------------------- contribution
def upsample(cam):
    """The existing tool's resize: PIL bilinear on a float image, to 1920x1080."""
    return np.asarray(Image.fromarray(cam.astype(np.float32), mode="F").resize(
        (WIDTH, HEIGHT), Image.Resampling.BILINEAR), dtype=np.float64)


def shares(field, masks):
    total = float(field.sum())
    return {k: (float(field[m].sum() / total) if total > 0 else 0.0) for k, m in masks.items()}


# ---------------------------------------------------------------- towers
def load_tower(fold, chain, device):
    paths = tower_paths(fold, chain)
    names = phase_names()
    backbone = resnet50(weights=None)
    backbone.fc = nn.Linear(2048, len(names))
    state = torch.load(paths["backbone_ckpt"], map_location="cpu", weights_only=True)
    backbone.load_state_dict(state["model"], strict=True)
    backbone.fc = nn.Identity()
    backbone = backbone.to(device).eval().requires_grad_(False)
    cfg = OmegaConf.create(yaml.safe_load((paths["head_run"] / "config.yaml").read_text()))
    head = base.build_model(cfg, len(names))
    head.load_state_dict(torch.load(paths["head_ckpt"], map_location="cpu",
                                    weights_only=True)["model"], strict=True)
    head = head.to(device).eval().requires_grad_(False)
    return backbone, head, paths, cfg


def receptive_field(cfg):
    one_stage = 2 * (2 ** cfg.layers - 1)
    field = 1 + 2 * one_stage
    if cfg.candidate == "B":
        field += cfg.history - 1
    return field


@torch.no_grad()
def trunk(backbone, images):
    """layer4 activation and the GAP feature exactly as ``backbone(images)`` gives it."""
    x = backbone.maxpool(backbone.relu(backbone.bn1(backbone.conv1(images))))
    act = backbone.layer4(backbone.layer3(backbone.layer2(backbone.layer1(x))))
    return act, torch.flatten(backbone.avgpool(act), 1)


def last_logits(head, seq):
    """seq (B, 2048, T) -> logits of the final output at every time (B, C, T)."""
    return head(seq)[-1]


def grad_at(head, prefix, column, t, classes):
    """d logit_t[c] / d column, with ``column`` placed at time t of ``prefix``."""
    column = column.detach().clone().requires_grad_(True)
    seq = torch.cat((prefix[:, :t], column[:, None], prefix[:, t + 1:]), dim=1)
    with torch.enable_grad():
        logits = last_logits(head, seq[None])[0, :, t]
        grads = [torch.autograd.grad(logits[c], column, retain_graph=True)[0] for c in classes]
    return logits.detach(), grads


def cam_from_grad(act, grad):
    """Grad-CAM of the existing tool: weights = spatial mean of d logit / d layer4."""
    weights = grad / (act.shape[-1] * act.shape[-2])
    return torch.relu((weights[:, None, None] * act).sum(0))


class Frames(Dataset):
    def __init__(self, frames, boxes, seeds):
        self.frames, self.boxes, self.seeds = frames, boxes, seeds

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, i):
        f = self.frames[i]
        with Image.open(ROOT / f["image_path"]) as im:
            image = EVAL_TRANSFORM(im.convert("RGB"))
        masks, areas, overlaps, shifts = condition_masks(self.boxes[f["frame"]], self.seeds[i])
        small = np.stack([to_input_grid(masks[c]) for c in CONDITIONS])
        return (image, torch.from_numpy(small), i,
                np.array([areas[c] for c in CONDITIONS]),
                np.array([overlaps[r] for r in REGIONS]),
                np.array([shifts[r] for r in REGIONS]))


def frame_seeds(frames):
    """audit.md §6.1: 20261005 + the frame's index within its video."""
    return [CONTROL_SEED + i for i in range(len(frames))]


# ---------------------------------------------------------------- baseline (Task B)
@torch.no_grad()
def baseline(args):
    base.deterministic(42)
    names, plan = phase_names(), target_folds()
    rows = []
    for fold in sorted(set(plan.values())):
        videos = check_targets([v for v, f in plan.items() if f == fold])
        frames = video_frames(videos)
        for chain in HEADS:
            _, head, paths, _ = load_tower(fold, chain, args.device)
            log_read("baseline", fold, chain, videos)
            clips = [(v, cache_rows(paths["cache"], [f["frame"] for f in frames[v]]),
                      np.array([f["label"] for f in frames[v]])) for v in videos]
            got = base.evaluate(head, clips, args.device, names)
            rec = paths["metrics"]
            whole = set(base.folds()[fold]["val"]) == set(videos)
            rows.append({"fold": fold, "chain": chain, "videos": videos,
                         "head_run": paths["head_run"].name, "whole_val": whole,
                         "recorded_jaccard": rec["phase_jaccard"], "recorded_accuracy": rec["phase_accuracy"],
                         "measured_jaccard": got["phase_jaccard"], "measured_accuracy": got["phase_accuracy"],
                         "reproduced": (abs(got["phase_jaccard"] - rec["phase_jaccard"]) <= 1e-9
                                        and abs(got["phase_accuracy"] - rec["phase_accuracy"]) <= 1e-9)
                         if whole else "UNKNOWN"})
            if fold == "A":
                # Breaking control for c: swap one frame's feature for another one.
                x = clips[0][1].copy()
                x[100] = x[300]
                swapped = base.evaluate(head, [(clips[0][0], x, clips[0][2])] + clips[1:],
                                        args.device, names)
                rows[-1]["swap_one_frame_jaccard"] = swapped["phase_jaccard"]
                rows[-1]["swap_one_frame_accuracy"] = swapped["phase_accuracy"]
                rows[-1]["correct_frames"] = int(sum(
                    int((head(torch.from_numpy(c[1]).T[None].to(args.device))[-1][0].argmax(0).cpu().numpy()
                         == c[2]).sum()) for c in clips))
    # Control for b: another fold's tower on fold A's val (output not used in analysis).
    _, head, paths, _ = load_tower("B", "coco", args.device)
    log_read("control_b", "B", "coco", ["09", "10"])
    frames = video_frames(["09", "10"])
    clips = [(v, cache_rows(paths["cache"], [f["frame"] for f in frames[v]]),
              np.array([f["label"] for f in frames[v]])) for v in ("09", "10")]
    got = base.evaluate(head, clips, args.device, names)
    control = {"tower": "B/coco", "videos": ["09", "10"], "measured_jaccard": got["phase_jaccard"],
               "measured_accuracy": got["phase_accuracy"]}
    OUT.mkdir(parents=True, exist_ok=True)
    result = {"rows": rows, "control_other_fold": control}
    (OUT / "baseline.json").write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


# ---------------------------------------------------------------- C/D/E per tower
def run(args):
    base.deterministic(42)
    names = phase_names()
    plan = target_folds()
    videos = check_targets([v for v, f in plan.items() if f == args.fold])
    backbone, head, paths, cfg = load_tower(args.fold, args.chain, args.device)
    field = receptive_field(cfg)
    frames = video_frames(videos)
    boxes = load_boxes(videos)
    out_dir = OUT / "towers" / f"{args.fold}_{args.chain}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_read("run", args.fold, args.chain, videos)
    dev = args.device
    for video in videos:
        target = out_dir / f"{video}.npz"
        if target.exists():
            print(f"skip existing {target}", flush=True)
            continue
        started = time.monotonic()
        fr = frames[video]
        n = len(fr)
        ids = [f["frame"] for f in fr]
        labels = np.array([f["label"] for f in fr])
        cache = torch.from_numpy(cache_rows(paths["cache"], ids)).T.contiguous().to(dev)  # (2048, T)
        with torch.no_grad():
            base_logits = last_logits(head, cache[None])[0].T.contiguous()  # (T, C)
        pred = base_logits.argmax(1).cpu().numpy()
        nc = len(CONDITIONS)
        occ = torch.zeros((nc, 2048, n), device=dev)
        cam = np.zeros((n, 2, 25, 45), dtype=np.float32)
        cam_logits = np.zeros((n, len(names)), dtype=np.float32)
        feat_err = np.zeros(n)
        areas = np.zeros((n, nc), dtype=np.int64)
        overlaps = np.zeros((n, len(REGIONS)))
        shifts = np.zeros((n, len(REGIONS), 2), dtype=np.int64)
        loader = DataLoader(Frames(fr, boxes, frame_seeds(fr)), batch_size=1, shuffle=False,
                            num_workers=args.workers)
        for image, masks, i, area, overlap, shift in loader:
            i = int(i)
            image = image.to(dev)
            batch = image.repeat(nc, 1, 1, 1)
            batch = batch * (~masks[0].to(dev))[:, None]  # 0 = ImageNet mean after normalization
            act, gap = trunk(backbone, batch)
            occ[:, :, i] = gap
            feat_err[i] = float((gap[0] - cache[:, i]).abs().max())
            classes = [int(pred[i]), int(labels[i])]
            logits, grads = grad_at(head, cache[:, : i + 1], gap[0], i, classes)
            cam_logits[i] = logits.cpu().numpy()
            for j, g in enumerate(grads):
                cam[i, j] = cam_from_grad(act[0], g).cpu().numpy()
            areas[i], overlaps[i], shifts[i] = area[0].numpy(), overlap[0].numpy(), shift[0].numpy()
        with torch.no_grad():
            # D, scope "all frames": every frame occluded with its own region.
            occ_all = torch.stack([last_logits(head, occ[c][None])[0].T for c in range(nc)], 1)
            occ_cur = torch.zeros((n, nc, len(names)), device=dev)
            for t in range(n):
                seq = cache[:, : t + 1].unsqueeze(0).repeat(nc, 1, 1)
                seq[:, :, t] = occ[:, :, t]
                occ_cur[t] = last_logits(head, seq)[:, :, t]
        # E: gradient x feature over time, replacement, receptive-field controls.
        gpos = np.zeros((n, 2, n), dtype=np.float32)
        gneg = np.zeros((n, 2, n), dtype=np.float32)
        ks = [k if k != "all" else None for k in REPLACE_K]
        repl = np.zeros((n, 2, len(ks), len(names)), dtype=np.float32)
        rf_out = np.full(n, np.nan)
        rf_lag1 = np.full(n, np.nan)
        for t in range(n):
            classes = [int(pred[t]), int(labels[t])]
            seq = cache[:, : t + 1].detach().clone().requires_grad_(True)
            with torch.enable_grad():
                logits = last_logits(head, seq[None])[0, :, t]
                for j, c in enumerate(classes):
                    g, = torch.autograd.grad(logits[c], seq, retain_graph=True)
                    prod = g * seq.detach()
                    gpos[t, j, : t + 1] = prod.clamp(min=0).sum(0).cpu().numpy()
                    gneg[t, j, : t + 1] = prod.clamp(max=0).sum(0).cpu().numpy()
            with torch.no_grad():
                variants = []
                for fill in ("copy", "zero"):
                    for k in ks:
                        s = cache[:, : t + 1].clone()
                        lo = 0 if k is None else max(0, t - k)
                        s[:, lo:t] = cache[:, t : t + 1] if fill == "copy" else 0.0
                        variants.append(s)
                extra = t >= field
                if extra:
                    s = cache[:, : t + 1].clone()
                    s[:, : t - field + 1] = 0.0
                    variants.append(s)
                if t >= 1:
                    s = cache[:, : t + 1].clone()
                    s[:, t - 1] = 0.0
                    variants.append(s)
                out = last_logits(head, torch.stack(variants))[:, :, t]
                repl[t] = out[: 2 * len(ks)].reshape(2, len(ks), -1).cpu().numpy()
                ref = base_logits[t]
                pos = 2 * len(ks)
                if extra:
                    rf_out[t] = float((out[pos] - ref).abs().max())
                    pos += 1
                if t >= 1:
                    rf_lag1[t] = float((out[pos] - ref).abs().max())
        np.savez(target, frame_ids=np.array(ids), labels=labels, pred=pred,
                 base_logits=base_logits.cpu().numpy(), cam=cam, cam_logits=cam_logits,
                 feat_err=feat_err, conditions=np.array(CONDITIONS), regions=np.array(REGIONS),
                 occ_all=occ_all.cpu().numpy(), occ_cur=occ_cur.cpu().numpy(),
                 areas=areas, overlaps=overlaps, shifts=shifts,
                 gpos=gpos, gneg=gneg, replace_k=np.array([str(k) for k in REPLACE_K]),
                 repl=repl, rf_out=rf_out, rf_lag1=rf_lag1, receptive_field=field)
        print(f"{args.fold}/{args.chain}/{video}: {n} frames in {time.monotonic() - started:.0f}s",
              flush=True)


# ---------------------------------------------------------------- E-4 positional
def positional_selection(gpos_gt, t, field):
    """Lags chosen by the rule fixed in audit.md §6.3 for target frame t."""
    fixed = [lag for lag in (1, 5, 15, 30, 60) if t - lag >= 0]
    upper = min(t, field - 1)
    contrib = [(-float(gpos_gt[t - lag]), lag) for lag in range(1, upper + 1)]
    top = [lag for _, lag in sorted(contrib)[:3]]
    chosen = {}
    for lag in fixed:
        chosen.setdefault(lag, set()).add("fixed")
    for lag in top:
        chosen.setdefault(lag, set()).add("top")
    return {lag: sorted(tags) for lag, tags in sorted(chosen.items())}


def positional(args):
    base.deterministic(42)
    plan = target_folds()
    videos = check_targets([v for v, f in plan.items() if f == args.fold])
    backbone, head, paths, cfg = load_tower(args.fold, args.chain, args.device)
    field = receptive_field(cfg)
    frames = video_frames(videos)
    out_dir = OUT / "towers" / f"{args.fold}_{args.chain}"
    log_read("positional", args.fold, args.chain, videos)
    dev = args.device
    for video in videos:
        target = out_dir / f"{video}_positional.json"
        if target.exists():
            continue
        data = np.load(out_dir / f"{video}.npz")
        fr = frames[video]
        ids = [f["frame"] for f in fr]
        cache = torch.from_numpy(cache_rows(paths["cache"], ids)).T.contiguous().to(dev)
        rows = []
        for t in range(100, len(fr), 100):
            gt = int(data["labels"][t])
            for lag, tags in positional_selection(data["gpos"][t, 1], t, field).items():
                tau = t - lag
                with Image.open(ROOT / fr[tau]["image_path"]) as im:
                    image = EVAL_TRANSFORM(im.convert("RGB"))[None].to(dev)
                act, gap = trunk(backbone, image)
                column = gap[0].detach().clone().requires_grad_(True)
                seq = torch.cat((cache[:, :tau], column[:, None], cache[:, tau + 1: t + 1]), 1)
                with torch.enable_grad():
                    logit = last_logits(head, seq[None])[0, gt, t]
                    g, = torch.autograd.grad(logit, column)
                m = cam_from_grad(act[0], g).cpu().numpy()
                rows.append({"t": t, "frame": ids[t], "lag": lag, "tau_frame": ids[tau], "tags": tags,
                             "class": gt, "raw_max": float(m.max()), "raw_sum": float(m.sum()),
                             "cam": m.round(9).tolist()})
        target.write_text(json.dumps(rows))
        print(f"positional {args.fold}/{args.chain}/{video}: {len(rows)} maps", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("action", choices=("baseline", "run", "positional"))
    parser.add_argument("--fold")
    parser.add_argument("--chain", choices=tuple(HEADS))
    parser.add_argument("--device", default="cuda:1")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required")
    {"baseline": baseline, "run": run, "positional": positional}[args.action](args)


if __name__ == "__main__":
    main()
