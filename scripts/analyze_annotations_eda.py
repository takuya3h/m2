#!/usr/bin/env python
"""EgoSurgery アノテーション EDA — ドメイン特性の網羅的集計。

入力 (data/annotations/):
  - egosurgery_tool/instances_{train,val,test}.json    : 術具 15 クラス COCO
  - egosurgery_tool_hand/instances_{train,val,test}.json: 術具15+手4=19 クラス COCO
  - egosurgery_phase/<vid>_<sess>.csv                  : Frame,Phase（工程 9 クラス）

出力 (experiments/analysis/annotations_eda/):
  - stats.json                       : 全集計値（機械可読・証跡）
  - REPORT.md                        : 日本語ドキュメント
  - tool_by_phase_appearance.csv     : 工程ごとの術具登場割合 [phase x tool]
  - phase_by_tool_distribution.csv   : 術具ごとの工程登場割合 [tool x phase]
  - fig_*.png                        : 図（matplotlib があれば）

結合キー: COCO 画像 file_name の basename(拡張子無) == phase CSV の Frame 列。
数値は一切捏造せず実データから集計する。未結合フレームはカバレッジとして明示。
"""
from __future__ import annotations

import csv
import glob
import json
import os
import statistics
from collections import Counter, defaultdict

ANN = "data/annotations"
OUT = "experiments/analysis/annotations_eda"
SPLITS = ["train", "val", "test"]

# 手術ワークフロー順（表示順を臨床的な流れに揃える）
PHASE_ORDER = [
    "disinfection", "design", "anesthesia", "incision", "dissection",
    "hemostasis", "irrigation", "closure", "dressing",
]


def basename_noext(fn: str) -> str:
    return os.path.splitext(os.path.basename(fn))[0]


def load_coco(path: str):
    with open(path) as f:
        return json.load(f)


def phase_map_and_stats():
    """全 phase CSV を読み、frame->phase の写像と工程系列(動画別)を返す。"""
    pmap: dict[str, str] = {}
    seq_by_video: dict[str, list[tuple[str, str]]] = defaultdict(list)  # video -> [(frame, phase)]
    for p in sorted(glob.glob(f"{ANN}/egosurgery_phase/*.csv")):
        sess = os.path.splitext(os.path.basename(p))[0]  # e.g. 03_2
        with open(p) as f:
            for row in csv.DictReader(f):
                fr, ph = row["Frame"].strip(), row["Phase"].strip()
                pmap[fr] = ph
                seq_by_video[sess].append((fr, ph))
    return pmap, seq_by_video


def phase_temporal(seq_by_video):
    """アノテーション済みフレーム列上の連続セグメントと遷移を集計（実時間ではない）。"""
    seg_lengths = defaultdict(list)
    transitions = Counter()
    for sess, seq in seq_by_video.items():
        prev = None
        run = 0
        run_phase = None
        for _, ph in seq:
            if ph != run_phase:
                if run_phase is not None:
                    seg_lengths[run_phase].append(run)
                run_phase, run = ph, 0
            run += 1
            if prev is not None and prev != ph:
                transitions[(prev, ph)] += 1
            prev = ph
        if run_phase is not None:
            seg_lengths[run_phase].append(run)
    seg_summary = {
        ph: {
            "n_segments": len(v),
            "mean_len": round(statistics.mean(v), 1),
            "median_len": int(statistics.median(v)),
            "max_len": max(v),
        }
        for ph, v in seg_lengths.items()
    }
    return seg_summary, transitions


def main():
    os.makedirs(OUT, exist_ok=True)
    pmap, seq_by_video = phase_map_and_stats()

    phase_total = Counter(pmap.values())
    n_phase_classes = len(phase_total)
    phases_sorted = [p for p in PHASE_ORDER if p in phase_total] + \
                    [p for p in phase_total if p not in PHASE_ORDER]

    # ---- COCO (tool 15-class) を split 横断でロード ----
    tool_cats = None
    per_split = {}
    # frame -> set/counter（全 split 合算の結合用）
    frame_tool_presence: dict[str, set] = {}
    frame_tool_count: dict[str, Counter] = {}
    frame_split: dict[str, str] = {}
    video_split: dict[str, set] = defaultdict(set)

    for split in SPLITS:
        d = load_coco(f"{ANN}/egosurgery_tool/instances_{split}.json")
        if tool_cats is None:
            tool_cats = {c["id"]: c["name"] for c in d["categories"]}
        id2img = {im["id"]: im for im in d["images"]}
        # 物理動画→split
        vids = set()
        for im in d["images"]:
            bn = basename_noext(im["file_name"])
            vid = bn.split("_")[0]
            vids.add(vid)
            video_split[vid].add(split)
            frame_split[bn] = split
            frame_tool_presence.setdefault(bn, set())
            frame_tool_count.setdefault(bn, Counter())
        # クラス分布・画像頻度・bbox
        inst_count = Counter()
        img_with_class = defaultdict(set)
        rel_area_by_class = defaultdict(list)
        coco_size = Counter()  # small/medium/large
        per_image_instances = Counter()
        for a in d["annotations"]:
            cid = a["category_id"]
            im = id2img[a["image_id"]]
            bn = basename_noext(im["file_name"])
            inst_count[cid] += 1
            img_with_class[cid].add(a["image_id"])
            per_image_instances[a["image_id"]] += 1
            frame_tool_presence[bn].add(cid)
            frame_tool_count[bn][cid] += 1
            area = a.get("area") or (a["bbox"][2] * a["bbox"][3])
            rel_area_by_class[cid].append(area / (im["width"] * im["height"]))
            if area < 32 ** 2:
                coco_size["small"] += 1
            elif area < 96 ** 2:
                coco_size["medium"] += 1
            else:
                coco_size["large"] += 1
        # フレーム共起（distinct class / instances per frame）
        n_img = len(d["images"])
        imgs_with_any = len(per_image_instances)
        distinct_per_frame = [len(frame_tool_presence[basename_noext(im["file_name"])]) for im in d["images"]]
        inst_per_frame = [per_image_instances.get(im["id"], 0) for im in d["images"]]

        per_split[split] = {
            "n_images": n_img,
            "n_annotations": len(d["annotations"]),
            "ann_per_image": round(len(d["annotations"]) / n_img, 3),
            "videos": sorted(vids),
            "n_videos": len(vids),
            "images_with_no_tool": n_img - imgs_with_any,
            "frac_images_with_tool": round(imgs_with_any / n_img, 4),
            "mean_instances_per_frame": round(statistics.mean(inst_per_frame), 3),
            "mean_distinct_classes_per_frame": round(statistics.mean(distinct_per_frame), 3),
            "max_distinct_classes_per_frame": max(distinct_per_frame),
            "class_instances": {tool_cats[c]: inst_count.get(c, 0) for c in tool_cats},
            "class_image_freq": {tool_cats[c]: len(img_with_class.get(c, set())) for c in tool_cats},
            "coco_size": dict(coco_size),
            "class_median_rel_area_pct": {
                tool_cats[c]: round(100 * statistics.median(rel_area_by_class[c]), 3)
                for c in tool_cats if rel_area_by_class.get(c)
            },
        }

    # ---- 全 split 合算のクラス分布 ----
    overall_inst = Counter()
    overall_imgfreq = Counter()
    for split in SPLITS:
        for name, n in per_split[split]["class_instances"].items():
            overall_inst[name] += n
        for name, n in per_split[split]["class_image_freq"].items():
            overall_imgfreq[name] += n
    total_inst = sum(overall_inst.values())
    nz = [v for v in overall_inst.values() if v > 0]
    imbalance_ratio = round(max(nz) / min(nz), 1) if nz else None

    # ---- 手クラス（19-class COCO から手4クラスのみ）----
    hand_inst = Counter()
    dh = load_coco(f"{ANN}/egosurgery_tool_hand/instances_train.json")
    hand_cats = {c["id"]: c["name"] for c in dh["categories"] if c["id"] >= 15}
    id2img_h = {im["id"]: im for im in dh["images"]}
    hand_frame_presence = defaultdict(set)
    for a in dh["annotations"]:
        if a["category_id"] in hand_cats:
            hand_inst[hand_cats[a["category_id"]]] += 1
            bn = basename_noext(id2img_h[a["image_id"]]["file_name"])
            hand_frame_presence[bn].add(a["category_id"])

    # ---- tool x phase クロス集計（全 split 合算・検出フレームのみ）----
    # C[phase][tool_name] = phase=P のフレームで tool=T を1つ以上含むフレーム数
    C = defaultdict(lambda: Counter())
    N_phase = Counter()        # 検出フレームのうち各 phase のフレーム数
    M_tool = Counter()         # 各 tool を含むフレーム数
    frames_any_tool_by_phase = Counter()
    unmatched = 0
    for bn, present in frame_tool_presence.items():
        ph = pmap.get(bn)
        if ph is None:
            unmatched += 1
            continue
        N_phase[ph] += 1
        if present:
            frames_any_tool_by_phase[ph] += 1
        for cid in present:
            C[ph][tool_cats[cid]] += 1
            M_tool[tool_cats[cid]] += 1
    n_detection_frames = sum(N_phase.values())

    tools_by_count = [name for name, _ in overall_inst.most_common()]

    # A: 工程ごとの術具登場割合 [phase][tool] = C/N_phase
    appearance = {ph: {t: round(100 * C[ph][t] / N_phase[ph], 1) if N_phase[ph] else 0.0
                       for t in tools_by_count} for ph in phases_sorted}
    # B: 術具ごとの工程登場割合 [tool][phase] = C/M_tool
    distribution = {t: {ph: round(100 * C[ph][t] / M_tool[t], 1) if M_tool[t] else 0.0
                        for ph in phases_sorted} for t in tools_by_count}

    seg_summary, transitions = phase_temporal(seq_by_video)

    stats = {
        "generated_for": "data/annotations EgoSurgery EDA",
        "join_key": "basename(file_name) == phase CSV Frame",
        "phase": {
            "n_classes": n_phase_classes,
            "classes_sorted": phases_sorted,
            "frame_counts_all_csv": dict(phase_total),
            "total_labeled_frames": sum(phase_total.values()),
            "segment_summary": seg_summary,
        },
        "tool": {
            "n_classes": len(tool_cats),
            "names": [tool_cats[c] for c in sorted(tool_cats)],
            "overall_instances": dict(overall_inst),
            "overall_image_freq": dict(overall_imgfreq),
            "total_instances": total_inst,
            "imbalance_ratio_max_over_min": imbalance_ratio,
        },
        "hand": {
            "n_classes": len(hand_cats),
            "names": list(hand_cats.values()),
            "instances": dict(hand_inst),
        },
        "per_split": per_split,
        "video_split": {v: sorted(s) for v, s in sorted(video_split.items())},
        "coupling": {
            "n_detection_frames_joined": n_detection_frames,
            "unmatched_frames": unmatched,
            "N_phase_detection_frames": dict(N_phase),
            "M_tool_frames": dict(M_tool),
            "frames_any_tool_by_phase": dict(frames_any_tool_by_phase),
            "appearance_phase_by_tool_pct": appearance,
            "distribution_tool_by_phase_pct": distribution,
        },
        "top_transitions": [
            {"from": a, "to": b, "count": c}
            for (a, b), c in transitions.most_common(15)
        ],
    }

    with open(f"{OUT}/stats.json", "w") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # ---- CSV マトリクス ----
    with open(f"{OUT}/tool_by_phase_appearance.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["phase \\ tool (=登場割合%)"] + tools_by_count + ["any_tool%", "N_frames"])
        for ph in phases_sorted:
            anyp = round(100 * frames_any_tool_by_phase[ph] / N_phase[ph], 1) if N_phase[ph] else 0.0
            w.writerow([ph] + [appearance[ph][t] for t in tools_by_count] + [anyp, N_phase[ph]])
    with open(f"{OUT}/phase_by_tool_distribution.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tool \\ phase (=工程分布%)"] + phases_sorted + ["M_frames"])
        for t in tools_by_count:
            w.writerow([t] + [distribution[t][ph] for ph in phases_sorted] + [M_tool[t]])

    # ---- 図（任意）----
    figs = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        # 1) tool instance 分布（log）
        names = [n for n, _ in overall_inst.most_common()]
        vals = [overall_inst[n] for n in names]
        plt.figure(figsize=(10, 4))
        plt.bar(range(len(names)), vals, color="#4477aa")
        plt.yscale("log")
        plt.xticks(range(len(names)), names, rotation=60, ha="right", fontsize=8)
        plt.ylabel("instances (log)")
        plt.title("Tool class instance distribution (all splits)")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_tool_distribution.png", dpi=120)
        plt.close()
        figs.append("fig_tool_distribution.png")

        # 2) phase frame 分布
        plt.figure(figsize=(8, 4))
        pv = [phase_total[p] for p in phases_sorted]
        plt.bar(range(len(phases_sorted)), pv, color="#aa6644")
        plt.xticks(range(len(phases_sorted)), phases_sorted, rotation=45, ha="right", fontsize=9)
        plt.ylabel("labeled frames")
        plt.title("Phase frame distribution (all CSV)")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_phase_distribution.png", dpi=120)
        plt.close()
        figs.append("fig_phase_distribution.png")

        # 3) tool x phase 登場割合 ヒートマップ
        mat = np.array([[appearance[ph][t] for t in tools_by_count] for ph in phases_sorted])
        plt.figure(figsize=(11, 5))
        im = plt.imshow(mat, aspect="auto", cmap="viridis")
        plt.colorbar(im, label="appearance rate (%)")
        plt.xticks(range(len(tools_by_count)), tools_by_count, rotation=60, ha="right", fontsize=8)
        plt.yticks(range(len(phases_sorted)), phases_sorted, fontsize=9)
        plt.title("Tool appearance rate per phase  C(P,T)/N(P)")
        plt.tight_layout()
        plt.savefig(f"{OUT}/fig_tool_by_phase_heatmap.png", dpi=120)
        plt.close()
        figs.append("fig_tool_by_phase_heatmap.png")
    except Exception as e:  # 図は任意。失敗しても集計は完了させる。
        print(f"[warn] figure generation skipped: {e}")

    print("OK. detection frames joined:", n_detection_frames, "unmatched:", unmatched)
    print("figs:", figs)
    print("outputs in", OUT)
    return stats, tools_by_count, phases_sorted, figs


if __name__ == "__main__":
    main()
