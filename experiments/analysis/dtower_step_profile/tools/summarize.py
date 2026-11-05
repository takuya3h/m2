"""Tables of T-2026-11-06-dtower-step-profile from the raw records under $STORE/B.

    python summarize.py --out <levels.json> --md <tables.md> [--inject-video 04]

Per level and rank, over steps 21-80 (1-based; step k runs from forward entry k to forward
entry k+1, so 81 entries give 80 steps): the step time and its breakdown (observer.py's
boundaries, synchronised clocks), the rest (= step - the five parts) and its pieces, the
matcher and its CPU assignment, the explicit collectives, the synchronisation waits, the CPU
issue time of the five parts (the clock without waiting for the GPU), the GPU utilisation
and power from nvidia-smi inside the summarised steps only, the frames handed to the model
and loaded by the dataset, the videos those frames came from, the epoch projection, and the
COCO initialisation record. ``--inject-video`` adds one video to the read set, as the breaking
input of the test-video check.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-dtower-step-profile")
TEST = {"04", "05", "07"}
FIRST, LAST = 21, 80  # 1-based steps summarised
BASE_STEPS, BASE_BATCH, BASE_PROCS = 2405, 2, 2  # T-2026-11-06-tower-batch-probe, b2 x 2
PARTS = ("data", "forward", "loss", "backward", "optimizer")
BOUNDARIES = ("t0", "loss_start", "loss_end", "data_start", "data_end", "bwd_start", "bwd_end", "opt_end")


def step_rows(steps):
    rows = []
    for k in range(1, len(steps)):  # step k (1-based) = steps[k-1] .. steps[k]
        a, b = steps[k - 1], steps[k]
        step = b["t0"] - a["t0"]
        row = {"k": k, "step": step, "wall0": a["wall0"], "wall1": b["wall0"], "frames": a["frames"],
               "data": a["data_end"] - a["data_start"], "forward": a["loss_start"] - a["t0"],
               "loss": a["loss_end"] - a["loss_start"], "backward": a["bwd_end"] - a["bwd_start"],
               "optimizer": a["opt_end"] - a["bwd_end"],
               "gap_loss_sum": a["data_start"] - a["loss_end"],
               "gap_zero_grad": a["bwd_start"] - a["data_end"],
               "gap_tail": b["t0"] - a["opt_end"],
               "matcher": a.get("matcher_s", 0.0), "matcher_calls": a.get("matcher_calls", 0),
               "lsa": a.get("lsa_s", 0.0), "lsa_calls": a.get("lsa_calls", 0),
               "criterion_calls": a.get("criterion_calls", 0),
               "collectives": a.get("coll_s", 0.0), "collective_calls": a.get("coll_calls", 0),
               "reduce": a.get("reduce_s", 0.0), "reduce_tensors": a.get("reduce_tensors", 0),
               "sync_wait": sum(a[n] - a[n + "_pre"] for n in BOUNDARIES[1:]) + b["t0"] - b["t0_pre"],
               # the CPU issue time of each part: from its synchronised start to the clock read
               # before its closing synchronisation (what a clock without the wait would see)
               "issue_data": a["data_end_pre"] - a["data_start"],
               "issue_forward": a["loss_start_pre"] - a["t0"],
               "issue_loss": a["loss_end_pre"] - a["loss_start"],
               "issue_backward": a["bwd_end_pre"] - a["bwd_start"],
               "issue_optimizer": a["opt_end_pre"] - a["bwd_end"]}
        row["parts_sum"] = sum(row[p] for p in PARTS)
        row["rest"] = step - row["parts_sum"]
        row["rest_pieces_diff"] = row["rest"] - (row["gap_loss_sum"] + row["gap_zero_grad"] + row["gap_tail"])
        row["issue_sum"] = sum(row["issue_" + p] for p in PARTS)
        rows.append(row)
    return rows


def mean(rows, key):
    return statistics.mean(r[key] for r in rows)


def nvsmi(path):
    samples = defaultdict(list)
    with open(path, newline="") as handle:
        for row in csv.reader(handle):
            if len(row) != 5:
                continue
            stamp, index, used, utilisation, draw = (c.strip() for c in row)
            try:
                when = datetime.strptime(stamp, "%Y/%m/%d %H:%M:%S.%f").replace(tzinfo=timezone.utc).timestamp()
                samples[index].append((when, int(used), float(utilisation), float(draw)))
            except ValueError:
                continue
    return samples


def gpu_window(samples, start, end):
    inside = [s for s in samples if start <= s[0] <= end]
    if not inside:
        return {"samples": 0}
    gaps = [b[0] - a[0] for a, b in zip(inside, inside[1:])]
    zero = sum(1 for s in inside if s[2] == 0)
    return {"samples": len(inside), "sample_interval_median_s": statistics.median(gaps) if gaps else None,
            "util_mean": statistics.mean(s[2] for s in inside), "util_zero_samples": zero,
            "util_zero_fraction": zero / len(inside),
            "power_mean_w": statistics.mean(s[3] for s in inside), "power_max_w": max(s[3] for s in inside),
            "memory_max_mib": max(s[1] for s in inside), "peak_mib_whole_run": max(s[1] for s in samples)}


def videos_read(probe):
    seen, frames = defaultdict(int), 0
    for path in probe.glob("reads_det_pid*.txt"):
        for line in path.read_text().splitlines():
            seen[Path(line).name[:2]] += 1
            frames += 1
    return dict(sorted(seen.items())), frames


def rank_summary(record, batch, processes, samples):
    steps = record["steps"]
    rows = step_rows(steps)
    window = [r for r in rows if FIRST <= r["k"] <= LAST]
    out = {"rank": record["rank"], "forward_entries": len(steps), "steps_whole": len(rows),
           "steps_per_epoch": record["steps_per_epoch"], "dataset_frames": record["dataset_frames"],
           "frames_per_entry_set": sorted({s["frames"] for s in steps}),
           "frames_match_batch": all(s["frames"] == batch for s in steps),
           "frames_whole_steps": sum(r["frames"] for r in rows), "oom": record.get("oom"),
           "error": record.get("error"), "memory": record.get("memory"), "cached": record.get("cached"),
           "initial_fetch": record.get("initial_fetch")}
    for key in ("num_workers", "pin_memory", "persistent_workers", "batch_sampler_batch_size",
                "mixed_precision", "num_processes", "ddp_wrapped", "sync_batchnorm_modules",
                "ms_deform_attn_cuda_ext_loaded", "cuda_device_name", "no_load"):
        out[key] = record.get(key)
    if len(window) != LAST - FIRST + 1:
        out["summarised_steps"] = len(window)
        return out, rows
    out["summarised_steps"] = len(window)
    keys = ("step", *PARTS, "rest", "gap_loss_sum", "gap_zero_grad", "gap_tail", "matcher", "lsa",
            "collectives", "reduce", "sync_wait", "issue_sum", *("issue_" + p for p in PARTS),
            "parts_sum", "rest_pieces_diff")
    out["mean"] = {k: mean(window, k) for k in keys}
    out["sd"] = {k: statistics.stdev(r[k] for r in window) for k in ("step", *PARTS, "rest")}
    out["median_step"] = statistics.median(r["step"] for r in window)
    out["counts_per_step"] = {k: sorted({r[k] for r in window}) for k in
                              ("criterion_calls", "matcher_calls", "lsa_calls", "collective_calls",
                               "reduce_tensors")}
    out["max_abs_rest_pieces_diff"] = max(abs(r["rest_pieces_diff"]) for r in window)
    out["idle_parts_1_3_5_6"] = out["mean"]["data"] + out["mean"]["loss"] + out["mean"]["optimizer"] + out["mean"]["rest"]
    out["epoch_projection"] = {
        "steps_actual": record["steps_per_epoch"],
        "seconds_actual_steps": record["steps_per_epoch"] * out["mean"]["step"],
        "steps_converted_from_2405": BASE_STEPS * BASE_BATCH * BASE_PROCS / (batch * processes),
        "seconds_converted": BASE_STEPS * BASE_BATCH * BASE_PROCS / (batch * processes) * out["mean"]["step"]}
    start, end = window[0]["wall0"], window[-1]["wall1"]
    gpu = str(record["rank"]) if processes == 2 else "0"
    out["gpu_window"] = {"gpu_index": gpu, "start_wall": start, "end_wall": end,
                         **gpu_window(samples.get(gpu, []), start, end)}
    win = out["gpu_window"]
    if win.get("samples"):
        out["gpu_zero_seconds_per_step"] = win["util_zero_fraction"] * out["mean"]["step"]
    return out, rows


def level_summary(directory, inject):
    run = json.loads((directory / "run.json").read_text())
    batch, processes = run["batch_per_gpu"], run["processes"]
    samples = nvsmi(directory / "nvsmi.csv")
    ranks, per_step = [], {}
    for path in sorted((directory / "probe").glob("steps_rank*.json")):
        summary, rows = rank_summary(json.loads(path.read_text()), batch, processes, samples)
        ranks.append(summary)
        per_step[summary["rank"]] = rows
    videos, loaded_frames = videos_read(directory / "probe")
    if inject:
        videos[inject] = videos.get(inject, 0) + 1
    init = [json.loads(p.read_text()) for p in sorted((directory / "work").glob("initialization_rank*.json"))]
    log = (directory / "stdout.log").read_text(errors="replace")
    return {"level": run["level"], "number": run["number"], "batch_per_gpu": batch, "processes": processes,
            "num_workers": run["num_workers"], "loaded": run["loaded"], "gpus": run["gpus"],
            "status": run["status"], "returncode": run["returncode"], "wall_seconds": run["wall_seconds"],
            "start_utc": run["start_utc"], "before_gpu": run["before"]["gpu"],
            "before_procs": run["before"]["procs"]["count"], "ranks": ranks,
            "dataset_loaded_frames": loaded_frames, "videos_read": videos,
            "test_videos_read": sorted(TEST & set(videos)), "weight_files": run["weight_files"],
            "coco_init": [{k: i.get(k) for k in ("source", "matching_tensors", "source_sha256", "matched")}
                          for i in init],
            "log_load_pretrained_lines": sum("load pretrained from" in line for line in log.splitlines()),
            "log_control_complete_lines": sum("CONTROL_COMPLETE" in line for line in log.splitlines())}, per_step


def fmt(x, digits=4):
    return "UNKNOWN" if x is None else f"{x:.{digits}f}"


def tables(levels):
    lines = ["| 水準 | rank | 一歩の平均 ± sd (s) | 1 読み込みの待ち | 2 順伝播 | 3 損失と対応づけ | 4 逆伝播 | 5 最適化器 | 6 残り | 1〜5 の和 | 和と一歩の差 (= 残り) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for lv in levels:
        for r in lv["ranks"]:
            m = r.get("mean")
            if not m:
                lines.append(f"| {lv['level']} | {r['rank']} | UNKNOWN（{r['summarised_steps']} 歩） |" + " |" * 9)
                continue
            lines.append(f"| {lv['level']} | {r['rank']} | {fmt(m['step'])} ± {fmt(r['sd']['step'])} | "
                         + " | ".join(fmt(m[p]) for p in PARTS) + f" | {fmt(m['rest'])} | "
                         f"{fmt(m['parts_sum'])} | {fmt(m['step'] - m['parts_sum'])} |")
    lines += ["", "| 水準 | rank | 残りの内訳: 損失の和 / zero_grad / 末尾 | うち損失の集約 (reduce, 項目数) | 対応づけ (回/歩) | うち CPU の割り当て (回/歩) | 明示の集団通信 (回/歩) | 同期の待ちの合計 | 1〜5 の CPU の発行時間の和 | 1+3+5+6 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for lv in levels:
        for r in lv["ranks"]:
            m = r.get("mean")
            if not m:
                continue
            c = r["counts_per_step"]
            lines.append(f"| {lv['level']} | {r['rank']} | {fmt(m['gap_loss_sum'])} / {fmt(m['gap_zero_grad'])} / {fmt(m['gap_tail'])} | "
                         f"{fmt(m['reduce'])} ({c['reduce_tensors']}) | {fmt(m['matcher'])} ({c['matcher_calls']}) | "
                         f"{fmt(m['lsa'])} ({c['lsa_calls']}) | {fmt(m['collectives'])} ({c['collective_calls']}) | "
                         f"{fmt(m['sync_wait'])} | {fmt(m['issue_sum'])} | {fmt(r['idle_parts_1_3_5_6'])} |")
    lines += ["", "| 水準 | rank (GPU) | 歩の区間の nvidia-smi 標本数 | 使用率の平均 (%) | 使用率 0 の標本の割合 | 使用率 0 の長さ/歩 (s) | 電力の平均 / 最大 (W) | 1 epoch の歩数（実の長さ / 2,405 からの換算） | 見込み (s)（実 / 換算） |",
              "|---|---|---|---|---|---|---|---|---|"]
    for lv in levels:
        for r in lv["ranks"]:
            m, w = r.get("mean"), r.get("gpu_window", {})
            if not m:
                continue
            e = r["epoch_projection"]
            lines.append(f"| {lv['level']} | {r['rank']} ({w['gpu_index']}) | {w['samples']} | {fmt(w.get('util_mean'), 1)} | "
                         f"{fmt(w.get('util_zero_fraction'), 3)} | {fmt(r.get('gpu_zero_seconds_per_step'))} | "
                         f"{fmt(w.get('power_mean_w'), 1)} / {fmt(w.get('power_max_w'), 1)} | "
                         f"{e['steps_actual']} / {fmt(e['steps_converted_from_2405'], 1)} | "
                         f"{fmt(e['seconds_actual_steps'], 1)} / {fmt(e['seconds_converted'], 1)} |")
    lines += ["", "| 水準 | 結果 | 各歩でモデルに渡った枚数 | 80 歩の枚数 = batch × 80 | データセットが読んだ枚数 | 読んだ動画（フレーム数） | test との共通 | COCO の重み（テンソル数） | 保存された重み |",
              "|---|---|---|---|---|---|---|---|---|"]
    for lv in levels:
        frames = "; ".join(f"r{r['rank']} {r['frames_per_entry_set']}" for r in lv["ranks"])
        whole = "; ".join(f"r{r['rank']} {r['frames_whole_steps']} = {lv['batch_per_gpu']} × {r['steps_whole']}"
                          f" {'一致' if r['frames_whole_steps'] == lv['batch_per_gpu'] * r['steps_whole'] == lv['batch_per_gpu'] * 80 else '不一致'}"
                          for r in lv["ranks"])
        videos = ", ".join(f"{v}:{n}" for v, n in lv["videos_read"].items())
        coco = ", ".join(f"{i['matching_tensors']}{'' if i['matched'] else ' 不一致'}" for i in lv["coco_init"])
        lines.append(f"| {lv['level']} | {lv['status']} / rc {lv['returncode']} | {frames} | {whole} | {lv['dataset_loaded_frames']} | "
                     f"{videos} | {len(lv['test_videos_read'])} 件 | {coco} | {len(lv['weight_files'])} 件 |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--md")
    ap.add_argument("--steps-dir")
    ap.add_argument("--inject-video")
    args = ap.parse_args()
    levels = []
    for directory in sorted((STORE / "B").iterdir(), key=lambda d: d.name):
        if not (directory / "run.json").exists():
            continue
        level, per_step = level_summary(directory, args.inject_video)
        levels.append(level)
        if args.steps_dir:
            target = Path(args.steps_dir)
            target.mkdir(parents=True, exist_ok=True)
            for rank, rows in per_step.items():
                with open(target / f"{level['level']}_rank{rank}.csv", "w", newline="") as handle:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                    writer.writeheader()
                    writer.writerows(rows)
    for lv in levels:  # the projection is recomputed from its parts
        for r in lv["ranks"]:
            if r.get("mean"):
                e = r["epoch_projection"]
                assert abs(e["seconds_actual_steps"] - e["steps_actual"] * r["mean"]["step"]) < 1e-9
                assert abs(e["seconds_converted"] - e["steps_converted_from_2405"] * r["mean"]["step"]) < 1e-9
    Path(args.out).write_text(json.dumps(levels, ensure_ascii=False, indent=1) + "\n")
    if args.md:
        Path(args.md).write_text(tables(levels))
    for lv in levels:
        print(lv["level"], lv["status"], lv["returncode"], "test_read", lv["test_videos_read"],
              "weights", len(lv["weight_files"]), "loaded_frames", lv["dataset_loaded_frames"])
        for r in lv["ranks"]:
            m = r.get("mean") or {}
            print("  rank", r["rank"], "steps", r.get("summarised_steps"), "frames_ok", r["frames_match_batch"],
                  {k: round(v, 4) for k, v in m.items() if k in ("step", *PARTS, "rest", "reduce", "matcher", "lsa", "collectives")},
                  "util", r.get("gpu_window", {}).get("util_mean"))


if __name__ == "__main__":
    main()
