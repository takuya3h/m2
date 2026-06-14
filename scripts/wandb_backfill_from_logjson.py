#!/usr/bin/env python3
"""wandb_backfill_from_logjson.py — mmdet 2.x の .log.json を wandb へ後追い投稿。

リアルタイム track できなかった run (例: Phase B seed42 は WandbLoggerHook 無しで
起動済み) の学習曲線を、work_dir の <ts>.log.json から wandb 上に再構成する。

.log.json は 1 行 1 イベントの JSONL:
  - train 行: {"mode":"train","epoch":N,"iter":M,"loss":...,"lr":...,...}
  - val 行:   {"mode":"val","epoch":N,"bbox_mAP":...,...}
これらを時系列順に wandb.log(step=global_iter) で流し込む。val は epoch 境界の
global_iter に載せる。

認証は環境変数 WANDB_API_KEY (.env から)。entity/project は WANDB_ENTITY/
WANDB_PROJECT か引数。

使い方:
  set -a; source .env; set +a
  python scripts/wandb_backfill_from_logjson.py \
      --work-dir /tmp/sensex_codino_work_seed42 \
      --run-name sensex_codino_9enc_seed42 \
      --group s0_sensex_codino --seed 42 \
      --tags S0 detector_benchmark sensex_codino mmdet2x backfill
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path


def _iter_log_events(log_json: Path):
    """log.json を 1 行ずつ dict で yield (壊れ行はスキップ)。"""
    for line in log_json.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(d, dict) and d.get("mode") in ("train", "val"):
            yield d


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work-dir", required=True, type=Path)
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--group", default="s0_sensex_codino")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--project", default=os.environ.get("WANDB_PROJECT", "egosurgery_multitask"))
    ap.add_argument("--entity", default=os.environ.get("WANDB_ENTITY"))
    ap.add_argument("--tags", nargs="*", default=["backfill"])
    ap.add_argument("--iters-per-epoch", type=int, default=2415,
                    help="val を載せる global step 計算用 (1 epoch の iter 数)")
    args = ap.parse_args(argv)

    if not os.environ.get("WANDB_API_KEY"):
        print("[backfill] WANDB_API_KEY が未設定。`set -a; source .env; set +a` してから実行してください。")
        return 1

    log_jsons = sorted(glob.glob(str(args.work_dir / "2026*.log.json")))
    if not log_jsons:
        print(f"[backfill] {args.work_dir} に .log.json が見つかりません。")
        return 1

    import wandb

    config = {"seed": args.seed, "source": "log.json backfill", "work_dir": str(args.work_dir)}
    run = wandb.init(
        project=args.project,
        entity=args.entity,
        name=args.run_name,
        group=args.group,
        job_type="train-backfill",
        tags=list(args.tags),
        config=config,
        reinit=True,
    )
    print(f"[backfill] wandb run: {run.url}")

    n_train, n_val, last_epoch = 0, 0, 0
    # 複数 log.json (resume で分割) を時系列順に処理。
    for lj in log_jsons:
        for ev in _iter_log_events(Path(lj)):
            epoch = int(ev.get("epoch", last_epoch) or last_epoch)
            last_epoch = epoch
            if ev["mode"] == "train":
                it = int(ev.get("iter", 0) or 0)
                step = (epoch - 1) * args.iters_per_epoch + it
                payload = {f"train/{k}": v for k, v in ev.items()
                           if isinstance(v, (int, float)) and k not in ("epoch", "iter")}
                payload["epoch"] = epoch
                if payload:
                    wandb.log(payload, step=max(step, 0))
                    n_train += 1
            else:  # val
                step = epoch * args.iters_per_epoch
                payload = {f"val/{k}": v for k, v in ev.items()
                           if isinstance(v, (int, float)) and k != "epoch"}
                payload["epoch"] = epoch
                if payload:
                    wandb.log(payload, step=max(step, 0))
                    n_val += 1

    # 最終 best metrics を summary に固定 (metrics.json があれば優先)。
    mp = args.work_dir / "metrics.json"
    summary_src = None
    exp_metrics = list(glob.glob(str(args.work_dir.parent / "*" / "metrics.json")))
    if mp.exists():
        try:
            summary_src = json.loads(mp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            summary_src = None
    if isinstance(summary_src, dict):
        for k, v in summary_src.items():
            if isinstance(v, (int, float)):
                run.summary[f"best/{k}"] = v

    print(f"[backfill] train行={n_train}, val行={n_val} を投稿。run={run.url}")
    wandb.finish()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
