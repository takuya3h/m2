"""通した動画の集合と型ごとのホスト（非公式 T-2026-11-01-stage2-w23-bengio、§8 の e と g）。

読むだけ。本契約の run（experiments/phase1/w23b_dp_W{2,3}_*、w23b_pd_*_ep4_seed42。試走と aborted は除く）から:

- DP と案 A: config.yaml の videos（train・val）
- PD: config.yaml の stage2pilot.ann_dir の instances_train.json の全画像の動画（学習）と、logs/eval_meta_val.json の image_ids
  を instances_val.json で引いた動画（評価）
- 型ごとのホスト: server.txt の集合（要素が 1 つであること）。存在しない run の名前を数えると 0 件になることも返す
- 陽性対照: 集合に 04 を混ぜた入力で test の動画との共通が 1 件になる

    python test_audit.py --out <json>
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[4]
PH = ROOT / "experiments/phase1"
TEST = {"04", "05", "07"}


def video_of(file_name):
    return Path(file_name).stem.split("_")[0]


def ann_videos(path, ids=None):
    d = json.loads(Path(path).read_text())
    imgs = {im["id"]: im["file_name"] for im in d["images"]}
    keep = imgs if ids is None else {i: imgs[i] for i in ids}
    return sorted({video_of(f) for f in keep.values()})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    runs, hosts, used = {}, {}, set()
    for d in sorted(glob.glob(str(PH / "w23b_dp_W[23]_*"))):
        d = Path(d)
        cfg = yaml.safe_load((d / "config.yaml").read_text())
        v = {"train": cfg["videos"]["train"], "val": cfg["videos"]["val"]}
        runs[d.name] = v
        hosts.setdefault(("DP", cfg["type"]), set()).add((d / "server.txt").read_text().split()[0])
        used |= set(v["train"]) | set(v["val"])
    for d in sorted(glob.glob(str(PH / "w23b_pd_*_ep4_seed42"))):
        d = Path(d)
        if not (d / "w23_metrics.json").exists():
            continue
        cfg = yaml.safe_load((d / "config.yaml").read_text())
        ann = Path(cfg["stage2pilot"]["ann_dir"])
        ids = json.loads((d / "logs/eval_meta_val.json").read_text())["image_ids"]
        v = {"train": ann_videos(ann / "instances_train.json"), "val": ann_videos(ann / "instances_val.json", ids),
             "n_val_images": len(ids)}
        runs[d.name] = v
        typ = d.name.split("_")[2].split("-")[0]
        hosts.setdefault(("PD", typ), set()).add((d / "server.txt").read_text().split()[0])
        used |= set(v["train"]) | set(v["val"])
    host_sets = {f"{k[0]}:{k[1]}": sorted(v) for k, v in sorted(hosts.items())}
    out = {"task_id": "T-2026-11-01-stage2-w23-bengio", "n_runs": len(runs), "videos_used": sorted(used),
           "test_videos": sorted(TEST), "intersection_with_test": sorted(used & TEST),
           "positive_control_with_04": sorted((used | {"04"}) & TEST),
           "hosts_by_type": host_sets, "one_host_per_type": all(len(v) == 1 for v in host_sets.values()),
           "nonexistent_run_count": len(glob.glob(str(PH / "w23b_pd_NOSUCH_*"))), "runs": runs}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "runs"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
