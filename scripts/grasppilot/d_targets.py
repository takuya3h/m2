"""案 D の標的の表（非公式 T-2026-11-01-grasp-pilot-d、SPEC §3.3・Task C-2・D-1〜D-3）。

表の形は npz（``ann_ids`` (N,) = COCO の注釈 id、``q`` (N, 4) = 左手・右手・両手・なし）。
``grasp_aux_d.load_q_table`` が読む。

    python scripts/grasppilot/d_targets.py from-boxstate --src <boxstate_train.npz> --out <q.npz>
        一本目の枠ごとの r（3）から q = (r, 1 − min(Σr, 1))（grasp_signals.box_state と同じ式）。試走だけに使う
    python scripts/grasppilot/d_targets.py check --q <q.npz> --ann <instances_train.json> --out <json>
        train の注釈の全枠に q があり、余りが無く、4 値の和が 1 か
    python scripts/grasppilot/d_targets.py shuffle --src <q.npz> --ann <instances_train.json> --seed 42 --out <q.npz>
        各画像の中で、正解の枠の間で q を並べ替える（画像ごとに seed から決まる固定の並べ替えを一度だけ作る）
        --identity で恒等の並べ替え（陽性対照。元と同じ枠に戻った割合が 1 になる）
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

TEST_VIDEOS = {"04", "05", "07"}


def sha256(path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def boxes_by_image(ann_path):
    d = json.loads(Path(ann_path).read_text())
    stems = {im["id"]: Path(im["file_name"]).stem for im in d["images"]}
    videos = sorted({s.split("_")[0] for s in stems.values()})
    by = defaultdict(list)
    for a in d["annotations"]:
        by[a["image_id"]].append(int(a["id"]))
    return {k: sorted(v) for k, v in by.items()}, stems, videos


def save(out, ann_ids, q, meta):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, ann_ids=np.asarray(ann_ids, np.int64), q=np.asarray(q, np.float32))
    meta = {**meta, "out": str(out), "out_sha256": sha256(out), "n_boxes": int(len(ann_ids))}
    Path(str(out) + ".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(meta, ensure_ascii=False))


def cmd_from_boxstate(a):
    d = np.load(a.src)
    r = d["r"].astype(np.float64)
    tot = r.sum(1)
    q = np.concatenate([r, (1.0 - np.minimum(tot, 1.0))[:, None]], 1)
    save(a.out, d["ann_ids"], q, {"kind": "from_boxstate", "src": a.src, "src_sha256": sha256(a.src),
                                  "sum_over_1": int((tot > 1.0).sum())})


def cmd_check(a):
    d = np.load(a.q)
    ids = d["ann_ids"].astype(np.int64)
    q = d["q"].astype(np.float64)
    by, stems, videos = boxes_by_image(a.ann)
    want = {i for v in by.values() for i in v}
    have = set(ids.tolist())
    s = q.sum(1)
    res = {"q": a.q, "q_sha256": sha256(a.q), "ann": a.ann, "ann_sha256": sha256(a.ann),
           "ann_videos": videos, "test_videos_in_ann": sorted(set(videos) & TEST_VIDEOS),
           "n_q": int(len(ids)), "n_unique_q": int(len(have)), "n_ann_boxes": int(len(want)),
           "n_ann_images_with_boxes": int(len(by)),
           "missing_in_q": int(len(want - have)), "extra_in_q": int(len(have - want)),
           "sum_min": float(s.min()), "sum_max": float(s.max()), "sum_max_abs_err": float(np.abs(s - 1).max()),
           "value_min": float(q.min()), "value_max": float(q.max()),
           "argmax_counts": {k: int((q.argmax(1) == i).sum()) for i, k in enumerate(("L", "R", "B", "none"))}}
    res["ok"] = (res["missing_in_q"] == 0 and res["extra_in_q"] == 0 and res["n_unique_q"] == res["n_q"]
                 and res["sum_max_abs_err"] < 1e-5 and res["value_min"] >= -1e-6 and not res["test_videos_in_ann"])
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(res, ensure_ascii=False))


def cmd_shuffle(a):
    d = np.load(a.src)
    ids = d["ann_ids"].astype(np.int64)
    q = d["q"].astype(np.float32)
    row = {int(x): i for i, x in enumerate(ids)}
    by, stems, _ = boxes_by_image(a.ann)
    rng = np.random.default_rng(a.seed)
    out_ids, out_q = [], []
    n_single_img = n_single_box = n_same = n_total = 0
    n_same_multi = n_multi = 0
    for img in sorted(by):
        boxes = by[img]
        n = len(boxes)
        perm = np.arange(n) if a.identity else rng.permutation(n)
        if n == 1:
            n_single_img += 1
            n_single_box += 1
        for k, b in enumerate(boxes):
            src = boxes[int(perm[k])]
            out_ids.append(b)
            out_q.append(q[row[src]])
            same = src == b
            n_same += same
            n_total += 1
            if n > 1:
                n_multi += 1
                n_same_multi += same
    save(a.out, out_ids, out_q, {"kind": "shuffle_within_image", "identity": bool(a.identity), "seed": a.seed,
                                 "src": a.src, "src_sha256": sha256(a.src), "ann": a.ann,
                                 "n_images": len(by), "n_single_box_images": n_single_img,
                                 "n_boxes_in_single_box_images": n_single_box,
                                 "same_box_fraction_all": n_same / n_total,
                                 "same_box_fraction_multi_box_images": (n_same_multi / n_multi) if n_multi else None,
                                 "n_boxes_in_multi_box_images": n_multi})


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("from-boxstate")
    p.add_argument("--src", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("check")
    p.add_argument("--q", required=True)
    p.add_argument("--ann", required=True)
    p.add_argument("--out", required=True)
    p = sub.add_parser("shuffle")
    p.add_argument("--src", required=True)
    p.add_argument("--ann", required=True)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--identity", action="store_true")
    p.add_argument("--out", required=True)
    a = ap.parse_args()
    {"from-boxstate": cmd_from_boxstate, "check": cmd_check, "shuffle": cmd_shuffle}[a.cmd](a)


if __name__ == "__main__":
    main()
