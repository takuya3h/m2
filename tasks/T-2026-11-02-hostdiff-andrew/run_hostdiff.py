"""andrew 側のホスト差の測定（T-2026-11-02-hostdiff-andrew）。一度に一本ずつ、背景で回す。

起動は dlsta 探索の 0 番の手本（``scripts/run_tower_search.py`` の ``phase_point`` と ``detector_point``）と
同じ命令と同じ設定で組み立てる。手本と違うのは SPEC §4 の許した違いだけ:
経路、GPU の番号（このホストは 0 と 1）、seed、出力と記録の置き場、run の名前、
``NCCL_P2P_DISABLE=1``、本契約の識別子（``TOWER_SEARCH_TASK``）、観測器（``TOWER_SEARCH_OBSERVER``）。

手本の run は ``scripts/run_tower_search.py`` の 11ab3747（工程塔）と bce323bc（検出塔）の版で回った。
どちらも fine-tune と検出塔の学習の後は、一枚目の GPU だけで順に回す版である（二枚へ配る 3c562015 より前）。
本契約はその版の順と起こし方に合わせる。一度に一本しか回さない規則とも合う。

checkpoint・特徴・ログは repo の外（``~/m2-scratch/<task>/``）。repo へは手本と同じ型
（.json .yaml .md .txt .sh）だけを写す。

    source scripts/load_env.sh && .venv/bin/python tasks/T-2026-11-02-hostdiff-andrew/run_hostdiff.py <step>
    <step>: determinism | phase42 | phase123 | det42a | det42b | det123 | all
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[2]
TASK = "T-2026-11-02-hostdiff-andrew"
SCRATCH = Path.home() / "m2-scratch" / TASK
OBSERVER = ROOT / "tasks" / TASK / "tools/observer.py"
BODY = str(ROOT / ".venv/bin/python")
DET = str(ROOT / ".venv-relation-detr/bin/accelerate")
MANIFEST = "data/processed/phase_manifest_all_phase"
PAIR, FIRST, SECOND = "0,1", "0", "1"
PHASE_PUBLISH = "experiments/phase1/stage1_ptower_hostdiff_andrew"
DET_PUBLISH = ROOT / "experiments/baselines/stage1_dtower_hostdiff_andrew"
POINT = 0
DISK_FLOOR = 150_000_000_000

stopping = threading.Event()
active = {"tag": None}


def now():
    return datetime.now(ZoneInfo("Asia/Tokyo")).isoformat()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")


def status(state, **values):
    write_json(SCRATCH / "status.json", {"state": state, "time_jst": now(), "pid": os.getpid(),
                                         "active": active["tag"], **values})


def descendants():
    parents = {}
    for entry in Path("/proc").iterdir():
        if entry.name.isdigit():
            try:
                fields = (entry / "stat").read_text().rpartition(") ")[2].split()
                parents[int(entry.name)] = int(fields[1])
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                continue
    owned = {os.getpid()}
    while True:
        more = {pid for pid, parent in parents.items() if parent in owned} - owned
        if not more:
            return owned
        owned |= more


GPU_FIELDS = ["index", "uuid", "power.draw", "clocks.sm", "clocks.mem", "utilization.gpu",
              "memory.used", "temperature.gpu"]


def monitor():
    """10 秒ごとの GPU の標本と、本契約以外の compute プロセスの記録。"""
    with (SCRATCH / "gpu_monitor.jsonl").open("a", buffering=1) as output:
        while not stopping.is_set():
            try:
                rows = subprocess.check_output(
                    ["nvidia-smi", f"--query-gpu={','.join(GPU_FIELDS)}", "--format=csv,noheader,nounits"],
                    text=True, timeout=30).splitlines()
                gpus = [dict(zip(GPU_FIELDS, (v.strip() for v in r.split(",")))) for r in rows if r.strip()]
                apps = subprocess.check_output(
                    ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory",
                     "--format=csv,noheader,nounits"], text=True, timeout=30).splitlines()
                own = descendants()
                procs = []
                for line in apps:
                    if not line.strip():
                        continue
                    uuid, pid, memory = (v.strip() for v in line.split(","))
                    try:
                        exe = os.readlink(f"/proc/{int(pid)}/exe")
                    except (FileNotFoundError, PermissionError, ValueError):
                        exe = None
                    procs.append({"uuid": uuid, "pid": int(pid) if pid.isdigit() else pid,
                                  "memory": memory, "exe": exe,
                                  "owned": pid.isdigit() and int(pid) in own})
                output.write(json.dumps({"time_jst": now(), "t": time.time(), "gpus": gpus,
                                         "processes": procs, "active": active["tag"]}) + "\n")
            except Exception as exc:  # 標本の失敗は記録して続ける。学習は止めない
                output.write(json.dumps({"time_jst": now(), "t": time.time(),
                                         "error": f"{type(exc).__name__}: {exc}"}) + "\n")
            stopping.wait(10)


def environment(gpus, work, **extra):
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": gpus, "WANDB_MODE": "offline",
           "WANDB_DIR": str(work), "PYTHONPATH": str(ROOT / "src") + ":" + str(ROOT / "scripts"),
           "CUDA_HOME": "/usr/local/cuda", "NCCL_P2P_DISABLE": "1",
           "TOWER_SEARCH_TASK": TASK, "TOWER_SEARCH_OBSERVER": str(OBSERVER),
           "TOWER_SEARCH_PHASE_PUBLISH": PHASE_PUBLISH}
    env.pop("TOWER_SEARCH_CONTROL_STEPS", None)
    env.pop("TOWER_SEARCH_LOSS_HEX", None)
    env.update(extra)
    return env


REPLAY_KEYS = ("CUDA_VISIBLE_DEVICES", "WANDB_MODE", "WANDB_DIR", "PYTHONPATH", "CUDA_HOME",
               "EGO_ROOT", "EGO_ANN_DIR", "RELDETR_COCO_CKPT", "RELDETR_OUTPUT_DIR", "RELDETR_EVIDENCE_DIR",
               "DTOWER_LR", "DTOWER_WEIGHT_DECAY", "DTOWER_MAX_NORM", "DTOWER_EVAL_SPLIT", "TOWER_SEARCH_POINT",
               "NCCL_P2P_DISABLE", "TOWER_SEARCH_TASK", "TOWER_SEARCH_OBSERVER", "TOWER_SEARCH_PHASE_PUBLISH",
               "TOWER_SEARCH_SEED", "TOWER_SEARCH_LOSS_HEX")


def replay(cmd, env, cwd):
    return ("#!/usr/bin/env bash\nset -euo pipefail\ncd " + shlex.quote(str(ROOT)) +
            "\nsource scripts/load_env.sh\n" +
            "\n".join(f"export {key}={shlex.quote(env[key])}" for key in REPLAY_KEYS if key in env) +
            "\ncd " + shlex.quote(str(cwd)) + "\nexec " + shlex.join(cmd) + "\n")


def finetune_cmd(common):
    return [BODY, "-m", "torch.distributed.run", "--nproc_per_node=2", "--master_port=29811",
            "scripts/run_ptower_search.py", "action=finetune", *common]


def extract_cmd(checkpoint, common):
    return [BODY, "scripts/run_ptower_search.py", "action=extract", f"checkpoint={checkpoint}", *common]


def head_cmd(common, recipe):
    return [BODY, "scripts/run_ptower_search.py", "action=train", *common,
            *(f"{key}={value}" for key, value in recipe.items())]


def det_train_cmd(seed):
    return [DET, "launch", "--multi_gpu", "--num_processes", "2", "--main_process_port", "29801",
            str(ROOT / "scripts/train_relation_detr_search.py"), "--config-file",
            str(ROOT / "configs/detector_relation_detr/train_search.py"), "--seed", str(seed),
            "--mixed-precision", "fp16", "--convergence-schedule", "--max-epochs", "36"]


def det_eval_cmd(work, split):
    return [str(ROOT / ".venv-relation-detr/bin/python"), str(ROOT / "scripts/eval_relation_detr_map.py"),
            "--config", str(ROOT / "configs/detector_relation_detr/train_search.py"),
            "--checkpoint", str(work / "best_ap.pth"), "--out", str(work / f"eval_{split}.json")]


def command(cmd, env, cwd, log, tag, timeout_hours):
    """手本の ``command`` と同じ再生用の台本を書き、一本だけ回す。壁時計の時刻を返す。"""
    if stopping.is_set():
        raise RuntimeError("stopped")
    free = shutil.disk_usage(SCRATCH).free
    if free < DISK_FLOOR:
        status("stopped", reason=f"scratch free {free} B below floor")
        raise RuntimeError("Scratch free space below 150 GB; stop and ask")
    log.parent.mkdir(parents=True, exist_ok=True)
    log.with_suffix(".command.sh").write_text(replay(cmd, env, cwd))
    active["tag"] = tag
    status("running", log=str(log))
    begin_wall, begin = time.time(), time.monotonic()
    with log.open("w") as output:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT,
                                start_new_session=True)
        write_json(log.with_suffix(".command.json"), {"cmd": cmd, "pid": proc.pid, "time_jst": now(),
                                                    "tag": tag, "t_start": begin_wall})
        try:
            while proc.poll() is None:
                if stopping.wait(5) or time.monotonic() - begin > timeout_hours * 3600:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=120)
                    raise RuntimeError(f"stopped or wall time limit: {tag}")
        finally:
            active["tag"] = None
    timing = {"tag": tag, "t_start": begin_wall, "t_end": time.time(),
              "wall_s": time.monotonic() - begin, "returncode": proc.returncode,
              "start_jst": datetime.fromtimestamp(begin_wall, ZoneInfo("Asia/Tokyo")).isoformat(),
              "end_jst": now()}
    write_json(log.with_suffix(".timing.json"), timing)
    if proc.returncode:
        status("stopped", reason=f"exit={proc.returncode}: {tag}", log=str(log))
        raise RuntimeError(f"exit={proc.returncode}: {tag}; see {log}")
    return timing


def publish_phase(work, action, launch):
    """手本の ``publish_phase`` と同じ写し方。置き場と server.txt だけ違う。"""
    pointer = json.loads((work / f"{action}_last_run.json").read_text())
    source = Path(pointer["path"])
    dest = ROOT / PHASE_PUBLISH / pointer["exp_id"]
    for file in source.iterdir():
        if file.is_file() and file.suffix in (".json", ".yaml", ".md", ".txt", ".sh"):
            shutil.copy2(file, dest / file.name)
    shutil.copy2(work / f"{launch}.command.sh", dest / "command.sh")
    (dest / "server.txt").write_text("andrew\n")
    with (dest / "notes.md").open("a") as handle:
        handle.write(f"\nArtifacts, checkpoints and raw logs: {source}\n")
    return source, dest


def phase_common(work, seed):
    common = [f"+point_id={POINT}", f"+artifact_root={work}", f"manifest_dir={MANIFEST}",
              f"cache={work / 'features/all_gap.npz'}", "workers=4"]
    return common + ([] if seed == 42 else [f"seed={seed}"])


def run_phase(seed):
    """手本の時点（11ab3747）の ``phase_point`` と同じ順。fine-tune の後はすべて一枚目の GPU で順に回す。"""
    work = SCRATCH / "phase" / f"seed{seed}"
    work.mkdir(parents=True, exist_ok=False)
    env = environment(PAIR, work)
    single = environment(FIRST, work)
    common = phase_common(work, seed)
    timings = {"finetune": command(finetune_cmd(common), env, ROOT, work / "finetune.log",
                                   f"phase{seed}_finetune", 16)}
    timings["finetune_records"] = command(
        [BODY, "scripts/tower_search_records.py", "phase", str(work), "--action", "finetune"],
        single, ROOT, work / "finetune_records.log", f"phase{seed}_train_eval", 2)
    backbone, _ = publish_phase(work, "finetune", "finetune")
    checkpoint = backbone / "checkpoints/best.pth"
    timings["extract"] = command(extract_cmd(checkpoint, common), single, ROOT, work / "extract.log",
                                 f"phase{seed}_extract", 2)
    timings["extract_records"] = command(
        [BODY, "scripts/tower_search_records.py", "phase", str(work), "--action", "extract"],
        single, ROOT, work / "extract_records.log", f"phase{seed}_extract_records", 1)
    publish_phase(work, "extract", "extract")
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_stage1_ptower_r3 import heads
    for index, recipe in enumerate(heads()):
        timings[f"head{index:02d}"] = command(head_cmd(common, recipe), single, ROOT,
                                              work / f"head{index:02d}.log", f"phase{seed}_head{index}", 1)
        timings[f"head{index:02d}_records"] = command(
            [BODY, "scripts/tower_search_records.py", "phase", str(work), "--action", "train"],
            single, ROOT, work / f"head{index:02d}_records.log", f"phase{seed}_head{index}_records", 1)
        publish_phase(work, "train", f"head{index:02d}")
    write_json(work / "timings.json", timings)
    return timings


def detector_env(gpus, work, seed):
    return environment(gpus, work,
                       EGO_ROOT=str(ROOT / "data/raw/ego"),
                       EGO_ANN_DIR=str(ROOT / "data/annotations/egosurgery_tool_folds/A"),
                       RELDETR_COCO_CKPT=str(ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"),
                       RELDETR_OUTPUT_DIR=str(work), RELDETR_EVIDENCE_DIR=str(work),
                       DTOWER_LR="0.0001", DTOWER_WEIGHT_DECAY="0.0001", DTOWER_MAX_NORM="0.1",
                       TOWER_SEARCH_POINT=str(POINT), TOWER_SEARCH_SEED=str(seed))


def run_detector(seed, tag):
    name = f"seed{seed}{tag}"
    work = SCRATCH / "detector" / name
    work.mkdir(parents=True, exist_ok=False)
    out = DET_PUBLISH / f"point00_dcoco_foldA_{name}"
    out.mkdir(parents=True, exist_ok=False)
    env = detector_env(PAIR, work, seed)
    config = {"task_id": TASK, "point_id": POINT,
              "point": {"point": 0, "lr": 0.0001, "phase_S": 3.3e-05, "phase_weight_decay": 0.0001,
                        "accum": 4, "detector_S": 0.00048, "detector_weight_decay": 0.0001, "max_norm": 0.1},
              "seed": seed, "fold": "A", "kind": "detector", "gpus": PAIR, "work": str(work),
              "epochs": 36, "mixed_precision": "fp16", "repeat": tag or None}
    (out / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False))
    (out / "git_commit.txt").write_text(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True))
    (out / "notes.md").write_text(f"Artifacts and raw logs: {work}\nValidation selection only; no test evaluation.\n")
    timings = {"train": command(det_train_cmd(seed), env, ROOT / "third_party/Relation-DETR", work / "train.log",
                                f"detector_{name}", 48)}
    shutil.copy2(work / "train.command.sh", out / "command.sh")
    for split in ("val", "train"):
        eval_env = {**env, "CUDA_VISIBLE_DEVICES": FIRST, "DTOWER_EVAL_SPLIT": split}
        timings[f"eval_{split}"] = command(det_eval_cmd(work, split), eval_env, ROOT, work / f"eval_{split}.log",
                                           f"detector_{name}_{split}", 8)
        text = (work / f"eval_{split}.log").read_text()
        if "skip loading" in text or "State dict is None" in text:
            raise RuntimeError("Detector evaluator skipped checkpoint loading")
    timings["records"] = command([BODY, str(ROOT / "scripts/tower_search_records.py"), "detector", str(work)],
                                 environment("", work), ROOT, work / "records.log", f"detector_{name}_records", 1)
    write_json(out / "metrics.json", json.loads((work / "search_metrics.json").read_text()))
    val = json.loads((work / "eval_val.json").read_text())
    write_json(out / "per_class_ap.json", {k: v for k, v in val["per_class_ap"].items() if math.isfinite(v)})
    shutil.copy2(work / "posthoc_records.json", out / "posthoc_records.json")
    shutil.copy2(work / "convergence.json", out / "convergence.json")
    shutil.copy2(work / "wandb/wandb_run.json", out / "wandb_run.json")
    (out / "server.txt").write_text("andrew\n")
    write_json(work / "timings.json", timings)
    return timings


def run_determinism():
    """同じ seed・0 番の設定の fine-tune を、最初の 50 optimizer step（200 micro-step）だけ二度回す。"""
    results = []
    for trial in ("a", "b"):
        work = SCRATCH / "determinism" / trial
        work.mkdir(parents=True, exist_ok=False)
        cmd = finetune_cmd(phase_common(work, 42)) + ["+control_frames=3200", "ft_epochs=1"]
        env = environment(PAIR, work, TOWER_SEARCH_LOSS_HEX="1")
        timing = command(cmd, env, ROOT, work / "finetune.log", f"determinism_{trial}", 2)
        results.append({"trial": trial, "work": str(work), "timing": timing})
    write_json(SCRATCH / "determinism" / "runs.json", results)
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=("determinism", "phase42", "phase123", "det42a", "det42b",
                                         "det123", "measure"))
    args = parser.parse_args()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    thread = threading.Thread(target=monitor, daemon=True)
    thread.start()
    steps = {"determinism": [run_determinism],
             "phase42": [lambda: run_phase(42)], "phase123": [lambda: run_phase(123)],
             "det42a": [lambda: run_detector(42, "a")], "det42b": [lambda: run_detector(42, "b")],
             "det123": [lambda: run_detector(123, "")]}
    steps["measure"] = steps["phase42"] + steps["phase123"] + steps["det42a"] + steps["det42b"] + steps["det123"]
    try:
        for step in steps[args.step]:
            step()
        status("done", step=args.step)
    except BaseException as exc:
        status("stopped", step=args.step, reason=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        stopping.set()
        thread.join(timeout=30)


if __name__ == "__main__":
    main()
