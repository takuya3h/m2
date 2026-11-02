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

# 既定の公開先は dlsta の探索の置き場。別の契約は環境変数で置き場を分ける（既定の挙動は変えない）。
PUBLISH_DEFAULT = "experiments/phase1/stage1_ptower_search"


def publish_root():
    return ROOT / os.environ.get("TOWER_SEARCH_PHASE_PUBLISH", PUBLISH_DEFAULT)


def install_step_log(cfg, directory):
    """``TOWER_SEARCH_STEP_LOG`` があるときだけ、backbone の学習の一歩ごとの時刻を記録する。

    micro-step の入口の時刻、optimizer step の後の時刻、val の始めと終わりの時刻を書く。
    ``TOWER_SEARCH_LOSS_LOG=1`` のときだけ micro-step の損失（この rank の和）を 16 進で書く
    （値を読むと GPU と同期するため、速さを測る run では書かない）。戻り値は元に戻す関数。
    """
    import stage1_ptower_r3_dist as dist_path
    rank = os.environ.get("RANK", "0")
    path = Path(directory) / f"{cfg.action}_steps_rank{rank}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a", buffering=1)
    record_loss = os.environ.get("TOWER_SEARCH_LOSS_LOG") == "1"
    original_micro, original_predictions = dist_path.micro_step, r3.frame_predictions

    def timed_micro(*args, **kwargs):
        begin = time.monotonic()
        result = original_micro(*args, **kwargs)
        row = {"event": "micro", "t": begin}
        if record_loss:
            row["loss_hex"] = float(result).hex()
        handle.write(json.dumps(row) + "\n")
        return result

    def timed_predictions(*args, **kwargs):
        handle.write(json.dumps({"event": "val_start", "t": time.monotonic()}) + "\n")
        result = original_predictions(*args, **kwargs)
        handle.write(json.dumps({"event": "val_end", "t": time.monotonic()}) + "\n")
        return result

    dist_path.micro_step, r3.frame_predictions = timed_micro, timed_predictions

    def restore():
        dist_path.micro_step, r3.frame_predictions = original_micro, original_predictions
        handle.close()
    return handle, restore


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

        def step(self, *args, **kwargs):
            result = super().step(*args, **kwargs)
            if step_handle is not None:
                step_handle.write(json.dumps({"event": "optimizer", "t": time.monotonic()}) + "\n")
            return result

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
    step_handle, restore_step_log = None, None
    if os.environ.get("TOWER_SEARCH_STEP_LOG") and cfg.action == "finetune":
        step_handle, restore_step_log = install_step_log(cfg, os.environ["TOWER_SEARCH_STEP_LOG"])
    try:
        r3.main(cfg)
    finally:
        if restore_step_log is not None:
            restore_step_log()
        torch.optim.AdamW = adamw
        base.ExperimentManager = original_manager
        base.tracking.log = original_log
        r3.build_backbone = original_backbone
        for manager in managers:
            if manager.exp_dir is not None:
                write_json(manager.exp_dir / "search_epoch_history.json", epoch_history)
                if not cfg.get("control_frames", 0) and not cfg.get("control_only", False):
                    publish(manager, publish_root())
                write_json(work / f"{cfg.action}_last_run.json", {
                    "exp_id": manager.exp_id, "path": str(manager.exp_dir),
                    "config": OmegaConf.to_container(cfg, resolve=True)})


if __name__ == "__main__":
    main()
