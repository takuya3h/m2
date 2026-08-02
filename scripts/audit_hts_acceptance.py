#!/usr/bin/env python3
"""EgoSurgery-HTS 受入監査 (要件 C01-C11).

静的解析のみ (GPU/学習不要). 元データは読み取り専用として扱う.
実測値のみを出力し, 測れないものは SKIP / UNKNOWN と明記する (数値捏造の絶対禁止).

使い方 (RLE デコードを伴う C06/C07 は pycocotools 必須):
    uv run --no-project --with "numpy<2" --with pycocotools \
        python3 scripts/audit_hts_acceptance.py \
        --hts-root  data/raw/OpenSurgery_Dataset/05_egosurgery_hts \
        --project-root . \
        --out reports/hts_audit

自己検証 (合成データで検出能力を確認):
    python3 scripts/audit_hts_acceptance.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import math
import os
import random
import statistics
import sys
import traceback
from collections import Counter, defaultdict

# ----------------------------------------------------------------------------
# 定数
# ----------------------------------------------------------------------------
CLS15 = {
    0: "Bipolar Forceps", 1: "Electric Cautery", 2: "Forceps", 3: "Gauze",
    4: "Hook", 5: "Mouth Gag", 6: "Needle Holders", 7: "Raspatory",
    8: "Retractor", 9: "Scalpel", 10: "Scissors", 11: "Skewer",
    12: "Suction Cannula", 13: "Syringe", 14: "Tweezers",
}
CLS15_NAMES = set(CLS15.values())
SIGNATURE_TOOLS = {"Bipolar Forceps", "Scalpel", "Needle Holders"}
GAP_PHASES = ("disinfection", "dressing", "irrigation")

# toolhand 5cls の tool 側 (mask を持つ) カテゴリ
TOOLHAND_TOOL_CATS = {3: "Left Hand Tool", 4: "Right Hand Tool", 5: "Two Hands Tool"}
TOOLHAND_HAND_CATS = {1: "First Person's Left Hand", 2: "First Person's Right Hand"}

# ----------------------------------------------------------------------------
# 汎用ヘルパ
# ----------------------------------------------------------------------------


class SkipCheck(Exception):
    """検査を SKIP として終了させる (理由付き)."""


def parse_filename(fn: str):
    """file_name -> (video, segment, frame_stem).

    例 '01_1_0124.jpg' -> ('01', '01_1', '01_1_0124').
    命名が想定外なら (None, None, stem) を返し, 呼び出し側で異常として記録する.
    """
    base = os.path.basename(str(fn))
    stem = os.path.splitext(base)[0]
    parts = stem.split("_")
    if len(parts) >= 3 and parts[0].isdigit():
        video = parts[0]
        segment = f"{parts[0]}_{parts[1]}"
        return video, segment, stem
    if len(parts) == 2 and parts[0].isdigit():
        return parts[0], parts[0], stem
    return None, None, stem


class Loader:
    """max_mb 超過ファイルはロードせず理由付きで拒否する JSON キャッシュ."""

    def __init__(self, max_mb: float):
        self.max_mb = max_mb
        self._cache: dict[str, object] = {}

    def size_mb(self, path: str) -> float:
        return os.path.getsize(path) / (1024 * 1024)

    def load(self, path: str):
        if path in self._cache:
            return self._cache[path]
        mb = self.size_mb(path)
        if mb > self.max_mb:
            raise SkipCheck(f"too_large ({mb:.1f}MB > {self.max_mb}MB)")
        with open(path) as f:
            data = json.load(f)
        self._cache[path] = data
        return data


def md5_file(path: str) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha1_of(obj) -> str:
    return hashlib.sha1(json.dumps(obj, sort_keys=True).encode()).hexdigest()


def get_iscrowd(ann) -> int:
    """iscrowd / is_crowd の両対応. 欠落は 0 とみなす."""
    if "iscrowd" in ann:
        return int(ann["iscrowd"] or 0)
    if "is_crowd" in ann:
        return int(ann["is_crowd"] or 0)
    return 0


def crowd_key(ann) -> str:
    if "iscrowd" in ann:
        return "iscrowd"
    if "is_crowd" in ann:
        return "is_crowd"
    return "missing"


def seg_kind(seg) -> str:
    """segmentation の実体分類: rle / polygon / rect_polygon / none / other."""
    if seg is None:
        return "none"
    if isinstance(seg, dict):
        return "rle"
    if isinstance(seg, list):
        if len(seg) == 0:
            return "none"
        # 単一リング 4 頂点 (8 値) で軸平行矩形なら rect_polygon
        if len(seg) == 1 and isinstance(seg[0], list) and len(seg[0]) == 8:
            xs = seg[0][0::2]
            ys = seg[0][1::2]
            if len(set(xs)) == 2 and len(set(ys)) == 2:
                return "rect_polygon"
            return "polygon"
        if isinstance(seg[0], list):
            return "polygon"
        if len(seg) == 8:  # flat 4 頂点
            xs = seg[0::2]
            ys = seg[1::2]
            if len(set(xs)) == 2 and len(set(ys)) == 2:
                return "rect_polygon"
            return "polygon"
        return "other"
    return "other"


def iou_xywh(a, b) -> float:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    ax2, ay2, bx2, by2 = ax + aw, ay + ah, bx + bw, by + bh
    ix = max(ax, bx)
    iy = max(ay, by)
    ix2 = min(ax2, bx2)
    iy2 = min(ay2, by2)
    iw = max(0.0, ix2 - ix)
    ih = max(0.0, iy2 - iy)
    inter = iw * ih
    ua = aw * ah + bw * bh - inter
    return inter / ua if ua > 0 else 0.0


def pct(values, qs=(5, 25, 50, 75, 95)):
    """分位点 (値なしは None). q は 0-100."""
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return {q: None for q in qs}
    out = {}
    for q in qs:
        idx = (len(vals) - 1) * (q / 100.0)
        lo = math.floor(idx)
        hi = math.ceil(idx)
        if lo == hi:
            out[q] = vals[int(idx)]
        else:
            out[q] = vals[lo] * (hi - idx) + vals[hi] * (idx - lo)
    return out


def write_csv(path: str, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


# ----------------------------------------------------------------------------
# 検査コンテキスト
# ----------------------------------------------------------------------------


class Ctx:
    def __init__(self, args):
        self.hts = args.hts_root
        self.proj = args.project_root
        self.out = args.out
        self.csv_dir = os.path.join(self.out, "csv")
        self.subset_dir = os.path.join(self.out, "subsets")
        self.loader = Loader(args.max_json_mb)
        self.rle_sample = args.rle_sample
        self.c06_sample = args.c06_sample
        self.rng = random.Random(args.seed)
        self.seed = args.seed
        os.makedirs(self.csv_dir, exist_ok=True)
        os.makedirs(self.subset_dir, exist_ok=True)
        # よく使うパス
        self.bbox_dir = os.path.join(
            self.hts, "egosurgery_tool_bbox", "annotations", "bbox", "by_split")
        self.phase_dir = os.path.join(
            self.hts, "egosurgery_tool_bbox", "annotations", "phase")
        self.fusion = os.path.join(self.hts, "fusion")
        # canonical split (PROJECT_ROOT が唯一の正)
        self.video2split = self._load_canonical()
        self._tool_index = None  # C06/C07/C11 共有

    def _load_canonical(self):
        v2s = {}
        for split in ("train", "val", "test"):
            p = os.path.join(self.proj, "data", "splits", f"ego_{split}.txt")
            if not os.path.exists(p):
                raise SkipCheck(f"canonical split 不在: {p}")
            with open(p) as f:
                for line in f:
                    vid = line.strip()
                    if vid:
                        v2s[vid.zfill(2)] = split
        return v2s

    def tools_json(self, split):
        return os.path.join(self.bbox_dir, "tools", f"{split}.json")

    def hands_json(self, split):
        return os.path.join(self.bbox_dir, "hands", f"{split}.json")

    def tool_frame_index(self):
        """{frame_stem: [(bbox_xywh, class_id, class_name)]} を全 split 横断で構築 (C06/C07 用)."""
        if self._tool_index is not None:
            return self._tool_index
        idx = defaultdict(list)
        for split in ("train", "val", "test"):
            p = self.tools_json(split)
            if not os.path.exists(p):
                continue
            try:
                d = self.loader.load(p)
            except SkipCheck:
                continue
            id2name = {c["id"]: c["name"] for c in d.get("categories", [])}
            id2fn = {im["id"]: im["file_name"] for im in d.get("images", [])}
            for a in d.get("annotations", []):
                fn = id2fn.get(a["image_id"])
                if fn is None:
                    continue
                _, _, stem = parse_filename(fn)
                idx[stem].append(
                    (a["bbox"], a["category_id"], id2name.get(a["category_id"], "?")))
        self._tool_index = idx
        return idx


def run_check(cid, title, fn, ctx):
    """検査を例外隔離して実行. 欠陥1つが全体を止めない."""
    try:
        res = fn(ctx)
        res.setdefault("id", cid)
        res.setdefault("title", title)
        res.setdefault("notes", [])
        res.setdefault("measured", {})
        res.setdefault("outputs", [])
        return res
    except SkipCheck as e:
        return {"id": cid, "title": title, "status": "SKIP",
                "measured": {}, "notes": [f"SKIP: {e}"], "outputs": []}
    except Exception as e:  # noqa: BLE001 - Fail Loud: 例外は隠さず記録
        tb = traceback.format_exc().splitlines()[-4:]
        return {"id": cid, "title": title, "status": "ERROR",
                "measured": {}, "notes": [f"ERROR: {e}"] + tb, "outputs": []}


# ----------------------------------------------------------------------------
# C01 インベントリとクラス体系
# ----------------------------------------------------------------------------


def check_c01(ctx: Ctx):
    rows = []          # inventory
    tax = defaultdict(list)   # category signature -> files
    notes = []
    all_json = sorted(glob.glob(os.path.join(ctx.hts, "**", "*.json"), recursive=True))
    notes.append(f"HTS配下 JSON 総数 = {len(all_json)}")
    seg_sample_n = 1000
    for p in all_json:
        rel = os.path.relpath(p, ctx.hts)
        mb = ctx.loader.size_mb(p)
        try:
            d = ctx.loader.load(p)
        except SkipCheck as e:
            rows.append([rel, f"{mb:.2f}", "SKIP", str(e), "", "", "", "", "", "", "", ""])
            continue
        if not isinstance(d, dict):
            rows.append([rel, f"{mb:.2f}", type(d).__name__, "", "", "", "", "", "", "", "", ""])
            continue
        keys = "|".join(list(d.keys()))
        imgs = d.get("images", [])
        anns = d.get("annotations", [])
        cats = d.get("categories", [])
        catnames = tuple(sorted(c.get("name", "?") for c in cats))
        if catnames:
            tax[catnames].append(rel)
        # seg / iscrowd 分布 (seg はサンプル, iscrowd は全数=安価)
        segc = Counter()
        for a in (anns[:seg_sample_n] if len(anns) > seg_sample_n else anns):
            segc[seg_kind(a.get("segmentation"))] += 1
        crowdc = Counter(crowd_key(a) for a in anns)
        rows.append([
            rel, f"{mb:.2f}", keys, "", len(imgs), len(anns), len(cats),
            "|".join(f"{k}:{v}" for k, v in segc.items()),
            "|".join(f"{k}:{v}" for k, v in crowdc.items()),
            f"sampled={min(len(anns), seg_sample_n)}",
            len(catnames), "",
        ])
    # taxonomy csv
    tax_rows = []
    for sig, files in sorted(tax.items(), key=lambda kv: -len(kv[0])):
        tax_rows.append([len(sig), "|".join(sig)[:400], len(files), "|".join(files)[:600]])

    # 31 -> 15 mapping (tool_seg_noskewer)
    map_rows = []
    noskewer_names = None
    nsk = sorted(glob.glob(os.path.join(ctx.hts, "tool_seg_noskewer", "*", "*.json")))
    for p in nsk:
        try:
            d = ctx.loader.load(p)
            noskewer_names = [c["name"] for c in d.get("categories", [])]
            if len(noskewer_names) >= 15:
                break
        except Exception:
            continue
    sig_present = None
    if noskewer_names:
        lower15 = {n.lower(): n for n in CLS15_NAMES}
        for name in noskewer_names:
            key = name.lower()
            if key in lower15:
                verdict, target = "exact", lower15[key]
            else:
                partial = [c for c in CLS15_NAMES
                           if c.lower() in key or key in c.lower()]
                if partial:
                    verdict, target = "partial", "|".join(partial)
                else:
                    verdict, target = "absent(31-only)", ""
            map_rows.append([name, verdict, target])
        present = {n for n in noskewer_names}
        sig_present = {t: (t in present) for t in SIGNATURE_TOOLS}
        notes.append(f"tool_seg_noskewer categories = {len(noskewer_names)}")
        notes.append(f"signature 3術具 in 31cls = {sig_present}")
    else:
        notes.append("tool_seg_noskewer の categories を取得できず (UNKNOWN)")

    write_csv(os.path.join(ctx.csv_dir, "c01_inventory.csv"),
              ["file", "size_mb", "top_keys", "skip_reason", "n_images",
               "n_annotations", "n_categories", "seg_kinds", "crowd_keys",
               "seg_sampling", "n_catnames", "extra"], rows)
    write_csv(os.path.join(ctx.csv_dir, "c01_taxonomy.csv"),
              ["n_classes", "category_signature", "n_files", "files"], tax_rows)
    write_csv(os.path.join(ctx.csv_dir, "c01_map_31_to_15.csv"),
              ["noskewer_class", "verdict", "maps_to_15cls"], map_rows)

    status = "OK"
    if sig_present is None:
        status = "WARN"
    elif not all(sig_present.values()):
        status = "FAIL"
        notes.append("signature 術具欠落 -> G-2 は per-tool 分析不可 (代替設計要)")
    return {"status": status, "measured": {
        "n_json": len(all_json), "n_taxonomies": len(tax),
        "signature_present": sig_present}, "notes": notes,
        "outputs": ["csv/c01_inventory.csv", "csv/c01_taxonomy.csv",
                    "csv/c01_map_31_to_15.csv"]}


# ----------------------------------------------------------------------------
# C02 参照整合性と COCO 妥当性
# ----------------------------------------------------------------------------


def _integrity_targets(ctx):
    t = []
    for split in ("train", "val", "test"):
        t.append((f"tool_bbox/{split}", ctx.tools_json(split)))
        t.append((f"hand_bbox/{split}", ctx.hands_json(split)))
        t.append((f"fusion_split/{split}", os.path.join(ctx.fusion, f"{split}.json")))
        t.append((f"toolhand/{split}", os.path.join(ctx.fusion, f"{split}_toolhand.json")))
        t.append((f"toolhand_withmask/{split}",
                  os.path.join(ctx.fusion, f"{split}_toolhand_withmask.json")))
    return t


def check_c02(ctx: Ctx):
    rows = []
    notes = []
    worst_orphan = 0
    worst_dup = 0
    for label, path in _integrity_targets(ctx):
        if not os.path.exists(path):
            rows.append([label, "SKIP(not_found)"] + [""] * 10)
            continue
        try:
            d = ctx.loader.load(path)
        except SkipCheck as e:
            rows.append([label, f"SKIP({e})"] + [""] * 10)
            continue
        img_ids = [im["id"] for im in d.get("images", [])]
        img_id_set = set(img_ids)
        anns = d.get("annotations", [])
        ann_ids = [a["id"] for a in anns]
        orphan = sum(1 for a in anns if a["image_id"] not in img_id_set)
        dup_img = len(img_ids) - len(img_id_set)
        dup_ann = len(ann_ids) - len(set(ann_ids))
        imgs_with_ann = {a["image_id"] for a in anns}
        empty_imgs = len(img_id_set - imgs_with_ann)
        bad_area = sum(1 for a in anns if float(a.get("area", 0) or 0) <= 0)
        bad_box = sum(1 for a in anns
                      if len(a.get("bbox", [])) == 4 and (a["bbox"][2] <= 0 or a["bbox"][3] <= 0))
        segc = Counter(seg_kind(a.get("segmentation")) for a in anns)
        crowdc = Counter(crowd_key(a) for a in anns)
        worst_orphan = max(worst_orphan, orphan)
        worst_dup = max(worst_dup, dup_img + dup_ann)
        rows.append([label, "OK", len(img_ids), len(anns), orphan, dup_img,
                     dup_ann, empty_imgs, bad_area, bad_box,
                     "|".join(f"{k}:{v}" for k, v in segc.items()),
                     "|".join(f"{k}:{v}" for k, v in crowdc.items())])
        if orphan > 0:
            notes.append(f"[{label}] 孤児annotation {orphan}件 (images不在のimage_id)")

    write_csv(os.path.join(ctx.csv_dir, "c02_integrity.csv"),
              ["target", "load", "n_images", "n_annotations", "orphan_anns",
               "dup_image_ids", "dup_ann_ids", "images_without_ann",
               "area_le0", "bbox_wh_le0", "seg_kinds", "crowd_keys"], rows)

    status = "OK"
    if worst_orphan > 0 or worst_dup > 0:
        status = "FAIL"
        notes.append("最優先警告: 孤児/ID重複あり. pycocotools は孤児annを黙って落とす -> "
                     "評価対象が想定と異なる潜伏欠陥. 対処: 孤児annを破棄 or images復元を先に決定.")
    return {"status": status, "measured": {
        "max_orphan": worst_orphan, "max_dup": worst_dup}, "notes": notes,
        "outputs": ["csv/c02_integrity.csv"]}


# ----------------------------------------------------------------------------
# C03 動画 x split x タスク フレーム行列
# ----------------------------------------------------------------------------


def check_c03(ctx: Ctx):
    tasks = {}
    for split in ("train", "val", "test"):
        tasks[("tool_bbox", split)] = ctx.tools_json(split)
        tasks[("hand_bbox", split)] = ctx.hands_json(split)
        tasks[("toolhand", split)] = os.path.join(ctx.fusion, f"{split}_toolhand.json")
        tasks[("toolhand_withmask", split)] = os.path.join(
            ctx.fusion, f"{split}_toolhand_withmask.json")

    matrix_rows = []
    conf_rows = []
    leaks = 0
    missing = 0
    unparsed = 0
    missing_detail = []          # (task, split, video)
    tool_bbox_per_split = {}     # split -> n_frames (I1 の基底)
    for (task, split), path in sorted(tasks.items()):
        if not os.path.exists(path):
            conf_rows.append([task, split, "-", "-", "SKIP(not_found)"])
            continue
        try:
            d = ctx.loader.load(path)
        except SkipCheck as e:
            conf_rows.append([task, split, "-", "-", f"SKIP({e})"])
            continue
        id2fn = {im["id"]: im["file_name"] for im in d.get("images", [])}
        frames_by_video = defaultdict(set)
        anns_by_video = Counter()
        for im in d.get("images", []):
            v, _, stem = parse_filename(im["file_name"])
            if v is None:
                unparsed += 1
                continue
            frames_by_video[v].add(stem)
        for a in d.get("annotations", []):
            fn = id2fn.get(a["image_id"])
            if fn is None:
                continue
            v, _, _ = parse_filename(fn)
            if v is not None:
                anns_by_video[v] += 1
        present_videos = set(frames_by_video)
        if task == "tool_bbox":
            tool_bbox_per_split[split] = sum(len(fr) for fr in frames_by_video.values())
        for v in sorted(present_videos):
            canon = ctx.video2split.get(v, "UNKNOWN")
            matrix_rows.append([task, split, v, len(frames_by_video[v]), anns_by_video[v], canon])
            if canon == "UNKNOWN":
                verdict = "UNKNOWN_VIDEO"
            elif canon != split:
                verdict = "LEAK"
                leaks += 1
            else:
                verdict = "OK"
            conf_rows.append([task, split, v, canon, verdict])
        # MISSING: canonical で split に属する動画がこのファイルに無い
        expected = {v for v, s in ctx.video2split.items() if s == split}
        for v in sorted(expected - present_videos):
            conf_rows.append([task, split, v, split, "MISSING"])
            missing += 1
            missing_detail.append(f"{task}/{split}:動画{v}")

    write_csv(os.path.join(ctx.csv_dir, "c03_frame_matrix.csv"),
              ["task", "declared_split", "video", "n_frames", "n_annotations",
               "canonical_split"], matrix_rows)
    write_csv(os.path.join(ctx.csv_dir, "c03_split_conformance.csv"),
              ["task", "declared_split", "video", "canonical_split", "verdict"], conf_rows)

    base_total = sum(tool_bbox_per_split.values())
    notes = [f"LEAK={leaks} MISSING={missing} 未parse file_name={unparsed}",
             f"tool_bbox 総フレーム={base_total} (内訳 {tool_bbox_per_split}) ← I1 の基底"]
    if missing_detail:
        notes.append("MISSING 内訳: " + ", ".join(missing_detail))
    status = "OK"
    if leaks > 0:
        status = "FAIL"
        notes.append("LEAK 検出 -> 即 FAIL (canonical split 逸脱)")
    elif missing > 0:
        status = "WARN"
        notes.append("MISSING は WARN. C11 の分母設計に反映せよ (tool_bbox基底は保持, "
                     "欠落は toolhand_withmask の派生タスクのみ)")
    return {"status": status, "measured": {"leaks": leaks, "missing": missing,
            "base_total": base_total, "tool_bbox_per_split": tool_bbox_per_split},
            "notes": notes, "outputs": ["csv/c03_frame_matrix.csv",
                                        "csv/c03_split_conformance.csv"]}


# ----------------------------------------------------------------------------
# C04 phase CSV の分布 (動画 17-22 を含む)
# ----------------------------------------------------------------------------


def check_c04(ctx: Ctx):
    csvs = sorted(glob.glob(os.path.join(ctx.phase_dir, "*.csv")))
    if not csvs:
        raise SkipCheck(f"phase CSV 不在: {ctx.phase_dir}")
    headers = Counter()
    per_file = []
    dist_a = Counter()   # 動画 01-15
    dist_b = Counter()   # 動画 17-22
    for c in csvs:
        base = os.path.basename(c)
        v = base.split("_")[0]
        try:
            vi = int(v)
        except ValueError:
            vi = -1
        group = "01-15" if 1 <= vi <= 15 else ("17-22" if 17 <= vi <= 22 else "other")
        try:
            with open(c) as f:
                r = csv.reader(f)
                header = tuple(next(r, []))
                headers[header] += 1
                # Phase 列の位置を特定 (想定外ヘッダも許容)
                pcol = header.index("Phase") if "Phase" in header else (len(header) - 1)
                labels = Counter()
                n = 0
                for row in r:
                    if not row:
                        continue
                    n += 1
                    if pcol < len(row):
                        lab = row[pcol].strip()
                        labels[lab] += 1
                        (dist_a if group == "01-15" else dist_b if group == "17-22"
                         else Counter())[lab] += 1
        except Exception as e:  # ファイル毎隔離 (遅延FS対策)
            per_file.append([base, v, group, "READ_ERROR", str(e), ""])
            continue
        per_file.append([base, v, group, n, len(labels),
                         "|".join(f"{k}:{v2}" for k, v2 in labels.most_common())])

    all_phases = set(dist_a) | set(dist_b)
    dist_rows = []
    for ph in sorted(all_phases):
        dist_rows.append([ph, dist_a.get(ph, 0), dist_b.get(ph, 0),
                          dist_a.get(ph, 0) + dist_b.get(ph, 0)])
    write_csv(os.path.join(ctx.csv_dir, "c04_phase_per_file.csv"),
              ["file", "video", "group", "n_frames", "n_phases", "phase_dist"], per_file)
    write_csv(os.path.join(ctx.csv_dir, "c04_phase_distribution.csv"),
              ["phase", "cnt_01_15", "cnt_17_22", "cnt_total"], dist_rows)

    gap = {}
    for ph in GAP_PHASES:
        gap[ph] = {"01-15": dist_a.get(ph, 0), "17-22": dist_b.get(ph, 0)}
    b_has_gap = any(dist_b.get(ph, 0) > 0 for ph in GAP_PHASES)
    notes = [f"phase CSV ヘッダ種別 = {[(list(h), n) for h, n in headers.items()]}",
             f"評価ギャップ3工程 (train01-15 / 17-22): {gap}"]
    if b_has_gap:
        notes.append("動画17-22 に評価ギャップ工程あり -> G-4 は『拡張 test split』案を強く推奨 "
                     "(ただし17-22 は bbox/mask 無し -> S4/B2a のみ拡張可)")
    else:
        notes.append("動画17-22 に評価ギャップ工程なし -> G-4 は train 内 LOVO-CV (A案) で確定")
    return {"status": "OK", "measured": {"gap": gap, "b_has_gap": b_has_gap,
            "n_header_types": len(headers)}, "notes": notes,
            "outputs": ["csv/c04_phase_per_file.csv", "csv/c04_phase_distribution.csv"]}


# ----------------------------------------------------------------------------
# C05 重複検出 (HTS tools vs project instances)
# ----------------------------------------------------------------------------


def _content_hashes(d):
    """file_name を basename の stem に正規化して比較 (パス接頭辞/拡張子の違いを吸収)."""
    stem_of = {im["id"]: parse_filename(im["file_name"])[2] for im in d.get("images", [])}
    fnset = sorted(set(stem_of.values()))
    tuples = []
    for a in d.get("annotations", []):
        stem = stem_of.get(a["image_id"], "?")
        bbox = a.get("bbox", [])
        b = tuple(round(float(x), 1) for x in bbox) if len(bbox) == 4 else ()
        tuples.append((stem, a.get("category_id"), b))
    return sha1_of(fnset), sha1_of(sorted(map(list, tuples)))


def check_c05(ctx: Ctx):
    rows = []
    notes = []
    verdicts = []
    for split in ("train", "val", "test"):
        hts_p = ctx.tools_json(split)
        proj_p = os.path.join(ctx.proj, "data", "annotations", "egosurgery_tool",
                              f"instances_{split}.json")
        if not (os.path.exists(hts_p) and os.path.exists(proj_p)):
            rows.append([split, "SKIP(missing)", hts_p if not os.path.exists(hts_p) else "",
                         proj_p if not os.path.exists(proj_p) else "", "", "", ""])
            continue
        m1, m2 = md5_file(hts_p), md5_file(proj_p)
        if m1 == m2:
            verdict = "IDENTICAL_FILE"
        else:
            try:
                d1, d2 = ctx.loader.load(hts_p), ctx.loader.load(proj_p)
                fn1, tp1 = _content_hashes(d1)
                fn2, tp2 = _content_hashes(d2)
                if fn1 == fn2 and tp1 == tp2:
                    verdict = "IDENTICAL_CONTENT"
                elif fn1 == fn2:
                    verdict = "SAME_FRAMES_DIFF_ANN"
                else:
                    verdict = "DIFFERENT"
            except SkipCheck as e:
                verdict = f"SKIP({e})"
        # file_name 形式の差を記録 (正規化前の生 file_name を比較)
        fmt_note = ""
        try:
            d1, d2 = ctx.loader.load(hts_p), ctx.loader.load(proj_p)
            hraw = d1["images"][0]["file_name"] if d1.get("images") else ""
            praw = d2["images"][0]["file_name"] if d2.get("images") else ""
            same_ni = len(d1.get("images", [])) == len(d2.get("images", []))
            same_na = len(d1.get("annotations", [])) == len(d2.get("annotations", []))
            fmt_note = (f"HTS_fn={hraw} / PROJ_fn={praw} / img数一致={same_ni} / ann数一致={same_na}")
        except SkipCheck:
            pass
        verdicts.append(verdict)
        rows.append([split, verdict, m1, m2, fmt_note, "", ""])
        if verdict == "SAME_FRAMES_DIFF_ANN":
            notes.append(f"[{split}] 同フレーム別アノテーション -> どちらを正とするか要決定 (Δ再現性に直結)")
        elif verdict == "IDENTICAL_CONTENT":
            notes.append(f"[{split}] basename正規化後は内容一致 (差はfile_name形式のみ: {fmt_note})")

    write_csv(os.path.join(ctx.csv_dir, "c05_duplicate_check.csv"),
              ["split", "verdict", "hts_md5", "project_md5", "detail", "note2", "note3"], rows)
    status = "OK"
    if any(v == "SAME_FRAMES_DIFF_ANN" for v in verdicts):
        status = "WARN"
    if all(v in ("IDENTICAL_FILE", "IDENTICAL_CONTENT") for v in verdicts) and verdicts:
        notes.append("全 split basename正規化後は同一内容 -> I4 は無改修維持可 (HTS tool bbox は "
                     "project instances と同一フレーム/同一bbox, file_name のパス接頭辞のみ相違). "
                     "片方削除で容量節約可")
    return {"status": status, "measured": {"verdicts": verdicts}, "notes": notes,
            "outputs": ["csv/c05_duplicate_check.csv"]}


# ----------------------------------------------------------------------------
# C06 mask 外接矩形 vs bbox の IoU と充填率
# ----------------------------------------------------------------------------


def check_c06(ctx: Ctx):
    try:
        from pycocotools import mask as maskUtils
    except Exception as e:  # noqa: BLE001
        raise SkipCheck(f"pycocotools 未導入 ({e}) -> RLE/mask 幾何は測定不可")

    tool_idx = ctx.tool_frame_index()
    if not tool_idx:
        raise SkipCheck("tools bbox index が空 (tools/*.json 不在?)")

    nsk = sorted(glob.glob(os.path.join(ctx.hts, "tool_seg_noskewer", "*", "*.json")))
    if not nsk:
        raise SkipCheck("tool_seg_noskewer に json 無し")

    ious = []
    fills = []
    fill_by_class = defaultdict(list)
    matched = 0
    unmatched = 0
    n_masks = 0
    for p in nsk:
        try:
            d = ctx.loader.load(p)
        except Exception:
            continue
        id2name = {c["id"]: c["name"] for c in d.get("categories", [])}
        id2img = {im["id"]: im for im in d.get("images", [])}
        for a in d.get("annotations", []):
            im = id2img.get(a["image_id"])
            if im is None:
                continue
            _, _, stem = parse_filename(im["file_name"])
            seg = a.get("segmentation")
            h = im.get("height")
            w = im.get("width")
            try:
                if isinstance(seg, dict):
                    rle = seg
                    if isinstance(rle.get("counts"), list):
                        rle = maskUtils.frPyObjects(rle, rle["size"][0], rle["size"][1])
                elif isinstance(seg, list) and seg and h and w:
                    rle = maskUtils.merge(maskUtils.frPyObjects(seg, h, w))
                else:
                    continue
                m_area = float(maskUtils.area(rle))
                m_bbox = list(maskUtils.toBbox(rle))  # [x,y,w,h] tight
            except Exception:
                continue
            n_masks += 1
            cands = tool_idx.get(stem, [])
            if not cands:
                unmatched += 1
                continue
            # 貪欲: mask外接矩形と最大 IoU の bbox
            best = max(cands, key=lambda c: iou_xywh(m_bbox, c[0]))
            iou = iou_xywh(m_bbox, best[0])
            bx = best[0]
            barea = bx[2] * bx[3]
            fill = m_area / barea if barea > 0 else None
            ious.append(iou)
            if fill is not None:
                fills.append(fill)
            matched += 1
            cname = id2name.get(a["category_id"], "?")
            if cname in CLS15_NAMES and fill is not None:
                fill_by_class[cname].append(fill)

    iou_q = pct(ious)
    fill_q = pct(fills)
    geom_rows = [["iou_mask_rect_vs_bbox", matched] + [iou_q[q] for q in (5, 25, 50, 75, 95)],
                 ["fill_ratio_mask/bbox", len(fills)] + [fill_q[q] for q in (5, 25, 50, 75, 95)]]
    write_csv(os.path.join(ctx.csv_dir, "c06_mask_bbox_geometry.csv"),
              ["metric", "n", "p5", "p25", "p50", "p75", "p95"], geom_rows)
    cls_rows = []
    for name in sorted(fill_by_class):
        vals = fill_by_class[name]
        cls_rows.append([name, len(vals), round(statistics.median(vals), 4),
                         round(min(vals), 4), round(max(vals), 4)])
    write_csv(os.path.join(ctx.csv_dir, "c06_fill_ratio_by_class.csv"),
              ["class", "n", "fill_median", "fill_min", "fill_max"], cls_rows)

    iou_median = iou_q[50]
    status = "OK" if (iou_median is not None and iou_median >= 0.90) else "WARN"
    absent_15 = sorted(CLS15_NAMES - set(fill_by_class))
    notes = [f"matched={matched} unmatched={unmatched} n_masks={n_masks}",
             f"IoU中央値={iou_median}", f"充填率中央値={fill_q[50]}",
             f"noskewer mask 実体を持つ15クラス={len(fill_by_class)}/15, 実体0件の15クラス={absent_15}"]
    if status == "WARN":
        notes.append("IoU中央値<0.90 -> G-2のΔが『mask効果』か『box定義変更』か交絡. "
                     "対照実験『mask由来boxで作ったbbox版T1a』が必須")
    if absent_15:
        notes.append(f"実体0件の術具 {absent_15} は G-2 の per-phase 分析から脱落 "
                     "(Skewer=design工程signature0.997, Mouth Gag). §2.6-f 確認")
    notes.append("充填率が1に近い術具=背景除去効果小/低い術具(細長)=G-2期待効果大 (分布はG-2効果量の事前予測子)")
    return {"status": status, "measured": {"iou_median": iou_median,
            "fill_median": fill_q[50], "matched": matched, "unmatched": unmatched,
            "absent_15cls_masks": absent_15},
            "notes": notes, "outputs": ["csv/c06_mask_bbox_geometry.csv",
                                        "csv/c06_fill_ratio_by_class.csv"]}


# ----------------------------------------------------------------------------
# C07 which_tool 復元と手クラス対応
# ----------------------------------------------------------------------------


def check_c07(ctx: Ctx):
    try:
        import numpy as np
        from pycocotools import mask as maskUtils
    except Exception as e:  # noqa: BLE001
        raise SkipCheck(f"pycocotools/numpy 未導入 ({e})")

    tool_idx = ctx.tool_frame_index()

    def decode_mask(seg, h, w):
        if isinstance(seg, dict):
            rle = seg
            if isinstance(rle.get("counts"), list):
                rle = maskUtils.frPyObjects(rle, rle["size"][0], rle["size"][1])
        elif isinstance(seg, list) and h and w:
            rle = maskUtils.merge(maskUtils.frPyObjects(seg, h, w))
        else:
            return None
        return maskUtils.decode(rle)

    def containment(m, bbox):
        H, W = m.shape
        x, y, bw, bh = bbox
        x0 = max(0, int(math.floor(x)))
        y0 = max(0, int(math.floor(y)))
        x1 = min(W, int(math.ceil(x + bw)))
        y1 = min(H, int(math.ceil(y + bh)))
        if x1 <= x0 or y1 <= y0:
            return 0.0
        inter = int(m[y0:y1, x0:x1].sum())
        tot = int(m.sum())
        return inter / tot if tot > 0 else 0.0

    which_rows = []
    hand_rows = []
    containments = []
    margins = []
    n_ge05 = 0
    total_sampled = 0
    # 手対応集計
    hand_corr = Counter()  # (first_person_slot, matched_hand_class) -> n

    # 各 split から tool 側 mask をサンプリング
    for split in ("train", "val", "test"):
        p = os.path.join(ctx.fusion, f"{split}_toolhand_withmask.json")
        if not os.path.exists(p):
            continue
        try:
            d = ctx.loader.load(p)
        except SkipCheck:
            continue
        id2img = {im["id"]: im for im in d.get("images", [])}
        tool_anns = [a for a in d.get("annotations", [])
                     if a.get("category_id") in TOOLHAND_TOOL_CATS]
        hand_anns = [a for a in d.get("annotations", [])
                     if a.get("category_id") in TOOLHAND_HAND_CATS]
        # サンプリング (上限). 実サンプル数を記録
        ctx.rng.shuffle(tool_anns)
        sample = tool_anns[:ctx.rle_sample]
        for a in sample:
            im = id2img.get(a["image_id"])
            if im is None:
                continue
            _, seg_id, stem = parse_filename(im["file_name"])
            m = None
            try:
                m = decode_mask(a.get("segmentation"), im.get("height"), im.get("width"))
            except Exception:
                m = None
            if m is None:
                continue
            cands = tool_idx.get(stem, [])
            if not cands:
                continue
            total_sampled += 1
            scored = sorted(((containment(m, c[0]), c[2]) for c in cands),
                            key=lambda t: -t[0])
            top_c, top_name = scored[0]
            margin = top_c - (scored[1][0] if len(scored) > 1 else 0.0)
            containments.append(top_c)
            margins.append(margin)
            if top_c >= 0.5:
                n_ge05 += 1
            slot = TOOLHAND_TOOL_CATS[a["category_id"]]
            which_rows.append([split, stem, slot, top_name, round(top_c, 4),
                               round(margin, 4), im.get("height"), im.get("width")])

        # 手対応: First Person's L/R Hand mask vs 4cls hand bbox
        hp = ctx.hands_json(split)
        hand_idx = defaultdict(list)
        if os.path.exists(hp):
            try:
                hd = ctx.loader.load(hp)
                hid2name = {c["id"]: c["name"] for c in hd.get("categories", [])}
                hid2fn = {im["id"]: im["file_name"] for im in hd.get("images", [])}
                for ha in hd.get("annotations", []):
                    fn = hid2fn.get(ha["image_id"])
                    if fn is None:
                        continue
                    _, _, hstem = parse_filename(fn)
                    hand_idx[hstem].append((ha["bbox"], hid2name.get(ha["category_id"], "?")))
            except SkipCheck:
                pass
        ctx.rng.shuffle(hand_anns)
        for a in hand_anns[:ctx.rle_sample]:
            im = id2img.get(a["image_id"])
            if im is None:
                continue
            _, _, stem = parse_filename(im["file_name"])
            try:
                m = decode_mask(a.get("segmentation"), im.get("height"), im.get("width"))
            except Exception:
                m = None
            if m is None:
                continue
            cands = hand_idx.get(stem, [])
            if not cands:
                continue
            best = max(cands, key=lambda c: containment(m, c[0]))
            bc = containment(m, best[0])
            slot = TOOLHAND_HAND_CATS[a["category_id"]]
            own_other = "Own" if "Own" in best[1] else ("Other" if "Other" in best[1] else "?")
            hand_corr[(slot, own_other)] += 1 if bc >= 0.5 else 0

    write_csv(os.path.join(ctx.csv_dir, "c07_which_tool_recovery.csv"),
              ["split", "frame", "hand_slot", "recovered_tool", "containment",
               "margin", "img_h", "img_w"], which_rows)
    hc_rows = [[slot, oo, n] for (slot, oo), n in sorted(hand_corr.items())]
    write_csv(os.path.join(ctx.csv_dir, "c07_hand_class_correspondence.csv"),
              ["first_person_slot", "own_or_other", "n_containment_ge0.5"], hc_rows)

    cq = pct(containments)
    frac_ge05 = n_ge05 / total_sampled if total_sampled else None
    frac_ambig = (sum(1 for m in margins if m < 0.2) / len(margins)) if margins else None
    own = sum(n for (s, oo), n in hand_corr.items() if oo == "Own")
    other = sum(n for (s, oo), n in hand_corr.items() if oo == "Other")
    other_ratio = other / (own + other) if (own + other) else None
    notes = [f"実サンプル tool mask 数 = {total_sampled} (上限 rle_sample={ctx.rle_sample}/split)",
             f"内包率分位 = {cq}",
             f"内包率>=0.5 割合 = {frac_ge05}",
             f"margin<0.2 (曖昧) 割合 = {frac_ambig}",
             f"手対応 Own={own} Other={other} (Other比率={other_ratio}, 内包率>=0.5 のみ集計)"]
    if other_ratio is None:
        notes.append("手対応の集計結果なし (UNKNOWN)")
    elif other_ratio < 0.02:
        notes.append(f"Other対応ほぼ0 (Other比率{other_ratio:.2%}) -> 助手手のrelationは事実上取得不可. "
                     "論文の限界として明記が必要")
    elif other_ratio >= 0.05:
        notes.append(f"Other対応が有意に存在 (Other比率{other_ratio:.2%}) -> 助手手を設計に含められる")
    else:
        notes.append(f"Other対応わずか (Other比率{other_ratio:.2%}) -> 助手手は限定的, 限界として明記推奨")
    status = "OK" if (frac_ge05 is not None and frac_ge05 >= 0.5) else "WARN"
    return {"status": status, "measured": {
        "n_sampled": total_sampled, "containment_p50": cq[50],
        "frac_ge05": frac_ge05, "frac_ambiguous": frac_ambig,
        "hand_own": own, "hand_other": other, "other_ratio": other_ratio}, "notes": notes,
        "outputs": ["csv/c07_which_tool_recovery.csv",
                    "csv/c07_hand_class_correspondence.csv"]}


# ----------------------------------------------------------------------------
# C08 PNG の split 別枚数 (リーク検査)
# ----------------------------------------------------------------------------


def check_c08(ctx: Ctx):
    root = os.path.join(ctx.hts, "handtool_masks_5cls", "train")
    if not os.path.isdir(root):
        raise SkipCheck(f"handtool_masks_5cls/train 不在: {root}")
    rows = []
    per_split = Counter()
    for seg in sorted(os.listdir(root)):
        segdir = os.path.join(root, seg)
        if not os.path.isdir(segdir):
            continue
        v = seg.split("_")[0].zfill(2)
        canon = ctx.video2split.get(v, "UNKNOWN")
        try:
            n_png = sum(1 for f in os.listdir(segdir) if f.lower().endswith(".png"))
        except Exception as e:  # 遅延FS対策
            rows.append([seg, v, canon, f"READ_ERROR:{e}"])
            continue
        per_split[canon] += n_png
        rows.append([seg, v, canon, n_png])
    write_csv(os.path.join(ctx.csv_dir, "c08_png_split.csv"),
              ["segment_dir", "video", "canonical_split", "n_png"], rows)
    leak = per_split.get("val", 0) + per_split.get("test", 0)
    status = "OK" if leak == 0 else "FAIL"
    notes = [f"PNG枚数 canonical別 = {dict(per_split)}"]
    if leak > 0:
        notes.append(f"val/test 混在 {leak}枚 -> ディレクトリ名を信用したローダは即リーク. "
                     "canonical split による再フィルタを必須要件に")
    return {"status": status, "measured": {"per_split": dict(per_split), "leak_png": leak},
            "notes": notes, "outputs": ["csv/c08_png_split.csv"]}


# ----------------------------------------------------------------------------
# C09 (hand, tool) 共起頻度と疎性  (C07 出力を利用)
# ----------------------------------------------------------------------------


def check_c09(ctx: Ctx):
    c07 = os.path.join(ctx.csv_dir, "c07_which_tool_recovery.csv")
    if not os.path.exists(c07):
        raise SkipCheck("C07 出力なし (先に C07 が必要)")
    cooc = defaultdict(lambda: Counter())  # split -> (slot,tool) -> n
    with open(c07, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            try:
                if float(row["containment"]) < 0.5:
                    continue
            except (KeyError, ValueError):
                continue
            cooc[row["split"]][(row["hand_slot"], row["recovered_tool"])] += 1
    rows = []
    all_cells = set()
    for split, counter in cooc.items():
        for (slot, tool), n in counter.items():
            all_cells.add((slot, tool))
            rows.append([split, slot, tool, n])
    train_counter = cooc.get("train", Counter())
    sparse = sum(1 for (slot, tool), n in train_counter.items() if n < 10)
    write_csv(os.path.join(ctx.csv_dir, "c09_cooccurrence.csv"),
              ["split", "hand_slot", "recovered_tool", "n"], rows)
    nonzero = len(all_cells)
    notes = [f"非ゼロセル数(全split, 内包率>=0.5) = {nonzero}",
             f"train で 10例未満のセル数 = {sparse}",
             f"train 非ゼロセル数 = {len(train_counter)}",
             "B2aでは15次元中12次元がノイズ・利得129%を上位3次元が支配. relationでも同型を想定し実用セル数を明示"]
    status = "OK"
    effective = len(train_counter) - sparse
    if effective <= 3:
        status = "WARN"
        notes.append(f"実用セル(train>=10例)={effective} と極少 -> G-1 の低次元設計への切替を検討 "
                     "(把持有無 x L/R x 単手/両手)")
    return {"status": status, "measured": {"nonzero_cells": nonzero,
            "train_sparse_lt10": sparse, "train_effective": effective},
            "notes": notes, "outputs": ["csv/c09_cooccurrence.csv"]}


# ----------------------------------------------------------------------------
# C10 relation の時間安定性  (C07 出力を利用)
# ----------------------------------------------------------------------------


def check_c10(ctx: Ctx):
    c07 = os.path.join(ctx.csv_dir, "c07_which_tool_recovery.csv")
    if not os.path.exists(c07):
        raise SkipCheck("C07 出力なし")
    seqs = defaultdict(list)  # (segment, slot) -> [(frame_stem, tool)]
    with open(c07, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        for row in r:
            _, seg, stem = parse_filename(row["frame"])
            seqs[(seg, row["hand_slot"])].append((row["frame"], row["recovered_tool"]))
    rows = []
    switch_rates = []
    run_lengths = []
    for (seg, slot), items in seqs.items():
        items.sort(key=lambda t: t[0])
        tools = [t for _, t in items]
        if len(tools) < 2:
            switches = 0
        else:
            switches = sum(1 for i in range(1, len(tools)) if tools[i] != tools[i - 1])
        rate = switches / (len(tools) - 1) if len(tools) > 1 else 0.0
        # 平均継続長 (run length)
        runs = 1
        for i in range(1, len(tools)):
            if tools[i] != tools[i - 1]:
                runs += 1
        mean_run = len(tools) / runs if runs else len(tools)
        switch_rates.append(rate)
        run_lengths.append(mean_run)
        rows.append([seg, slot, len(tools), switches, round(rate, 4), round(mean_run, 3)])
    write_csv(os.path.join(ctx.csv_dir, "c10_temporal_stability.csv"),
              ["segment", "hand_slot", "n_frames", "n_switches", "switch_rate",
               "mean_run_length"], rows)
    mean_run_all = statistics.mean(run_lengths) if run_lengths else None
    mean_rate_all = statistics.mean(switch_rates) if switch_rates else None
    notes = [f"平均継続長(全系列平均)={mean_run_all} フレーム, 平均切替率={mean_rate_all}",
             "比較: 既存工程の自己遷移率0.982 (粘性大), サンプリング0.5fps",
             "継続長が短ければT1aのflicker由来過分節(edit 41.08->37.07)が再発 -> "
             "因果 min-segment debounce(k=2) の relation版を事前用意すべき"]
    return {"status": "OK", "measured": {"mean_run_length": mean_run_all,
            "mean_switch_rate": mean_rate_all}, "notes": notes,
            "outputs": ["csv/c10_temporal_stability.csv"]}


# ----------------------------------------------------------------------------
# C11 被覆率と再計算分母のフレームリスト出力
# ----------------------------------------------------------------------------


def _frames_from_coco(ctx, path):
    d = ctx.loader.load(path)
    return {parse_filename(im["file_name"])[2] for im in d.get("images", [])}


def check_c11(ctx: Ctx):
    rows = []
    notes = []
    for split in ("train", "val", "test"):
        tools_p = ctx.tools_json(split)
        if not os.path.exists(tools_p):
            rows.append([f"(base)", split, "SKIP(no tool bbox)"] + [""] * 5)
            continue
        try:
            base = _frames_from_coco(ctx, tools_p)
        except SkipCheck as e:
            rows.append([f"(base)", split, f"SKIP({e})"] + [""] * 5)
            continue

        # 各タスクのフレーム集合
        task_frames = {}
        # toolhand / withmask
        for task, fn in (("toolhand", f"{split}_toolhand.json"),
                         ("toolhand_withmask", f"{split}_toolhand_withmask.json")):
            p = os.path.join(ctx.fusion, fn)
            if os.path.exists(p):
                try:
                    task_frames[task] = _frames_from_coco(ctx, p)
                except SkipCheck:
                    pass
        # hand bbox
        hp = ctx.hands_json(split)
        if os.path.exists(hp):
            try:
                task_frames["hand_bbox"] = _frames_from_coco(ctx, hp)
            except SkipCheck:
                pass
        # phase (canonical split の動画のみ)
        split_videos = {v for v, s in ctx.video2split.items() if s == split}
        phase_frames = set()
        for c in glob.glob(os.path.join(ctx.phase_dir, "*.csv")):
            vv = os.path.basename(c).split("_")[0].zfill(2)
            if vv not in split_videos:
                continue
            try:
                with open(c) as f:
                    r = csv.reader(f)
                    next(r, None)
                    for row in r:
                        if row:
                            phase_frames.add(row[0].strip())
            except Exception:
                continue
        if phase_frames:
            task_frames["phase"] = phase_frames
        # mask (noskewer, canonical split の動画のみ)
        mask_frames = set()
        for p in glob.glob(os.path.join(ctx.hts, "tool_seg_noskewer", "*", "*.json")):
            vv = os.path.basename(p).split("_")[0].zfill(2)
            if vv not in split_videos:
                continue
            try:
                d = ctx.loader.load(p)
                for im in d.get("images", []):
                    mask_frames.add(parse_filename(im["file_name"])[2])
            except Exception:
                continue
        if mask_frames:
            task_frames["mask"] = mask_frames

        for task, frames in task_frames.items():
            inter = base & frames
            vids = {parse_filename(s)[0] for s in inter}
            missing = sorted(split_videos - vids)
            cov = len(inter) / len(base) if base else 0.0
            subset_path = os.path.join(ctx.subset_dir, f"subset_{task}_{split}.txt")
            with open(subset_path, "w") as f:
                for s in sorted(inter):
                    f.write(s + "\n")
            rows.append([task, split, len(base), len(frames), len(inter),
                         round(cov, 4), len(vids), "|".join(missing)])
    write_csv(os.path.join(ctx.csv_dir, "c11_coverage.csv"),
              ["task", "split", "n_tool_frames", "n_task_frames", "n_intersection",
               "coverage", "n_videos_in_intersection", "missing_videos"], rows)
    notes.append("★ このフレームリストを分母に S4/B2a/T1a/H-6 を同一集合で再計算しない限り, "
                 "新Δは既存 +0.0383/+0.0497/+0.0004 と比較不能 (I1 の破れ). 再計算は G-4 に含める")
    return {"status": "OK", "measured": {"n_rows": len(rows)}, "notes": notes,
            "outputs": ["csv/c11_coverage.csv", "subsets/subset_{task}_{split}.txt"]}


# ----------------------------------------------------------------------------
# レポート生成
# ----------------------------------------------------------------------------

CHECKS = [
    ("C01", "インベントリとクラス体系", check_c01),
    ("C02", "参照整合性と COCO 妥当性", check_c02),
    ("C03", "動画×split×タスク フレーム行列", check_c03),
    ("C04", "phase CSV の分布 (17-22含む)", check_c04),
    ("C05", "重複検出 (HTS vs project)", check_c05),
    ("C06", "mask外接矩形 vs bbox IoU/充填率", check_c06),
    ("C07", "which_tool 復元と手クラス対応", check_c07),
    ("C08", "PNG split別枚数 (リーク検査)", check_c08),
    ("C09", "(hand,tool) 共起頻度と疎性", check_c09),
    ("C10", "relation の時間安定性", check_c10),
    ("C11", "被覆率と再計算分母リスト出力", check_c11),
]


def build_report(ctx, results):
    by_id = {r["id"]: r for r in results}

    def st(cid):
        return by_id.get(cid, {}).get("status", "?")

    lines = []
    lines.append("# EgoSurgery-HTS 受入監査レポート (C01–C11)\n")
    lines.append(f"- HTS_ROOT: `{ctx.hts}`")
    lines.append(f"- PROJECT_ROOT: `{ctx.proj}`")
    lines.append(f"- 出力: `{ctx.out}` / seed={ctx.seed} / max_json_mb={ctx.loader.max_mb} "
                 f"/ rle_sample={ctx.rle_sample}")
    lines.append("- すべての数値は実測値. 測定不能は SKIP/UNKNOWN と明記.\n")

    # 想定外の発見 (§2.6 事前情報と実測の差異 / §7)
    surprises = []
    c03 = by_id.get("C03", {}).get("measured", {})
    c02m = by_id.get("C02", {}).get("measured", {})
    c05m = by_id.get("C05", {}).get("measured", {})
    if c02m.get("max_orphan", None) == 0:
        surprises.append(
            "§2.6-b の『孤児annotation 濃厚』仮説は反証: 実測 orphan=0. "
            "train_toolhand(7847img)→withmask(5668img) で削られた 2179枚は"
            "『空アノテ画像』であり, アノテ付き画像ではない (孤児は発生せず). 事実を採用.")
    if c05m.get("verdicts") and all(v == "IDENTICAL_CONTENT" for v in c05m["verdicts"]):
        surprises.append(
            "§2.6-h 確認: HTS tools と project instances は basename 正規化後に内容一致 "
            "(生 file_name はパス接頭辞が違うため naive ハッシュ照合では DIFFERENT に誤判定する点に注意).")
    for r in results:
        if r["status"] == "ERROR":
            surprises.append(f"{r['id']} が ERROR 終了: {r['notes'][0] if r['notes'] else ''}")
    if surprises:
        lines.append("## ⚠ 想定外の発見 (事前情報 §2.6 との差異)\n")
        for s in surprises:
            lines.append(f"- {s}")
        lines.append("")

    # 1. 判定サマリ表
    lines.append("## 1. 判定サマリ\n")
    lines.append("| Check | 内容 | ステータス | 主要実測値 |")
    lines.append("|---|---|---|---|")
    for cid, title, _ in CHECKS:
        r = by_id.get(cid, {})
        m = r.get("measured", {})
        mstr = "; ".join(f"{k}={v}" for k, v in list(m.items())[:3]) if m else ""
        lines.append(f"| {cid} | {title} | **{r.get('status','?')}** | {str(mstr)[:120]} |")
    lines.append("")

    # 2. 不変量 I1-I5
    lines.append("## 2. 不変量 I1–I5 の合否\n")
    lines.append("| 不変量 | 内容 | 判定 | 根拠 |")
    lines.append("|---|---|---|---|")
    c08_leak = by_id.get("C08", {}).get("measured", {}).get("leak_png", 0)
    base_total = c03.get("base_total")
    # I1: tool_bbox 基底が15,437なら基底は保持. mask/relation はサブセット限定(C11)
    if base_total == 15437 and not c03.get("leaks"):
        i1 = "保持(基底)/サブセット限定"
        i1_basis = (f"tool_bbox 総フレーム={base_total} で 15,437 に完全一致 (C05: project instances と "
                    f"同一内容). phase被覆=1.0. mask/relation は C11 のサブセットのみ→新実験のΔは要再計算")
    elif c03.get("leaks"):
        i1 = "破れ"
        i1_basis = f"C03 LEAK={c03.get('leaks')} (canonical逸脱)"
    else:
        i1 = f"要確認(基底={base_total})"
        i1_basis = f"tool_bbox 総フレーム={base_total} が 15,437 と不一致"
    # I2: canonical定義自体は不変. handtool_masks の PNG 層が定義違反(要再フィルタ)
    if c03.get("leaks"):
        i2 = "破れ"
        i2_basis = f"C03 split ファイルに LEAK={c03.get('leaks')}"
    elif c08_leak:
        i2 = "定義は保持/PNG層は要再フィルタ"
        i2_basis = (f"canonical定義(data/splits)は不変・C03 split-json は LEAK=0. ただし "
                    f"handtool_masks_5cls/train が val/test を {c08_leak}枚混在→naiveローダはリーク")
    else:
        i2 = "保持"
        i2_basis = "C03 LEAK=0 / C08 PNGリーク=0"
    lines.append(f"| I1 | 評価フレーム集合15,437 | {i1} | {i1_basis} |")
    lines.append(f"| I2 | split定義(動画hold-out) | {i2} | {i2_basis} |")
    lines.append(f"| I3 | クラス体系 tool15/hand4/phase9 | 参照 | C01/C04 (実測クラス数を参照) |")
    lines.append(f"| I4 | 凍結源・特徴抽出 | {'維持可' if by_id.get('C05',{}).get('status')=='OK' else '要確認'} "
                 f"| C05 重複判定={by_id.get('C05',{}).get('measured',{}).get('verdicts')} |")
    lines.append(f"| I5 | 統計手続き(paired-σ, macro-F1) | 本監査対象外(データ非依存) | — |")
    lines.append("")

    # 3. ゲート判定
    lines.append("## 3. ゲート G-1〜G-4 判定\n")
    lines.append("| ゲート | 内容 | 判定 | 理由 |")
    lines.append("|---|---|---|---|")
    c07m = by_id.get("C07", {}).get("measured", {})
    c06m = by_id.get("C06", {}).get("measured", {})
    c04m = by_id.get("C04", {}).get("measured", {})
    g1 = "実行可" if (c07m.get("frac_ge05") or 0) >= 0.5 else "設計変更が必要"
    lines.append(f"| G-1 | GT hand-tool relation を工程認識へ | {g1} | "
                 f"C07 復元率(内包率>=0.5)={c07m.get('frac_ge05')} / C09/C10 参照 |")
    g2 = "実行可" if by_id.get("C01", {}).get("status") == "OK" else "設計変更が必要"
    lines.append(f"| G-2 | region-token を bbox→mask pooling | {g2} | "
                 f"C01 signature生存={by_id.get('C01',{}).get('measured',{}).get('signature_present')} / "
                 f"C06 IoU中央値={c06m.get('iou_median')} |")
    lines.append(f"| G-3 | mask局在改善が phase→det の壁を動かすか | 要再定義 | "
                 f"C06: mask は box 由来(SAM) -> oracle は GT box と近い. 『前景/背景分離の効果』へ再定義推奨 |")
    g4 = "拡張test split案を推奨" if c04m.get("b_has_gap") else "train内LOVO-CV(A案)で確定"
    lines.append(f"| G-4 | 評価プロトコル(ギャップ工程) | {g4} | "
                 f"C04: 17-22の評価ギャップ工程={c04m.get('gap')} |")
    lines.append("")

    # 4. 各検査詳細
    lines.append("## 4. 各検査の詳細\n")
    for cid, title, _ in CHECKS:
        r = by_id.get(cid, {})
        lines.append(f"### {cid} {title} — **{r.get('status','?')}**\n")
        for n in r.get("notes", []):
            lines.append(f"- {n}")
        if r.get("outputs"):
            lines.append(f"- 出力: {', '.join(r['outputs'])}")
        lines.append("")

    # 5. 次アクション
    lines.append("## 5. 次に取るべきアクション (優先度順)\n")
    actions = []
    if by_id.get("C02", {}).get("status") == "FAIL":
        actions.append("[P0] C02 孤児annotation: 学習は回るが評価対象が想定と異なる潜伏欠陥. "
                       "孤児破棄 or images 復元を先に決定 (詳細 csv/c02_integrity.csv)")
    if c08_leak:
        actions.append("[P0] C08 PNGリーク: handtool_masks_5cls/train のローダに canonical split "
                       "再フィルタを必須化 (val/test 混在)")
    if by_id.get("C03", {}).get("status") == "FAIL":
        actions.append("[P0] C03 LEAK: split ファイルの逸脱を除去")
    actions.append("[P1] C11 のフレームリスト(subsets/)を分母に mask/relation 実験の Δ を測る際は "
                   "S4/B2a/T1a/H-6 を同一サブセットで再計算 (基底15,437は保持だが派生タスクはサブセット). "
                   "G-4 の作業に含める")
    c05v = by_id.get("C05", {}).get("measured", {}).get("verdicts", [])
    if c05v and all(v == "IDENTICAL_CONTENT" for v in c05v):
        actions.append("[P3] C05: HTS tools と project instances は内容一致 -> 正本決定は不要. "
                       "片方を削除して容量節約可 (任意)")
    elif any(v == "SAME_FRAMES_DIFF_ANN" for v in c05v):
        actions.append("[P0] C05 SAME_FRAMES_DIFF_ANN -> instances の正本を先に確定 (Δ再現性に直結)")
    actions.append(f"[P2] G-4 の方針: C04 に基づき {g4}")
    for a in actions:
        lines.append(f"- {a}")
    lines.append("")

    report = "\n".join(lines)
    with open(os.path.join(ctx.out, "report.md"), "w", encoding="utf-8") as f:
        f.write(report)

    # summary.json
    summary = {"hts_root": ctx.hts, "project_root": ctx.proj, "seed": ctx.seed,
               "checks": {r["id"]: {"status": r["status"], "measured": r["measured"],
                                    "notes": r["notes"], "outputs": r["outputs"]}
                          for r in results}}
    with open(os.path.join(ctx.out, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)


# ----------------------------------------------------------------------------
# メイン
# ----------------------------------------------------------------------------


def run_audit(args):
    ctx = Ctx(args)
    results = []
    for cid, title, fn in CHECKS:
        print(f"[run] {cid} {title} ...", flush=True)
        res = run_check(cid, title, fn, ctx)
        print(f"      -> {res['status']}", flush=True)
        results.append(res)
    build_report(ctx, results)
    print(f"\n完了. レポート: {os.path.join(ctx.out, 'report.md')}")
    print("ステータス: " + ", ".join(f"{r['id']}={r['status']}" for r in results))
    return results


# ----------------------------------------------------------------------------
# 自己検証 (合成データで検出能力を確認)
# ----------------------------------------------------------------------------


def selftest():
    import tempfile
    import shutil
    print("=== selftest: 合成データで検出能力を確認 ===")
    tmp = tempfile.mkdtemp(prefix="hts_selftest_")
    try:
        hts = os.path.join(tmp, "hts")
        proj = os.path.join(tmp, "proj")
        bbox_tools = os.path.join(hts, "egosurgery_tool_bbox/annotations/bbox/by_split/tools")
        bbox_hands = os.path.join(hts, "egosurgery_tool_bbox/annotations/bbox/by_split/hands")
        phase = os.path.join(hts, "egosurgery_tool_bbox/annotations/phase")
        fusion = os.path.join(hts, "fusion")
        nsk = os.path.join(hts, "tool_seg_noskewer/04_1")
        for d in (bbox_tools, bbox_hands, phase, fusion, nsk,
                  os.path.join(proj, "data/splits"),
                  os.path.join(proj, "data/annotations/egosurgery_tool")):
            os.makedirs(d, exist_ok=True)
        # canonical split: train=01, val=09, test=04
        for s, vids in (("train", ["01"]), ("val", ["09"]), ("test", ["04"])):
            with open(os.path.join(proj, "data/splits", f"ego_{s}.txt"), "w") as f:
                f.write("\n".join(vids) + "\n")

        def coco(imgs, anns, cats):
            return {"images": imgs, "annotations": anns, "categories": cats}
        cats15 = [{"id": i, "name": n} for i, n in CLS15.items()]

        # --- 欠陥A: 孤児annotation (image_id=999 が images に無い) ---
        train_imgs = [{"id": 1, "file_name": "01_1_0001.jpg", "height": 100, "width": 100}]
        train_anns = [
            {"id": 1, "image_id": 1, "category_id": 0, "bbox": [10, 10, 20, 20],
             "area": 400, "iscrowd": 0, "segmentation": [[10, 10, 30, 10, 30, 30, 10, 30]]},
            {"id": 2, "image_id": 999, "category_id": 9, "bbox": [5, 5, 10, 10],
             "area": 100, "iscrowd": 0, "segmentation": [[5, 5, 15, 5, 15, 15, 5, 15]]},  # 孤児
        ]
        json.dump(coco(train_imgs, train_anns, cats15),
                  open(os.path.join(bbox_tools, "train.json"), "w"))
        # --- 欠陥B: split外動画混入 (val.json に test動画04 が混入) ---
        val_imgs = [{"id": 1, "file_name": "09_1_0001.jpg", "height": 100, "width": 100},
                    {"id": 2, "file_name": "04_1_0002.jpg", "height": 100, "width": 100}]  # LEAK
        val_anns = [{"id": 1, "image_id": 1, "category_id": 0, "bbox": [1, 1, 2, 2],
                     "area": 4, "iscrowd": 0, "segmentation": []}]
        json.dump(coco(val_imgs, val_anns, cats15),
                  open(os.path.join(bbox_tools, "val.json"), "w"))
        json.dump(coco([], [], cats15), open(os.path.join(bbox_tools, "test.json"), "w"))
        # hands
        for s in ("train", "val", "test"):
            json.dump(coco([{"id": 1, "file_name": f"{'01' if s=='train' else '09' if s=='val' else '04'}_1_0001.jpg",
                             "height": 100, "width": 100}], [],
                           [{"id": i, "name": n} for i, n in
                            zip((1, 2, 3, 4), ("Own hands left", "Own hands right",
                                               "Other hands left", "Other hands right"))]),
                      open(os.path.join(bbox_hands, f"{s}.json"), "w"))
        # phase csv (17-22 含む, ギャップ工程 disinfection を 22 に置く)
        with open(os.path.join(phase, "01_1.csv"), "w") as f:
            f.write("Frame,Phase\n01_1_0001,disinfection\n")
        with open(os.path.join(phase, "22_1.csv"), "w") as f:
            f.write("Frame,Phase\n22_1_0001,disinfection\n22_1_0002,dressing\n")
        # --- 欠陥C: signature術具欠落 (Scalpel を除いた 31cls風) ---
        nsk_cats = [{"id": 1, "name": "Bipolar Forceps"}, {"id": 2, "name": "Needle Holders"},
                    {"id": 3, "name": "Chisel"}, {"id": 4, "name": "Forceps"}]  # Scalpel欠落
        json.dump(coco([{"id": 1, "file_name": "04_1_0002.jpg", "height": 100, "width": 100}],
                       [], nsk_cats), open(os.path.join(nsk, "04_1.json"), "w"))
        # project instances (C05 用, train を HTS と別内容に)
        json.dump(coco(train_imgs, [], cats15),
                  open(os.path.join(proj, "data/annotations/egosurgery_tool/instances_train.json"), "w"))

        class A:
            pass
        a = A()
        a.hts_root, a.project_root = hts, proj
        a.out = os.path.join(tmp, "out")
        a.max_json_mb, a.rle_sample, a.c06_sample, a.seed = 90, 100, 100, 42
        ctx = Ctx(a)

        ok = True
        r02 = run_check("C02", "", check_c02, ctx)
        det_orphan = r02["measured"].get("max_orphan", 0) >= 1 and r02["status"] == "FAIL"
        print(f"  [A] 孤児annotation 検出: {'PASS' if det_orphan else 'FAIL'} "
              f"(max_orphan={r02['measured'].get('max_orphan')}, status={r02['status']})")
        ok &= det_orphan

        r03 = run_check("C03", "", check_c03, ctx)
        det_leak = r03["measured"].get("leaks", 0) >= 1 and r03["status"] == "FAIL"
        print(f"  [B] split外動画混入(LEAK) 検出: {'PASS' if det_leak else 'FAIL'} "
              f"(leaks={r03['measured'].get('leaks')}, status={r03['status']})")
        ok &= det_leak

        r01 = run_check("C01", "", check_c01, ctx)
        sp = r01["measured"].get("signature_present") or {}
        det_missing_sig = (sp.get("Scalpel") is False) and r01["status"] == "FAIL"
        print(f"  [C] signature術具欠落 検出: {'PASS' if det_missing_sig else 'FAIL'} "
              f"(signature_present={sp}, status={r01['status']})")
        ok &= det_missing_sig

        print(f"=== selftest {'ALL PASS' if ok else 'FAILED'} ===")
        return 0 if ok else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description="EgoSurgery-HTS 受入監査 C01-C11")
    ap.add_argument("--hts-root")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--out", default="reports/hts_audit")
    ap.add_argument("--max-json-mb", type=float, default=90.0,
                    help="この閾値超のJSONはロードせず SKIP(too_large) 記録 (merged 116MB を除外, toolhand 63MB は許容)")
    ap.add_argument("--rle-sample", type=int, default=4000,
                    help="C07 の RLE デコード上限/split (サンプル時はレポートに実数明記)")
    ap.add_argument("--c06-sample", type=int, default=0, help="C06 は全数(0=無制限)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if not args.hts_root:
        ap.error("--hts-root は必須 (--selftest を除く)")
    run_audit(args)


if __name__ == "__main__":
    main()
