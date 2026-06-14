#!/usr/bin/env python3
"""post_process_detrex.py — detrex (Stable-DINO 等) の work_dir を証跡へ変換。

detectron2/detrex は output_dir に metrics.json (JSONL: 1行1イベント) を書き、
COCO 評価結果を bbox/AP, bbox/AP50, bbox/AP75, bbox/AP-<クラス名> として記録する。
本スクリプトはそれを EgoSurgery 標準証跡 (config.yaml / command.sh / git_commit.txt /
metrics.json / per_class_ap.json / notes.md / server.txt) に変換する。

重要な単位変換: detectron2 の COCO AP は 0-100 スケール。他検出器 (mmdet) は 0-1 で
metrics.json に保存しているので、Δ 比較の整合のため /100 して 0-1 に揃える。

完了後に Notion 台帳投稿 + Slack seed 通知を行う (失敗しても証跡は壊さない)。

Usage:
  python scripts/post_process_detrex.py \
      --work-dir /tmp/stabledino_work_seed42 \
      --exp-dir experiments/baselines/s0_019_stabledino_bbox_seed42 \
      --command-sh "<cmd>" --seed 42 --description stabledino_bbox \
      --detector "Stable-DINO" --world-size 2 --server-name philip
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from egosurgery.datasets.constants import RARE_CLASSES, TOOL_CLASSES  # noqa: E402

CLASSES = [c["name"] for c in TOOL_CLASSES]
_RARE = set(RARE_CLASSES)


def _load_eval_rows(work_dir: Path) -> list[dict]:
    """metrics.json (JSONL) から bbox/AP を含む eval 行を返す。"""
    mp = work_dir / "metrics.json"
    rows = []
    if not mp.exists():
        return rows
    for line in mp.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "bbox/AP" in d:
            rows.append(d)
    return rows


def _best_eval(rows: list[dict]) -> tuple[dict, int]:
    """bbox/AP 最大の eval 行と、その index(=eval回数, 1始まり)を返す。"""
    if not rows:
        return {}, 0
    best_i = max(range(len(rows)), key=lambda i: rows[i].get("bbox/AP", 0.0))
    return rows[best_i], best_i + 1


def _to_unit(v) -> float:
    """detectron2 の 0-100 AP を 0-1 に変換 (None は 0.0)。"""
    try:
        return round(float(v) / 100.0, 6)
    except (TypeError, ValueError):
        return 0.0


def _build_per_class_ap(best: dict) -> dict:
    """bbox/AP-<クラス名> を 0-1 の per-class dict に変換。"""
    out = {}
    for cls in CLASSES:
        key = f"bbox/AP-{cls}"
        if key in best:
            out[cls] = _to_unit(best[key])
    return out


def _split_rare_common(per_class: dict) -> tuple[float, float]:
    """rare/common の平均 AP。val に存在しないクラス (AP=NaN) は除外して平均する。

    DDQ 等の mmdet 系 (stage_a_trainer) と集計を揃えるため NaN を除外する
    (例: Retractor は val アノテーション無しで AP=NaN。これを平均に含めると
    AP_common 全体が NaN に汚染され、検出器間の Δ 比較が不能になる)。
    """
    import math

    def _avg(vals):
        clean = [v for v in vals if isinstance(v, (int, float)) and not math.isnan(v)]
        return round(sum(clean) / len(clean), 6) if clean else 0.0

    rare = [v for k, v in per_class.items() if k in _RARE]
    common = [v for k, v in per_class.items() if k not in _RARE]
    return _avg(rare), _avg(common)


def _build_eval_recipe(seed: int, world_size: int, server_name: str) -> dict:
    """他検出器と同形式の eval_recipe。detrex は topk(NMS-free)・max_per_img=300。"""
    return {
        "effective_batch_size": 2 * world_size,
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
            # detrex DINO は topk 方式 (NMS-free)。score_thr 相当なし、
            # max_per_img = select_box_nums_for_evaluation = 300。
            "score_thr": 0.0,
            "max_per_img": 300,
            "nms_pre": None,
            "nms_iou": None,
            "note": "DINO topk (NMS-free), select_box_nums=300",
        },
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--work-dir", required=True, type=Path)
    p.add_argument("--exp-dir", required=True, type=Path)
    p.add_argument("--command-sh", required=True)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--description", default="stabledino_bbox")
    p.add_argument("--detector", default="Stable-DINO")
    p.add_argument("--world-size", default=2, type=int)
    p.add_argument("--server-name", default=os.environ.get("SERVERNAME", "philip"))
    args = p.parse_args()

    args.exp_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_eval_rows(args.work_dir)
    best, best_eval_idx = _best_eval(rows)
    if not best:
        print(f"[post-process-detrex] WARN: eval 行が無い ({args.work_dir}/metrics.json)")
    per_class = _build_per_class_ap(best)
    ap_rare, ap_common = _split_rare_common(per_class)
    eval_recipe = _build_eval_recipe(args.seed, args.world_size, args.server_name)
    eval_recipe["description"] = args.description

    metrics = {
        "epoch": best_eval_idx,  # eval は 1 epoch ごとなので eval回数=epoch
        "mAP": _to_unit(best.get("bbox/AP")),
        "val/mAP": _to_unit(best.get("bbox/AP")),
        "val/mAP_50": _to_unit(best.get("bbox/AP50")),
        "val/mAP_75": _to_unit(best.get("bbox/AP75")),
        "val/AP_rare": ap_rare,
        "val/AP_common": ap_common,
        "eval_recipe": eval_recipe,
    }

    def _dump(path: Path, obj):
        path.write_text(
            json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    _dump(args.exp_dir / "metrics.json", metrics)
    _dump(args.exp_dir / "per_class_ap.json", per_class)

    (args.exp_dir / "command.sh").write_text(
        "#!/usr/bin/env bash\n# Stable-DINO (detrex) 実行コマンド\n"
        f"# seed={args.seed}\n{args.command_sh}\n",
        encoding="utf-8",
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
        f"検出器: {args.detector} (detrex, torch 2.1.2+cu118, .venv-detectron2)\n"
        f"seed: {args.seed}\n\n## 結果\n"
        f"mAP={metrics['val/mAP']:.4f} / AP_rare={ap_rare:.4f} / "
        f"AP_common={ap_common:.4f} (best eval #{best_eval_idx})\n\n"
        f"## 初期化\nDINO R50 COCO 12ep 重み (backbone+transformer)、"
        f"class_embed は 80->15 で再初期化 (他検出器の COCO fine-tune と同条件)。\n",
        encoding="utf-8",
    )
    src_cfg = args.work_dir / "config.yaml"
    if src_cfg.exists():
        shutil.copy(src_cfg, args.exp_dir / "config.yaml")

    # detrex は wandb を work_dir/wandb/run-<ts>-<id> に置く (mmdet は exp_dir 直下)。
    # notify_experiment.py は exp_dir/wandb を見るので、run_id を wandb_run.txt に
    # 橋渡しして検出器差を吸収する。
    _bridge_wandb_run_id(args.work_dir, args.exp_dir)

    print(f"[post-process-detrex] OK: {args.exp_dir}")
    print(f"  mAP={metrics['val/mAP']:.4f}, AP_rare={ap_rare:.4f}, "
          f"AP_common={ap_common:.4f} (best eval #{best_eval_idx})")

    _load_dotenv(REPO_ROOT / ".env")

    try:
        from egosurgery.utils.notion_logger import log_experiment_to_notion
        resp = log_experiment_to_notion(
            args.exp_dir, status="completed", step="S0", tier="must"
        )
        print(f"[post-process-detrex] Notion: {'投稿済' if resp else 'スキップ'}")
    except Exception as exc:  # noqa: BLE001
        print(f"[post-process-detrex] Notion 例外 (無視): {exc}")

    try:
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "notify_experiment.py"),
             "--mode", "seed", "--dirs", str(args.exp_dir),
             "--detector", args.detector],
            timeout=60, check=False,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[post-process-detrex] Slack 例外 (無視): {exc}")

    return 0


def _bridge_wandb_run_id(work_dir: Path, exp_dir: Path) -> None:
    """work_dir/wandb/run-<ts>-<id> から run_id を exp_dir/wandb_run.txt に書く。

    detrex の wandb 出力場所 (work_dir) と notify が見る場所 (exp_dir) の差を吸収。
    """
    import re

    wandb_root = work_dir / "wandb"
    if not wandb_root.is_dir():
        return
    runs = sorted(
        d for d in wandb_root.iterdir()
        if d.is_dir() and re.match(r"run-\d{8}_\d{6}-\w+", d.name)
    )
    if not runs:
        return
    m = re.search(r"run-\d{8}_\d{6}-(\w+)", runs[-1].name)
    if m:
        (exp_dir / "wandb_run.txt").write_text(m.group(1) + "\n", encoding="utf-8")


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
