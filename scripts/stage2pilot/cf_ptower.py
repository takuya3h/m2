"""Task E-2: 工程の交差適合用の塔（非公式 T-2026-10-18-stage2-pilot-folda）。

確定塔（P*-15-COCO 折り A seed 42）と同じ処方・同じ関数で、train を H1 だけ（または H2 だけ）にして学ぶ。
初期化は確定塔と同じ公開の重み（D*-COCO が出発する checkpoint の backbone）、止め方に使う val は折り A の val。

    finetune   stage1_ptower_r3.finetune をそのまま呼ぶ（折りの表の train だけを差し替える）
    extract    特徴を作る。r3.extract は test を含む全動画を通すため使わず、同じ部品（FoldFrames / build_backbone /
               _features）で train 10 本と val 2 本だけを通す。キャッシュは版管理の外（STORE）
    train      stage1_ptower.train をそのまま呼ぶ（candidate C、8 層、平滑化 0.3、履歴 30。確定塔の時間ヘッドと同じ）

    .venv/bin/python scripts/stage2pilot/cf_ptower.py --half H1 --action finetune --device cuda:0
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from omegaconf import OmegaConf
from torch import nn
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import stage1_ptower as base  # noqa: E402
import stage1_ptower_r3 as r3  # noqa: E402

from egosurgery.utils import tracking  # noqa: E402
from stage2pilot import common as C  # noqa: E402

_canonical = base.folds


def config(half, action, device, checkpoint=None):
    split = json.loads((C.ANALYSIS / "crossfit/split.json").read_text())["chosen"]
    cfg = OmegaConf.load(ROOT / "configs/stage1_ptower_20.yaml")
    cfg.pop("hydra", None)
    cfg.merge_with({
        "task_id": C.TASK_ID, "step": "stage2pilot_cf_ptower", "action": action, "data_setting": "P15",
        "fold": f"A{half}", "seed": 42, "init": "coco", "ft_lr": 0.0001, "device": device,
        "manifest_dir": "data/processed/phase_manifest",
        "cache": str(C.STORE / f"cf_ptower/{half}/all_gap.npz"), "checkpoint": checkpoint,
        "crossfit": {"half": half, "train_videos": split[half], "unofficial": C.TASK_ID},
    })
    if action == "train":
        cfg.merge_with({"candidate": "C", "layers": 8, "smoothing_weight": 0.3, "history": 30,
                        "backbone_tag": f"coco_r50_ft800_lr0.0001_cf{half}", "desc_suffix": "_coco_lr0.0001"})
    return cfg, split[half]


def install_fold(half, videos):
    """折りの表に A<半分>（train = その半分、val と test は折り A のまま）を足す。"""
    def folds():
        table = _canonical()
        table[f"A{half}"] = {"test": table["A"]["test"], "val": table["A"]["val"], "train": list(videos)}
        return table
    base.folds = folds


@torch.no_grad()
def extract(cfg):
    out = Path(cfg.cache)
    if out.exists():
        raise FileExistsError(out)
    split = C.fold_a()
    videos = sorted(split["train"] + split["val"])
    C.assert_no_test(videos, "cf_ptower.extract")
    clips = [c for part in ("train", "val")
             for c in json.loads((C.MANIFEST_DIR / f"{part}.json").read_text())["clips"]]
    names = C.phase_names()
    every = r3.FoldFrames(clips, videos, train=False)
    loader = DataLoader(every, batch_size=cfg.batch_size, shuffle=False, num_workers=cfg.workers,
                        pin_memory=cfg.get("pin_memory", True))  # nosemgrep
    ckpt = ROOT / cfg.checkpoint if not Path(cfg.checkpoint).is_absolute() else Path(cfg.checkpoint)
    state = torch.load(ckpt, map_location="cpu", weights_only=True)
    model, source, _ = r3.build_backbone(len(names), cfg.device, cfg.init)
    model.load_state_dict(state["model"])
    model.fc = nn.Identity()
    model.eval().requires_grad_(False)
    cfg = base.enrich(cfg, {"weights": source, "transform": str(r3.EVAL_TRANSFORM), "short_side": r3.SHORT_SIDE,
                            "crop": "none", "feature_dim": 2048, "best_epoch": int(state["epoch"]),
                            "checkpoint_sha256": base.sha256(ckpt), "videos_extracted": videos})
    manager = base.evidence(cfg, f"features_{cfg.init}_lr{cfg.ft_lr}_fold{cfg.fold}")
    before = time.monotonic()
    features, frame_ids = r3._features(model, loader, cfg.device)
    C.assert_no_test(frame_ids, "cf_ptower.extract")
    expected = Counter(c["video"] for c in clips if c["video"] in videos for _ in c["frames"])
    actual = Counter(C.video_of(f) for f in frame_ids)
    assert actual == expected and features.shape == (len(every), 2048) and np.isfinite(features).all()
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, frame_ids=np.asarray(frame_ids), features=features)
    report = {"task_id": C.TASK_ID, "fold": cfg.fold, "seed": cfg.seed, "checkpoint_sha256": cfg.checkpoint_sha256,
              "best_epoch": int(state["epoch"]), "feature_sha256": hashlib.sha256(features.tobytes()).hexdigest(),
              "cache_sha256": base.sha256(out), "cache_bytes": out.stat().st_size, "video_counts": dict(actual),
              "elapsed_seconds": time.monotonic() - before}
    base.write_json(out.with_suffix(".json"), report)
    base.write_json(manager.exp_dir / "feature_audit.json", report)
    manager.log_metrics({"frames": len(every), "elapsed_seconds": report["elapsed_seconds"]})
    (manager.exp_dir / "notes.md").write_text(
        f"# 非公式（{C.TASK_ID}） 工程の交差適合用の塔 {cfg.fold} の特徴\n\n"
        f"train 10 本と val 2 本だけを通した（test は通していない）。キャッシュ {out}\n")
    tracking.finish()
    print(f"EXTRACT_COMPLETE {out}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--half", required=True, choices=["H1", "H2"])
    ap.add_argument("--action", required=True, choices=["finetune", "extract", "train"])
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--checkpoint", default=None)
    a = ap.parse_args()
    cfg, videos = config(a.half, a.action, a.device, a.checkpoint)
    C.assert_no_test(videos, "cf_ptower")
    install_fold(a.half, videos)
    base.deterministic(cfg.seed)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required")
    if a.action == "finetune":
        r3.finetune(cfg)
    elif a.action == "extract":
        extract(cfg)
    else:
        base.train(cfg)


if __name__ == "__main__":
    main()
