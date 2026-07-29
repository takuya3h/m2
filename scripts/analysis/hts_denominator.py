#!/usr/bin/env python3
"""T1: EgoSurgery-HTS の分母確定 — canonical split に対する Hand-Tool 被覆率の実測。

現行の「被覆率 59.0% (9,106/15,437)」は不完全な検出 split 版 (fusion/*_toolhand_withmask)
で測った値。完全版とされる fusion/merged_annotations.json で測り直し、
G-1 を広い分母で回せるかを決める。

- 集合 A: canonical split (data/annotations/egosurgery_tool/instances_{split}.json)
- 集合 B: by_split 版 Hand-Tool (fusion/{split}_toolhand_withmask.json)
- 集合 C: 完全版とされる Hand-Tool (fusion/merged_annotations.json)

被覆率は 2 通りの定義で測る (この 2 つが乖離することが本タスクの核心):
  (i)  entry     : merged に画像エントリが存在する
  (ii) annotated : 有効な Hand-Tool annotation を 1 件以上持つ  ← G-1 が使えるのはこちら
判定は (ii) で行う。annotation 0 件の画像は relation 特徴を持たないため分母に数えられない。

join は必ず basename で行う (A のみ file_name に "train/01/" 等のパス接頭辞が付くため)。
canonical split の動画割当は data/splits/ego_{train,val,test}.txt を正とする (ハードコードしない)。

Usage:
    python3 scripts/analysis/hts_denominator.py --out $OUT
    python3 scripts/analysis/hts_denominator.py --self-test   # 合成データで検出能力を確認
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HTS = os.path.join(REPO, "data/raw/OpenSurgery_Dataset/05_egosurgery_hts")
TOOL_BY_VIDEO = os.path.join(HTS, "egosurgery_tool_bbox/annotations/bbox/by_video/tool")
SPLITS = ["train", "val", "test"]

# §1.1 で canonical split から除外されているとされるセグメント (再確認の対象)
EXCLUDED_SEGMENTS_EXPECTED = {"03_1", "03_3", "12_2", "15_2"}

# basename 例: "01_1_0124.jpg" -> video="01", segment="01_1", frame="0124"
#              A 側は "train/01/01_1_0124.jpg" のようにパス接頭辞が付くため basename 化してから適用する
FRAME_RE = re.compile(r"^(?P<video>\d+)_(?P<segidx>\d+)_(?P<frame>\d+)\.(?:jpg|png)$")


def parse_frame(basename: str):
    """basename から (video, segment, frame) を抽出。規則に合わなければ None。"""
    m = FRAME_RE.match(basename)
    if not m:
        return None
    v, s = m.group("video"), m.group("segidx")
    return v, f"{v}_{s}", m.group("frame")


def load_coco(path: str):
    """COCO JSON を読み、basename 単位の annotation 数と整合性情報を返す。

    returns dict(
        basenames        = {basename: image_id},
        ann_by_basename  = Counter{basename: 有効 annotation 数},
        n_ann_raw        = annotations 配列の長さ (論文値はこちらを数えている),
        n_ann_valid      = image_id が images に存在する annotation 数,
        n_ann_dangling   = image_id が images に存在しない annotation 数,
        dangling_ids     = 該当 image_id の例,
    )
    """
    with open(path) as f:
        d = json.load(f)
    id2bn, dupes = {}, []
    basenames = {}
    for im in d["images"]:
        b = os.path.basename(im["file_name"])
        if b in basenames:
            dupes.append(b)
        basenames[b] = im["id"]
        id2bn[im["id"]] = b
    if dupes:
        print(f"  [WARN] {path}: basename 重複 {len(dupes)} 件 (例 {dupes[:5]})", file=sys.stderr)

    ann = Counter()
    dangling = []
    for a in d.get("annotations", []):
        iid = a["image_id"]
        if iid in id2bn:
            ann[id2bn[iid]] += 1
        else:
            dangling.append(iid)
    return {
        "basenames": basenames,
        "ann_by_basename": ann,
        "n_ann_raw": len(d.get("annotations", [])),
        "n_ann_valid": sum(ann.values()),
        "n_ann_dangling": len(dangling),
        "dangling_ids": sorted(set(dangling))[:20],
        "n_images": len(d["images"]),
        "n_categories": len(d.get("categories", [])),
    }


def load_canonical_video_split(repo: str) -> dict[str, str]:
    """data/splits/ego_{split}.txt から {video: split} を作る (canonical の正本)。"""
    v2s: dict[str, str] = {}
    for sp in SPLITS:
        p = os.path.join(repo, f"data/splits/ego_{sp}.txt")
        with open(p) as f:
            for line in f:
                v = line.strip()
                if v:
                    v2s[v] = sp
    return v2s


# --------------------------------------------------------------------------- #
# Step 1-5: 合成データによる検出能力の確認
# --------------------------------------------------------------------------- #
def _mini_coco(images, anns, path, prefix=""):
    """images: [basename], anns: [(image_id, n)] -> COCO JSON を書く"""
    d = {
        "images": [{"id": i + 1, "file_name": prefix + b, "width": 10, "height": 10}
                   for i, b in enumerate(images)],
        "annotations": [],
        "categories": [{"id": 1, "name": "dummy"}],
    }
    k = 1
    for iid, n in anns:
        for _ in range(n):
            d["annotations"].append({"id": k, "image_id": iid, "category_id": 1,
                                     "bbox": [0, 0, 1, 1], "area": 1, "iscrowd": 0})
            k += 1
    with open(path, "w") as f:
        json.dump(d, f)
    return path


def self_test() -> int:
    """検出できることを確認する項目:
       (1) 片方にしか存在しない画像を n_recovered として数えられるか
       (2) 母集団外の画像を検出できるか
       (3) annotation 0 件の「空エントリ」を被覆に数えないか  ← 本タスクの核心
       (4) dangling annotation (存在しない image_id) を検出できるか
    """
    ok = True
    with tempfile.TemporaryDirectory() as td:
        a_names = ["01_1_0001.jpg", "01_1_0002.jpg", "01_1_0003.jpg"]
        pa = _mini_coco(a_names, [(1, 1), (2, 1), (3, 1)],
                        os.path.join(td, "a.json"), prefix="train/01/")
        # B: A の部分集合 (1 枚のみ・ann あり)
        pb = _mini_coco(["01_1_0001.jpg"], [(1, 2)], os.path.join(td, "b.json"))
        # C: 画像 3 枚 (うち 01_1_0002 は ann 0 件の空エントリ) + 母集団外 1 枚
        #    + dangling annotation (image_id=99 は存在しない)
        pc = _mini_coco(["01_1_0001.jpg", "01_1_0002.jpg", "99_9_9999.jpg"],
                        [(1, 2), (3, 1), (99, 5)], os.path.join(td, "c.json"))

        A = load_coco(pa)
        B = load_coco(pb)
        C = load_coco(pc)

        # (0) basename 正規化
        if set(A["basenames"]) != set(a_names):
            print("  [FAIL] basename 正規化が機能していない"); ok = False
        else:
            print("  [OK]   basename 正規化 (パス接頭辞を除去できた)")

        Aset = set(A["basenames"])
        C_entry = set(C["basenames"])
        C_annotated = {b for b, n in C["ann_by_basename"].items() if n > 0}

        # (1) n_recovered (entry 基準) = |A∩C_entry| - |A∩B| = 2 - 1 = 1
        n_rec = len(Aset & C_entry) - len(Aset & set(B["basenames"]))
        if n_rec != 1:
            print(f"  [FAIL] n_recovered(entry) 期待 1, 実測 {n_rec}"); ok = False
        else:
            print("  [OK]   片方にしか無い画像を n_recovered として検出できた (=1)")

        # (2) 母集団外検出
        outside = C_entry - Aset
        if outside != {"99_9_9999.jpg"}:
            print(f"  [FAIL] 母集団外検出 期待 {{99_9_9999.jpg}}, 実測 {outside}"); ok = False
        else:
            print("  [OK]   母集団外の画像を検出できた (99_9_9999.jpg)")

        # (3) 空エントリを被覆に数えない: 01_1_0002 は ann 0 件なので annotated 側では 1 枚のみ
        cov_entry = len(Aset & C_entry)       # = 2 (0001, 0002)
        cov_ann = len(Aset & C_annotated)     # = 1 (0001 のみ)
        if not (cov_entry == 2 and cov_ann == 1):
            print(f"  [FAIL] 空エントリ判別 期待 entry=2/annotated=1, "
                  f"実測 entry={cov_entry}/annotated={cov_ann}"); ok = False
        else:
            print("  [OK]   annotation 0 件の空エントリを被覆から除外できた (entry=2 vs annotated=1)")

        # (4) dangling annotation 検出
        if C["n_ann_dangling"] != 5:
            print(f"  [FAIL] dangling 検出 期待 5, 実測 {C['n_ann_dangling']}"); ok = False
        else:
            print("  [OK]   存在しない image_id を指す annotation を検出できた (=5)")

        # (5) 未知パターン拒否
        if parse_frame("garbage.jpg") is not None:
            print("  [FAIL] 未知パターンを parse_frame が受理した"); ok = False
        else:
            print("  [OK]   未知 file_name パターンを parse_frame が拒否した")

    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None, help="出力ディレクトリ ($OUT)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.out:
        ap.error("--out か --self-test のどちらかが必要")

    out = args.out
    for sub in ("json", "csv", "subsets"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    v2s = load_canonical_video_split(REPO)
    print(f"canonical video->split ({len(v2s)} videos): {sorted(v2s.items())}")

    # ---- Step 1-1: 3 つのフレーム集合 -------------------------------------- #
    A = {sp: load_coco(os.path.join(REPO, f"data/annotations/egosurgery_tool/instances_{sp}.json"))
         for sp in SPLITS}
    B = {sp: load_coco(os.path.join(HTS, f"fusion/{sp}_toolhand_withmask.json")) for sp in SPLITS}
    C = load_coco(os.path.join(HTS, "fusion/merged_annotations.json"))

    C_entry = set(C["basenames"])
    C_annotated = {b for b, n in C["ann_by_basename"].items() if n > 0}

    # merged には split 情報が無い -> basename から video を取り、canonical 割当で split を導出
    C_split: dict[str, set[str]] = {sp: set() for sp in SPLITS}
    C_unparsed, C_unknown_video = [], []
    for b in C_entry:
        pf = parse_frame(b)
        if pf is None:
            C_unparsed.append(b); continue
        sp = v2s.get(pf[0])
        if sp is None:
            C_unknown_video.append(b); continue
        C_split[sp].add(b)

    # ---- Step 1-2: 交差 ---------------------------------------------------- #
    rows, per_video = [], []
    totals = Counter()
    identical_to_bysplit = True
    for sp in SPLITS:
        a = set(A[sp]["basenames"])
        b = set(B[sp]["basenames"])
        c_e = C_split[sp] & C_entry
        c_a = C_split[sp] & C_annotated
        i_b, i_ce, i_ca = a & b, a & c_e, a & c_a
        ann_b = sum(B[sp]["ann_by_basename"][x] for x in i_b)
        ann_c = sum(C["ann_by_basename"][x] for x in i_ca)
        if i_ca != i_b:
            identical_to_bysplit = False
        r = {
            "split": sp,
            "n_canonical": len(a),
            "n_ht_bysplit": len(i_b),
            "n_ht_merged_entry": len(i_ce),
            "n_ht_merged_annotated": len(i_ca),
            "coverage_bysplit": len(i_b) / len(a) if a else 0.0,
            "coverage_merged_entry": len(i_ce) / len(a) if a else 0.0,
            "coverage_merged_annotated": len(i_ca) / len(a) if a else 0.0,
            "n_recovered_entry": len(i_ce) - len(i_b),
            "n_recovered_annotated": len(i_ca) - len(i_b),
            "ann_bysplit": ann_b,
            "ann_merged": ann_c,
        }
        rows.append(r)
        for k, v in r.items():
            if isinstance(v, int):
                totals[k] += v

        vids = defaultdict(lambda: [0, 0, 0, 0])
        for x in a:
            if (pf := parse_frame(x)): vids[pf[0]][0] += 1
        for x in i_b:
            if (pf := parse_frame(x)): vids[pf[0]][1] += 1
        for x in i_ce:
            if (pf := parse_frame(x)): vids[pf[0]][2] += 1
        for x in i_ca:
            if (pf := parse_frame(x)): vids[pf[0]][3] += 1
        for v in sorted(vids):
            n_can, n_bs, n_me, n_ma = vids[v]
            per_video.append({
                "split": sp, "video": v, "n_canonical": n_can, "n_ht_bysplit": n_bs,
                "n_ht_merged_entry": n_me, "n_ht_merged_annotated": n_ma,
                "coverage_bysplit": n_bs / n_can if n_can else 0.0,
                "coverage_merged_annotated": n_ma / n_can if n_can else 0.0,
                "n_recovered_annotated": n_ma - n_bs,
            })

    cov_bysplit = totals["n_ht_bysplit"] / totals["n_canonical"]
    cov_entry = totals["n_ht_merged_entry"] / totals["n_canonical"]
    cov_annotated = totals["n_ht_merged_annotated"] / totals["n_canonical"]

    # ---- Step 1-3: 母集団はみ出し確認 -------------------------------------- #
    P = set()
    for v in sorted(os.listdir(TOOL_BY_VIDEO)):
        p = os.path.join(TOOL_BY_VIDEO, v, "annotations.json")
        if os.path.exists(p):
            P |= set(load_coco(p)["basenames"])
    A_all = set().union(*[set(A[sp]["basenames"]) for sp in SPLITS])
    canonical_segments = {pf[1] for y in A_all if (pf := parse_frame(y))}
    P_segments = {pf[1] for y in P if (pf := parse_frame(y))}
    excluded_imgs = {x for x in P if (pf := parse_frame(x)) and pf[1] not in canonical_segments}
    excluded_segments_actual = sorted({pf[1] for x in excluded_imgs if (pf := parse_frame(x))})
    # canonical セグメント内なのに canonical split に採用されていないフレーム
    within_seg_gap = {x for x in P if (pf := parse_frame(x)) and pf[1] in canonical_segments} - A_all

    outside_P = C_entry - P
    outside_AplusExcl = C_entry - (A_all | excluded_imgs)

    # ---- Step 1-4: subset 出力 (annotated 基準 = Phase C の分母) ------------ #
    subset_sizes = {}
    for sp in SPLITS:
        usable = sorted(set(A[sp]["basenames"]) & C_annotated)
        subset_sizes[sp] = len(usable)
        with open(os.path.join(out, "subsets", f"subset_ht_{sp}.txt"), "w") as f:
            f.write("\n".join(usable) + ("\n" if usable else ""))

    # ---- Step 1-6: 判定 (annotated 基準) ----------------------------------- #
    if cov_annotated >= 0.85:
        verdict, action = "PASS", "I1 は実質回復。G-1 を広い分母で実行可 (Phase C へ)"
    elif cov_annotated >= 0.70:
        verdict, action = "WARN", "G-1 は実行可だが被覆率を論文に明記し、非被覆フレームの工程分布を追加報告"
    else:
        verdict, action = "FAIL", "従来の 59% と大差なし。G-1 を「縮約 split 上での比較」に設計変更が必要"

    result = {
        "task": "T1_denominator",
        "canonical_video_split": v2s,
        "video_id_extraction_rule": (
            "os.path.basename 適用後、正規表現 "
            r"'^(?P<video>\d+)_(?P<segidx>\d+)_(?P<frame>\d+)\.(jpg|png)$' を適用し "
            "video=第1トークン、segment='video_segidx' とする。"
            "A 側の file_name は 'train/01/01_1_0124.jpg' のようにパス接頭辞を持つため basename 化が必須。"
        ),
        "coverage_definitions": {
            "entry": "merged に画像エントリが存在する (annotation 0 件でも数える)",
            "annotated": "有効な Hand-Tool annotation を 1 件以上持つ (G-1 が使えるのはこちら。判定に使用)",
        },
        "per_split": rows,
        "totals": {
            "n_canonical": totals["n_canonical"],
            "n_ht_bysplit": totals["n_ht_bysplit"],
            "n_ht_merged_entry": totals["n_ht_merged_entry"],
            "n_ht_merged_annotated": totals["n_ht_merged_annotated"],
            "n_recovered_entry": totals["n_recovered_entry"],
            "n_recovered_annotated": totals["n_recovered_annotated"],
            "ann_bysplit": totals["ann_bysplit"],
            "ann_merged": totals["ann_merged"],
            "coverage_bysplit": cov_bysplit,
            "coverage_merged_entry": cov_entry,
            "coverage_merged_annotated": cov_annotated,
        },
        "merged_file_integrity": {
            "n_images": C["n_images"],
            "n_ann_raw": C["n_ann_raw"],
            "n_ann_valid": C["n_ann_valid"],
            "n_ann_dangling": C["n_ann_dangling"],
            "dangling_image_id_examples": C["dangling_ids"],
            "n_images_with_zero_ann": C["n_images"] - len(C_annotated),
            "note": ("論文値 41,605 は annotations 配列の生の長さ。"
                     "うち image_id が images に存在しない dangling が含まれる。"),
        },
        "identical_to_bysplit": identical_to_bysplit,
        "identical_note": ("True の場合、merged の annotated フレーム集合は by_split 版と完全一致し、"
                           "merged による被覆率向上は存在しない (追加分は全て annotation 0 件の空エントリ)。"),
        "population_check": {
            "population_size_P": len(P),
            "population_segments": sorted(P_segments),
            "canonical_total_A": len(A_all),
            "canonical_segments": sorted(canonical_segments),
            "excluded_segments_actual": excluded_segments_actual,
            "excluded_segments_expected": sorted(EXCLUDED_SEGMENTS_EXPECTED),
            "excluded_segment_images": len(excluded_imgs),
            "within_canonical_segment_gap": len(within_seg_gap),
            "gap_P_minus_A": len(P) - len(A_all),
            "merged_size_C": len(C_entry),
            "C_outside_P": len(outside_P),
            "C_outside_P_examples": sorted(outside_P)[:20],
            "C_outside_A_plus_excluded": len(outside_AplusExcl),
            "C_outside_A_plus_excluded_examples": sorted(outside_AplusExcl)[:20],
            "C_unparsed_basenames": len(C_unparsed),
            "C_unknown_video": len(C_unknown_video),
        },
        "subset_sizes": subset_sizes,
        "verdict": verdict,
        "action": action,
    }
    with open(os.path.join(out, "json", "t1_denominator.json"), "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    cols = ["split", "n_canonical", "n_ht_bysplit", "n_ht_merged_entry",
            "n_ht_merged_annotated", "coverage_bysplit", "coverage_merged_entry",
            "coverage_merged_annotated", "n_recovered_entry", "n_recovered_annotated",
            "ann_bysplit", "ann_merged"]
    with open(os.path.join(out, "csv", "t1_coverage_by_split.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for r in rows:
            f.write(",".join(str(r[c]) for c in cols) + "\n")
    vcols = ["split", "video", "n_canonical", "n_ht_bysplit", "n_ht_merged_entry",
             "n_ht_merged_annotated", "coverage_bysplit", "coverage_merged_annotated",
             "n_recovered_annotated"]
    with open(os.path.join(out, "csv", "t1_coverage_by_video.csv"), "w") as f:
        f.write(",".join(vcols) + "\n")
        for r in per_video:
            f.write(",".join(str(r[c]) for c in vcols) + "\n")

    print("\n=== T1 per-split (annotated 基準が判定に使う値) ===")
    for r in rows:
        print(f"  {r['split']:5s} canonical={r['n_canonical']:5d} | "
              f"bysplit={r['n_ht_bysplit']:5d}({r['coverage_bysplit']:.3f}) | "
              f"merged_entry={r['n_ht_merged_entry']:5d}({r['coverage_merged_entry']:.3f}) | "
              f"merged_annotated={r['n_ht_merged_annotated']:5d}({r['coverage_merged_annotated']:.3f}) "
              f"recovered={r['n_recovered_annotated']:+d}")
    print(f"  TOTAL canonical={totals['n_canonical']} bysplit={totals['n_ht_bysplit']}({cov_bysplit:.4f}) "
          f"entry={totals['n_ht_merged_entry']}({cov_entry:.4f}) "
          f"annotated={totals['n_ht_merged_annotated']}({cov_annotated:.4f})")
    print(f"  annotated 集合が by_split と完全一致: {identical_to_bysplit}")
    mi = result["merged_file_integrity"]
    print(f"\n=== merged 整合性 ===\n  ann_raw={mi['n_ann_raw']} valid={mi['n_ann_valid']} "
          f"dangling={mi['n_ann_dangling']} / ann0 画像={mi['n_images_with_zero_ann']}")
    pc = result["population_check"]
    print(f"\n=== 母集団 ===\n  P={pc['population_size_P']} A={pc['canonical_total_A']} "
          f"gap={pc['gap_P_minus_A']} (除外セグ由来={pc['excluded_segment_images']}, "
          f"canonicalセグ内未採用={pc['within_canonical_segment_gap']})")
    print(f"  除外セグ 実測={pc['excluded_segments_actual']} / 指示書記載={pc['excluded_segments_expected']}")
    print(f"  C_outside_P={pc['C_outside_P']}")
    print(f"\n=== T1 VERDICT: {verdict} ===\n  {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
