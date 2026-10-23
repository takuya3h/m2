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


# Δ at a clip start, inside or between clips, is not in the release: kept apart from 0 and 1.
GAP_UNKNOWN = -1
# Δ fed for an unknown gap under gap_input=delta, above the largest observed Δ (254).
GAP_CAP = 256
GAP_INPUTS = {"none": 0, "flag": 1, "delta": 2}


def clip_number(clip_id):
    return int(clip_id.split("_")[1])


def sequence_info(clip_frames):
    """Per-frame clip order, Δ and clip-start flag of one video joined clip by clip.

    Δ is the manifest frame-number difference to the previous frame of the same clip.
    """
    order, delta, boundary = [], [], []
    for index, frames in enumerate(clip_frames):
        numbers = [int(f["frame"].rsplit("_", 1)[1]) for f in frames]
        order += [index] * len(numbers)
        delta += [GAP_UNKNOWN] + [b - a for a, b in zip(numbers, numbers[1:])]
        boundary += [1] + [0] * (len(numbers) - 1)
    return {"clip": np.array(order), "delta": np.array(delta), "boundary": np.array(boundary)}


def gap_summary(clips):
    """Clip count and Δ statistics over the videos joined in load_fold's clip order."""
    videos = {}
    for c in clips:
        videos.setdefault(c["video"], []).append(c)
    infos = [sequence_info([c["frames"] for c in sorted(v, key=lambda c: clip_number(c["clip_id"]))])
             for v in videos.values()]
    delta = np.concatenate([i["delta"] for i in infos])
    known = delta[delta != GAP_UNKNOWN]
    return {"videos": len(infos), "clips": sum(int(i["clip"].max()) + 1 for i in infos),
            "frames": len(delta), "pairs": len(known), "delta_one": int((known == 1).sum()),
            "delta_max": int(known.max()), "unknown": int((delta == GAP_UNKNOWN).sum()),
            "unknown_between_clips": sum(int((i["delta"][1:] == GAP_UNKNOWN).sum()) for i in infos)}


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
    manager = ExperimentManager(ROOT / "experiments", "phase1",
                                cfg.get("step", "stage1_ptower"), description, cfg.seed)
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


def load_fold(cfg, parts=("train", "val"), info=False):
    """Videos as (video, x, y); info=True appends sequence_info as a fourth element."""
    split = folds()[cfg.fold]
    cache_path = ROOT / cfg.cache
    audit = json.loads(cache_path.with_suffix(".json").read_text())
    assert sha256(cache_path) == audit["cache_sha256"]
    with np.load(cache_path) as cache:
        features = cache["features"]
        by_id = {str(fid): i for i, fid in enumerate(cache["frame_ids"])}
    result = {part: [] for part in parts}
    frames = {}
    # Test frame features exist but no test labels or predictions enter training.
    for c in manifests(cfg):
        for part in result:
            if c["video"] in split[part]:
                x = np.stack([features[by_id[f["frame"]]] for f in c["frames"]])
                y = np.array([f["label"] for f in c["frames"]], dtype=np.int64)
                result[part].append((c["clip_id"], x, y))
                frames[c["clip_id"]] = c["frames"]
    # One batch is one complete video, ordered by clip then manifest frame order.
    for part, clips in result.items():
        videos = []
        for video in split[part]:
            selected = sorted((c for c in clips if c[0].split("_")[0] == video),
                              key=lambda c: clip_number(c[0]))
            if not selected:
                raise ValueError(f"Missing video {video} in {part}")
            videos.append((video, np.concatenate([c[1] for c in selected]),
                           np.concatenate([c[2] for c in selected]))
                          + ((sequence_info([frames[c[0]] for c in selected]),) if info else ()))
        result[part] = videos
    return split, result


def input_dim(cfg):
    """2048 features plus the boundary-flag and gap-input columns when they are enabled."""
    gap = cfg.get("gap_input", "none")
    if gap not in GAP_INPUTS:
        raise ValueError(gap)
    return 2048 + int(cfg.get("boundary_flag", False)) + GAP_INPUTS[gap]


def model_input(cfg, x, info):
    """(T, 2048) features with the enabled columns appended, as a (1, C, T) tensor.

    gap_input=flag appends the unknown-Δ flag (a clip start); delta also prepends log Δ,
    with GAP_CAP standing in where Δ is unknown.
    """
    columns = [x]
    if cfg.get("boundary_flag", False):
        columns.append(info["boundary"][:, None])
    gap = cfg.get("gap_input", "none")
    if gap != "none":
        unknown = info["delta"] == GAP_UNKNOWN
        if gap == "delta":
            columns.append(np.log(np.where(unknown, GAP_CAP, info["delta"]))[:, None])
        columns.append(unknown[:, None])
    return torch.from_numpy(np.concatenate(columns, 1).astype(np.float32)).T[None]


def run_video(model, cfg, x, info, device, **kwargs):
    """Model outputs for one video; reset_at_clip runs every clip on its own."""
    if info is None:
        return model(torch.from_numpy(x).T[None].to(device), **kwargs)
    inputs = model_input(cfg, x, info).to(device)
    if not cfg.get("reset_at_clip", False):
        return model(inputs, **kwargs)
    edges = [*np.flatnonzero(info["boundary"]).tolist(), inputs.shape[2]]
    parts = [model(inputs[:, :, a:b], **kwargs) for a, b in zip(edges, edges[1:])]
    return [torch.cat(stage, 2) for stage in zip(*parts)]


class LinearFrame(nn.Module):
    def __init__(self, classes, in_dim=2048):
        super().__init__()
        self.head = nn.Conv1d(in_dim, classes, 1)

    def forward(self, x):
        return [self.head(x)]


class AggregatedTeCNO(nn.Module):
    """A output embedding followed by one local causal Transformer, without PE."""
    def __init__(self, cfg, classes):
        super().__init__()
        self.base = TeCNO(2, cfg.layers, cfg.maps, input_dim(cfg), classes)
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


class SelectiveSSM(nn.Module):
    """Candidate ssm (P-A): unidirectional Mamba layers on a maps-dim projection.

    The state runs on from the video start. ssm_selective false zeroes and freezes dt_proj,
    so Δ = softplus(dt bias) is input-independent and not learned. Mamba runs on CUDA only.
    """
    def __init__(self, cfg, classes):
        super().__init__()
        from mamba_ssm import Mamba
        layers = cfg.get("ssm_layers", 2)
        self.projection = nn.Conv1d(input_dim(cfg), cfg.maps, 1)
        self.norms = nn.ModuleList(nn.LayerNorm(cfg.maps) for _ in range(layers))
        # d_conv 4 is the Mamba default (arXiv 2312.00752), fixed by the card.
        self.layers = nn.ModuleList(
            Mamba(cfg.maps, d_state=cfg.get("ssm_state_dim", 64), d_conv=4, expand=2)
            for _ in range(layers))
        self.dropout = nn.Dropout(0.5)
        self.head = nn.Linear(cfg.maps, classes)
        if not cfg.get("ssm_selective", True):
            for layer in self.layers:
                layer.dt_proj.weight.data.zero_()
                layer.dt_proj.requires_grad_(False)

    def forward(self, x):
        z = self.projection(x).transpose(1, 2)
        for norm, layer in zip(self.norms, self.layers):
            z = z + self.dropout(layer(norm(z)))
        return [self.head(z).transpose(1, 2)]


class MemoryTeCNO(nn.Module):
    """Candidate memory (P-B): A's TCN, a GRU on its output, and an adaptive memory.

    The memory holds the last memory_len GRU states (the current one included); a causal
    attention reads it and a learned gate decides how much of the read joins the state.
    """
    def __init__(self, cfg, classes):
        super().__init__()
        self.base = TeCNO(2, cfg.layers, cfg.maps, input_dim(cfg), classes)
        self.embedding = nn.Linear(classes, cfg.maps)
        self.gru = nn.GRU(cfg.maps, cfg.maps, batch_first=True)
        self.query = nn.Linear(cfg.maps, cfg.maps)
        self.key = nn.Linear(cfg.maps, cfg.maps)
        self.value = nn.Linear(cfg.maps, cfg.maps)
        self.gate = nn.Linear(2 * cfg.maps, cfg.maps)
        self.dropout = nn.Dropout(0.5)
        self.head = nn.Linear(cfg.maps, classes)
        self.memory_len = cfg.get("memory_len", 128)

    def forward(self, x):
        outputs = self.base(x)
        h, _ = self.gru(self.embedding(outputs[-1].transpose(1, 2)))
        positions = torch.arange(h.shape[1], device=h.device)
        distance = positions[:, None] - positions[None, :]
        scores = self.query(h) @ self.key(h).transpose(1, 2) / h.shape[2] ** 0.5
        scores = scores.masked_fill((distance < 0) | (distance >= self.memory_len), float("-inf"))
        read = torch.softmax(scores, -1) @ self.value(h)
        z = h + torch.sigmoid(self.gate(torch.cat([h, read], 2))) * read
        return outputs[:-1] + [self.head(self.dropout(z)).transpose(1, 2)]


class ProgressTeCNO(TeCNO):
    """Candidate progress (P-C): A's TCN plus a per-phase progress head on stage-1 maps."""
    def __init__(self, cfg, classes):
        super().__init__(2, cfg.layers, cfg.maps, input_dim(cfg), classes)
        self.progress = nn.Conv1d(cfg.maps, classes, 1)

    def forward(self, x, with_progress=False):
        hidden = self.stage1.conv_in(x)
        for layer in self.stage1.layers:
            hidden = layer(hidden)
        out = self.stage1.conv_out(hidden)
        outputs = [out]
        for stage in self.refine_stages:
            out = stage(F.softmax(out, dim=1))
            outputs.append(out)
        if with_progress:
            return outputs + [torch.sigmoid(self.progress(hidden))]
        return outputs


def build_model(cfg, classes):
    if cfg.candidate == "linear":
        return LinearFrame(classes, input_dim(cfg))
    if cfg.candidate == "B":
        return AggregatedTeCNO(cfg, classes)
    if cfg.candidate == "ssm":
        return SelectiveSSM(cfg, classes)
    if cfg.candidate == "memory":
        return MemoryTeCNO(cfg, classes)
    if cfg.candidate == "progress":
        return ProgressTeCNO(cfg, classes)
    if cfg.candidate == "stabilize":
        # P-D keeps the head of an existing candidate; only the loss and the decoding change.
        base = cfg.get("base_candidate", "A")
        if base not in ("A", "B", "C"):
            raise ValueError(base)
        return build_model(OmegaConf.merge(cfg, {"candidate": base}), classes)
    if cfg.candidate not in ("A", "C"):
        raise ValueError(cfg.candidate)
    return TeCNO(num_stages=2, num_layers=cfg.layers, num_f_maps=cfg.maps,
                 in_dim=input_dim(cfg), num_classes=classes)


def progress_target(y):
    """Elapsed fraction 0..1 in each run of one phase over the joined video.

    A phase that continues across a clip start stays one run.
    """
    target = np.zeros(len(y), dtype=np.float32)
    starts = np.flatnonzero(np.r_[True, y[1:] != y[:-1]])
    for a, b in zip(starts, np.r_[starts[1:], len(y)]):
        target[a:b] = np.linspace(0, 1, b - a)
    return target


def transition_matrix(data, classes):
    """Allowed phase transitions (staying included) seen in the fold's train videos only."""
    allowed = np.eye(classes, dtype=bool)
    for _, _, y, *_ in data["train"]:
        allowed[y[:-1], y[1:]] = True
    return allowed


def transition_decode(scores, allowed):
    """Causal argmax over (C, T) scores that excludes phases unreachable from the previous one."""
    pred = np.empty(scores.shape[1], dtype=np.int64)
    for t in range(scores.shape[1]):
        s = scores[:, t] if t == 0 else np.where(allowed[pred[t - 1]], scores[:, t], -np.inf)
        pred[t] = s.argmax()
    return pred


def tec_weights(pred, labels, alpha, m, sigma):
    """1 + α·exp(−(t−s)²/2σ²) on the first m frames of each wrong run starting at s, else 1."""
    wrong = (pred != labels).cpu().numpy()
    weights = np.ones(len(wrong), dtype=np.float32)
    start = None
    for t, miss in enumerate(wrong):
        start = (t if start is None else start) if miss else None
        if miss and t - start < m:
            weights[t] = 1 + alpha * np.exp(-(t - start) ** 2 / (2 * sigma ** 2))
    return torch.from_numpy(weights).to(labels.device)


def tec_loss(logits, labels, class_weights, alpha, m, sigma):
    """Class-weighted CE on (T, C) logits with TEC frame weights; α 0 is the plain weighted CE."""
    per_frame = F.cross_entropy(logits, labels, weight=class_weights, reduction="none")
    weights = tec_weights(logits.detach().argmax(1), labels, alpha, m, sigma)
    return (weights * per_frame).sum() / class_weights[labels].sum()


def egtp(prob, k, starts=()):
    """EGTP-style causal state over (C, T) probabilities, which are returned unchanged.

    Evidence for c accumulates max(0, e + p_c − p_state); the state switches to the class
    whose evidence first exceeds k. At each index in starts the state restarts from argmax.
    """
    state = np.empty(prob.shape[1], dtype=np.int64)
    restart = set(int(s) for s in starts)
    current, evidence = None, np.zeros(prob.shape[0])
    for t in range(prob.shape[1]):
        p = prob[:, t]
        if current is None or t in restart:
            current, evidence = int(p.argmax()), np.zeros(prob.shape[0])
        else:
            evidence = np.maximum(0.0, evidence + p - p[current])
            evidence[current] = 0.0
            if evidence.max() > k:
                current, evidence = int(evidence.argmax()), np.zeros(prob.shape[0])
        state[t] = current
    return prob, state


@torch.no_grad()
def evaluate(model, clips, device, names, cfg=None, decoders=None):
    """Main metrics from argmax, or decoders[""]; other decoders are reported under their key."""
    model.eval()
    decoders = decoders or {}
    evaluators = {key: PhaseEvaluator(num_classes=len(names), class_names=names)
                  for key in {"", *decoders}}
    for clip_id, x, y, *info in clips:
        logits = run_video(model, cfg, x, info[0] if info else None, device)[-1][0]
        for key, evaluator in evaluators.items():
            if key in decoders:
                pred = decoders[key](logits, info[0] if info else None)
            else:
                pred = logits.argmax(0).cpu().numpy()
            evaluator.update(pred, y, video_id=clip_id)
    result = evaluators[""].compute()
    for key in decoders.keys() - {""}:
        result.update({f"{key}/{name}": value for name, value in evaluators[key].compute().items()})
    return result


NEW_CANDIDATES = ("ssm", "memory", "progress", "stabilize")


def needs_info(cfg):
    return (cfg.candidate in NEW_CANDIDATES or cfg.get("boundary_flag", False)
            or cfg.get("gap_input", "none") != "none" or cfg.get("reset_at_clip", False))


def decoders(cfg, data, classes):
    """Inference rules of the new candidates; p_t itself is never changed."""
    result = {}
    if cfg.candidate == "progress" and cfg.get("transition_prior", False):
        allowed = transition_matrix(data, classes)
        result[""] = lambda logits, info: transition_decode(logits.cpu().numpy(), allowed)
    if cfg.candidate == "stabilize" and cfg.get("egtp", False):
        reset = cfg.get("egtp_reset_at_clip", False)
        result["egtp"] = lambda logits, info: egtp(
            F.softmax(logits, 0).cpu().numpy(), cfg.egtp_k,
            np.flatnonzero(info["boundary"]) if reset else ())[1]
    return result


def train(cfg):
    splits, data = load_fold(cfg, info=needs_info(cfg))
    names = list(json.loads((ROOT / cfg.manifest_dir / "phase_vocab.json").read_text()))
    counts = np.bincount(np.concatenate([y for _, _, y, *_ in data["train"]]), minlength=len(names))
    # Inverse frequency weights use the current training fold only.
    weights = np.divide(1.0, counts, out=np.zeros(len(counts)), where=counts > 0)
    weights /= weights[weights > 0].mean()
    cfg = enrich(cfg, {"data": {"videos": splits, "class_counts": counts.tolist()},
                              "class_weights": weights.tolist(),
                              "data_setting": cfg.get("data_setting", "P15"),
                              "receptive_field": 1 + 4 * (2 ** cfg.layers - 1),
                              "selection_metric": "phase_jaccard",
                              "cache_sha256": sha256(ROOT / cfg.cache)})
    manager = evidence(cfg, f"{cfg.get('data_setting', 'P15')}_{cfg.candidate}"
                           f"_L{cfg.layers}_w{cfg.smoothing_weight}"
                           f"_h{cfg.history}_fold{cfg.fold}{cfg.get('desc_suffix', '')}")
    model = build_model(cfg, len(names)).to(cfg.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    warm = torch.optim.lr_scheduler.LinearLR(optimizer, start_factor=0.5, total_iters=cfg.warmup_epochs)
    cosine = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs-cfg.warmup_epochs)
    scheduler = torch.optim.lr_scheduler.SequentialLR(optimizer, [warm, cosine], [cfg.warmup_epochs])
    ce = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=cfg.device))
    rules = decoders(cfg, data, len(names))
    if "" in rules:
        write_json(manager.exp_dir / "transition_matrix.json",
                   transition_matrix(data, len(names)).astype(int).tolist())
    kind = cfg.get("base_candidate", "A") if cfg.candidate == "stabilize" else cfg.candidate
    progress_on = cfg.candidate == "progress"
    best_score, stale = -1.0, 0
    started = time.monotonic()
    best = None
    for epoch in range(1, cfg.epochs + 1):
        model.train()
        random.shuffle(data["train"])
        total = 0.0
        for _, x, y, *info in data["train"]:
            outs = run_video(model, cfg, x, info[0] if info else None, cfg.device,
                             **({"with_progress": True} if progress_on else {}))
            labels = torch.from_numpy(y).to(cfg.device)
            progress = outs.pop() if progress_on else None
            if cfg.get("tec_alpha", 0):
                loss = sum(tec_loss(o[0].T, labels, ce.weight, cfg.tec_alpha, cfg.get("tec_m", 8),
                                    cfg.get("tec_sigma", 1.5)) for o in outs)
            else:
                loss = sum(ce(o[0].T, labels) for o in outs)
            if progress is not None and cfg.get("progress_weight", 0):
                target = torch.from_numpy(progress_target(y)).to(cfg.device)
                loss = loss + cfg.progress_weight * F.mse_loss(progress[0].gather(0, labels[None])[0],
                                                               target)
            if kind == "C":
                for o in outs:
                    logp = F.log_softmax(o, dim=1)
                    loss = loss + cfg.smoothing_weight * F.mse_loss(
                        logp[:, :, 1:], logp[:, :, :-1].detach(), reduction="none").clamp(max=16).mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            total += loss.item()
        val = evaluate(model, data["val"], cfg.device, names, cfg, rules)
        score = val["phase_jaccard"]
        tracking.log({"train/loss": total / len(data["train"]),
                      "val/jaccard": score, "val/accuracy": val["phase_accuracy"],
                      **({"val/egtp_jaccard": val["egtp/phase_jaccard"]} if "egtp" in rules else {})},
                     step=epoch)
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
    manager.log_eval_recipe({"test_cfg": {
        "task": "phase", "backbone": cfg.get("backbone_tag", "imagenet_r50_v1_frozen"),
        "inference_protocol": "online_causal", "jaccard_mode": "strict"}})
    (manager.exp_dir / "notes.md").write_text(
        f"# Stage 1 {cfg.candidate} {cfg.get('data_setting', 'P15')} fold {cfg.fold}\n\n"
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
