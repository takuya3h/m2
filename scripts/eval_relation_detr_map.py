#!/usr/bin/env python
"""Relation-DETR の COCO mAP を **eval-only** で算出（凍結源 sanity / 改善検出器の評価に再利用）。

repo の `test.py` は COCO-2017 レイアウト（`{coco_path}/val2017`）を前提で本プロジェクトの
`data/raw/ego/<video>/<frame>.jpg` と噛み合わず、`main.py` は学習ループ内でしか eval しない。
本スクリプトは main.py のモデル構築・`_classes_` 登録・`evaluate_acc` の呼び出しだけを取り出し、
学習せずに val（または test）の mAP を出す。データ経路は config の env 変数（EGO_ROOT/EGO_ANN_DIR）で
本チェックアウトへ向ける（configs 改変不要）。

用途:
  - 凍結源 sanity: seed42 best_ap.pth が val/mAP ≈ 0.7297 を再現するか（stack + env parity 検証）。
  - 改善検出器の評価: 同一 recipe で mAP / per-class AP を測る。

実行（.venv-relation-detr で・repo 直下を CWD にする）:
  .venv-relation-detr/bin/python scripts/eval_relation_detr_map.py \
      --config configs/train_config_egosurgery_seed42.py \
      --checkpoint checkpoints/incoming/seed42/best_ap.pth
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJ = Path(__file__).resolve().parents[1]
REPO = PROJ / "third_party" / "Relation-DETR"


def main() -> None:
    ap = argparse.ArgumentParser(description="Relation-DETR eval-only COCO mAP")
    ap.add_argument("--config", type=str, default="configs/train_config_egosurgery_seed42.py",
                    help="train config（repo 相対）。test_dataset / model_path を提供する")
    ap.add_argument("--checkpoint", type=str, required=True, help="best_ap.pth（repo 相対 or 絶対）")
    ap.add_argument("--num-workers", type=int, default=4)
    ap.add_argument("--out", type=str, default=None, help="stats を書き出す json（任意）")
    args = ap.parse_args()

    # config の env 経路を本チェックアウトへ（未設定時のみ）。detector は 15-class tool。
    os.environ.setdefault("EGO_ROOT", str(PROJ / "data" / "raw" / "ego"))
    os.environ.setdefault("EGO_ANN_DIR", str(PROJ / "data" / "annotations" / "egosurgery_tool"))

    # repo 直下を CWD & import path に（相対 config 参照・util import を解決）
    os.chdir(REPO)
    sys.path.insert(0, str(REPO))

    import torch
    from accelerate import Accelerator
    from torch.utils import data
    from util.collate_fn import collate_fn
    from util.engine import evaluate_acc
    from util.lazy_load import Config
    from util.misc import encode_labels
    from util.utils import load_checkpoint, load_state_dict

    print(f"[eval] EGO_ROOT={os.environ['EGO_ROOT']}")
    print(f"[eval] EGO_ANN_DIR={os.environ['EGO_ANN_DIR']}")
    print(f"[eval] config={args.config}  checkpoint={args.checkpoint}")

    # optimizer/lr_scheduler/param_dicts は partial 化して遅延（main.py と同一）→ eager 構築エラー回避
    cfg = Config(args.config, partials=("lr_scheduler", "optimizer", "param_dicts"))
    accelerator = Accelerator()

    test_loader = data.DataLoader(
        cfg.test_dataset, 1, shuffle=False, num_workers=args.num_workers, collate_fn=collate_fn,
    )
    model = Config(cfg.model_path).model.eval()

    # クラス情報を model に登録（main.py と同一手順・推論に必須）
    cat_ids = list(range(max(cfg.train_dataset.coco.cats.keys()) + 1))
    classes = tuple(cfg.train_dataset.coco.cats.get(c, {"name": "none"})["name"] for c in cat_ids)
    model.register_buffer("_classes_", torch.tensor(encode_labels(classes)))

    ckpt = load_checkpoint(args.checkpoint)
    if isinstance(ckpt, dict) and "model" in ckpt:
        ckpt = ckpt["model"]
    load_state_dict(model, ckpt)

    model, test_loader = accelerator.prepare(model, test_loader)

    import numpy as np

    coco_evaluator = evaluate_acc(model, test_loader, 0, accelerator)
    if not accelerator.is_main_process:
        return  # 2GPU 時は main のみが集計・出力（gather 済）

    ce = coco_evaluator.coco_eval["bbox"]
    stats = ce.stats  # 12 要素 COCO 標準
    names = ["AP", "AP50", "AP75", "AP_s", "AP_m", "AP_l",
             "AR1", "AR10", "AR100", "AR_s", "AR_m", "AR_l"]
    out = {n: float(v) for n, v in zip(names, stats)}

    # per-class AP@[.5:.95]（area=all, maxDet=100）
    prec = ce.eval["precision"]  # [T,R,K,A,M]
    cat_id2name = {cid: c["name"] for cid, c in cfg.test_dataset.coco.cats.items()}
    per_class = {}
    for k, cid in enumerate(ce.params.catIds):
        p = prec[:, :, k, 0, -1]
        p = p[p > -1]
        per_class[cat_id2name.get(cid, str(cid))] = float(p.mean()) if p.size else float("nan")
    out["per_class_ap"] = per_class

    print("\n[eval] COCO bbox stats:")
    for n in names:
        print(f"  {n:5s} = {out[n]:.4f}")
    print(f"\n[eval] => mAP={out['AP']:.4f}  mAP50={out['AP50']:.4f}  "
          f"(凍結源 目標 val/mAP≈0.7297 / mAP50≈0.854)")
    print("\n[eval] per-class AP（弱い順）:")
    for name, ap in sorted(per_class.items(), key=lambda kv: (kv[1] if kv[1] == kv[1] else -1)):
        print(f"  {name:22s} AP={ap:.4f}")
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
        print(f"[eval] stats -> {args.out}")


if __name__ == "__main__":
    main()
