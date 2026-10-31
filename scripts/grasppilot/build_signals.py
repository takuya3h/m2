"""正解の把持の信号と注釈の計測（非公式 T-2026-10-31-grasp-pilot-probe、Task C-1・C-6・C-7、Task E-2）。

折り A の train と val のフレームだけを走査する（test と extra の注釈は開かない）。

    g_{part}.npz        工程注釈のある全フレーム（マニフェスト）の g（14）と旗（注釈のあるフレームで 1）
    boxstate_{part}.npz 検出塔の正解の枠ごとの r（3）。q と s は grasp_signals.box_state で τ ごとに作る
    summary.json        被覆、要約値、案 C の材料、E-2 の重なり、通した動画の集合

案 B の地図 m は保存しない（学習と評価のときに注釈から作る。grasp_signals.HTSIndex.map_channels）。ここでは被覆だけを数える。

    .venv/bin/python scripts/grasppilot/build_signals.py --out <dir> [--workers 16]
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grasppilot import grasp_signals as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402

IDX = None
TOOL = {}


def _iou(a, b):
    u = np.logical_or(a, b).sum()
    return float(np.logical_and(a, b).sum() / u) if u else 0.0


def per_frame(stem):
    h, w = IDX.size.get(stem, (1080, 1920))
    has = {k: stem in IDX.anns[k] for k in IDX.KINDS}
    ann = IDX.annotated(stem)
    ch = IDX.g_channels(stem)
    g = G.summary_g(ch) if ann else np.zeros(14, np.float32)
    boxes = TOOL.get(stem, [])
    r = G.box_ratios(ch, [b["bbox"] for b in boxes], h, w) if ann else np.zeros((len(boxes), 3))
    out = {"stem": stem, "has": has, "annotated": ann, "g": g, "r": r,
           "box_ids": [b["id"] for b in boxes], "box_cats": [b["category_id"] for b in boxes]}
    tool_inst = []
    if has["tool_seg"]:
        names = IDX.cats["tool_seg"]
        tool_inst = [(names[a["category_id"]], G.decode(a["segmentation"], h, w)) for a in IDX.anns["tool_seg"][stem]]
    if ann:
        grasped = {}
        for side in ("L", "R", "B"):
            m = ch.get(f"tool_{side}")
            if m is None or not m.any():
                grasped[side] = "__not_grasping__"
                continue
            mb = m > 0
            inter = [(int(np.logical_and(mb, t).sum()), n) for n, t in tool_inst]
            best = max(inter, default=(0, None))
            grasped[side] = best[1] if best[0] > 0 else "__none__"
        out["grasped"] = grasped
        # E-2: 扱う器具のインスタンスごとの、術具の分割のインスタンスとの IoU の最大
        ht = IDX.anns["hand_tool_seg"][stem]
        out["ht_tool_iou"] = []
        for a in ht:
            if a["category_id"] in (3, 4, 5):
                m = G.decode(a["segmentation"], h, w)
                out["ht_tool_iou"].append((a["category_id"], max((_iou(m, t) for _, t in tool_inst), default=None)))
        hands = IDX.class_masks("hand_seg", stem, G.HAND_CAT) if has["hand_seg"] else {}
        out["hand_iou"] = {k: (_iou(ch[k] > 0, hands[k] > 0) if (k in ch and k in hands) else
                               ("only_hts" if k in ch else ("only_hand_seg" if k in hands else "neither")))
                           for k in ("hand_L", "hand_R")}
    mc = IDX.map_channels(stem)
    out["map_nonzero"] = [bool(mc[i].any()) for i in range(mc.shape[0])]
    out["map_mass"] = [int(mc[i].sum()) for i in range(mc.shape[0])]
    return out


def main():
    global IDX, TOOL
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=16)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    fold = C.fold_a()
    IDX = G.HTSIndex(("train", "val"))
    seqs = {v: fr for v, fr, _ in C.phase_sequences(fold["train"] + fold["val"])}
    summary = {"task_id": "T-2026-10-31-grasp-pilot-probe", "unofficial": True,
               "function_sha256": C.sha256(Path(G.__file__)), "builder_sha256": C.sha256(Path(__file__)),
               "parts": {}}
    for part in ("train", "val"):
        tool = json.loads((C.DET_ANN_A / f"instances_{part}.json").read_text())
        imgs = {im["id"]: Path(im["file_name"]).stem for im in tool["images"]}
        TOOL = {}
        for a in tool["annotations"]:
            TOOL.setdefault(imgs[a["image_id"]], []).append(a)
        frames = [f for v in fold[part] for f in seqs[v]]
        tool_stems = set(imgs.values())
        with Pool(args.workers) as pool:
            rows = pool.map(per_frame, frames, chunksize=8)
        by = {r["stem"]: r for r in rows}
        g = np.stack([r["g"] for r in rows])
        flag = np.array([r["annotated"] for r in rows], np.float32)
        gp = out / f"g_{part}.npz"
        np.savez(gp, frame_ids=np.array(frames), x=g, flag=flag, names=np.array(G.G_NAMES))
        # 枠ごとの r（術具注釈のあるフレームの全枠）
        bs, bid, bcat, br, bann = [], [], [], [], []
        for s in sorted(tool_stems):
            r = by[s]
            for i, c, rr in zip(r["box_ids"], r["box_cats"], r["r"]):
                bs.append(s); bid.append(i); bcat.append(c); br.append(rr); bann.append(r["annotated"])
        bp = out / f"boxstate_{part}.npz"
        np.savez(bp, stems=np.array(bs), ann_ids=np.array(bid), cats=np.array(bcat), r=np.array(br),
                 annotated=np.array(bann))
        br = np.array(br)
        bann = np.array(bann)
        states = {}
        for tau in (0.05, 0.1, 0.2):
            q, s, over = G.box_state(br, tau)
            s = np.where(bann, s, 4)
            states[str(tau)] = {"counts": {G.STATE_NAMES[k]: int((s == k).sum()) for k in range(5)}, "sum_over_1": over}
        combos = collections.Counter(tuple(int(by[s]["has"][k]) for k in IDX.KINDS) for s in frames)
        ann_rows = [r for r in rows if r["annotated"]]
        grasped = {side: dict(collections.Counter(r["grasped"][side] for r in ann_rows).most_common())
                   for side in ("L", "R", "B")}
        ious = collections.defaultdict(list)
        for r in ann_rows:
            for cat, v in r["ht_tool_iou"]:
                ious[cat].append(v)
        def dist(vs):
            nn = [v for v in vs if v is not None]
            qs = np.quantile(nn, [0.1, 0.25, 0.5, 0.75, 0.9]).round(4).tolist() if nn else None
            return {"n": len(vs), "no_tool_instance": len(vs) - len(nn), "quantiles_10_25_50_75_90": qs,
                    "ge_0.5": int(sum(v >= 0.5 for v in nn)), "lt_0.1": int(sum(v < 0.1 for v in nn))}
        hand = {}
        for k in ("hand_L", "hand_R"):
            vals = [r["hand_iou"][k] for r in ann_rows]
            nums = [v for v in vals if isinstance(v, float)]
            hand[k] = {"both": len(nums), "quantiles_10_25_50_75_90": np.quantile(nums, [0.1, 0.25, 0.5, 0.75, 0.9]).round(4).tolist() if nums else None,
                       **{lab: int(sum(v == lab for v in vals)) for lab in ("only_hts", "only_hand_seg", "neither")}}
        tool_rows = [by[s] for s in sorted(tool_stems)]
        summary["parts"][part] = {
            "videos": C.assert_no_test(frames, f"build_signals:{part}"),
            "phase_frames": len(frames), "tool_frames": len(tool_stems), "tool_frames_not_in_phase": len(tool_stems - set(frames)),
            "g_file": str(gp), "g_sha256": C.sha256(gp), "g_annotated": int(flag.sum()),
            "g_mean_annotated": dict(zip(G.G_NAMES, g[flag > 0].mean(0).round(6).tolist())),
            "g_positive_rate_annotated": {G.G_NAMES[i]: float((g[flag > 0, i] > 0).mean()) for i in G.G_BINARY},
            "boxstate_file": str(bp), "boxstate_sha256": C.sha256(bp), "n_boxes": len(bs),
            "n_boxes_annotated": int(bann.sum()), "states_by_tau": states,
            "map_frames": len(tool_rows),
            "map_channel_nonzero_frames": dict(zip(G.MAP_CHANNELS, np.sum([r["map_nonzero"] for r in tool_rows], 0).tolist())),
            "map_channel_mass_px": dict(zip(G.MAP_CHANNELS, np.sum([r["map_mass"] for r in tool_rows], 0).tolist())),
            "map_any_nonzero_frames": int(sum(any(r["map_nonzero"]) for r in tool_rows)),
            "combos_hts_hand_tool": {"".join(map(str, k)): v for k, v in sorted(combos.items())},
            "caseC_grasped_tool_class": grasped,
            "E2_handtool_vs_toolseg_iou": {str(k): dist(v) for k, v in sorted(ious.items())},
            "E2_hand_hts_vs_handseg_iou": hand,
        }
        print(part, json.dumps({k: summary["parts"][part][k] for k in ("phase_frames", "g_annotated", "n_boxes", "states_by_tau")},
                               ensure_ascii=False))
    tool_seg = {}
    for part in ("train", "val"):
        d = json.loads((G.HTS / f"tool_seg/{part}.json").read_text())
        names = {c["id"]: c["name"] for c in d["categories"]}
        ci = collections.Counter(names[a["category_id"]] for a in d["annotations"])
        cf = collections.Counter(names[cat] for _, cat in {(a["image_id"], a["category_id"]) for a in d["annotations"]})
        tool_seg[part] = {n: {"instances": ci.get(n, 0), "frames": cf.get(n, 0)} for n in names.values()}
    summary["caseC_tool_seg_classes"] = tool_seg
    C.write_json(out / "summary.json", summary)


if __name__ == "__main__":
    main()
