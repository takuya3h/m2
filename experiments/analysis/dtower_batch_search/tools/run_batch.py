"""Runner of T-2026-11-06-dtower-batch-search: the G2 controls and the six training runs.

    python run_batch.py control <name>       # few-step controls of Task B (CONTROLS below)
    python run_batch.py train                 # the six runs in the prereg order, one after another

Each run repeats the search's detector sequence (``scripts/run_tower_search.py`` ``detector_point``):
train with accelerate on both GPUs, evaluate the best checkpoint on val and train, collect the
post-hoc records, and copy the run's files to ``experiments/baselines/stage1_dtower_batch/``.
Only the point (prereg §2.1 values through ``tools/train_level.py``), the per-GPU batch (the
config copy outside the repo), the seed, the work directory and the observer differ. Work
directories, checkpoints and the accelerate state stay under ``$STORE`` (outside the synced
paths). Must be started after ``source scripts/load_env.sh`` (the W&B offline tracker needs it).

Stop conditions of the prereg (§6) are checked after every stage; a stop prints ``STOP <reason>``
and exits 3. A batch 6 overflow prints ``OVERFLOW`` and skips that level.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
TOOLS = Path(__file__).resolve().parent
TASK = "T-2026-11-06-dtower-batch-search"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
CONFIG_COPY = STORE / "config/train_search_batch.py"
OUT_ROOT = ROOT / "experiments/baselines/stage1_dtower_batch"
VENV = ROOT / ".venv-relation-detr"
BODY = ROOT / ".venv/bin/python"
COCO = ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"
COCO_SHA256 = "2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff"
LR, MAX_NORM, POINT = 3.07e-4, 0.059, 12
S = 3.07e-4 * 3.37e-4 * 48100  # 4.976e-3, prereg §2.1 (amended 2026-11-06)
# prereg §2.1: level -> (per-GPU batch, weight decay, 1 epoch steps in the prereg table)
LEVELS = {"b2": (2, 3.37e-4, 2405), "b4": (4, 6.7428e-4, 1202), "b6": (6, 1.01058e-3, 802)}
ORDER = [("b2", 42), ("b2", 123), ("b4", 42), ("b4", 123), ("b6", 42), ("b6", 123)]
WALL_ASK_HOURS = 18  # prereg §6: twice the 9 h estimate -> ask
WALL_KILL_HOURS = 48  # the search's own limit for one detector training command
# Task B controls: name -> (script, config, batch, point file weight decay, env weight decay,
#                           expected batch for the frames check, point number, lr, max_norm)
POINT0 = (1e-4, 1e-4, 0.1)
CONTROLS = {
    "b2": ("level", "copy", 2, 3.37e-4, 3.37e-4, 2, POINT, LR, MAX_NORM),
    "b4": ("level", "copy", 4, 6.7428e-4, 6.7428e-4, 4, POINT, LR, MAX_NORM),
    "b6": ("level", "copy", 6, 1.01058e-3, 1.01058e-3, 6, POINT, LR, MAX_NORM),
    "changed": ("level", "copy", 3, 5e-4, 5e-4, 3, POINT, LR, MAX_NORM),
    "wd_mismatch": ("level", "copy", 2, 3.37e-4, 6.7428e-4, 2, POINT, LR, MAX_NORM),
    "batch_mismatch": ("level", "copy", 2, 3.37e-4, 3.37e-4, 4, POINT, LR, MAX_NORM),
    "default": ("search", "original", 2, POINT0[1], POINT0[1], None, 0, POINT0[0], POINT0[2]),
}


def say(*parts):
    print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), *parts, flush=True)


def gpu_idle():
    smi = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, check=True).stdout
    used = [int(line.split(",")[1]) for line in smi.strip().splitlines()]
    procs = json.loads(subprocess.run([sys.executable, str(TOOLS / "procs.py"), "--exclude-pid", str(os.getpid())],
                                      capture_output=True, text=True, check=True).stdout)
    return {"memory_used_mib": used, "procs": procs["count"], "apps": len(procs["nvidia_smi_compute_apps"]),
            "idle": all(u <= 100 for u in used) and not procs["count"] and not procs["nvidia_smi_compute_apps"]}


def environment(work, probe, batch, point_file, env_wd, expect, point, lr, max_norm, seed):
    env = {k: v for k, v in os.environ.items() if k not in ("PYTORCH_CUDA_ALLOC_CONF", "TOWER_SEARCH_CONTROL_STEPS")}
    env.update(CUDA_VISIBLE_DEVICES="0,1", NCCL_P2P_DISABLE="1", WANDB_MODE="offline", WANDB_DIR=str(work),
               PYTHONPATH=str(ROOT / "src") + ":" + str(ROOT / "scripts"), CUDA_HOME="/usr/local/cuda",
               PYTHONDONTWRITEBYTECODE="1", VIRTUAL_ENV=str(VENV), PATH=f"{VENV}/bin:" + os.environ["PATH"],
               EGO_ROOT=str(ROOT / "data/raw/ego"), EGO_ANN_DIR=str(ROOT / "data/annotations/egosurgery_tool_folds/A"),
               RELDETR_COCO_CKPT=str(COCO), RELDETR_OUTPUT_DIR=str(work), RELDETR_EVIDENCE_DIR=str(work),
               DTOWER_LR=repr(lr), DTOWER_WEIGHT_DECAY=repr(env_wd), DTOWER_MAX_NORM=repr(max_norm),
               TOWER_SEARCH_POINT=str(point), TOWER_SEARCH_TASK=TASK, TOWER_SEARCH_SEED=str(seed),
               TOWER_SEARCH_OBSERVER=str(TOOLS / "observer.py"), PROBE_OUT=str(probe),
               PROBE_BATCH_SIZE=str(batch), PROBE_NUM_WORKERS="4")
    if point_file:
        env["DTOWER_LEVEL_POINT"] = str(point_file)
    if expect is not None:
        env["PROBE_EXPECT_BATCH"] = str(expect)
    return env


def run(cmd, env, cwd, log, ask_hours=None, kill_hours=WALL_KILL_HOURS):
    (log.parent / (log.stem + ".command.sh")).write_text("#!/usr/bin/env bash\n" + shlex.join(cmd) + "\n")
    started = time.time()
    asked = False
    with open(log, "w") as handle:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        while proc.poll() is None:
            time.sleep(30)
            hours = (time.time() - started) / 3600
            if ask_hours and hours > ask_hours and not asked:
                say("WALL_LIMIT_EXCEEDED", log, f"{hours:.2f}h")
                asked = True
            if hours > kill_hours:
                os.killpg(proc.pid, signal.SIGTERM)
                time.sleep(30)
                os.killpg(proc.pid, signal.SIGKILL)
    wall = time.time() - started
    (log.parent / (log.stem + ".timing.json")).write_text(json.dumps(
        {"start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)), "wall_seconds": wall,
         "returncode": proc.returncode}) + "\n")
    return proc.returncode, wall


def train_command(script, config, seed, port):
    entry = TOOLS / "train_level.py" if script == "level" else ROOT / "scripts/train_relation_detr_search.py"
    conf = CONFIG_COPY if config == "copy" else ROOT / "configs/detector_relation_detr/train_search.py"
    return [str(VENV / "bin/accelerate"), "launch", "--multi_gpu", "--num_processes", "2", "--main_process_port",
            str(port), str(entry), "--config-file", str(conf), "--seed", str(seed), "--mixed-precision", "fp16",
            "--convergence-schedule", "--max-epochs", "36"]


def write_point(path, point, lr, wd, max_norm, batch):
    steps = LEVELS[f"b{batch}"][2] if f"b{batch}" in LEVELS else None
    path.write_text(json.dumps({"point": point, "lr": lr, "detector_weight_decay": wd, "max_norm": max_norm,
                                "batch_per_gpu": batch,
                                "detector_S": lr * wd * 20 * steps if steps else None}) + "\n")


def control(name):
    script, config, batch, point_wd, env_wd, expect, point, lr, max_norm = CONTROLS[name]
    base = STORE / "B" / f"control_{name}"
    work, probe = base / "work", base / "probe"
    work.mkdir(parents=True, exist_ok=False)
    probe.mkdir()
    state = gpu_idle()
    if not state["idle"]:
        say("STOP gpus_not_idle", state)
        sys.exit(3)
    point_file = None
    if script == "level":
        point_file = base / "level_point.json"
        write_point(point_file, point, lr, point_wd, max_norm, batch)
    env = environment(work, probe, batch, point_file, env_wd, expect, point, lr, max_norm, 42)
    env["TOWER_SEARCH_CONTROL_STEPS"] = "5"
    rc, wall = run(train_command(script, config, 42, 29801), env, ROOT / "third_party/Relation-DETR", base / "train.log")
    text = (base / "train.log").read_text(errors="replace")
    result = {"control": name, "returncode": rc, "wall_seconds": wall,
              "control_complete": "CONTROL_COMPLETE" in text,
              "groups_differ_error": "detector optimizer groups differ" in text,
              "frames_error": "differ from the level batch" in text,
              "optimizer": json.loads((work / "optimizer_rank0.json").read_text())["groups"]
              if (work / "optimizer_rank0.json").exists() else None,
              "loader": json.loads((probe / "loader_rank0.json").read_text()) if (probe / "loader_rank0.json").exists() else None,
              "weights": sorted(str(p.relative_to(base)) for p in base.rglob("*.pth"))}
    (base / "result.json").write_text(json.dumps(result, indent=1) + "\n")
    say("CONTROL", name, json.dumps({k: result[k] for k in ("returncode", "control_complete", "groups_differ_error",
                                                             "frames_error")}),
        "groups", [(g["lr"], g["weight_decay"]) for g in (result["optimizer"] or [])],
        "batch", result["loader"] and result["loader"]["batch_sampler_batch_size"])


def check_groups(groups, wd):
    expected_lr = [LR * f for f in (1, .1, .1, .1, .1, 1)]
    expected_wd = [wd * f for f in (1, 1, 0, 1, 0, 0)]
    return len(groups) == 6 and all(abs(g["lr"] - a) <= 1e-15 and abs(g["weight_decay"] - b) <= 1e-15
                                    for g, a, b in zip(groups, expected_lr, expected_wd))


def train_one(level, seed, slot):
    batch, wd, _ = LEVELS[level]
    name = f"dtowerbatch_{level}_dcoco_foldA_seed{seed}"
    work = STORE / "runs" / name
    probe = work / "probe"
    out = OUT_ROOT / name
    work.mkdir(parents=True, exist_ok=False)
    probe.mkdir()
    out.mkdir(parents=True, exist_ok=False)
    state = gpu_idle()
    if not state["idle"]:
        say("STOP gpus_not_idle", name, state)
        sys.exit(3)
    point_file = work / "level_point.json"
    write_point(point_file, POINT, LR, wd, MAX_NORM, batch)
    env = environment(work, probe, batch, point_file, wd, batch, POINT, LR, MAX_NORM, seed)
    cmd = train_command("level", "copy", seed, 29801)
    config = {"task_id": TASK, "level": level, "batch_per_gpu": batch, "effective_batch": 2 * batch, "seed": seed,
              "point_id": POINT, "lr": LR, "weight_decay": wd, "max_norm": MAX_NORM, "S": S,
              "fold": "A", "kind": "detector", "gpus": "0,1", "host": "andrew", "work": str(work),
              "epochs": 36, "mixed_precision": "fp16", "num_workers": 4, "config_copy": str(CONFIG_COPY),
              "train_entry": str(TOOLS / "train_level.py")}
    (out / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    (out / "git_commit.txt").write_text(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True))
    (out / "command.sh").write_text("#!/usr/bin/env bash\n" + shlex.join(cmd) + "\n")
    (out / "server.txt").write_text("andrew\n")
    say("RUN_START", name, f"batch={batch} wd={wd!r} seed={seed}")
    rc, wall = run(cmd, env, ROOT / "third_party/Relation-DETR", work / "train.log", ask_hours=WALL_ASK_HOURS)
    text = (work / "train.log").read_text(errors="replace")
    say("TRAIN_DONE", name, f"rc={rc}", f"wall={wall:.0f}s")
    if rc != 0:
        if "OutOfMemoryError" in text and level == "b6":
            say("OVERFLOW", name)
            return "overflow"
        reason = "nonfinite_loss" if "Loss is" in text else "train_failed"
        say("STOP", reason, name)
        sys.exit(3)
    inits = [json.loads(p.read_text()) for p in sorted(work.glob("initialization_rank*.json"))]
    if ("load pretrained from" not in text or len(inits) != 2 or
            not all(i["matched"] and i["source_sha256"] == COCO_SHA256 for i in inits)):
        say("STOP coco_initialization", name)
        sys.exit(3)
    groups = json.loads((work / "optimizer_rank0.json").read_text())["groups"]
    loader = json.loads((probe / "loader_rank0.json").read_text())
    if not check_groups(groups, wd) or loader["batch_sampler_batch_size"] != batch:
        say("STOP settings_not_reached", name)
        sys.exit(3)
    for split in ("val", "train"):
        eval_env = {**env, "DTOWER_EVAL_SPLIT": split}
        eval_cmd = [str(VENV / "bin/accelerate"), "launch", "--multi_gpu", "--num_processes", "2",
                    "--mixed_precision", "no", "--main_process_port", "29821",
                    str(ROOT / "scripts/eval_relation_detr_map.py"), "--config", str(CONFIG_COPY),
                    "--checkpoint", str(work / "best_ap.pth"), "--out", str(work / f"eval_{split}.json")]
        erc, _ = run(eval_cmd, eval_env, ROOT, work / f"eval_{split}.log", kill_hours=8)
        etext = (work / f"eval_{split}.log").read_text(errors="replace")
        if erc != 0 or "skip loading" in etext or "State dict is None" in etext:
            say("STOP evaluator", name, split, f"rc={erc}")
            sys.exit(3)
    rrc, _ = run([str(BODY), str(ROOT / "scripts/tower_search_records.py"), "detector", str(work)],
                 {**env, "CUDA_VISIBLE_DEVICES": ""}, ROOT, work / "records.log", kill_hours=1)
    if rrc != 0:
        say("STOP records", name, (work / "records.log").read_text(errors="replace")[-400:])
        sys.exit(3)
    metrics = json.loads((work / "search_metrics.json").read_text())
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n")
    val = json.loads((work / "eval_val.json").read_text())
    (out / "per_class_ap.json").write_text(json.dumps(
        {k: v for k, v in val["per_class_ap"].items() if v == v}, indent=2) + "\n")
    for src, dst in (("posthoc_records.json", "posthoc_records.json"), ("convergence.json", "convergence.json"),
                     ("wandb/wandb_run.json", "wandb_run.json"), ("search_history.json", "search_history.json"),
                     ("probe/eval_epochs.json", "eval_epochs.json"), ("probe/loader_rank0.json", "loader_rank0.json"),
                     ("probe/loader_rank1.json", "loader_rank1.json")):
        if (work / src).exists():
            shutil.copy2(work / src, out / dst)
    warm = json.loads((probe / "warmup_rank0.json").read_text())
    (out / "warmup_rank0.json").write_text(json.dumps(
        {k: warm[k] for k in ("target_lr", "first_step_at_target", "steps_in_epoch0")}
        | {"lr_group0_first_last": [warm["lr_per_step"][0][0], warm["lr_per_step"][-1][0]]}, indent=1) + "\n")
    (out / "notes.md").write_text(
        f"# {name}\n\nContract {TASK}. Level {level} (per-GPU batch {batch}, effective {2 * batch}), seed {seed}, "
        f"point 12 settings with weight decay {wd!r} (S {S:.4e}).\n\n"
        f"Artifacts, checkpoints and raw logs: {work} (outside the synced paths).\n"
        "Validation selection only; no test evaluation. Train and val evaluations of the best checkpoint.\n")
    say("RUN_DONE", name, f"mAP={metrics['mAP']:.4f}", f"AP_target={metrics['AP_target']:.4f}",
        f"best_epoch={metrics['best_epoch']}", f"epochs={metrics['epochs_completed']}")
    return "done"


def main():
    if sys.argv[1] == "control":
        control(sys.argv[2])
        return
    skipped = set()
    for slot, (level, seed) in enumerate(ORDER):
        if level in skipped:
            say("SKIP", level, seed, "overflow")
            continue
        if train_one(level, seed, slot) == "overflow":
            skipped.add(level)
    say("ALL_DONE")


if __name__ == "__main__":
    main()
