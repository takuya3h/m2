"""Summarise one Task D probe directory (T-2026-10-19-dlsta-tower-feasibility).

Step time: from the rank-0 training.log, the logged iteration index and the windowed
``iter_time`` average (last 20 steps) at every 50th step. The steady value is the mean of
the windowed averages from step ``--skip`` on; the rule for "steady" is that the last three
windowed averages lie within 5 % of their mean (reported as ``steady``).
Memory: torch's peak (bytes, per rank) from memprobe and nvidia-smi's peak memory.used (MiB,
per GPU) from the 0.5 s samples. Nothing is rounded.

    python summarize_dprobe.py <probe dir> [--skip 100]
"""
import argparse
import csv
import json
import re
from pathlib import Path

LINE = re.compile(r"\]  \[(\d+)/(\d+)\].*?iter_time: ([0-9.]+).*?max mem: (\d+)")


def summarise(directory, skip):
    d = Path(directory)
    rows = []
    for text in (d / "work/training.log").read_text().splitlines():
        m = LINE.search(text)
        if m and "Epoch: [0]" in text:
            rows.append((int(m[1]), float(m[3]), int(m[4])))
    rows = sorted(set(rows))
    steady_rows = [r for r in rows if r[0] >= skip]
    tail = [r[1] for r in steady_rows[-3:]]
    mean_tail = sum(tail) / len(tail) if tail else None
    steady = bool(tail) and all(abs(t - mean_tail) <= 0.05 * mean_tail for t in tail)
    torch_mem = {}
    for f in sorted((d / "memprobe").glob("torch_mem_rank*.json")):
        torch_mem[f.stem] = json.loads(f.read_text())
    nvsmi = {}
    with (d / "nvsmi.csv").open() as handle:
        for row in csv.reader(handle):
            if len(row) == 3 and row[2].strip().isdigit():
                gpu = row[1].strip()
                nvsmi[gpu] = max(nvsmi.get(gpu, 0), int(row[2].strip()))
    return {
        "probe": d.name,
        "iterations_logged": [r[0] for r in rows],
        "iter_time_window_avg": [r[1] for r in rows],
        "log_max_mem_mib_rank0_rounded": [r[2] for r in rows],
        "step_seconds_steady_mean": (sum(r[1] for r in steady_rows) / len(steady_rows)) if steady_rows else None,
        "steady_last3": tail, "steady": steady, "skip": skip,
        "torch_peak": {k: {"max_memory_allocated_bytes": v["max_memory_allocated_bytes"],
                           "max_memory_reserved_bytes": v["max_memory_reserved_bytes"],
                           "cuda_visible_devices": v["cuda_visible_devices"]} for k, v in torch_mem.items()},
        "nvidia_smi_peak_used_mib": nvsmi,
        "probe_txt_tail": (d / "probe.txt").read_text().splitlines()[-9:],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--skip", type=int, default=100)
    args = ap.parse_args()
    print(json.dumps(summarise(args.directory, args.skip), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
