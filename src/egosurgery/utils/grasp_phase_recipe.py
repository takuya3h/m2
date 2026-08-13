"""Evaluation recipe for grasp-inference phase models.

Grasp inference and control/injection selection are deliberately excluded from
``test_cfg``.  They are experimental-arm settings, not phase evaluation
conditions, so baseline comparability remains governed by the existing S4
online-causal and strict-Jaccard keys.
"""

from __future__ import annotations

from egosurgery.utils.eval_recipe import (
    PAPER_SPLIT_SIZES,
    PHASE_EVAL_PROTOCOL,
    build_eval_recipe,
)


def build_grasp_phase_recipe(cfg, server_name: str) -> dict:
    """Build an S4-compatible recipe from a dict or ``DictConfig``."""
    model_cfg = cfg.get("model", {})
    temporal_cfg = model_cfg.get("temporal", {})
    test_cfg = {
        "task": "phase",
        **PHASE_EVAL_PROTOCOL,
        "backbone": "relation_detr_resnet50_frozen_seed42",
        "temporal_head": "tecno",
        "num_stages": int(temporal_cfg.get("num_stages", 2)),
        "num_layers": int(temporal_cfg.get("num_layers", 8)),
        "num_f_maps": int(temporal_cfg.get("num_f_maps", 64)),
    }
    return build_eval_recipe(
        test_cfg=test_cfg,
        split_sizes=PAPER_SPLIT_SIZES,
        server_name=server_name,
        gpu_count=1,
        effective_batch_size=1,
        lr_scaling="none",
    )
