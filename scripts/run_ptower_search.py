"""Run the unchanged phase tower with evidence and artifacts outside sync paths."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

import hydra
import stage1_ptower as base
import stage1_ptower_r3 as r3
import torch
from omegaconf import OmegaConf
from tower_search_common import ROOT, TASK, load_point, optimizer_groups, write_json


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
                        "effective_batch": int(cfg.ft_batch_size) * int(cfg.ft_accum_steps)})

    cfg = base.enrich(cfg, {"task_id": TASK, "point": point, "ft_lr": point["lr"],
                            "ft_weight_decay": point["phase_weight_decay"],
                            "ft_accum_steps": point["accum"], "step": "stage1_ptower_search"})
    base.ExperimentManager = manager_factory
    torch.optim.AdamW = RecordedAdamW
    # Extraction uses only train and val images; manifests retain the canonical table.
    if cfg.action == "extract":
        allowed = set(base.folds()[cfg.fold]["train"] + base.folds()[cfg.fold]["val"])
        original_manifests = base.manifests
        base.manifests = lambda config: [c for c in original_manifests(config) if c["video"] in allowed]
    try:
        r3.main(cfg)
    finally:
        torch.optim.AdamW = adamw
        base.ExperimentManager = original_manager
        for manager in managers:
            if manager.exp_dir is not None:
                publish(manager, ROOT / "experiments/phase1/stage1_ptower_search")
                write_json(work / f"{cfg.action}_last_run.json", {
                    "exp_id": manager.exp_id, "path": str(manager.exp_dir),
                    "config": OmegaConf.to_container(cfg, resolve=True)})


if __name__ == "__main__":
    main()
