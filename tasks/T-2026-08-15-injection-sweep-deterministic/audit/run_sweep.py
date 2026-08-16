#!/usr/bin/env python
"""Phase B: 六つの腕を六十の種で走らせる（三百六十本）。

走らせる順序は問わない（決定化してあるため結果に効かない）。**ただし実際に
使った順序を記録する。** 記録は audit/run_log.jsonl に一行ずつ追記する。

装置は二枚使う。採番の競合について:
`ExperimentManager.setup()` は `next_sequence()` で走査してから
`mkdir(exist_ok=False)` する（experiment_manager.py:140-144）。二つのプロセスが
同時に採番すると片方が FileExistsError で落ちる。**学習コードは変更しない**
（禁止 5）ため、起動をずらし、落ちた本は再試行する。

結果は途中で見ない。すべて終わってから Phase C へ進む。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

AUDIT = Path(__file__).resolve().parent
PROJ = AUDIT.parents[2]
ENTRY = "scripts/train_grasp_phase_injection_variants.py"
LOG = AUDIT / "run_log.jsonl"
ORDER = AUDIT / "run_order.json"

ARMS = ["uninformative", "oracle", "inferred", "raw_logits", "standardized", "staged"]
GPUS = [0, 1]
MAX_RETRY = 3

_log_lock = threading.Lock()
_launch_lock = threading.Lock()
# 採番の窓を外すための最小間隔。setup() はデータ読み込み（約 6 秒）の後に走る
# ため、起動が数秒ずれていれば二つのプロセスが同時に採番することはまず無い。
# **無条件に待たない。** 直前の起動から間隔が空いていなければその分だけ待つ。
# 一本は約 40 秒なので、定常状態では待ち時間は零である。
LAUNCH_GAP_S = 3.0
_last_launch = 0.0


def append(record: dict) -> None:
    with _log_lock:
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_one(arm: str, seed: int, gpu: int, index: int) -> dict:
    cfg = AUDIT / "configs" / f"{arm}.yaml"
    env = dict(os.environ)
    env["CUDA_VISIBLE_DEVICES"] = str(gpu)
    env["PYTHONPATH"] = "src"
    cmd = [sys.executable, ENTRY, "--config", str(cfg.relative_to(PROJ)), "--seed", str(seed)]

    global _last_launch
    for attempt in range(1, MAX_RETRY + 1):
        with _launch_lock:
            wait = LAUNCH_GAP_S - (time.time() - _last_launch)
            if wait > 0:
                time.sleep(wait)
            _last_launch = time.time()
            started = time.time()
            proc = subprocess.Popen(
                cmd, cwd=PROJ, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )
        out, _ = proc.communicate()
        elapsed = time.time() - started
        if proc.returncode == 0:
            return {
                "index": index, "arm": arm, "seed": seed, "gpu": gpu,
                "attempt": attempt, "returncode": 0, "wall_seconds": round(elapsed, 2),
                "tail": out.strip().splitlines()[-1:] if out else [],
            }
        tail = out.strip().splitlines()[-6:] if out else []
        append({"index": index, "arm": arm, "seed": seed, "gpu": gpu, "attempt": attempt,
                "returncode": proc.returncode, "wall_seconds": round(elapsed, 2),
                "retrying": attempt < MAX_RETRY, "tail": tail})
        if attempt == MAX_RETRY:
            return {"index": index, "arm": arm, "seed": seed, "gpu": gpu, "attempt": attempt,
                    "returncode": proc.returncode, "wall_seconds": round(elapsed, 2), "tail": tail}
    raise AssertionError("unreachable")


def worker(tasks: list[tuple[int, str, int]], gpu: int, results: list) -> None:
    for index, arm, seed in tasks:
        rec = run_one(arm, seed, gpu, index)
        append(rec)
        results.append(rec)


def main() -> int:
    seeds = json.loads((AUDIT / "seeds.json").read_text(encoding="utf-8"))["seeds"]
    assert len(seeds) == 60, len(seeds)

    # 順序: 腕を外側、種を内側。**走らせる前に記録する。**
    work = [(i, arm, seed) for i, (arm, seed) in enumerate(
        [(a, s) for a in ARMS for s in seeds])]
    assert len(work) == 360, len(work)

    split = {g: [w for w in work if w[0] % len(GPUS) == k] for k, g in enumerate(GPUS)}
    ORDER.write_text(json.dumps({
        "total": len(work),
        "arms": ARMS,
        "seeds": seeds,
        "order_rule": "腕を外側、種を内側。索引の偶奇で装置へ振り分ける",
        "gpu_assignment": {str(g): [[w[1], w[2]] for w in v] for g, v in split.items()},
        "launch_gap_seconds": LAUNCH_GAP_S,
        "max_retry": MAX_RETRY,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    started = time.time()
    results: list = []
    threads = [threading.Thread(target=worker, args=(split[g], g, results)) for g in GPUS]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    ok = [r for r in results if r["returncode"] == 0]
    bad = [r for r in results if r["returncode"] != 0]
    summary = {
        "total_planned": len(work),
        "completed": len(ok),
        "failed": len(bad),
        "failures": bad,
        "wall_seconds_total": round(time.time() - started, 1),
        "wall_seconds_mean_per_run": round(sum(r["wall_seconds"] for r in ok) / max(len(ok), 1), 2),
        "retries_used": sum(r["attempt"] - 1 for r in results),
    }
    (AUDIT / "run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "failures"},
                     ensure_ascii=False, indent=2))
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
