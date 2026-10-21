"""Run the unchanged phase tower with evidence and artifacts outside sync paths."""
from __future__ import annotations

import json
import math
import os
import shutil
import time
from pathlib import Path

import hydra
import stage1_ptower as base
import stage1_ptower_r3 as r3
import torch
from omegaconf import OmegaConf
from tower_search_common import (
    ANALYSIS,
    ROOT,
    TASK,
    load_point,
    optimizer_groups,
    runtime_state,
    write_json,
)


def publish(manager, destination):
    out = Path(destination) / manager.exp_id
    out.mkdir(parents=True, exist_ok=False)
    for source in manager.exp_dir.iterdir():
        if source.is_file() and source.suffix in (".json", ".yaml", ".md", ".sh", ".txt"):
            shutil.copy2(source, out / source.name)
    with (out / "notes.md").open("a") as handle:
        handle.write(f"\nArtifacts, checkpoints and raw logs: {manager.exp_dir}\n")
    return out


@hydra.main(version_base=None, config_path="../configs", config_name="stage1_ptower_r3")
def main(cfg):
    point = load_point(cfg.point_id)
    work = Path(cfg.artifact_root)
    managers = []
    original_manager = base.ExperimentManager
    adamw = torch.optim.AdamW
    original_log = base.tracking.log
    original_backbone = r3.build_backbone
    epoch_history = []
    last_log = time.monotonic()

    def observed_log(metrics, *, step=None):
        nonlocal last_log
        if any(not math.isfinite(float(v)) for v in metrics.values() if isinstance(v, (int, float))):
            raise RuntimeError("Non-finite loss or validation metric")
        now = time.monotonic()
        epoch_history.append({"epoch": step, "seconds_since_previous": now - last_log,
                              "metrics": metrics,
                              "peak_memory_bytes": torch.cuda.max_memory_allocated()})
        last_log = now
        original_log(metrics, step=step)

    def observed_backbone(classes, device, init):
        result = original_backbone(classes, device, init)
        if init == "coco":
            inventory = json.loads((ANALYSIS / "inputs_inventory.json").read_text())
            expected = next(r["count"] for r in inventory["items"] if r["item"].startswith("B5b"))
            if result[2] != expected:
                raise RuntimeError("COCO backbone initialization hash differs")
            print(f"load pretrained COCO backbone {result[1]} sha256={result[2]}", flush=True)
            write_json(work / f"{cfg.action}_initialization_rank{os.environ.get('RANK', '0')}.json",
                       {"source": result[1], "backbone_init_sha256": result[2], "matched": True})
        return result

    def manager_factory(_base, category, step, description, seed):
        manager = original_manager(work / "runs", category, step,
                                   f"{description}_point{point['point']:02d}", seed)
        managers.append(manager)
        return manager

    class RecordedAdamW(adamw):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            write_json(work / f"{cfg.action}_optimizer_rank{os.environ.get('RANK', '0')}.json",
                       {"groups": optimizer_groups(self), "point": point,
                        "initial_weight_norms": [float(sum(p.detach().double().square().sum().cpu().item()
                                                          for p in g["params"]) ** .5)
                                                 for g in self.param_groups],
                        "runtime": runtime_state(),
                        "effective_batch": int(cfg.ft_batch_size) * int(cfg.ft_accum_steps)})

    cfg = base.enrich(cfg, {"task_id": TASK, "point": point, "ft_lr": point["lr"],
                            "ft_weight_decay": point["phase_weight_decay"],
                            "ft_accum_steps": point["accum"], "step": "stage1_ptower_search"})
    base.ExperimentManager = manager_factory
    torch.optim.AdamW = RecordedAdamW
    base.tracking.log = observed_log
    r3.build_backbone = observed_backbone
    if cfg.get("control_frames", 0):
        control_manifest_source = base.manifests
        videos = base.folds()[cfg.fold]

        def limited_manifests(config):
            remaining = {"train": int(cfg.control_frames), "val": 16}
            clips = []
            for clip in control_manifest_source(config):
                for split in remaining:
                    if clip["video"] in videos[split] and remaining[split]:
                        frames = clip["frames"][:remaining[split]]
                        clips.append({**clip, "frames": frames})
                        remaining[split] -= len(frames)
            return clips
        base.manifests = limited_manifests
    # Extraction uses only train and val images; manifests retain the canonical table.
    if cfg.action == "extract":
        allowed = set(base.folds()[cfg.fold]["train"] + base.folds()[cfg.fold]["val"])
        extract_manifest_source = base.manifests
        base.manifests = lambda config: [c for c in extract_manifest_source(config) if c["video"] in allowed]
    try:
        r3.main(cfg)
    finally:
        torch.optim.AdamW = adamw
        base.ExperimentManager = original_manager
        base.tracking.log = original_log
        r3.build_backbone = original_backbone
        for manager in managers:
            if manager.exp_dir is not None:
                write_json(manager.exp_dir / "search_epoch_history.json", epoch_history)
                if not cfg.get("control_frames", 0):
                    publish(manager, ROOT / "experiments/phase1/stage1_ptower_search")
                write_json(work / f"{cfg.action}_last_run.json", {
                    "exp_id": manager.exp_id, "path": str(manager.exp_dir),
                    "config": OmegaConf.to_container(cfg, resolve=True)})


if __name__ == "__main__":
    main()
