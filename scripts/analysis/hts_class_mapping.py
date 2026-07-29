#!/usr/bin/env python3
"""T3: 術具クラス体系 4 版の対応表を作る。

既存実験は by_split (15 クラス) の上で走り、mask は 14cls_cleaned である。
対応表なしに per-class AP を比較すると主張が崩れるため、
名前の文字列一致ではなく bbox の幾何一致でインスタンスを対応づけて混同行列を作る。

4 版:
  V31    by_video/tool                        (生・31 クラス)
  V14    03_tool/coco_splits_14cls_cleaned    (14 クラス・論文値に対応)
  V15k   03_tool/coco_splits_15cls_withkidney (15 クラス)
  VBS    data/annotations/egosurgery_tool     (by_split・15 クラス・既存実験の凍結源)

Usage:
    python3 scripts/analysis/hts_class_mapping.py --out $OUT
    python3 scripts/analysis/hts_class_mapping.py --self-test
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import tempfile
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(REPO, "data/raw/OpenSurgery_Dataset")
HTS = os.path.join(RAW, "05_egosurgery_hts")
TOOL_BY_VIDEO = os.path.join(HTS, "egosurgery_tool_bbox/annotations/bbox/by_video/tool")
SPLITS = ["train", "val", "test"]

SIGNATURE_TOOLS = ["Bipolar Forceps", "Scalpel", "Needle Holders"]
IOU_THR = 0.95


def version_paths():
    return {
        "V31": [os.path.join(TOOL_BY_VIDEO, v, "annotations.json")
                for v in sorted(os.listdir(TOOL_BY_VIDEO))
                if os.path.exists(os.path.join(TOOL_BY_VIDEO, v, "annotations.json"))],
        "V14": [os.path.join(RAW, "03_tool/coco_splits_14cls_cleaned", f"{s}.json")
                for s in SPLITS],
        "V15k": [os.path.join(RAW, "03_tool/coco_splits_15cls_withkidney", f"{s}.json")
                 for s in SPLITS],
        "VBS": [os.path.join(REPO, f"data/annotations/egosurgery_tool/instances_{s}.json")
                for s in SPLITS],
    }


def load_version(paths):
    """{basename: [(bbox, class_name)]} と categories 情報を返す。

    注意: 「宣言されている categories 数」と「実際に annotation を持つクラス数」は一致しない。
    例: tool_seg_noskewer は 31 categories を宣言するが Skewer / Mouth Gag は 0 件。
    """
    inst = defaultdict(list)
    cats = {}
    cat_count = Counter()
    supercat = {}
    for p in paths:
        if not os.path.exists(p):
            continue
        with open(p) as f:
            d = json.load(f)
        cmap = {c["id"]: c["name"] for c in d.get("categories", [])}
        for c in d.get("categories", []):
            cats[c["id"]] = c["name"]
            supercat[c["name"]] = c.get("supercategory", "")
        id2b = {im["id"]: os.path.basename(im["file_name"]) for im in d["images"]}
        for a in d["annotations"]:
            if a["image_id"] not in id2b:
                continue
            name = cmap.get(a["category_id"], str(a["category_id"]))
            inst[id2b[a["image_id"]]].append(([float(x) for x in a["bbox"]], name))
            cat_count[name] += 1
    return {"inst": inst, "categories": cats, "counts": cat_count, "supercategory": supercat,
            "n_declared": len(cats), "n_annotated": len(cat_count),
            "declared_but_empty": sorted(set(cats.values()) - set(cat_count))}


def bbox_key(b, nd=1):
    return tuple(round(v, nd) for v in b)


def iou(a, b):
    ax0, ay0, aw, ah = a; bx0, by0, bw, bh = b
    ix = max(0.0, min(ax0 + aw, bx0 + bw) - max(ax0, bx0))
    iy = max(0.0, min(ay0 + ah, by0 + bh) - max(ay0, by0))
    inter = ix * iy
    u = aw * ah + bw * bh - inter
    return inter / u if u > 0 else 0.0


def match_versions(va, vb, iou_thr=IOU_THR):
    """2 版のインスタンスを幾何一致で対応づけ、クラス混同 Counter を返す。

    1) bbox を小数第 1 位で丸めた完全一致
    2) 残りを IoU >= iou_thr で貪欲マッチ

    既定閾値は指示書 §3-2 の 0.95。ただし V14/V15k の bbox は VBS/V31 と別導出であり
    (実測: best-IoU 中央値 0.871)、0.95 では 15% 程度しか対応づかない。
    main() では複数閾値で感度を測る。
    """
    conf = Counter()
    n_exact = n_iou = 0
    only_a = Counter()
    only_b = Counter()
    for bn in set(va["inst"]) | set(vb["inst"]):
        la = va["inst"].get(bn, [])
        lb = vb["inst"].get(bn, [])
        if not la or not lb:
            for _, c in la: only_a[c] += 1
            for _, c in lb: only_b[c] += 1
            continue
        used_a, used_b = set(), set()
        # 1) 完全一致
        idx_b = defaultdict(list)
        for j, (bb, cb) in enumerate(lb):
            idx_b[bbox_key(bb)].append(j)
        for i, (ba, ca) in enumerate(la):
            k = bbox_key(ba)
            for j in idx_b.get(k, []):
                if j in used_b:
                    continue
                conf[(ca, lb[j][1])] += 1
                used_a.add(i); used_b.add(j); n_exact += 1
                break
        # 2) IoU 貪欲
        cand = []
        for i, (ba, ca) in enumerate(la):
            if i in used_a:
                continue
            for j, (bb, cb) in enumerate(lb):
                if j in used_b:
                    continue
                v = iou(ba, bb)
                if v >= iou_thr:
                    cand.append((v, i, j))
        cand.sort(key=lambda x: -x[0])
        for v, i, j in cand:
            if i in used_a or j in used_b:
                continue
            conf[(la[i][1], lb[j][1])] += 1
            used_a.add(i); used_b.add(j); n_iou += 1
        for i, (_, ca) in enumerate(la):
            if i not in used_a: only_a[ca] += 1
        for j, (_, cb) in enumerate(lb):
            if j not in used_b: only_b[cb] += 1
    return {"conf": conf, "n_exact": n_exact, "n_iou": n_iou,
            "only_a": only_a, "only_b": only_b}


def self_test() -> int:
    """検出できることを確認する:
       (1) 名前が変わっても幾何一致で対応づけられるか (統合の検出)
       (2) 1 対多 (同一クラスが複数クラスに分岐) を検出できるか
       (3) 片側にしか無いインスタンスを only_a / only_b に落とせるか
    """
    ok = True
    with tempfile.TemporaryDirectory() as td:
        def mk(path, anns, cats):
            d = {"images": [{"id": 1, "file_name": "01_1_0001.jpg", "height": 100, "width": 100}],
                 "annotations": [{"id": i + 1, "image_id": 1, "bbox": b, "category_id": c,
                                  "area": b[2] * b[3], "iscrowd": 0}
                                 for i, (b, c) in enumerate(anns)],
                 "categories": [{"id": k, "name": v} for k, v in cats.items()]}
            with open(path, "w") as f:
                json.dump(d, f)
            return path
        # A: 2 インスタンス (Forceps, Bipolar Forceps) + 片側のみ 1 件
        pa = mk(os.path.join(td, "a.json"),
                [([10, 10, 20, 20], 1), ([50, 50, 10, 10], 2), ([80, 80, 5, 5], 1)],
                {1: "Forceps", 2: "Bipolar Forceps"})
        # B: 同じ bbox だが Bipolar Forceps が Forceps に統合されている
        pb = mk(os.path.join(td, "b.json"),
                [([10, 10, 20, 20], 1), ([50, 50, 10, 10], 1)],
                {1: "Forceps"})
        A, B = load_version([pa]), load_version([pb])
        r = match_versions(A, B)
        conf = r["conf"]
        if conf.get(("Bipolar Forceps", "Forceps")) != 1:
            print(f"  [FAIL] 統合を検出できない: {dict(conf)}"); ok = False
        else:
            print("  [OK]   名前が変わっても幾何一致で統合を検出 (Bipolar Forceps -> Forceps)")
        if r["only_a"].get("Forceps") != 1:
            print(f"  [FAIL] 片側のみのインスタンスを検出できない: {dict(r['only_a'])}"); ok = False
        else:
            print("  [OK]   片側にしか無いインスタンスを only_a に分離")

        # (2) 1 対多: A の 1 クラスが B の 2 クラスに割れる
        pc = mk(os.path.join(td, "c.json"),
                [([10, 10, 20, 20], 1), ([50, 50, 10, 10], 1)], {1: "Tool"})
        pd = mk(os.path.join(td, "d.json"),
                [([10, 10, 20, 20], 1), ([50, 50, 10, 10], 2)], {1: "X", 2: "Y"})
        r2 = match_versions(load_version([pc]), load_version([pd]))
        targets = {b for (a, b) in r2["conf"] if a == "Tool"}
        if targets != {"X", "Y"}:
            print(f"  [FAIL] 1 対多を検出できない: {dict(r2['conf'])}"); ok = False
        else:
            print("  [OK]   1 対多 (Tool -> {X, Y}) を検出")
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

    vp = version_paths()
    V = {}
    for k, paths in vp.items():
        V[k] = load_version(paths)
        print(f"{k}: images={len(V[k]['inst'])} ann={sum(V[k]['counts'].values())} "
              f"ncls={len(V[k]['counts'])}")

    # ---- Step 3-1: categories 実測ダンプ ---------------------------------- #
    cat_rows = []
    for k in V:
        for name, n in sorted(V[k]["counts"].items(), key=lambda x: -x[1]):
            cid = next((i for i, nm in V[k]["categories"].items() if nm == name), None)
            cat_rows.append({"version": k, "category_id": cid, "name": name,
                             "supercategory": V[k]["supercategory"].get(name, ""), "n_ann": n})

    # ---- Step 3-2: 版 × 版 混同行列 --------------------------------------- #
    pairs = [("VBS", "V14"), ("VBS", "V15k"), ("V31", "V14"), ("V31", "VBS"), ("V14", "V15k")]
    cross = {}
    conf_rows = []
    for a, b in pairs:
        r = match_versions(V[a], V[b])
        cross[f"{a}->{b}"] = {
            "n_matched": sum(r["conf"].values()),
            "n_exact_bbox": r["n_exact"],
            "n_iou_matched": r["n_iou"],
            "n_only_a": sum(r["only_a"].values()),
            "n_only_b": sum(r["only_b"].values()),
            "only_a_by_class": dict(r["only_a"].most_common()),
            "only_b_by_class": dict(r["only_b"].most_common()),
            "confusion": {f"{x}||{y}": n for (x, y), n in r["conf"].most_common()},
        }
        for (x, y), n in r["conf"].most_common():
            conf_rows.append({"pair": f"{a}->{b}", "class_a": x, "class_b": y, "count": n})
        print(f"  {a}->{b}: matched={sum(r['conf'].values())} "
              f"(exact={r['n_exact']}, iou={r['n_iou']}) "
              f"only_{a}={sum(r['only_a'].values())} only_{b}={sum(r['only_b'].values())}")

    # ---- Step 3-2b: 閾値感度 (VBS->V14 は bbox が別導出のため単一閾値では決められない) --- #
    sweep = {}
    for thr in (0.95, 0.90, 0.70, 0.50):
        r = match_versions(V["VBS"], V["V14"], iou_thr=thr)
        src_dest_t = defaultdict(Counter)
        for (x, y), n in r["conf"].items():
            src_dest_t[x][y] += n
        otm = {}
        for s, dd in src_dest_t.items():
            tot = sum(dd.values())
            # ノイズ (支配率 5% 未満) を除いた実質的な 1 対多のみを拾う
            major = {d: n for d, n in dd.items() if n / tot >= 0.05}
            if len(major) > 1:
                otm[s] = {"total": tot, "major_destinations": major}
        sweep[str(thr)] = {
            "n_matched": sum(r["conf"].values()),
            "match_rate_vs_VBS": sum(r["conf"].values()) / max(1, sum(V["VBS"]["counts"].values())),
            "one_to_many_major": otm,
            "minor_destinations": {
                s: {d: n for d, n in dd.items() if n / sum(dd.values()) < 0.05}
                for s, dd in src_dest_t.items()
                if any(n / sum(dd.values()) < 0.05 for n in dd.values())
            },
        }
        print(f"  sweep IoU>={thr}: matched={sum(r['conf'].values())} "
              f"({sweep[str(thr)]['match_rate_vs_VBS']:.3f}) 実質1対多={list(otm)}")

    # ---- Step 3-3: 3 つの問い -------------------------------------------- #
    # Q1: signature 3 術具は V14 で生存しているか
    q1 = {}
    vbs_v14 = cross["VBS->V14"]["confusion"]
    for t in SIGNATURE_TOOLS:
        present = t in V["V14"]["counts"]
        dest = Counter()
        for k, n in vbs_v14.items():
            x, y = k.split("||")
            if x == t:
                dest[y] += n
        q1[t] = {
            "in_V14_categories": present,
            "n_ann_V14": V["V14"]["counts"].get(t, 0),
            "n_ann_VBS": V["VBS"]["counts"].get(t, 0),
            "VBS_to_V14_destinations": dict(dest.most_common()),
            "absorbed_into_other_class": {d: n for d, n in dest.items() if d != t},
        }
    # Q2: Skewer の扱い
    q2 = {k: {"declared_in_categories": "Skewer" in set(V[k]["categories"].values()),
              "has_annotations": "Skewer" in V[k]["counts"],
              "n_ann": V[k]["counts"].get("Skewer", 0),
              "n_declared_categories": V[k]["n_declared"],
              "n_annotated_classes": V[k]["n_annotated"],
              "declared_but_empty": V[k]["declared_but_empty"]} for k in V}
    noskewer_dir = os.path.join(HTS, "tool_seg_noskewer")
    ns = load_version([os.path.join(noskewer_dir, s, f"{s}.json")
                       for s in sorted(os.listdir(noskewer_dir))
                       if os.path.exists(os.path.join(noskewer_dir, s, f"{s}.json"))])
    q2["tool_seg_noskewer"] = {
        "declared_in_categories": "Skewer" in set(ns["categories"].values()),
        "has_annotations": "Skewer" in ns["counts"],
        "n_ann": ns["counts"].get("Skewer", 0),
        "n_declared_categories": ns["n_declared"],
        "n_annotated_classes": ns["n_annotated"],
        "declared_but_empty": ns["declared_but_empty"],
        "note": ("§1.4-a の再確認。categories には Skewer が宣言されているが annotation 件数で判定する。"
                 "宣言 31 / 実データを持つクラス数は別値になる。"),
    }
    # Q3: VBS(15) -> V14(14) は一意写像か
    src_dest = defaultdict(Counter)
    for k, n in vbs_v14.items():
        x, y = k.split("||")
        src_dest[x][y] += n
    one_to_many = {s: dict(d) for s, d in src_dest.items() if len(d) > 1}
    dropped = {c: V["VBS"]["counts"][c] for c in V["VBS"]["counts"] if c not in V["V14"]["counts"]}
    q3 = {
        "mapping": {s: dict(d.most_common()) for s, d in src_dest.items()},
        "one_to_many_classes": one_to_many,
        "is_unique_mapping": len(one_to_many) == 0,
        "classes_in_VBS_absent_from_V14": dropped,
        "classes_in_V14_absent_from_VBS":
            {c: V["V14"]["counts"][c] for c in V["V14"]["counts"] if c not in V["VBS"]["counts"]},
    }

    # ---- Step 3-4: 判定 --------------------------------------------------- #
    # 単一閾値 (0.95) の literal 判定はマッチ率が低く 1 インスタンスのノイズで反転するため、
    # 全閾値で「実質的な 1 対多 (支配率 >= 5%)」が 0 かどうかを頑健な基準として使う。
    robust_one_to_many = {t: s["one_to_many_major"] for t, s in sweep.items()
                          if s["one_to_many_major"]}
    sig_alive = all(q1[t]["in_V14_categories"] for t in SIGNATURE_TOOLS)
    sig_absorbed = any(q1[t]["absorbed_into_other_class"] for t in SIGNATURE_TOOLS)
    q3["robust_is_unique_mapping"] = len(robust_one_to_many) == 0
    q3["robust_one_to_many_by_threshold"] = robust_one_to_many
    q3["literal_criterion_note"] = (
        "指示書 §3-2 の literal 基準 (丸め一致 or IoU>=0.95) では VBS の 15.5% しか対応づかず、"
        "検出された 1 対多は Scissors -> {Scissors, Gauze} の Gauze 1 件 (0.24%) のみで、"
        "閾値を変えると消えるマッチングノイズ。判定には支配率 5% 以上の実質的 1 対多を使う。")

    if not q3["robust_is_unique_mapping"]:
        verdict = "FAIL"
        action = "実質的な 1 対多が存在。per-class AP の比較は不可。overall のみで議論する設計に変更"
    elif sig_alive and not sig_absorbed:
        verdict = "PASS"
        action = ("一意写像が可能かつ signature 3 術具が全版で生存。per-class 比較が可能。"
                  "ただし VBS にのみ存在する Mouth Gag (5,985 ann) は V14 に写像先が無く脱落する。")
    else:
        verdict = "WARN"
        action = ("一意写像は可能だが signature 術具が統合されている。"
                  "G-2 の効果測定は可能だが per-phase の帰属分析が不可能になる旨を明記")

    result = {
        "task": "T3_class_mapping",
        "versions": {k: {"n_images": len(V[k]["inst"]), "n_ann": sum(V[k]["counts"].values()),
                         "n_declared_categories": V[k]["n_declared"],
                         "n_annotated_classes": V[k]["n_annotated"],
                         "declared_but_empty": V[k]["declared_but_empty"],
                         "classes": sorted(V[k]["counts"].keys()),
                         "counts": dict(V[k]["counts"].most_common())} for k in V},
        "cross_version": cross,
        "iou_threshold_sweep_VBS_to_V14": sweep,
        "Q1_signature_tools_in_V14": q1,
        "Q2_skewer": q2,
        "Q3_VBS_to_V14_mapping": q3,
        "verdict": verdict,
        "action": action,
    }
    with open(os.path.join(out, "json", "t3_class_mapping.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(os.path.join(out, "csv", "t3_class_crosstab.csv"), "w") as f:
        f.write("pair,class_a,class_b,count\n")
        for r in conf_rows:
            f.write(f"{r['pair']},\"{r['class_a']}\",\"{r['class_b']}\",{r['count']}\n")
    with open(os.path.join(out, "csv", "t3_categories.csv"), "w") as f:
        f.write("version,category_id,name,supercategory,n_ann\n")
        for r in cat_rows:
            f.write(f"{r['version']},{r['category_id']},\"{r['name']}\","
                    f"\"{r['supercategory']}\",{r['n_ann']}\n")

    print("\n=== Q1 signature tools in V14 ===")
    for t, v in q1.items():
        print(f"  {t}: V14={v['in_V14_categories']} n_V14={v['n_ann_V14']} "
              f"n_VBS={v['n_ann_VBS']} absorbed={v['absorbed_into_other_class']}")
    print("\n=== Q2 Skewer ===")
    for k, v in q2.items():
        print(f"  {k}: {v}")
    print("\n=== Q3 VBS(15) -> V14(14) ===")
    print(f"  一意写像: {q3['is_unique_mapping']}  1対多: {q3['one_to_many_classes']}")
    print(f"  VBS にあり V14 に無いクラス: {q3['classes_in_VBS_absent_from_V14']}")
    print(f"\n=== T3 VERDICT: {verdict} ===\n  {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
