#!/usr/bin/env python
"""EgoSurgery アノテーション 追加分析（実験設計向け）。

基本EDA (analyze_annotations_eda.py) に対し、本プロジェクト固有の判断に効く分析を追加する:
  1. split 間分布シフト（術具/工程 + JS divergence）
  2. クラス↔動画の集中度・split カバレッジ（per-class AP 評価可能性）
  3. tool-presence -> 工程 予測上限（GT presence frame-level Bayes 精度 + 相互情報量）
  4. 工程の混同度（tool appearance 空間の cosine 類似）
  5. 術具共起（frame-level PMI / 条件付き確率）
  6. bbox 幾何（中心バイアス・truncation・サイズ・縦横比）
  7. データ品質（退化/枠外 bbox・iscrowd・サンプリング間隔）
  8. 手の解析（工程別 手在・hand-tool 共起）

出力 (experiments/analysis/annotations_eda/):
  stats_advanced.json / 追加CSV / fig_adv_*.png
数値は実データ集計のみ。未結合・例外は明示。
"""
from __future__ import annotations

import csv
import glob
import json
import math
import os
import statistics
from collections import Counter, defaultdict

ANN = "data/annotations"
OUT = "experiments/analysis/annotations_eda"
SPLITS = ["train", "val", "test"]
PHASE_ORDER = [
    "disinfection", "design", "anesthesia", "incision", "dissection",
    "hemostasis", "irrigation", "closure", "dressing",
]


def basename_noext(fn):
    return os.path.splitext(os.path.basename(fn))[0]


def load_coco(p):
    with open(p) as f:
        return json.load(f)


def load_phase_map():
    pmap = {}
    for p in sorted(glob.glob(f"{ANN}/egosurgery_phase/*.csv")):
        with open(p) as f:
            for row in csv.DictReader(f):
                pmap[row["Frame"].strip()] = row["Phase"].strip()
    return pmap


def js_divergence(p, q):
    """2 分布(dict)の Jensen-Shannon divergence (bits)。キー和集合で正規化。"""
    keys = set(p) | set(q)
    sp, sq = sum(p.values()) or 1, sum(q.values()) or 1
    P = {k: p.get(k, 0) / sp for k in keys}
    Q = {k: q.get(k, 0) / sq for k in keys}
    M = {k: 0.5 * (P[k] + Q[k]) for k in keys}

    def kl(a, b):
        s = 0.0
        for k in keys:
            if a[k] > 0 and b[k] > 0:
                s += a[k] * math.log2(a[k] / b[k])
        return s
    return round(0.5 * kl(P, M) + 0.5 * kl(Q, M), 4)


def macro_f1(y_true, y_pred, labels):
    f1s = []
    for lb in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lb and p == lb)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lb and p == lb)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lb and p != lb)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s.append(2 * prec * rec / (prec + rec) if prec + rec else 0.0)
    return round(sum(f1s) / len(f1s), 4) if f1s else 0.0


def main():
    os.makedirs(OUT, exist_ok=True)
    pmap = load_phase_map()

    # ---- ロード: tool COCO（split/video/frame 構造） ----
    tool_cats = None
    # frame -> (split, video, set(cids))
    frame_info = {}
    # per split: class instance counts; per class: video set & per-video inst
    split_class_inst = {s: Counter() for s in SPLITS}
    split_phase_frames = {s: Counter() for s in SPLITS}
    class_video_inst = defaultdict(Counter)   # cid -> Counter(video -> inst)
    class_split_inst = defaultdict(Counter)   # cid -> Counter(split -> inst)
    # bbox 幾何・品質
    geom = defaultdict(lambda: {"cx": [], "cy": [], "ar": [], "rel_area": []})
    quality = Counter()
    n_box = 0
    # 共起用 frame -> set
    frame_present = {}

    for split in SPLITS:
        d = load_coco(f"{ANN}/egosurgery_tool/instances_{split}.json")
        if tool_cats is None:
            tool_cats = {c["id"]: c["name"] for c in d["categories"]}
        id2img = {im["id"]: im for im in d["images"]}
        for im in d["images"]:
            bn = basename_noext(im["file_name"])
            vid = bn.split("_")[0]
            frame_info[bn] = [split, vid, set()]
            frame_present.setdefault(bn, set())
            ph = pmap.get(bn)
            if ph:
                split_phase_frames[split][ph] += 1
        for a in d["annotations"]:
            cid = a["category_id"]
            im = id2img[a["image_id"]]
            bn = basename_noext(im["file_name"])
            vid = bn.split("_")[0]
            W, H = im["width"], im["height"]
            x, y, w, h = a["bbox"]
            n_box += 1
            split_class_inst[split][cid] += 1
            class_video_inst[cid][vid] += 1
            class_split_inst[cid][split] += 1
            frame_info[bn][2].add(cid)
            frame_present[bn].add(cid)
            # geometry
            if w > 0 and h > 0:
                geom[cid]["cx"].append((x + w / 2) / W)
                geom[cid]["cy"].append((y + h / 2) / H)
                geom[cid]["ar"].append(w / h)
                geom[cid]["rel_area"].append((w * h) / (W * H))
            else:
                quality["degenerate_wh<=0"] += 1
            if x < 0 or y < 0 or x + w > W + 1 or y + h > H + 1:
                quality["out_of_bounds"] += 1
            if x <= 1 or y <= 1 or x + w >= W - 1 or y + h >= H - 1:
                quality["touches_border(truncation)"] += 1
            if a.get("iscrowd"):
                quality["iscrowd"] += 1

    names = [tool_cats[c] for c in sorted(tool_cats)]

    # ---- 1. split 間分布シフト ----
    def named(counter):
        return {tool_cats[c]: n for c, n in counter.items()}
    cls_dist = {s: named(split_class_inst[s]) for s in SPLITS}
    shift = {
        "tool_js_train_val": js_divergence(split_class_inst["train"], split_class_inst["val"]),
        "tool_js_train_test": js_divergence(split_class_inst["train"], split_class_inst["test"]),
        "tool_js_val_test": js_divergence(split_class_inst["val"], split_class_inst["test"]),
        "phase_js_train_val": js_divergence(split_phase_frames["train"], split_phase_frames["val"]),
        "phase_js_train_test": js_divergence(split_phase_frames["train"], split_phase_frames["test"]),
        "phase_js_val_test": js_divergence(split_phase_frames["val"], split_phase_frames["test"]),
    }

    # ---- 2. クラス↔動画 集中度・カバレッジ ----
    coverage = {}
    for cid in sorted(tool_cats):
        tot = sum(class_video_inst[cid].values())
        vids = class_video_inst[cid]
        max_share = round(max(vids.values()) / tot, 3) if tot else 0.0
        coverage[tool_cats[cid]] = {
            "total_inst": tot,
            "n_videos": len(vids),
            "max_single_video_share": max_share,
            "in_train": class_split_inst[cid].get("train", 0) > 0,
            "in_val": class_split_inst[cid].get("val", 0) > 0,
            "in_test": class_split_inst[cid].get("test", 0) > 0,
            "split_inst": dict(class_split_inst[cid]),
        }
    eval_gaps = [n for n, c in coverage.items() if not c["in_test"] or not c["in_train"]]

    # ---- 3. tool-presence -> 工程 予測上限 + MI ----
    det_frames = [(bn, frame_info[bn][0], frozenset(frame_info[bn][2]), pmap[bn])
                  for bn in frame_info if bn in pmap]
    phases_present = sorted({ph for *_, ph in det_frames},
                            key=lambda p: PHASE_ORDER.index(p) if p in PHASE_ORDER else 99)
    # 経験ベイズ: train で pattern->majority phase
    pat2phase = defaultdict(Counter)
    for bn, sp, pat, ph in det_frames:
        if sp == "train":
            pat2phase[pat][ph] += 1
    train_phase_counter = Counter(ph for _, sp, _, ph in det_frames if sp == "train")
    fallback = train_phase_counter.most_common(1)[0][0]
    pat_map = {pat: c.most_common(1)[0][0] for pat, c in pat2phase.items()}

    def eval_split(sp):
        yt, yp = [], []
        for bn, s, pat, ph in det_frames:
            if s != sp:
                continue
            yt.append(ph)
            yp.append(pat_map.get(pat, fallback))
        acc = round(sum(1 for t, p in zip(yt, yp) if t == p) / len(yt), 4) if yt else 0.0
        return acc, macro_f1(yt, yp, phases_present), len(yt)

    train_acc, train_mf1, n_tr = eval_split("train")
    test_acc, test_mf1, n_te = eval_split("test")
    val_acc, val_mf1, n_va = eval_split("val")
    # majority baseline (test)
    te_phase = Counter(ph for _, s, _, ph in det_frames if s == "test")
    maj_acc = round(max(te_phase.values()) / sum(te_phase.values()), 4) if te_phase else 0.0

    # MI(presence_T ; phase) bits, 全検出フレーム
    N = len(det_frames)
    ph_count = Counter(ph for *_, ph in det_frames)
    mi = {}
    for cid in sorted(tool_cats):
        # joint counts
        joint = Counter()  # (present(0/1), phase)
        pres_count = 0
        for _, _, pat, ph in det_frames:
            t = 1 if cid in pat else 0
            pres_count += t
            joint[(t, ph)] += 1
        Pt = {1: pres_count / N, 0: 1 - pres_count / N}
        val = 0.0
        for (t, ph), c in joint.items():
            pjoint = c / N
            denom = Pt[t] * (ph_count[ph] / N)
            if pjoint > 0 and denom > 0:
                val += pjoint * math.log2(pjoint / denom)
        mi[tool_cats[cid]] = round(val, 4)

    # ---- 4. 工程混同度（tool appearance 空間 cosine） ----
    # phase vector = [P(tool in frame | phase)] over tools, on detection frames
    Cmat = defaultdict(lambda: Counter())
    Nph = Counter()
    for _, _, pat, ph in det_frames:
        Nph[ph] += 1
        for cid in pat:
            Cmat[ph][cid] += 1
    phase_vec = {ph: [Cmat[ph][c] / Nph[ph] if Nph[ph] else 0.0 for c in sorted(tool_cats)]
                 for ph in phases_present}

    def cosine(a, b):
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        return round(dot / (na * nb), 3) if na and nb else 0.0
    confus = []
    pl = phases_present
    for i in range(len(pl)):
        for j in range(i + 1, len(pl)):
            confus.append((pl[i], pl[j], cosine(phase_vec[pl[i]], phase_vec[pl[j]])))
    confus.sort(key=lambda x: -x[2])

    # ---- 5. 術具共起 PMI（frame-level, 検出フレーム） ----
    Nf = len(frame_present)
    pres = {c: 0 for c in tool_cats}
    pair = Counter()
    for bn, s in [(b, frame_info[b][0]) for b in frame_present]:
        cs = sorted(frame_present[bn])
        for c in cs:
            pres[c] += 1
        for ii in range(len(cs)):
            for jj in range(ii + 1, len(cs)):
                pair[(cs[ii], cs[jj])] += 1
    cooc = []
    for (i, j), cij in pair.items():
        pi, pj = pres[i] / Nf, pres[j] / Nf
        pij = cij / Nf
        pmi = round(math.log2(pij / (pi * pj)), 3) if pi and pj and pij else None
        cond_j_given_i = round(cij / pres[i], 3) if pres[i] else 0.0
        cooc.append({"a": tool_cats[i], "b": tool_cats[j], "frames": cij,
                     "pmi": pmi, "p(b|a)": cond_j_given_i,
                     "p(a|b)": round(cij / pres[j], 3) if pres[j] else 0.0})
    cooc_top_pmi = sorted([c for c in cooc if c["pmi"] is not None],
                          key=lambda x: -x["pmi"])[:15]
    cooc_top_freq = sorted(cooc, key=lambda x: -x["frames"])[:15]

    # ---- 6. bbox 幾何サマリ ----
    geom_summary = {}
    for cid in sorted(tool_cats):
        g = geom[cid]
        if not g["cx"]:
            continue
        geom_summary[tool_cats[cid]] = {
            "median_cx": round(statistics.median(g["cx"]), 3),
            "median_cy": round(statistics.median(g["cy"]), 3),
            "median_aspect_w_over_h": round(statistics.median(g["ar"]), 2),
            "median_rel_area_pct": round(100 * statistics.median(g["rel_area"]), 2),
        }
    all_cx = [v for cid in geom for v in geom[cid]["cx"]]
    all_cy = [v for cid in geom for v in geom[cid]["cy"]]
    center_bias = {
        "median_cx": round(statistics.median(all_cx), 3),
        "median_cy": round(statistics.median(all_cy), 3),
        "frac_center_third": round(
            sum(1 for x, y in zip(all_cx, all_cy) if 1 / 3 <= x <= 2 / 3 and 1 / 3 <= y <= 2 / 3)
            / len(all_cx), 3),
    }

    # ---- 7. サンプリング間隔（連続アノテフレームの frame-number stride） ----
    strides = []
    by_sess = defaultdict(list)
    for fr in pmap:
        parts = fr.rsplit("_", 1)
        if len(parts) == 2 and parts[1].isdigit():
            by_sess[parts[0]].append(int(parts[1]))
    for sess, nums in by_sess.items():
        nums.sort()
        strides += [b - a for a, b in zip(nums, nums[1:]) if b > a]
    stride_summary = {
        "median_stride": int(statistics.median(strides)) if strides else None,
        "mode_stride": Counter(strides).most_common(1)[0][0] if strides else None,
        "p90_stride": sorted(strides)[int(0.9 * len(strides))] if strides else None,
    }

    # ---- 8. 手の解析（19-class instances） ----
    dh = load_coco(f"{ANN}/egosurgery_tool_hand/instances_train.json")
    hand_ids = {c["id"] for c in dh["categories"] if c["id"] >= 15}
    id2img_h = {im["id"]: im for im in dh["images"]}
    frame_hand = defaultdict(set)
    for a in dh["annotations"]:
        if a["category_id"] in hand_ids:
            frame_hand[basename_noext(id2img_h[a["image_id"]]["file_name"])].add(a["category_id"])
    hand_by_phase = {}
    for ph in phases_present:
        frames = [bn for bn, _, _, p in det_frames if p == ph]
        if not frames:
            continue
        with_hand = sum(1 for bn in frames if frame_hand.get(bn))
        with_both = sum(1 for bn in frames if frame_hand.get(bn) and frame_info[bn][2])
        mean_hands = round(statistics.mean([len(frame_hand.get(bn, ())) for bn in frames]), 2)
        hand_by_phase[ph] = {
            "frac_with_hand": round(with_hand / len(frames), 3),
            "frac_hand_and_tool": round(with_both / len(frames), 3),
            "mean_hands_per_frame": mean_hands,
        }

    stats = {
        "1_split_shift": {"tool_class_dist_per_split": cls_dist,
                          "phase_frames_per_split": {s: dict(split_phase_frames[s]) for s in SPLITS},
                          "js_divergence_bits": shift},
        "2_class_video_coverage": {"per_class": coverage, "eval_gaps_missing_train_or_test": eval_gaps},
        "3_tool_to_phase_bound": {
            "note": "GT tool-presence からのフレーム単位 phase 予測（時間情報なし）。B2a 信号上限の目安。",
            "train_fit_acc": train_acc, "train_macro_f1": train_mf1, "n_train": n_tr,
            "val_acc": val_acc, "val_macro_f1": val_mf1, "n_val": n_va,
            "test_acc": test_acc, "test_macro_f1": test_mf1, "n_test": n_te,
            "test_majority_baseline_acc": maj_acc,
            "mutual_information_bits": dict(sorted(mi.items(), key=lambda x: -x[1])),
        },
        "4_phase_confusability_cosine": [{"a": a, "b": b, "cosine": c} for a, b, c in confus[:10]],
        "5_tool_cooccurrence": {"top_pmi": cooc_top_pmi, "top_frequency": cooc_top_freq},
        "6_bbox_geometry": {"center_bias": center_bias, "per_class": geom_summary},
        "7_quality": {"n_boxes": n_box, "flags": dict(quality), "sampling_stride": stride_summary},
        "8_hand": {"hand_by_phase": hand_by_phase},
    }
    with open(f"{OUT}/stats_advanced.json", "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # 追加CSV: クラス↔動画カバレッジ
    with open(f"{OUT}/class_video_coverage.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tool", "total_inst", "n_videos", "max_single_video_share",
                    "in_train", "in_val", "in_test"])
        for n, c in sorted(coverage.items(), key=lambda x: -x[1]["total_inst"]):
            w.writerow([n, c["total_inst"], c["n_videos"], c["max_single_video_share"],
                        c["in_train"], c["in_val"], c["in_test"]])

    # 図（任意）
    figs = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        # 中心バイアス heatmap
        plt.figure(figsize=(5, 4))
        H2, xe, ye = np.histogram2d(all_cx, all_cy, bins=20, range=[[0, 1], [0, 1]])
        plt.imshow(H2.T, origin="lower", extent=[0, 1, 0, 1], aspect="auto", cmap="magma")
        plt.colorbar(label="bbox count")
        plt.xlabel("cx (norm)")
        plt.ylabel("cy (norm)")
        plt.title("Tool bbox center distribution")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_adv_center_bias.png", dpi=120)
        plt.close()
        figs.append("fig_adv_center_bias.png")

        # 共起 PMI ヒートマップ
        ncls = len(names)
        M = np.full((ncls, ncls), np.nan)
        idx = {tool_cats[c]: k for k, c in enumerate(sorted(tool_cats))}
        for c in cooc:
            if c["pmi"] is not None:
                i, j = idx[c["a"]], idx[c["b"]]
                M[i, j] = M[j, i] = c["pmi"]
        plt.figure(figsize=(8, 7))
        im = plt.imshow(M, cmap="coolwarm", vmin=-2, vmax=2)
        plt.colorbar(im, label="PMI (bits)")
        plt.xticks(range(ncls), names, rotation=90, fontsize=7)
        plt.yticks(range(ncls), names, fontsize=7)
        plt.title("Tool-tool co-occurrence PMI (frame-level)")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_adv_cooccurrence_pmi.png", dpi=120)
        plt.close()
        figs.append("fig_adv_cooccurrence_pmi.png")

        # split 間 工程分布（正規化）
        plt.figure(figsize=(9, 4))
        x = np.arange(len(phases_present))
        for k, s in enumerate(SPLITS):
            tot = sum(split_phase_frames[s].values()) or 1
            vals = [split_phase_frames[s].get(p, 0) / tot for p in phases_present]
            plt.bar(x + (k - 1) * 0.25, vals, width=0.25, label=s)
        plt.xticks(x, phases_present, rotation=45, ha="right", fontsize=8)
        plt.ylabel("frame fraction")
        plt.legend()
        plt.title("Phase distribution per split (normalized)")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_adv_phase_split.png", dpi=120)
        plt.close()
        figs.append("fig_adv_phase_split.png")
    except Exception as e:
        print(f"[warn] figure generation skipped: {e}")

    print("OK advanced. det_frames:", N, "boxes:", n_box)
    print("eval_gaps (missing train or test):", eval_gaps)
    print("tool->phase test acc/mf1:", test_acc, test_mf1, "majority:", maj_acc)
    print("stride:", stride_summary, "figs:", figs)
    return stats


if __name__ == "__main__":
    main()
