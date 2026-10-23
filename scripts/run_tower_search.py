"""Run the preregistered search in the background, with explicit stop gates and GPU logs."""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import queue
import shlex
import shutil
import signal
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from tower_search_common import (
    ANALYSIS,
    ROOT,
    SCRATCH,
    TASK,
    check_detector_groups,
    load_point,
    write_json,
)

BODY = str(ROOT / ".venv/bin/python")
DET = str(ROOT / ".venv-relation-detr/bin/accelerate")
MANIFEST = "data/processed/phase_manifest_all_phase"
PAIRS = ("1,2", "3,4")
records = []
active = {}
guard = threading.Lock()
stopping = threading.Event()
processes = {}
started = time.monotonic()
handoff_commands = {}
handoff_points = set()
adopted_roots = {}
handoff_started = {}
running_actions = {}
current_stage = "C"


def process_identity(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rpartition(") ")[2].split()
        return None if fields[0] == "Z" else fields[19]
    except FileNotFoundError:
        return None


def completed_command(log):
    """Require actual end-of-stage evidence when adopting a reaped process."""
    text = log.read_text(errors="replace")
    if "Traceback (most recent call last)" in text:
        return False
    if log.name == "train.log":
        convergence = log.parent / "convergence.json"
        if not convergence.exists() or "Training time:" not in text:
            return False
        result = json.loads(convergence.read_text())
        return (result["stopped_epoch"] is not None or result["observed_epochs"] == 36) and (log.parent / "best_ap.pth").exists()
    if log.name.startswith("eval_"):
        path = log.with_suffix(".json")
        return "[eval] stats ->" in text and path.exists() and math.isfinite(json.loads(path.read_text())["AP"])
    markers = {"finetune.log": "FINETUNE_COMPLETE", "extract.log": "EXTRACT_COMPLETE"}
    marker = markers.get(log.name, "RECORDS_COMPLETE" if "records" in log.name else None)
    return marker is not None and marker in text


def adopt_command(log, tag, timeout_hours):
    info = handoff_commands.pop(str(log), None)
    if info is None:
        return False
    pid, identity = info["pid"], info["identity"]
    begin = datetime.fromisoformat(info["time_jst"]).timestamp()
    with guard:
        running_actions[pid] = {"tag": tag, "gpus": info["gpus"], "log": str(log), "adopted": True}
    try:
        while identity is not None and process_identity(pid) == identity:
            if stopping.wait(2) or time.time() - begin > timeout_hours * 3600:
                os.killpg(pid, signal.SIGTERM)
                raise RuntimeError(f"Adopted command stopped or timed out: {tag}")
    finally:
        with guard:
            running_actions.pop(pid, None)
    if not completed_command(log):
        raise RuntimeError(f"Adopted command lacks completion evidence: {tag}; {log}")
    write_json(log.with_suffix(".adopted.json"), {
        "original_pid": pid, "completed_jst": now(), "completion_evidence_checked": True,
        "exit_code": None, "note": "Original parent was replaced; completion verified from stage output and log."})
    return True


def now():
    return datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()


def status(state, **values):
    with guard:
        write_json(ANALYSIS / "live_status.json", {
            "state": state, "time_jst": now(), "supervisor_pid": os.getpid(),
            "active": dict(active), "completed_points": len(records),
            "running_commands": dict(running_actions), "stage": current_stage, **values})


def gpu_snapshot():
    fields = ["index", "uuid", "memory.used", "memory.free", "utilization.gpu"]
    output = subprocess.check_output(["nvidia-smi", f"--query-gpu={','.join(fields)}",
                                      "--format=csv,noheader,nounits"], text=True)
    return [dict(zip(fields, (v.strip() for v in row.split(","))))
            for row in output.splitlines() if row.strip()]


def descendants():
    parents = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                fields = (entry / "stat").read_text().rpartition(") ")[2].split()
                parents[int(entry.name)] = int(fields[1])
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
    owned = {os.getpid()} | {pid for pid, identity in adopted_roots.items()
                            if process_identity(pid) == identity}
    while True:
        more = {pid for pid, parent in parents.items() if parent in owned} - owned
        if not more:
            return owned
        owned |= more


def monitor():
    with (SCRATCH / "gpu_monitor.jsonl").open("a", buffering=1) as output:
        while not stopping.is_set():
            try:
                gpus = gpu_snapshot()
                own = descendants()
                apps = subprocess.check_output([
                    "nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory",
                    "--format=csv,noheader,nounits"], text=True)
                procs = []
                for line in apps.splitlines():
                    uuid, pid, memory = (v.strip() for v in line.split(","))
                    pid = int(pid)
                    try:
                        exe = os.readlink(f"/proc/{pid}/exe")
                    except (FileNotFoundError, PermissionError):
                        exe = None
                    procs.append({"uuid": uuid, "pid": pid, "memory": memory,
                                  "exe": exe, "owned": pid in own})
                gpu0 = next(g["uuid"] for g in gpus if g["index"] == "0")
                if any(p["owned"] and p["uuid"] == gpu0 for p in procs):
                    stopping.set()
                    status("stopped", reason="GPU0 owned process detected")
                with guard:
                    current = dict(active)
                output.write(json.dumps({"time_jst": now(), "gpus": gpus,
                                         "processes": procs, "active": current}) + "\n")
                if not stopping.is_set():
                    status("running")
            except Exception as exc:
                stopping.set()
                status("stopped", reason=f"GPU monitoring failed: {type(exc).__name__}")
            stopping.wait(10)


def pair_is_available(pair, gpus, busy_uuids):
    if pair not in PAIRS:
        raise RuntimeError("Only the two authorized GPU pairs are allowed")
    rows = [g for g in gpus if g["index"] in pair.split(",")]
    return len(rows) == 2 and all(
        g["uuid"] not in busy_uuids and int(g["memory.free"]) >= 22000 and
        int(g["utilization.gpu"]) == 0 for g in rows)


def free_pair(pair):
    while not stopping.is_set():
        output = subprocess.check_output(["nvidia-smi", "--query-compute-apps=gpu_uuid",
                                          "--format=csv,noheader,nounits"], text=True)
        if pair_is_available(pair, gpu_snapshot(), set(output.splitlines())):
            return
        stopping.wait(10)
    raise RuntimeError("Stopped while waiting for free GPUs")


def command(cmd, env, cwd, log, tag, timeout_hours):
    if stopping.is_set():
        raise RuntimeError("Search stopped")
    if shutil.disk_usage(SCRATCH).free < 150_000_000_000:
        raise RuntimeError("Scratch free space below 150 GB")
    if adopt_command(log, tag, timeout_hours):
        return
    log.parent.mkdir(parents=True, exist_ok=True)
    keys = ("CUDA_VISIBLE_DEVICES", "WANDB_MODE", "WANDB_DIR", "PYTHONPATH", "CUDA_HOME",
            "EGO_ROOT", "EGO_ANN_DIR", "RELDETR_COCO_CKPT", "RELDETR_OUTPUT_DIR", "RELDETR_EVIDENCE_DIR",
            "DTOWER_LR", "DTOWER_WEIGHT_DECAY", "DTOWER_MAX_NORM", "DTOWER_EVAL_SPLIT", "TOWER_SEARCH_POINT")
    replay = ("#!/usr/bin/env bash\nset -euo pipefail\ncd " + shlex.quote(str(ROOT)) +
              "\nsource scripts/load_env.sh\n" +
              "\n".join(f"export {key}={shlex.quote(env[key])}" for key in keys if key in env) +
              "\ncd " + shlex.quote(str(cwd)) + "\nexec " + shlex.join(cmd) + "\n")
    log.with_suffix(".command.sh").write_text(replay)
    with log.open("w") as output:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=output,
                                stderr=subprocess.STDOUT, start_new_session=True)
        with guard:
            processes[proc.pid] = proc
            running_actions[proc.pid] = {"tag": tag, "gpus": env.get("CUDA_VISIBLE_DEVICES", ""),
                                         "log": str(log), "adopted": False}
        write_json(log.with_suffix(".command.json"), {"cmd": cmd, "pid": proc.pid,
                                                    "time_jst": now(), "tag": tag})
        begin = time.monotonic()
        try:
            while proc.poll() is None:
                if stopping.wait(5) or time.monotonic() - begin > timeout_hours * 3600:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=60)
                    raise RuntimeError(f"Stopped or wall time limit: {tag}")
            if proc.returncode:
                raise RuntimeError(f"exit={proc.returncode}: {tag}; see {log}")
        finally:
            with guard:
                processes.pop(proc.pid, None)
                running_actions.pop(proc.pid, None)


def environment(pair, work):
    return {**os.environ, "CUDA_VISIBLE_DEVICES": pair, "WANDB_MODE": "offline",
            "WANDB_DIR": str(work), "PYTHONPATH": str(ROOT / "src") + ":" + str(ROOT / "scripts"),
            "CUDA_HOME": "/usr/local/cuda"}


def detector_environment(pair, work, point):
    env = environment(pair, work)
    env.update(EGO_ROOT=str(ROOT / "data/raw/ego"),
               EGO_ANN_DIR=str(ROOT / "data/annotations/egosurgery_tool_folds/A"),
               RELDETR_COCO_CKPT=str(ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"),
               RELDETR_OUTPUT_DIR=str(work), RELDETR_EVIDENCE_DIR=str(work),
               DTOWER_LR=str(point["lr"]), DTOWER_WEIGHT_DECAY=str(point["detector_weight_decay"]),
               DTOWER_MAX_NORM=str(point["max_norm"]), TOWER_SEARCH_POINT=str(point["point"]))
    env.pop("TOWER_SEARCH_CONTROL_STEPS", None)
    return env


def record_run(kind, number, action, run, pair):
    """Keep one row per completed run; detailed measured quantities stay in JSON."""
    metrics = json.loads((run / "metrics.json").read_text())
    detail = json.loads((run / "posthoc_records.json").read_text())
    path = ANALYSIS / "records.csv"
    with guard:
        exists = path.exists()
        if exists:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                prior = [r for r in csv.DictReader(handle) if
                         (r["kind"], r["point"], r["action"], r["run"]) ==
                         (kind, str(number), action, str(run))]
            if prior:
                if len(prior) != 1 or json.loads(prior[0]["metrics_json"]) != metrics:
                    raise RuntimeError("Conflicting completed run record during handoff")
                return
        with path.open("a", encoding="utf-8-sig" if not exists else "utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["task_id", "kind", "point", "action", "run",
                                                       "gpus", "metrics_json", "records_json"])
            if not exists:
                writer.writeheader()
            writer.writerow({"task_id": TASK, "kind": kind, "point": number, "action": action,
                             "run": str(run), "gpus": pair,
                             "metrics_json": json.dumps(metrics, allow_nan=False),
                             "records_json": json.dumps(detail, allow_nan=False)})


def publish_phase(work, action, launch_name=None):
    pointer = json.loads((work / f"{action}_last_run.json").read_text())
    source = Path(pointer["path"])
    dest = ROOT / "experiments/phase1/stage1_ptower_search" / pointer["exp_id"]
    for file in source.iterdir():
        if file.is_file() and file.suffix in (".json", ".yaml", ".md", ".txt", ".sh"):
            shutil.copy2(file, dest / file.name)
    shutil.copy2(work / f"{launch_name or action}.command.sh", dest / "command.sh")
    (dest / "server.txt").write_text("dlsta\n")
    with (dest / "notes.md").open("a") as handle:
        handle.write(f"\nArtifacts, checkpoints and raw logs: {source}\n")
    return source


def detector_point(number, pair, slot):
    point = load_point(number)
    work = SCRATCH / "detector" / f"point{number:02d}"
    resuming = ("detector", number) in handoff_points
    work.mkdir(parents=True, exist_ok=resuming)
    env = detector_environment(pair, work, point)
    out = ROOT / "experiments/baselines/stage1_dtower_search" / f"point{number:02d}_dcoco_foldA_seed42"
    out.mkdir(parents=True, exist_ok=resuming)
    config = {"task_id": TASK, "point_id": number, "point": point, "seed": 42,
              "fold": "A", "kind": "detector", "gpus": pair, "work": str(work),
              "epochs": 36, "mixed_precision": "fp16"}
    if resuming:
        existing = yaml.safe_load((out / "config.yaml").read_text())
        if existing["task_id"] != TASK or existing["point"] != point:
            raise RuntimeError("Resumed detector config differs")
    else:
        (out / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
        (out / "git_commit.txt").write_text(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True))
        (out / "notes.md").write_text(f"Artifacts and raw logs: {work}\nValidation selection only; no test evaluation.\n")
    cmd = [DET, "launch", "--multi_gpu", "--num_processes", "2", "--main_process_port", str(29801 + slot),
           str(ROOT / "scripts/train_relation_detr_search.py"), "--config-file",
           str(ROOT / "configs/detector_relation_detr/train_search.py"), "--seed", "42",
           "--mixed-precision", "fp16", "--convergence-schedule", "--max-epochs", "36"]
    if not resuming:
        (out / "command.sh").write_text("#!/usr/bin/env bash\n" + shlex.join(cmd) + "\n")
    command(cmd, env, ROOT / "third_party/Relation-DETR", work / "train.log", f"detector{number}", 48)
    shutil.copy2(work / "train.command.sh", out / "command.sh")
    for split in ("val", "train"):
        eval_env = {**env, "DTOWER_EVAL_SPLIT": split}
        cmd = [DET, "launch", "--multi_gpu", "--num_processes", "2", "--mixed_precision", "no",
               "--main_process_port", str(29821 + slot), str(ROOT / "scripts/eval_relation_detr_map.py"),
               "--config", str(ROOT / "configs/detector_relation_detr/train_search.py"),
               "--checkpoint", str(work / "best_ap.pth"), "--out", str(work / f"eval_{split}.json")]
        command(cmd, eval_env, ROOT, work / f"eval_{split}.log", f"detector{number}_{split}", 8)
        text = (work / f"eval_{split}.log").read_text()
        if "skip loading" in text or "State dict is None" in text:
            raise RuntimeError("Detector evaluator skipped checkpoint loading")
    command([BODY, str(ROOT / "scripts/tower_search_records.py"), "detector", str(work)],
            environment("", work), ROOT, work / "records.log", f"detector{number}_records", 1)
    metrics = json.loads((work / "search_metrics.json").read_text())
    write_json(out / "metrics.json", metrics)
    val = json.loads((work / "eval_val.json").read_text())
    write_json(out / "per_class_ap.json", {k: v for k, v in val["per_class_ap"].items() if math.isfinite(v)})
    shutil.copy2(work / "posthoc_records.json", out / "posthoc_records.json")
    shutil.copy2(work / "convergence.json", out / "convergence.json")
    shutil.copy2(work / "wandb/wandb_run.json", out / "wandb_run.json")
    (out / "server.txt").write_text("dlsta\n")
    record_run("detector", number, "train", out, pair)
    return {"kind": "detector", "point": point, "metric": metrics["mAP"], "metrics": metrics,
            "work": str(work), "run": str(out), "gpus": pair}


def phase_point(number, pair, slot):
    point = load_point(number)
    work = SCRATCH / "phase" / f"point{number:02d}"
    work.mkdir(parents=True, exist_ok=("phase", number) in handoff_points)
    env = environment(pair, work)
    cache = work / "features/all_gap.npz"
    common = [f"+point_id={number}", f"+artifact_root={work}", f"manifest_dir={MANIFEST}",
              f"cache={cache}", "workers=4"]
    cmd = [BODY, "-m", "torch.distributed.run", "--nproc_per_node=2", f"--master_port={29811 + slot}",
           "scripts/run_ptower_search.py", "action=finetune", *common]
    command(cmd, env, ROOT, work / "finetune.log", f"phase{number}_finetune", 16)
    first, second = pair.split(",")
    backbone = Path(json.loads((work / "finetune_last_run.json").read_text())["path"])
    checkpoint = backbone / "checkpoints/best.pth"

    def measure_backbone():
        command([BODY, "scripts/tower_search_records.py", "phase", str(work), "--action", "finetune"],
                environment(first, work), ROOT, work / "finetune_records.log", f"phase{number}_train_eval", 2)
        publish_phase(work, "finetune")
        record_run("phase", number, "finetune", backbone, first)

    def extract():
        command([BODY, "scripts/run_ptower_search.py", "action=extract", f"checkpoint={checkpoint}", *common],
                environment(second, work), ROOT, work / "extract.log", f"phase{number}_extract", 2)
        command([BODY, "scripts/tower_search_records.py", "phase", str(work), "--action", "extract"],
                environment("", work), ROOT, work / "extract_records.log", f"phase{number}_extract_records", 1)
        extracted = publish_phase(work, "extract")
        record_run("phase", number, "extract", extracted, second)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(fn) for fn in (measure_backbone, extract)]
        for future in as_completed(futures):
            future.result()
    backbone_metrics = json.loads((backbone / "metrics.json").read_text())
    from run_stage1_ptower_r3 import heads
    recipes = heads()
    pending_heads = queue.Queue()
    for index in range(len(recipes)):
        pending_heads.put(index)

    def run_heads(gpu):
        results = []
        while True:
            try:
                index = pending_heads.get_nowait()
            except queue.Empty:
                return results
            recipe = recipes[index]
            head_work = work / f"head{index:02d}"
            head_work.mkdir(exist_ok=False)
            head_common = [arg for arg in common if not arg.startswith("+artifact_root=")]
            cmd = [BODY, "scripts/run_ptower_search.py", "action=train", *head_common,
               f"+artifact_root={head_work}",
               *(f"{key}={value}" for key, value in recipe.items())]
            head_env = environment(gpu, head_work)
            command(cmd, head_env, ROOT, head_work / "train.log", f"phase{number}_head{index}", 1)
            command([BODY, "scripts/tower_search_records.py", "phase", str(head_work), "--action", "train"],
                    head_env, ROOT, head_work / "records.log", f"phase{number}_head{index}_records", 1)
            run = publish_phase(head_work, "train")
            record_run("phase", number, f"head{index:02d}", run, gpu)
            metrics = json.loads((run / "metrics.json").read_text())
            results.append((index, {"recipe": recipe, "metrics": metrics, "run": str(run)}))

    head_results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_heads, gpu) for gpu in (first, second)]
        for future in as_completed(futures):
            head_results.extend(future.result())
    head_records = [r for _, r in sorted(head_results)]
    return {"kind": "phase", "point": point,
            "metric": max(r["metrics"]["phase_jaccard"] for r in head_records),
            "backbone_metrics": backbone_metrics, "heads": head_records,
            "work": str(work), "gpus": pair}


def run_point(kind, number, pair, slot):
    if (kind, number) not in handoff_points:
        free_pair(pair)
    tag = f"{kind}_point{number:02d}"
    with guard:
        active[pair] = tag
    status("running", stage="C" if number in (0, 13) and len(records) < 4 else "D")
    begin = time.monotonic()
    if (kind, number) in handoff_started:
        begin -= time.time() - datetime.fromisoformat(handoff_started[(kind, number)]).timestamp()
    verify_cmd = [BODY, str(ROOT / "tasks" / TASK / "prepare_inputs.py"),
                  "--verify", str(ANALYSIS / "image_input_lock.json")]
    suffix = "resume_before" if (kind, number) in handoff_points else "before"
    command(verify_cmd, environment("", SCRATCH), ROOT, SCRATCH / f"{tag}_input_{suffix}.log", tag + "_inputs", 1)
    try:
        result = detector_point(number, pair, slot) if kind == "detector" else phase_point(number, pair, slot)
    except RuntimeError:
        work = SCRATCH / kind / f"point{number:02d}"
        logs = list(work.glob("*.log"))
        nonfinite = any(any(token in p.read_text(errors="replace") for token in
                            ("Non-finite loss", "Loss is nan", "Loss is inf")) for p in logs)
        if not nonfinite or number == 0:
            raise
        result = {"kind": kind, "point": load_point(number), "metric": None,
                  "diverged": True, "work": str(work), "gpus": pair}
    command(verify_cmd, environment("", SCRATCH), ROOT, SCRATCH / f"{tag}_input_after.log", tag + "_inputs", 1)
    result.update(elapsed_seconds=time.monotonic() - begin, completed_jst=now())
    with guard:
        records.append(result)
        active.pop(pair, None)
        write_json(ANALYSIS / "point_records.json", records)
        divergent = sum(r.get("diverged", False) and r["kind"] == kind for r in records)
    if divergent >= 5:
        raise RuntimeError(f"Five or more divergent {kind} points; ask user")
    status("running")
    return result


def batch(jobs):
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(run_point, kind, number, PAIRS[slot], slot)
                   for slot, (kind, number) in enumerate(jobs)]
        for future in as_completed(futures):
            try:
                future.result()
            except BaseException:
                stopping.set()
                raise


def tables():
    tops = []
    for kind in ("phase", "detector"):
        selected = sorted((r for r in records if r["kind"] == kind),
                          key=lambda r: (r["metric"] is None, -(r["metric"] or 0), r["point"]["point"]))
        if len(selected) != 20:
            raise RuntimeError("Incomplete point table")
        valid = [r for r in selected if r["metric"] is not None]
        if len(valid) < 3:
            raise RuntimeError(f"Fewer than three valid {kind} points; ask user")
        zero = next(r["metric"] for r in valid if r["point"]["point"] == 0)
        with (ANALYSIS / f"results_{'ptower' if kind == 'phase' else 'dtower'}.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["rank", "point", "lr", "weight_decay", "accum_or_max_norm",
                                                       "primary", "co_primary", "difference_from_0", "diverged",
                                                       "reached_epoch_cap", "checkpoint_epoch", "run", "work"])
            writer.writeheader()
            writer.writerows({"rank": i if r["metric"] is not None else "excluded_diverged",
                              "point": r["point"]["point"], "primary": r["metric"],
                              "lr": r["point"]["lr"],
                              "weight_decay": r["point"]["phase_weight_decay" if kind == "phase" else "detector_weight_decay"],
                              "accum_or_max_norm": r["point"]["accum" if kind == "phase" else "max_norm"],
                              "co_primary": ((r["backbone_metrics"]["phase_accuracy"] if kind == "phase" else r["metrics"]["AP_target"])
                                             if r["metric"] is not None else None),
                              "diverged": r.get("diverged", False),
                              "reached_epoch_cap": ((r["backbone_metrics"] if kind == "phase" else r["metrics"])["reached_epoch_cap"]
                                                    if r["metric"] is not None else "UNKNOWN: diverged"),
                              "checkpoint_epoch": ((r["backbone_metrics"]["epoch"] if kind == "phase" else r["metrics"]["best_epoch"])
                                                   if r["metric"] is not None else "UNKNOWN: diverged"),
                              "run": (max(r["heads"], key=lambda h: h["metrics"]["phase_jaccard"])["run"] if kind == "phase"
                                      else r["run"]) if r["metric"] is not None else "UNKNOWN: diverged",
                              "difference_from_0": r["metric"] - zero if r["metric"] is not None else None,
                              "work": r["work"]}
                             for i, r in enumerate(selected, 1))
        ids = [r["point"]["point"] for r in valid[:3]]
        tops.append(f"{kind}: top3={ids}, first={ids[0]}, point0_in_top3={0 in ids}")
        metrics = [r["backbone_metrics"] if kind == "phase" else r["metrics"] for r in selected[:3]]
        if all(r["reached_epoch_cap"] for r in metrics):
            raise RuntimeError(f"Top three {kind} points all reached epoch cap; ask user")
    (ANALYSIS / "top3.md").write_text("# Exploration ranking; no final recipe selection\n\n" + "\n\n".join(tops) + "\n")


def gate_c():
    if ({(r["kind"], r["point"]["point"]) for r in records} !=
            {("detector", 0), ("detector", 13), ("phase", 0), ("phase", 13)} or
            len(records) != 4 or any(r.get("diverged") for r in records)):
        raise RuntimeError("G3: four successful points are required")
    expected = next(r["count"] for r in json.loads((ANALYSIS / "inputs_inventory.json").read_text())["items"]
                    if r["item"].startswith("B5b"))
    for record in records:
        work, point = Path(record["work"]), record["point"]
        if record["kind"] == "detector":
            for rank in (0, 1):
                init = json.loads((work / f"initialization_rank{rank}.json").read_text())
                if not init["matched"] or init["source_sha256"] != "2d2c19a7a49e7d77dfb1253bdeba8414785af9f0786fb51651b4a25325c6e8ff":
                    raise RuntimeError("G3: detector initialization differs")
                opt = json.loads((work / f"optimizer_rank{rank}.json").read_text())
                check_detector_groups(opt["groups"], point)
                if opt["max_norm"] != point["max_norm"] or opt["autocast"] != "fp16":
                    raise RuntimeError("G3: detector clipping or precision differs")
            if not (work / "posthoc_records.json").exists():
                raise RuntimeError("G3: detector measurements missing")
        else:
            if len(record["heads"]) != 10:
                raise RuntimeError("G3: ten temporal heads required")
            pointer = json.loads((work / "finetune_last_run.json").read_text())
            history = json.loads((Path(pointer["path"]) / "finetune_history.json").read_text())
            if history["world_size"] != 2 or history["backbone_init_sha256"] != expected:
                raise RuntimeError("G3: phase path or initialization differs")
            for rank in (0, 1):
                opt = json.loads((work / f"finetune_optimizer_rank{rank}.json").read_text())
                runtime = opt["runtime"]
                if (opt["groups"][0]["lr"] != point["lr"] or
                        opt["groups"][0]["weight_decay"] != point["phase_weight_decay"] or
                        opt["effective_batch"] != 16 * point["accum"]):
                    raise RuntimeError("G3: phase optimizer differs")
                if not runtime["deterministic_algorithms"] or runtime["tf32_matmul"] or runtime["tf32_cudnn"]:
                    raise RuntimeError("G3: phase determinism differs")


def remaining_points(jobs, resume=None):
    pending = queue.Queue()
    for job in jobs:
        pending.put(job)

    def worker(slot):
        try:
            if resume and PAIRS[slot] in resume:
                kind, number = resume[PAIRS[slot]]
                run_point(kind, number, PAIRS[slot], slot)
            while not stopping.is_set():
                try:
                    kind, number = pending.get_nowait()
                except queue.Empty:
                    return
                run_point(kind, number, PAIRS[slot], slot)
        except BaseException:
            stopping.set()
            raise

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, slot) for slot in range(2)]
        for future in futures:
            future.result()


def main():
    global current_stage
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume-handoff", type=Path)
    args = parser.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    gates = json.loads((ANALYSIS / "gates.json").read_text())
    if gates.get("G2", {}).get("verdict") != "pass":
        raise RuntimeError("G2 has not passed; training must not start")
    resume = None
    if args.resume_handoff:
        if gates.get("G3", {}).get("verdict") != "pass":
            raise RuntimeError("Handoff requires completed G3")
        handoff = json.loads(args.resume_handoff.read_text())
        if handoff["task_id"] != TASK:
            raise RuntimeError("Handoff belongs to another task")
        old = Path(f"/proc/{handoff['old_pid']}/stat").read_text().rpartition(") ")[2].split()
        if old[0] != "T" or old[19] != handoff["old_identity"]:
            raise RuntimeError("Previous supervisor must be stopped for an exclusive handoff")
        handoff_commands.update(handoff["commands"])
        adopted_roots.update({r["pid"]: r["identity"] for r in handoff_commands.values() if r["identity"] is not None})
        records.extend(json.loads((ANALYSIS / "point_records.json").read_text()))
        resume = {pair: (tag.split("_point")[0], int(tag.split("_point")[1]))
                  for pair, tag in handoff["active"].items()}
        handoff_points.update(resume.values())
        for pair, job in resume.items():
            handoff_started[job] = handoff["point_started_jst"][pair]
    elif (ANALYSIS / "point_records.json").exists():
        raise RuntimeError("Search records exist; do not start a duplicate supervisor")
    if resume:
        current_stage = "D"
    write_json(SCRATCH / "supervisor.json", {"pid": os.getpid(), "started_jst": now(),
                                            "handoff": str(args.resume_handoff) if args.resume_handoff else None,
                                            "training_command_wall_limit_hours": {"detector": 48, "phase": 16}})
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    try:
        if not resume:
            batch([("detector", 0), ("detector", 13)])
            batch([("phase", 0), ("phase", 13)])
            gate_c()
            gates["G3"] = {"verdict": "pass", "completed_points": 4, "time_jst": now()}
            write_json(ANALYSIS / "gates.json", gates)
            current_stage = "D"
        else:
            write_json(args.resume_handoff.with_suffix(".ready.json"), {
                "pid": os.getpid(), "time_jst": now(), "source": str(args.resume_handoff)})
        remaining = [i for i in range(1, 20) if i != 13]
        accounted = {(r["kind"], r["point"]["point"]) for r in records} | handoff_points
        jobs = [(kind, i) for i in remaining for kind in ("detector", "phase") if (kind, i) not in accounted]
        remaining_points(jobs, resume)
        if len(records) != 40:
            raise RuntimeError("G4: forty point records are required")
        gates["G4"] = {"verdict": "pass", "completed_points": 40, "time_jst": now(),
                       "evidence": "GPU0 owned-process guard active throughout; scratch/gpu_monitor.jsonl"}
        write_json(ANALYSIS / "gates.json", gates)
        tables()
        status("experiments_finished", elapsed_seconds=time.monotonic() - started,
               next="Task F: harvest, validation, report, PR, task-report; not yet complete")
    except BaseException as exc:
        stopping.set()
        status("stopped", reason=str(exc))
        with guard:
            children = list(processes.values())
        for proc in children:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
        for pid, identity in adopted_roots.items():
            if process_identity(pid) == identity:
                os.killpg(pid, signal.SIGTERM)
        raise
    finally:
        stopping.set()
        thread.join(timeout=15)


if __name__ == "__main__":
    main()
