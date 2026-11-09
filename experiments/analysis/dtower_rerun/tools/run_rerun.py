"""Runner of T-2026-11-07-dtower-rerun: the Task B controls and the twenty training runs.

    python run_rerun.py control <name>    # few-step controls of Task B (control_spec below)
    python run_rerun.py steps             # fold_steps.json from the len_<fold> controls (measured)
    python run_rerun.py train             # the twenty runs in the prereg §2.1 order, one after another

Built from ``experiments/analysis/dtower_batch_search/tools/run_batch.py`` (PR 299). Each run repeats
its sequence: train with accelerate on both GPUs (the search script through ``train_level.py``, the
config copy with the per-GPU batch, the observer), evaluate the best checkpoint on val and train,
collect the post-hoc records. Added for this contract: the fold's annotations (``EGO_ANN_DIR``), the
two points (12 and 0), the weight decay of every fold from its measured 1 epoch steps
(``S / (lr x 20 x steps)``, prereg §2.1, amended 2026-11-07), the test evaluation once per run after
everything else (``--split test`` of the evaluation script, prereg §2.4) and the per-video values of
the evaluator (``eval_dump.py``). Work directories, checkpoints and the accelerate state stay under
``$STORE`` (outside the synced paths). Start after ``source scripts/load_env.sh``.

Stop conditions of the prereg (§6) are checked after every stage; a stop prints ``STOP <reason>`` and
exits 3. An overflow of the GPU memory is a stop (the batch is a fixed level; it is never lowered).
A finished run leaves ``RUN_DONE`` in its work directory and is skipped when ``train`` is restarted.
"""
from __future__ import annotations

import json
import math
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
TASK = "T-2026-11-07-dtower-rerun"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
CONFIG_COPY = STORE / "config/train_search_batch.py"
STEPS_FILE = STORE / "B/fold_steps.json"
OUT_ROOT = ROOT / "experiments/baselines/stage1_dtower_rerun"
VENV = ROOT / ".venv-relation-detr"
BODY = ROOT / ".venv/bin/python"
COCO = ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"
COCO_SHA256 = "2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff"
BATCH = 6
EPOCH_STEPS_PER_S = 20  # S = lr x weight decay x (20 epochs of updates), card §14
# prereg §2.1: point -> learning rate of the body group, max_norm, S (exact products, amended 2026-11-07)
POINTS = {12: {"lr": 3.07e-4, "max_norm": 0.059, "S": 3.07e-4 * 3.37e-4 * 48100},
          0: {"lr": 1e-4, "max_norm": 0.1, "S": 1e-4 * 1e-4 * 48100}}
FOLDS = "ABCDE"
ORDER = ([(12, f, 42) for f in FOLDS] + [(12, f, 123) for f in FOLDS]
         + [(0, f, 42) for f in FOLDS] + [(0, f, 123) for f in FOLDS])
TABLE = {"A": {"test": ["04", "05", "07"], "val": ["09", "10"]},
         "B": {"test": ["01", "03", "14"], "val": ["02", "08"]},
         "C": {"test": ["02", "08", "11"], "val": ["06", "12"]},
         "D": {"test": ["06", "13", "15"], "val": ["04", "05"]},
         "E": {"test": ["09", "10", "12"], "val": ["07", "15"]}}  # conventions#folds
WALL_ASK_HOURS = 18  # prereg §6: twice the 9 h upper estimate -> ask
WALL_KILL_HOURS = 48
PROVISIONAL_WD = 1.01058e-3  # only for the len_<fold> controls, which measure the loader length


def say(*parts):
    print(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), *parts, flush=True)


def ann_dir(fold):
    return ROOT / "data/annotations/egosurgery_tool_folds" / fold


def gpu_idle():
    """No compute app on either GPU, no memory in use, no accelerate launcher running.

    Both virtual environments resolve to the same interpreter, so the launcher is told apart by the
    argv element ``launch`` (exact) rather than by the executable alone; short body-venv tools
    started meanwhile are not selected. The exe-and-argv enumeration of Task A-3 is separate.
    """
    smi = subprocess.run(["nvidia-smi", "--query-gpu=index,memory.used", "--format=csv,noheader,nounits"],
                         capture_output=True, text=True, check=True).stdout
    used = [int(line.split(",")[1]) for line in smi.strip().splitlines()]
    procs = json.loads(subprocess.run([sys.executable, str(TOOLS / "procs.py"), "--exe", str(VENV / "bin/python"),
                                       "--arg", "launch", "--exclude-pid", str(os.getpid())],
                                      capture_output=True, text=True, check=True).stdout)
    return {"memory_used_mib": used, "procs": procs["count"], "apps": len(procs["nvidia_smi_compute_apps"]),
            "idle": all(u <= 100 for u in used) and not procs["count"] and not procs["nvidia_smi_compute_apps"]}


def fold_steps():
    return json.loads(STEPS_FILE.read_text())["steps"]


def weight_decay(point, fold):
    steps = fold_steps()[fold]
    return POINTS[point]["S"] / (POINTS[point]["lr"] * EPOCH_STEPS_PER_S * steps)


def environment(work, probe, fold, batch, point_file, env_wd, expect, point, lr, max_norm, seed, coco=COCO):
    env = {k: v for k, v in os.environ.items()
           if k not in ("PYTORCH_CUDA_ALLOC_CONF", "TOWER_SEARCH_CONTROL_STEPS", "DTOWER_EVAL_SPLIT")}
    env.update(CUDA_VISIBLE_DEVICES="0,1", NCCL_P2P_DISABLE="1", WANDB_MODE="offline", WANDB_DIR=str(work),
               PYTHONPATH=str(ROOT / "src") + ":" + str(ROOT / "scripts"), CUDA_HOME="/usr/local/cuda",
               PYTHONDONTWRITEBYTECODE="1", VIRTUAL_ENV=str(VENV), PATH=f"{VENV}/bin:" + os.environ["PATH"],
               EGO_ROOT=str(ROOT / "data/raw/ego"), EGO_ANN_DIR=str(ann_dir(fold)),
               RELDETR_COCO_CKPT=str(coco), RELDETR_OUTPUT_DIR=str(work), RELDETR_EVIDENCE_DIR=str(work),
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
        {"start_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
         "end_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "wall_seconds": wall,
         "returncode": proc.returncode}) + "\n")
    return proc.returncode, wall


def train_command(script, config, seed, port):
    entry = TOOLS / "train_level.py" if script == "level" else ROOT / "scripts/train_relation_detr_search.py"
    conf = CONFIG_COPY if config == "copy" else ROOT / "configs/detector_relation_detr/train_search.py"
    return [str(VENV / "bin/accelerate"), "launch", "--multi_gpu", "--num_processes", "2", "--main_process_port",
            str(port), str(entry), "--config-file", str(conf), "--seed", str(seed), "--mixed-precision", "fp16",
            "--convergence-schedule", "--max-epochs", "36"]


def write_point(path, point, lr, wd, max_norm, batch, steps):
    path.write_text(json.dumps({"point": point, "lr": lr, "detector_weight_decay": wd, "max_norm": max_norm,
                                "batch_per_gpu": batch, "epoch_steps": steps,
                                "detector_S": lr * wd * EPOCH_STEPS_PER_S * steps if steps else None}) + "\n")


def control_spec(name):
    """name -> (script, config, fold, batch, point-file wd, env wd, expected batch, point, lr, max_norm, coco)."""
    p12, p0 = POINTS[12], POINTS[0]
    if name.startswith("len_"):
        return ("level", "copy", name[4:], BATCH, PROVISIONAL_WD, PROVISIONAL_WD, BATCH, 12, p12["lr"],
                p12["max_norm"], COCO)
    wd12, wd0 = weight_decay(12, "A"), weight_decay(0, "A")
    return {
        "p12_A": ("level", "copy", "A", BATCH, wd12, wd12, BATCH, 12, p12["lr"], p12["max_norm"], COCO),
        "p0_A": ("level", "copy", "A", BATCH, wd0, wd0, BATCH, 0, p0["lr"], p0["max_norm"], COCO),
        "changed": ("level", "copy", "A", 3, 5e-4, 5e-4, 3, 12, 2e-4, 0.07, COCO),
        "wd_mismatch": ("level", "copy", "A", BATCH, wd12, wd0, BATCH, 12, p12["lr"], p12["max_norm"], COCO),
        "batch_mismatch": ("level", "copy", "A", BATCH, wd12, wd12, 4, 12, p12["lr"], p12["max_norm"], COCO),
        "default": ("search", "original", "A", 2, 1e-4, 1e-4, None, 0, 1e-4, 0.1, COCO),
        "coco_missing": ("level", "copy", "A", BATCH, wd12, wd12, BATCH, 12, p12["lr"], p12["max_norm"],
                         Path("/nonexistent/zzz_no_such_coco_checkpoint.pth")),
    }[name]


def control(name):
    script, config, fold, batch, point_wd, env_wd, expect, point, lr, max_norm, coco = control_spec(name)
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
        write_point(point_file, point, lr, point_wd, max_norm, batch, None)
    env = environment(work, probe, fold, batch, point_file, env_wd, expect, point, lr, max_norm, 42, coco)
    env["TOWER_SEARCH_CONTROL_STEPS"] = "5"
    rc, wall = run(train_command(script, config, 42, 29801), env, ROOT / "third_party/Relation-DETR", base / "train.log")
    text = (base / "train.log").read_text(errors="replace")

    def read(path):
        return json.loads(path.read_text()) if path.exists() else None

    result = {"control": name, "fold": fold, "returncode": rc, "wall_seconds": wall,
              "control_complete": "CONTROL_COMPLETE" in text,
              "groups_differ_error": "detector optimizer groups differ" in text,
              "frames_error": "differ from the level batch" in text,
              "file_not_found": "FileNotFoundError: " in text,  # the raised exception, not the printed config source
              "load_pretrained_line": "load pretrained from" in text,
              "optimizer": (read(work / "optimizer_rank0.json") or {}).get("groups"),
              "max_norm_seen": (read(work / "optimizer_rank0.json") or {}).get("max_norm"),
              "initialization": [read(p) for p in sorted(work.glob("initialization_rank*.json"))],
              "load_digest": [read(p) for p in sorted(probe.glob("load_digest_rank*.json"))],
              "loader": [read(p) for p in sorted(probe.glob("loader_rank*.json"))],
              "weights": sorted(str(p.relative_to(base)) for p in base.rglob("*.pth"))}
    (base / "result.json").write_text(json.dumps(result, indent=1) + "\n")
    loaders = result["loader"]
    say("CONTROL", name, json.dumps({k: result[k] for k in ("returncode", "control_complete", "groups_differ_error",
                                                             "frames_error", "file_not_found",
                                                             "load_pretrained_line")}),
        "groups", [(g["lr"], g["weight_decay"]) for g in (result["optimizer"] or [])],
        "max_norm", result["max_norm_seen"],
        "loader", [(x["batch_sampler_batch_size"], x["loader_length"], x["dataset_frames"]) for x in loaders],
        "load_changed", [d["changed"] for d in result["load_digest"]])


def steps():
    measured, rows = {}, {}
    for fold in FOLDS:
        loaders = [json.loads(p.read_text()) for p in sorted((STORE / "B" / f"control_len_{fold}" / "probe")
                                                            .glob("loader_rank*.json"))]
        lengths = {x["loader_length"] for x in loaders}
        if len(loaders) != 2 or len(lengths) != 1 or any(x["batch_sampler_batch_size"] != BATCH for x in loaders):
            raise SystemExit(f"fold {fold}: loader records missing or inconsistent: {loaders}")
        measured[fold] = lengths.pop()
        rows[fold] = {"loader_length": measured[fold], "dataset_frames": [x["dataset_frames"] for x in loaders],
                      "dataset_videos": [x["dataset_videos"] for x in loaders]}
    wds = {f"{p}_{fold}": POINTS[p]["S"] / (POINTS[p]["lr"] * EPOCH_STEPS_PER_S * measured[fold])
           for p in POINTS for fold in FOLDS}
    STEPS_FILE.write_text(json.dumps({"steps": measured, "rows": rows, "weight_decay": wds,
                                      "S": {str(p): v["S"] for p, v in POINTS.items()}}, indent=1) + "\n")
    print(json.dumps({"steps": measured, "weight_decay": wds}, indent=1))


def check_groups(groups, lr, wd):
    expected_lr = [lr * f for f in (1, .1, .1, .1, .1, 1)]
    expected_wd = [wd * f for f in (1, 1, 0, 1, 0, 0)]
    return len(groups) == 6 and all(abs(g["lr"] - a) <= 1e-15 and abs(g["weight_decay"] - b) <= 1e-15
                                    for g, a, b in zip(groups, expected_lr, expected_wd))


def run_name(point, fold, seed):
    return f"dtowerrerun_p{point:02d}_dcoco_fold{fold}_seed{seed}"


def evaluate(env, work, name, split, port=29821):
    eval_env = {**env, "EVAL_DUMP_PREFIX": str(work / f"eval_{split}"),
                "EVAL_DUMP_DETECTIONS": "0" if split == "train" else "1"}
    extra = []
    if split == "test":
        eval_env.pop("DTOWER_EVAL_SPLIT", None)
        extra = ["--split", "test"]  # the config copy refuses test; the script swaps the annotations
    else:
        eval_env["DTOWER_EVAL_SPLIT"] = split
    cmd = [str(VENV / "bin/accelerate"), "launch", "--multi_gpu", "--num_processes", "2",
           "--mixed_precision", "no", "--main_process_port", str(port), str(TOOLS / "eval_dump.py"),
           "--config", str(CONFIG_COPY), "--checkpoint", str(work / "best_ap.pth"),
           "--out", str(work / f"eval_{split}.json"), *extra]
    erc, wall = run(cmd, eval_env, ROOT, work / f"eval_{split}.log", kill_hours=8)
    etext = (work / f"eval_{split}.log").read_text(errors="replace")
    if erc != 0 or "skip loading" in etext or "State dict is None" in etext or not (work / f"eval_{split}.json").exists():
        say("STOP evaluator", name, split, f"rc={erc}")
        sys.exit(3)
    if split == "test" and f"instances_test.json" not in etext:
        say("STOP test_annotations_not_read", name)
        sys.exit(3)
    per_video = json.loads((work / f"eval_{split}.per_video.json").read_text())
    diff = per_video.get("recomputed_minus_evaluator_AP")
    if diff is None or abs(diff) > 1e-9:
        say("WARN per_video_recompute", name, split, diff)
    return wall


def train_one(point, fold, seed):
    name = run_name(point, fold, seed)
    work = STORE / "runs" / name
    if (work / "RUN_DONE").exists():
        say("SKIP_DONE", name)
        return
    lr, max_norm = POINTS[point]["lr"], POINTS[point]["max_norm"]
    steps_fold = fold_steps()[fold]
    wd = weight_decay(point, fold)
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
    write_point(point_file, point, lr, wd, max_norm, BATCH, steps_fold)
    env = environment(work, probe, fold, BATCH, point_file, wd, BATCH, point, lr, max_norm, seed)
    cmd = train_command("level", "copy", seed, 29801)
    config = {"task_id": TASK, "point_id": point, "fold": fold, "seed": seed, "batch_per_gpu": BATCH,
              "effective_batch": 2 * BATCH, "lr": lr, "weight_decay": wd, "max_norm": max_norm,
              "S": POINTS[point]["S"], "epoch_steps_measured": steps_fold,
              "kind": "detector", "init": "coco", "gpus": "0,1", "host": "andrew", "work": str(work),
              "epochs": 36, "mixed_precision": "fp16", "num_workers": 4, "config_copy": str(CONFIG_COPY),
              "train_entry": str(TOOLS / "train_level.py"), "annotations": str(ann_dir(fold).relative_to(ROOT))}
    (out / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True))
    (out / "git_commit.txt").write_text(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True))
    (out / "command.sh").write_text("#!/usr/bin/env bash\n" + shlex.join(cmd) + "\n")
    (out / "server.txt").write_text("andrew\n")
    say("RUN_START", name, f"fold={fold} point={point} wd={wd!r} steps={steps_fold} seed={seed}")
    rc, wall = run(cmd, env, ROOT / "third_party/Relation-DETR", work / "train.log", ask_hours=WALL_ASK_HOURS)
    text = (work / "train.log").read_text(errors="replace")
    say("TRAIN_DONE", name, f"rc={rc}", f"wall={wall:.0f}s")
    if rc != 0:
        if "OutOfMemoryError" in text or "CUDA out of memory" in text:
            say("STOP overflow", name)
        elif "Loss is" in text:
            say("STOP nonfinite_loss", name)
        else:
            say("STOP train_failed", name)
        sys.exit(3)
    inits = [json.loads(p.read_text()) for p in sorted(work.glob("initialization_rank*.json"))]
    digests = [json.loads(p.read_text()) for p in sorted(probe.glob("load_digest_rank*.json"))]
    if ("load pretrained from" not in text or len(inits) != 2 or
            not all(i["matched"] and i["source_sha256"] == COCO_SHA256 for i in inits)
            or len(digests) != 2 or not all(d["changed"] for d in digests)):
        say("STOP coco_initialization", name)
        sys.exit(3)
    groups = json.loads((work / "optimizer_rank0.json").read_text())["groups"]
    loaders = [json.loads(p.read_text()) for p in sorted(probe.glob("loader_rank*.json"))]
    if (not check_groups(groups, lr, wd) or len(loaders) != 2
            or any(x["batch_sampler_batch_size"] != BATCH or x["loader_length"] != steps_fold for x in loaders)):
        say("STOP settings_not_reached", name)
        sys.exit(3)
    allowed = set(TABLE[fold]["val"]) | (set(f"{i:02d}" for i in range(1, 16)) - set(TABLE[fold]["test"])
                                         - set(TABLE[fold]["val"]))
    read = set()
    for path in probe.glob("reads_det_pid*.txt"):
        read |= set(path.read_text().split())
    if not read or read - allowed:
        say("STOP videos_outside_fold", name, sorted(read - allowed))
        sys.exit(3)
    timings = {}
    for split in ("val", "train"):
        timings[split] = evaluate(env, work, name, split)
    rrc, _ = run([str(BODY), str(ROOT / "scripts/tower_search_records.py"), "detector", str(work)],
                 {**env, "CUDA_VISIBLE_DEVICES": ""}, ROOT, work / "records.log", kill_hours=1)
    if rrc != 0:
        say("STOP records", name, (work / "records.log").read_text(errors="replace")[-400:])
        sys.exit(3)
    # test: once, after the checkpoint, the selection and the records are fixed (prereg §2.4)
    if (work / "eval_test.json").exists() or (work / "test_access.json").exists():
        say("STOP test_already_evaluated", name)
        sys.exit(3)
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    timings["test"] = evaluate(env, work, name, "test")
    (work / "test_access.json").write_text(json.dumps(
        {"run": name, "evaluations": 1, "start_utc": started, "end_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "videos": TABLE[fold]["test"], "checkpoint": str(work / "best_ap.pth")}) + "\n")
    metrics = json.loads((work / "search_metrics.json").read_text())
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=False) + "\n")
    for split, dst in (("val", "per_class_ap.json"), ("test", "per_class_ap_test.json")):
        ev = json.loads((work / f"eval_{split}.json").read_text())
        (out / dst).write_text(json.dumps({k: v for k, v in ev["per_class_ap"].items() if v == v}, indent=2) + "\n")
    for src, dst in (("posthoc_records.json", "posthoc_records.json"), ("convergence.json", "convergence.json"),
                     ("wandb/wandb_run.json", "wandb_run.json"), ("search_history.json", "search_history.json"),
                     ("probe/eval_epochs.json", "eval_epochs.json"), ("probe/loader_rank0.json", "loader_rank0.json"),
                     ("probe/loader_rank1.json", "loader_rank1.json"), ("eval_val.json", "eval_val.json"),
                     ("eval_train.json", "eval_train.json"), ("eval_test.json", "eval_test.json"),
                     ("eval_val.per_video.json", "per_video_val.json"),
                     ("eval_test.per_video.json", "per_video_test.json"), ("test_access.json", "test_access.json"),
                     ("probe/load_digest_rank0.json", "load_digest_rank0.json"),
                     ("probe/load_digest_rank1.json", "load_digest_rank1.json"),
                     ("initialization_rank0.json", "initialization_rank0.json"),
                     ("optimizer_rank0.json", "optimizer_rank0.json"), ("train.timing.json", "train.timing.json")):
        if (work / src).exists():
            shutil.copy2(work / src, out / dst)
    warm = json.loads((probe / "warmup_rank0.json").read_text())
    (out / "warmup_rank0.json").write_text(json.dumps(
        {k: warm[k] for k in ("target_lr", "first_step_at_target", "steps_in_epoch0")}
        | {"lr_group0_first_last": [warm["lr_per_step"][0][0], warm["lr_per_step"][-1][0]]}, indent=1) + "\n")
    (out / "eval_timing.json").write_text(json.dumps(timings) + "\n")
    (out / "notes.md").write_text(
        f"# {name}\n\nContract {TASK}. Point {point} (lr {lr!r}, max_norm {max_norm!r}, S {POINTS[point]['S']:.6e}), "
        f"fold {fold}, seed {seed}, per-GPU batch {BATCH} (effective {2 * BATCH}), weight decay {wd!r} from the "
        f"measured {steps_fold} steps per epoch.\n\n"
        f"Artifacts, checkpoints, detections and raw logs: {work} (outside the synced paths).\n"
        "Checkpoint chosen on the fold's val mAP. Val and train evaluations of the best checkpoint; the fold's "
        "test videos evaluated once afterwards (secondary, prereg §2.4; never used for any decision).\n")
    (work / "RUN_DONE").write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()) + "\n")
    test = json.loads((work / "eval_test.json").read_text())
    say("RUN_DONE", name, f"mAP={metrics['mAP']:.4f}", f"AP_target={metrics['AP_target']:.4f}",
        f"best_epoch={metrics['best_epoch']}", f"epochs={metrics['epochs_completed']}", f"test_mAP={test['AP']:.4f}")


def main():
    if sys.argv[1] == "control":
        control(sys.argv[2])
    elif sys.argv[1] == "steps":
        steps()
    elif sys.argv[1] == "train":
        for point, fold, seed in ORDER:
            train_one(point, fold, seed)
        say("ALL_DONE")
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
