#!/usr/bin/env python3
"""欠落の性質を切り分ける:
  (a) HTS のフレーム宇宙(19,560)に存在しない  -> 真の欠落
  (b) 列挙されているが annotation 0 件        -> 「写っていない」正当な負例
さらにセグメント命名ズレ (03_1 vs 03_3 等) を frame index レンジで検証。
"""
import csv, json, re
from collections import defaultdict
from pathlib import Path

ROOT = Path("/home/ubuntu/slocal/m2")
HTS = ROOT / "data/raw/OpenSurgery_Dataset"
ANN = ROOT / "data/annotations"
FRAME_RE = re.compile(r"^(\d{2})_(\d+)_(\d+)$")


def parse(fr):
    m = FRAME_RE.match(fr)
    return (m.group(1), f"{m.group(1)}_{m.group(2)}", int(m.group(3)))


def stem(fn):
    return Path(fn).stem


def load_ref():
    tool = set()
    for s in ("train", "val", "test"):
        tool |= {stem(i["file_name"]) for i in json.load(open(ANN / f"egosurgery_tool/instances_{s}.json"))["images"]}
    phase = set()
    for p in sorted((ANN / "egosurgery_phase").glob("*.csv")):
        with open(p) as f:
            phase |= {r["Frame"].strip() for r in csv.DictReader(f)}
    return tool, phase


def load_hts():
    universe = set()
    ann = {}
    for sub in ("02_hand", "03_tool", "04_handtool"):
        a = set()
        for jp in sorted((HTS / sub / "json_per_video").glob("*/*.json")):
            d = json.load(open(jp))
            id2 = {im["id"]: stem(im["file_name"]) for im in d["images"]}
            universe |= set(id2.values())
            for x in d["annotations"]:
                if x["image_id"] in id2:
                    a.add(id2[x["image_id"]])
        ann[sub] = a
    return universe, ann


def seg_range(frames):
    d = defaultdict(list)
    for f in frames:
        _, seg, idx = parse(f)
        d[seg].append(idx)
    return {s: (len(v), min(v), max(v)) for s, v in sorted(d.items())}


def main():
    tool, phase = load_ref()
    universe, ann = load_hts()
    frames_on_disk = {p.stem for p in (HTS / "01_frames/initial_videos").rglob("*.jpg")}

    print("=" * 90)
    print("A. セグメント別 frame index レンジ（命名ズレの検証）")
    print("=" * 90)
    rs = {"HTS_universe": seg_range(universe), "tool_bbox": seg_range(tool), "phase": seg_range(phase),
          "frames_on_disk": seg_range(frames_on_disk)}
    segs = sorted(set().union(*[set(r) for r in rs.values()]))
    print(f"{'seg':<8}" + "".join(f"{k:<30}" for k in rs))
    for s in segs:
        row = f"{s:<8}"
        for k in rs:
            v = rs[k].get(s)
            row += f"{(f'{v[0]:>5} [{v[1]}-{v[2]}]' if v else '-'):<30}"
        print(row)

    print("\n" + "=" * 90)
    print("B. 欠落の性質切り分け")
    print("=" * 90)
    for rname, ref in (("tool_bbox", tool), ("phase", phase)):
        print(f"\n--- 参照 {rname} ({len(ref):,} フレーム) ---")
        not_in_universe = ref - universe
        not_on_disk = ref - frames_on_disk
        print(f"  HTS のフレーム宇宙(19,560)に存在しない : {len(not_in_universe):,} ({100*len(not_in_universe)/len(ref):.2f}%)")
        print(f"  元フレーム画像(27,535)にも存在しない   : {len(not_on_disk):,}")
        if not_in_universe:
            by = defaultdict(int)
            for f in not_in_universe:
                by[parse(f)[1]] += 1
            print(f"    セグメント別: {dict(sorted(by.items()))}")
        for sub in ("02_hand", "03_tool", "04_handtool"):
            miss = ref - ann[sub]
            b = len(miss & universe)   # 列挙あり・ann0
            a = len(miss - universe)   # 宇宙外
            print(f"  {sub:<12}: 欠落 {len(miss):>5,} = 宇宙外 {a:>5,} + 列挙あり/ann0件 {b:>5,}"
                  f"   (カバー率 {100*(1-len(miss)/len(ref)):.2f}%)")

    print("\n" + "=" * 90)
    print("C. HTS 側にあって参照側にないフレーム（新規に使えるフレーム）")
    print("=" * 90)
    for sub in ("02_hand", "03_tool", "04_handtool"):
        ex = ann[sub] - tool
        by = defaultdict(int)
        for f in ex:
            by[parse(f)[1]] += 1
        print(f"  {sub:<12}: {len(ex):,} フレーム  セグメント別 {dict(sorted(by.items()))}")

    print("\n" + "=" * 90)
    print("D. split 構成（動画レベル）の一致確認")
    print("=" * 90)
    def vids(frames):
        return sorted({parse(f)[0] for f in frames})
    print("[egosurgery_tool]")
    for s in ("train", "val", "test"):
        f = {stem(i["file_name"]) for i in json.load(open(ANN / f"egosurgery_tool/instances_{s}.json"))["images"]}
        print(f"  {s:<6} {len(f):>6,} frames  videos={vids(f)}")
    for name, sub in (("02_hand/coco_splits_4cls", "02_hand/coco_splits_4cls"),
                      ("03_tool/coco_splits_14cls_cleaned", "03_tool/coco_splits_14cls_cleaned"),
                      ("04_handtool/coco_splits_5cls", "04_handtool/coco_splits_5cls"),
                      ("04_handtool/seg_ann_4cls", "04_handtool/seg_ann_4cls")):
        p = HTS / sub
        if not p.exists():
            continue
        print(f"[{name}]")
        for s in ("train", "val", "test"):
            cand = list(p.glob(f"{s}*.json")) + list(p.glob(f"*{s}*.json"))
            if not cand:
                print(f"  {s:<6} (ファイルなし)")
                continue
            f = {stem(i["file_name"]) for i in json.load(open(cand[0]))["images"]}
            print(f"  {s:<6} {len(f):>6,} frames  videos={vids(f)}")


if __name__ == "__main__":
    main()

# --- CSV 出力（experiments/analysis/hts_coverage_2026-07-30/csv/） ---
# 下記 export 部は同ディレクトリの hts_export.py 相当
# #!/usr/bin/env python3
# """最終レポート用の CSV を出力（セグメント別／動画別カバレッジ）。"""
# import csv, json, re
# from collections import defaultdict
# from pathlib import Path
# 
# ROOT = Path("/home/ubuntu/slocal/m2")
# HTS = ROOT / "data/raw/OpenSurgery_Dataset"
# ANN = ROOT / "data/annotations"
# OUT = ROOT / "experiments/analysis/hts_coverage_2026-07-30/csv"
# OUT.mkdir(parents=True, exist_ok=True)
# FRAME_RE = re.compile(r"^(\d{2})_(\d+)_(\d+)$")
# 
# 
# def parse(f):
#     m = FRAME_RE.match(f)
#     return m.group(1), f"{m.group(1)}_{m.group(2)}"
# 
# 
# def stem(fn):
#     return Path(fn).stem
# 
# 
# tool = set()
# for s in ("train", "val", "test"):
#     tool |= {stem(i["file_name"]) for i in json.load(open(ANN / f"egosurgery_tool/instances_{s}.json"))["images"]}
# hand_bb = set()
# for s in ("train", "val", "test"):
#     hand_bb |= {stem(i["file_name"]) for i in json.load(open(ANN / f"egosurgery_tool/hand/{s}.json"))["images"]}
# phase = set()
# for p in sorted((ANN / "egosurgery_phase").glob("*.csv")):
#     with open(p) as f:
#         phase |= {r["Frame"].strip() for r in csv.DictReader(f)}
# 
# universe = set()
# ann = {}
# for sub in ("02_hand", "03_tool", "04_handtool"):
#     a = set()
#     for jp in sorted((HTS / sub / "json_per_video").glob("*/*.json")):
#         d = json.load(open(jp))
#         id2 = {im["id"]: stem(im["file_name"]) for im in d["images"]}
#         universe |= set(id2.values())
#         for x in d["annotations"]:
#             if x["image_id"] in id2:
#                 a.add(id2[x["image_id"]])
#     ann[sub] = a
# disk = {p.stem for p in (HTS / "01_frames/initial_videos").rglob("*.jpg")}
# 
# LABEL = {"02_hand": "hand_seg", "03_tool": "tool_seg", "04_handtool": "handtool_seg"}
# 
# 
# def dump(fname, keyfn, header):
#     keys = sorted({keyfn(f) for f in disk})
#     rows = []
#     for k in keys:
#         sel = lambda S: sum(1 for f in S if keyfn(f) == k)  # noqa: E731
#         r = {header: k, "frames_on_disk": sel(disk), "hts_universe": sel(universe),
#              "ref_tool_bbox": sel(tool), "ref_hand_bbox": sel(hand_bb), "ref_phase": sel(phase)}
#         for sub, lab in LABEL.items():
#             r[f"{lab}_annotated"] = sel(ann[sub])
#             for rn, R in (("vs_tool", tool), ("vs_phase", phase)):
#                 miss = {f for f in R - ann[sub] if keyfn(f) == k}
#                 base = sel(R)
#                 r[f"{lab}_{rn}_missing"] = len(miss)
#                 r[f"{lab}_{rn}_missing_pct"] = round(100 * len(miss) / base, 2) if base else ""
#         rows.append(r)
#     with open(OUT / fname, "w", newline="", encoding="utf-8-sig") as f:
#         w = csv.DictWriter(f, fieldnames=list(rows[0]))
#         w.writeheader()
#         w.writerows(rows)
#     print(f"wrote {OUT / fname} ({len(rows)} rows)")
# 
# 
# dump("coverage_by_segment.csv", lambda f: parse(f)[1], "segment")
# dump("coverage_by_video.csv", lambda f: parse(f)[0], "video")
# 
# # 欠落フレーム一覧
# with open(OUT / "missing_frames.csv", "w", newline="", encoding="utf-8-sig") as f:
#     w = csv.writer(f)
#     w.writerow(["reference", "hts_annotation", "frame", "reason"])
#     for rn, R in (("tool_bbox", tool), ("phase", phase)):
#         for sub, lab in LABEL.items():
#             for fr in sorted(R - ann[sub]):
#                 w.writerow([rn, lab, fr,
#                             "not_in_hts_universe" if fr not in universe else "listed_but_zero_annotation"])
# print(f"wrote {OUT / 'missing_frames.csv'}")
