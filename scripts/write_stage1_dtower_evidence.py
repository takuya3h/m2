#!/usr/bin/env python
"""Stage 1 検出塔の各 run に証跡を書く。契約 T-2026-09-18-stage1-detector-towers。

`main.py`（上流の Relation-DETR）は `metrics.json` も `per_class_ap.json` も書かない。
凍結源の run（s0_016）でも「証跡補完」として後から作られている。同じ作法で作る。

書くもの（`outputs.must_have`）:
    config.yaml        処方と task_id（指示書と run を結ぶ唯一の鍵）
    metrics.json       val と test の mAP / AP_50 / AP_75 / AP_rare / AP_common
    per_class_ap.json  val の per-class AP（test は per_class_ap_test.json）
    notes.md           人が読む要約

**数値は評価の出力（eval_{val,test}.json）からしか取らない。** 手で書かない。

二周目（契約 T-2026-09-19-stage1-detector-towers-r2）は `--root` と `--task-id` で
行き先と契約を差し替える。**既定は一周目のままである。** 二周目の run には
`work/convergence.json`（`util/convergence.py` が毎 epoch 書く）があり、
epoch 数・学習率の低下 epoch・打ち切り epoch・最良 epoch はそこから取る。
一周目の run には無いので、従来どおり 12 epoch・`MultiStepLR([10])` と書く。
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "experiments/baselines/stage1_dtower"
TASK_ID = "T-2026-09-18-stage1-detector-towers"
RARE = {"Skewer", "Syringe"}
FOLDS = {"A": ("04,05,07", "09,10"), "B": ("01,03,14", "02,08"), "C": ("02,08,11", "06,12"),
         "D": ("06,13,15", "04,05"), "E": ("09,10,12", "07,15")}


def split_ap(per_class: dict) -> tuple[float, float, int, int]:
    r = [v for k, v in per_class.items() if k in RARE and not math.isnan(v)]
    c = [v for k, v in per_class.items() if k not in RARE and not math.isnan(v)]
    return (sum(r) / len(r) if r else float("nan"),
            sum(c) / len(c) if c else float("nan"), len(r), len(c))


def convergence_of(run_dir: Path) -> dict | None:
    """収束基準の記録を返す。一周目の run には無いので None。

    **log の丸めた値は使わない。** `convergence.json` は float の原値を持つ。
    """
    path = run_dir / "work" / "convergence.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT), help="run を探す場所")
    parser.add_argument("--task-id", default=TASK_ID, help="証跡に刻む契約")
    args = parser.parse_args()
    root, task_id = Path(args.root), args.task_id

    commit = (REPO / ".git" / "HEAD").read_text().strip()
    written = 0
    for d in sorted(root.glob("d*_fold*_seed*")):
        if not d.is_dir():
            continue
        m = re.match(r"d(coco|imagenet)_fold([A-E])_seed(\d+)$", d.name)
        if not m:
            continue
        tower, fold, seed = m.group(1), m.group(2), int(m.group(3))
        ev = d / "eval_val.json"
        if not ev.exists():
            print(f"[skip] 評価が無い: {d.name}")
            continue
        val = json.loads(ev.read_text())
        tst = json.loads((d / "eval_test.json").read_text()) if (d / "eval_test.json").exists() else None

        log = (d / "train.log").read_text(errors="ignore")
        tt = re.findall(r"Training time: (\d+:\d\d:\d\d)", log)
        steps = re.findall(r"Epoch: \[0\]  \[\d+/(\d+)\]", log)

        v_rare, v_common, nr, nc = split_ap(val["per_class_ap"])
        conv = convergence_of(d)
        metrics = {
            "task_id": task_id,
            "tower": f"D*-{'COCO' if tower == 'coco' else 'ImageNet'}",
            "fold": fold, "seed": seed,
            "val": {"mAP": val["AP"], "mAP_50": val["AP50"], "mAP_75": val["AP75"],
                    "AP_rare": v_rare, "AP_common": v_common,
                    "n_rare_classes": nr, "n_common_classes": nc},
            "eval_recipe": {"note": "NMS-free（conventions#eval_recipe）", "score_thr": 0.0,
                            "max_per_img": 300, "nms_pre": None, "nms_iou": None},
            "training_time": tt[-1] if tt else None,
            "steps_per_epoch": int(steps[0]) if steps else None,
            "epochs": conv["observed_epochs"] if conv else 12,
        }
        if conv:
            # 学習の長さを収束基準で決めた run。**測った値だけを載せる。**
            metrics["convergence"] = {
                "patience": conv["patience"], "factor": conv["factor"],
                "best_epoch": conv["best_epoch"], "best_val_map": conv["best_ap"],
                "decayed_epoch": conv["decayed_epoch"],
                "stopped_epoch": conv["stopped_epoch"],
                "reached_max_epochs": conv["stopped_epoch"] is None,
                "val_map_per_epoch": conv["val_ap_per_epoch"],
            }
        if tst:
            t_rare, t_common, _, _ = split_ap(tst["per_class_ap"])
            metrics["test"] = {"mAP": tst["AP"], "mAP_50": tst["AP50"], "mAP_75": tst["AP75"],
                               "AP_rare": t_rare, "AP_common": t_common,
                               "note": "折りごとに一度だけ評価。test_access_ledger.csv に記録"}
        (d / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False))
        (d / "per_class_ap.json").write_text(
            json.dumps(val["per_class_ap"], indent=2, ensure_ascii=False))
        if tst:
            (d / "per_class_ap_test.json").write_text(
                json.dumps(tst["per_class_ap"], indent=2, ensure_ascii=False))

        cfg = {
            "task_id": task_id,
            "run_name": d.name,
            "tower": metrics["tower"], "fold": fold, "seed": seed,
            "fold_test_videos": FOLDS[fold][0], "fold_val_videos": FOLDS[fold][1],
            "entrypoint": "third_party/Relation-DETR/main.py (accelerate launch --num_processes 2)",
            "config_file": (f"configs/train_config_egosurgery_seed{seed}.py" if tower == "coco"
                            else f"configs/train_config_egosurgery_stage1_imagenet_seed{seed}.py"),
            "mixed_precision": "fp16",
            "epochs": conv["observed_epochs"] if conv else 12,
            "batch_size_per_gpu": 2, "gpus": 2, "effective_batch_size": 4,
            "learning_rate": 1e-4, "weight_decay": 1e-4, "betas": [0.9, 0.999],
            "max_norm": 0.1, "transforms": "presets.detr",
            "backbone_freeze_indices": [0],
            "init": ("COCO 1x 重み（class head は 91->15 で再初期化）" if tower == "coco"
                     else "backbone のみ torchvision ImageNet-1K、検出ヘッドは乱数初期化"),
            "annotations": f"data/annotations/egosurgery_tool_folds/{fold}/",
            "git_commit": commit,
        }
        # 学習率の決め方は経路ごとに書き分ける。**既定の出力は一周目のままにする。**
        if conv:
            cfg["lr_schedule"] = (
                f"val mAP が {conv['patience']} epoch 続けて最良を更新しなければ lr を "
                f"{conv['factor']} 倍（一度だけ）、その後の再停滞で打ち切り"
            )
            cfg["lr_plateau_patience"] = conv["patience"]
            cfg["lr_plateau_factor"] = conv["factor"]
            cfg["max_epochs"] = 36
        else:
            cfg["lr_milestones"] = [10]
            cfg["lr_gamma"] = 0.1
        (d / "config.yaml").write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=True))

        lines = [f"# {d.name}", "",
                 f"契約: {task_id}", f"塔: {metrics['tower']} / 折り: {fold} / seed: {seed}", "",
                 "## 結果", "",
                 f"- val  mAP={val['AP']:.4f} / AP_rare={v_rare:.4f} / AP_common={v_common:.4f}"]
        if tst:
            t_rare, t_common, _, _ = split_ap(tst["per_class_ap"])
            lines.append(f"- test mAP={tst['AP']:.4f} / AP_rare={t_rare:.4f} / AP_common={t_common:.4f}"
                         "（**折りごとに一度だけ**評価）")
        if conv:
            lines += ["", "## 収束", "",
                      f"- 最良 epoch: {conv['best_epoch']}（val mAP {conv['best_ap']:.6f}）",
                      f"- 学習率の低下: epoch {conv['decayed_epoch']}"
                      if conv["decayed_epoch"] is not None else "- 学習率の低下: 起きていない",
                      f"- 打ち切り: epoch {conv['stopped_epoch']}"
                      if conv["stopped_epoch"] is not None else "- 打ち切り: 起きず上限に達した",
                      f"- 観測した epoch 数: {conv['observed_epochs']}"]
        prescription = (
            "凍結源 `s0_016` と**学習の長さの決め方だけ**が違う"
            f"（fp16・実効バッチ 4・lr 1e-4・`presets.detr` は同一。上限 36、停滞 {conv['patience']} で"
            f"lr を {conv['factor']} 倍、再停滞で打ち切り）。"
            if conv else
            "凍結源 `s0_016` と**同一**（fp16・12 epoch・実効バッチ 4・lr 1e-4・`presets.detr`）。"
        )
        lines += ["", "## 処方", "", prescription,
                  f"違うのは折りの注釈と seed と初期化だけである。所要 {tt[-1] if tt else 'UNKNOWN'}。", "",
                  "## 評価", "",
                  "NMS-free（`conventions#eval_recipe`）。`AP_rare` は Skewer と Syringe の平均",
                  "（`src/egosurgery/datasets/constants.py:71`）。NaN のクラスは平均から除く。"]
        (d / "notes.md").write_text("\n".join(lines) + "\n")
        (d / "git_commit.txt").write_text(commit + "\n")
        written += 1
    print(f"証跡を書いた run: {written}")


if __name__ == "__main__":
    main()
