"""bengio 側のホスト差の測定の起動（T-2026-11-02-hostdiff-bengio）。

dlsta 探索の 0 番の run（`scripts/run_tower_search.py` の ``phase_point`` と ``detector_point``）と同じ命令を、
許した違い（経路・GPU の番号・ポート・seed・置き場・run の名前・``NCCL_P2P_DISABLE=1``・本契約の識別子）だけを
変えて起こす。一度に走らせる塔の run は一本。塔の run の中の段取り（記録の評価と取り出しの並行、ヘッドを
GPU 2 枚で 2 本ずつ）は手本どおり（利用者の決定 2026-11-02）。

    python run_hostdiff.py <run> [--dry-run]
      run: control1 control2 phase42 phase123 det42a det42b det123

checkpoint・特徴・ログ・GPU の標本は repo の外（``SCR``）に置く。repo には公開の道具が
.json/.yaml/.md/.txt/.sh だけを写す（同期の型を置かない）。
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK_ID = "T-2026-11-02-hostdiff-bengio"
SCR = Path.home() / "m2-scratch" / TASK_ID
PAIR = "0,1"
BODY = str(ROOT / ".venv/bin/python")
DET = str(ROOT / ".venv-relation-detr/bin/accelerate")
MANIFEST = "data/processed/phase_manifest_all_phase"
PHASE_PUBLISH = "experiments/phase1/stage1_ptower_hostdiff_bengio"
DET_PUBLISH = ROOT / "experiments/baselines/stage1_dtower_hostdiff_bengio"
POINT = {"point": 0, "lr": 0.0001, "phase_S": 3.3e-05, "phase_weight_decay": 0.0001, "accum": 4,
         "detector_S": 0.00048, "detector_weight_decay": 0.0001, "max_norm": 0.1}
KEYS = ("CUDA_VISIBLE_DEVICES", "WANDB_MODE", "WANDB_DIR", "PYTHONPATH", "CUDA_HOME",
        "EGO_ROOT", "EGO_ANN_DIR", "RELDETR_COCO_CKPT", "RELDETR_OUTPUT_DIR", "RELDETR_EVIDENCE_DIR",
        "DTOWER_LR", "DTOWER_WEIGHT_DECAY", "DTOWER_MAX_NORM", "DTOWER_EVAL_SPLIT", "TOWER_SEARCH_POINT",
        # 以下は本契約が足した（許した違い）
        "NCCL_P2P_DISABLE", "TOWER_SEARCH_TASK", "TOWER_SEARCH_SCRATCH", "TOWER_SEARCH_PHASE_PUBLISH",
        "TOWER_SEARCH_STEP_LOG", "TOWER_SEARCH_LOSS_LOG")
DRY = False
EVENTS = []


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def event(**kw):
    kw["t_utc"] = now()
    kw["t_mono"] = time.monotonic()
    EVENTS.append(kw)
    print(json.dumps(kw, ensure_ascii=False), flush=True)


def environment(gpus, work):
    return {**os.environ, "CUDA_VISIBLE_DEVICES": gpus, "WANDB_MODE": "offline",
            "WANDB_DIR": str(work), "PYTHONPATH": str(ROOT / "src") + ":" + str(ROOT / "scripts"),
            "CUDA_HOME": "/usr/local/cuda", "NCCL_P2P_DISABLE": "1", "TOWER_SEARCH_TASK": TASK_ID,
            "TOWER_SEARCH_SCRATCH": str(SCR), "TOWER_SEARCH_PHASE_PUBLISH": PHASE_PUBLISH}


def detector_environment(gpus, work):
    env = environment(gpus, work)
    env.update(EGO_ROOT=str(ROOT / "data/raw/ego"),
               EGO_ANN_DIR=str(ROOT / "data/annotations/egosurgery_tool_folds/A"),
               RELDETR_COCO_CKPT=str(ROOT / "data/external/weights/relation_detr_resnet50_800_1333_coco_1x.pth"),
               RELDETR_OUTPUT_DIR=str(work), RELDETR_EVIDENCE_DIR=str(work),
               DTOWER_LR=str(POINT["lr"]), DTOWER_WEIGHT_DECAY=str(POINT["detector_weight_decay"]),
               DTOWER_MAX_NORM=str(POINT["max_norm"]), TOWER_SEARCH_POINT=str(POINT["point"]))
    env.pop("TOWER_SEARCH_CONTROL_STEPS", None)
    return env


def command(cmd, env, cwd, log, tag):
    """手本の ``command`` と同じ形の再現台本を書いてから起こす。経過秒を返す。"""
    log.parent.mkdir(parents=True, exist_ok=True)
    replay = ("#!/usr/bin/env bash\nset -euo pipefail\ncd " + shlex.quote(str(ROOT)) +
              "\nsource scripts/load_env.sh\n" +
              "\n".join(f"export {key}={shlex.quote(env[key])}" for key in KEYS if key in env) +
              "\ncd " + shlex.quote(str(cwd)) + "\nexec " + shlex.join(cmd) + "\n")
    log.with_suffix(".command.sh").write_text(replay)
    if DRY:
        return 0.0
    event(kind="start", tag=tag, log=str(log), gpus=env.get("CUDA_VISIBLE_DEVICES"))
    begin = time.monotonic()
    with log.open("w") as output:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=output, stderr=subprocess.STDOUT,
                                start_new_session=True)
        (log.with_suffix(".command.json")).write_text(json.dumps({"cmd": cmd, "pid": proc.pid, "time_utc": now(),
                                                                  "tag": tag}, indent=1))
        code = proc.wait()
    seconds = time.monotonic() - begin
    event(kind="end", tag=tag, exit=code, seconds=seconds)
    if code:
        raise RuntimeError(f"exit={code}: {tag}; see {log}")
    text = log.read_text(errors="replace")
    for token in ("Non-finite loss", "Loss is nan", "Loss is inf"):
        if token in text:
            raise RuntimeError(f"{token}: {tag}")
    return seconds


class GpuSampler:
    """10 秒ごとに GPU と compute アプリを標本にとる。本契約の子孫でないプロセスを他の使用として数える。"""

    def __init__(self, path):
        self.path, self.stop = path, threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)

    def descendants(self):
        mine, children = {os.getpid()}, {}
        for p in Path("/proc").iterdir():
            if p.name.isdigit():
                try:
                    ppid = int((p / "stat").read_text().rsplit(")", 1)[1].split()[1])
                except (OSError, IndexError, ValueError):
                    continue
                children.setdefault(ppid, []).append(int(p.name))
        stack = [os.getpid()]
        while stack:
            for c in children.get(stack.pop(), []):
                if c not in mine:
                    mine.add(c)
                    stack.append(c)
        return mine

    def run(self):
        q = ("index,uuid,power.draw,clocks.sm,clocks.mem,utilization.gpu,memory.used,temperature.gpu,"
             "power.limit,pcie.link.gen.current,pcie.link.width.current")
        with self.path.open("a", buffering=1) as handle:
            while not self.stop.is_set():
                try:
                    gpus = subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"],
                                          capture_output=True, text=True, timeout=30).stdout.strip().splitlines()
                    apps = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,gpu_uuid,used_memory",
                                           "--format=csv,noheader,nounits"],
                                          capture_output=True, text=True, timeout=30).stdout.strip().splitlines()
                    mine = self.descendants()
                    rows = [dict(zip(q.split(","), [x.strip() for x in line.split(",")])) for line in gpus]
                    procs = [dict(zip(("pid", "gpu_uuid", "used_memory"), [x.strip() for x in a.split(",")]))
                             for a in apps if a.strip()]
                    foreign = [p for p in procs if p["pid"].isdigit() and int(p["pid"]) not in mine]
                    handle.write(json.dumps({"t_utc": now(), "t_mono": time.monotonic(), "gpus": rows,
                                             "apps": procs, "foreign": foreign}) + "\n")
                except Exception as exc:  # noqa: BLE001
                    handle.write(json.dumps({"t_utc": now(), "error": repr(exc)}) + "\n")
                self.stop.wait(10)

    def __enter__(self):
        if not DRY:
            self.thread.start()
        return self

    def __exit__(self, *exc):
        self.stop.set()
        if not DRY:
            self.thread.join(timeout=60)


def publish_phase(work, action, launch, dest_root):
    pointer = json.loads((work / f"{action}_last_run.json").read_text())
    source = Path(pointer["path"])
    dest = dest_root / pointer["exp_id"]
    dest.mkdir(parents=True, exist_ok=True)
    for file in source.iterdir():
        if file.is_file() and file.suffix in (".json", ".yaml", ".md", ".txt", ".sh"):
            shutil.copy2(file, dest / file.name)
    shutil.copy2(work / f"{launch}.command.sh", dest / "command.sh")
    (dest / "server.txt").write_text("bengio\n")
    with (dest / "notes.md").open("a") as handle:
        handle.write(f"\nArtifacts, checkpoints and raw logs: {source}\n")
    return source, dest


def control(name):
    """Task B: 0 番の設定で backbone を短く（optimizer step 50）学ぶ。本測定に数えない。公開しない。"""
    work = SCR / "controls" / name
    work.mkdir(parents=True, exist_ok=DRY)
    env = environment(PAIR, work)
    env.update(TOWER_SEARCH_STEP_LOG=str(work / "steps"), TOWER_SEARCH_LOSS_LOG="1")
    frames = 50 * POINT["accum"] * 16
    cmd = [BODY, "-m", "torch.distributed.run", "--nproc_per_node=2", "--master_port=29811",
           "scripts/run_ptower_search.py", "action=finetune", "+point_id=0", f"+artifact_root={work}",
           f"manifest_dir={MANIFEST}", f"cache={work / 'features/all_gap.npz'}", "workers=4",
           f"+control_frames={frames}", "ft_epochs=1"]
    with GpuSampler(work / "gpu.jsonl"):
        command(cmd, env, ROOT, work / "finetune.log", f"{name}_finetune")


def phase(seed):
    from run_stage1_ptower_r3 import heads
    work = SCR / "phase" / f"seed{seed}"
    work.mkdir(parents=True, exist_ok=DRY)
    dest_root = ROOT / PHASE_PUBLISH
    env = environment(PAIR, work)
    env["TOWER_SEARCH_STEP_LOG"] = str(work / "steps")
    cache = work / "features/all_gap.npz"
    common = ["+point_id=0", f"+artifact_root={work}", f"manifest_dir={MANIFEST}", f"cache={cache}", "workers=4"]
    if seed != 42:
        common.append(f"seed={seed}")
    timing = {}
    with GpuSampler(work / "gpu.jsonl"):
        begin = time.monotonic()
        cmd = [BODY, "-m", "torch.distributed.run", "--nproc_per_node=2", "--master_port=29811",
               "scripts/run_ptower_search.py", "action=finetune", *common]
        timing["finetune_s"] = command(cmd, env, ROOT, work / "finetune.log", f"phase{seed}_finetune")
        if DRY:
            backbone = work / "runs/DRY"
        else:
            backbone = Path(json.loads((work / "finetune_last_run.json").read_text())["path"])
        checkpoint = backbone / "checkpoints/best.pth"
        first, second = PAIR.split(",")

        def measure_backbone():
            t = command([BODY, "scripts/tower_search_records.py", "phase", str(work), "--action", "finetune"],
                        environment(first, work), ROOT, work / "finetune_records.log", f"phase{seed}_train_eval")
            if not DRY:
                publish_phase(work, "finetune", "finetune", dest_root)
            return ("finetune_records_s", t)

        def extract():
            t = command([BODY, "scripts/run_ptower_search.py", "action=extract", f"checkpoint={checkpoint}", *common],
                        environment(second, work), ROOT, work / "extract.log", f"phase{seed}_extract")
            t2 = command([BODY, "scripts/tower_search_records.py", "phase", str(work), "--action", "extract"],
                         environment("", work), ROOT, work / "extract_records.log", f"phase{seed}_extract_records")
            if not DRY:
                publish_phase(work, "extract", "extract", dest_root)
            return ("features_s", t), ("extract_records_s", t2)

        with ThreadPoolExecutor(max_workers=2) as pool:
            a = pool.submit(measure_backbone)
            b = pool.submit(extract)
            timing.update([a.result()])
            timing.update(b.result())
        recipes = heads()
        pending = queue.Queue()
        for index in range(len(recipes)):
            pending.put(index)
        head_times = {}
        heads_begin = time.monotonic()

        def run_heads(gpu):
            while True:
                try:
                    index = pending.get_nowait()
                except queue.Empty:
                    return
                recipe = recipes[index]
                head_work = work / f"head{index:02d}"
                head_work.mkdir(exist_ok=DRY)
                # 手本のヘッドの起動と同じ引数の順（+artifact_root は +point_id の直後）。置き場だけヘッドごとに分ける
                head_common = [f"+artifact_root={head_work}" if arg.startswith("+artifact_root=") else arg
                               for arg in common]
                cmd = [BODY, "scripts/run_ptower_search.py", "action=train", *head_common,
                       *(f"{k}={v}" for k, v in recipe.items())]
                head_env = environment(gpu, head_work)
                t = command(cmd, head_env, ROOT, head_work / "train.log", f"phase{seed}_head{index}")
                command([BODY, "scripts/tower_search_records.py", "phase", str(head_work), "--action", "train"],
                        head_env, ROOT, head_work / "records.log", f"phase{seed}_head{index}_records")
                if not DRY:
                    publish_phase(head_work, "train", "train", dest_root)
                head_times[index] = t

        with ThreadPoolExecutor(max_workers=2) as pool:
            for f in [pool.submit(run_heads, g) for g in (first, second)]:
                f.result()
        timing["heads_s"] = time.monotonic() - heads_begin
        timing["head_s"] = [head_times.get(i) for i in range(len(recipes))]
        timing["wall_s"] = time.monotonic() - begin
    (work / "timing.json").write_text(json.dumps(timing, indent=1))


def detector(label, seed):
    work = SCR / "detector" / label
    work.mkdir(parents=True, exist_ok=DRY)
    env = detector_environment(PAIR, work)
    env["TOWER_SEARCH_STEP_LOG"] = str(work / "steps")
    out = DET_PUBLISH / f"{label}_dcoco_foldA_seed{seed}"
    out.mkdir(parents=True, exist_ok=DRY)
    config = {"task_id": TASK_ID, "point_id": 0, "point": POINT, "seed": seed, "fold": "A", "kind": "detector",
              "gpus": PAIR, "work": str(work), "epochs": 36, "mixed_precision": "fp16", "label": label}
    (out / "config.yaml").write_text(json.dumps(config, ensure_ascii=False, indent=1))
    (out / "git_commit.txt").write_text(subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True))
    (out / "notes.md").write_text(f"Artifacts and raw logs: {work}\nValidation selection only; no test evaluation.\n")
    cmd = [DET, "launch", "--multi_gpu", "--num_processes", "2", "--main_process_port", "29801",
           str(ROOT / "scripts/train_relation_detr_search.py"), "--config-file",
           str(ROOT / "configs/detector_relation_detr/train_search.py"), "--seed", str(seed),
           "--mixed-precision", "fp16", "--convergence-schedule", "--max-epochs", "36"]
    timing = {}
    with GpuSampler(work / "gpu.jsonl"):
        begin = time.monotonic()
        timing["train_s"] = command(cmd, env, ROOT / "third_party/Relation-DETR", work / "train.log", f"{label}")
        shutil.copy2(work / "train.command.sh", out / "command.sh")
        for split in ("val", "train"):
            eval_env = {**env, "DTOWER_EVAL_SPLIT": split}
            eval_env.pop("TOWER_SEARCH_STEP_LOG", None)
            cmd = [DET, "launch", "--multi_gpu", "--num_processes", "2", "--mixed_precision", "no",
                   "--main_process_port", "29821", str(ROOT / "scripts/eval_relation_detr_map.py"),
                   "--config", str(ROOT / "configs/detector_relation_detr/train_search.py"),
                   "--checkpoint", str(work / "best_ap.pth"), "--out", str(work / f"eval_{split}.json")]
            timing[f"eval_{split}_s"] = command(cmd, eval_env, ROOT, work / f"eval_{split}.log", f"{label}_{split}")
            if not DRY:
                text = (work / f"eval_{split}.log").read_text()
                if "skip loading" in text or "State dict is None" in text:
                    raise RuntimeError("Detector evaluator skipped checkpoint loading")
        command([BODY, str(ROOT / "scripts/tower_search_records.py"), "detector", str(work)],
                environment("", work), ROOT, work / "records.log", f"{label}_records")
        timing["wall_s"] = time.monotonic() - begin
    if not DRY:
        shutil.copy2(work / "search_metrics.json", out / "metrics.json")
        val = json.loads((work / "eval_val.json").read_text())
        import math
        (out / "per_class_ap.json").write_text(json.dumps(
            {k: v for k, v in val["per_class_ap"].items() if math.isfinite(v)}, indent=2))
        for name in ("posthoc_records.json", "convergence.json"):
            shutil.copy2(work / name, out / name)
        shutil.copy2(work / "wandb/wandb_run.json", out / "wandb_run.json")
        (out / "server.txt").write_text("bengio\n")
    (work / "timing.json").write_text(json.dumps(timing, indent=1))


def main():
    global DRY, SCR, DET_PUBLISH
    ap = argparse.ArgumentParser()
    ap.add_argument("run", choices=("control1", "control2", "phase42", "phase123", "det42a", "det42b", "det123"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    DRY = a.dry_run
    if DRY:  # 書き出すだけ。repo の中に置き場を作らない
        SCR = SCR / "dry"
        DET_PUBLISH = SCR / "dry_publish"
    sys.path.insert(0, str(ROOT / "scripts"))
    os.chdir(ROOT)
    event(kind="run_start", run=a.run, dry=DRY)
    try:
        if a.run.startswith("control"):
            control(a.run)
        elif a.run.startswith("phase"):
            phase(int(a.run[5:]))
        else:
            detector(a.run[3:], int(a.run[3:].rstrip("ab")))
        event(kind="run_end", run=a.run, ok=True)
    except Exception as exc:
        event(kind="run_end", run=a.run, ok=False, error=repr(exc))
        raise
    finally:
        if not DRY:
            (SCR / f"events_{a.run}.json").write_text(json.dumps(EVENTS, indent=1))


if __name__ == "__main__":
    main()
