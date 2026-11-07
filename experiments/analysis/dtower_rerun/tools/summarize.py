"""Tables and records of T-2026-11-07-dtower-rerun (prereg §3, §2.4, §5), from the run records only.

    python summarize.py --out <summary.json> --md <tables.md> --frozen <frozen_towers.json>
                        [--secondary-videos 01,03,11,13,14] [--runs-root DIR]

Reads ``experiments/baselines/stage1_dtower_rerun/<run>/`` (metrics.json, posthoc_records.json,
convergence.json, config.yaml, loader_rank*.json, warmup_rank0.json, per_video_*.json,
test_access.json, eval_timing.json, eval_epochs.json) and the work directories under ``$STORE/runs``
(train_epoch_*_rank*.json, the dataset read logs, the test detections, best_ap.pth).

No selection is made (prereg §3: 選定は行わない). The tables are records:

- per point and fold the val mAP of the two seeds, per point the mean over the ten runs, the
  difference 12 − 0 per fold and over the ten runs (not read as a true difference), the seed spread
  (|42 − 123| per fold and the pooled within-fold SD sqrt(sum d^2 / (2 x 5)));
- fold A of point 12 against the batch search's b6 runs (0.7385 seed 42, 0.7328 seed 123) and the
  tie width 0.0076;
- the secondary test values (prereg §2.4): per point and seed the five videos that never enter a val
  set, each from the fold model that has it in test (01·03·14 fold B, 11 fold C, 13 fold D), pooled
  into one COCO evaluation of their detections, and per video. ``--secondary-videos`` changes the set
  (the control of SPEC §7 h: a six-video set must change the value). The pooling code is checked by
  pooling each fold's own three test videos and comparing with the run's test AP.
- the frozen towers (point 12, seed 42, five folds): checkpoint path, sha256, epoch, val values.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import gzip
import hashlib
import io
import json
import math
import re
import statistics
from pathlib import Path

import yaml
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval as CocoEvalStandard  # alias: semgrep hook

ROOT = Path(__file__).resolve().parents[4]
TASK = "T-2026-11-07-dtower-rerun"
STORE = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
RUNS = ROOT / "experiments/baselines/stage1_dtower_rerun"
POINTS, FOLDS, SEEDS = (12, 0), "ABCDE", (42, 123)
TIE = 0.0076  # PR 299 prereg §3 (2 x mAP_sstd 0.0037965 of baselines/dcoco_foldA/dcoco_foldA@val)
B6 = {42: 0.7385, 123: 0.7328}  # PR 299 RESULT (four digits as published)
B6_FULL = ROOT / "experiments/baselines/stage1_dtower_batch"
R2 = ROOT / "experiments/baselines/stage1_dtower_r2"
TEST_OWNER = {"01": "B", "03": "B", "14": "B", "11": "C", "13": "D",  # conventions#folds
              "04": "A", "05": "A", "07": "A", "02": "C", "08": "C", "06": "D", "15": "D",
              "09": "E", "10": "E", "12": "E"}
TABLE = {"A": ["04", "05", "07"], "B": ["01", "03", "14"], "C": ["02", "08", "11"],
         "D": ["06", "13", "15"], "E": ["09", "10", "12"]}


def load(path):
    path = Path(path)
    return json.loads(path.read_text()) if path.exists() else None


def name(point, fold, seed):
    return f"dtowerrerun_p{point:02d}_dcoco_fold{fold}_seed{seed}"


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def run_record(point, fold, seed, runs_root):
    run = name(point, fold, seed)
    out, work = runs_root / run, STORE / "runs" / run
    metrics = load(out / "metrics.json")
    if metrics is None:
        return {"name": run, "point": point, "fold": fold, "seed": seed, "status": "missing"}
    post = load(out / "posthoc_records.json")
    conv = load(out / "convergence.json")
    config = yaml.safe_load((out / "config.yaml").read_text())
    loaders = [load(p) for p in sorted(out.glob("loader_rank*.json"))]
    warm = load(out / "warmup_rank0.json")
    epochs = load(out / "eval_epochs.json") or []
    peaks, train_seconds = {}, []
    for p in sorted(work.glob("train_epoch_*_rank*.json")):
        rank = re.search(r"rank(\d+)", p.name).group(1)
        rec = load(p)
        peaks[rank] = max(peaks.get(rank, 0), rec["peak_memory_bytes"])
        if rank == "0":
            train_seconds.append(rec["seconds"])
    videos = {}
    for p in work.glob("probe/reads_det_pid*.txt"):
        for line in p.read_text().split():
            videos[line] = videos.get(line, 0) + 1
    best = metrics["best_epoch"]
    by_epoch = {e["epoch"]: e for e in epochs}
    last = epochs[-1] if epochs else None
    groups = post["optimizer"]["groups"]
    return {
        "name": run, "point": point, "fold": fold, "seed": seed, "status": "done",
        "val_mAP": metrics["mAP"], "val_AP_target": metrics["AP_target"], "val_AP_negative": metrics["AP_negative"],
        "train_mAP": metrics["train_mAP"], "train_val_mAP_gap": metrics["train_val_mAP_gap"],
        "best_epoch": best, "epochs_completed": metrics["epochs_completed"],
        "reached_epoch_cap": metrics["reached_epoch_cap"], "decayed_epoch": conv.get("decayed_epoch"),
        "stopped_epoch": conv.get("stopped_epoch"),
        "best_epoch_val_mAP_during_training": by_epoch.get(best, {}).get("stats", [None])[0],
        "best_epoch_AP_target_during_training": by_epoch.get(best, {}).get("AP_target"),
        "last_epoch_val_mAP": last["stats"][0] if last else None,
        "last_epoch_AP_target": last["AP_target"] if last else None,
        "warmup_first_step_at_target": warm["first_step_at_target"], "steps_in_epoch0": warm["steps_in_epoch0"],
        "steps_per_epoch": [x["loader_length"] for x in loaders],
        "total_updates_rank0": sum(e["steps"] for e in loaders[0]["epochs"]),
        "frames_per_step": sorted({int(k) for x in loaders for e in x["epochs"] for k in e["frames_per_step"]}),
        "batch_sampler_batch_size": [x["batch_sampler_batch_size"] for x in loaders],
        "weight_decay_config": config["weight_decay"], "lr_config": config["lr"], "max_norm_config": config["max_norm"],
        "groups": [(g["lr"], g["weight_decay"]) for g in groups], "max_norm_seen": post["optimizer"]["max_norm"],
        "gradient_norm_quantiles_5_50_95": post["gradient_norm_quantiles_5_50_95"],
        "gradient_nonfinite_steps": post["gradient_nonfinite_steps"], "clipping_fraction": post["clipping_fraction"],
        "train_seconds_per_epoch_rank0": train_seconds,
        "eval_seconds_per_epoch": [e["seconds"] for e in epochs],
        "peak_memory_bytes_per_rank": peaks, "train_wall": load(out / "train.timing.json"),
        "eval_timing": load(out / "eval_timing.json"), "test_access": load(out / "test_access.json"),
        "videos_read_in_training": sorted(videos), "test_mAP": load(out / "eval_test.json")["AP"],
        "per_video_val": {k: v["AP"] for k, v in load(out / "per_video_val.json")["per_video"].items()},
        "per_video_test": {k: v["AP"] for k, v in load(out / "per_video_test.json")["per_video"].items()},
        "checkpoint": str(work / "best_ap.pth"),
    }


def mean(values):
    values = [v for v in values if v is not None]
    return statistics.fmean(values) if values else None


def coco_from(images, annotations, categories):
    gt = COCO()
    gt.dataset = {"images": images, "annotations": annotations, "categories": categories}
    with contextlib.redirect_stdout(io.StringIO()):
        gt.createIndex()
    return gt


def pooled_ap(sources):
    """sources: list of (fold, run work dir, videos). One COCO evaluation of their detections."""
    images, annotations, detections, categories = [], [], [], None
    next_image, next_ann = 1, 1
    for fold, work, videos in sources:
        gt = json.loads((ROOT / "data/annotations/egosurgery_tool_folds" / fold / "instances_test.json").read_text())
        if categories is None:
            categories = gt["categories"]
        elif [(c["id"], c["name"]) for c in gt["categories"]] != [(c["id"], c["name"]) for c in categories]:
            raise RuntimeError("categories differ between folds")
        with gzip.open(work / "eval_test.detections.json.gz", "rt") as handle:
            dump = json.load(handle)
        keep = {img["id"]: img for img in gt["images"] if Path(img["file_name"]).name[:2] in videos}
        remap = {}
        for old, img in keep.items():
            remap[old] = next_image
            images.append({**img, "id": next_image})
            next_image += 1
        for ann in gt["annotations"]:
            if ann["image_id"] in remap:
                annotations.append({**ann, "id": next_ann, "image_id": remap[ann["image_id"]]})
                next_ann += 1
        dumped = {img["id"] for img in dump["images"]}
        if not set(keep) <= dumped:
            raise RuntimeError(f"detections missing for images of fold {fold}")
        detections += [{**d, "image_id": remap[d["image_id"]]} for d in dump["detections"] if d["image_id"] in remap]
    gt = coco_from(images, annotations, categories)
    dt = gt.loadRes(copy.deepcopy(detections))
    ev = CocoEvalStandard(gt, dt, iouType="bbox")
    with contextlib.redirect_stdout(io.StringIO()):
        ev.evaluate()
        ev.accumulate()
        ev.summarize()
    return {"AP": float(ev.stats[0]), "images": len(images), "annotations": len(annotations),
            "detections": len(detections)}


def shifted_ap(fold, work):
    """The fold's raw test GT with only the annotation ids moved by +1, and the run's detections.

    Every annotation file holds one annotation with id 0. pycocotools stores the matched GT id in
    ``dtm`` and reads 0 as "unmatched", so the run's own evaluation scores detections matched to it as
    false positives. ``pooled_ap`` numbers annotations from 1, so its identity is checked against this
    (image ids, detections and everything else as in the run's evaluation)."""
    gt = json.loads((ROOT / "data/annotations/egosurgery_tool_folds" / fold / "instances_test.json").read_text())
    gt["annotations"] = [{**a, "id": a["id"] + 1} for a in gt["annotations"]]
    with gzip.open(work / "eval_test.detections.json.gz", "rt") as handle:
        detections = json.load(handle)["detections"]
    coco = coco_from(gt["images"], gt["annotations"], gt["categories"])
    with contextlib.redirect_stdout(io.StringIO()):
        ev = CocoEvalStandard(coco, coco.loadRes(detections), iouType="bbox")
        ev.evaluate()
        ev.accumulate()
        ev.summarize()
    return float(ev.stats[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--frozen", required=True)
    ap.add_argument("--secondary-videos", default="01,03,11,13,14")
    ap.add_argument("--runs-root", default=str(RUNS))
    args = ap.parse_args()
    runs_root = Path(args.runs_root)
    secondary = args.secondary_videos.split(",")
    records = {(p, f, s): run_record(p, f, s, runs_root) for p in POINTS for f in FOLDS for s in SEEDS}
    done = {k: r for k, r in records.items() if r["status"] == "done"}
    extra = sorted(d.name for d in runs_root.glob("dtowerrerun_*")
                   if not any(d.name == name(*k) for k in records))
    val = {k: r["val_mAP"] for k, r in done.items()}
    target = {k: r["val_AP_target"] for k, r in done.items()}
    table, diffs = {}, {}
    for f in FOLDS:
        for p in POINTS:
            pair = [val.get((p, f, s)) for s in SEEDS]
            table[f"{p}_{f}"] = {"seed42": pair[0], "seed123": pair[1], "mean": mean(pair),
                                 "seed_abs_diff": abs(pair[0] - pair[1]) if None not in pair else None,
                                 "AP_target_mean": mean([target.get((p, f, s)) for s in SEEDS])}
        a, b = table[f"12_{f}"]["mean"], table[f"0_{f}"]["mean"]
        diffs[f] = a - b if None not in (a, b) else None
    point_mean = {p: mean([val.get((p, f, s)) for f in FOLDS for s in SEEDS]) for p in POINTS}
    point_n = {p: sum((p, f, s) in val for f in FOLDS for s in SEEDS) for p in POINTS}
    pooled_sd = {}
    for p in POINTS:
        d = [table[f"{p}_{f}"]["seed_abs_diff"] for f in FOLDS]
        pooled_sd[p] = math.sqrt(sum(x * x for x in d) / (2 * len(d))) if None not in d else None
    fold_a = {}
    for s in SEEDS:
        v = val.get((12, "A", s))
        full = load(B6_FULL / f"dtowerbatch_b6_dcoco_foldA_seed{s}/metrics.json")
        fold_a[s] = {"rerun": v, "b6_published": B6[s], "b6_full": full and full["mAP"],
                     "diff_vs_b6_full": (v - full["mAP"]) if v is not None and full else None,
                     "within_tie": (abs(v - full["mAP"]) <= TIE) if v is not None and full else None}
    # secondary test values (prereg §2.4)
    second = {}
    for p in POINTS:
        for s in SEEDS:
            owners = {}
            for v in secondary:
                owners.setdefault(TEST_OWNER[v], []).append(v)
            if not all((p, f, s) in done for f in owners):
                second[f"{p}_{s}"] = None
                continue
            pooled = pooled_ap([(f, STORE / "runs" / name(p, f, s), vids) for f, vids in sorted(owners.items())])
            per_video = {v: pooled_ap([(TEST_OWNER[v], STORE / "runs" / name(p, TEST_OWNER[v], s), [v])])["AP"]
                         for v in secondary}
            per_video_evaluator = {v: done[(p, TEST_OWNER[v], s)]["per_video_test"][v] for v in secondary}
            second[f"{p}_{s}"] = {"videos": secondary, "pooled": pooled, "per_video": per_video,
                                  "per_video_evaluator_gt": per_video_evaluator}
    identity = {}
    for k, r in done.items():
        p, f, s = k
        work = STORE / "runs" / r["name"]
        mine = pooled_ap([(f, work, TABLE[f])])["AP"]
        shifted = shifted_ap(f, work)
        identity[r["name"]] = {"pooled_own_three": mine, "raw_gt_ann_ids_plus_1": shifted,
                               "diff": mine - shifted, "exact": mine == shifted,
                               "run_test_mAP": r["test_mAP"], "run_minus_shifted": r["test_mAP"] - shifted}
    reference = {}
    for f in FOLDS:
        m = load(R2 / f"dcoco_fold{f}_seed42/metrics.json")
        reference[f] = m and m["val"]["mAP"]
    frozen = []
    for f in FOLDS:
        r = done.get((12, f, 42))
        if r is None:
            frozen.append({"fold": f, "status": "missing"})
            continue
        ckpt = Path(r["checkpoint"])
        frozen.append({"fold": f, "run": r["name"], "checkpoint": str(ckpt), "sha256": sha256(ckpt),
                       "bytes": ckpt.stat().st_size, "checkpoint_epoch": r["best_epoch"],
                       "val_mAP": r["val_mAP"], "val_AP_target": r["val_AP_target"],
                       "val_AP_negative": r["val_AP_negative"],
                       "outside_synced_paths": not str(ckpt).startswith(str(ROOT))})
    summary = {"task_id": TASK, "runs_done": len(done), "runs_expected": len(records), "extra_runs": extra,
               "records": {r["name"]: r for r in records.values()}, "table": table, "difference_12_minus_0": {
                   "per_fold": diffs, "ten_run_mean": (point_mean[12] - point_mean[0])
                   if None not in point_mean.values() else None},
               "point_mean": point_mean, "point_n": point_n, "pooled_within_fold_seed_sd": pooled_sd,
               "fold_A_vs_b6": fold_a, "tie_width": TIE, "secondary_test": second,
               "pooling_identity_check": identity, "reference_r2_seed42_val_mAP": reference,
               "selection": "none (prereg §3)"}
    Path(args.out).write_text(json.dumps(summary, indent=1, allow_nan=False) + "\n")
    Path(args.frozen).write_text(json.dumps({"task_id": TASK, "point": 12, "seed": 42, "towers": frozen},
                                            indent=1) + "\n")
    lines = [f"# dtower-rerun tables ({len(done)}/{len(records)} runs)", "",
             "| fold | 12 seed 42 | 12 seed 123 | 12 mean | 0 seed 42 | 0 seed 123 | 0 mean | 12 − 0 | r2 0番 seed 42 (ref) |",
             "|---|---|---|---|---|---|---|---|---|"]

    def fmt(x):
        return "—" if x is None else f"{x:.4f}"
    for f in FOLDS:
        a, b = table[f"12_{f}"], table[f"0_{f}"]
        lines.append(f"| {f} | {fmt(a['seed42'])} | {fmt(a['seed123'])} | {fmt(a['mean'])} | {fmt(b['seed42'])} | "
                     f"{fmt(b['seed123'])} | {fmt(b['mean'])} | {fmt(diffs[f])} | {fmt(reference[f])} |")
    lines += ["", f"- 10 本の平均: 12 番 {fmt(point_mean[12])}（n={point_n[12]}）、0 番 {fmt(point_mean[0])}（n={point_n[0]}）",
              f"- seed 間の SD（折り内の対からの合算）: 12 番 {fmt(pooled_sd[12])}、0 番 {fmt(pooled_sd[0])}",
              "- 選定: なし"]
    Path(args.md).write_text("\n".join(lines) + "\n")
    print(json.dumps({"runs_done": len(done), "extra_runs": extra, "point_mean": point_mean}, indent=1))


if __name__ == "__main__":
    main()
