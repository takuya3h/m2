"""Task E: V→P 全本（4 epoch 確かめ 3 本＋16 epoch 63 本）の並列実行オーケストレータ。"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/vlm_caption_signal_pilot")
SIG = STORE / "signals"
TASK_ID = "T-2026-11-26-vlm-caption-signal-pilot"
PY = ROOT / ".venv/bin/python"
TYPES = ("D1-L2", "D2", "D3-L2")
SCOPES = ("W1", "W2", "W3")
ARMS = ("empty", "vlm_ko", "vlm_otsu", "vlm_hei", "vlm_ko_shuf", "vlm_otsu_shuf", "vlm_hei_shuf")


def find_existing_run(prefix: str, typ: str, arm: str, epochs: int) -> Path | None:
    p1 = ROOT / "experiments/phase1"
    pat = f"{prefix}_*_{typ}_{arm}_ep{epochs}_seed42"
    for d in sorted(p1.glob(pat)):
        if (d / "metrics.json").exists() and (d / f"metrics_ep{epochs}.json").exists():
            return d
    return None


def run_one(job: dict, gpu_id: int) -> dict:
    prefix = job["prefix"]
    typ, scope, arm, epochs = job["type"], job["scope"], job["arm"], job["epochs"]
    rec_eps = [4] if epochs == 4 else [4, 8, 12, 16]
    existing = find_existing_run(prefix, typ, arm, epochs)
    if existing is not None:
        return {**job, "status": "skipped_existing", "exp_dir": str(existing), "rc": 0, "seconds": 0.0}

    cmd = [
        str(PY), str(ROOT / "scripts/stage2pilot/dp_train.py"), "train",
        "--type", typ, "--arm", arm, "--seed", "42",
        "--scope", scope, "--fixed-epochs", str(epochs),
        "--record-epochs", *[str(e) for e in rec_eps],
        "--save-last-probs",
        "--task-id", TASK_ID,
        "--exp-prefix", prefix,
        "--vlm-dir", str(SIG),
        "--ckpt-dir", str(STORE / "dp_ckpt"),
    ]
    (STORE / "wandb").mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "CUDA_VISIBLE_DEVICES": str(gpu_id),
        "WANDB_MODE": "offline",
        "WANDB_API_KEY": "offline",
        "WANDB_DIR": str(STORE / "wandb"),
        "PYTHONUTF8": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": f"{ROOT / 'src'}:{ROOT / 'scripts'}",
    })
    t0 = time.monotonic()
    proc = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    dt = time.monotonic() - t0
    exp_dir = None
    for line in proc.stdout.splitlines():
        if line.startswith("DP_RUN_COMPLETE "):
            exp_dir = line.split()[1]
    if proc.returncode != 0:
        print(f"[FAIL] {typ} {scope} {arm} ep{epochs} rc={proc.returncode}\n{proc.stderr[-800:]}", flush=True)
    else:
        print(f"[OK] gpu={gpu_id} {typ} {scope} {arm} ep{epochs} ({dt:.1f}s) -> {Path(exp_dir).name if exp_dir else '?'}", flush=True)
    return {**job, "rc": proc.returncode, "exp_dir": exp_dir, "seconds": dt}


def compare_ep4(ep4_dir: Path, ep16_dir: Path) -> dict:
    p4 = np.load(ep4_dir / "predictions/val_probs_ep4.npz")
    p16 = np.load(ep16_dir / "predictions/val_probs_ep4.npz")
    p8 = np.load(ep16_dir / "predictions/val_probs_ep8.npz")
    max_diff_4 = max(float(np.abs(p4[k] - p16[k]).max()) for k in p4.files)
    max_diff_4v8 = max(float(np.abs(p4[k] - p8[k]).max()) for k in p4.files)
    m4 = json.loads((ep4_dir / "metrics_ep4.json").read_text())
    m16 = json.loads((ep16_dir / "metrics_ep4.json").read_text())
    return {
        "ep4_dir": ep4_dir.name, "ep16_dir": ep16_dir.name,
        "probs_exact_equal": max_diff_4 == 0.0,
        "probs_max_abs_diff": max_diff_4,
        "jaccard_diff": abs(m4["phase_jaccard"] - m16["phase_jaccard"]),
        "control_ep4_vs_ep8_max_abs_diff": max_diff_4v8,
        "control_ep4_vs_ep8_differs": max_diff_4v8 > 0.0,
    }


def run_batch(jobs: list[dict], workers_per_gpu: int = 4) -> list[dict]:
    total_workers = 2 * workers_per_gpu
    results = []
    with ThreadPoolExecutor(max_workers=total_workers) as pool:
        futs = {}
        for idx, job in enumerate(jobs):
            gpu = idx % 2
            futs[pool.submit(run_one, job, gpu)] = job
        for fut in as_completed(futs):
            results.append(fut.result())
    failed = [r for r in results if r["rc"] != 0]
    if failed:
        raise SystemExit(f"V→P に失敗した run がある: {len(failed)} 件")
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers-per-gpu", type=int, default=4)
    a = ap.parse_args()

    # 1. 先に 4 epoch 止め確かめ 3 本（W1/W2/W3 の D2 予測-甲）と 16 epoch の対応 3 本を回す
    check_jobs = []
    for sc in SCOPES:
        check_jobs.append({"type": "D2", "scope": sc, "arm": "vlm_ko", "epochs": 4,
                           "prefix": f"vlm_caption_signal_pilot_dp_{sc}_ep4chk"})
        check_jobs.append({"type": "D2", "scope": sc, "arm": "vlm_ko", "epochs": 16,
                           "prefix": f"vlm_caption_signal_pilot_dp_{sc}"})
    print(f"[run_v2p_all] phase 1: running {len(check_jobs)} ep4-consistency jobs...", flush=True)
    res1 = run_batch(check_jobs, workers_per_gpu=a.workers_per_gpu)

    by_key = {(r["scope"], r["epochs"]): Path(r["exp_dir"]) for r in res1}
    ep4_cmp = {sc: compare_ep4(by_key[(sc, 4)], by_key[(sc, 16)]) for sc in SCOPES}
    all_eq = all(v["probs_exact_equal"] for v in ep4_cmp.values())
    (STORE / "task_e").mkdir(parents=True, exist_ok=True)
    (STORE / "task_e/ep4_compare.json").write_text(json.dumps({
        "all_equal": all_eq, "by_scope": ep4_cmp,
    }, ensure_ascii=False, indent=2) + "\n")
    print(f"[run_v2p_all] ep4 compare: all_equal={all_eq}", flush=True)
    if not all_eq:
        raise SystemExit("4 epoch 止めと 16 epoch 続けの 4 epoch 目が一致しないため、SPEC §6.1 に従い 4 epoch 止めを全腕で回す必要がある")

    # 2. 残り 60 本（16 epoch）を回す
    rest_jobs = []
    for sc in SCOPES:
        for typ in TYPES:
            for arm in ARMS:
                if typ == "D2" and arm == "vlm_ko":
                    continue
                rest_jobs.append({"type": typ, "scope": sc, "arm": arm, "epochs": 16,
                                  "prefix": f"vlm_caption_signal_pilot_dp_{sc}"})
    print(f"[run_v2p_all] phase 2: running remaining {len(rest_jobs)} V→P jobs...", flush=True)
    res2 = run_batch(rest_jobs, workers_per_gpu=a.workers_per_gpu)

    all_res = res1 + res2
    (STORE / "task_e/v2p_runs.json").write_text(json.dumps({
        "workers_per_gpu": a.workers_per_gpu,
        "total_runs": len(all_res),
        "runs": all_res,
    }, ensure_ascii=False, indent=2) + "\n")
    print(f"[run_v2p_all] DONE: {len(all_res)} runs complete.", flush=True)


if __name__ == "__main__":
    main()
