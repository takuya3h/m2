"""Stage 1: frozen ImageNet features and fold-specific phase towers.

Hydra actions extract/train use the same cache for every candidate. Training
never evaluates test. Evidence is created with ExperimentManager.
"""
from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

import hydra
import numpy as np
import torch
import torch.nn.functional as F
from omegaconf import OmegaConf
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision.models import ResNet50_Weights, resnet50

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from egosurgery.models.heads.tecno_head import TeCNO  # noqa: E402
from egosurgery.utils import tracking  # noqa: E402
from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def enrich(cfg, values):
    return OmegaConf.merge(OmegaConf.create(OmegaConf.to_container(cfg, resolve=True)), values)


def folds():
    """Read the canonical table, never derive new splits from labels."""
    text = (ROOT / "docs/stage0/A1_fold_table.md").read_text()
    result = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) == 4 and cells[0] in "ABCDE" and len(cells[0]) == 1:
            result[cells[0]] = {
                key: re.findall(r"\b\d{2}\b", cell)
                for key, cell in zip(("test", "val", "train"), cells[1:])
            }
    assert set(result) == set("ABCDE")
    for split in ("train", "val", "test"):
        official = (ROOT / f"data/splits/ego_{split}.txt").read_text().split()
        assert set(result["A"][split]) == set(official)
    return result


def manifests(cfg):
    clips = []
    for split in ("train", "val", "test"):
        clips.extend(json.loads((ROOT / cfg.manifest_dir / f"{split}.json").read_text())["clips"])
    ids = [f["frame"] for c in clips for f in c["frames"]]
    assert len(ids) == len(set(ids))
    return clips


class Frames(Dataset):
    def __init__(self, clips):
        self.frames = [f for c in clips for f in c["frames"]]
        self.transform = ResNet50_Weights.IMAGENET1K_V1.transforms()

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, index):
        f = self.frames[index]
        with Image.open(ROOT / f["image_path"]) as im:
            return self.transform(im.convert("RGB")), f["frame"]


def deterministic(seed):
    os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    torch.use_deterministic_algorithms(True)
    torch.set_num_threads(4)


def evidence(cfg, description):
    cfg = enrich(cfg, {"source_sha256": sha256(__file__),
                              "contract_sha256": sha256(ROOT / "tasks" / cfg.task_id / "spec.yaml")})
    manager = ExperimentManager(ROOT / "experiments", "phase1", "stage1_ptower",
                                description, cfg.seed)
    manager.setup(OmegaConf.to_container(cfg, resolve=True))
    # A missing/failed tracking connection must not silently produce untracked runs.
    run = tracking.init(manager.exp_id, config=OmegaConf.to_container(cfg, resolve=True),
                        group=cfg.task_id, job_type=cfg.action, exp_dir=manager.exp_dir)
    if run is None:
        raise RuntimeError("W&B tracking could not start; no experiment executed")
    return manager


@torch.no_grad()
def extract(cfg):
    out = ROOT / cfg.cache
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite features: {out}")
    clips = manifests(cfg)
    ds = Frames(clips)
    loader = DataLoader(ds, batch_size=cfg.batch_size, shuffle=False,
                        num_workers=cfg.workers, pin_memory=True)
    weights = ResNet50_Weights.IMAGENET1K_V1
    model = resnet50(weights=weights)
    model.fc = nn.Identity()
    model.eval().requires_grad_(False).to(cfg.device)
    cfg = enrich(cfg, {"weights": str(weights), "transform": str(ds.transform),
                              "feature_dim": 2048, "data_setting": "P15"})
    manager = evidence(cfg, "imagenet_r50_v1_features_P15")
    before = time.monotonic()
    arrays, frame_ids = [], []
    first_batch = None
    for images, ids in loader:
        images = images.to(cfg.device, non_blocking=True)
        features = model(images).cpu().numpy()
        if first_batch is None:
            first_batch = (images.clone(), features.copy())
        arrays.append(features)
        frame_ids.extend(ids)
        if len(frame_ids) % (cfg.batch_size * 20) == 0:
            print(f"features: {len(frame_ids)}/{len(ds)}", flush=True)
    features = np.concatenate(arrays)
    # Full second extraction; preserve only the first cache and hash both arrays.
    digest = hashlib.sha256()
    offset = 0
    for images, ids in loader:
        second = model(images.to(cfg.device, non_blocking=True)).cpu().numpy()
        assert list(ids) == frame_ids[offset:offset + len(ids)]
        assert np.array_equal(second, features[offset:offset + len(ids)])
        digest.update(second.tobytes())
        offset += len(ids)
    first_hash = hashlib.sha256(features.tobytes()).hexdigest()
    assert digest.hexdigest() == first_hash
    # Breaking control: change a used convolution, restore it afterwards.
    saved = model.conv1.weight.clone()
    model.conv1.weight.zero_()
    changed = model(first_batch[0]).cpu().numpy()
    model.conv1.weight.copy_(saved)
    assert not np.array_equal(changed, first_batch[1])
    expected = Counter(c["video"] for c in clips for _ in c["frames"])
    actual = Counter(fid.split("_")[0] for fid in frame_ids)
    assert actual == expected and features.shape == (len(ds), 2048)
    assert np.isfinite(features).all()
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, frame_ids=np.asarray(frame_ids), features=features)
    weight_path = Path(torch.hub.get_dir()) / "checkpoints" / Path(weights.url).name
    report = {"task_id": cfg.task_id, "feature_sha256": first_hash,
              "second_feature_sha256": digest.hexdigest(), "weights_sha256": sha256(weight_path),
              "cache_sha256": sha256(out), "cache_bytes": out.stat().st_size,
              "video_counts": dict(actual), "weight_change_detected": True,
              "removed_video_detected": dict(actual) != {k: v for k, v in actual.items() if k != "01"},
              "elapsed_seconds": time.monotonic() - before}
    write_json(out.with_suffix(".json"), report)
    manager.log_metrics({"frames": len(ds), "elapsed_seconds": report["elapsed_seconds"]})
    write_json(manager.exp_dir / "feature_audit.json", report)
    (manager.exp_dir / "notes.md").write_text("ImageNet V1 frozen C5 GAP; two full extractions matched.\n")
    tracking.log({"frames": len(ds), "cache_bytes": out.stat().st_size})
    tracking.finish()
    print(json.dumps(report), flush=True)


def load_fold(cfg, parts=("train", "val")):
    split = folds()[cfg.fold]
    cache_path = ROOT / cfg.cache
    audit = json.loads(cache_path.with_suffix(".json").read_text())
    assert sha256(cache_path) == audit["cache_sha256"]
    with np.load(cache_path) as cache:
        features = cache["features"]
        by_id = {str(fid): i for i, fid in enumerate(cache["frame_ids"])}
    result = {part: [] for part in parts}
    # Test frame features exist but no test labels or predictions enter training.
    for c in manifests(cfg):
        for part in result:
            if c["video"] in split[part]:
                x = np.stack([features[by_id[f["frame"]]] for f in c["frames"]])
                y = np.array([f["label"] for f in c["frames"]], dtype=np.int64)
                result[part].append((c["clip_id"], x, y))
    # One batch is one complete video, ordered by clip then manifest frame order.
    for part, clips in result.items():
        videos = []
        for video in split[part]:
            selected = sorted((c for c in clips if c[0].split("_")[0] == video),
                              key=lambda c: int(c[0].split("_")[1]))
            if not selected:
                raise ValueError(f"Missing video {video} in {part}")
            videos.append((video, np.concatenate([c[1] for c in selected]),
                           np.concatenate([c[2] for c in selected])))
        result[part] = videos
    return split, result


class LinearFrame(nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.head = nn.Conv1d(2048, classes, 1)

    def forward(self, x):
        return [self.head(x)]


class AggregatedTeCNO(nn.Module):
    """A output embedding followed by one local causal Transformer, without PE."""
    def __init__(self, cfg, classes):
        super().__init__()
        self.base = TeCNO(2, cfg.layers, cfg.maps, 2048, classes)
        self.embedding = nn.Linear(classes, cfg.maps)
        self.attention = nn.TransformerEncoderLayer(
            cfg.maps, 4, dim_feedforward=4 * cfg.maps, dropout=0.5, batch_first=True)
        self.head = nn.Linear(cfg.maps, classes)
        self.history = cfg.history

    def forward(self, x):
        outputs = self.base(x)
        z = self.embedding(outputs[-1].transpose(1, 2))
        positions = torch.arange(z.shape[1], device=z.device)
        distance = positions[:, None] - positions[None, :]
        mask = (distance < 0) | (distance >= self.history)
        z = self.attention(z, src_mask=mask)
        return outputs[:-1] + [self.head(z).transpose(1, 2)]


def build_model(cfg, classes):
    if cfg.candidate == "linear":
        return LinearFrame(classes)
    if cfg.candidate == "B":
        return AggregatedTeCNO(cfg, classes)
    if cfg.candidate not in ("A", "C"):
        raise ValueError(cfg.candidate)
    return TeCNO(num_stages=2, num_layers=cfg.layers, num_f_maps=cfg.maps,
                 in_dim=2048, num_classes=classes)


@torch.no_grad()
def evaluate(model, clips, device, names):
    model.eval()
    evaluator = PhaseEvaluator(num_classes=len(names), class_names=names)
    for clip_id, x, y in clips:
        pred = model(torch.from_numpy(x).T[None].to(device))[-1][0].argmax(0).cpu().numpy()
        evaluator.update(pred, y, video_id=clip_id)
    return evaluator.compute()


def train(cfg):
    splits, data = load_fold(cfg)
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    counts = np.bincount(np.concatenate([y for _, _, y in data["train"]]), minlength=len(names))
    # Inverse frequency weights use the current training fold only.
    weights = np.divide(1.0, counts, out=np.zeros(len(counts)), where=counts > 0)
    weights /= weights[weights > 0].mean()
    cfg = enrich(cfg, {"data": {"videos": splits, "class_counts": counts.tolist()},
                              "class_weights": weights.tolist(), "data_setting": "P15",
                              "receptive_field": 1 + 4 * (2 ** cfg.layers - 1),
                              "selection_metric": "phase_jaccard",
                              "cache_sha256": sha256(ROOT / cfg.cache)})
    manager = evidence(cfg, f"P15_{cfg.candidate}_L{cfg.layers}_w{cfg.smoothing_weight}"
                           f"_h{cfg.history}_fold{cfg.fold}")
    model = build_model(cfg, len(names)).to(cfg.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    warm = torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=0.5, total_iters=cfg.warmup_epochs)
    cosine = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs-cfg.warmup_epochs)
    scheduler = torch.optim.lr_scheduler.SequentialLR(optimizer, [warm, cosine], [cfg.warmup_epochs])
    ce = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=cfg.device))
    best_score, stale = -1.0, 0
    started = time.monotonic()
    best = None
    for epoch in range(1, cfg.epochs + 1):
        model.train()
        random.shuffle(data["train"])
        total = 0.0
        for _, x, y in data["train"]:
            outs = model(torch.from_numpy(x).T[None].to(cfg.device))
            labels = torch.from_numpy(y).to(cfg.device)
            loss = sum(ce(o[0].T, labels) for o in outs)
            if cfg.candidate == "C":
                for o in outs:
                    logp = F.log_softmax(o, dim=1)
                    loss = loss + cfg.smoothing_weight * F.mse_loss(
                        logp[:, :, 1:], logp[:, :, :-1].detach(), reduction="none").clamp(max=16).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total += loss.item()
        val = evaluate(model, data["val"], cfg.device, names)
        score = val["phase_jaccard"]
        tracking.log({"train/loss": total / len(data["train"]),
                      "val/jaccard": score, "val/accuracy": val["phase_accuracy"]}, step=epoch)
        print(f"epoch={epoch} val_jaccard={score:.6f} accuracy={val['phase_accuracy']:.6f}", flush=True)
        if score > best_score:
            best_score, stale = score, 0
            best = {**val, "epoch": epoch}
            torch.save({"model": model.state_dict(), "epoch": epoch}, manager.exp_dir / "checkpoints/best.pth")
        else:
            stale += 1
        scheduler.step()
        if stale >= cfg.patience:
            break
    best["elapsed_seconds"] = time.monotonic() - started
    best["epochs_completed"] = epoch
    manager.log_metrics({k: v for k, v in best.items() if isinstance(v, (int, float))})
    manager.log_per_class_ap(best["phase_per_class_jaccard"])
    manager.log_eval_recipe({"test_cfg": {"task": "phase", "backbone": "imagenet_r50_v1_frozen",
                                           "inference_protocol": "online_causal", "jaccard_mode": "strict"}})
    (manager.exp_dir / "notes.md").write_text(
        f"# Stage 1 {cfg.candidate} P15 fold {cfg.fold}\n\n"
        f"Validation-only selection; test unevaluated.\nBest epoch: {best['epoch']}\n"
        f"Jaccard: {best_score}\nElapsed seconds: {best['elapsed_seconds']}\n")
    tracking.finish()
    print(f"RUN_COMPLETE {manager.exp_dir}", flush=True)


@hydra.main(version_base=None, config_path="../configs", config_name="stage1_ptower")
def main(cfg):
    deterministic(cfg.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required by task")
    if cfg.action == "extract":
        extract(cfg)
    elif cfg.action == "train":
        train(cfg)
    else:
        raise ValueError(cfg.action)


if __name__ == "__main__":
    main()
