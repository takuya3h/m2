#!/usr/bin/env python3
"""D2: canonical split の間引き規則 — 仮説 H-e「canonical split = phase ラベルを持つフレーム」の検定。

2026-07-29 の M3 は「規則不明」と判定したが、同じレポートの M3-3 が答えを示している可能性がある
(未採用 3,660 枚は全件 phase 未ラベルだった)。H-e を 2 方向の包含関係で検定する。

  方向 1: canonical 15,437 のうち phase 未ラベルの件数        → H-e が正しければ 0
  方向 2: phase ラベルを持つが canonical に含まれない件数     → H-e が正しければ 0

方向 2 は「どの母集団で見るか」で答えが変わるため、必ず 2 通り出す:
  - 母集団 P (19,560 枚 = tool アノテーションが存在する画像) に限定
  - phase CSV 全体 (動画 17-22 など P の外側を含む)

join は必ず basename (拡張子除去) で行う (§1.5)。

Usage:
    python3 scripts/analysis/verify_thinning_rule.py --out $OUT
    python3 scripts/analysis/verify_thinning_rule.py --self-test
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
TOOL_BY_VIDEO = os.path.join(HTS, "egosurgery_tool_bbox/annotations/bbox/by_video/tool")
PHASE_DIRS = [os.path.join(REPO, "data/annotations/egosurgery_phase"),
              os.path.join(HTS, "egosurgery_tool_bbox/annotations/phase")]
MANIFEST_DIR = os.path.join(REPO, "data/processed/phase_manifest")
SPLITS = ["train", "val", "test"]
SIGNATURE_TOOLS = ["Bipolar Forceps", "Scalpel", "Needle Holders"]
RARE_TOOLS = ["Skewer", "Mouth Gag"]

FRAME_RE = re.compile(r"^(?P<video>\d+)_(?P<segidx>\d+)_(?P<frame>\d+)$")


def stem(b):
    return os.path.splitext(os.path.basename(b))[0]


def seg_of(s):
    m = FRAME_RE.match(s)
    return f"{m.group('video')}_{m.group('segidx')}" if m else None


def load_phase_labels():
    """phase CSV から {frame_stem: phase}。どの CSV から来たかも返す。"""
    lab, src = {}, {}
    for d in PHASE_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".csv"):
                continue
            p = os.path.join(d, fn)
            with open(p) as f:
                for row in csv.DictReader(f):
                    fr = (row.get("Frame") or "").strip()
                    ph = (row.get("Phase") or "").strip()
                    if fr and ph:
                        lab[fr] = ph
                        src.setdefault(fr, os.path.relpath(p, REPO))
    return lab, src


def load_manifest_frames():
    """phase_manifest から {split: {frame_stem}} (学習が実際に使う frame 集合)。"""
    out = {}
    for sp in SPLITS:
        p = os.path.join(MANIFEST_DIR, f"{sp}.json")
        if not os.path.exists(p):
            out[sp] = set()
            continue
        with open(p) as f:
            d = json.load(f)
        s = set()
        for clip in d.get("clips", []):
            for fr in clip.get("frames", []):
                s.add(stem(fr["frame"]))
        out[sp] = s
    return out


def load_canonical():
    """canonical split の basename stem を {split: set} で返す。"""
    out = {}
    for sp in SPLITS:
        p = os.path.join(REPO, f"data/annotations/egosurgery_tool/instances_{sp}.json")
        with open(p) as f:
            d = json.load(f)
        out[sp] = {stem(im["file_name"]) for im in d["images"]}
    return out


def load_population_with_tool_ann():
    """母集団 P と、各フレームの tool ann クラス内訳を返す (ann>=1 基準で数える)。"""
    frames = set()
    cls_by_frame = defaultdict(Counter)
    for v in sorted(os.listdir(TOOL_BY_VIDEO)):
        p = os.path.join(TOOL_BY_VIDEO, v, "annotations.json")
        if not os.path.exists(p):
            continue
        with open(p) as f:
            d = json.load(f)
        cm = {c["id"]: c["name"] for c in d["categories"]}
        id2s = {im["id"]: stem(im["file_name"]) for im in d["images"]}
        frames |= set(id2s.values())
        for a in d["annotations"]:
            if a["image_id"] in id2s:
                cls_by_frame[id2s[a["image_id"]]][cm[a["category_id"]]] += 1
    return frames, cls_by_frame


def self_test() -> int:
    """検出できることを確認する:
       1) canonical 側に未ラベルが混ざったら方向 1 で検出できるか
       2) canonical 外にラベル付きがあれば方向 2 で検出できるか
       3) 拡張子つき basename と拡張子なし Frame を正しく join できるか
    """
    ok = True
    lab = {"01_1_0001": "incision", "01_1_0002": "closure", "01_1_0003": "closure"}
    canonical = {"01_1_0001.jpg", "01_1_0002.jpg", "01_1_0009.jpg"}  # 0009 は未ラベル
    canon_stems = {stem(b) for b in canonical}

    unlabeled_in_canon = {s for s in canon_stems if s not in lab}
    if unlabeled_in_canon != {"01_1_0009"}:
        print(f"  [FAIL] 方向 1 検出: {unlabeled_in_canon}"); ok = False
    else:
        print("  [OK]   canonical 内の未ラベルフレームを検出 (方向 1)")

    labeled_outside = {s for s in lab if s not in canon_stems}
    if labeled_outside != {"01_1_0003"}:
        print(f"  [FAIL] 方向 2 検出: {labeled_outside}"); ok = False
    else:
        print("  [OK]   canonical 外のラベル付きフレームを検出 (方向 2)")

    if stem("train/01/01_1_0001.jpg") != "01_1_0001":
        print("  [FAIL] basename 正規化"); ok = False
    else:
        print("  [OK]   パス接頭辞と拡張子を除去して join できる")

    # 4) ann>=1 基準: ann 0 件のフレームを「tool ann あり」に数えない
    with tempfile.TemporaryDirectory() as td:
        cnt = Counter()
        cnt["Tweezers"] += 1
        have = {f for f, c in {"a": cnt, "b": Counter()}.items() if sum(c.values()) > 0}
        if have != {"a"}:
            print(f"  [FAIL] ann>=1 基準: {have}"); ok = False
        else:
            print("  [OK]   ann 0 件のフレームを「ann あり」に数えない")
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

    lab, lab_src = load_phase_labels()
    manifest = load_manifest_frames()
    canon = load_canonical()
    P, cls_by_frame = load_population_with_tool_ann()

    A = set().union(*canon.values())
    canon_segs = {seg_of(s) for s in A}
    excluded = {s for s in P if seg_of(s) not in canon_segs}
    unused = {s for s in P if seg_of(s) in canon_segs} - A
    manifest_all = set().union(*manifest.values()) if manifest else set()

    # ---- Step D2-1: 2 方向の包含関係 --------------------------------------- #
    unlabeled_in_canonical = {s for s in A if s not in lab}
    labeled_not_in_canonical_P = {s for s in (P & set(lab)) if s not in A}
    labeled_not_in_canonical_all = {s for s in lab if s not in A}
    # manifest 基準でも見る (学習が実際に使う集合)
    unlabeled_in_manifest = {s for s in manifest_all if s not in lab}
    manifest_vs_canonical = {"manifest_not_in_canonical": len(manifest_all - A),
                             "canonical_not_in_manifest": len(A - manifest_all),
                             "manifest_size": len(manifest_all)}

    # ---- Step D2-2: 分割表 ------------------------------------------------- #
    def cat_of(s):
        if s in A:
            return "canonical"
        if s in excluded:
            return "excluded_segment"
        return "unused_within_canonical_segment"

    table = defaultdict(lambda: Counter())
    for s in P:
        table[cat_of(s)]["labeled" if s in lab else "unlabeled"] += 1

    # ---- Step D2-3: 判定 --------------------------------------------------- #
    dir1_ok = len(unlabeled_in_canonical) == 0
    dir2_ok_P = len(labeled_not_in_canonical_P) == 0
    if dir1_ok and dir2_ok_P:
        verdict = "H-e 確定"
        action = ("間引き規則は「phase ラベルの有無」。母集団 P の内側では canonical と "
                  "phase ラベル保持フレームが完全一致する。M3 の「規則不明」を訂正する。")
    elif dir1_ok and not dir2_ok_P:
        verdict = "H-e 部分成立"
        action = (f"方向 1 は 0 件だが、方向 2 が {len(labeled_not_in_canonical_P)} 件。"
                  "canonical ⊆ ラベル保持 は成立するが逆は成立しない。")
    else:
        verdict = "H-e 不成立"
        action = f"canonical 内に未ラベルが {len(unlabeled_in_canonical)} 件存在する。"

    # ---- Step D2-4: 未採用フレームの検出用途としての価値 -------------------- #
    unused_with_ann = {s for s in unused if sum(cls_by_frame[s].values()) > 0}
    cls_total = Counter()
    for s in unused_with_ann:
        cls_total.update(cls_by_frame[s])
    sig = {t: cls_total.get(t, 0) for t in SIGNATURE_TOOLS}
    rare = {t: cls_total.get(t, 0) for t in RARE_TOOLS}

    result = {
        "task": "D2_verify_thinning_rule",
        "hypothesis": "H-e: canonical split = phase ラベルを持つフレーム",
        "counts": {"P": len(P), "canonical_A": len(A), "excluded_segment": len(excluded),
                   "unused_within_canonical_segment": len(unused),
                   "phase_labeled_total": len(lab)},
        "direction_1_unlabeled_in_canonical": {
            "n": len(unlabeled_in_canonical),
            "examples": sorted(unlabeled_in_canonical)[:20],
            "expected_if_He": 0,
        },
        "direction_2_labeled_not_in_canonical": {
            "within_population_P": {
                "n": len(labeled_not_in_canonical_P),
                "examples": sorted(labeled_not_in_canonical_P)[:20],
                "expected_if_He": 0,
            },
            "all_phase_csv": {
                "n": len(labeled_not_in_canonical_all),
                "examples": sorted(labeled_not_in_canonical_all)[:20],
                "note": ("phase CSV は動画 17-22 など母集団 P の外側も含むため、"
                         "この値は 0 にならない。H-e の検定は P 内で行う。"),
                "segments": sorted({seg_of(s) for s in labeled_not_in_canonical_all
                                    if seg_of(s)})[:40],
            },
        },
        "manifest_cross_check": {
            **manifest_vs_canonical,
            "unlabeled_in_manifest": len(unlabeled_in_manifest),
        },
        "crosstab": {k: dict(v) for k, v in table.items()},
        "unused_frames_detection_value": {
            "n_unused": len(unused),
            "n_unused_with_tool_ann": len(unused_with_ann),
            "tool_ann_total": sum(cls_total.values()),
            "by_class": dict(cls_total.most_common()),
            "signature_tools": sig,
            "rare_tools": rare,
            "usage_note": (
                "これらは phase 評価には使えない (ラベルが無い) が、検出器の学習データとしては使える量である。"
                "ただし使用すると S0-frozen が変わり I4 を破るため現時点では採用不可。"
                "将来「凍結源を取り直す」判断をする場合の材料として記録する。"),
        },
        "verdict": verdict,
        "action": action,
    }
    with open(os.path.join(out, "json", "d2_thinning_rule.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out, "csv", "d2_label_crosstab.csv"), "w") as f:
        f.write("category,labeled,unlabeled,total\n")
        for k in ("canonical", "unused_within_canonical_segment", "excluded_segment"):
            v = table.get(k, Counter())
            f.write(f"{k},{v.get('labeled',0)},{v.get('unlabeled',0)},{sum(v.values())}\n")
    with open(os.path.join(out, "csv", "d2_unused_tool_class.csv"), "w") as f:
        f.write("class,n_ann,is_signature,is_rare\n")
        for c, n in cls_total.most_common():
            f.write(f"\"{c}\",{n},{c in SIGNATURE_TOOLS},{c in RARE_TOOLS}\n")

    print(f"P={len(P)} canonical={len(A)} excluded={len(excluded)} unused={len(unused)} "
          f"phase_labeled={len(lab)}")
    print(f"\n方向1 canonical 内の未ラベル: {len(unlabeled_in_canonical)} (期待 0)")
    print(f"方向2 ラベル有り∧canonical外 (P 内): {len(labeled_not_in_canonical_P)} (期待 0)")
    print(f"方向2 ラベル有り∧canonical外 (CSV 全体): {len(labeled_not_in_canonical_all)}")
    print(f"\n分割表:")
    for k in ("canonical", "unused_within_canonical_segment", "excluded_segment"):
        v = table.get(k, Counter())
        print(f"  {k:36s} labeled={v.get('labeled',0):6d} unlabeled={v.get('unlabeled',0):6d}")
    print(f"\nmanifest 照合: {manifest_vs_canonical} 未ラベル={len(unlabeled_in_manifest)}")
    print(f"\n未採用の tool ann: {len(unused_with_ann)} フレーム / {sum(cls_total.values())} ann")
    print(f"  signature: {sig}")
    print(f"  rare: {rare}")
    print(f"\n=== D2 VERDICT: {verdict} ===\n  {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
