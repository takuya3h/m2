"""Task F-1: 学習と評価に通した動画の集合が、折り A の test 動画 04・05・07 と交わらないことを確かめる（完了判定 f）。

工程塔: manifest（phase_manifest_all_phase）の train・val の clip の video。
検出塔: 折り A の instances_train・instances_val の画像の file_name（`<split>/<video>/<frame>.jpg`）の video。
--selftest: 学習の集合に 04 を混ぜると共通が 1 になることを示す。

    python check_test_videos.py <out.json> [--selftest]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEST = {"04", "05", "07"}


def sets():
    man = ROOT / "data/processed/phase_manifest_all_phase"
    ann = ROOT / "data/annotations/egosurgery_tool_folds/A"
    out = {}
    for s in ("train", "val"):
        out[f"phase_{s}"] = sorted({c["video"] for c in json.loads((man / f"{s}.json").read_text())["clips"]})
        out[f"detector_{s}"] = sorted({i["file_name"].split("/")[1]
                                       for i in json.loads((ann / f"instances_{s}.json").read_text())["images"]})
    return out


def main():
    used = sets()
    if "--selftest" in sys.argv:
        used["phase_train"] = sorted(set(used["phase_train"]) | {"04"})
    res = {"test_videos": sorted(TEST), "used": used,
           "overlap": {k: sorted(set(v) & TEST) for k, v in used.items()}}
    res["n_overlap"] = len(set().union(*map(set, res["overlap"].values())))
    if "--selftest" in sys.argv:
        print(json.dumps({"n_overlap_with_04": res["n_overlap"]}))
        return
    Path(sys.argv[1]).write_text(json.dumps(res, indent=1))
    print(json.dumps(res))


if __name__ == "__main__":
    main()
