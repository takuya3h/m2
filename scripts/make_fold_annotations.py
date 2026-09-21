#!/usr/bin/env python
"""`conventions#folds` の 5 折りについて、動画単位で COCO 注釈を組み替える。

契約 T-2026-09-18-stage1-detector-towers。

**折り A は公式分割そのもの**（`conventions#split` の test と val に一致）であるため、
公式ファイルを**そのまま複製**して使う。再現の忠実さを保つためで、ID の振り直しをしない。
折り B〜E は 3 ファイルをプールして作る。**公式 3 ファイルの image_id と annotation_id は
いずれも 0 始まりで衝突する**（実測: image 4,265 件・annotation 12,673 件の衝突）ため、
プールした上で `file_name` の順に決定的に振り直す。

`file_name` は分割の接頭辞を含む（`train/01/01_1_0124.jpg`）。`img_folder` は親の
`data/raw/ego` なので、どの折りへ移っても経路は解決する。**画像の実体は動かさない。**

出力は `data/annotations/egosurgery_tool_folds/<fold>/instances_{train,val,test}.json`。
`.gitignore:10` により追跡外である（公式の `egosurgery_tool/instances_*.json` は 118 行目で
追跡対象なので、別ディレクトリへ置いて取り違えを防ぐ）。

照合は動画 ID の集合で行う。**陰性対照**として、折り A の test 動画を 1 本入れ替えた
集合が差 1 を返すことを示す。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OFFICIAL = REPO / "data/annotations/egosurgery_tool"
OUT = REPO / "data/annotations/egosurgery_tool_folds"

# conventions#folds の表。正本は docs/stage0/A1_fold_table.md。
FOLDS = {
    "A": {"test": ["04", "05", "07"], "val": ["09", "10"]},
    "B": {"test": ["01", "03", "14"], "val": ["02", "08"]},
    "C": {"test": ["02", "08", "11"], "val": ["06", "12"]},
    "D": {"test": ["06", "13", "15"], "val": ["04", "05"]},
    "E": {"test": ["09", "10", "12"], "val": ["07", "15"]},
}
ALL_VIDEOS = [f"{i:02d}" for i in range(1, 16)]
VIDEO_RE = re.compile(r"^[^/]+/(\d+)/")


def video_of(file_name: str) -> str:
    m = VIDEO_RE.match(file_name)
    if not m:
        raise ValueError(f"動画 ID を取り出せない file_name: {file_name!r}")
    return m.group(1)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_official() -> tuple[list[dict], list[dict], list[dict]]:
    """3 ファイルをプールする。ID は衝突するため、ここでは元 ID を保持しない。"""
    images, anns, cats = [], [], None
    for split in ("train", "val", "test"):
        d = json.loads((OFFICIAL / f"instances_{split}.json").read_text())
        if cats is None:
            cats = d["categories"]
        elif json.dumps(cats, sort_keys=True) != json.dumps(d["categories"], sort_keys=True):
            raise RuntimeError(f"categories が {split} で食い違う")
        by_img: dict[int, list[dict]] = {}
        for a in d["annotations"]:
            by_img.setdefault(a["image_id"], []).append(a)
        for im in d["images"]:
            images.append({"src": split, "image": im, "anns": by_img.get(im["id"], [])})
    # file_name で決定的に並べる。プールの順序が実行ごとに変わらないようにする。
    images.sort(key=lambda r: r["image"]["file_name"])
    return images, anns, cats


def build(records: list[dict], cats: list[dict], videos: set[str]) -> dict:
    """指定した動画集合だけを取り出し、ID を 0 から振り直す。"""
    out_images, out_anns = [], []
    for rec in records:
        if video_of(rec["image"]["file_name"]) not in videos:
            continue
        new_id = len(out_images)
        im = dict(rec["image"])
        im["id"] = new_id
        out_images.append(im)
        for a in rec["anns"]:
            na = dict(a)
            na["id"] = len(out_anns)
            na["image_id"] = new_id
            out_anns.append(na)
    return {"images": out_images, "annotations": out_anns, "categories": cats}


def video_set(path: Path) -> set[str]:
    d = json.loads(path.read_text())
    return {video_of(im["file_name"]) for im in d["images"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    out_root = Path(args.out)

    records, _unused, cats = load_official()
    total = len(records)
    pooled_videos = {video_of(r["image"]["file_name"]) for r in records}
    if pooled_videos != set(ALL_VIDEOS):
        raise RuntimeError(f"プールした動画集合が 15 本と一致しない: {sorted(pooled_videos)}")

    report = {"pooled_images": total, "videos": sorted(pooled_videos), "folds": {}}

    for fold, spec in FOLDS.items():
        d = out_root / fold
        d.mkdir(parents=True, exist_ok=True)
        test_v = set(spec["test"])
        val_v = set(spec["val"])
        train_v = set(ALL_VIDEOS) - test_v - val_v
        want = {"train": train_v, "val": val_v, "test": test_v}

        if fold == "A":
            # 折り A は公式分割そのもの。**複製して使う**（ID を振り直さない）。
            for split in ("train", "val", "test"):
                shutil.copyfile(OFFICIAL / f"instances_{split}.json", d / f"instances_{split}.json")
        else:
            for split in ("train", "val", "test"):
                (d / f"instances_{split}.json").write_text(
                    json.dumps(build(records, cats, want[split]), ensure_ascii=False))

        entry = {"copied_from_official": fold == "A", "splits": {}}
        for split in ("train", "val", "test"):
            path = d / f"instances_{split}.json"
            got = video_set(path)
            data = json.loads(path.read_text())
            entry["splits"][split] = {
                "videos_expected": sorted(want[split]),
                "videos_got": sorted(got),
                "set_difference": len(got ^ want[split]),
                "images": len(data["images"]),
                "annotations": len(data["annotations"]),
                "sha256": sha256_file(path),
            }
            if fold == "A":
                entry["splits"][split]["official_sha256"] = sha256_file(
                    OFFICIAL / f"instances_{split}.json")
        # 折り内で 3 分割が重ならず、合わせて 15 本になること
        got_all = [set(entry["splits"][s]["videos_got"]) for s in ("train", "val", "test")]
        entry["overlap_between_splits"] = sum(
            len(a & b) for i, a in enumerate(got_all) for b in got_all[i + 1:])
        entry["union_videos"] = len(set().union(*got_all))
        entry["total_images"] = sum(entry["splits"][s]["images"] for s in ("train", "val", "test"))
        report["folds"][fold] = entry

    # 陰性対照: 折り A の test 動画を 1 本入れ替えると差が 1 ではなく 2 になる
    # （1 本抜けて 1 本入るため対称差は 2）。**差 0 でないことを示すのが目的である。**
    a_test = set(FOLDS["A"]["test"])
    swapped = (a_test - {"04"}) | {"11"}
    report["negative_control"] = {
        "description": "折り A の test から 04 を抜き 11 を入れた集合と、生成物の集合を比べる",
        "set_difference_vs_generated": len(video_set(out_root / "A" / "instances_test.json") ^ swapped),
        "set_difference_normal": len(video_set(out_root / "A" / "instances_test.json") ^ a_test),
    }

    (out_root / "fold_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
