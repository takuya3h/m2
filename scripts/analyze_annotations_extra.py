#!/usr/bin/env python
"""EgoSurgery アノテーション さらなる追加分析（実験設計・疑似ラベル前段）。

§1-§17（analyze_annotations_eda.py / analyze_annotations_advanced.py）と重複しない新規分析:
  18. 手-術具の空間接触（IoU/中心距離）— bbox_near_contact / hand_tool_relation 疑似ラベル前段
  19. 工程の時間予測性（1次マルコフ精度・粘性・境界フレーム率）
  20. シーンテンプレート（頻出術具セット・ラベル濃度分布）
  21. 工程順序の動画間一貫性（標準ワークフロー遵守率）
  22. 手の左右/自他 × 工程別内訳
  23. 推奨クラス重み（effective number, 術具/工程）
  24. 工程別の術具スケール + 検出難易度プロキシ
  25. 検出アノテ無しの工程フレームの素性

出力 (experiments/analysis/annotations_eda/): stats_extra.json / fig_ext_*.png
全て実データ集計。数値捏造なし。
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
HAND_NAMES = {15: "Own L", 16: "Own R", 17: "Other L", 18: "Other R"}


def basename_noext(fn):
    return os.path.splitext(os.path.basename(fn))[0]


def load_coco(p):
    with open(p) as f:
        return json.load(f)


def load_phase():
    pmap = {}
    seq = defaultdict(list)  # sess -> [(framenum, phase)]
    for p in sorted(glob.glob(f"{ANN}/egosurgery_phase/*.csv")):
        sess = os.path.splitext(os.path.basename(p))[0]
        with open(p) as f:
            for row in csv.DictReader(f):
                fr, ph = row["Frame"].strip(), row["Phase"].strip()
                pmap[fr] = ph
                num = int(fr.rsplit("_", 1)[1])
                seq[sess].append((num, ph))
    for s in seq:
        seq[s].sort()
    return pmap, seq


def iou(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    x1, y1 = max(ax, bx), max(ay, by)
    x2, y2 = min(ax + aw, bx + bw), min(ay + ah, by + bh)
    iw, ih = max(0.0, x2 - x1), max(0.0, y2 - y1)
    inter = iw * ih
    union = aw * ah + bw * bh - inter
    return inter / union if union > 0 else 0.0


def main():
    os.makedirs(OUT, exist_ok=True)
    pmap, seq = load_phase()

    # ---- 19-class から frame -> (tool_boxes, hand_boxes) ----
    frame_tool_boxes = defaultdict(list)
    frame_hand_boxes = defaultdict(list)
    frame_hand_cls = defaultdict(set)
    diag = None
    for split in SPLITS:
        d = load_coco(f"{ANN}/egosurgery_tool_hand/instances_{split}.json")
        id2img = {im["id"]: im for im in d["images"]}
        for a in d["annotations"]:
            im = id2img[a["image_id"]]
            if diag is None:
                diag = math.hypot(im["width"], im["height"])
            bn = basename_noext(im["file_name"])
            if a["category_id"] >= 15:
                frame_hand_boxes[bn].append(a["bbox"])
                frame_hand_cls[bn].add(a["category_id"])
            else:
                frame_tool_boxes[bn].append((a["category_id"], a["bbox"]))

    # ---- 18. 手-術具 空間接触 ----
    max_ious, min_dists = [], []
    n_tool_boxes = 0
    overlap_boxes = 0          # IoU>0.1
    near_boxes = 0             # 中心距離 < 0.15*diag
    frames_with_contact = 0
    contact_by_phase_num = Counter()
    contact_by_phase_den = Counter()
    for bn, tools in frame_tool_boxes.items():
        hands = frame_hand_boxes.get(bn, [])
        ph = pmap.get(bn)
        frame_has_contact = False
        for _, tb in tools:
            n_tool_boxes += 1
            if not hands:
                max_ious.append(0.0)
                continue
            tcx, tcy = tb[0] + tb[2] / 2, tb[1] + tb[3] / 2
            mi = max(iou(tb, hb) for hb in hands)
            md = min(math.hypot(tcx - (hb[0] + hb[2] / 2), tcy - (hb[1] + hb[3] / 2)) for hb in hands)
            max_ious.append(mi)
            min_dists.append(md / diag)
            if mi > 0.1:
                overlap_boxes += 1
                frame_has_contact = True
            if md / diag < 0.15:
                near_boxes += 1
        if ph:
            contact_by_phase_den[ph] += 1
            if frame_has_contact:
                contact_by_phase_num[ph] += 1
        if frame_has_contact:
            frames_with_contact += 1
    contact = {
        "n_tool_boxes": n_tool_boxes,
        "frac_tool_overlap_hand_iou>0.1": round(overlap_boxes / n_tool_boxes, 3),
        "frac_tool_near_hand_dist<0.15diag": round(near_boxes / n_tool_boxes, 3),
        "mean_max_iou_tool_hand": round(statistics.mean(max_ious), 3),
        "median_min_center_dist_norm": round(statistics.median(min_dists), 3) if min_dists else None,
        "frames_with_contact": frames_with_contact,
        "contact_rate_by_phase": {
            ph: round(contact_by_phase_num[ph] / contact_by_phase_den[ph], 3)
            for ph in contact_by_phase_den
        },
    }

    # ---- 19. 工程の時間予測性（1次マルコフ） ----
    trans = Counter()       # (prev,cur)
    prev_count = Counter()  # prev
    n_steps = 0
    self_trans = 0
    boundary_frames = 0
    total_frames = 0
    for s, lst in seq.items():
        phs = [p for _, p in lst]
        total_frames += len(phs)
        for i in range(len(phs)):
            if 0 < i:
                trans[(phs[i - 1], phs[i])] += 1
                prev_count[phs[i - 1]] += 1
                n_steps += 1
                if phs[i] == phs[i - 1]:
                    self_trans += 1
            is_boundary = (i > 0 and phs[i] != phs[i - 1]) or (i < len(phs) - 1 and phs[i] != phs[i + 1])
            if is_boundary:
                boundary_frames += 1
    # 1次マルコフ予測精度: predict argmax P(cur|prev)
    best_next = {}
    by_prev = defaultdict(Counter)
    for (p, c), n in trans.items():
        by_prev[p][c] += n
    for p, cnt in by_prev.items():
        best_next[p] = cnt.most_common(1)[0][0]
    markov_acc = round(sum(c.most_common(1)[0][1] for c in by_prev.values()) / n_steps, 4) if n_steps else 0.0
    temporal = {
        "n_frames": total_frames,
        "self_transition_rate": round(self_trans / n_steps, 4) if n_steps else 0.0,
        "boundary_frame_rate": round(boundary_frames / total_frames, 4) if total_frames else 0.0,
        "first_order_markov_next_acc": markov_acc,
        "most_likely_next": {p: best_next[p] for p in by_prev},
    }

    # ---- 20. シーンテンプレート（頻出術具セット・ラベル濃度） ----
    tool_cats = {c["id"]: c["name"]
                 for c in load_coco(f"{ANN}/egosurgery_tool/instances_train.json")["categories"]}
    frame_toolset = {}
    for split in SPLITS:
        d = load_coco(f"{ANN}/egosurgery_tool/instances_{split}.json")
        id2img = {im["id"]: im for im in d["images"]}
        for im in d["images"]:
            frame_toolset.setdefault(basename_noext(im["file_name"]), set())
        for a in d["annotations"]:
            bn = basename_noext(id2img[a["image_id"]]["file_name"])
            frame_toolset[bn].add(a["category_id"])
    cardinality = Counter(len(s) for s in frame_toolset.values())
    setcount = Counter(frozenset(s) for s in frame_toolset.values())
    set_phase = defaultdict(Counter)
    for bn, s in frame_toolset.items():
        if bn in pmap:
            set_phase[frozenset(s)][pmap[bn]] += 1
    top_sets = []
    for fs, n in setcount.most_common(12):
        dom = set_phase[fs].most_common(1)[0] if set_phase[fs] else ("-", 0)
        top_sets.append({
            "tools": sorted(tool_cats[c] for c in fs) if fs else ["(none)"],
            "frames": n,
            "dominant_phase": dom[0],
            "dominant_phase_frac": round(dom[1] / n, 2) if n else 0.0,
        })
    templates = {
        "cardinality_distribution": {str(k): cardinality[k] for k in sorted(cardinality)},
        "n_unique_toolsets": len(setcount),
        "top_toolsets": top_sets,
    }

    # ---- 21. 工程順序の動画間一貫性 ----
    canon = [p for p in PHASE_ORDER]
    first_pos = {}  # sess -> {phase: median framenum}
    for s, lst in seq.items():
        pos = defaultdict(list)
        for num, ph in lst:
            pos[ph].append(num)
        first_pos[s] = {ph: statistics.median(v) for ph, v in pos.items()}
    pair_adh = {}
    for i in range(len(canon)):
        for j in range(i + 1, len(canon)):
            a, b = canon[i], canon[j]
            agree = tot = 0
            for s, pos in first_pos.items():
                if a in pos and b in pos:
                    tot += 1
                    if pos[a] < pos[b]:
                        agree += 1
            if tot >= 3:
                pair_adh[f"{a}<{b}"] = {"adherence": round(agree / tot, 2), "videos": tot}
    violations = sorted(pair_adh.items(), key=lambda x: x[1]["adherence"])[:6]
    overall_adh = round(statistics.mean([v["adherence"] for v in pair_adh.values()]), 3) if pair_adh else None
    ordering = {"overall_canonical_adherence": overall_adh,
                "most_violated_pairs": [{"pair": k, **v} for k, v in violations]}

    # ---- 22. 手の左右/自他 × 工程 ----
    hand_lat = {}
    for ph in [p for p in PHASE_ORDER]:
        frames = [bn for bn in frame_toolset if pmap.get(bn) == ph]
        if not frames:
            continue
        n = len(frames)
        cls_frac = {HAND_NAMES[h]: round(sum(1 for bn in frames if h in frame_hand_cls.get(bn, ())) / n, 3)
                    for h in HAND_NAMES}
        own = sum(1 for bn in frames if (15 in frame_hand_cls.get(bn, ()) or 16 in frame_hand_cls.get(bn, ())))
        other = sum(1 for bn in frames if (17 in frame_hand_cls.get(bn, ()) or 18 in frame_hand_cls.get(bn, ())))
        cls_frac["any_own"] = round(own / n, 3)
        cls_frac["any_other"] = round(other / n, 3)
        hand_lat[ph] = cls_frac

    # ---- 23. 推奨クラス重み（effective number, beta=0.999） ----
    def eff_weights(counts, beta=0.999):
        w = {k: (1 - beta) / (1 - beta ** n) if n > 0 else 0.0 for k, n in counts.items()}
        s = sum(w.values()) or 1
        K = len(w)
        return {k: round(v / s * K, 3) for k, v in w.items()}  # 平均1に正規化
    tool_counts = Counter()
    for split in SPLITS:
        d = load_coco(f"{ANN}/egosurgery_tool/instances_{split}.json")
        for a in d["annotations"]:
            tool_counts[tool_cats[a["category_id"]]] += 1
    phase_counts = Counter(pmap.values())
    weights = {
        "note": "effective-number (beta=0.999), 平均1に正規化。loss 重み/RFS 閾値の出発点。",
        "tool_weights": dict(sorted(eff_weights(tool_counts).items(), key=lambda x: -x[1])),
        "phase_weights": dict(sorted(eff_weights(phase_counts).items(), key=lambda x: -x[1])),
    }

    # ---- 24. 工程別 術具スケール + 検出難易度プロキシ ----
    rel_by_phase = defaultdict(list)
    rel_by_class = defaultdict(list)
    ar_by_class = defaultdict(list)
    inst_per_img_by_class = defaultdict(Counter)  # cid -> Counter(image_id->n)
    for split in SPLITS:
        d = load_coco(f"{ANN}/egosurgery_tool/instances_{split}.json")
        id2img = {im["id"]: im for im in d["images"]}
        for a in d["annotations"]:
            im = id2img[a["image_id"]]
            bn = basename_noext(im["file_name"])
            ra = (a["bbox"][2] * a["bbox"][3]) / (im["width"] * im["height"])
            if pmap.get(bn):
                rel_by_phase[pmap[bn]].append(ra)
            rel_by_class[tool_cats[a["category_id"]]].append(ra)
            if a["bbox"][3] > 0:
                ar_by_class[tool_cats[a["category_id"]]].append(a["bbox"][2] / a["bbox"][3])
            inst_per_img_by_class[tool_cats[a["category_id"]]][a["image_id"]] += 1

    def iqr(v):
        v = sorted(v)
        if len(v) < 4:
            return [round(min(v), 3), round(max(v), 3)] if v else [0, 0]
        return [round(v[len(v) // 4], 4), round(v[3 * len(v) // 4], 4)]
    scale = {
        "mean_rel_area_pct_by_phase": {ph: round(100 * statistics.mean(rel_by_phase[ph]), 2)
                                       for ph in rel_by_phase},
        "difficulty_proxy_by_class": {
            cls: {
                "rel_area_iqr_pct": [round(100 * x, 3) for x in iqr(rel_by_class[cls])],
                "aspect_iqr": iqr(ar_by_class[cls]),
                "mean_inst_per_image": round(statistics.mean(inst_per_img_by_class[cls].values()), 2),
            } for cls in tool_cats.values()
        },
    }

    # ---- 25. 検出アノテ無しの工程フレーム ----
    det_frames = set(frame_toolset)
    phase_only = [fr for fr in pmap if fr not in det_frames]
    phase_only_by_phase = Counter(pmap[fr] for fr in phase_only)
    gap = {
        "n_phase_labeled_frames": len(pmap),
        "n_detection_frames": len(det_frames),
        "n_phase_only_frames": len(phase_only),
        "phase_only_by_phase": dict(phase_only_by_phase.most_common()),
    }

    stats = {
        "18_hand_tool_contact": contact,
        "19_temporal_predictability": temporal,
        "20_scene_templates": templates,
        "21_phase_ordering_consistency": ordering,
        "22_hand_laterality_by_phase": hand_lat,
        "23_suggested_class_weights": weights,
        "24_tool_scale_and_difficulty": scale,
        "25_phase_only_frames": gap,
    }
    with open(f"{OUT}/stats_extra.json", "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # 図
    figs = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # tool-hand maxIoU ヒスト
        plt.figure(figsize=(6, 4))
        plt.hist(max_ious, bins=30, color="#338866")
        plt.xlabel("max IoU(tool, any hand) per tool box")
        plt.ylabel("count")
        plt.title("Hand-tool spatial overlap distribution")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_ext_hand_tool_iou.png", dpi=120)
        plt.close()
        figs.append("fig_ext_hand_tool_iou.png")

        # 接触率 by phase
        phs = [p for p in PHASE_ORDER if p in contact["contact_rate_by_phase"]]
        plt.figure(figsize=(8, 4))
        plt.bar(range(len(phs)), [contact["contact_rate_by_phase"][p] for p in phs], color="#aa4466")
        plt.xticks(range(len(phs)), phs, rotation=45, ha="right", fontsize=8)
        plt.ylabel("frames with hand-tool contact")
        plt.title("Hand-tool contact rate by phase")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_ext_contact_by_phase.png", dpi=120)
        plt.close()
        figs.append("fig_ext_contact_by_phase.png")

        # ラベル濃度分布
        ks = sorted(cardinality)
        plt.figure(figsize=(6, 4))
        plt.bar([str(k) for k in ks], [cardinality[k] for k in ks], color="#4466aa")
        plt.xlabel("# distinct tool classes per frame")
        plt.ylabel("frames")
        plt.title("Tool label cardinality")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_ext_cardinality.png", dpi=120)
        plt.close()
        figs.append("fig_ext_cardinality.png")
    except Exception as e:
        print(f"[warn] figure generation skipped: {e}")

    print("OK extra.")
    print("hand-tool overlap frac:", contact["frac_tool_overlap_hand_iou>0.1"],
          "near frac:", contact["frac_tool_near_hand_dist<0.15diag"])
    print("markov next acc:", temporal["first_order_markov_next_acc"],
          "self-trans:", temporal["self_transition_rate"],
          "boundary:", temporal["boundary_frame_rate"])
    print("ordering adherence:", ordering["overall_canonical_adherence"])
    print("phase-only frames:", gap["n_phase_only_frames"], gap["phase_only_by_phase"])
    print("figs:", figs)
    return stats


if __name__ == "__main__":
    main()
