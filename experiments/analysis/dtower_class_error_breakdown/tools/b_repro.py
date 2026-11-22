"""Task B（G2）: 保存済みの予測から記録の値を再現する（非公式 T-2026-11-22-dtower-class-error-breakdown）。

    .venv/bin/python .../b_repro.py

対象の塔と Fold ごとに、保存済みの予測の全件と val の注釈から overall mAP・クラス別 AP・signature class の AP・
negative control の AP を計算し直し（common.evaluate。記録と同じ COCOeval）、記録と比べる。
記録: 塔 1 は frozen_towers.json（val_mAP・val_AP_target・val_AP_negative）と run の eval_val.json（AP・AP50・AP75・
クラス別 AP）、塔 2 は SPEC §1.1 の値・per_class_ap.json・pd_plain.json（AP50）。一致は小数第 4 位に丸めた値の一致。
計算し直した値（クラス別の AP・AP50・AP75 を含む）は b/eval_<塔>_<Fold>.json に置き、Task C の「直す前」に使う。
対照: 塔 1 の Fold A の予測の写しで、一つの画像の中の score の並びを逆にすると、比べが差を出す。
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def r4(x):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 4)


def compare(pairs: dict[str, tuple]) -> dict:
    rows, worst = {}, 0.0
    for key, (mine, rec) in pairs.items():
        both_nan = (mine is None or math.isnan(mine)) and (rec is None or (isinstance(rec, float) and math.isnan(rec)))
        if both_nan:
            rows[key] = {"mine": None, "record": None, "equal_4dp": True, "abs_diff": 0.0}
            continue
        d = abs(float(mine) - float(rec))
        worst = max(worst, d)
        rows[key] = {"mine": mine, "record": rec, "equal_4dp": r4(mine) == r4(rec), "abs_diff": d}
    return {"rows": rows, "all_equal_4dp": all(r["equal_4dp"] for r in rows.values()), "max_abs_diff": worst}


def records(tower: str, fold: str) -> dict:
    if tower == "T1":
        frozen = C.read_json(C.FROZEN, "凍結した塔の記録", "record")
        t = [x for x in frozen["towers"] if x["fold"] == fold][0]
        ev = C.read_json(C.RERUN_RUNS / C.t1_run(fold) / "eval_val.json", f"T1 Fold {fold} の評価の出力", "record")
        rec = {"AP": t["val_mAP"], "AP_eval_val_json": ev["AP"], "AP50": ev["AP50"], "AP75": ev["AP75"],
               "signature": t["val_AP_target"], "negative": t["val_AP_negative"]}
        per_class = ev["per_class_ap"]
    else:
        pc = C.read_json(C.T2_DIR / "per_class_ap.json", "T2 のクラス別 AP の記録", "record")
        plain = C.read_json(C.T2_PD_PLAIN, "T2 の塔単独の評価の記録", "record")["metrics"]
        rec = {"AP": C.T2_RECORD["AP"], "AP_pd_plain": plain["AP"], "AP50": plain["AP50"],
               "signature": C.T2_RECORD["target_AP"], "negative": C.T2_RECORD["control_AP"]}
        per_class = pc
    return {"scalars": rec, "per_class": per_class}


def pairs_of(mine: dict, rec: dict) -> dict:
    s = rec["scalars"]
    out = {"AP": (mine["AP"], s["AP"]), "AP50": (mine["AP50"], s["AP50"]),
           "signature": (mine["means"]["signature"], s["signature"]), "negative": (mine["means"]["negative"], s["negative"])}
    for k in ("AP_eval_val_json", "AP_pd_plain"):
        if k in s:
            out[k] = (mine["AP"], s[k])
    if "AP75" in s:
        out["AP75"] = (mine["AP75"], s["AP75"])
    for c, v in rec["per_class"].items():
        out[f"class:{c}"] = (mine["per_class"][c]["AP"], v)
    return out


def main():
    out = {"task_id": C.TASK_ID, "targets": {}}
    for tower, fold in C.TARGETS:
        gt = C.coco_from(C.load_ann(fold, "val"))
        P = C.load_preds(tower, fold)
        mine = C.evaluate(gt, P)
        C.write_json(C.OUT / f"b/eval_{tower}_{fold}.json", {"tower": tower, "fold": fold, **mine})
        cmp = compare(pairs_of(mine, records(tower, fold)))
        out["targets"][f"{tower}_{fold}"] = {"images": mine["images"], "detections": mine["detections"], **cmp,
                                             "missing_classes": mine["means"]["all_missing"]}
        print(tower, fold, "equal_4dp", cmp["all_equal_4dp"], "max_abs_diff", cmp["max_abs_diff"],
              "AP", round(mine["AP"], 7), "sig", round(mine["means"]["signature"], 7),
              "neg", round(mine["means"]["negative"], 7), "missing", mine["means"]["all_missing"], flush=True)
        if (tower, fold) == ("T1", "A"):
            # 対照 c: 一つの画像（id 0）の予測の score の並びを逆にした写し
            Q = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in P.items()}
            rows = np.flatnonzero(Q["image_id"] == 0)
            Q["score"][rows] = Q["score"][rows][::-1]
            ctl = C.evaluate(gt, Q)
            ccmp = compare(pairs_of(ctl, records(tower, fold)))
            out["control_score_reversed_in_one_image"] = {
                "image_id": 0, "predictions_changed": int(len(rows)), "all_equal_4dp": ccmp["all_equal_4dp"],
                "max_abs_diff": ccmp["max_abs_diff"],
                "rows_not_equal": [k for k, r in ccmp["rows"].items() if not r["equal_4dp"]],
                "abs_diff_AP": abs(ctl["AP"] - mine["AP"])}
            print("control", json.dumps(out["control_score_reversed_in_one_image"], ensure_ascii=False), flush=True)
    out["G2_pass"] = all(t["all_equal_4dp"] for t in out["targets"].values())
    out["max_abs_diff_over_all"] = max(t["max_abs_diff"] for t in out["targets"].values())
    C.write_json(C.OUT / "b/b_repro.json", out)
    print("G2_pass", out["G2_pass"], "max_abs_diff_over_all", out["max_abs_diff_over_all"])


if __name__ == "__main__":
    main()
