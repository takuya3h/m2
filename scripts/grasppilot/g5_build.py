"""把持塔 G の 5 クラスの instance の注釈を把持関係の注釈だけから組む（非公式 T-2026-11-05-grasp-tower-rebuild、Task B-1・B-2）。

二本目の `g38_build.py`（38 クラス、三種がそろうフレーム）を変えずに足した派生。
5 クラス = 把持関係（hand_tool_seg）の 1〜5（1 左手、2 右手、3 左手が扱う器具、4 右手が扱う器具、5 両手で扱う器具）。id はそのまま写す。
手 4 クラス（hand_seg）と術具 31 クラス（tool_seg）は開かない。
学ぶフレーム = 折り A の train / val の動画で、把持関係の注釈があるフレームの全体（三種がそろうフレームに限らない）。
欠落の印（loss_mask）の付いたフレームは注釈を持たないので含まれない（含まれたら止める）。
RLE は元の注釈のまま写す。読むのは train と val のファイルだけ（test と extra は開かない）。data/annotations を変えない。

    .venv/bin/python scripts/grasppilot/g5_build.py --out <dir> [--check-frames 8]
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

TASK = "T-2026-11-05-grasp-tower-rebuild"
HTS = G.HTS / "hand_tool_seg"
CLASSES = [1, 2, 3, 4, 5]
SWAP = {1: 2, 2: 1, 3: 4, 4: 3, 5: 5}      # 左右反転のときのラベルの入れ替え（1 始まり）


def load_part(part):
    assert part in ("train", "val"), part
    d = json.loads((HTS / f"{part}.json").read_text())
    imgs = {im["id"]: im for im in d["images"]}
    anns = collections.defaultdict(list)
    size = {}
    for im in d["images"]:
        size[Path(im["file_name"]).stem] = (im["height"], im["width"])
    for a in d["annotations"]:
        anns[Path(imgs[a["image_id"]]["file_name"]).stem].append(a)
    cats = {c["id"]: c["name"] for c in d["categories"]}
    loss_mask = set((HTS / "loss_mask" / f"{part}.txt").read_text().split())
    return anns, size, cats, loss_mask


def class_check(annotations):
    """対応表の検査: すべてのインスタンスが把持関係の注釈から来て、クラスが 1〜5 であること。外れの件数を返す。"""
    bad = [a for a in annotations if a.get("source") != "hand_tool_seg" or a["category_id"] not in CLASSES]
    return {"n": len(annotations), "violations": len(bad), "examples": [(a.get("source"), a["category_id"]) for a in bad[:3]]}


def loss_mask_check(images, loss_mask):
    """欠落の印の付いたフレームが学ぶフレームに入っていないこと。入った件数を返す。"""
    hit = [im["stem"] for im in images if im["stem"] in loss_mask]
    return {"n_images": len(images), "n_loss_mask": len(loss_mask), "in_images": len(hit), "examples": hit[:3]}


def build(part, seqs):
    anns, size, cats, loss_mask = load_part(part)
    fold = C.fold_a()
    phase = [f for v in fold[part] for f in seqs[v]]
    C.assert_no_test(phase, f"g5_{part}")
    extra = sorted(set(anns) - set(phase))
    if extra:
        raise RuntimeError(f"工程の経路に無い注釈のフレーム {len(extra)} 件（{extra[:3]}）")
    keep = [s for s in phase if s in anns]
    images, annotations = [], []
    for i, stem in enumerate(keep, start=1):
        h, w = size[stem]
        v = C.video_of(stem)
        images.append({"id": i, "file_name": f"data/raw/ego/{part}/{v}/{stem}.jpg", "stem": stem, "video": v, "height": h, "width": w})
        for a in anns[stem]:
            annotations.append({"id": len(annotations) + 1, "image_id": i, "category_id": a["category_id"],
                                "segmentation": a["segmentation"], "bbox": a["bbox"], "area": a.get("area"), "iscrowd": 0,
                                "source": "hand_tool_seg", "source_ann_id": a["id"]})
    return phase, keep, images, annotations, anns, cats, loss_mask


def restore_check(src_anns, images, annotations, n, seed=42):
    """組んだ注釈から 5 クラスのマスクを戻し、元の注釈のマスクと画素で一致するかを数フレームで見る（Task B-2）。"""
    by = collections.defaultdict(list)
    for a in annotations:
        by[a["image_id"]].append(a)
    picks = np.random.default_rng(seed).choice(len(images), size=min(n, len(images)), replace=False)
    rows = []
    for j in sorted(picks.tolist()):
        im = images[j]
        h, w = im["height"], im["width"]
        got = sorted((a["category_id"], G.decode(a["segmentation"], h, w).tobytes()) for a in by[im["id"]])
        want = sorted((a["category_id"], G.decode(a["segmentation"], h, w).tobytes()) for a in src_anns[im["stem"]])
        rows.append({"stem": im["stem"], "n_restored": len(got), "n_source": len(want), "equal": got == want})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--check-frames", type=int, default=8)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fold = C.fold_a()
    seqs = {v: fr for v, fr, _ in C.phase_sequences(fold["train"] + fold["val"])}
    summary = {"task_id": TASK, "unofficial": True, "builder_sha256": C.sha256(Path(__file__)), "parts": {}}
    for part in ("train", "val"):
        phase, keep, images, annotations, src, cats, loss_mask = build(part, seqs)
        table = [{"id": c, "name": cats[c], "source": "hand_tool_seg", "source_id": c, "flip_swap_to": SWAP[c]} for c in CLASSES]
        summary["classes"] = table
        coco = {"info": {"description": f"G 5 grasp classes (unofficial {TASK})"}, "images": images, "annotations": annotations,
                "categories": [{"id": t["id"], "name": t["name"]} for t in table]}
        p = out / f"g5_{part}.json"
        p.write_text(json.dumps(coco))
        inst = collections.Counter(x["category_id"] for x in annotations)
        frm = collections.Counter(c for _, c in {(x["image_id"], x["category_id"]) for x in annotations})
        vids = collections.Counter(im["video"] for im in images)
        cc = class_check(annotations)
        # 陽性対照: 手 4 クラスの注釈を 1 件混ぜた写し（source と id を手 4 クラスのものにする）
        spiked = annotations + [{**annotations[0], "id": -1, "source": "hand_seg", "category_id": 3}]
        lc = loss_mask_check(images, loss_mask)
        # 陽性対照: 印の付いたフレームを 1 件混ぜた写し
        lm_one = sorted(loss_mask)[0]
        lc_ctrl = loss_mask_check(images + [{"stem": lm_one}], loss_mask)
        rc = restore_check(src, images, annotations, a.check_frames)
        summary["parts"][part] = {
            "path": str(p), "sha256": C.sha256(p), "phase_frames": len(phase), "frames": len(keep),
            "videos": dict(sorted(vids.items())), "n_annotations": len(annotations),
            "per_class": {t["name"]: {"id": t["id"], "instances": inst.get(t["id"], 0), "frames": frm.get(t["id"], 0)} for t in table},
            "loss_mask_frames_listed": len(loss_mask), "class_check": cc, "class_check_control_hand_seg_spiked": class_check(spiked),
            "loss_mask_check": lc, "loss_mask_check_control_one_added": lc_ctrl, "restore_check": rc}
        if cc["violations"] or lc["in_images"] or not all(r["equal"] for r in rc):
            raise RuntimeError(f"検査の外れ {part}: {cc} {lc}")
        print(part, len(phase), len(keep), len(annotations), dict(sorted(vids.items())), "restore_equal",
              all(r["equal"] for r in rc), "class_viol", cc["violations"], "ctrl", summary["parts"][part]["class_check_control_hand_seg_spiked"]["violations"],
              "lm_in", lc["in_images"], "lm_ctrl", lc_ctrl["in_images"], flush=True)
    C.write_json(out / "g5_summary.json", summary)


if __name__ == "__main__":
    main()
