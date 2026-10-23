"""視線データの被覆と範囲を測る（T-2026-10-23-gaze-data-survey、Task D・E）。

data/ は読むだけ。出力は本ディレクトリだけに書く。

    .venv/bin/python experiments/analysis/gaze_data_survey/survey.py [--gaze DIR] [--out DIR] [--no-fig]

--gaze と --out は空振りの対照（写しで回す）のためにある。
"""

import argparse
import csv
import glob
import json
import os
from collections import Counter, defaultdict

import numpy as np
from PIL import Image

MANIFEST = "data/processed/phase_manifest_all_phase"
PHASE_CSV = "data/annotations/egosurgery_phase"
EGO = "data/raw/ego"
HERE = os.path.dirname(os.path.abspath(__file__))
SIGMA_PX = 64.0  # 仮の値（記録だけ）
HEAT_FRAME = "01_1_0004"


def read_gaze(gdir):
    rows = {}
    per_frame = Counter()
    for f in sorted(glob.glob(os.path.join(gdir, "*.csv"))):
        with open(f) as fh:
            for r in csv.DictReader(fh):
                k = r["Frame"]
                per_frame[k] += 1
                rows[k] = (float(r["norm_pos_x"]), float(r["norm_pos_y"]))
    return rows, per_frame


def manifest_frames():
    out = []
    for s in ("train", "val", "test"):
        for c in json.load(open(f"{MANIFEST}/{s}.json"))["clips"]:
            out += [(c["video"], f["frame"], f["image_path"]) for f in c["frames"]]
    return out


def phase_rows(lo, hi):
    out = []
    for f in sorted(glob.glob(f"{PHASE_CSV}/*.csv")):
        v = os.path.basename(f)[:2]
        if lo <= int(v) <= hi:
            with open(f) as fh:
                out += [(v, r["Frame"]) for r in csv.DictReader(fh)]
    return out


def ego_images():
    out = defaultdict(set)
    for dp, _, fn in os.walk(EGO):
        for n in fn:
            if n.lower().endswith(".jpg"):
                out[n[:2]].add(n[:-4])
    return out


def inside(xy, w, h):
    x, y = xy[0] * w, xy[1] * h
    return 0 <= x < w and 0 <= y < h


def heatmap(xy, w, h, sigma):
    gx, gy = xy[0] * w, xy[1] * h
    xs = np.arange(w)[None, :]
    ys = np.arange(h)[:, None]
    return np.exp(-((xs - gx) ** 2 + (ys - gy) ** 2) / (2 * sigma**2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gaze", default="data/raw/gaze")
    ap.add_argument("--out", default=HERE)
    ap.add_argument("--no-fig", action="store_true")
    ap.add_argument("--heat-xy", type=float, nargs=2, default=None)
    a = ap.parse_args()

    gaze, per_frame = read_gaze(a.gaze)
    imgs = ego_images()
    man = manifest_frames()
    p17 = phase_rows(17, 21)
    assert len(man) == len(phase_rows(1, 15))

    # 解像度は実物の jpg から（全数）
    res = Counter()
    for _, _, p in man:
        with Image.open(p) as im:
            res[im.size] = res[im.size] + 1
    w, h = res.most_common(1)[0][0]

    table = []
    by_video = defaultdict(list)
    for v, k, _ in man:
        by_video[v].append(k)
    for v, k in p17:
        by_video[v].append(k)
    for v in sorted(by_video):
        ann = by_video[v]
        img = sorted(imgs.get(v, ()))
        hit = [k for k in ann if k in gaze]
        hit_img = [k for k in img if k in gaze]
        ins = sum(inside(gaze[k], w, h) for k in hit)
        table.append({
            "video": v,
            "set": "01-15" if int(v) <= 15 else "17-21",
            "ann_rows": len(ann), "ann_with_gaze": len(hit),
            "img_files": len(img), "img_with_gaze": len(hit_img),
            "inside": ins,
        })

    gaze_vids = Counter(k[:2] for k in gaze)
    gaze_clips = Counter(k.rsplit("_", 1)[0] for k in gaze)
    target_keys = {k for ks in by_video.values() for k in ks}
    summary = {
        "resolution": {f"{k[0]}x{k[1]}": n for k, n in res.items()},
        "gaze_rows": sum(per_frame.values()),
        "gaze_unique_frames": len(gaze),
        "samples_per_frame": {"min": min(per_frame.values()), "median": float(np.median(list(per_frame.values()))),
                              "max": max(per_frame.values())},
        "x_eq_y": sum(x == y for x, y in gaze.values()),
        "min_xy": [min(x for x, _ in gaze.values()), min(y for _, y in gaze.values())],
        "max_xy": [max(x for x, _ in gaze.values()), max(y for _, y in gaze.values())],
        "gaze_videos": dict(sorted(gaze_vids.items())),
        "gaze_clips_outside_targets": sorted(c for c in gaze_clips
                                             if not any(k.startswith(c + "_") for k in target_keys)),
        "gaze_frames_not_in_targets": len(set(gaze) - target_keys),
    }
    for s in ("01-15", "17-21"):
        rs = [r for r in table if r["set"] == s]
        summary[s] = {c: sum(r[c] for r in rs) for c in
                      ("ann_rows", "ann_with_gaze", "img_files", "img_with_gaze", "inside")}

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "coverage_by_video.csv"), "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(table[0]))
        wr.writeheader()
        wr.writerows(table)

    xy = tuple(a.heat_xy) if a.heat_xy else gaze[HEAT_FRAME]
    hm = heatmap(xy, w, h, SIGMA_PX)
    am = np.unravel_index(hm.argmax(), hm.shape)
    summary["heatmap"] = {
        "frame": HEAT_FRAME, "norm_xy": list(xy), "sigma_px": SIGMA_PX,
        "shape_hw": list(hm.shape), "max": float(hm.max()),
        "argmax_xy_px": [int(am[1]), int(am[0])],
        "gaze_xy_px": [xy[0] * w, xy[1] * h],
    }
    if not a.no_fig:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        path = next(p for _, k, p in man if k == HEAT_FRAME)
        fig, ax = plt.subplots(figsize=(9.6, 5.4), dpi=100)
        ax.imshow(Image.open(path))
        ax.imshow(hm, cmap="jet", alpha=0.4)
        ax.plot(*summary["heatmap"]["gaze_xy_px"], "w+", ms=14, mew=2)
        ax.set_title(f"{HEAT_FRAME}  gaze=({xy[0]:.4f}, {xy[1]:.4f})  sigma={SIGMA_PX:g}px  "
                     "(x==y in the delivered file)")
        ax.axis("off")
        fig.savefig(os.path.join(a.out, "fig_heatmap_01_1_0004.png"), bbox_inches="tight")
    with open(os.path.join(a.out, "summary.json"), "w") as fh:
        json.dump(summary, fh, indent=1, ensure_ascii=False)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
