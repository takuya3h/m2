#!/usr/bin/env python3
"""post_process_dac_detr.py — DAC-DETR (standalone Deformable-DETR系) の
work_dir を EgoSurgery 標準証跡へ変換する。

DAC-DETR は output_dir に:
  - log.txt          : JSONL (1行1epoch)。eval は "test_coco_eval_bbox" = pycocotools
                       12 統計 [AP, AP50, AP75, APs, APm, APl, AR1, AR10, AR100, ...]。
                       全て 0-1 スケール (mmdet 系と同じ。detrex の 0-100 とは異なる)。
  - per_class_ap_egosurgery.json : engine.evaluate が COCOeval.precision から抽出した
                       {クラス名: AP(0-1)} (val に存在しないクラスは NaN)。

overall(mAP/50/75) と per-class AP は **同一 (最終) epoch** の COCOeval から取得し
整合させる。AP_rare/AP_common は val 非存在クラス(NaN)を除外して平均する
(他検出器の post_process と同一規約)。

生成物: config.yaml / command.sh / git_commit.txt / metrics.json /
per_class_ap.json / notes.md / server.txt / visualizations/confusion_matrix.npy。

Usage:
  python scripts/post_process_dac_detr.py \
      --work-dir /tmp/dac_work_seed42 \
      --exp-dir experiments/baselines/s0_037_dacdetr_bbox_seed42 \
      --command-sh "<cmd>" --seed 42 --description dacdetr_bbox \
      --detector "DAC-DETR" --world-size 2 --server-name philip
"""
from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from egosurgery.datasets.constants import RARE_CLASSES, TOOL_CLASSES  # noqa: E402

CLASSES = [c["name"] for c in TOOL_CLASSES]
_RARE = set(RARE_CLASSES)


def _read_final_eval(work_dir: Path) -> dict:
    """log.txt (JSONL) の最終 eval 行から overall AP/AP50/AP75 と epoch を返す。
    per_class_ap_egosurgery.json は eval 毎に上書きされ最終 epoch を保持するため、
    overall も最終 epoch に揃える (overall と per-class を同一 checkpoint に固定)。"""
    lp = work_dir / "log.txt"
    last = None
    if lp.exists():
        for line in lp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "test_coco_eval_bbox" in d:
                last = d
    if last is None:
        return {"mAP": float("nan"), "mAP_50": float("nan"),
                "mAP_75": float("nan"), "epoch": 0}
    ce = last["test_coco_eval_bbox"]
    return {
        "mAP": float(ce[0]),
        "mAP_50": float(ce[1]),
        "mAP_75": float(ce[2]),
        "epoch": int(last.get("epoch", 0)),
    }


def _read_per_class(work_dir: Path) -> dict:
    """engine.evaluate が dump した {クラス名: AP} を読む。欠損クラスは NaN。"""
    pp = work_dir / "per_class_ap_egosurgery.json"
    per_class = {c: float("nan") for c in CLASSES}
    if pp.exists():
        raw = json.loads(pp.read_text(encoding="utf-8"))
        for name, ap in raw.items():
            if name in per_class:
                per_class[name] = float(ap) if ap is not None else float("nan")
    return per_class


def _aggregate_ap(per_class: dict) -> tuple[float, float]:
    """AP_rare / AP_common。val に存在しないクラス (AP=NaN) は除外して平均する
    (除外しないと NaN 汚染で Δ 比較が不能になる)。"""
    rare_vals = [per_class[c] for c in RARE_CLASSES
                 if c in per_class and not math.isnan(per_class[c])]
    common_vals = [per_class[c] for c in CLASSES
                   if c not in _RARE and not math.isnan(per_class[c])]
    AP_rare = float(np.mean(rare_vals)) if rare_vals else float("nan")
    AP_common = float(np.mean(common_vals)) if common_vals else float("nan")
    return AP_rare, AP_common


def _build_eval_recipe(seed: int, world_size: int, server_name: str) -> dict:
    return {
        "framework": "dac_detr_deformable_standalone",
        "config_name": "r50_deformplus_cdn_ice_ep12_egosurgery",
        "detector_variant": "dac_cdn_ice (DAC + CDN denoising + ICE/IoU-aware = +Align)",
        "backbone": "ResNet-50",
        "encoder_num_layers": 6,
        "decoder_num_layers": 6,
        "num_queries_one2one": 900,
        "gpu_count": int(world_size),
        "per_gpu_batch_size": 2,
        "effective_batch_size": int(world_size * 2),
        "lr": 2e-4,
        "lr_backbone": 2e-5,
        "lr_scaling": "native_2e-4 (= unified 1e-4 x linear_x2)",
        "optimizer": "AdamW",
        "weight_decay": 1e-4,
        "scheduler": "StepLR drop@11",
        "epochs": 12,
        "seed": int(seed),
        "server_name": server_name,
        "split_train_images": 9657,
        "split_val_images": 1515,
        "split_test_images": 4265,
        "eval_split": "val",
        "finetune_from": "dac_cdn_ice_r50_12ep_coco (official, COCO AP 50.9); "
                         "class_embed 91->15 reinit, bbox-only",
        "test_cfg": {"topk": 300, "note": "DETR topk (NMS-free)"},
        "rare_classes": list(RARE_CLASSES),
        "num_classes": len(CLASSES),
    }


def _save_metrics(exp_dir: Path, final_eval: dict, eval_recipe: dict,
                  per_class: dict) -> dict:
    AP_rare, AP_common = _aggregate_ap(per_class)
    metrics = {
        "val/mAP": final_eval["mAP"],
        "val/mAP_50": final_eval["mAP_50"],
        "val/mAP_75": final_eval["mAP_75"],
        "val/AP_rare": AP_rare,
        "val/AP_common": AP_common,
        "val/tool_mAP": final_eval["mAP"],
        "mAP": final_eval["mAP"],
        "best_epoch": final_eval["epoch"],
        "epoch": final_eval["epoch"] + 1,
        "eval_recipe": eval_recipe,
    }
    (exp_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, allow_nan=True)
    )
    return metrics


def _save_notes(exp_dir: Path, exp_name: str, metrics: dict) -> None:
    m = metrics
    r = m["eval_recipe"]
    notes = f"""# {exp_name}

## 仮説
DAC-DETR (Divide-And-Conquer DETR, NeurIPS 2023) を EgoSurgery-Tool に統一 recipe
で fine-tune する。auxiliary decoder (cross-attention 特化 + one-to-many 割当) により
query の object 集約が改善し、特に小型・希少術具 (Skewer/Syringe) の AP 向上を期待。
評価する構成は dac_cdn_ice = DAC + CDN(対照denoising) + ICE(IoU関連loss / align系)。

## 実験設定
- Detector: DAC-DETR / dac_cdn_ice (ResNet-50, enc6/dec6, num_queries_one2one=900)
- Epochs: 12 / per-GPU batch=2 / seed={r['seed']}
- DDP: {r['gpu_count']} GPU (RTX 6000 Ada, {r['server_name']}) → effective_bs={r['effective_batch_size']}
- Optimizer: AdamW lr={r['lr']} (backbone {r['lr_backbone']}), wd={r['weight_decay']},
  scheduler={r['scheduler']}
- 事前重み: {r['finetune_from']}
- データ split: EgoSurgery 公式 (train 9657 / val 1515 / test 4265)、評価=val、bbox-only
- 評価: pycocotools COCOeval (test_coco_eval_bbox)。per-class AP は COCOeval.precision
  から IoU0.5:0.95/area=all/maxDet=100 で抽出 (mmdet 系と同定義)

## 結果
- val mAP={m['val/mAP']:.4f}, mAP_50={m['val/mAP_50']:.4f}, mAP_75={m['val/mAP_75']:.4f}
- AP_rare={m['val/AP_rare']:.4f}, AP_common={m['val/AP_common']:.4f} (best epoch={m['best_epoch']})

## 解釈
- 他検出器 (judge #6) との Δ 比較は compare_judge6.py で集計。
- val 非存在クラス (Retractor 等) は per-class AP=NaN として rare/common 平均から除外。
"""
    (exp_dir / "notes.md").write_text(notes)


def _save_misc(exp_dir: Path, command_sh: str, server_name: str) -> None:
    (exp_dir / "command.sh").write_text(command_sh + "\n")
    (exp_dir / "server.txt").write_text(server_name + "\n")
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True
        ).strip()
        (exp_dir / "git_commit.txt").write_text(sha + "\n")
    except Exception:
        (exp_dir / "git_commit.txt").write_text("(git unavailable)\n")


def _save_config(exp_dir: Path, eval_recipe: dict) -> None:
    (exp_dir / "config.yaml").write_text(
        "# Generated by post_process_dac_detr.py\n"
        + "\n".join(f"{k}: {v}" for k, v in eval_recipe.items()
                    if not isinstance(v, (dict, list)))
        + "\n"
    )


def _build_confusion(exp_dir: Path, per_class: dict) -> None:
    vis_dir = exp_dir / "visualizations"
    vis_dir.mkdir(parents=True, exist_ok=True)
    arr = np.array([per_class[c] for c in CLASSES], dtype=np.float32)
    np.save(vis_dir / "confusion_matrix.npy", arr)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--work-dir", required=True, type=Path)
    p.add_argument("--exp-dir", required=True, type=Path)
    p.add_argument("--command-sh", required=True, type=str)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--description", default="dacdetr_bbox")
    p.add_argument("--detector", default="DAC-DETR")
    p.add_argument("--world-size", default=2, type=int)
    p.add_argument("--server-name", default=os.environ.get("SERVERNAME", "philip"))
    args = p.parse_args()

    args.exp_dir.mkdir(parents=True, exist_ok=True)
    final_eval = _read_final_eval(args.work_dir)
    per_class = _read_per_class(args.work_dir)
    eval_recipe = _build_eval_recipe(args.seed, args.world_size, args.server_name)
    eval_recipe["description"] = args.description
    metrics = _save_metrics(args.exp_dir, final_eval, eval_recipe, per_class)

    (args.exp_dir / "per_class_ap.json").write_text(
        json.dumps(per_class, indent=2, allow_nan=True)
    )
    _save_notes(args.exp_dir, args.exp_dir.name, metrics)
    _save_misc(args.exp_dir, args.command_sh, args.server_name)
    _save_config(args.exp_dir, eval_recipe)
    _build_confusion(args.exp_dir, per_class)

    print(f"[post-process-dac] OK: {args.exp_dir}")
    print(f"  mAP={metrics['val/mAP']:.4f}, AP_rare={metrics['val/AP_rare']:.4f}, "
          f"AP_common={metrics['val/AP_common']:.4f} (best epoch={metrics['best_epoch']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
