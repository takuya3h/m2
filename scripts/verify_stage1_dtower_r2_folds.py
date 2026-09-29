#!/usr/bin/env python
"""折りごとの注釈が規約の折り表と一致することを照合する。

契約 T-2026-09-19-stage1-detector-towers-r2 / Task A-5、完了判定 b。

**画像の集合を動画 ID に戻してから比べる。** 注釈の `file_name` は
`<split>/<video>/<video>_<clip>_<frame>.jpg` の形なので、二つ目の要素が動画 ID である。
期待は `context/conventions.md#folds`（正本は `docs/stage0/A1_fold_table.md`）。

陰性対照: 折り A の test 動画を一本入れ替えた集合を作ると、対称差が 2 になることを示す。
**差 0 が出る照合が、差を出せることを一度見せる。**
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ANN = REPO / "data/annotations/egosurgery_tool_folds"

# context/conventions.md#folds の表。train はその折りの test と val を除いた 10 本。
EXPECTED = {
    "A": {"test": {"04", "05", "07"}, "val": {"09", "10"}},
    "B": {"test": {"01", "03", "14"}, "val": {"02", "08"}},
    "C": {"test": {"02", "08", "11"}, "val": {"06", "12"}},
    "D": {"test": {"06", "13", "15"}, "val": {"04", "05"}},
    "E": {"test": {"09", "10", "12"}, "val": {"07", "15"}},
}
ALL_VIDEOS = {f"{i:02d}" for i in range(1, 16)}


def videos_of(path: Path) -> set[str]:
    """注釈に現れる動画 ID の集合を返す。"""
    images = json.loads(path.read_text())["images"]
    return {img["file_name"].split("/")[1] for img in images}


def main() -> int:
    rows: list[dict] = []
    failures = 0
    for fold, expect in EXPECTED.items():
        want = {
            "test": expect["test"],
            "val": expect["val"],
            "train": ALL_VIDEOS - expect["test"] - expect["val"],
        }
        for split, wanted in want.items():
            got = videos_of(ANN / fold / f"instances_{split}.json")
            diff = wanted ^ got
            failures += bool(diff)
            rows.append({
                "fold": fold, "split": split,
                "expected": sorted(wanted), "observed": sorted(got),
                "symmetric_difference": sorted(diff), "n_diff": len(diff),
            })

    # 陰性対照。折り A の test から 1 本抜いて別の 1 本を入れると対称差は 2 になる。
    swapped = (EXPECTED["A"]["test"] - {"07"}) | {"11"}
    control_diff = swapped ^ videos_of(ANN / "A" / "instances_test.json")
    control = {
        "case": "折り A の test 動画を 07 から 11 へ一本入れ替える",
        "symmetric_difference": sorted(control_diff), "n_diff": len(control_diff),
        "expected_n_diff": 2, "passed": len(control_diff) == 2,
    }
    if not control["passed"]:
        failures += 1

    out = {"rows": rows, "negative_control": control, "n_failed": failures}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
