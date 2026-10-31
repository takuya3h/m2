"""把持塔 G の 38 クラスの instance の注釈を三種の注釈から組む（非公式 T-2026-11-01-grasp-pilot-g、Task C-1・C-2）。

38 クラス = 把持関係 5（hand_tool_seg の 1〜5）＋ 他者の手 2（hand_seg の 3・4）＋ 術具 31（tool_seg の 1〜31）。
自分の手は把持関係の 1・2 と hand_seg の 1・2 が同じマスク（一本目の audit E-2、IoU 全件 1.0）なので一度だけ入れる。
学ぶフレームは三種の注釈がそろうフレーム（一本目の E-2 の組み合わせ 111）。母集団は工程の経路のフレーム（術具の枠と同じ集合）。
インスタンスは重なりを許す（器具は把持関係と術具の分割で同じ画素が二つのインスタンスになる）。RLE は元の注釈のまま写す。

読むのは折り A の train と val のファイルだけ（test と extra は開かない）。data/annotations を変えない。出力は --out（版管理の外）。

    .venv/bin/python scripts/grasppilot/g38_build.py --out <dir> [--check-frames 8]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grasppilot import grasp_signals as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402

# (元の種類, 元のクラス id) → 38 クラスの id（1 始まり）
SOURCES = [("hand_tool_seg", c) for c in range(1, 6)] + [("hand_seg", 3), ("hand_seg", 4)] + [("tool_seg", c) for c in range(1, 32)]
CLASS_OF = {src: i + 1 for i, src in enumerate(SOURCES)}
GRASP5 = list(range(1, 6))          # 把持関係 5 クラスの 38 クラスでの id


def class_table(cats):
    """38 クラスの id・名前・元の種類と id。名前は種類を前置きして重ならないようにする。"""
    prefix = {"hand_tool_seg": "grasp", "hand_seg": "hand", "tool_seg": "tool"}
    return [{"id": CLASS_OF[(k, c)], "name": f"{prefix[k]}:{cats[k][c]}", "source": k, "source_id": c} for k, c in SOURCES]


def frame_annotations(index, stem):
    """一フレームの 38 クラスのインスタンス（元の注釈の RLE を写す）。自分の手（hand_seg の 1・2）は入れない。"""
    out = []
    for kind in index.KINDS:
        for a in index.anns[kind].get(stem, []):
            cid = CLASS_OF.get((kind, a["category_id"]))
            if cid is None:
                continue
            out.append({"category_id": cid, "segmentation": a["segmentation"], "bbox": a["bbox"], "area": a.get("area"),
                        "iscrowd": 0, "source": kind, "source_ann_id": a["id"]})
    return out


def restore(anns38, kind):
    """組んだ注釈から元の種類の (元のクラス id, RLE) の一覧を戻す（試験用）。hand_seg の 1・2 は把持関係の 1・2 から戻す。"""
    inv = {v: k for k, v in CLASS_OF.items()}
    out = []
    for a in anns38:
        k, c = inv[a["category_id"]]
        if k == kind:
            out.append((c, a["segmentation"]))
        elif kind == "hand_seg" and k == "hand_tool_seg" and c in (1, 2):
            out.append((c, a["segmentation"]))
    return out


def build(part, index, seqs):
    fold = C.fold_a()
    stems = [f for v in fold[part] for f in seqs[v]]
    C.assert_no_test(stems, f"g38_{part}")
    keep = [s for s in stems if all(s in index.anns[k] for k in index.KINDS)]
    images, annotations = [], []
    for i, stem in enumerate(keep, start=1):
        h, w = index.size[stem]
        v = C.video_of(stem)
        images.append({"id": i, "file_name": f"data/raw/ego/{part}/{v}/{stem}.jpg", "stem": stem, "video": v, "height": h, "width": w})
        for a in frame_annotations(index, stem):
            annotations.append({"id": len(annotations) + 1, "image_id": i, **a})
    return stems, keep, images, annotations


def check(index, images, annotations, n, seed=42):
    """組んだ注釈から三種のマスクを戻し、元の注釈のマスクと画素で一致するかを数フレームで見る（Task C-2）。"""
    by = collections.defaultdict(list)
    for a in annotations:
        by[a["image_id"]].append(a)
    picks = np.random.default_rng(seed).choice(len(images), size=min(n, len(images)), replace=False)
    rows = []
    for j in sorted(picks.tolist()):
        im = images[j]
        h, w = im["height"], im["width"]
        row = {"stem": im["stem"]}
        for kind in index.KINDS:
            got = sorted((c, G.decode(s, h, w).tobytes()) for c, s in restore(by[im["id"]], kind))
            want = sorted((a["category_id"], G.decode(a["segmentation"], h, w).tobytes()) for a in index.anns[kind][im["stem"]])
            row[kind] = {"n_restored": len(got), "n_source": len(want), "equal": got == want}
        rows.append(row)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--check-frames", type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    index = G.HTSIndex(("train", "val"))
    fold = C.fold_a()
    seqs = {v: fr for v, fr, _ in C.phase_sequences(fold["train"] + fold["val"])}
    table = class_table(index.cats)
    summary = {"task_id": "T-2026-11-01-grasp-pilot-g", "unofficial": True, "classes": table,
               "builder_sha256": C.sha256(Path(__file__)), "parts": {}}
    for part in ("train", "val"):
        stems, keep, images, annotations = build(part, index, seqs)
        coco = {"info": {"description": "G 38 classes (unofficial T-2026-11-01-grasp-pilot-g)"},
                "images": images, "annotations": annotations,
                "categories": [{"id": t["id"], "name": t["name"]} for t in table]}
        p = out / f"g38_{part}.json"
        p.write_text(json.dumps(coco))
        inst = collections.Counter(x["category_id"] for x in annotations)
        frm = collections.Counter(c for c in {(x["image_id"], x["category_id"]) for x in annotations})
        vids = collections.Counter(im["video"] for im in images)
        summary["parts"][part] = {
            "path": str(p), "sha256": C.sha256(p), "phase_frames": len(stems), "frames_all_three": len(keep),
            "videos": dict(sorted(vids.items())), "n_annotations": len(annotations),
            "per_class": {t["name"]: {"instances": inst.get(t["id"], 0), "frames": frm.get(t["id"], 0)} for t in table},
            "check": check(index, images, annotations, a.check_frames)}
        print(part, len(stems), len(keep), len(annotations), dict(sorted(vids.items())),
              all(r[k]["equal"] for r in summary["parts"][part]["check"] for k in index.KINDS))
    C.write_json(out / "g38_summary.json", summary)


if __name__ == "__main__":
    main()
