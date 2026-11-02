"""Task E: 5 本の run の記録から values.json を作る（読むだけ。書くのは --out の一か所）。

値はすべて run の記録から取る。取れない欄は ``{"UNKNOWN": "<理由>"}`` にする。相手のホストは読まない。

    .venv/bin/python tasks/T-2026-11-02-hostdiff-andrew/tools/aggregate.py --out <values.json>
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TASK = "T-2026-11-02-hostdiff-andrew"
SCRATCH = Path.home() / "m2-scratch" / TASK
PHASE_PUBLISH = ROOT / "experiments/phase1/stage1_ptower_hostdiff_andrew"
DET_PUBLISH = ROOT / "experiments/baselines/stage1_dtower_hostdiff_andrew"
SKIP_STEPS = 50
GPU_KEYS = {"power_W": "power.draw", "sm_clock_MHz": "clocks.sm", "mem_clock_MHz": "clocks.mem",
            "utilization_pct": "utilization.gpu", "memory_MiB": "memory.used", "temperature_C": "temperature.gpu"}


def unknown(reason):
    return {"UNKNOWN": reason}


def load(path):
    return json.loads(Path(path).read_text())


def stats(values):
    values = [float(v) for v in values]
    if not values:
        return unknown("no samples")
    return {"n": len(values), "mean": statistics.fmean(values), "median": statistics.median(values)}


def steps(work, rank=0):
    path = Path(work) / f"step_times_rank{rank}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def intervals(rows, kind, key):
    """同じ epoch の中の、連続する ``kind`` の記録の時刻の差。run の最初の SKIP_STEPS 歩を除く。"""
    marks = [(r["epoch"], r[key]) for r in rows if r["kind"] == kind]
    out = []
    for index in range(1, len(marks)):
        if index <= SKIP_STEPS:
            continue
        (e0, t0), (e1, t1) = marks[index - 1], marks[index]
        if e0 == e1:
            out.append(t1 - t0)
    return out


def epoch_spans(rows, start_kind, end_kind):
    starts = {r["epoch"]: r["t"] for r in rows if r["kind"] == start_kind}
    ends = {r["epoch"]: r["t"] for r in rows if r["kind"] == end_kind}
    return [{"epoch": e, "seconds": ends[e] - starts[e]} for e in sorted(starts) if e in ends]


def gpu_window(t0, t1):
    rows = []
    for line in (SCRATCH / "gpu_monitor.jsonl").read_text().splitlines():
        r = json.loads(line)
        if "gpus" in r and t0 <= r["t"] <= t1:
            rows.append(r)
    per_gpu = {}
    for r in rows:
        for g in r["gpus"]:
            slot = per_gpu.setdefault(g["index"], {k: [] for k in GPU_KEYS})
            for name, field in GPU_KEYS.items():
                try:
                    slot[name].append(float(g[field]))
                except ValueError:
                    pass
    return {"samples": len(rows), "interval_s": 10,
            "per_gpu": {i: {k: stats(v) for k, v in s.items()} for i, s in per_gpu.items()}}


def foreign(t0, t1):
    """本契約以外の compute プロセスが標本に出た区間（連続する標本をまとめる）。"""
    spans, current = [], None
    for line in (SCRATCH / "gpu_monitor.jsonl").read_text().splitlines():
        r = json.loads(line)
        if "gpus" not in r or not t0 <= r["t"] <= t1:
            continue
        others = [p for p in r["processes"] if not p["owned"]]
        if others:
            util = {g["index"]: g["utilization.gpu"] for g in r["gpus"]}
            if current is None:
                current = {"start_jst": r["time_jst"], "end_jst": r["time_jst"], "samples": 0,
                           "processes": {}, "utilization_pct": []}
            current["end_jst"] = r["time_jst"]
            current["samples"] += 1
            current["utilization_pct"].append(util)
            for p in others:
                current["processes"][str(p["pid"])] = {"exe": p["exe"], "memory_MiB": p["memory"],
                                                      "gpu_uuid": p["uuid"]}
        elif current is not None:
            spans.append(current)
            current = None
    if current is not None:
        spans.append(current)
    return spans


def coco_line(log, text):
    return any(text in line for line in Path(log).read_text(errors="replace").splitlines())


def phase(seed):
    work = SCRATCH / "phase" / f"seed{seed}"
    if not (work / "timings.json").exists():
        return unknown(f"run not finished: {work / 'timings.json'} missing")
    timings = load(work / "timings.json")
    backbone = Path(load(work / "finetune_last_run.json")["path"])
    bm = load(backbone / "metrics.json")
    runs = sorted((work / "runs/phase1").iterdir())
    heads = [r for r in runs if "_P15_" in r.name]
    if len(heads) != 10:
        return unknown(f"expected 10 head runs, found {len(heads)}")
    head_rows = []
    for index, run in enumerate(heads):
        m = load(PHASE_PUBLISH / run.name / "metrics.json")
        head_rows.append({"index": index, "run": run.name, "val_macro_jaccard": m["phase_jaccard"],
                          "epochs_completed": m.get("epochs_completed"), "best_epoch": m.get("epoch")})
    j = [h["val_macro_jaccard"] for h in head_rows]
    rows = steps(work)
    train = epoch_spans(rows, "epoch_start", "val_start")
    val = epoch_spans(rows, "val_start", "val_end")
    ft = timings["finetune"]
    last = max(timings.values(), key=lambda t: t["t_end"])
    init = load(work / "finetune_initialization_rank0.json")
    return {
        "J_heads": j, "J_mean": statistics.fmean(j), "J_max": max(j), "heads": head_rows,
        "backbone_val_frame_acc": bm["phase_accuracy"],
        "lr_drop_epoch": bm["lr_lowered_epoch"], "stop_epoch": bm["early_stopped_epoch"],
        "checkpoint_epoch": bm["epoch"], "epochs_completed": bm["epochs_completed"],
        "cap_reached": bm["reached_epoch_cap"],
        "epoch_numbering": "1 始まり",
        "coco_loaded": bool(init.get("matched")) and coco_line(work / "finetune.log", "load pretrained COCO backbone"),
        "coco_init_sha256": init.get("backbone_init_sha256"),
        "runtime_read_by_process": load(work / "finetune_optimizer_rank0.json").get("runtime"),
        "backbone_run": backbone.name,
        "timing": {
            "wall_s": last["t_end"] - ft["t_start"], "start_jst": ft["start_jst"], "end_jst": last["end_jst"],
            "finetune_wall_s": ft["wall_s"],
            "train_s_per_epoch": {"per_epoch": train, "median": statistics.median(x["seconds"] for x in train)},
            "s_per_step_median": {
                "micro_step": statistics.median(intervals(rows, "micro", "t0")),
                "optimizer_step": statistics.median(intervals(rows, "opt", "t")),
                "skipped_first_steps": SKIP_STEPS, "rank": 0},
            "eval_s": {"per_epoch_val": val, "total": sum(x["seconds"] for x in val),
                       "train_eval_wall_s": timings["finetune_records"]["wall_s"]},
            "features_s": timings["extract"]["wall_s"],
            "heads_s": sum(timings[f"head{i:02d}"]["wall_s"] for i in range(10)),
            "heads_records_s": sum(timings[f"head{i:02d}_records"]["wall_s"] for i in range(10)),
        },
        "gpu": gpu_window(ft["t_start"], ft["t_end"]),
        "gpu_window": "fine-tune の起動から終わりまで",
        "foreign_gpu_use": foreign(ft["t_start"], last["t_end"]),
    }


def detector(name):
    work = SCRATCH / "detector" / name
    if not (work / "timings.json").exists():
        return unknown(f"run not finished: {work / 'timings.json'} missing")
    timings = load(work / "timings.json")
    metrics = load(work / "search_metrics.json")
    conv = load(work / "convergence.json")
    val = load(work / "eval_val.json")
    rows = steps(work)
    per_epoch = sorted((load(p) for p in work.glob("train_epoch_*_rank0.json")), key=lambda r: r["epoch"])
    in_loop_val = epoch_spans(rows, "val_start", "val_end")
    train = timings["train"]
    last = max(timings.values(), key=lambda t: t["t_end"])
    init = load(work / "initialization_rank0.json")
    return {
        "mAP": metrics["mAP"], "AP_signature": metrics["AP_target"], "AP_negative": metrics["AP_negative"],
        "AP50": val["AP50"], "train_mAP": metrics["train_mAP"],
        "lr_drop_epoch": conv["decayed_epoch"], "stop_epoch": conv["stopped_epoch"],
        "checkpoint_epoch": conv["best_epoch"], "epochs_completed": metrics["epochs_completed"],
        "cap_reached": metrics["reached_epoch_cap"], "epoch_numbering": "0 始まり",
        "coco_loaded": bool(init.get("matched")) and coco_line(work / "train.log", "load pretrained from"),
        "coco_source_sha256": init.get("source_sha256"),
        "runtime_read_by_process": load(work / "optimizer_rank0.json").get("runtime"),
        "autocast": load(work / "optimizer_rank0.json").get("autocast"),
        "timing": {
            "wall_s": last["t_end"] - train["t_start"], "start_jst": train["start_jst"], "end_jst": last["end_jst"],
            "train_wall_s": train["wall_s"],
            "train_s_per_epoch": {"per_epoch": [{"epoch": r["epoch"], "seconds": r["seconds"]} for r in per_epoch],
                                  "median": statistics.median(r["seconds"] for r in per_epoch)},
            "s_per_step_median": {"optimizer_step": statistics.median(intervals(rows, "opt", "t")),
                                  "skipped_first_steps": SKIP_STEPS, "rank": 0},
            "eval_s": {"per_epoch_val": in_loop_val, "total_in_training": sum(x["seconds"] for x in in_loop_val),
                       "posthoc_val_wall_s": timings["eval_val"]["wall_s"],
                       "posthoc_train_wall_s": timings["eval_train"]["wall_s"]},
        },
        "gpu": gpu_window(train["t_start"], train["t_end"]),
        "gpu_window": "学習の起動から終わりまで",
        "foreign_gpu_use": foreign(train["t_start"], last["t_end"]),
    }


def determinism():
    path = SCRATCH / "determinism/compare.json"
    if not path.exists():
        return unknown("compare.json missing")
    d = load(path)
    return {"identical": d["identical_all_ranks"],
            "loss_sequence_sha256": {r: v["sha256"] for r, v in d["ranks"].items()},
            "micro_steps": d["ranks"]["0"]["micro_steps"][0], "optimizer_steps": d["ranks"]["0"]["optimizer_steps"][0],
            "self_test_detects_one_bit": not load(SCRATCH / "determinism/compare_selftest.json")["identical_all_ranks"]}


def env():
    a = SCRATCH / "A"
    body, det = load(a / "env_venv.json"), load(a / "env_venv-relation-detr.json")
    keys = ("torch", "torch_cuda_runtime", "cudnn", "nccl", "torchvision", "accelerate", "pillow",
            "image_decoder", "python_version")
    return {"phase_venv": {k: body[k] for k in keys}, "detector_venv": {k: det[k] for k in keys},
            "driver": "595.84", "nvidia_smi": body["nvidia_smi"], "power_limit_W": [300.0, 300.0],
            "NCCL_P2P_DISABLE": "1（両塔の起動の環境。run_hostdiff.environment）",
            "phase_determinism": "deterministic_algorithms True、cudnn_deterministic True、cudnn_benchmark False、"
                                 "TF32 matmul False・cudnn False、CUBLAS_WORKSPACE_CONFIG :4096:8（各 rank の記録）",
            "detector_autocast": "fp16（--mixed-precision fp16。各 run の optimizer_rank0.json の autocast）",
            "tf32": "各 run の runtime_read_by_process を見る",
            "ms_deform_attn_so_sha256": "d1d9d1ac5470d3f6750fabae2d7912d3b70e97be2092282683a72c100dac5c04"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    import subprocess
    values = {
        "host": "andrew", "task_id": TASK,
        "code_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "env": env(), "determinism_check": determinism(),
        "phase": {"seed42": phase(42), "seed123": phase(123)},
        "detector": {"seed42a": detector("seed42a"), "seed42b": detector("seed42b"), "seed123": detector("seed123")},
        "notes": {"s_per_step": f"最初の {SKIP_STEPS} 歩を除き、同じ epoch の中の連続する歩の時刻の差の中央値（rank 0）",
                  "comparison": "相手のホストとの比べは本契約では行わない（SPEC §6.2）"},
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(values, ensure_ascii=False, indent=1, allow_nan=False) + "\n")
    print(args.out)


if __name__ == "__main__":
    main()
