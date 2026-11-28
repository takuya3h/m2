"""andrew 上で Task F の指定 W（既定 W2: 14 本）を GPU 2 枚並列で実行するオーケストレータ。"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from queue import Queue

ROOT = Path(__file__).resolve().parents[4]
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot")
SCRIPT = ROOT / "experiments/analysis/vlm_caption_signal_pilot/tools/run_v2t_one_andrew.sh"
TYPES = ("P1", "P2L")
ARMS = ("empty", "vlm_ko", "vlm_otsu", "vlm_hei", "vlm_ko_shuf", "vlm_otsu_shuf", "vlm_hei_shuf")


def run_one(job: dict, gpu_id: int) -> dict:
    typ, w, arm, ep = job["type"], job["w"], job["arm"], job["epochs"]
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    t0 = time.monotonic()
    proc = subprocess.run(["bash", str(SCRIPT), typ, w, arm, str(ep)],
                          cwd=str(ROOT), env=env, capture_output=True, text=True)
    dt = time.monotonic() - t0
    if proc.returncode != 0:
        print(f"[FAIL] andrew V2T gpu={gpu_id} {typ} {w} {arm} ep{ep} rc={proc.returncode}\n{proc.stderr[-800:]}", flush=True)
    else:
        tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
        print(f"[OK] andrew V2T gpu={gpu_id} {typ} {w} {arm} ep{ep} ({dt/60:.1f}m) {tail}", flush=True)
    return {**job, "host": "andrew", "gpu": gpu_id, "rc": proc.returncode, "seconds": dt}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w", default="W2", choices=("W1", "W2", "W3"))
    ap.add_argument("--workers-per-gpu", type=int, default=2)
    a = ap.parse_args()

    jobs = [{"type": typ, "w": a.w, "arm": arm, "epochs": 16} for typ in TYPES for arm in ARMS]
    total_workers = 2 * a.workers_per_gpu
    print(f"[run_v2t_stage_andrew] W={a.w} jobs={len(jobs)} workers={total_workers}", flush=True)
    results = []
    t_all = time.monotonic()
    gpu_q: Queue[int] = Queue()
    for _ in range(a.workers_per_gpu):
        gpu_q.put(0)
        gpu_q.put(1)

    def wrapped(j, delay):
        if delay > 0:
            time.sleep(delay)
        gid = gpu_q.get()
        try:
            return run_one(j, gid)
        finally:
            gpu_q.put(gid)

    with ThreadPoolExecutor(max_workers=total_workers) as pool:
        futs = {pool.submit(wrapped, job, idx * 3 if idx < total_workers else 0): job for idx, job in enumerate(jobs)}
        for fut in as_completed(futs):
            results.append(fut.result())

    failed = [r for r in results if r["rc"] != 0]
    out_dir = STORE / "task_f"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"v2t_{a.w}_andrew_runs.json").write_text(json.dumps({
        "host": "andrew", "w": a.w, "workers_per_gpu": a.workers_per_gpu,
        "wall_seconds": time.monotonic() - t_all,
        "n_ok": len(results) - len(failed), "n_failed": len(failed),
        "runs": results,
    }, ensure_ascii=False, indent=2) + "\n")
    if failed:
        raise SystemExit(f"andrew V→T {a.w} に失敗した run がある: {len(failed)} 件")
    print(f"[run_v2t_stage_andrew] W={a.w} DONE ({(time.monotonic()-t_all)/3600:.2f}h)", flush=True)


if __name__ == "__main__":
    main()
