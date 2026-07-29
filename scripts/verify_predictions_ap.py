#!/usr/bin/env python
"""保存済み predictions から COCO eval を再実行し、記録済み mAP と bit-exact 一致するか検証する。

「predictions を残した」だけでは不十分で、**それが本当に AP を再現できる実体か**を
証明できて初めて、ckpt 消失後の解析が信用に足る。本スクリプトはその動作証明を担う。

再評価は ``util.coco_eval`` の関数（``loadRes`` / ``evaluate`` / ``create_common_coco_eval``）を
そのまま使う。学習時の :class:`CocoEvaluator` はバッチ毎に ``update()`` を呼ぶが、
``evaluateImg`` は (image, category) 毎に独立なので、全画像を 1 回で評価しても結果は同一になる。
モデル出力から作り直すのではなく **保存された COCO results をそのまま流す**ので、
xywh↔xyxy 往復による浮動小数の揺れも入らない。

実行（.venv-relation-detr, cwd はどこでもよい）::

    .venv-relation-detr/bin/python scripts/verify_predictions_ap.py \
        --run t1b_clsbias_film_inj_seed42 --split val --epoch -1
    .venv-relation-detr/bin/python scripts/verify_predictions_ap.py \
        --run t1b_clsbias_film_inj_seed42 --split val --best
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_artifacts as ra  # noqa: E402

RELDETR = ra.PROJECT_ROOT / "third_party" / "Relation-DETR"
sys.path.insert(0, str(RELDETR))


def recompute_map(ann_file: str, results: list, image_ids: list[int]) -> float:
    """保存済み COCO results から overall mAP（``stats[0]``）を再計算する。"""
    from pycocotools.coco import COCO
    from pycocotools.cocoeval import COCOeval
    from util.coco_eval import create_common_coco_eval, evaluate, loadRes

    with contextlib.redirect_stdout(io.StringIO()):
        coco_gt = COCO(ann_file)
        coco_eval = COCOeval(coco_gt, iouType="bbox")
        coco_eval.cocoDt = loadRes(coco_gt, results)
        coco_eval.params.imgIds = list(image_ids)
        img_ids, eval_imgs = evaluate(coco_eval)
        create_common_coco_eval(coco_eval, img_ids, eval_imgs)
        coco_eval.accumulate()
        coco_eval.summarize()
    return float(coco_eval.stats[0])


def main() -> int:
    ap = argparse.ArgumentParser(description="predictions から AP を再計算して記録値と照合する。")
    ap.add_argument("--run", required=True, help="run 名（experiments/transfer/<run>）または絶対パス")
    ap.add_argument("--split", default="val")
    ap.add_argument("--tag", default=None, help="inj / ctrl（省略時は logs から解決）")
    ap.add_argument("--epoch", type=int, default=None, help="評価する epoch（init は -1）")
    ap.add_argument("--best", action="store_true", help="best epoch の predictions を検証する")
    ap.add_argument("--expect", type=float, default=None, help="期待 mAP（省略時は logs から解決）")
    ap.add_argument("--tol", type=float, default=0.0, help="許容差（既定 0 = bit-exact）")
    args = ap.parse_args()

    run_dir = ra.resolve_run_dir(args.run, work_dir=args.run if os.sep in args.run else None)
    log_path = ra.logs_dir(run_dir) / ra.EPOCH_LOG_NAME
    if not log_path.exists():
        print(f"[verify][FAIL] epoch ログが無い: {log_path}")
        return 2
    log = json.loads(log_path.read_text(encoding="utf-8"))
    tag = args.tag or log.get("variant") or "inj"

    pred_path = ra.find_predictions(
        run_dir, args.split, tag, epoch=args.epoch, best=args.best)
    if pred_path is None:
        print(f"[verify][FAIL] predictions が無い: run={run_dir} split={args.split} "
              f"tag={tag} epoch={args.epoch} best={args.best}")
        return 2

    meta = ra.load_eval_meta(run_dir, args.split)
    if meta is None:
        print(f"[verify][FAIL] eval メタが無い: {ra.logs_dir(run_dir)}/"
              f"{ra.eval_meta_name(args.split)}")
        return 2

    expected = args.expect
    if expected is None:
        if args.best:
            expected = log.get("best_mAP")
        elif args.epoch == -1:
            expected = (log.get("init") or {}).get("mAP")
        else:
            for row in log.get("epochs_eval", []):
                if row.get("epoch") == args.epoch:
                    expected = row.get("mAP")
                    break
    if expected is None:
        print("[verify][FAIL] 期待 mAP を解決できない（--expect を指定せよ）")
        return 2

    results = ra.load_predictions(pred_path)
    got = recompute_map(meta["ann_file"], results, meta["image_ids"])
    diff = abs(got - float(expected))
    ok = diff <= args.tol
    n_img = len({r["image_id"] for r in results})
    max_per_img = max(
        [sum(1 for r in results if r["image_id"] == i) for i in list({r["image_id"] for r in results})[:1]] or [0]
    )
    print(f"[verify] {pred_path.name}: images={n_img} dets={len(results)} "
          f"(先頭画像の検出数={max_per_img}, 上限={meta.get('topk')})")
    print(f"[verify] 再計算 mAP={got:.10f} / 記録 mAP={float(expected):.10f} / 差={diff:.3e}")
    print(f"[verify] => {'PASS (bit-exact)' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
