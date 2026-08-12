#!/usr/bin/env python3
"""egosurgery_tool（術具 bbox）の split × クラス分布を監査する。

目的:
    検出実験で使う `data/annotations/egosurgery_tool/instances_{train,val,test}.json`
    について、各 split が何クラスを定義し、実際に何件のアノテーションを持つかを確定させる。
    特に「定義クラス数」と「実出現クラス数」の乖離は mAP の分母を変えるため、
    Δ 基準点の比較可能性に直結する。

出力（--out 配下）:
    report.json              … 機械可読な全集計
    csv/tool_class_counts.csv … split × クラスの箱数/画像数（UTF-8 BOM）
    csv/tool_split_summary.csv … split 単位の要約（UTF-8 BOM）

使い方:
    python scripts/audit_tool_class_distribution.py \
        --ann-dir data/annotations/egosurgery_tool \
        --out experiments/audit/tool_class_distribution_2026-07-31
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import subprocess
from pathlib import Path

SPLITS = ("train", "val", "test")

# EgoSurgery-Tool 論文 arXiv:2406.03095v4 の Table 3(a) 記載値（2026-07-31 に arxiv.org/html で確認）。
# 数値は論文の印字通り。実測との突き合わせを自動化し、手作業の照合ミスを防ぐ。
PAPER_REF = {
    "source": "arXiv:2406.03095v4 (EgoSurgery-Tool) Table 3(a) / §Dataset Statistics",
    "checked_on": "2026-07-31",
    "images": 15437,
    "tool_instances": 49652,
    "hand_instances": 46320,
    "num_tool_classes": 15,
    "split_images": {"train": 9657, "val": 1515, "test": 4265},
    "split_videos": {"train": 10, "val": 2, "test": 3},
    # クラス名: (train, val, test, total)
    "per_class": {
        "Bipolar Forceps": (446, 55, 195, 696),
        "Electric Cautery": (1404, 101, 162, 1667),
        "Forceps": (2534, 154, 3375, 6063),
        "Gauze": (4596, 455, 1644, 6695),
        "Hook": (1045, 147, 157, 1349),
        "Mouth Gag": (3807, 990, 1188, 5985),
        "Needle Holders": (3031, 512, 1286, 4829),
        "Raspatory": (654, 76, 84, 814),
        "Retractor": (2079, 0, 325, 2404),
        "Scalpel": (739, 168, 159, 1066),
        "Scissors": (1780, 391, 565, 2736),
        "Skewer": (212, 103, 29, 344),
        "Suction Cannula": (3134, 509, 768, 4411),
        "Syringe": (344, 96, 141, 581),
        "Tweezers": (6467, 950, 2595, 10012),
    },
}


def crosscheck_paper(per_split: dict, hand_total: int | None) -> dict:
    """実測値を論文 Table 3(a) と突き合わせる。差分があれば mismatches に列挙する。"""
    mismatches: list[dict] = []

    def cmp(label: str, measured, paper) -> None:
        if measured != paper:
            mismatches.append({"item": label, "measured": measured, "paper": paper})

    cmp("images_total", sum(per_split[s]["num_images"] for s in SPLITS), PAPER_REF["images"])
    cmp("tool_instances_total",
        sum(per_split[s]["num_annotations"] for s in SPLITS), PAPER_REF["tool_instances"])
    cmp("num_tool_classes", per_split["train"]["num_categories_defined"],
        PAPER_REF["num_tool_classes"])
    for s in SPLITS:
        cmp(f"images_{s}", per_split[s]["num_images"], PAPER_REF["split_images"][s])
        cmp(f"videos_{s}", per_split[s]["num_videos"], PAPER_REF["split_videos"][s])
    if hand_total is not None:
        cmp("hand_instances_total", hand_total, PAPER_REF["hand_instances"])

    measured_names = set(per_split["train"]["per_class"])
    paper_names = set(PAPER_REF["per_class"])
    if measured_names != paper_names:
        mismatches.append({"item": "class_name_set",
                           "measured_only": sorted(measured_names - paper_names),
                           "paper_only": sorted(paper_names - measured_names)})

    for name, (tr, va, te, tot) in PAPER_REF["per_class"].items():
        if name not in measured_names:
            continue
        got = tuple(per_split[s]["per_class"][name]["annotations"] for s in SPLITS)
        if got != (tr, va, te) or sum(got) != tot:
            mismatches.append({"item": f"per_class:{name}",
                               "measured": list(got) + [sum(got)],
                               "paper": [tr, va, te, tot]})

    return {
        "reference": {k: v for k, v in PAPER_REF.items() if k != "per_class"},
        "all_match": not mismatches,
        "num_cells_compared": 3 * len(PAPER_REF["per_class"]) + 10,
        "mismatches": mismatches,
    }


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # noqa: BLE001 — 証跡が取れなくても監査自体は続行
        return "unknown"


def analyze_split(path: Path) -> dict:
    """1 split の COCO JSON を集計する。"""
    with path.open(encoding="utf-8") as f:
        d = json.load(f)

    cats = {c["id"]: c["name"] for c in d["categories"]}
    ann_per_cat = collections.Counter(a["category_id"] for a in d["annotations"])
    img_per_cat: dict[int, set] = collections.defaultdict(set)
    for a in d["annotations"]:
        img_per_cat[a["category_id"]].add(a["image_id"])

    image_ids = {i["id"] for i in d["images"]}
    annotated_ids = {a["image_id"] for a in d["annotations"]}

    return {
        "file": str(path),
        "categories": {str(k): v for k, v in sorted(cats.items())},
        "num_categories_defined": len(cats),
        "num_categories_present": sum(1 for i in cats if ann_per_cat.get(i, 0) > 0),
        "absent_categories": [cats[i] for i in sorted(cats) if ann_per_cat.get(i, 0) == 0],
        "num_images": len(image_ids),
        "num_annotations": len(d["annotations"]),
        "num_videos": len(d.get("videos") or []),
        "images_without_annotation": len(image_ids - annotated_ids),
        "mean_boxes_per_image": round(len(d["annotations"]) / max(len(image_ids), 1), 4),
        "degenerate_boxes": sum(
            1 for a in d["annotations"] if a["bbox"][2] <= 0 or a["bbox"][3] <= 0
        ),
        "iscrowd_annotations": sum(1 for a in d["annotations"] if a.get("iscrowd", 0)),
        "per_class": {
            cats[i]: {
                "category_id": i,
                "annotations": ann_per_cat.get(i, 0),
                "images": len(img_per_cat.get(i, ())),
            }
            for i in sorted(cats)
        },
        "_file_names": {i["file_name"] for i in d["images"]},  # リーク検査用（JSON には出さない）
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ann-dir", default="data/annotations/egosurgery_tool")
    ap.add_argument("--hand-dir", default="data/annotations/egosurgery_tool_hand",
                    help="手 bbox の COCO ディレクトリ（論文の hand instances 照合用）")
    ap.add_argument("--out", default="experiments/audit/tool_class_distribution_2026-07-31")
    ap.add_argument("--date", default="2026-07-31", help="監査日（report.json に記録）")
    args = ap.parse_args()

    ann_dir = Path(args.ann_dir)
    out = Path(args.out)
    (out / "csv").mkdir(parents=True, exist_ok=True)

    per_split = {s: analyze_split(ann_dir / f"instances_{s}.json") for s in SPLITS}

    # split 間の file_name 重複（動画単位 split のリーク検査）
    leakage = {}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        leakage[f"{a}&{b}"] = len(per_split[a]["_file_names"] & per_split[b]["_file_names"])

    # カテゴリ定義が split 間で一致しているか
    cat_sets = [json.dumps(per_split[s]["categories"], ensure_ascii=False, sort_keys=True) for s in SPLITS]
    categories_identical = len(set(cat_sets)) == 1

    for s in SPLITS:
        per_split[s].pop("_file_names")

    # 手 bbox の総数（論文の hand instances 照合用。無ければ None にして照合を飛ばす）
    hand_dir = Path(args.hand_dir)
    hand_total: int | None = None
    hand_detail: dict | None = None
    try:
        hand_detail = {}
        total = 0
        for s in SPLITS:
            hd = json.loads((hand_dir / f"{s}.json").read_text(encoding="utf-8"))
            hand_detail[s] = {"images": len(hd["images"]), "annotations": len(hd["annotations"]),
                              "num_categories": len(hd["categories"])}
            total += len(hd["annotations"])
        hand_total = total
    except Exception as exc:  # noqa: BLE001 — 手 bbox が無くても術具側の監査は成立させる
        print(f"[warn] 手 bbox を読めず論文照合の hand 項目を skip: {exc}")
        hand_detail = None

    class_names = list(per_split["train"]["categories"].values())
    report = {
        "audit": "egosurgery_tool_class_distribution",
        "date": args.date,
        "git_commit": _git_commit(),
        "ann_dir": str(ann_dir),
        "script": "scripts/audit_tool_class_distribution.py",
        "categories_identical_across_splits": categories_identical,
        "num_classes_defined": per_split["train"]["num_categories_defined"],
        "class_names": class_names,
        "filename_overlap_between_splits": leakage,
        "totals": {
            "annotations": sum(per_split[s]["num_annotations"] for s in SPLITS),
            "images": sum(per_split[s]["num_images"] for s in SPLITS),
            "videos": sum(per_split[s]["num_videos"] for s in SPLITS),
        },
        "hand_bbox": hand_detail,
        "hand_instances_total": hand_total,
        "paper_crosscheck": crosscheck_paper(per_split, hand_total),
        "splits": per_split,
        "findings": [
            {
                "id": "F1_val_missing_retractor",
                "severity": "P1",
                "known_since": "docs/m2_plan_rewrite/source_current.md §33 (2026/05/29) — 本監査は再導出",
                "detail": (
                    "val に Retractor のアノテーションが 0 件。COCOeval は該当クラス AP を -1 とし "
                    "mAP 平均から除外するため、val の mAP は実質 14 クラス平均、test は 15 クラス平均となり "
                    "分母が一致しない。val と test の mAP を直接比較してはならない。"
                    "これは配布データの欠損ではなく EgoSurgery-Tool 論文 Table 3(a) が Retractor val=0 と "
                    "明記する公式 split の性質である。"
                    "既知の派生問題として mmdet_components.py:87 が GT 不在クラスの NaN を 0.0 に倒して "
                    "算入するため AP_common に約 -4.6pt の押し下げバイアスが乗る（source_current.md §33）。"
                ),
            },
            {
                "id": "F2_class_imbalance",
                "severity": "P2",
                "detail": (
                    "train の最多/最少クラス比が約 30 倍（Tweezers 6467 / Skewer 212）。"
                    "val の rare クラス（Bipolar 55 / Raspatory 76 / Syringe 96 箱）は "
                    "per-class AP の分散が大きく、|Δ| > 1σ 判定には試行反復が必要。"
                ),
            },
            {
                "id": "F3_empty_images",
                "severity": "P3",
                "detail": (
                    "箱ゼロ画像が train 39 / test 84 枚存在（val は 0）。"
                    "空アノテーション画像を学習・評価で除外するか否かで実効サンプル数が変わる。"
                ),
            },
        ],
    }

    (out / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # CSV 1: split × クラス
    with (out / "csv" / "tool_class_counts.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category_id", "class_name"]
                   + [f"{s}_{k}" for s in SPLITS for k in ("annotations", "images")]
                   + ["total_annotations"])
        for name in class_names:
            cid = per_split["train"]["per_class"][name]["category_id"]
            row = [cid, name]
            total = 0
            for s in SPLITS:
                pc = per_split[s]["per_class"][name]
                row += [pc["annotations"], pc["images"]]
                total += pc["annotations"]
            w.writerow(row + [total])

    # CSV 2: split 要約
    with (out / "csv" / "tool_split_summary.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["split", "images", "annotations", "videos", "classes_defined",
                    "classes_present", "absent_classes", "images_without_annotation",
                    "mean_boxes_per_image", "degenerate_boxes", "iscrowd"])
        for s in SPLITS:
            p = per_split[s]
            w.writerow([s, p["num_images"], p["num_annotations"], p["num_videos"],
                        p["num_categories_defined"], p["num_categories_present"],
                        ";".join(p["absent_categories"]), p["images_without_annotation"],
                        p["mean_boxes_per_image"], p["degenerate_boxes"],
                        p["iscrowd_annotations"]])

    cc = report["paper_crosscheck"]
    print(f"論文照合 ({PAPER_REF['source']}): "
          f"{'ALL MATCH' if cc['all_match'] else 'MISMATCH'} "
          f"({cc['num_cells_compared']} セル比較, 不一致 {len(cc['mismatches'])} 件)")
    for m in cc["mismatches"]:
        print("  !", m)
    print(f"wrote {out}/report.json")
    print(f"wrote {out}/csv/tool_class_counts.csv")
    print(f"wrote {out}/csv/tool_split_summary.csv")
    for s in SPLITS:
        p = per_split[s]
        print(f"  {s}: images={p['num_images']:,} anns={p['num_annotations']:,} "
              f"classes_present={p['num_categories_present']}/{p['num_categories_defined']} "
              f"absent={p['absent_categories']}")


if __name__ == "__main__":
    main()
