"""Task C: 直した場合の上限の目安（SPEC §4.5。非公式 T-2026-11-22-dtower-class-error-breakdown）。

    .venv/bin/python .../c_fix.py [--targets T1_A,T2_A] [--controls-only] [--allow-manifest-test]

予測の全件（足切りなし）を五通りに直し、直す前と後のクラス別 AP・AP50（と AP75）と差を出す。直し方は一つずつ別々に当てる。
直す前の値は common.evaluate を同じ予測に通した値で、Task B の b/eval_<塔>_<Fold>.json と一致することを確かめる。

- 予測ごとの「クラスを問わず IoU が最大の GT」は、同じ画像の GT との IoU の最大（IoU 0.5 以上のときだけ）。
  同じ IoU の GT が複数あれば注釈の並びで先のもの（実行者の判断。件数を gt_ties として数える）
- (a) 重複を除く: (画像, その GT, 予測のクラス) が同じ予測のうち score 最大の一つだけを残す（同じ score なら保存の並びで先）。
  IoU 0.5 以上の GT を持たない予測は残す
- (b) クラスを直す: その GT を持つ予測のクラスを GT のクラスに書き換え、(a) の除き方を当てる
- (c) 枠を直す: 同じクラスの GT との最大の IoU が 0.1 以上 0.5 未満の予測の枠を、その GT の枠に置き換え、
  IoU 最大の GT を測り直してから (a) の除き方を当てる
- (d) 在否を直す: クラス c の GT が一つも無い画像から、クラス c の予測を除く
- (e) 工程で在り得ないクラスを除く: その Fold の train の注釈の画像で、工程 p の画像にクラス c の box が一度も無い組
  (p, c)（p は train の注釈の画像に一度でも現れる工程に限る）について、val の正解の工程が p の画像からクラス c の予測を除く。
  工程の正解は data/processed/phase_manifest（前回の予備測定の正解の腕と同じ出所。scripts/stage2pilot/common.py の
  phase_sequences、scripts/stage2pilot/phase_signals.py の p2f）。その Fold の train と val の動画の項目だけを使う。
  マニフェストの test.json が要る Fold は --allow-manifest-test が無ければ (e) を UNKNOWN にする

書くもの: c/fix_<塔>_<Fold>.json、c/fix_controls.json（完了判定 g の対照）。
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

FIXES = ["a", "b", "c", "d", "e"]
EMPTY = np.zeros(0, dtype=np.int64)


def nearest(G: dict, P: dict) -> dict:
    """予測ごとの、クラスを問わず IoU が最大の GT（0.5 以上）と、同じクラスの GT との最大の IoU とその GT。"""
    n = len(P["score"])
    bg = np.full(n, -1)
    ties = np.zeros(n, bool)
    smax = np.zeros(n)
    sidx = np.full(n, -1)
    gimg = C.by_image(G["image_id"])
    for img, pi in C.by_image(P["image_id"]).items():
        gi = gimg.get(img, EMPTY)
        if len(gi) == 0:
            continue
        M = C.iou(P["bbox"][pi], G["bbox"][gi])
        mx = M.max(1)
        arg = M.argmax(1)
        sel = mx >= C.IOU_MATCH
        bg[pi[sel]] = gi[arg[sel]]
        ties[pi] = sel & ((M == mx[:, None]).sum(1) > 1)
        same = G["category_id"][gi][None, :] == P["category_id"][pi][:, None]
        Ms = np.where(same, M, -1.0)
        sm = Ms.max(1)
        sa = Ms.argmax(1)
        has = sm >= 0
        smax[pi] = np.where(has, sm, 0.0)
        sidx[pi[has]] = gi[sa[has]]
    return {"bg": bg, "ties": ties, "smax": smax, "sidx": sidx}


def dedup_keep(P: dict, bg: np.ndarray) -> np.ndarray:
    keep = np.ones(len(P["score"]), bool)
    idx = np.flatnonzero(bg >= 0)
    idx = idx[np.argsort(-P["score"][idx], kind="mergesort")]
    seen = set()
    for i in idx:
        key = (int(P["image_id"][i]), int(bg[i]), int(P["category_id"][i]))
        if key in seen:
            keep[i] = False
        else:
            seen.add(key)
    return keep


def copy_of(P: dict) -> dict:
    return {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in P.items()}


def apply_fixes(G: dict, P: dict, phase_rule=None) -> dict:
    """五つの直し方を一つずつ当てた予測と、当てた件数を返す。phase_rule は (val の画像 → 工程, 除く組の集合) か None。"""
    near = nearest(G, P)
    out, info = {}, {"gt_ties_ge0.5": int(near["ties"].sum()), "preds": int(len(P["score"]))}
    ka = dedup_keep(P, near["bg"])
    out["a"] = C.subset(P, np.flatnonzero(ka))
    info["a_removed"] = int((~ka).sum())
    Pb = copy_of(P)
    sel = near["bg"] >= 0
    info["b_relabelled"] = int((Pb["category_id"][sel] != G["category_id"][near["bg"][sel]]).sum())
    Pb["category_id"][sel] = G["category_id"][near["bg"][sel]]
    kb = dedup_keep(Pb, near["bg"])
    out["b"] = C.subset(Pb, np.flatnonzero(kb))
    info["b_removed_after_relabel"] = int((~kb).sum())
    Pc = copy_of(P)
    selc = (near["smax"] >= C.IOU_NEAR) & (near["smax"] < C.IOU_MATCH) & (near["sidx"] >= 0)
    Pc["bbox"][selc] = G["bbox"][near["sidx"][selc]]
    info["c_boxes_replaced"] = int(selc.sum())
    near_c = nearest(G, Pc)
    kc = dedup_keep(Pc, near_c["bg"])
    out["c"] = C.subset(Pc, np.flatnonzero(kc))
    info["c_removed_after_replace"] = int((~kc).sum())
    present = set(zip(G["image_id"].tolist(), G["category_id"].tolist()))
    kd = np.array([(int(i), int(c)) in present for i, c in zip(P["image_id"], P["category_id"])], dtype=bool)
    out["d"] = C.subset(P, np.flatnonzero(kd))
    info["d_removed"] = int((~kd).sum())
    if phase_rule is None:
        out["e"] = None
    else:
        phase_of_img, impossible = phase_rule
        ke = np.array([(phase_of_img.get(int(i)), int(c)) not in impossible
                       for i, c in zip(P["image_id"], P["category_id"])], dtype=bool)
        out["e"] = C.subset(P, np.flatnonzero(ke))
        info["e_removed"] = int((~ke).sum())
    return {"preds": out, "info": info}


def needed_manifests(fold: str, F: dict) -> list[str]:
    """その Fold の train ∪ val の動画を含むマニフェスト（折り A は公式分割そのもの: conventions#folds）。"""
    need = set(F[fold]["train"]) | set(F[fold]["val"])
    return [part for part in ("train", "val", "test") if need & set(F["A"][part])]


def phase_maps(fold: str, F: dict, names: list[str]):
    """その Fold の train と val の動画のフレーム → 工程。マニフェストの test.json が要り、許されていなければ None。"""
    files = needed_manifests(fold, F)
    if "test" in files and not C.allow_manifest_test:
        return None, {"files_needed": files, "reason": "工程のマニフェストの test.json（公式の test の動画 04・05・07 の工程の注釈）"
                                                    "が要る。利用者の判断が出るまで開かない"}
    need = set(F[fold]["train"]) | set(F[fold]["val"])
    frame_phase, skipped = {}, {}
    for part in files:
        clips = C.read_json(C.MANIFEST / f"{part}.json", f"工程の正解（Fold {fold} の (e)）")["clips"]
        for clip in clips:
            if clip["video"] in need:
                for f in clip["frames"]:
                    frame_phase[f["frame"]] = int(f["label"])
            else:
                skipped[clip["video"]] = skipped.get(clip["video"], 0) + len(clip["frames"])
    vocab = C.read_json(C.MANIFEST / "phase_vocab.json", "工程の語彙", "record")
    phase_names = [k for k, _ in sorted(vocab.items(), key=lambda kv: kv[1])]
    return frame_phase, {"files": files, "videos_used": sorted(need), "videos_skipped_frames": skipped,
                         "phase_names": phase_names}


def phase_rule_for(fold: str, F: dict, names: list[str], val_ann: dict):
    frame_phase, info = phase_maps(fold, F, names)
    if frame_phase is None:
        return None, info
    tr = C.load_ann(fold, "train")
    n_phase = np.zeros(len(info["phase_names"]), dtype=np.int64)
    n_both = np.zeros((len(info["phase_names"]), len(names)), dtype=np.int64)
    present = {}
    for x in tr["annotations"]:
        present.setdefault(x["image_id"], set()).add(x["category_id"])
    no_phase_train = 0
    for im in tr["images"]:
        p = frame_phase.get(Path(im["file_name"]).stem)
        if p is None:
            no_phase_train += 1
            continue
        n_phase[p] += 1
        for c in present.get(im["id"], ()):
            n_both[p, c] += 1
    impossible = {(p, c) for p in range(len(n_phase)) if n_phase[p] > 0 for c in range(len(names)) if n_both[p, c] == 0}
    phase_of_img = {}
    for im in val_ann["images"]:
        p = frame_phase.get(Path(im["file_name"]).stem)
        if p is not None:
            phase_of_img[im["id"]] = p
    in_removed = {}
    for x in val_ann["annotations"]:
        if (phase_of_img.get(x["image_id"]), x["category_id"]) in impossible:
            in_removed[names[x["category_id"]]] = in_removed.get(names[x["category_id"]], 0) + 1
    info.update(val_gt_boxes_in_removed_pairs=in_removed)
    info.update(train_images=len(tr["images"]), train_images_without_phase=no_phase_train,
                val_images=len(val_ann["images"]), val_images_with_phase=len(phase_of_img),
                phases_in_train=[info["phase_names"][p] for p in range(len(n_phase)) if n_phase[p] > 0],
                phases_not_in_train=[info["phase_names"][p] for p in range(len(n_phase)) if n_phase[p] == 0],
                val_images_by_phase={info["phase_names"][p]: sum(1 for v in phase_of_img.values() if v == p)
                                     for p in range(len(n_phase))},
                n_phase_train=n_phase.tolist(), n_both_train=n_both.tolist(),
                removed_pairs=[[info["phase_names"][p], names[c]] for p, c in sorted(impossible)])
    return (phase_of_img, impossible), info


def diff_table(before: dict, after: dict) -> dict:
    rows = {}
    for c, b in before["per_class"].items():
        a = after["per_class"][c]
        rows[c] = {k: {"before": b[k], "after": a[k], "diff": a[k] - b[k]} for k in ("AP", "AP50", "AP75")}
    m = {}
    for key, mk in (("AP", "means"), ("AP50", "means50"), ("AP75", "means75")):
        m[key] = {g: {"before": before[mk][g], "after": after[mk][g], "diff": after[mk][g] - before[mk][g]}
                  for g in ("all", "signature", "negative", "other")}
    return {"per_class": rows, "means": m, "overall_AP": {"before": before["AP"], "after": after["AP"],
                                                            "diff": after["AP"] - before["AP"]}}


def strip(e: dict) -> dict:
    return {k: e[k] for k in ("AP", "AP50", "AP75", "per_class", "means", "means50", "means75", "detections")}


def same_values(x: dict, y: dict) -> bool:
    def eq(u, v):
        return (isinstance(u, float) and isinstance(v, float) and math.isnan(u) and math.isnan(v)) or u == v
    return eq(x["AP"], y["AP"]) and all(eq(x["per_class"][c][k], y["per_class"][c][k])
                                        for c in x["per_class"] for k in ("AP", "AP50", "AP75"))


def run_target(tower: str, fold: str, F: dict) -> dict:
    ann = C.load_ann(fold, "val")
    names = [c["name"] for c in sorted(ann["categories"], key=lambda c: c["id"])]
    gt = C.coco_from(ann)
    G = C.gt_arrays(ann)
    P = C.load_preds(tower, fold)
    before = C.evaluate(gt, P)
    taskb = json.loads((C.OUT / f"b/eval_{tower}_{fold}.json").read_text())
    rule, phase_info = phase_rule_for(fold, F, names, ann)
    fx = apply_fixes(G, P, rule)
    res = {"tower": tower, "fold": fold, "before": strip(before), "before_equals_taskB": same_values(before, taskb),
           "info": fx["info"], "phase": phase_info, "fixes": {}}
    after = {}
    for k in FIXES:
        if fx["preds"][k] is None:
            res["fixes"][k] = {"status": "UNKNOWN", "reason": phase_info.get("reason")}
            continue
        after[k] = C.evaluate(gt, fx["preds"][k])
        res["fixes"][k] = {"status": "measured", "after": strip(after[k]), **diff_table(before, after[k])}
    for k in ("b", "c"):
        if k in after:
            res["fixes"][f"{k}_minus_a"] = diff_table(after["a"], after[k])
    return res


def synth_dataset(images=4):
    """作り物の GT: 画像 4 枚、クラス 3、GT 7 個（互いに重ならない）。工程は画像 0・2 が 0、1・3 が 1。"""
    boxes = [(0, 0, [10, 10, 50, 50]), (0, 1, [200, 10, 40, 60]), (1, 2, [10, 200, 80, 40]), (1, 0, [300, 300, 30, 30]),
             (2, 1, [100, 100, 60, 60]), (3, 2, [400, 50, 50, 50]), (3, 0, [50, 400, 40, 40])]
    ds = {"images": [{"id": i, "file_name": f"99_1_{i:04d}.png", "width": 1000, "height": 1000} for i in range(images)],
          "categories": [{"id": k, "name": f"c{k}"} for k in range(3)],
          "annotations": [{"id": n + 1, "image_id": b[0], "category_id": b[1], "bbox": b[2], "area": b[2][2] * b[2][3],
                           "iscrowd": 0} for n, b in enumerate(boxes)]}
    phase = {0: 0, 1: 1, 2: 0, 3: 1}
    return ds, phase


def controls() -> dict:
    ds, phase = synth_dataset()
    gt = C.coco_from(ds)
    G = C.gt_arrays(ds)
    n = len(G["id"])
    base = {"image_id": G["image_id"].copy(), "category_id": G["category_id"].copy(), "bbox": G["bbox"].copy(),
            "score": np.linspace(0.9, 0.5, n)}
    # 工程の表: 作り物の GT そのものから作る（GT の組はすべて在り得る）
    seen = {(phase[int(i)], int(c)) for i, c in zip(G["image_id"], G["category_id"])}
    impossible = {(p, c) for p in (0, 1) for c in range(3) if (p, c) not in seen}

    def measure(P):
        before = C.evaluate(gt, P)
        fx = apply_fixes(G, P, (phase, impossible))
        return {k: diff_table(before, C.evaluate(gt, fx["preds"][k]))["means"]["AP"]["all"]["diff"] for k in FIXES}

    out = {"impossible_pairs": sorted(impossible)}
    out["gt_as_preds"] = measure(base)
    rot = copy_of(base)
    rot["category_id"] = (rot["category_id"] + 1) % 3
    out["class_rotated"] = measure(rot)
    extra = copy_of(base)
    extra["score"][:] = 0.5
    absent = [(0, 2), (2, 0), (2, 2)]  # 画像 0 に c2、画像 2 に c0・c2 の GT は無い
    for img, c in absent:
        extra["image_id"] = np.append(extra["image_id"], img)
        extra["category_id"] = np.append(extra["category_id"], c)
        extra["bbox"] = np.vstack([extra["bbox"], [700, 700, 50, 50]])
        extra["score"] = np.append(extra["score"], 0.9)
    out["absent_class_added"] = measure(extra)
    ph = copy_of(base)
    imp = sorted(impossible)[0]  # 工程 imp[0] の画像に在り得ないクラス imp[1] の予測を足す
    img = [i for i, p in phase.items() if p == imp[0]][0]
    ph["image_id"] = np.append(ph["image_id"], img)
    ph["category_id"] = np.append(ph["category_id"], imp[1])
    ph["bbox"] = np.vstack([ph["bbox"], [800, 800, 40, 40]])
    ph["score"] = np.append(ph["score"], 0.95)
    out["phase_impossible_added"] = measure(ph)
    z = out["gt_as_preds"]
    r = out["class_rotated"]
    x = out["absent_class_added"]
    out["pass"] = (all(abs(v) == 0 for v in z.values())
                   and r["b"] > 0 and all(abs(r[k]) == 0 for k in FIXES if k != "b")
                   and x["d"] > 0 and abs(x["c"]) == 0
                   and out["phase_impossible_added"]["e"] > 0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default=",".join(f"{t}_{f}" for t, f in C.TARGETS))
    ap.add_argument("--controls-only", action="store_true")
    ap.add_argument("--allow-manifest-test", action="store_true")
    a = ap.parse_args()
    C.allow_manifest_test = a.allow_manifest_test
    ctl = controls()
    C.write_json(C.OUT / "c/fix_controls.json", ctl)
    print("controls", json.dumps(ctl, ensure_ascii=False), flush=True)
    if a.controls_only:
        return
    F = C.folds()
    for key in a.targets.split(","):
        tower, fold = key.split("_")
        res = run_target(tower, fold, F)
        C.write_json(C.OUT / f"c/fix_{tower}_{fold}.json", res)
        brief = {k: (round(v["means"]["AP"]["all"]["diff"], 4) if v.get("status") == "measured" else v.get("status"))
                 for k, v in res["fixes"].items() if k in FIXES}
        print(key, "before_equals_taskB", res["before_equals_taskB"], "info", json.dumps(res["info"]),
              "mean AP diff", brief, flush=True)


if __name__ == "__main__":
    main()
