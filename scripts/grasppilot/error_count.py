"""検出塔の val の誤りの数え上げ（非公式 T-2026-10-31-grasp-pilot-probe、Task C-4）。

val の各画像で、検出塔の評価の後処理の出力（上位 300、確信度の下限なし）と正解の枠を、確信度の閾値 s* と IoU 0.5 で照らす。
    正しい   同じクラスで IoU 0.5 以上、確信度 s* 以上の検出がある
    取り違え それは無いが、別のクラスでその条件の検出がある
    見逃し   どちらも無い（s* = 0.0 の見逃しは four-new-types の K1 の見落としと同じ定義。xq_missed の kept_gt・iou_xywh を使う）
正解の枠の把持の状態 s(b) は build_signals の boxstate_val.npz の r から grasp_signals.box_state で作る（注釈の無いフレームは「注釈なし」）。

§8-f の空振りの確認: 検出を一つ消した写しで、その検出だけが覆っていた枠が見逃しに移ること、
正解の枠を確信度 1 の検出として足した写しで見逃しが 0 件になること。

    .venv/bin/python scripts/grasppilot/error_count.py --preds <json.gz> --boxstate <npz> --out <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grasppilot import grasp_signals as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402
from stage2pilot.xq_missed import iou_xywh, kept_gt  # noqa: E402

THRESHOLDS = (0.0, 0.1, 0.3, 0.5)
OUTCOMES = ("correct", "confused", "missed")


def outcomes(gt, dets, s_star):
    """gt: {img: [(ann_id, cat, xywh)]}、dets: {img: [result]} → {ann_id: 結果}。"""
    out = {}
    for img, boxes in gt.items():
        ds = [d for d in dets.get(img, []) if d["score"] >= s_star]
        if not boxes:
            continue
        if not ds:
            out.update({a: "missed" for a, _, _ in boxes})
            continue
        dbox = np.array([d["bbox"] for d in ds], float)
        dcat = np.array([d["category_id"] for d in ds])
        iou = iou_xywh(np.array([b for _, _, b in boxes], float), dbox)
        for (a, c, _), row in zip(boxes, iou):
            hit = row >= 0.5
            out[a] = "correct" if (hit & (dcat == c)).any() else ("confused" if (hit & (dcat != c)).any() else "missed")
    return out


def table(res, state, group, keys):
    t = {}
    for g in ("all", "target", "control", "other"):
        sel = [a for a in keys if g == "all" or group[a] == g]
        t[g] = {}
        for sname in G.STATE_NAMES:
            ids = [a for a in sel if state[a] == sname]
            n = len(ids)
            t[g][sname] = {"n": n, **{o: int(sum(res[a] == o for a in ids)) for o in OUTCOMES},
                           **{f"{o}_rate": (float(sum(res[a] == o for a in ids)) / n if n else None) for o in OUTCOMES}}
        held = [a for a in sel if state[a] in ("left", "right", "both")]
        err = [a for a in sel if res[a] != "correct"]
        held_err = [a for a in err if state[a] in ("left", "right", "both")]
        ann = [a for a in sel if state[a] != "no_annotation"]
        t[g]["summary"] = {"n_boxes": len(sel), "n_errors": len(err),
                           "held_share_of_errors": len(held_err) / len(err) if err else None,
                           "held_share_of_boxes": len(held) / len(sel) if sel else None,
                           "held_share_of_boxes_annotated": len(held) / len(ann) if ann else None,
                           "held_share_of_errors_annotated": (len(held_err) / len([a for a in err if state[a] != "no_annotation"])
                                                              if [a for a in err if state[a] != "no_annotation"] else None)}
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preds", required=True)
    ap.add_argument("--boxstate", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    raw = json.loads((C.DET_ANN_A / "instances_val.json").read_text())
    coco = {"images": {im["id"]: im for im in raw["images"]}, "annotations": raw["annotations"]}
    names = {c["id"]: c["name"] for c in raw["categories"]}
    videos = C.assert_no_test([Path(im["file_name"]).stem for im in raw["images"]], "error_count")
    gt = kept_gt(coco)
    results = M.load_results(a.preds)
    dets = {}
    for r in results:
        dets.setdefault(r["image_id"], []).append(r)
    groups = M.read_groups()
    cat_group = {cid: ("target" if n in groups["target"] else "control" if n in groups["control"] else "other")
                 for cid, n in names.items()}
    bs = np.load(a.boxstate)
    r_by = {int(i): r for i, r in zip(bs["ann_ids"], bs["r"])}
    ann_by = {int(i): bool(v) for i, v in zip(bs["ann_ids"], bs["annotated"])}
    keys = [aid for boxes in gt.values() for aid, _, _ in boxes]
    missing_state = [k for k in keys if k not in r_by]
    cat_of = {aid: c for boxes in gt.values() for aid, c, _ in boxes}
    group = {k: cat_group[cat_of[k]] for k in keys}
    out = {"task_id": "T-2026-10-31-grasp-pilot-probe", "unofficial": True, "preds": a.preds,
           "preds_sha256": C.sha256(a.preds), "boxstate": a.boxstate, "boxstate_sha256": C.sha256(a.boxstate),
           "videos": videos, "n_gt_kept": len(keys), "n_gt_without_state": len(missing_state), "groups": groups,
           "tables": {}}
    for tau in (0.05, 0.1, 0.2):
        rr = np.array([r_by[k] for k in keys])
        _, s, _ = G.box_state(rr, tau)
        state = {k: (G.STATE_NAMES[int(v)] if ann_by[k] else "no_annotation") for k, v in zip(keys, s)}
        for s_star in THRESHOLDS:
            if tau != 0.1 and s_star != 0.3:
                continue                                  # τ の併記は s* = 0.3 だけ（SPEC Task C-4）
            res = outcomes(gt, dets, s_star)
            out["tables"][f"tau{tau}_s{s_star}"] = table(res, state, group, keys)
    # §8-f の空振りの確認（τ = 0.1、s* = 0.0）
    res0 = outcomes(gt, dets, 0.0)
    victim = None
    for img, boxes in gt.items():
        for aid, c, b in boxes:
            same = [d for d in dets.get(img, []) if d["category_id"] == c]
            hits = [d for d in same if iou_xywh(np.array([b], float), np.array([d["bbox"]], float))[0, 0] >= 0.5]
            if len(hits) == 1:
                others = [d for d in dets.get(img, []) if d["category_id"] != c and
                          iou_xywh(np.array([b], float), np.array([d["bbox"]], float))[0, 0] >= 0.5]
                if not others:
                    victim = (img, aid, hits[0])
                    break
        if victim:
            break
    dets_drop = {k: [d for d in v if d is not victim[2]] for k, v in dets.items()}
    res_drop = outcomes(gt, dets_drop, 0.0)
    dets_add = {k: list(v) for k, v in dets.items()}
    for img, boxes in gt.items():
        for _, c, b in boxes:
            dets_add.setdefault(img, []).append({"image_id": img, "category_id": c, "bbox": list(b), "score": 1.0})
    res_add = outcomes(gt, dets_add, 0.0)
    out["positive_controls"] = {
        "victim_ann_id": victim[1], "victim_before": res0[victim[1]], "victim_after_drop": res_drop[victim[1]],
        "n_changed_by_drop": int(sum(res0[k] != res_drop[k] for k in keys)),
        "missed_before": int(sum(v == "missed" for v in res0.values())),
        "missed_with_gt_added": int(sum(v == "missed" for v in res_add.values())),
    }
    C.write_json(a.out, out)
    t = out["tables"]["tau0.1_s0.3"]["all"]
    print(json.dumps({"n_gt": len(keys), "no_state": len(missing_state), "summary_tau0.1_s0.3": t["summary"],
                      "pc": out["positive_controls"]}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
