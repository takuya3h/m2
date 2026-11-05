"""Run one level of T-2026-11-06-dtower-step-profile (SPEC §2.1) and stop it.

    python run_level.py <level number 1..8>

The command is the search's own detector command (``scripts/run_tower_search.py``'s detector
stage, as T-2026-11-06-tower-batch-probe ran it) with the point 0 recipe; only the per-GPU
batch, the worker count, the process count, the input (loaded or one cached batch), the
step limit and the observer differ. Everything is written under ``$STORE/B/<level>/``.
Before starting, the GPUs to be used must hold no compute process and at most 100 MiB;
after stopping, the work directory is searched for saved weights.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TOOLS = Path(__file__).resolve().parent
TASK = "T-2026-11-06-dtower-step-profile"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
CONFIG_COPY = STORE / "config/train_search_profile.py"
FORWARD_STARTS = 81  # forward entries 1..81 give 80 whole steps; steps 21-80 are the summarised 60
TIMEOUT = 2400

# SPEC §2.1: number -> (per-GPU batch, processes, workers, loaded)
LEVELS = {
    1: (2, 2, 4, True),
    2: (4, 2, 4, True),
    3: (2, 2, 8, True),
    4: (2, 2, 16, True),
    5: (2, 1, 4, True),
    6: (4, 1, 4, True),
    7: (2, 2, 4, False),
    8: (4, 2, 4, False),
}


def gpu_state():
    out = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used,utilization.gpu",
                          "--format=csv,noheader,nounits"], capture_output=True, text=True,
                         check=True).stdout
    return [[c.strip() for c in line.split(",")] for line in out.strip().splitlines()]


def procs():
    out = subprocess.run([sys.executable, str(TOOLS / "procs.py"), "--exclude-pid", str(os.getpid())],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def main():
    number = int(sys.argv[1])
    batch, processes, workers, loaded = LEVELS[number]
    gpus = "0,1" if processes == 2 else "0"
    level = f"L{number}_b{batch}_p{processes}_w{workers}_{'load' if loaded else 'noload'}"
    out = STORE / "B" / level
    out.mkdir(parents=True, exist_ok=False)
    work = out / "work"
    probe = out / "probe"
    work.mkdir()
    probe.mkdir()
    before = {"gpu": gpu_state(), "procs": procs()}
    busy = [g for g in before["gpu"] if int(g[1]) > 100]
    if before["procs"]["count"] or before["procs"]["nvidia_smi_compute_apps"] or busy:
        (out / "refused.json").write_text(json.dumps(before, indent=1))
        raise SystemExit(f"{level}: GPUs not idle, refused")

    venv = ROOT / ".venv-relation-detr"
    env = {k: v for k, v in os.environ.items() if k != "PYTORCH_CUDA_ALLOC_CONF"}
    env.update(CUDA_VISIBLE_DEVICES=gpus, WANDB_MODE="offline", WANDB_DIR=str(work),
               PYTHONPATH=str(ROOT / "src") + ":" + str(ROOT / "scripts"),
               CUDA_HOME="/usr/local/cuda", PYTHONDONTWRITEBYTECODE="1",
               TOWER_SEARCH_TASK=TASK, TOWER_SEARCH_OBSERVER=str(TOOLS / "observer.py"),
               PROBE_OUT=str(probe), VIRTUAL_ENV=str(venv), PATH=f"{venv}/bin:" + env["PATH"],
               EGO_ROOT=str(ROOT / "data/raw/ego"),
               EGO_ANN_DIR=str(ROOT / "data/annotations/egosurgery_tool_folds/A"),
               RELDETR_COCO_CKPT=str(ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"),
               RELDETR_OUTPUT_DIR=str(work), RELDETR_EVIDENCE_DIR=str(work),
               DTOWER_LR="0.0001", DTOWER_WEIGHT_DECAY="0.0001", DTOWER_MAX_NORM="0.1",
               TOWER_SEARCH_POINT="0", TOWER_SEARCH_CONTROL_STEPS=str(FORWARD_STARTS),
               PROBE_BATCH_SIZE=str(batch), PROBE_NUM_WORKERS=str(workers),
               PROBE_NO_LOAD="0" if loaded else "1")
    env.pop("NCCL_P2P_DISABLE", None)
    launch = [str(venv / "bin/accelerate"), "launch"]
    if processes == 2:
        env["NCCL_P2P_DISABLE"] = "1"
        launch += ["--multi_gpu", "--num_processes", "2", "--main_process_port", "29801"]
    else:
        launch += ["--num_processes", "1"]
    cmd = launch + [str(ROOT / "scripts/train_relation_detr_search.py"),
                    "--config-file", str(CONFIG_COPY), "--seed", "42", "--mixed-precision", "fp16",
                    "--convergence-schedule", "--max-epochs", "36"]
    cwd = ROOT / "third_party/Relation-DETR"

    sampler = subprocess.Popen(
        ["nvidia-smi", "--query-gpu=timestamp,index,memory.used,utilization.gpu,power.draw",
         "--format=csv,noheader,nounits", "-lms", "200"],
        stdout=open(out / "nvsmi.csv", "w"), stderr=subprocess.STDOUT)
    started = time.time()
    with open(out / "stdout.log", "w") as log:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            rc = proc.wait(timeout=TIMEOUT)
            status = "exited"
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)
            time.sleep(10)
            os.killpg(proc.pid, signal.SIGKILL)
            rc = proc.wait()
            status = "timeout"
    wall = time.time() - started
    time.sleep(2)
    sampler.terminate()
    sampler.wait()
    weights = sorted(str(p.relative_to(out)) for p in out.rglob("*")
                     if p.is_file() and (p.suffix in (".pth", ".pt", ".safetensors", ".bin", ".ckpt")
                                         or "checkpoint" in p.parent.name))
    record = {"task_id": TASK, "level": level, "number": number, "batch_per_gpu": batch,
              "processes": processes, "num_workers": workers, "loaded": loaded, "gpus": gpus,
              "command": cmd, "cwd": str(cwd), "status": status, "returncode": rc,
              "wall_seconds": wall, "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
              "env": {k: env.get(k) for k in ("CUDA_VISIBLE_DEVICES", "NCCL_P2P_DISABLE", "WANDB_MODE",
                                              "PYTORCH_CUDA_ALLOC_CONF", "PROBE_BATCH_SIZE",
                                              "PROBE_NUM_WORKERS", "PROBE_NO_LOAD",
                                              "TOWER_SEARCH_CONTROL_STEPS", "TOWER_SEARCH_POINT",
                                              "DTOWER_LR", "DTOWER_WEIGHT_DECAY", "DTOWER_MAX_NORM",
                                              "VIRTUAL_ENV", "PYTHONDONTWRITEBYTECODE")},
              "before": before, "after": {"gpu": gpu_state(), "procs": procs()},
              "weight_files": weights}
    (out / "run.json").write_text(json.dumps(record, indent=1) + "\n")
    print(f"{level} status={status} rc={rc} wall={wall:.0f}s weights={len(weights)}")


if __name__ == "__main__":
    main()
