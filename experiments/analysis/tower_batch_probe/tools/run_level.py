"""Run one measurement level of T-2026-11-06-tower-batch-probe and stop it.

    python run_level.py det <per-GPU batch>   # detector tower, accelerate, 2 GPUs, fp16
    python run_level.py ph2 <per-GPU batch>   # phase tower, torchrun, 2 GPUs (ft_batch_size = 2 x batch)
    python run_level.py ph1 <batch>           # phase tower, one GPU

The commands are the search's own (``scripts/run_tower_search.py``'s detector and phase
stages) with the point 0 recipe; only the batch, the step limit and the observer differ.
Everything is written under ``$STORE/<level>/``. Before starting, the GPUs must hold no
compute process and at most 100 MiB; after stopping, the work directory is searched for
saved weights.
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
TASK = "T-2026-11-06-tower-batch-probe"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
CONFIG_COPY = STORE / "config/train_search_batch.py"
MANIFEST = "data/processed/phase_manifest_all_phase"
DET_STEPS = 61    # forward starts 1..61 give 60 whole steps; steps 11-60 are the steady 50
PHASE_STEPS = 61  # handovers 1..61 give 60 whole micro-steps; steps 11-60 are the steady 50
TIMEOUT = 2400


def gpu_state():
    out = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used,utilization.gpu",
                          "--format=csv,noheader,nounits"], capture_output=True, text=True,
                         check=True).stdout
    return [[c.strip() for c in line.split(",")] for line in out.strip().splitlines()]


def procs():
    out = subprocess.run([sys.executable, str(TOOLS / "procs.py"), "--exclude-pid", str(os.getpid())], capture_output=True,
                         text=True, check=True).stdout
    return json.loads(out)


def main():
    kind, batch = sys.argv[1], int(sys.argv[2])
    gpus = "0" if kind == "ph1" else "0,1"
    level = f"{kind}_b{batch}"
    out = STORE / ("B" if kind == "det" else "C") / level
    out.mkdir(parents=True, exist_ok=False)
    work = out / "work"
    probe = out / "probe"
    work.mkdir()
    probe.mkdir()
    before = {"gpu": gpu_state(), "procs": procs()}
    busy = [g for g in before["gpu"] if g[0] in gpus.split(",") and int(g[1]) > 100]
    if before["procs"]["count"] or before["procs"]["nvidia_smi_compute_apps"] or busy:
        (out / "refused.json").write_text(json.dumps(before, indent=1))
        raise SystemExit(f"{level}: GPUs not idle, refused")

    env = {k: v for k, v in os.environ.items() if k != "PYTORCH_CUDA_ALLOC_CONF"}
    env.update(CUDA_VISIBLE_DEVICES=gpus, WANDB_MODE="offline", WANDB_DIR=str(work),
               PYTHONPATH=str(ROOT / "src") + ":" + str(ROOT / "scripts"),
               CUDA_HOME="/usr/local/cuda", PYTHONDONTWRITEBYTECODE="1",
               TOWER_SEARCH_TASK=TASK, TOWER_SEARCH_OBSERVER=str(TOOLS / "observer.py"),
               PROBE_OUT=str(probe))
    if gpus == "0,1":
        env["NCCL_P2P_DISABLE"] = "1"
    if kind == "det":
        venv = ROOT / ".venv-relation-detr"
        env.update(VIRTUAL_ENV=str(venv), PATH=f"{venv}/bin:" + env["PATH"],
                   EGO_ROOT=str(ROOT / "data/raw/ego"),
                   EGO_ANN_DIR=str(ROOT / "data/annotations/egosurgery_tool_folds/A"),
                   RELDETR_COCO_CKPT=str(ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"),
                   RELDETR_OUTPUT_DIR=str(work), RELDETR_EVIDENCE_DIR=str(work),
                   DTOWER_LR="0.0001", DTOWER_WEIGHT_DECAY="0.0001", DTOWER_MAX_NORM="0.1",
                   TOWER_SEARCH_POINT="0", TOWER_SEARCH_CONTROL_STEPS=str(DET_STEPS),
                   PROBE_BATCH_SIZE=str(batch))
        cmd = [str(venv / "bin/accelerate"), "launch", "--multi_gpu", "--num_processes", "2",
               "--main_process_port", "29801", str(ROOT / "scripts/train_relation_detr_search.py"),
               "--config-file", str(CONFIG_COPY), "--seed", "42", "--mixed-precision", "fp16",
               "--convergence-schedule", "--max-epochs", "36"]
        cwd = ROOT / "third_party/Relation-DETR"
    else:
        venv = ROOT / ".venv"
        env.update(VIRTUAL_ENV=str(venv), PATH=f"{venv}/bin:" + env["PATH"],
                   PROBE_STEPS=str(PHASE_STEPS))
        total = batch * (2 if kind == "ph2" else 1)
        common = ["scripts/run_ptower_search.py", "action=finetune", "+point_id=0",
                  f"+artifact_root={work}", f"manifest_dir={MANIFEST}",
                  f"cache={work}/features/all_gap.npz", "workers=4", "+control_only=true",
                  f"ft_batch_size={total}"]
        launcher = ([str(venv / "bin/python"), "-m", "torch.distributed.run", "--nproc_per_node=2",
                     "--master_port=29811"] if kind == "ph2" else [str(venv / "bin/python")])
        cmd = launcher + common
        cwd = ROOT

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
    record = {"task_id": TASK, "level": level, "kind": kind, "batch_per_gpu": batch, "gpus": gpus,
              "command": cmd, "cwd": str(cwd), "status": status, "returncode": rc,
              "wall_seconds": wall, "start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
              "env": {k: env.get(k) for k in ("CUDA_VISIBLE_DEVICES", "NCCL_P2P_DISABLE", "WANDB_MODE",
                                              "PYTORCH_CUDA_ALLOC_CONF", "PROBE_BATCH_SIZE", "PROBE_STEPS",
                                              "TOWER_SEARCH_CONTROL_STEPS", "TOWER_SEARCH_POINT",
                                              "DTOWER_LR", "DTOWER_WEIGHT_DECAY", "DTOWER_MAX_NORM",
                                              "VIRTUAL_ENV", "PYTHONDONTWRITEBYTECODE")},
              "before": before, "after": {"gpu": gpu_state(), "procs": procs()},
              "weight_files": weights}
    (out / "run.json").write_text(json.dumps(record, indent=1) + "\n")
    print(f"{level} status={status} rc={rc} wall={wall:.0f}s weights={len(weights)}")


if __name__ == "__main__":
    main()
