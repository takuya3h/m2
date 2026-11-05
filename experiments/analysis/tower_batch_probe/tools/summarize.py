"""Tables of T-2026-11-06-tower-batch-probe from the raw records under $STORE.

    python summarize.py --out <levels.json> [--inject-video 04]

Per level and rank: fit or overflow, torch's peak allocated / reserved bytes, nvidia-smi's
peak MiB, the steady step time (steps 11-60: mean and sample standard deviation), the
frames of every step against the batch, the epoch's steps and the projected epoch time
(steps x mean; validation and evaluation are not included). The videos whose frames the
datasets loaded are collected from every worker's read log; ``--inject-video`` adds one
video to that set, as the breaking input of the test-video check.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path

STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-tower-batch-probe")
TEST = {"04", "05", "07"}
FIRST, LAST = 11, 60  # 1-based steps of the steady window


def nvsmi(path):
    peak, util, power = defaultdict(int), defaultdict(list), defaultdict(float)
    with open(path, newline="") as handle:
        for row in csv.reader(handle):
            if len(row) != 5:
                continue
            _, index, used, utilisation, draw = (c.strip() for c in row)
            try:
                used = int(used)
            except ValueError:
                continue
            peak[index] = max(peak[index], used)
            if used > 1024:
                util[index].append(float(utilisation))
                power[index] = max(power[index], float(draw))
    return {i: {"peak_mib": peak[i], "util_mean_while_loaded": statistics.mean(util[i]) if util[i] else None,
                "util_samples": len(util[i]), "power_peak_w": power[i]} for i in sorted(peak)}


def videos_read(probe):
    seen = defaultdict(int)
    for path in probe.glob("reads_*_pid*.txt"):
        for line in path.read_text().splitlines():
            seen[Path(line).name[:2]] += 1
    return dict(sorted(seen.items()))


def rank_summary(record, batch):
    starts = record["step_start"]
    out = {"rank": record["rank"], "steps_started": len(starts),
           "steps_per_epoch": record["steps_per_epoch"], "dataset_frames": record["dataset_frames"],
           "frames_per_step_set": sorted(set(record["frames"])),
           "frames_match_batch": all(f == batch for f in record["frames"]),
           "frames_total": sum(record["frames"]), "oom": record.get("oom"),
           "error": record.get("error")}
    memory = (record.get("oom") or record.get("memory") or {})
    out["max_memory_allocated_bytes"] = memory.get("max_memory_allocated_bytes")
    out["max_memory_reserved_bytes"] = memory.get("max_memory_reserved_bytes")
    out["alloc_conf"] = memory.get("alloc_conf", "UNKNOWN")
    if len(starts) > LAST:
        steady = [starts[k] - starts[k - 1] for k in range(FIRST, LAST + 1)]
        out["steady_steps"] = len(steady)
        out["step_seconds_mean"] = statistics.mean(steady)
        out["step_seconds_sd"] = statistics.stdev(steady)
        out["first_step_seconds"] = starts[1] - starts[0]
        if record.get("gpu_done"):
            done = record["gpu_done"]
            out["gpu_part_seconds_mean"] = statistics.mean(done[k - 1] - starts[k - 1]
                                                           for k in range(FIRST, LAST + 1))
            out["load_wait_seconds_mean"] = statistics.mean(starts[k] - done[k - 1]
                                                            for k in range(FIRST, LAST + 1))
        out["epoch_seconds_projected"] = out["steps_per_epoch"] * out["step_seconds_mean"]
    for key in ("ms_deform_attn_cuda_ext_loaded", "mixed_precision", "num_processes",
                "world_size", "ft_batch_size", "ft_accum_steps", "input_shape"):
        if key in record:
            out[key] = record[key]
    return out


def level_summary(directory, inject):
    run = json.loads((directory / "run.json").read_text())
    batch = run["batch_per_gpu"]
    ranks = [rank_summary(json.loads(p.read_text()), batch)
             for p in sorted((directory / "probe").glob("steps_rank*.json"))]
    videos = videos_read(directory / "probe")
    if inject:
        videos[inject] = videos.get(inject, 0) + 1
    fitted = bool(ranks) and all(r.get("steady_steps") == LAST - FIRST + 1 and not r["oom"] for r in ranks)
    return {"level": run["level"], "kind": run["kind"], "batch_per_gpu": batch, "gpus": run["gpus"],
            "status": run["status"], "returncode": run["returncode"], "wall_seconds": run["wall_seconds"],
            "fitted": fitted, "ranks": ranks, "nvidia_smi": nvsmi(directory / "nvsmi.csv"),
            "videos_read": videos, "test_videos_read": sorted(TEST & set(videos)),
            "weight_files": run["weight_files"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--inject-video")
    args = ap.parse_args()
    levels = [level_summary(d, args.inject_video)
              for stage in ("B", "C") for d in sorted((STORE / stage).iterdir())
              if (d / "run.json").exists()]
    Path(args.out).write_text(json.dumps(levels, ensure_ascii=False, indent=1) + "\n")
    for level in levels:
        print(level["level"], "fitted" if level["fitted"] else "NOT fitted", level["status"],
              level["returncode"], "test_read", level["test_videos_read"], "weights", len(level["weight_files"]))
        for rank in level["ranks"]:
            print("  rank", rank["rank"], {k: rank.get(k) for k in (
                "steps_started", "frames_match_batch", "frames_per_step_set", "steps_per_epoch",
                "dataset_frames", "max_memory_allocated_bytes", "max_memory_reserved_bytes",
                "step_seconds_mean", "step_seconds_sd", "epoch_seconds_projected",
                "load_wait_seconds_mean", "oom")})
        print("  nvsmi", level["nvidia_smi"])


if __name__ == "__main__":
    main()
