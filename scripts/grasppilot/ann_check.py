"""把持の三種の注釈の同定と動画の検査（非公式 T-2026-10-31-grasp-pilot-probe、Task B-1・B-2・B-5）。

被覆の数（data/annotations/egosurgery_hts_current_coverage.md §3）とフレーム数を照らし、使うディレクトリを同定する。
test と extra のファイルは開かない。§8-b の空振りの確認として、フレームを 1 件除いた写しで照合が不一致になること、
04 のフレームを 1 件足した写しで動画の検査が外れを 1 件出すことを確かめる。

    python scripts/grasppilot/ann_check.py --out <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402

HTS = C.ROOT / "data/annotations/egosurgery_hts"
# 被覆の文書 §3 の値（train, val）
DOC = {"hand_tool_seg_v2": (9356, 1514), "hand_seg": (9627, 1515), "tool_seg": (9528, 1512)}
DEPRECATED = (None, None)   # 旧 hand_tool_seg（被覆 65.82%）の split 別の値は文書に無い


def frames_of(path):
    d = json.loads(Path(path).read_text())
    with_ann = {a["image_id"] for a in d["annotations"]}
    return [Path(im["file_name"]).stem for im in d["images"] if im["id"] in with_ann], d


def match(counts, doc):
    return {k: [kind for kind, v in doc.items() if v == tuple(c)] for k, c in counts.items()}


def outside(frames, allowed):
    return sorted({C.video_of(f) for f in frames} - set(allowed))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    fold = C.fold_a()
    allowed = fold["train"] + fold["val"]
    rec = {"fold_a": fold, "dirs": {}, "doc": {k: list(v) for k, v in DOC.items()}}
    frames = {}
    for d in sorted(p for p in HTS.iterdir() if p.is_dir()):
        row = {}
        for part in ("train", "val"):
            fr, raw = frames_of(d / f"{part}.json")
            frames[(d.name, part)] = fr
            row[part] = {"n_frames": len(fr), "n_images": len(raw["images"]), "n_anns": len(raw["annotations"]),
                         "videos": sorted({C.video_of(f) for f in fr}),
                         "outside_fold_a_trainval": outside(fr, fold[part])}
            row["categories"] = [(c["id"], c["name"]) for c in raw["categories"]]
        row["matches_doc"] = [k for k, v in DOC.items() if v == (row["train"]["n_frames"], row["val"]["n_frames"])]
        rec["dirs"][d.name] = row
    # 欠落の印: 5 クラスの注釈と素であることと、術具の枠の画像に含まれること
    tool = {p: {Path(i["file_name"]).stem for i in json.loads((C.DET_ANN_A / f"instances_{p}.json").read_text())["images"]}
            for p in ("train", "val")}
    lm = {}
    for part in ("train", "val"):
        stems = set((HTS / f"hand_tool_seg/loss_mask/{part}.txt").read_text().split())
        ann = set(frames[("hand_tool_seg", part)])
        lm[part] = {"n": len(stems), "overlap_with_5cls_frames": len(stems & ann), "in_tool_frames": len(stems & tool[part]),
                    "tool_frames": len(tool[part]), "tool_minus_5cls": len(tool[part] - ann),
                    "tool_minus_5cls_equals_loss_mask": (tool[part] - ann) == stems}
    rec["loss_mask"] = lm
    # B-5: 工程注釈のあるフレームと術具注釈のあるフレームのうち、注釈のあるフレーム（5 クラスの注釈あり・欠落の印なし）
    seqs = {v: fr for v, fr, _ in C.phase_sequences(allowed)}
    b5 = {}
    for part in ("train", "val"):
        ann = set(frames[("hand_tool_seg", part)]) - set((HTS / f"hand_tool_seg/loss_mask/{part}.txt").read_text().split())
        ph = [f for v in fold[part] for f in seqs[v]]
        b5[part] = {"phase_frames": len(ph), "phase_annotated": len(set(ph) & ann),
                    "tool_frames": len(tool[part]), "tool_annotated": len(tool[part] & ann),
                    "annotated_not_in_phase": len(ann - set(ph)), "annotated_not_in_tool": len(ann - tool[part])}
    rec["b5"] = b5
    # §8-b の空振りの確認
    counts = {k: (len(frames[(k, "train")]), len(frames[(k, "val")])) for k in ("hand_tool_seg", "hand_seg", "tool_seg")}
    drop = dict(counts)
    drop["hand_tool_seg"] = (counts["hand_tool_seg"][0] - 1, counts["hand_tool_seg"][1])
    plus04 = frames[("hand_tool_seg", "train")] + ["04_1_0001"]
    rec["positive_controls"] = {
        "match_actual": match(counts, DOC), "match_one_frame_dropped": match(drop, DOC),
        "outside_actual": outside(frames[("hand_tool_seg", "train")], fold["train"]),
        "outside_with_04_added": outside(plus04, fold["train"]),
    }
    used = sorted({C.video_of(f) for k in ("hand_tool_seg", "hand_seg", "tool_seg") for p in ("train", "val")
                   for f in frames[(k, p)]})
    rec["used_videos"] = used
    rec["used_videos_test_overlap"] = sorted(set(used) & C.TEST_VIDEOS)
    C.write_json(args.out, rec)
    print(json.dumps({k: rec[k] for k in ("loss_mask", "b5", "positive_controls", "used_videos", "used_videos_test_overlap")},
                     ensure_ascii=False, indent=1))
    for k, v in rec["dirs"].items():
        print(k, v["train"]["n_frames"], v["val"]["n_frames"], "matches", v["matches_doc"],
              "outside", v["train"]["outside_fold_a_trainval"], v["val"]["outside_fold_a_trainval"])


if __name__ == "__main__":
    main()
