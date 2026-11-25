"""Task C: クラス別の AP・AP50・AP75 と、Fold・動画ごとの表（SPEC §4.6。非公式 T-2026-11-22-dtower-class-error-breakdown）。

    .venv/bin/python .../c_tables.py

- Fold ごと・クラスごとに、train の box の数・train でそのクラスが写る動画の数・val の box の数・val でそのクラスが
  写る動画の数・AP・AP50（AP・AP50・AP75 は Task B の b/eval_<塔>_<Fold>.json）
- box の数は注釈の並びの数え上げと、pycocotools の索引（getAnnIds）の数え上げの二通りで出して比べる
- 注釈の画像の動画の集合を、正本 docs/stage0/A1_fold_table.md と conventions#folds の表の両方と比べる
- 動画ごとのクラス別 AP・AP50 を common.evaluate（その動画の画像だけ）で出す。塔 1 は eval_val.per_video.json の
  クラス別 AP と比べる
- 対照: 注釈を一つ除いた写しで数が 1 減る。別の Fold の動画の画像を混ぜた写しで動画の集合が食い違う。
  AP50 ≥ AP を全クラスで確かめ、枠を一律に 8 px ずらした写し（塔 1 の Fold A）で AP75 が下がる

書くもの: c/tables.json。
"""
from __future__ import annotations

import copy
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def conventions_folds() -> dict:
    text = C.read_bytes(C.CONVENTIONS, "conventions#folds", "record").decode()
    m = re.search(r'<a id="folds"></a>\n(.*?)(?=<a id="|\Z)', text, re.S)
    out = {}
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 3 and cells[0] in list("ABCDE"):
            test, val = (re.findall(r"\b\d{2}\b", c) for c in cells[1:])
            train = [f"{i:02d}" for i in range(1, 16) if f"{i:02d}" not in set(test) | set(val)]
            out[cells[0]] = {"test": test, "val": val, "train": train}
    assert sorted(out) == list("ABCDE"), out
    return out


def counts(ann: dict, names: list[str]) -> dict:
    img_video = {im["id"]: C.video_of(im["file_name"]) for im in ann["images"]}
    box = Counter(x["category_id"] for x in ann["annotations"])
    vids = {}
    for x in ann["annotations"]:
        vids.setdefault(x["category_id"], set()).add(img_video[x["image_id"]])
    coco = C.coco_from(copy.deepcopy(ann))
    index = {c: len(coco.getAnnIds(catIds=[c])) for c in range(len(names))}
    return {"boxes": {names[c]: int(box.get(c, 0)) for c in range(len(names))},
            "videos": {names[c]: len(vids.get(c, ())) for c in range(len(names))},
            "boxes_by_index": {names[c]: index[c] for c in range(len(names))},
            "video_set": sorted(set(img_video.values())), "images": len(ann["images"]),
            "annotations": len(ann["annotations"])}


def main():
    F = C.folds()
    CF = conventions_folds()
    out = {"task_id": C.TASK_ID, "folds": {}, "targets": {}, "controls": {}}
    anns = {}
    for fold in "ABCDE":
        tr, va = C.load_ann(fold, "train"), C.load_ann(fold, "val")
        anns[fold] = va
        names = [c["name"] for c in sorted(va["categories"], key=lambda c: c["id"])]
        ct, cv = counts(tr, names), counts(va, names)
        out["folds"][fold] = {
            "train": ct, "val": cv,
            "train_videos_match_fold_table": ct["video_set"] == sorted(F[fold]["train"]) == sorted(CF[fold]["train"]),
            "val_videos_match_fold_table": cv["video_set"] == sorted(F[fold]["val"]) == sorted(CF[fold]["val"]),
            "test_overlap": sorted(set(ct["video_set"] + cv["video_set"]) & set(F[fold]["test"])),
            "counts_match_index": ct["boxes"] == ct["boxes_by_index"] and cv["boxes"] == cv["boxes_by_index"]}
        if fold == "A":
            # 対照 h: 注釈を一つ除いた写し、別の Fold の動画（B の val の 02）の画像を混ぜた写し
            drop = copy.deepcopy(va)
            removed = drop["annotations"].pop(0)
            cd = counts(drop, names)
            mix = copy.deepcopy(va)
            mix["images"].append({"id": 10 ** 6, "file_name": "02_1_0000.png", "width": 1, "height": 1})
            cm = counts(mix, names)
            out["controls"]["h"] = {
                "removed_class": names[removed["category_id"]],
                "count_before": cv["boxes"][names[removed["category_id"]]],
                "count_after": cd["boxes"][names[removed["category_id"]]],
                "mixed_video_set": cm["video_set"], "mixed_matches_fold_table": cm["video_set"] == sorted(F[fold]["val"])}
    for tower, fold in C.TARGETS:
        ev = json.loads((C.OUT / f"b/eval_{tower}_{fold}.json").read_text())
        gt = C.coco_from(anns[fold])
        P = C.load_preds(tower, fold)
        by_video = {}
        for im in anns[fold]["images"]:
            by_video.setdefault(C.video_of(im["file_name"]), []).append(im["id"])
        per_video = {}
        for v, ids in sorted(by_video.items()):
            keep = np.flatnonzero(np.isin(P["image_id"], ids))
            e = C.evaluate(gt, C.subset(P, keep), ids)
            per_video[v] = {"images": len(ids), "AP": e["AP"],
                            "per_class": {c: {"AP": x["AP"], "AP50": x["AP50"]} for c, x in e["per_class"].items()}}
        row = {"per_class": ev["per_class"], "means": ev["means"], "means50": ev["means50"], "means75": ev["means75"],
               "per_video": per_video,
               "AP50_ge_AP_all_classes": all(x["AP50"] >= x["AP"] for x in ev["per_class"].values() if not math.isnan(x["AP"]))}
        if tower == "T1":
            rec = C.read_json(C.RERUN_RUNS / C.t1_run(fold) / "eval_val.per_video.json", f"T1 Fold {fold} の動画ごとの記録",
                              "record")
            worst, compared = 0.0, 0
            for v, x in per_video.items():
                r = rec["per_video"][v]
                worst = max(worst, abs(x["AP"] - r["AP"]))
                compared += 1
                for c, y in x["per_class"].items():
                    rc = r["per_class_ap"][c]
                    if rc is None or math.isnan(y["AP"]):
                        assert rc is None and math.isnan(y["AP"]), (v, c, rc, y)
                        continue
                    worst = max(worst, abs(y["AP"] - rc))
                    compared += 1
            row["per_video_vs_record"] = {"values_compared": compared, "max_abs_diff": worst}
        else:
            rec = C.read_json(C.T2_PD_PLAIN, "T2 の動画ごとの記録", "record")["metrics"]["per_video_AP"]
            row["per_video_vs_record"] = {"values_compared": len(rec),
                                          "max_abs_diff": max(abs(per_video[v]["AP"] - rec[v]) for v in rec)}
        out["targets"][f"{tower}_{fold}"] = row
        print(tower, fold, "per_video_vs_record", row["per_video_vs_record"], "AP50>=AP", row["AP50_ge_AP_all_classes"],
              flush=True)
        if (tower, fold) == ("T1", "A"):
            S = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in P.items()}
            S["bbox"][:, 0] += 8.0
            es = C.evaluate(gt, S)
            out["controls"]["f"] = {"shift_px": 8.0, "AP75_mean_before": ev["means75"]["all"],
                                    "AP75_mean_after": es["means75"]["all"],
                                    "AP75_lower_classes": sum(es["per_class"][c]["AP75"] < ev["per_class"][c]["AP75"]
                                                              for c in ev["per_class"] if not math.isnan(ev["per_class"][c]["AP75"])),
                                    "classes": sum(not math.isnan(x["AP75"]) for x in ev["per_class"].values())}
    for fold, f in out["folds"].items():
        print(fold, "train/val videos match", f["train_videos_match_fold_table"], f["val_videos_match_fold_table"],
              "test_overlap", f["test_overlap"], "counts_match_index", f["counts_match_index"])
    print("controls", json.dumps(out["controls"], ensure_ascii=False))
    C.write_json(C.OUT / "c/tables.json", out)


if __name__ == "__main__":
    main()
