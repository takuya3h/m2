"""Task E-1: 折り A の train 10 本の二分割を選ぶ（非公式 T-2026-10-18-stage2-pilot-folda）。

5 本ずつの分け方を全数（動画 01 を含む側を H1。C(9,4) = 126 通り）調べる。各半分 H について
d(H) = TV(工程のフレーム比率) + TV(術具の枠のクラス比率) を、train 10 本全体を基準に出す。
定義は scripts/analysis/a1_fold_table.py の profile / total_variation / Material.cost と同じ（基準だけ train 10 本）。
max(d(H1), d(H2)) が最小の分け方を選ぶ。同点は和の小さい方、それでも同点なら H1 の動画番号の辞書順。

材料は test の行を取り出さないように読む: 工程は train 10 本の CSV だけ（a1 の load_phase に動画の集合を渡す）、
術具は折り A の instances_train.json だけ。

    python scripts/stage2pilot/crossfit_split.py --out <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))

import a1_fold_table as a1  # noqa: E402

from stage2pilot import common as C  # noqa: E402


def material(train):
    phase = a1.load_phase(videos=set(train))
    blob = json.loads((C.DET_ANN_A / "instances_train.json").read_text())
    cat = {c["id"]: c["name"] for c in blob["categories"]}
    img_vid = {im["id"]: Path(im["file_name"]).parent.name for im in blob["images"]}
    tool = defaultdict(lambda: defaultdict(int))
    for x in blob["annotations"]:
        tool[img_vid[x["image_id"]]][cat[x["category_id"]]] += 1
    tool = {v: dict(c) for v, c in tool.items()}
    assert set(phase) == set(train) and set(tool) == set(train), (sorted(phase), sorted(tool))
    return phase, tool


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    train = tuple(sorted(C.fold_a()["train"]))
    C.assert_no_test(train, "crossfit_split")
    phase, tool = material(train)
    phases = tuple(sorted({p for c in phase.values() for p in c}))
    classes = tuple(sorted({k for c in tool.values() for k in c}))
    ref_p, ref_t = a1.profile(train, phase, phases), a1.profile(train, tool, classes)

    def d(h):
        return (a1.total_variation(a1.profile(h, phase, phases), ref_p)
                + a1.total_variation(a1.profile(h, tool, classes), ref_t))

    rows = []
    rest = [v for v in train if v != "01"]
    for combo in combinations(rest, 4):
        h1 = tuple(sorted(("01",) + combo))
        h2 = tuple(v for v in train if v not in h1)
        d1, d2 = d(h1), d(h2)
        rows.append({"H1": list(h1), "H2": list(h2), "d_H1": d1, "d_H2": d2, "max": max(d1, d2), "sum": d1 + d2})
    rows.sort(key=lambda r: (r["max"], r["sum"], r["H1"]))
    best = rows[0]
    res = {"task_id": C.TASK_ID, "train": list(train), "n_partitions": len(rows),
           "definition": "d(H) = TV_phase + TV_tool（a1_fold_table.profile / total_variation）。基準は train 10 本全体",
           "rule": "max(d(H1), d(H2)) 最小 → 和 最小 → H1 の辞書順",
           "phase_source": "data/annotations/egosurgery_phase の train 10 本の CSV（工程注釈の全フレーム）",
           "tool_source": "data/annotations/egosurgery_tool_folds/A/instances_train.json の枠",
           "phase_frames": {v: sum(phase[v].values()) for v in train},
           "tool_boxes": {v: sum(tool[v].values()) for v in train},
           "chosen": best, "top5": rows[:5], "ties_at_top": sum(1 for r in rows if r["max"] == best["max"])}
    C.write_json(a.out, res)
    print(json.dumps({"chosen": best, "top5": [(r["H1"], round(r["max"], 4), round(r["sum"], 4)) for r in rows[:5]],
                      "n": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
