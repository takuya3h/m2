#!/usr/bin/env python3
"""detectron2 の metrics.json (JSONL) を wandb に後追い投稿する backfill。

DI-MaskDINO 等の plain detectron2 学習は wandb 統合が無いが、JSONWriter が
output_dir/metrics.json に 1 行 1 イベント (iter ごとの scalar) を残す。
本スクリプトはそれを読み wandb に step ごとに log し学習曲線を再現する
(9enc の wandb_backfill_from_logjson.py と同じ後追い方式)。W&B「全実験 track」要件用。

認証は環境変数 WANDB_API_KEY (.env)。entity/project は WANDB_ENTITY/WANDB_PROJECT。

Usage:
  python scripts/wandb_backfill_detectron2.py \
      --metrics experiments/transfer/dimaskdino_work_seed42/metrics.json \
      --run-name dimaskdino_r50_seed42 --exp-dir experiments/baselines/s0_022_...
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv(env_path: Path) -> None:
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", required=True, type=Path)
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--exp-dir", type=Path, default=None)
    ap.add_argument("--project", default=None)
    ap.add_argument("--group", default="s0_detector_benchmark")
    args = ap.parse_args()

    _load_dotenv(REPO_ROOT / ".env")
    if not os.environ.get("WANDB_API_KEY"):
        print("[wandb-backfill] WANDB_API_KEY 未設定、スキップ")
        return 0
    if not args.metrics.exists():
        print(f"[wandb-backfill] metrics.json 不在: {args.metrics}")
        return 0

    project = args.project or os.environ.get("WANDB_PROJECT", "egosurgery_multitask")
    entity = os.environ.get("WANDB_ENTITY")

    rows = []
    for line in args.metrics.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not rows:
        print("[wandb-backfill] metrics.json に有効行なし")
        return 0

    import wandb

    run = wandb.init(
        project=project, entity=entity, name=args.run_name,
        group=args.group, reinit=True,
    )
    n = 0
    for r in rows:
        step = r.get("iteration")
        payload = {k: v for k, v in r.items()
                   if isinstance(v, (int, float)) and k != "iteration"}
        if payload:
            run.log(payload, step=int(step) if step is not None else None)
            n += 1
    # exp-dir の最終 metrics.json を summary に
    if args.exp_dir is not None:
        mp = args.exp_dir / "metrics.json"
        if mp.exists():
            try:
                final = json.loads(mp.read_text(encoding="utf-8"))
                for k, v in final.items():
                    if isinstance(v, (int, float)):
                        run.summary[k] = v
            except json.JSONDecodeError:
                pass
    run.finish()
    print(f"[wandb-backfill] {n} 行を投稿: {args.run_name} (project={project})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
