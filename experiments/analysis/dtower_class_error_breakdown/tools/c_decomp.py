"""Task C: GT の側の分解・取り違えの表・予測の側の分解（SPEC §4.2〜§4.4。非公式 T-2026-11-22-dtower-class-error-breakdown）。

    .venv/bin/python .../c_decomp.py [--targets T1_A,T2_A] [--controls-only]

score 0.05 以上の予測だけを使う。IoU は COCO の bbox の IoU（common.iou）。

GT の側（§4.2）: GT の box を一つずつ 正解 / 取り違え / 位置のずれ / 見落とし に分ける。
- 読み 1（A6 の字面）: クラスを問わず IoU が最大の予測を対応させる。IoU が同じ予測が複数あれば score が最大のもの、
  それも同じなら予測の保存の並びで先のもの（この最後の決め方は実行者の判断。件数を score_tie として数える）
- 読み 2（同じクラスを優先）: IoU 0.5 以上の予測に同じクラスが一つでもあれば正解。無ければ IoU 0.5 以上で score 最大のもの
- 最大の IoU が 0.1 以上 0.5 未満なら位置のずれ、0.1 未満（予測が無い場合を含む）なら見落とし（二つの読みで同じ）
取り違えの表（§4.3）: GT のクラス × 対応する予測のクラスの件数（読みごと）と、行ごとの相手の上位。
予測の側（§4.4）: クラスごとに score の高い順に同じクラスの GT と IoU 0.5 以上で一対一に対応させ（COCOeval の
evaluateImg と同じ選び方: 未対応の GT のうち IoU が最大のもの、同じ IoU なら後の GT）、対応しなかった予測を
重複 → 取り違え → 位置のずれ → 背景 → その他 の順で最初に当たった区分に入れる。取り違えの相手は IoU が最大の
別のクラスの GT のクラス（同じ IoU なら先の GT）。

書くもの: c/decomp_<塔>_<Fold>.json、c/decomp_controls.json（完了判定 d・e の対照）。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

GT_CATS = ["correct", "confusion", "localization", "missed"]
PRED_CATS = ["hit", "duplicate", "confusion", "localization", "background", "other"]
EMPTY = np.zeros(0, dtype=np.int64)


def gt_side(G: dict, P: dict, n_cls: int) -> dict:
    n = len(G["id"])
    r1 = np.full(n, -1)
    r2 = np.full(n, -1)
    p1 = np.full(n, -1)  # 読み 1 の対応する予測のクラス（IoU 0.5 以上のとき）
    p2 = np.full(n, -1)
    tie_any = np.zeros(n, bool)
    tie_05 = np.zeros(n, bool)
    tie_05_diff = np.zeros(n, bool)
    score_tie = np.zeros(n, bool)
    max_iou = np.zeros(n)
    gimg, pimg = C.by_image(G["image_id"]), C.by_image(P["image_id"])
    for img, gi in gimg.items():
        pi = pimg.get(img, EMPTY)
        M = C.iou(P["bbox"][pi], G["bbox"][gi])
        for j, g in enumerate(gi):
            if len(pi) == 0:
                r1[g] = r2[g] = 3
                continue
            col = M[:, j]
            mx = col.max()
            max_iou[g] = mx
            cand = np.flatnonzero(col == mx)
            tie_any[g] = mx > 0 and len(cand) > 1
            if mx < C.IOU_NEAR:
                r1[g] = r2[g] = 3
                continue
            if mx < C.IOU_MATCH:
                r1[g] = r2[g] = 2
                continue
            gc = G["category_id"][g]
            sc = P["score"][pi[cand]]
            best = cand[np.flatnonzero(sc == sc.max())]
            pick = best[0]
            cls = P["category_id"][pi[pick]]
            tie_05[g] = len(cand) > 1
            tie_05_diff[g] = len(set(P["category_id"][pi[cand]].tolist())) > 1
            score_tie[g] = len(best) > 1
            r1[g], p1[g] = (0, cls) if cls == gc else (1, cls)
            ge = np.flatnonzero(col >= C.IOU_MATCH)
            if (P["category_id"][pi[ge]] == gc).any():
                r2[g], p2[g] = 0, gc
            else:
                s2 = P["score"][pi[ge]]
                r2[g], p2[g] = 1, P["category_id"][pi[ge[int(np.argmax(s2))]]]
    assert (r1 >= 0).all() and (r2 >= 0).all()
    return {"r1": r1, "r2": r2, "p1": p1, "p2": p2, "tie_any": tie_any, "tie_05": tie_05,
            "tie_05_diff": tie_05_diff, "score_tie": score_tie, "max_iou": max_iou}


def pred_side(G: dict, P: dict) -> dict:
    n = len(P["score"])
    cat = np.full(n, -1)
    partner = np.full(n, -1)
    gimg, pimg = C.by_image(G["image_id"]), C.by_image(P["image_id"])
    for img, pi in pimg.items():
        gi = gimg.get(img, EMPTY)
        Mall = C.iou(P["bbox"][pi], G["bbox"][gi])
        gcls = G["category_id"][gi]
        pcls = P["category_id"][pi]
        for c in np.unique(pcls):
            rows = np.flatnonzero(pcls == c)
            rows = rows[np.argsort(-P["score"][pi[rows]], kind="mergesort")]
            cols = np.flatnonzero(gcls == c)
            taken = np.zeros(len(cols), bool)
            for r in rows:
                best, thr = -1, min(C.IOU_MATCH, 1 - 1e-10)
                for k, g in enumerate(cols):
                    if taken[k] or Mall[r, g] < thr:
                        continue
                    thr, best = Mall[r, g], k
                if best >= 0:
                    taken[best] = True
                    cat[pi[r]] = 0
                    continue
                same = Mall[r, cols] if len(cols) else np.zeros(0)
                oth_cols = np.flatnonzero(gcls != c)
                oth = Mall[r, oth_cols] if len(oth_cols) else np.zeros(0)
                if len(same) and same.max() >= C.IOU_MATCH:
                    cat[pi[r]] = 1
                elif len(oth) and oth.max() >= C.IOU_MATCH:
                    cat[pi[r]] = 2
                    partner[pi[r]] = gcls[oth_cols[int(np.argmax(oth))]]
                elif len(same) and C.IOU_NEAR <= same.max() < C.IOU_MATCH:
                    cat[pi[r]] = 3
                elif len(gi) == 0 or Mall[r].max() < C.IOU_NEAR:
                    cat[pi[r]] = 4
                else:
                    cat[pi[r]] = 5
    assert (cat >= 0).all()
    return {"cat": cat, "partner": partner}


def summarize(G: dict, P: dict, names: list[str], gs: dict, ps: dict) -> dict:
    n_cls = len(names)
    out = {"n_gt": int(len(G["id"])), "n_pred_ge_0.05": int(len(P["score"])), "classes": {}, "confusion": {},
           "top_partners": {}}
    for key in ("r1", "r2"):
        mat = np.zeros((n_cls, n_cls), dtype=np.int64)
        part = gs["p1" if key == "r1" else "p2"]
        for g in np.flatnonzero(gs[key] == 1):
            mat[G["category_id"][g], part[g]] += 1
        out["confusion"][key] = mat.tolist()
        tops = {}
        for c in range(n_cls):
            tot = int(mat[c].sum())
            order = [k for k in np.argsort(-mat[c], kind="mergesort") if mat[c, k] > 0]
            tops[names[c]] = [{"class": names[k], "count": int(mat[c, k]), "share": mat[c, k] / tot} for k in order]
        out["top_partners"][key] = tops
    for c in range(n_cls):
        gsel = G["category_id"] == c
        psel = P["category_id"] == c
        row = {"n_gt": int(gsel.sum()), "n_pred": int(psel.sum())}
        for key in ("r1", "r2"):
            row[key] = {name: int(((gs[key] == k) & gsel).sum()) for k, name in enumerate(GT_CATS)}
            row[f"{key}_sum_ok"] = sum(row[key].values()) == row["n_gt"]
            row[f"{key}_confusion_row_sum_ok"] = sum(out["confusion"][key][c]) == row[key]["confusion"]
        row["r1_ties"] = {"max_iou_gt0": int((gs["tie_any"] & gsel).sum()), "max_iou_ge0.5": int((gs["tie_05"] & gsel).sum()),
                          "max_iou_ge0.5_classes_differ": int((gs["tie_05_diff"] & gsel).sum()),
                          "score_also_tied": int((gs["score_tie"] & gsel).sum())}
        pc = ps["cat"][psel]
        sc = P["score"][psel]
        row["pred"] = {name: int((pc == k).sum()) for k, name in enumerate(PRED_CATS)}
        row["pred_median_score"] = {name: (float(np.median(sc[pc == k])) if (pc == k).any() else None)
                                    for k, name in enumerate(PRED_CATS)}
        row["pred_sum_ok"] = sum(row["pred"].values()) == row["n_pred"]
        pp = ps["partner"][psel][pc == 2]
        row["pred_confusion_partner"] = {names[k]: int((pp == k).sum()) for k in range(n_cls) if (pp == k).any()}
        out["classes"][names[c]] = row
    out["all_sums_ok"] = all(r["r1_sum_ok"] and r["r2_sum_ok"] and r["pred_sum_ok"] and r["r1_confusion_row_sum_ok"]
                             and r["r2_confusion_row_sum_ok"] for r in out["classes"].values())
    out["totals"] = {key: {name: int((gs[key] == k).sum()) for k, name in enumerate(GT_CATS)} for key in ("r1", "r2")}
    out["totals"]["pred"] = {name: int((ps["cat"] == k).sum()) for k, name in enumerate(PRED_CATS)}
    return out


def run(G: dict, P: dict, names: list[str]) -> dict:
    keep = np.flatnonzero(P["score"] >= C.SCORE_MIN)
    Pf = C.subset(P, keep)
    gs = gt_side(G, Pf, len(names))
    ps = pred_side(G, Pf)
    return summarize(G, Pf, names, gs, ps)


def synth_gt():
    """作り物: 画像 3 枚、クラス 0〜2 の GT が 5 個（互いに重ならない）。"""
    boxes = [(0, 0, [10, 10, 50, 50]), (0, 1, [200, 10, 40, 60]), (1, 2, [10, 200, 80, 40]),
             (1, 0, [300, 300, 30, 30]), (2, 1, [100, 100, 60, 60])]
    G = {"id": np.arange(1, 6, dtype=np.int64), "image_id": np.array([b[0] for b in boxes], dtype=np.int64),
         "category_id": np.array([b[1] for b in boxes], dtype=np.int64),
         "bbox": np.array([b[2] for b in boxes], dtype=np.float64)}
    return G


def synth_preds(G, edit=None):
    P = {"image_id": G["image_id"].copy(), "category_id": G["category_id"].copy(), "bbox": G["bbox"].copy(),
         "score": np.linspace(0.9, 0.5, len(G["id"]))}
    if edit:
        P = edit(P)
    return P


def controls() -> dict:
    names = ["c0", "c1", "c2"]
    G = synth_gt()

    def change_class(P):
        P["category_id"][1] = 2
        return P

    def shift(P):
        P["bbox"][2] = P["bbox"][2] + np.array([60.0, 0, 0, 0])  # 幅 80 を 60 ずらす: IoU = 20/140 ≈ 0.14
        return P

    def remove(P):
        return C.subset(P, np.array([0, 1, 2, 4]))

    def dup(P):
        Q = C.subset(P, np.array([0, 1, 2, 3, 4, 0]))
        Q["score"][-1] = 0.3
        return Q

    def far(P):
        Q = C.subset(P, np.array([0, 1, 2, 3, 4, 4]))
        Q["bbox"][-1] = [900, 900, 20, 20]
        Q["score"][-1] = 0.6
        return Q

    out = {}
    for name, edit in (("identical", None), ("class_changed", change_class), ("box_shifted", shift),
                       ("pred_removed", remove), ("duplicate_added", dup), ("far_pred_added", far)):
        s = run(G, synth_preds(G, edit), names)
        out[name] = {"r1": s["totals"]["r1"], "r2": s["totals"]["r2"], "pred": s["totals"]["pred"],
                     "sums_ok": s["all_sums_ok"]}
    t = out
    out["pass"] = (t["identical"]["r1"]["correct"] == 5 and t["identical"]["r2"]["correct"] == 5
                   and t["identical"]["pred"]["hit"] == 5
                   and t["class_changed"]["r1"]["confusion"] == 1 and t["class_changed"]["r2"]["confusion"] == 1
                   and t["box_shifted"]["r1"]["localization"] == 1 and t["box_shifted"]["r2"]["localization"] == 1
                   and t["pred_removed"]["r1"]["missed"] == 1 and t["pred_removed"]["r2"]["missed"] == 1
                   and t["duplicate_added"]["pred"]["duplicate"] == 1
                   and t["far_pred_added"]["pred"]["background"] == 1
                   and all(v["sums_ok"] for k, v in t.items() if isinstance(v, dict)))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", default=",".join(f"{t}_{f}" for t, f in C.TARGETS))
    ap.add_argument("--controls-only", action="store_true")
    a = ap.parse_args()
    ctl = controls()
    C.write_json(C.OUT / "c/decomp_controls.json", ctl)
    print("controls pass", ctl["pass"], flush=True)
    if a.controls_only:
        return
    for key in a.targets.split(","):
        tower, fold = key.split("_")
        ann = C.load_ann(fold, "val")
        names = [c["name"] for c in sorted(ann["categories"], key=lambda c: c["id"])]
        assert [c["id"] for c in sorted(ann["categories"], key=lambda c: c["id"])] == list(range(len(names)))
        G = C.gt_arrays(ann)
        P = C.load_preds(tower, fold)
        s = run(G, P, names)
        s.update(tower=tower, fold=fold, class_names=names)
        C.write_json(C.OUT / f"c/decomp_{tower}_{fold}.json", s)
        print(key, "sums_ok", s["all_sums_ok"], "n_gt", s["n_gt"], "n_pred", s["n_pred_ge_0.05"],
              json.dumps(s["totals"]), flush=True)


if __name__ == "__main__":
    main()
