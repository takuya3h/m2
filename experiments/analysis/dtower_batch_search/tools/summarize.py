"""Tables and the prereg §3 selection of T-2026-11-06-dtower-batch-search, from the run records.

    python summarize.py --out <summary.json> --md <tables.md> [--tie 0.0076] [--inject-test]

Reads ``experiments/baselines/stage1_dtower_batch/<run>/`` (metrics.json, posthoc_records.json,
convergence.json, eval_epochs.json, warmup_rank0.json, loader_rank*.json, config.yaml) and the work
directories under ``$STORE/runs`` (train_epoch_*_rank*.json, eval logs, the dataset read logs).

The selection is prereg §3: per level the mean of the two val mAP; the level with the largest mean
is the candidate; levels whose mean is within ``--tie`` of the largest are tied, and the largest
batch among the tied is selected. A level with a diverged or missing run is not a candidate.
``--tie 0`` is the control of SPEC §5 g; ``--inject-test`` adds the test annotation to the set of
evaluated files, as the breaking input of the test-use check.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-11-06-dtower-batch-search")
RUNS = ROOT / "experiments/baselines/stage1_dtower_batch"
LEVELS = {"b2": 2, "b4": 4, "b6": 6}
SEEDS = (42, 123)
TEST_VIDEOS = {"04", "05", "07"}


def load(path):
    return json.loads(path.read_text()) if path.exists() else None


def run_record(level, seed):
    name = f"dtowerbatch_{level}_dcoco_foldA_seed{seed}"
    out, work = RUNS / name, STORE / "runs" / name
    metrics = load(out / "metrics.json")
    if metrics is None:
        return {"name": name, "level": level, "seed": seed, "status": "missing"}
    post = load(out / "posthoc_records.json")
    conv = load(out / "convergence.json")
    epochs = load(out / "eval_epochs.json") or []
    warm = load(out / "warmup_rank0.json")
    config = yaml.safe_load((out / "config.yaml").read_text())
    loaders = [load(p) for p in sorted(out.glob("loader_rank*.json"))]
    trains = [load(p) for p in sorted(work.glob("train_epoch_*_rank*.json"))]
    per_rank_peak = {}
    for p in sorted(work.glob("train_epoch_*_rank*.json")):
        rank = re.search(r"rank(\d+)", p.name).group(1)
        per_rank_peak[rank] = max(per_rank_peak.get(rank, 0), load(p)["peak_memory_bytes"])
    rank0_train = [t for p, t in zip(sorted(work.glob("train_epoch_*_rank*.json")), trains) if "rank0" in p.name]
    steps_per_epoch = loaders[0]["loader_length"] if loaders else None
    total_updates = sum(e["steps"] for e in loaders[0]["epochs"]) if loaders else None
    frames_sets = sorted({int(k) for ld in loaders for e in ld["epochs"] for k in e["frames_per_step"]})
    best = metrics["best_epoch"]
    eval_by_epoch = {e["epoch"]: e for e in epochs}
    # The split reaches the evaluator through DTOWER_EVAL_SPLIT and names its output eval_<split>.json;
    # the log's "Test: Total time: H:MM:SS (x s / it)" gives the per-rank iterations approximately (time
    # over seconds per iteration), which tells the frame sets apart (val 758, train 4,809 per rank).
    evaluated, eval_batches = [], {}
    for out_json in sorted(work.glob("eval_*.json")):
        named = re.fullmatch(r"eval_([a-z]+)\.json", out_json.name)  # not eval_<split>.timing.json
        if not named:
            continue
        split = named.group(1)
        evaluated.append(split)
        log = work / f"eval_{split}.log"
        found = re.findall(r"Test: Total time: (\d+):(\d+):(\d+) \(([\d.]+) s / it\)",
                           log.read_text(errors="replace")) if log.exists() else []
        eval_batches[split] = [round((int(h) * 3600 + int(m) * 60 + int(s)) / float(it)) for h, m, s, it in found] or None
    evaluated += ["val"] * len(epochs)  # the per-epoch validation inside training reads instances_val
    videos = {}
    for p in work.glob("probe/reads_det_pid*.txt"):
        for line in p.read_text().splitlines():
            videos[line] = videos.get(line, 0) + 1
    timings = {s: load(work / f"{s}.timing.json") for s in ("train", "eval_val", "eval_train", "records")}
    return {
        "name": name, "level": level, "seed": seed, "status": "done", "config": config,
        "mAP": metrics["mAP"], "AP_target": metrics["AP_target"], "AP_negative": metrics["AP_negative"],
        "train_mAP": metrics["train_mAP"], "train_val_mAP_gap": metrics["train_val_mAP_gap"],
        "best_epoch": best, "epochs_completed": metrics["epochs_completed"],
        "reached_epoch_cap": metrics["reached_epoch_cap"],
        "decayed_epoch": conv.get("decayed_epoch"), "stopped_epoch": conv.get("stopped_epoch"),
        "final_epoch": epochs[-1]["epoch"] if epochs else None,
        "final_val_mAP": post["last_val_mAP"],
        "final_AP_target": epochs[-1]["AP_target"] if epochs else None,
        "best_epoch_AP_target_in_training": eval_by_epoch.get(best, {}).get("AP_target"),
        "val_mAP_per_epoch": conv.get("val_ap_per_epoch"),
        "AP_target_per_epoch": [e["AP_target"] for e in epochs],
        "warmup_first_step_at_target": warm["first_step_at_target"] if warm else None,
        "warmup_steps": (warm["first_step_at_target"] - 1) if warm and warm["first_step_at_target"] else None,
        "steps_in_epoch0": warm["steps_in_epoch0"] if warm else None,
        "steps_per_epoch": steps_per_epoch, "total_updates": total_updates,
        "frames_per_step_set": frames_sets,
        "gradient_nonfinite_steps": post["gradient_nonfinite_steps"],
        "gradient_norm_quantiles_5_50_95": post["gradient_norm_quantiles_5_50_95"],
        "clipping_fraction": post["clipping_fraction"],
        "groups": post["optimizer"]["groups"],
        "train_epoch_seconds_mean_rank0": statistics.mean(t["seconds"] for t in rank0_train) if rank0_train else None,
        "eval_epoch_seconds_mean": statistics.mean(e["seconds"] for e in epochs) if epochs else None,
        "peak_memory_bytes_per_rank": per_rank_peak, "timings": timings,
        "evaluated_splits": sorted(set(evaluated)), "eval_batches_per_rank": eval_batches, "videos_read": dict(sorted(videos.items())),
    }


def select(levels, tie):
    candidates = {lv: v for lv, v in levels.items() if v["candidate"]}
    if not candidates:
        return None
    best = max(candidates.values(), key=lambda v: v["mAP_mean"])["mAP_mean"]
    tied = [lv for lv, v in candidates.items() if best - v["mAP_mean"] <= tie]
    chosen = max(tied, key=lambda lv: LEVELS[lv])
    co_best = max(candidates, key=lambda lv: candidates[lv]["AP_target_mean"])
    return {"tie_width": tie, "max_mean": best, "tied": sorted(tied, key=LEVELS.get),
            "selected": chosen, "selected_batch_per_gpu": LEVELS[chosen],
            "co_primary_best": co_best, "co_primary_disagrees": co_best != chosen}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--md")
    ap.add_argument("--tie", type=float, default=0.0076)
    ap.add_argument("--inject-test", action="store_true")
    args = ap.parse_args()
    runs = [run_record(lv, s) for lv in LEVELS for s in SEEDS]
    if args.inject_test:
        for r in runs:
            if r["status"] == "done":
                r["evaluated_splits"] = sorted(set(r["evaluated_splits"]) | {"test"})
    levels = {}
    for lv in LEVELS:
        pair = [r for r in runs if r["level"] == lv and r["status"] == "done"]
        ok = len(pair) == 2
        levels[lv] = {"candidate": ok, "runs": [r["name"] for r in pair]}
        if ok:
            for key in ("mAP", "AP_target", "AP_negative", "train_val_mAP_gap"):
                levels[lv][f"{key}_values"] = [r[key] for r in pair]
                levels[lv][f"{key}_mean"] = statistics.mean(r[key] for r in pair)
            levels[lv]["mAP_seed_difference_42_minus_123"] = pair[0]["mAP"] - pair[1]["mAP"]
    selection = select(levels, args.tie)
    if selection:
        best = selection["max_mean"]
        for lv, v in levels.items():
            if v["candidate"]:
                v["difference_from_max"] = v["mAP_mean"] - best
                v["difference_from_b2"] = v["mAP_mean"] - levels["b2"]["mAP_mean"] if levels["b2"]["candidate"] else None
    test_hits = sorted({r["name"] for r in runs if r["status"] == "done" and "test" in r["evaluated_splits"]})
    video_hits = sorted({r["name"] for r in runs if r["status"] == "done" and TEST_VIDEOS & set(r["videos_read"])})
    summary = {"runs": runs, "levels": levels, "selection": selection,
               "test_evaluated_runs": test_hits, "test_video_read_runs": video_hits}
    Path(args.out).write_text(json.dumps(summary, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"selection": selection, "levels": {k: {x: y for x, y in v.items() if not x.endswith("_values")}
                                                         for k, v in levels.items()},
                      "test_evaluated_runs": test_hits, "test_video_read_runs": video_hits}, ensure_ascii=False, indent=1))
    if args.md:
        Path(args.md).write_text(tables(runs, levels, selection))


def f(x, d=4):
    return "UNKNOWN" if x is None else (f"{x:.{d}f}" if isinstance(x, float) else str(x))


def tables(runs, levels, selection):
    lines = ["| run | val mAP | 標的群 AP | 陰性対照群 AP | train mAP | train − val | checkpoint の epoch | 総 epoch | 学習率を下げた epoch | 打ち切った epoch | 上限到達 | 最終 epoch の val mAP / 標的群 AP |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        if r["status"] != "done":
            lines.append(f"| {r['name']} | {r['status']} |" + " |" * 11)
            continue
        lines.append(f"| {r['name']} | {f(r['mAP'])} | {f(r['AP_target'])} | {f(r['AP_negative'])} | {f(r['train_mAP'])} | "
                     f"{f(r['train_val_mAP_gap'])} | {r['best_epoch']} | {r['epochs_completed']} | {f(r['decayed_epoch'])} | "
                     f"{f(r['stopped_epoch'])} | {r['reached_epoch_cap']} | {f(r['final_val_mAP'])} / {f(r['final_AP_target'])} |")
    lines += ["", "| run | 立ち上げの歩数 | 第 0 epoch の歩数 | 1 epoch の歩数 | 総更新回数 | 各歩の枚数 | 勾配のノルム 5/50/95% | 刈り込んだ歩の割合 | 勾配が非数の歩 | 学習 / 評価の秒/epoch | 最大確保 rank0 / rank1 (bytes) | 壁時計（学習, s） |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in runs:
        if r["status"] != "done":
            continue
        q = r["gradient_norm_quantiles_5_50_95"] or [None] * 3
        mem = r["peak_memory_bytes_per_rank"]
        lines.append(f"| {r['name']} | {f(r['warmup_steps'])} | {f(r['steps_in_epoch0'])} | {f(r['steps_per_epoch'])} | "
                     f"{f(r['total_updates'])} | {r['frames_per_step_set']} | {' / '.join(f(x, 2) for x in q)} | "
                     f"{f(r['clipping_fraction'])} | {r['gradient_nonfinite_steps']} | "
                     f"{f(r['train_epoch_seconds_mean_rank0'], 1)} / {f(r['eval_epoch_seconds_mean'], 1)} | "
                     f"{mem.get('0', 'UNKNOWN'):,} / {mem.get('1', 'UNKNOWN'):,} | {f(r['timings']['train']['wall_seconds'], 0)} |")
    lines += ["", "| 水準 | seed 42 / 123 の val mAP | 平均 | 最大との差 | b2 との差 | 標的群 AP の平均 | 陰性対照群 AP の平均 | 2 本の差（42 − 123） |",
              "|---|---|---|---|---|---|---|---|"]
    for lv, v in levels.items():
        if not v["candidate"]:
            lines.append(f"| {lv} | 候補から外した（2 本がそろわない） |" + " |" * 6)
            continue
        lines.append(f"| {lv} | {' / '.join(f(x) for x in v['mAP_values'])} | {f(v['mAP_mean'])} | {f(v.get('difference_from_max'))} | "
                     f"{f(v.get('difference_from_b2'))} | {f(v['AP_target_mean'])} | {f(v['AP_negative_mean'])} | "
                     f"{f(v['mAP_seed_difference_42_minus_123'])} |")
    if selection:
        lines += ["", f"- 同点幅 {selection['tie_width']}。平均の最大 {f(selection['max_mean'])}。同点の水準 {selection['tied']}。"
                  f"**選んだ水準 {selection['selected']}（GPU ごとの batch {selection['selected_batch_per_gpu']}）**。"
                  f"標的群 AP の平均の最良 {selection['co_primary_best']}（食い違い {'あり' if selection['co_primary_disagrees'] else 'なし'}）"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
