#!/usr/bin/env python3
"""S0 術具検出の best.pth を NMS-free (score_thr=0.0) 系で val 再評価する。

対象: Mask DINO / Co-DETR 等の DETR-family（元は locked-down score_thr=1e-8）。
仕様:
    - 元実験の ``mmdet_config.py`` を Config.fromfile で読む。
    - ``model.test_cfg`` を ``NMS_FREE_TEST_CFG`` で上書き（Co-DETR は branch 0）。
    - ``best_val_mAP_epoch_12.pth`` を load_from に指定して val 再評価。
    - 新規 ``experiments/baselines/s0_XXX_<desc>_nmsfree_seedN`` を作成し、
      metrics.json / per_class_ap.json / eval_recipe / notes.md を書き出す。
    - Notion 台帳へ log_experiment_to_notion 経由で post（NOTION_API_KEY 未設定なら no-op）。

Usage:
    python scripts/reeval_s0_nms_free.py \
        --exp-dir experiments/baselines/s0_001_maskdino_bbox_seed42
    # 複数一括
    python scripts/reeval_s0_nms_free.py \
        --exp-dir experiments/baselines/s0_001_maskdino_bbox_seed42 \
        --exp-dir experiments/baselines/s0_002_maskdino_bbox_seed123 ...
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _mutate_test_cfg(t):
    """dict / ConfigDict の test_cfg を NMS-free (score_thr=0.0) に整える。"""
    from egosurgery.utils.eval_recipe import NMS_FREE_TEST_CFG

    if t is None:
        t = {}
    t["score_thr"] = NMS_FREE_TEST_CFG["score_thr"]
    t["max_per_img"] = NMS_FREE_TEST_CFG["max_per_img"]
    # NMS 無効化。'nms' キーが残っていると mmdet PostProcess が NMS を適用する。
    if "nms" in t:
        try:
            del t["nms"]
        except Exception:
            t["nms"] = None
    if "nms_pre" in t:
        t["nms_pre"] = NMS_FREE_TEST_CFG["nms_pre"]
    return t


def apply_nms_free(mmcfg):
    tc = mmcfg.model.test_cfg
    if isinstance(tc, list) and len(tc) > 0:
        # Co-DETR: list[3] (detr / faster-rcnn / one-stage)。branch 0 が eval 支配。
        mmcfg.model.test_cfg[0] = _mutate_test_cfg(tc[0])
    else:
        mmcfg.model.test_cfg = _mutate_test_cfg(tc)
    return mmcfg


def parse_exp(exp_dir: Path):
    """例: s0_001_maskdino_bbox_seed42 → (method='maskdino', desc='maskdino_bbox', seed=42)"""
    name = exp_dir.name
    parts = name.split("_")
    if not parts[-1].startswith("seed"):
        raise ValueError(f"想定外の実験名: {name}")
    seed = int(parts[-1].replace("seed", ""))
    method_desc = "_".join(parts[2:-1])  # seq 番号(001)の後、seed の前まで
    method = method_desc.split("_")[0]
    return method, method_desc, seed


def _count_split(ann_file):
    try:
        d = json.loads(Path(ann_file).read_text(encoding="utf-8"))
        return {
            "images": len(d.get("images", [])),
            "annotations": len(d.get("annotations", [])),
        }
    except Exception:
        return {"images": 0, "annotations": 0}


def _extract_test_cfg(mmcfg):
    tc_raw = mmcfg.model.test_cfg
    tc = tc_raw[0] if isinstance(tc_raw, list) and len(tc_raw) > 0 else tc_raw
    nms = tc.get("nms") if hasattr(tc, "get") else None
    nms_iou = None
    if isinstance(nms, dict) and "iou_threshold" in nms:
        nms_iou = float(nms["iou_threshold"])
    return {
        "score_thr": float(tc.get("score_thr", 0.0)),
        "max_per_img": int(tc.get("max_per_img", 300)),
        "nms_pre": tc.get("nms_pre"),
        "nms_iou": nms_iou,
        "note": "Reeval: NMS-free (score_thr=0.0, no NMS)",
    }


def reeval_one(src_exp: Path):
    from mmengine.config import Config
    from mmengine.runner import Runner

    import egosurgery.engines.mmdet_components  # noqa: F401  register EgoCocoMetric
    from egosurgery.utils.eval_recipe import build_eval_recipe
    from egosurgery.utils.experiment_manager import ExperimentManager
    from egosurgery.utils.server_name import resolve_server_name

    method, method_desc, seed = parse_exp(src_exp)
    new_desc = f"{method_desc}_nmsfree"

    mgr = ExperimentManager(
        base_dir=str(REPO / "experiments"),
        category="baselines",
        step="s0",
        description=new_desc,
        seed=seed,
    )
    out_dir = mgr.setup(cfg=None)
    print(f"[reeval] {src_exp.name} → {out_dir.name}")

    cfg_py = src_exp / "mmdet_config.py"
    ckpt = src_exp / "best_val_mAP_epoch_12.pth"
    if not cfg_py.exists():
        raise FileNotFoundError(cfg_py)
    if not ckpt.exists():
        raise FileNotFoundError(ckpt)

    mmcfg = Config.fromfile(str(cfg_py))
    mmcfg.load_from = str(ckpt)
    mmcfg.resume = False
    mmcfg = apply_nms_free(mmcfg)

    # work_dir を新規 exp_dir 内に隔離
    work = out_dir / "mmdet_work"
    work.mkdir(parents=True, exist_ok=True)
    mmcfg.work_dir = str(work)

    # WandB カスタムフックは eval-only では不要
    if hasattr(mmcfg, "custom_hooks"):
        mmcfg.custom_hooks = [
            h for h in mmcfg.custom_hooks if h.get("type") != "EgoWandbHook"
        ]

    # eval-only では train ループを回さないため、学習時に初期化される
    # CheckpointHook (best 保存) が after_val_epoch でクラッシュする。除外する。
    if hasattr(mmcfg, "default_hooks"):
        if "checkpoint" in mmcfg.default_hooks:
            del mmcfg.default_hooks["checkpoint"]
        if mmcfg.default_hooks.get("visualization"):
            mmcfg.default_hooks["visualization"] = dict(
                type="DetVisualizationHook", draw=False
            )

    runner = Runner.from_cfg(mmcfg)
    metrics = runner.val()  # {"val/mAP": ..., "val/<Class>_precision": ...}

    per_class = {}
    scalars = {}
    for k, v in (metrics or {}).items():
        if k.startswith("val/") and k.endswith("_precision"):
            per_class[k[len("val/") : -len("_precision")]] = float(v)
        elif k in ("val/mAP", "val/mAP_50", "val/mAP_75", "val/AP_rare", "val/AP_common"):
            scalars[k] = float(v)

    split_sizes = {
        "train": _count_split(mmcfg.train_dataloader.dataset.get("ann_file")),
        "val": _count_split(mmcfg.val_evaluator.get("ann_file")),
        "test": _count_split(mmcfg.test_evaluator.get("ann_file")),
    }
    recipe = build_eval_recipe(
        test_cfg=_extract_test_cfg(mmcfg),
        split_sizes=split_sizes,
        server_name=resolve_server_name(None),
        gpu_count=1,
        effective_batch_size=1,
        lr_scaling="eval_only",
    )

    written = {
        "epoch": 0,
        "mAP": scalars.get("val/mAP", 0.0),
        "val/mAP": scalars.get("val/mAP", 0.0),
        "val/mAP_50": scalars.get("val/mAP_50", 0.0),
        "val/mAP_75": scalars.get("val/mAP_75", 0.0),
        "val/AP_rare": scalars.get("val/AP_rare", 0.0),
        "val/AP_common": scalars.get("val/AP_common", 0.0),
        "eval_recipe": recipe,
        "reeval_mode": "nms_free_score_thr_0",
        "source_exp": str(src_exp.relative_to(REPO)) if src_exp.is_relative_to(REPO) else str(src_exp),
        "source_ckpt": ckpt.name,
    }
    mgr.log_metrics(written)
    mgr.log_per_class_ap(per_class)

    notes_path = out_dir / "notes.md"
    existing = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""
    notes_path.write_text(
        existing
        + "\n\n## 再評価 (NMS-free)\n"
        + f"- 元実験: `{src_exp.name}`\n"
        + f"- source_ckpt: `{ckpt.name}`\n"
        + "- test_cfg: score_thr=0.0, nms=None, nms_pre=None (NMS_FREE_TEST_CFG)\n"
        + f"- val mAP={written['mAP']:.4f} / AP_rare={written['val/AP_rare']:.4f} / AP_common={written['val/AP_common']:.4f}\n",
        encoding="utf-8",
    )

    try:
        from egosurgery.utils.notion_logger import log_experiment_to_notion

        log_experiment_to_notion(out_dir, status="completed")
    except Exception as e:  # noqa: BLE001
        print(f"[reeval] Notion post skipped: {e}")

    print(
        f"[reeval] {out_dir.name} "
        f"mAP={written['mAP']:.4f} AP50={written['val/mAP_50']:.4f} "
        f"AP_rare={written['val/AP_rare']:.4f} AP_common={written['val/AP_common']:.4f}"
    )
    return out_dir, written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--exp-dir", type=Path, action="append", required=True,
                    help="元実験ディレクトリ (複数可)")
    args = ap.parse_args()
    for exp in args.exp_dir:
        exp = exp.resolve()
        if not exp.is_dir():
            print(f"[reeval] SKIP: not a directory: {exp}")
            continue
        reeval_one(exp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
