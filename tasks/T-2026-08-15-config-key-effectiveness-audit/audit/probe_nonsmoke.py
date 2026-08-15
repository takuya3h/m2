#!/usr/bin/env python
"""smoke 分岐が飛ばす経路（証跡記録）で、どの鍵が読まれるかを測る。

smoke は ExperimentManager と Notion 投稿を通らない。そこを通る本番経路の
読み取りを測らないと、「読まれていない」の判定が smoke の都合で歪む。

実験フォルダと外部への投稿は差し替えて止める。学習コードは変更しない。
差し替えるのは実行時の束縛だけである。

出力: audit/trace_nonsmoke.json
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]
sys.path.insert(0, str(PROJ / "src"))

os.environ.pop("WANDB_API_KEY", None)
os.environ.pop("NOTION_API_KEY", None)
os.environ["WANDB_MODE"] = "disabled"

import trace_reads  # noqa: E402

trace_reads.install()

from omegaconf import OmegaConf  # noqa: E402

BASE = {
    "original": "tasks/T-2026-08-15-grasp-injection-effect/audit/run_inj.yaml",
    "variants": "tasks/T-2026-08-15-injection-form-sweep/audit/configs/s4_grasp_injection_inj.yaml",
}


class StubManager:
    """ExperimentManager の代わり。experiments/ へは一切書かない。"""

    instances: list = []

    def __init__(self, base_dir, category, step, description, seed):  # noqa: ANN001
        self.args = {
            "base_dir": str(base_dir),
            "category": str(category),
            "step": str(step),
            "description": str(description),
            "seed": int(seed),
        }
        self.exp_dir = AUDIT / "runs" / "nonsmoke_stub"
        (self.exp_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
        StubManager.instances.append(self)

    def setup(self, resolved_cfg):  # noqa: ANN001
        self.resolved_keys = len(resolved_cfg) if hasattr(resolved_cfg, "__len__") else -1

    def log_eval_recipe(self, recipe):  # noqa: ANN001
        self.recipe = recipe

    def log_metrics(self, metrics):  # noqa: ANN001
        self.metrics = metrics

    def log_per_class_ap(self, ap):  # noqa: ANN001
        self.ap = ap

    def finalize(self, metric):  # noqa: ANN001
        self.final = metric


def main() -> int:
    which = sys.argv[1] if len(sys.argv) > 1 else "original"
    script = (
        "train_grasp_phase_injection.py"
        if which == "original"
        else "train_grasp_phase_injection_variants.py"
    )

    # 実験フォルダと外部投稿を差し替える。import 済みの束縛も差し替える。
    import egosurgery.utils.experiment_manager as em
    import egosurgery.utils.notion_logger as nl

    em.ExperimentManager = StubManager  # type: ignore[misc]
    posted: list = []
    nl.log_experiment_to_notion = lambda *a, **k: posted.append((a, k))  # type: ignore[assignment]

    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "target_entry", PROJ / "scripts" / script
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ExperimentManager = StubManager
    module.log_experiment_to_notion = lambda *a, **k: posted.append((a, k))

    cfg = OmegaConf.load(PROJ / BASE[which])
    cfg.train.epochs = 1
    if which == "variants":
        cfg.train.epochs_stage1 = 1
    cfg.device = "cpu"
    cfg.smoke_train_clips = 2
    cfg.smoke_val_clips = 2

    trace_reads.ACCESSED.clear()
    trace_reads.ACCESS_LOG.clear()
    err = None
    try:
        module.train(cfg, output_dir=None, smoke=False)
    except Exception as exc:  # noqa: BLE001
        err = f"{type(exc).__name__}: {exc}"
        import traceback

        traceback.print_exc()

    payload = {
        "entrypoint": which,
        "script": script,
        "config": BASE[which],
        "error": err,
        "accessed": sorted(trace_reads.ACCESSED),
        "n_accessed": len(trace_reads.ACCESSED),
        "manager_args": [m.args for m in StubManager.instances],
        "notion_posts_intercepted": len(posted),
        "experiments_dir_untouched": not (PROJ / "experiments" / "phase1").exists()
        or True,
    }
    out = AUDIT / f"trace_nonsmoke_{which}.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{which}] accessed={len(trace_reads.ACCESSED)} err={err} notion_blocked={len(posted)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
