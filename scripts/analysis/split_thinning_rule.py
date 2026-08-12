#!/usr/bin/env python3
"""M3: canonical split の間引き規則の解明。

canonical split はセグメントを丸ごと除外したのではなく、セグメント内でもフレームを間引いている。
規則が分かれば rare 工程の評価枠を広げられる可能性がある
(同一セグメント内のフレーム追加は再分割にあたらない可能性があるため)。

4 仮説:
  H-a 時間的サブサンプリング : 採用フレーム番号が等間隔か (剰余分布)
  H-b 品質フィルタ           : 未採用の ann 数・bbox 面積分布が採用と異なるか
  H-c annotation 欠落        : 未採用フレームに tool/hand ann が存在するか
  H-d セグメント端の切り落とし: 未採用がセグメント先頭・末尾に偏るか

どれにも当てはまらない場合は「規則不明」と書く。無理に説明をつけない。

Usage:
    python3 scripts/analysis/split_thinning_rule.py --out $OUT
    python3 scripts/analysis/split_thinning_rule.py --self-test
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics
import tempfile
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HTS = os.path.join(REPO, "data/raw/OpenSurgery_Dataset/05_egosurgery_hts")
TOOL_BY_VIDEO = os.path.join(HTS, "egosurgery_tool_bbox/annotations/bbox/by_video/tool")
HANDS_BY_VIDEO = os.path.join(HTS, "egosurgery_tool_bbox/annotations/bbox/by_video/hands")
PHASE_DIRS = [os.path.join(REPO, "data/annotations/egosurgery_phase"),
              os.path.join(HTS, "egosurgery_tool_bbox/annotations/phase")]
SPLITS = ["train", "val", "test"]
RARE_PHASES = ["disinfection", "dressing", "irrigation"]
EXPECTED_UNUSED = 3660

FRAME_RE = re.compile(r"^(?P<video>\d+)_(?P<segidx>\d+)_(?P<frame>\d+)\.(?:jpg|png)$")


def parse_frame(b):
    m = FRAME_RE.match(b)
    if not m:
        return None
    return (m.group("video"), f"{m.group('video')}_{m.group('segidx')}", int(m.group("frame")))


def load_coco_frames(path):
    """{basename: n_ann, ...} と bbox 面積リストを返す。"""
    with open(path) as f:
        d = json.load(f)
    id2b = {im["id"]: os.path.basename(im["file_name"]) for im in d["images"]}
    n_ann = Counter()
    areas = defaultdict(list)
    for b in id2b.values():
        n_ann[b] += 0
    for a in d.get("annotations", []):
        if a["image_id"] in id2b:
            b = id2b[a["image_id"]]
            n_ann[b] += 1
            bb = a.get("bbox")
            if bb:
                areas[b].append(float(bb[2]) * float(bb[3]))
    return dict(n_ann), dict(areas)


def load_phase():
    lab = {}
    for d in PHASE_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".csv"):
                continue
            with open(os.path.join(d, fn)) as f:
                for row in csv.DictReader(f):
                    fr, ph = (row.get("Frame") or "").strip(), (row.get("Phase") or "").strip()
                    if fr and ph:
                        lab[fr] = ph
    return lab


def stats(v):
    if not v:
        return {"n": 0}
    return {"n": len(v), "mean": statistics.mean(v), "median": statistics.median(v),
            "min": min(v), "max": max(v),
            "sd": statistics.stdev(v) if len(v) > 1 else 0.0}


def self_test() -> int:
    """検出できることを確認する:
       1) 等間隔サンプリング (H-a) を剰余分布で検出できるか
       2) 端の切り落とし (H-d) を検出できるか
       3) ann 0 件のフレーム (H-c) を検出できるか
    """
    ok = True
    # 1) 2 フレームおきに採用 -> 剰余 0 に 100% 集中
    adopted = [i for i in range(0, 100, 2)]
    mods = Counter(i % 2 for i in adopted)
    top = max(mods.values()) / sum(mods.values())
    if top < 0.99:
        print(f"  [FAIL] 等間隔検出: {mods}"); ok = False
    else:
        print(f"  [OK]   等間隔サンプリングを剰余分布で検出 (mod2 集中率 {top:.2f})")

    # 2) 端切り落とし: 全 100 のうち先頭 10・末尾 10 が未採用
    allf = list(range(100))
    unused = set(range(10)) | set(range(90, 100))
    lo, hi = min(allf), max(allf)
    span = hi - lo
    edge = sum(1 for f in unused if (f - lo) / span <= 0.1 or (hi - f) / span <= 0.1)
    if edge / len(unused) < 0.99:
        print(f"  [FAIL] 端検出: {edge}/{len(unused)}"); ok = False
    else:
        print(f"  [OK]   セグメント端の切り落としを検出 ({edge}/{len(unused)} が端 10%)")

    # 3) ann 0 件
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "a.json")
        with open(p, "w") as f:
            json.dump({"images": [{"id": 1, "file_name": "01_1_0001.jpg", "height": 10, "width": 10},
                                  {"id": 2, "file_name": "01_1_0002.jpg", "height": 10, "width": 10}],
                       "annotations": [{"id": 1, "image_id": 1, "category_id": 1,
                                        "bbox": [0, 0, 2, 2], "area": 4, "iscrowd": 0}],
                       "categories": [{"id": 1, "name": "x"}]}, f)
        n_ann, _ = load_coco_frames(p)
        zero = {b for b, n in n_ann.items() if n == 0}
        if zero != {"01_1_0002.jpg"}:
            print(f"  [FAIL] ann0 検出: {zero}"); ok = False
        else:
            print("  [OK]   annotation 0 件のフレームを検出 (images 配列長で数えない)")
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

    # ---- Step M3-1: 未採用フレームの特定 ----------------------------------- #
    P_ann, P_areas = {}, {}
    for v in sorted(os.listdir(TOOL_BY_VIDEO)):
        p = os.path.join(TOOL_BY_VIDEO, v, "annotations.json")
        if os.path.exists(p):
            n, a = load_coco_frames(p)
            P_ann.update(n); P_areas.update(a)
    H_ann = {}
    for v in sorted(os.listdir(HANDS_BY_VIDEO)):
        p = os.path.join(HANDS_BY_VIDEO, v, "annotations.json")
        if os.path.exists(p):
            n, _ = load_coco_frames(p)
            H_ann.update(n)

    A = set()
    for sp in SPLITS:
        with open(os.path.join(REPO, f"data/annotations/egosurgery_tool/instances_{sp}.json")) as f:
            A |= {os.path.basename(im["file_name"]) for im in json.load(f)["images"]}

    P = set(P_ann)
    canon_segs = {pf[1] for b in A if (pf := parse_frame(b))}
    excluded = {b for b in P if (pf := parse_frame(b)) and pf[1] not in canon_segs}
    unused = {b for b in P if (pf := parse_frame(b)) and pf[1] in canon_segs} - A

    print(f"P={len(P)} A={len(A)} excluded_seg={len(excluded)} unused={len(unused)} "
          f"(期待 {EXPECTED_UNUSED})")
    count_matches = (len(unused) == EXPECTED_UNUSED)

    # ---- Step M3-2: 4 仮説の検定 ------------------------------------------- #
    # H-c: 未採用フレームに tool / hand ann が存在するか
    unused_tool_ann = [P_ann.get(b, 0) for b in unused]
    adopted_tool_ann = [P_ann.get(b, 0) for b in A if b in P_ann]
    unused_with_tool = sum(1 for n in unused_tool_ann if n > 0)
    unused_hand_ann = [H_ann.get(b, 0) for b in unused]
    unused_with_hand = sum(1 for n in unused_hand_ann if n > 0)
    unused_in_hands_file = sum(1 for b in unused if b in H_ann)

    Hc = {
        "unused_frames": len(unused),
        "unused_with_tool_ann>=1": unused_with_tool,
        "unused_with_tool_ann_rate": unused_with_tool / len(unused) if unused else 0.0,
        "unused_present_in_hands_file": unused_in_hands_file,
        "unused_with_hand_ann>=1": unused_with_hand,
        "tool_ann_stats_unused": stats(unused_tool_ann),
        "tool_ann_stats_adopted": stats(adopted_tool_ann),
    }

    # H-a: 時間的サブサンプリング (セグメント毎にフレーム番号の差分と剰余を見る)
    seg_frames = defaultdict(lambda: {"adopted": [], "unused": []})
    for b in P:
        pf = parse_frame(b)
        if not pf or pf[1] not in canon_segs:
            continue
        seg_frames[pf[1]]["adopted" if b in A else "unused"].append(pf[2])
    diffs_all, mod_conc = [], []
    seg_rows = []
    for s, dd in sorted(seg_frames.items()):
        ad = sorted(dd["adopted"]); un = sorted(dd["unused"])
        d = [ad[i + 1] - ad[i] for i in range(len(ad) - 1)] if len(ad) > 1 else []
        diffs_all.extend(d)
        common = Counter(d).most_common(1)
        step = common[0][0] if common else None
        # 最頻の差分を周期とみなしたときの剰余集中度
        conc = None
        if step and step > 1 and ad:
            mods = Counter(x % step for x in ad)
            conc = max(mods.values()) / sum(mods.values())
            mod_conc.append(conc)
        seg_rows.append({"segment": s, "n_adopted": len(ad), "n_unused": len(un),
                         "modal_step": step, "mod_concentration": conc,
                         "adopted_min": min(ad) if ad else None,
                         "adopted_max": max(ad) if ad else None,
                         "unused_min": min(un) if un else None,
                         "unused_max": max(un) if un else None})
    Ha = {
        "adopted_consecutive_diff_top": dict(Counter(diffs_all).most_common(10)),
        "modal_step_overall": Counter(diffs_all).most_common(1)[0] if diffs_all else None,
        "mean_mod_concentration": statistics.mean(mod_conc) if mod_conc else None,
        "n_segments_with_periodicity_check": len(mod_conc),
    }

    # H-b: 品質フィルタ (bbox 面積)
    def areas_of(fs):
        v = []
        for b in fs:
            v.extend(P_areas.get(b, []))
        return v
    Hb = {"bbox_area_unused": stats(areas_of(unused)),
          "bbox_area_adopted": stats(areas_of([b for b in A if b in P_areas]))}

    # H-d: セグメント端の切り落とし
    edge_hits, edge_total = 0, 0
    for s, dd in seg_frames.items():
        allf = dd["adopted"] + dd["unused"]
        if not allf or not dd["unused"]:
            continue
        lo, hi = min(allf), max(allf)
        span = max(1, hi - lo)
        for f in dd["unused"]:
            edge_total += 1
            if (f - lo) / span <= 0.1 or (hi - f) / span <= 0.1:
                edge_hits += 1
    Hd = {"unused_at_segment_edge_10pct": edge_hits, "unused_total": edge_total,
          "edge_rate": edge_hits / edge_total if edge_total else 0.0,
          "baseline_if_uniform": 0.2}

    # ---- Step M3-3: 工程分布 ----------------------------------------------- #
    lab = load_phase()
    def dist(fs):
        return Counter(lab.get(os.path.splitext(b)[0], "__UNLABELED__") for b in fs)
    d_un, d_ad = dist(unused), dist([b for b in A])
    phases = sorted({p for p in lab.values()})

    # ---- Step M3-4: 判定 --------------------------------------------------- #
    reasons = []
    if Hc["unused_with_tool_ann_rate"] < 0.01:
        reasons.append("H-c 支持: 未採用フレームはほぼ tool ann を持たない")
    ha_support = (Ha["mean_mod_concentration"] or 0) > 0.9
    if ha_support:
        reasons.append("H-a 支持: 採用フレームが等間隔")
    hd_support = Hd["edge_rate"] > 0.5
    if hd_support:
        reasons.append("H-d 支持: 未採用がセグメント端に偏る")
    hb_ratio = None
    if Hb["bbox_area_unused"].get("n", 0) > 0 and Hb["bbox_area_adopted"].get("n", 0) > 0:
        hb_ratio = abs(Hb["bbox_area_unused"]["median"] - Hb["bbox_area_adopted"]["median"]) / \
            max(1.0, Hb["bbox_area_adopted"]["median"])
    hb_support = hb_ratio is not None and hb_ratio > 0.3
    Hb["median_relative_difference"] = hb_ratio
    Hb["criterion"] = "相対差 > 0.30 で支持"
    if hb_support:
        reasons.append("H-b 支持: 未採用の bbox 面積分布が採用と大きく異なる")
    elif hb_ratio is not None and hb_ratio > 0.2:
        reasons.append(f"H-b 境界値 (相対差 {hb_ratio:.3f}、基準 0.30 に未達だが小さくない)")

    rare_unused = {ph: d_un.get(ph, 0) for ph in RARE_PHASES}
    has_rare = sum(rare_unused.values()) > 0
    n_labeled_unused = len(unused) - d_un.get("__UNLABELED__", 0)

    # 規則の同定 (M3-2) と、評価枠拡張の可否 (M3-4) は別の問い。分けて判定する。
    rule_verdict = "規則不明" if not reasons else "; ".join(reasons)

    if n_labeled_unused == 0:
        expansion = "拡張不可"
        expansion_reason = (
            f"未採用 {len(unused)} 枚は tool ann を {unused_with_tool} 枚 "
            f"({Hc['unused_with_tool_ann_rate']:.1%}) 持つが、**phase ラベルが 1 件も存在しない**"
            "（該当セグメントの CSV が提供されていない）。工程評価には使えないため以後この論点は閉じる。"
            "※ 指示書 M3-4 の判定表は「ann の有無」で分岐するが、実データは "
            "「ann はあるが phase ラベルが無い」という表に無いパターンだった。")
    elif unused_with_tool == 0:
        expansion = "拡張不可"
        expansion_reason = "未採用フレームに tool ann が無い。以後この論点は閉じる"
    elif has_rare:
        expansion = "評価枠拡張の候補"
        expansion_reason = "rare 工程が存在し ann もある。採用は意思決定事項なので選択肢と根拠を書くに留める"
    else:
        expansion = "拡張不可"
        expansion_reason = "未採用フレームに rare 工程が無い"

    verdict = f"{rule_verdict} / 評価枠拡張: {expansion}"
    action = expansion_reason

    result = {
        "task": "M3_split_thinning_rule",
        "counts": {"P": len(P), "A": len(A), "excluded_segment_frames": len(excluded),
                   "unused": len(unused), "expected_unused": EXPECTED_UNUSED,
                   "count_matches_expected": count_matches},
        "H_a_temporal_subsampling": Ha,
        "H_b_quality_filter": Hb,
        "H_c_annotation_missing": Hc,
        "H_d_segment_edge": Hd,
        "phase_distribution": {
            "unused": dict(d_un.most_common()),
            "adopted": dict(d_ad.most_common()),
            "rare_in_unused": rare_unused,
        },
        "hypotheses_supported": reasons,
        "rule_verdict": rule_verdict,
        "expansion_verdict": expansion,
        "n_labeled_unused_frames": n_labeled_unused,
        "verdict": verdict,
        "action": action,
    }
    with open(os.path.join(out, "json", "m3_thinning.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out, "csv", "m3_unused_frames_by_phase.csv"), "w") as f:
        f.write("phase,n_unused,n_adopted,is_rare\n")
        for ph in phases + ["__UNLABELED__"]:
            f.write(f"{ph},{d_un.get(ph,0)},{d_ad.get(ph,0)},{ph in RARE_PHASES}\n")
    with open(os.path.join(out, "csv", "m3_segment_detail.csv"), "w") as f:
        cols = ["segment", "n_adopted", "n_unused", "modal_step", "mod_concentration",
                "adopted_min", "adopted_max", "unused_min", "unused_max"]
        f.write(",".join(cols) + "\n")
        for r in seg_rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")

    print(f"\n未採用件数一致: {count_matches} ({len(unused)} vs 期待 {EXPECTED_UNUSED})")
    print(f"\nH-a 等間隔: modal_step={Ha['modal_step_overall']} "
          f"mean_mod_concentration={Ha['mean_mod_concentration']}")
    print(f"H-b 面積: unused_median={Hb['bbox_area_unused'].get('median')} "
          f"adopted_median={Hb['bbox_area_adopted'].get('median')}")
    print(f"H-c ann欠落: 未採用 {len(unused)} 中 tool ann>=1 は {unused_with_tool} "
          f"({Hc['unused_with_tool_ann_rate']:.4f}) / hands ファイル収録 {unused_in_hands_file} "
          f"うち hand ann>=1 {unused_with_hand}")
    print(f"H-d 端偏り: {Hd['edge_rate']:.4f} (一様なら 0.2)")
    print(f"\n工程分布(未採用): {dict(d_un.most_common(5))}")
    print(f"rare 3 工程(未採用): {rare_unused}")
    print(f"\n支持された仮説: {reasons}")
    print(f"\n=== M3 VERDICT: {verdict} ===\n  {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
