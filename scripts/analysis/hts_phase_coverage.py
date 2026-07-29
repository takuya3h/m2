#!/usr/bin/env python3
"""T5: 工程 (phase) 被覆の実測 — 評価プロトコル (G-4) 決定の材料。

- subset_ht_{split}.txt (T1 出力 = HT が実際に使えるフレーム) と phase ラベルを basename で join
  (§1.4-f: image_id join は test の約 7 割が別フレームに繋がる既知バグがあるため使わない)
- rare 3 工程 (disinfection / dressing / irrigation) を必ず個別に出す
- canonical split から除外されたセグメントの工程分布も出す

Usage:
    python3 scripts/analysis/hts_phase_coverage.py --out $OUT
    python3 scripts/analysis/hts_phase_coverage.py --self-test
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import tempfile
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HTS = os.path.join(REPO, "data/raw/OpenSurgery_Dataset/05_egosurgery_hts")
PHASE_PROJECT = os.path.join(REPO, "data/annotations/egosurgery_phase")
PHASE_HTS = os.path.join(HTS, "egosurgery_tool_bbox/annotations/phase")
TOOL_BY_VIDEO = os.path.join(HTS, "egosurgery_tool_bbox/annotations/bbox/by_video/tool")
SPLITS = ["train", "val", "test"]

RARE_PHASES = ["disinfection", "dressing", "irrigation"]
FRAME_RE = re.compile(r"^(?P<video>\d+)_(?P<segidx>\d+)_(?P<frame>\d+)$")


def seg_of(stem):
    m = FRAME_RE.match(stem)
    return f"{m.group('video')}_{m.group('segidx')}" if m else None


def load_phase(dirs):
    """phase CSV 群から {frame_stem: phase} を作る。stem は拡張子なし ('01_1_0001')。"""
    lab, seg_files = {}, {}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".csv"):
                continue
            seg = fn[:-4]
            seg_files.setdefault(seg, os.path.join(d, fn))
            with open(seg_files[seg]) as f:
                for row in csv.DictReader(f):
                    fr = (row.get("Frame") or "").strip()
                    ph = (row.get("Phase") or "").strip()
                    if fr and ph:
                        lab[fr] = ph
    return lab, sorted(seg_files)


def self_test() -> int:
    """検出できることを確認する:
       (1) .jpg 付き basename と拡張子なし Frame を正しく join できるか
       (2) phase ラベルが無いフレームを未ラベルとして数えられるか
    """
    ok = True
    with tempfile.TemporaryDirectory() as td:
        with open(os.path.join(td, "01_1.csv"), "w") as f:
            f.write("Frame,Phase\n01_1_0001,incision\n01_1_0002,closure\n")
        lab, segs = load_phase([td])
        if lab != {"01_1_0001": "incision", "01_1_0002": "closure"}:
            print(f"  [FAIL] phase CSV の読み込み: {lab}"); ok = False
        else:
            print("  [OK]   phase CSV を {frame_stem: phase} として読める")

        frames = ["01_1_0001.jpg", "01_1_0002.jpg", "01_1_0999.jpg"]
        got = Counter(lab.get(os.path.splitext(b)[0], "__UNLABELED__") for b in frames)
        if got != Counter({"incision": 1, "closure": 1, "__UNLABELED__": 1}):
            print(f"  [FAIL] basename join: {dict(got)}"); ok = False
        else:
            print("  [OK]   .jpg 付き basename を拡張子除去して join でき、"
                  "未ラベル 1 件を検出 (image_id join を使わない)")
        if seg_of("01_1_0001") != "01_1":
            print("  [FAIL] segment 抽出"); ok = False
        else:
            print("  [OK]   segment 抽出 (01_1_0001 -> 01_1)")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("--out か --self-test のどちらかが必要")
    out = args.out
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    lab_proj, segs_proj = load_phase([PHASE_PROJECT])
    lab_all, segs_all = load_phase([PHASE_PROJECT, PHASE_HTS])
    print(f"phase labels: project={len(lab_proj)} ({len(segs_proj)} seg) / "
          f"project+HTS={len(lab_all)} ({len(segs_all)} seg)")

    # canonical split のフレーム (集合 A)
    A = {}
    for sp in SPLITS:
        p = os.path.join(REPO, f"data/annotations/egosurgery_tool/instances_{sp}.json")
        with open(p) as f:
            d = json.load(f)
        A[sp] = {os.path.basename(im["file_name"]) for im in d["images"]}

    # HT が実際に使えるフレーム (T1 出力)
    S = {}
    for sp in SPLITS:
        p = os.path.join(out, "subsets", f"subset_ht_{sp}.txt")
        with open(p) as f:
            S[sp] = {ln.strip() for ln in f if ln.strip()}

    def dist(frames):
        c = Counter()
        for b in frames:
            c[lab_all.get(os.path.splitext(b)[0], "__UNLABELED__")] += 1
        return c

    phases = sorted({p for p in lab_all.values()})
    rows = []
    summary = {}
    for sp in SPLITS:
        da, ds = dist(A[sp]), dist(S[sp])
        summary[sp] = {"canonical": dict(da), "ht_subset": dict(ds)}
        for ph in phases + ["__UNLABELED__"]:
            rows.append({
                "split": sp, "phase": ph,
                "n_canonical": da.get(ph, 0),
                "n_ht_subset": ds.get(ph, 0),
                "retention": (ds.get(ph, 0) / da[ph]) if da.get(ph) else 0.0,
                "is_rare": ph in RARE_PHASES,
            })

    # ---- Step 5-2: 除外セグメントの工程分布 -------------------------------- #
    P = set()
    for v in sorted(os.listdir(TOOL_BY_VIDEO)):
        p = os.path.join(TOOL_BY_VIDEO, v, "annotations.json")
        if os.path.exists(p):
            with open(p) as f:
                P |= {os.path.basename(im["file_name"]) for im in json.load(f)["images"]}
    A_all = set().union(*A.values())
    canon_segs = {seg_of(os.path.splitext(b)[0]) for b in A_all}
    excluded = {b for b in P if seg_of(os.path.splitext(b)[0]) not in canon_segs}
    within_gap = {b for b in P if seg_of(os.path.splitext(b)[0]) in canon_segs} - A_all
    excl_dist = dist(excluded)
    gap_dist = dist(within_gap)
    excl_segs = sorted({seg_of(os.path.splitext(b)[0]) for b in excluded})

    # 除外セグメントに phase ラベルが存在するか
    phase_avail = {s: (s in segs_all) for s in ["03_1", "03_3", "12_2", "15_2"]}

    result = {
        "task": "T5_phase_coverage",
        "join_rule": "basename から拡張子を除去し phase CSV の Frame 列と突き合わせる (image_id join は使わない)",
        "phase_label_sources": {
            "project_dir": PHASE_PROJECT, "project_segments": segs_proj,
            "hts_dir": PHASE_HTS, "combined_segments": segs_all,
            "n_labeled_frames_combined": len(lab_all),
        },
        "phases": phases,
        "rare_phases": RARE_PHASES,
        "per_split": summary,
        "rare_phase_detail": {
            sp: {ph: {"canonical": summary[sp]["canonical"].get(ph, 0),
                      "ht_subset": summary[sp]["ht_subset"].get(ph, 0)}
                 for ph in RARE_PHASES} for sp in SPLITS
        },
        "excluded_segments": {
            "segments": excl_segs,
            "n_frames": len(excluded),
            "phase_distribution": dict(excl_dist.most_common()),
            "rare_phase_frames": {ph: excl_dist.get(ph, 0) for ph in RARE_PHASES},
            "phase_label_available": phase_avail,
        },
        "within_canonical_segment_gap": {
            "n_frames": len(within_gap),
            "phase_distribution": dict(gap_dist.most_common()),
            "rare_phase_frames": {ph: gap_dist.get(ph, 0) for ph in RARE_PHASES},
        },
    }
    with open(os.path.join(out, "json", "t5_phase_coverage.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    cols = ["split", "phase", "n_canonical", "n_ht_subset", "retention", "is_rare"]
    with open(os.path.join(out, "csv", "t5_phase_coverage.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")

    print("\n=== 9 工程 × split (canonical -> HT subset) ===")
    print(f"  {'phase':14s} " + " ".join(f"{sp:>18s}" for sp in SPLITS))
    for ph in phases + ["__UNLABELED__"]:
        cells = []
        for sp in SPLITS:
            c = summary[sp]["canonical"].get(ph, 0)
            s = summary[sp]["ht_subset"].get(ph, 0)
            cells.append(f"{c:6d}->{s:5d}({s/c:.2f})" if c else f"{c:6d}->{s:5d}( -- )")
        mark = " *RARE*" if ph in RARE_PHASES else ""
        print(f"  {ph:14s} " + " ".join(cells) + mark)
    print(f"\n=== 除外セグメント {excl_segs} n={len(excluded)} ===")
    print(f"  phase 分布: {dict(excl_dist.most_common())}")
    print(f"  rare 3 工程: {result['excluded_segments']['rare_phase_frames']}")
    print(f"  phase ラベル存在: {phase_avail}")
    print(f"\n=== canonical セグメント内・未採用フレーム n={len(within_gap)} ===")
    print(f"  phase 分布: {dict(gap_dist.most_common())}")
    print(f"  rare 3 工程: {result['within_canonical_segment_gap']['rare_phase_frames']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
