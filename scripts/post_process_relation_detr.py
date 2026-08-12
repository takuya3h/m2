#!/usr/bin/env python3
"""post_process_relation_detr.py — Relation-DETR (accelerate) の出力を証跡へ変換。

Relation-DETR は accelerate ベースで、train dir に training.log (COCO summary) と
engine.py 改修で書き出す per_class_coco_map/epoch_*.json を残す。本スクリプトは
それらを EgoSurgery 標準証跡 (metrics.json / per_class_ap.json / command.sh /
git_commit.txt / notes.md / server.txt) に変換する。

単位: Relation-DETR/pycocotools の AP は 0-1 スケール (他検出器 mmdet と同じ)。
他検出器との Δ 比較整合のため per-class は COCO mAP(IoU=0.50:0.95) を使う
(engine.py で precision[:,...].mean() として出力済み)。
val 非存在クラス (Retractor 等, AP=NaN/-1) は AP_rare/common 平均から除外する。

best epoch は per_class_coco_map/epoch_*.json の overall_coco_mAP 最大で選ぶ。

完了後に Notion 台帳投稿 + Slack seed 通知 (失敗しても証跡を壊さない)。

Usage:
  python scripts/post_process_relation_detr.py \
      --train-dir <Relation-DETR checkpoints/.../train/YYYY-...> \
      --exp-dir experiments/baselines/s0_016_relationdetr_bbox_seed42 \
      --command-sh "<cmd>" --seed 42 --description relationdetr_bbox \
      --detector "Relation-DETR" --world-size 2 --server-name philip
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from egosurgery.datasets.constants import RARE_CLASSES, TOOL_CLASSES  # noqa: E402

CLASSES = [c["name"] for c in TOOL_CLASSES]
_RARE = set(RARE_CLASSES)


def _best_per_class(train_dir: Path) -> tuple[dict, int, float]:
    """per_class_coco_map/epoch_*.json から overall_coco_mAP 最大の epoch を選ぶ。

    Returns: (per_class dict, best_epoch, overall_mAP)
    """
    files = sorted(glob.glob(str(train_dir / "per_class_coco_map" / "epoch_*.json")))
    best, best_ep, best_map = {}, 0, -1.0
    for f in files:
        try:
            d = json.loads(Path(f).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        m = d.get("overall_coco_mAP", -1.0)
        if m > best_map:
            best_map = m
            best_ep = int(d.get("epoch", 0)) + 1  # epoch は 0始まり → 1始まりへ
            best = d.get("per_class_coco_map", {})
    return best, best_ep, best_map


def _parse_summary_from_log(train_dir: Path) -> dict:
    """training.log の COCO summary 行から overall AP/AP50/AP75 を取る (best不問の最終)。

    per_class_coco_map が無い場合のフォールバック用。0-1 スケール。
    """
    out = {}
    log = train_dir / "training.log"
    if not log.exists():
        return out
    import re

    text = log.read_text(encoding="utf-8", errors="ignore")
    # "Average Precision  (AP) @[ IoU=0.50:0.95 | area=   all | maxDets=100 ] = 0.577"
    m = re.findall(r"IoU=0\.50:0\.95 \| area=   all \| maxDets=100 \] = ([0-9.]+)", text)
    if m:
        out["mAP"] = float(m[-1])
    m50 = re.findall(r"IoU=0\.50      \| area=   all \| maxDets=100 \] = ([0-9.]+)", text)
    if m50:
        out["mAP_50"] = float(m50[-1])
    m75 = re.findall(r"IoU=0\.75      \| area=   all \| maxDets=100 \] = ([0-9.]+)", text)
    if m75:
        out["mAP_75"] = float(m75[-1])
    return out


def _avg_excl_nan(vals: list[float]) -> float:
    clean = [v for v in vals if isinstance(v, (int, float)) and not math.isnan(v) and v >= 0]
    return round(sum(clean) / len(clean), 6) if clean else 0.0


def _build_eval_recipe(
    seed: int, world_size: int, server_name: str, per_process_batch_size: int
) -> dict:
    return {
        "effective_batch_size": per_process_batch_size * world_size,
        "gpu_count": world_size,
        "lr_scaling": "linear_x2",
        "server_name": server_name,
        "split_train_images": 9657,
        "split_val_images": 1515,
        "split_test_images": 4265,
        "split_train_annotations": 32272,
        "split_val_annotations": 4707,
        "split_test_annotations": 12673,
        "test_cfg": {
            # Relation-DETR は NMS-free (topk)。PostProcess(select_box_nums=300)。
            "score_thr": 0.0,
            "max_per_img": 300,
            "nms_pre": None,
            "nms_iou": None,
            "note": "Relation-DETR topk (NMS-free), select_box_nums=300",
        },
    }


def _dump(path: Path, obj):
    path.write_text(
        json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--train-dir", required=True, type=Path)
    p.add_argument("--exp-dir", required=True, type=Path)
    p.add_argument("--command-sh", required=True)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--description", default="relationdetr_bbox")
    p.add_argument("--detector", default="Relation-DETR")
    p.add_argument("--world-size", default=2, type=int)
    p.add_argument("--per-process-batch-size", default=2, type=int)
    p.add_argument("--server-name", default=os.environ.get("SERVERNAME", "philip"))
    p.add_argument("--step", default="S0")
    p.add_argument("--init-note", default=(
        "Relation-DETR R50 COCO 1x 重み (backbone+transformer)、"
        "class head は 91->15 で再初期化 (他検出器の COCO fine-tune と同条件)。"
    ))
    p.add_argument("--skip-external-loggers", action="store_true")
    args = p.parse_args()

    args.exp_dir.mkdir(parents=True, exist_ok=True)

    per_class, best_ep, best_map = _best_per_class(args.train_dir)
    summary = _parse_summary_from_log(args.train_dir)

    # per-class が取れていれば AP_rare/common を計算。
    ap_rare = _avg_excl_nan([v for k, v in per_class.items() if k in _RARE])
    ap_common = _avg_excl_nan([v for k, v in per_class.items() if k not in _RARE])

    # overall mAP: per_class_coco_map の best を最優先、無ければ log summary。
    overall_map = best_map if best_map >= 0 else summary.get("mAP", 0.0)

    metrics = {
        "epoch": best_ep if best_ep else None,
        "mAP": round(overall_map, 6),
        "val/mAP": round(overall_map, 6),
        "val/mAP_50": round(summary.get("mAP_50", 0.0), 6),
        "val/mAP_75": round(summary.get("mAP_75", 0.0), 6),
        "val/AP_rare": ap_rare,
        "val/AP_common": ap_common,
        "eval_recipe": _build_eval_recipe(
            args.seed, args.world_size, args.server_name, args.per_process_batch_size
        ),
    }
    metrics["eval_recipe"]["description"] = args.description

    _dump(args.exp_dir / "metrics.json", metrics)
    # per_class は NaN 維持 (検証/比較で他検出器と同形式: val非存在は NaN)。
    pc_out = {c: (per_class.get(c, float("nan"))) for c in CLASSES}
    _dump(args.exp_dir / "per_class_ap.json", pc_out)

    (args.exp_dir / "command.sh").write_text(
        "#!/usr/bin/env bash\n# Relation-DETR (accelerate) 実行コマンド\n"
        f"# seed={args.seed}\n{args.command_sh}\n", encoding="utf-8",
    )
    try:
        commit = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        ).stdout.strip()
    except Exception:  # noqa: BLE001
        commit = "unknown"
    (args.exp_dir / "git_commit.txt").write_text(commit + "\n", encoding="utf-8")
    (args.exp_dir / "server.txt").write_text(args.server_name + "\n", encoding="utf-8")
    (args.exp_dir / "notes.md").write_text(
        f"# {args.exp_dir.name}\n\n"
        f"検出器: {args.detector} (accelerate, torch 2.1.2+cu118, .venv-relation-detr)\n"
        f"seed: {args.seed}\n\n## 結果\n"
        f"mAP={metrics['val/mAP']:.4f} / AP_rare={ap_rare:.4f} / "
        f"AP_common={ap_common:.4f} (best epoch {best_ep})\n\n"
        f"## per-class AP\nCOCO mAP(0.50:0.95)。engine.py 改修で precision 全 IoU 平均を出力。\n"
        f"Retractor 等 val 非存在クラスは NaN (AP_rare/common 平均から除外)。\n\n"
        f"## 初期化\n{args.init_note}\n\n"
        f"## tracking\nTensorBoard (train dir/tf_log)。wandb は未使用。\n",
        encoding="utf-8",
    )

    print(f"[post-process-reldetr] OK: {args.exp_dir}")
    print(f"  mAP={metrics['val/mAP']:.4f}, AP_rare={ap_rare:.4f}, "
          f"AP_common={ap_common:.4f} (best epoch {best_ep})")

    if not args.skip_external_loggers:
        _load_dotenv(REPO_ROOT / ".env")
        try:
            from egosurgery.utils.notion_logger import log_experiment_to_notion
            resp = log_experiment_to_notion(
                args.exp_dir, status="completed", step=args.step, tier="must"
            )
            print(f"[post-process-reldetr] Notion: {'投稿済' if resp else 'スキップ'}")
        except Exception as exc:  # noqa: BLE001
            print(f"[post-process-reldetr] Notion 例外 (無視): {exc}")

        try:
            subprocess.run(
                [sys.executable, str(REPO_ROOT / "scripts" / "notify_experiment.py"),
                 "--mode", "seed", "--dirs", str(args.exp_dir),
                 "--detector", args.detector],
                timeout=60, check=False,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[post-process-reldetr] Slack 例外 (無視): {exc}")
    else:
        print("[post-process-reldetr] external loggers skipped")

    return 0


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


if __name__ == "__main__":
    raise SystemExit(main())
