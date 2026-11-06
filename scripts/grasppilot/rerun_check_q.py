"""案 D の標的 q の照合（非公式 T-2026-11-06-grasp-pilot-d-rerun、Task B-1・B-5）。読むだけ。

目録 signals_manifest.json の ``D_q.CF_train`` の q と入れ替えの q について:
  1. sha256 が目録と一致するか。枠の数（32,272）・行の和の範囲・値の範囲が目録と一致するか
  2. ann_ids が折り A の train の注釈の枠と過不足なく対応するか（欠け 0・余り 0）。test の動画の注釈が混じっていないか
  3. 入れ替えの q: 規則（画像 id の昇順、画像ごとに rng.permutation、seed 42。目録の shuffle_rule）で q から作り直した表と一致するか。
     枠が一つの画像の数、元と同じ枠に戻った割合（全体・複数枠の画像だけ）。画像ごとに q の行の多重集合が保たれるか

    python scripts/grasppilot/rerun_check_q.py --out <json> [--q <npz> --shuffle <npz>]   # 後ろの二つは対照用に差し替える
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

M = Path(__file__).resolve().parents[2]
MANIFEST = M / "experiments/analysis/grasp_tower_rebuild/signals_manifest.json"
ANN = M / "data/annotations/egosurgery_tool_folds/A/instances_train.json"
TEST_VIDEOS = {"04", "05", "07"}


def sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def boxes_by_image(ann_path):
    d = json.loads(Path(ann_path).read_text())
    stems = {im["id"]: Path(im["file_name"]).stem for im in d["images"]}
    by: dict[int, list[int]] = {}
    for a in d["annotations"]:
        by.setdefault(a["image_id"], []).append(a["id"])
    videos = sorted({s.split("_")[0] for s in stems.values()})
    return by, videos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--q", default=None)
    ap.add_argument("--shuffle", default=None)
    ap.add_argument("--ann", default=str(ANN))
    a = ap.parse_args()
    man = json.loads(MANIFEST.read_text())["D_q"]["CF_train"]
    qp, sp = a.q or man["q"]["path"], a.shuffle or man["shuffle"]["path"]
    res = {"manifest": str(MANIFEST), "q_path": qp, "shuffle_path": sp, "ann": a.ann, "ann_sha256": sha(a.ann)}
    res["q_sha256"], res["shuffle_sha256"] = sha(qp), sha(sp)
    res["q_sha256_match"] = res["q_sha256"] == man["q"]["sha256"]
    res["shuffle_sha256_match"] = res["shuffle_sha256"] == man["shuffle"]["sha256"]

    try:
        z, zs = np.load(qp), np.load(sp)
        z["ann_ids"], zs["ann_ids"]
    except Exception as e:  # 壊れた写しは読めない。読めなかったこと自体を結果に残して落とす
        res.update(ok=False, load_error=f"{type(e).__name__}: {e}"[:200])
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
        print(json.dumps(res, ensure_ascii=False, indent=1))
        raise SystemExit(1)
    ids, q = z["ann_ids"].astype(np.int64), z["q"].astype(np.float64)
    ids_s, qs = zs["ann_ids"].astype(np.int64), zs["q"].astype(np.float64)
    res["keys"] = {"q": sorted(z.files), "shuffle": sorted(zs.files)}
    res["dtype"] = {"q": str(z["q"].dtype), "shuffle": str(zs["q"].dtype)}
    res["shape"] = {"q": list(q.shape), "shuffle": list(qs.shape)}
    rs = q.sum(1)
    res["boxes"] = int(len(ids))
    res["boxes_match"] = res["boxes"] == man["q"]["boxes"] == int(len(ids_s)) == man["shuffle"]["boxes"]
    res["rowsum_range"] = [float(rs.min()), float(rs.max())]
    res["rowsum_range_manifest"] = man["q"]["rowsum_range"]
    res["rowsum_range_match"] = bool(np.allclose(res["rowsum_range"], man["q"]["rowsum_range"], atol=1e-6))
    res["value_range"] = [float(q.min()), float(q.max())]
    res["value_range_manifest"] = man["q"]["range"]
    res["value_range_match"] = bool(np.allclose(res["value_range"], man["q"]["range"], atol=1e-6))
    res["ids_ascending"] = bool(np.all(np.diff(ids) > 0))
    res["ids_equal_shuffle_ids"] = bool(np.array_equal(ids, ids_s))
    res["rowsum_range_shuffle"] = [float(qs.sum(1).min()), float(qs.sum(1).max())]

    by, videos = boxes_by_image(a.ann)
    want = {i for v in by.values() for i in v}
    have = set(ids.tolist())
    res["ann_videos"] = videos
    res["test_videos_in_ann"] = sorted(set(videos) & TEST_VIDEOS)
    res["n_ann_boxes"] = len(want)
    res["missing_in_q"] = len(want - have)
    res["extra_in_q"] = len(have - want)

    if res["missing_in_q"] or res["extra_in_q"]:  # 対応が崩れていれば作り直しは意味が無い
        res.update(ok=False, shuffle_rebuilt_equal=None)
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
        print(json.dumps({k: res[k] for k in ("ok", "missing_in_q", "extra_in_q")}))
        raise SystemExit(1)
    # 入れ替えの作り直し（規則: 画像 id の昇順、画像ごとに rng.permutation、seed 42）
    row = {int(x): i for i, x in enumerate(ids)}
    rng = np.random.default_rng(42)
    out_ids, out_q = [], []
    n_single_img = n_same = n_total = n_same_multi = n_multi = 0
    multiset_ok = True
    for img in sorted(by):
        boxes = by[img]
        n = len(boxes)
        perm = rng.permutation(n)
        if n == 1:
            n_single_img += 1
        got = []
        for k, b in enumerate(boxes):
            src = boxes[int(perm[k])]
            out_ids.append(b)
            out_q.append(q[row[src]])
            got.append(tuple(np.round(q[row[src]], 6)))
            same = src == b
            n_same += same
            n_total += 1
            if n > 1:
                n_multi += 1
                n_same_multi += same
        orig = sorted(tuple(np.round(q[row[b]], 6)) for b in boxes)
        multiset_ok &= orig == sorted(got)
    out_ids, out_q = np.array(out_ids), np.array(out_q)
    o = np.argsort(out_ids)
    res["shuffle_rebuilt_ids_equal"] = bool(np.array_equal(out_ids[o], ids_s))
    res["shuffle_rebuilt_max_abs_diff"] = float(np.abs(out_q[o] - qs).max()) if len(out_ids) == len(ids_s) else None
    res["shuffle_rebuilt_equal"] = bool(res["shuffle_rebuilt_ids_equal"] and res["shuffle_rebuilt_max_abs_diff"] is not None
                                        and res["shuffle_rebuilt_max_abs_diff"] < 1e-6)
    res["n_images"] = len(by)
    res["n_single_box_images"] = n_single_img
    res["same_box_fraction_all"] = n_same / n_total
    res["same_box_fraction_multi_box_images"] = (n_same_multi / n_multi) if n_multi else None
    res["n_boxes_in_multi_box_images"] = n_multi
    res["per_image_multiset_preserved"] = bool(multiset_ok)
    # 作った表そのものの行が元と同じ値に戻る割合（同じ値の行が複数あると並べ替えでも同じになるので、上の「同じ枠に戻った」と区別する）
    res["shuffle_row_equal_to_original_fraction"] = float(np.mean(np.all(np.abs(qs - q[np.array([row[int(i)] for i in ids_s])]) < 1e-9, axis=1)))
    res["ok"] = bool(res["q_sha256_match"] and res["shuffle_sha256_match"] and res["boxes_match"] and res["rowsum_range_match"]
                     and res["value_range_match"] and res["missing_in_q"] == 0 and res["extra_in_q"] == 0
                     and not res["test_videos_in_ann"] and res["shuffle_rebuilt_equal"] and res["per_image_multiset_preserved"])
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: res[k] for k in res if k not in ("keys",)}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
