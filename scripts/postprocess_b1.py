#!/usr/bin/env python
"""B1 素朴MTL の後処理（本体 .venv）— work_dir → 証跡組成 + 工程厳密指標 + 両 eval_recipe。

train_b1_mtl.py（.venv-relation-detr）は egosurgery を import できないため、検出 mAP/per_class と
工程 frame 予測を work_dir に出す。本スクリプトは本体 .venv で:
  1. 工程 val 予測（phase_val_preds.json）に PhaseEvaluator を当て、厳密指標
     （accuracy/macro_f1/jaccard/edit/seg_f1@{10,25,50}/per_class_f1）を算出。
  2. 検出 mAP/per_class（b1_result.json）と合わせ、ExperimentManager で
     experiments/transfer/b1_mtl_{seq}_{desc}_seed{seed} に証跡を組成。
  3. 両 eval_recipe（検出 NMS-free / 工程 PHASE_EVAL_PROTOCOL）を metrics.json に併記。
両 Δ（vs S0-frozen′ / S4′）は 3-seed 揃ったあと paired-σ で別途集計する。

実行: .venv/bin/python scripts/postprocess_b1.py --work /tmp/b1_work_fixed_seed42 --weighting fixed --seed 42
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))

from egosurgery.metrics.phase import PhaseEvaluator  # noqa: E402
from egosurgery.utils.eval_recipe import (  # noqa: E402
    NMS_FREE_TEST_CFG,
    PAPER_SPLIT_SIZES,
    PHASE_EVAL_PROTOCOL,
    build_eval_recipe,
)
from egosurgery.utils.experiment_manager import ExperimentManager  # noqa: E402
from egosurgery.utils.server_name import resolve_server_name  # noqa: E402

MANIFEST_DIR = PROJ / "data/processed/phase_manifest"
VOCAB = json.loads((MANIFEST_DIR / "phase_vocab.json").read_text())
CLASS_NAMES = list(VOCAB.keys())


def phase_metrics_from_preds(preds_path: Path) -> dict:
    """保存済み val 予測（clip→{preds,labels}）に PhaseEvaluator を当てて厳密指標を返す。"""
    import numpy as np
    data = json.loads(preds_path.read_text())
    ev = PhaseEvaluator(num_classes=len(CLASS_NAMES), class_names=CLASS_NAMES)
    for clip_id, d in data.items():
        ev.update(np.asarray(d["preds"]), np.asarray(d["labels"]), video_id=clip_id)
    return ev.compute()


def build_recipes(server: str) -> tuple[dict, dict]:
    """検出（NMS-free）と工程（PHASE_EVAL_PROTOCOL）の eval_recipe。B1 の実構成を記録。

    B1 は単GPU。検出 eff_bs=2（det batch=2）/ 工程 eff_bs=1。lr_scaling=none（lr=1e-4）。
    ※ S0-frozen′ は 2GPU/eff_bs=4 で取得されており、GPU 構成差は Δ 集計時に §8.0 で扱う。
    """
    det = build_eval_recipe(
        test_cfg={**NMS_FREE_TEST_CFG, "backbone": "relation_detr_resnet50_frozen_seed42",
                  "coupling": "b1_naive_mtl", "neck": "c5_linear_shared"},
        split_sizes=PAPER_SPLIT_SIZES, server_name=server,
        gpu_count=1, effective_batch_size=2, lr_scaling="none",
    )
    phase = build_eval_recipe(
        test_cfg={"task": "phase", **PHASE_EVAL_PROTOCOL,
                  "backbone": "relation_detr_resnet50_frozen_seed42",
                  "temporal_head": "tecno", "num_stages": 2, "num_layers": 8, "num_f_maps": 64,
                  "coupling": "b1_naive_mtl", "neck": "c5_linear_shared"},
        split_sizes=PAPER_SPLIT_SIZES, server_name=server,
        gpu_count=1, effective_batch_size=1, lr_scaling="none",
    )
    return det, phase


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", required=True, help="train_b1_mtl.py の work_dir")
    ap.add_argument("--weighting", choices=["fixed", "uncertainty"], required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--no-evidence", action="store_true")
    args = ap.parse_args()

    work = Path(args.work)
    result = json.loads((work / "b1_result.json").read_text())
    phase = phase_metrics_from_preds(work / "phase_val_preds.json")
    server = resolve_server_name(None)

    # スカラ: 検出 mAP + 工程厳密指標（per_class_f1 は別キー）。
    phase_per_class = phase.pop("phase_per_class_f1", {})
    phase.pop("phase_per_class_jaccard", None)
    scalars = {
        "mAP": result["mAP"],
        "phase_frame_acc_inline": result.get("phase_frame_acc"),
        **{k: v for k, v in phase.items() if isinstance(v, (int, float))},
    }
    if args.weighting == "uncertainty":
        scalars["sigma2_d"] = result.get("sigma2_d")
        scalars["sigma2_p"] = result.get("sigma2_p")

    print(f"[b1-post] seed={args.seed} weighting={args.weighting} "
          f"mAP={result['mAP']:.4f} phase_acc={phase['phase_accuracy']:.4f} "
          f"macroF1={phase['phase_macro_f1']:.4f} jaccard={phase['phase_jaccard']:.4f}")

    if args.no_evidence:
        return
    desc = f"b1_naive_mtl_{args.weighting}"
    mgr = ExperimentManager(base_dir=str(PROJ / "experiments"), category="transfer",
                            step="b1_mtl", description=desc, seed=args.seed)
    cfg = {
        "experiment": {"category": "transfer", "step": "b1_mtl", "description": desc},
        "seed": args.seed,
        "method": {"name": "b1_naive_mtl", "weighting": args.weighting,
                   "shared_neck": "c5_linear_2048_residual_zeroinit",
                   "frozen_backbone": "relation_detr_resnet50_seed42",
                   "det_head": "relation_detr", "phase_head": "tecno",
                   "w_det": result.get("w_det"), "w_phase": result.get("w_phase"),
                   "step_ratio_R": result.get("R"), "best_epoch": result.get("best_epoch")},
        "server_name": server,
    }
    mgr.setup(cfg)
    det_recipe, phase_recipe = build_recipes(server)
    # 両 recipe を併記（Δ 集計時に task で振り分け）。
    mgr.log_metrics({**scalars, "eval_recipe_detection": det_recipe,
                     "eval_recipe_phase": phase_recipe})
    mgr.log_per_class_ap(result.get("per_class_coco_map", {}))  # 検出 per-class（S0 慣例）
    (mgr.exp_dir / "phase_per_class_f1.json").write_text(
        json.dumps(phase_per_class, ensure_ascii=False, indent=2))
    print(f"[b1-post] evidence -> {mgr.exp_dir}")


if __name__ == "__main__":
    main()
