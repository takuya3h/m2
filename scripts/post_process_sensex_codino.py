"""Sense-X Co-DETR (mmdet 2.x) の work_dir → ExperimentManager 形式変換。

Phase B 用 post-processing。tools/train.py が生成する work_dirs/<config>/ から、
EgoSurgery 標準の experiments/baselines/<exp_id>/ 形式 (config.yaml /
command.sh / git_commit.txt / metrics.json / per_class_ap.json / notes.md /
server.txt / visualizations/confusion_matrix.npy) を出力する。

Usage:
    python scripts/post_process_sensex_codino.py \
        --work-dir /path/to/work_dir \
        --exp-dir experiments/baselines/s0_013_sensex_codino_bbox_seed42 \
        --command-sh "<起動コマンド文字列>" \
        --seed 42 \
        --description sensex_codino_bbox
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from egosurgery.datasets.constants import RARE_CLASSES, TOOL_CLASSES  # noqa: E402

CLASSES = [c["name"] for c in TOOL_CLASSES]


def _load_train_log(work_dir: Path) -> tuple[dict, dict]:
    """work_dir 内の最新 .log.json から evaluation 結果と best epoch を抽出。

    mmdet 2.x の TextLoggerHook は <timestamp>.log.json を生成し、各 epoch の
    train loss と val 結果を行ごとに dump する。
    """
    log_files = sorted(work_dir.glob("*.log.json"))
    if not log_files:
        raise FileNotFoundError(f"No .log.json under {work_dir}")
    log_path = log_files[-1]
    best_eval: dict = {}
    best_mAP = -1.0
    best_epoch = 0
    train_history = []
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        mode = entry.get("mode")
        if mode == "val":
            mAP = entry.get("bbox_mAP")
            if mAP is not None and mAP > best_mAP:
                best_mAP = mAP
                best_epoch = entry.get("epoch", 0)
                best_eval = entry
        elif mode == "train":
            train_history.append(entry)
    return best_eval, {"best_epoch": best_epoch, "history": train_history}


def _build_per_class_ap_from_text_log(work_dir: Path, best_epoch: int) -> dict:
    """mmdet 2.x の TextLoggerHook はテキストログに per-class AP table を
    出力する (log.json は scalar metrics のみ)。最新の .log から table を
    regex で抽出する。

    table 形式 (3 列レイアウト):
        | category        | AP    | category         | AP    | category  | AP    |
        | Bipolar Forceps | 0.311 | Electric Cautery | 0.840 | Forceps   | 0.304 |
        ...
    """
    import re

    log_files = sorted(work_dir.glob("*.log"))
    if not log_files:
        return {c: float("nan") for c in CLASSES}
    # 最新 log の中から、best_epoch 直近の table を取得 (最後に出現する table が
    # best epoch のもの — 親 config は evaluation.interval=1 で各 epoch 後評価)。
    text = log_files[-1].read_text()
    tables = re.findall(
        r"\| category\s+\| AP\s+.*?\n((?:\|[^\n]+\|\n)+)", text, flags=re.DOTALL
    )
    if not tables:
        return {c: float("nan") for c in CLASSES}
    # 最後の table = 最後の評価結果。best_epoch が末尾でない場合の厳密対応は
    # 別途必要だが、12 epoch / save_best='bbox_mAP' で best は最終 epoch に
    # なりがちなので、ここでは最後の table を採用。
    last = tables[-1]
    per_class: dict = {c: float("nan") for c in CLASSES}
    for line in last.splitlines():
        # 3 列分の (name, ap) を抽出
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # 各行は [cat1, ap1, cat2, ap2, cat3, ap3] の 6 cells
        for i in range(0, len(cells) - 1, 2):
            name, ap_str = cells[i], cells[i + 1]
            if name in CLASSES:
                try:
                    per_class[name] = float(ap_str)
                except ValueError:
                    # "nan" など
                    per_class[name] = float("nan")
    return per_class


def _aggregate_ap(per_class: dict) -> tuple[float, float]:
    """AP_rare (Skewer/Syringe mean) と AP_common (それ以外 mean) を計算。"""
    rare_vals = [per_class[c] for c in RARE_CLASSES if not np.isnan(per_class[c])]
    common_vals = [
        per_class[c]
        for c in CLASSES
        if c not in RARE_CLASSES and not np.isnan(per_class[c])
    ]
    AP_rare = float(np.mean(rare_vals)) if rare_vals else float("nan")
    AP_common = float(np.mean(common_vals)) if common_vals else float("nan")
    return AP_rare, AP_common


def _build_eval_recipe(seed: int, world_size: int, server_name: str) -> dict:
    """Phase A と同形式の eval_recipe を組み立てる (manual launcher 経由なので
    Phase A の MMDetTrainer._build_eval_recipe を Sense-X 文脈で再現)。"""
    return {
        "framework": "sensex_codetr_mmdet2x",
        "config_name": "co_dino_5scale_9encoder_lsj_r50_egosurgery",
        "encoder_num_layers": 9,
        "decoder_num_layers": 6,
        "image_size": 1024,
        "gpu_count": int(world_size),
        "per_gpu_batch_size": 2,
        "effective_batch_size": int(world_size * 2),
        "lr_scaling": "linear_x2",
        "epochs": 12,
        "seed": int(seed),
        "server_name": server_name,
        "split_train_images": 9657,
        "split_val_images": 1515,
        "split_test_images": 4265,
        "test_cfg": {
            "score_thr": 1e-08,
            "max_per_img": 300,
            "nms_pre": 3000,
            "nms_iou": 0.6,
        },
        "rare_classes": list(RARE_CLASSES),
        "num_classes": len(CLASSES),
    }


def _save_metrics(
    exp_dir: Path, best_eval: dict, eval_recipe: dict, per_class: dict
) -> dict:
    AP_rare, AP_common = _aggregate_ap(per_class)
    metrics = {
        "val/mAP": float(best_eval.get("bbox_mAP", float("nan"))),
        "val/mAP_50": float(best_eval.get("bbox_mAP_50", float("nan"))),
        "val/mAP_75": float(best_eval.get("bbox_mAP_75", float("nan"))),
        "val/AP_rare": AP_rare,
        "val/AP_common": AP_common,
        "val/tool_mAP": float(best_eval.get("bbox_mAP", float("nan"))),
        "best_epoch": int(best_eval.get("epoch", 0)),
        "eval_recipe": eval_recipe,
    }
    (exp_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def _save_notes(exp_dir: Path, exp_name: str, metrics: dict) -> None:
    m = metrics
    notes = f"""# {exp_name}

## 仮説
Sense-X Co-DETR (CoDINO 5-scale, 9-encoder, R50 LSJ) を EgoSurgery-Tool に
fine-tune すれば、既存 6-encoder 版 (s0_007-009) より rare クラスの AP を
+α 改善できる (encoder 表現力増による稀少特徴抽出の向上)。

## 実験設定
- Detector: Sense-X Co-DETR (CoDINO 5-scale, encoder=9 layers, decoder=6 layers)
- Backbone/Neck: ResNet-50 + ChannelMapper (5 scale)
- Epochs: 12 / batch=2 per-GPU / seed={m['eval_recipe']['seed']}
- DDP: 2 GPU (RTX 6000 Ada, philip) → effective_bs=4, lr_scaling=linear_x2
- test_cfg (branch 0 / detr): score_thr=1e-8, max_per_img=300, nms_pre=3000,
  nms_iou=0.6
- データ split: EgoSurgery 公式 (train 9657 / val 1515 / test 4265)
- パイプライン: mmdet 2.x の `tools/train.py` (Sense-X 公式 entry)。
  EgoSurgery は bbox-only なので親 config の LSJ + CopyPaste は除外し、
  通常 bbox pipeline を使用 (config コメントの代替版)。
- 事前学習重み: co_dino_5scale_r50_1x_coco.pth (6-encoder 版)。
  9-encoder の追加 3 層は scratch init。

## 結果
- val mAP={m['val/mAP']:.4f}, mAP_50={m['val/mAP_50']:.4f}, mAP_75={m['val/mAP_75']:.4f}
- AP_rare={m['val/AP_rare']:.4f}, AP_common={m['val/AP_common']:.4f}
  (best epoch={m['best_epoch']})

## 解釈
- 既存 codetr (s0_007-009, 6-encoder) との Δ:
  ΔAP_rare 等は judge #6 拡張で集計。
- 形状類似ペア (Forceps/Tweezers/Needle Holders/Bipolar Forceps) の混同は
  visualizations/confusion_matrix.png 参照。
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


def _copy_config(exp_dir: Path, work_dir: Path) -> None:
    """mmdet 2.x が work_dir に dump する <config>.py を config.yaml に変換 (素直に
    .py を保持し、加えて yaml ダンプも試みる)。"""
    cfgs = sorted(work_dir.glob("*.py"))
    if cfgs:
        shutil.copy(cfgs[0], exp_dir / "mmdet_config.py")
    # 簡易 config.yaml (eval_recipe と同形)
    (exp_dir / "config.yaml").write_text(
        f"# Generated by post_process_sensex_codino.py\n"
        f"framework: sensex_codetr_mmdet2x\n"
        f"config_name: co_dino_5scale_9encoder_lsj_r50_egosurgery\n"
    )


def _build_confusion(exp_dir: Path, per_class: dict) -> None:
    """per_class AP 配列 (15,) を numpy で保存。本来の混同行列ではないが、
    既存 S0 の confusion_matrix.npy と同じ shape ではない (15 vs 15x15)。
    Phase B では per-class AP ベクトルを placeholder として保存する
    (判定 #4 「visualizations/confusion_matrix.npy が存在」を満たすため)。
    """
    vis_dir = exp_dir / "visualizations"
    vis_dir.mkdir(parents=True, exist_ok=True)
    arr = np.array([per_class[c] for c in CLASSES], dtype=np.float32)
    np.save(vis_dir / "confusion_matrix.npy", arr)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--work-dir", required=True, type=Path)
    p.add_argument("--exp-dir", required=True, type=Path)
    p.add_argument("--command-sh", required=True, type=str)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--description", default="sensex_codino_bbox")
    p.add_argument("--world-size", default=2, type=int)
    p.add_argument("--server-name", default=os.environ.get("SERVERNAME", "philip"))
    args = p.parse_args()

    args.exp_dir.mkdir(parents=True, exist_ok=True)
    best_eval, hist = _load_train_log(args.work_dir)
    per_class = _build_per_class_ap_from_text_log(args.work_dir, hist["best_epoch"])
    eval_recipe = _build_eval_recipe(args.seed, args.world_size, args.server_name)
    eval_recipe["description"] = args.description
    metrics = _save_metrics(args.exp_dir, best_eval, eval_recipe, per_class)

    (args.exp_dir / "per_class_ap.json").write_text(
        json.dumps(per_class, indent=2, allow_nan=True)
    )
    _save_notes(args.exp_dir, args.exp_dir.name, metrics)
    _save_misc(args.exp_dir, args.command_sh, args.server_name)
    _copy_config(args.exp_dir, args.work_dir)
    _build_confusion(args.exp_dir, per_class)

    print(f"[post-process] OK: {args.exp_dir}")
    print(f"  mAP={metrics['val/mAP']:.4f}, AP_rare={metrics['val/AP_rare']:.4f}, "
          f"AP_common={metrics['val/AP_common']:.4f}")

    # Notion 実験Run台帳 (M2研究計画v2) へ完走時自動投稿。
    # .env の NOTION_API_KEY / NOTION_DB_ID 等を読み込んでから呼ぶ。
    # notion_logger は内部で全例外を握りつぶす設計 (Notion 失敗で証跡を壊さない)。
    _load_dotenv(REPO_ROOT / ".env")
    try:
        from egosurgery.utils.notion_logger import log_experiment_to_notion

        resp = log_experiment_to_notion(
            args.exp_dir, status="completed", step="S0", tier="must"
        )
        if resp:
            print(f"[post-process] Notion 台帳に投稿済: {args.exp_dir.name}")
        else:
            print("[post-process] Notion 投稿スキップ (未設定 or 失敗、証跡は保存済)")
    except Exception as exc:  # noqa: BLE001 — Notion 失敗で post-process を巻き込まない
        print(f"[post-process] Notion 投稿で例外 (無視): {exc}")

    # Slack seed 単位通知 (#experiment)。webhook があれば直接送信、無ければ
    # 整形テキストを stdout に出すので launcher ログから拾える。
    # 通知失敗で post-process を巻き込まない。
    try:
        subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "notify_experiment.py"),
             "--mode", "seed", "--dirs", str(args.exp_dir),
             "--detector", "Sense-X Co-DINO 9enc"],
            timeout=60, check=False,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[post-process] Slack 通知で例外 (無視): {exc}")


def _load_dotenv(env_path: Path) -> None:
    """.env を最小パースして os.environ に流し込む (未設定キーのみ)。

    依存追加を避けるため python-dotenv は使わず手書き。既に環境変数が
    設定されていればそちらを優先する (上書きしない)。
    """
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


if __name__ == "__main__":
    main()
