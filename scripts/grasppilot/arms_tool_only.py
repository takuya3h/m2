"""術具だけの対照の送り手の信号（非公式 T-2026-11-06-grasp-pilot-arms、SPEC §3.3・Task B-4）。本体の .venv。

案 B の予測-noCF の 5 チャネル m（目録の B_m pred_noCF の地図。チャネルの並びは grasp_signals.MAP_CHANNELS =
tool_L, tool_R, tool_B, hand_L, hand_R）から、器具の 3 チャネルの画素ごとの最大を 1 チャネル目（tool_L の位置）に置き、
残り 4 チャネルを零にした 5 チャネルの地図を作る。「誰の手か」を落とし「器具がどこにあるか」だけを渡す。

入れ替えの腕は目録の B_shuffle の見取りと同じ並べ替え（stage2pilot.shuffle_signals.make_mapping、seed 42、フレーム名の昇順）。
規則から作り直した並べ替えが目録の見取りの mapping と一致することを確かめてから使う。

    python scripts/grasppilot/arms_tool_only.py --out-dir <S>/signals/tool_only

対照（SPEC §3.3、両方向）:
    手のチャネルを零にしない写し（[最大, 0, 0, hand_L, hand_R]）では術具だけの地図と一致しない
    1 チャネル目が各画素で元の器具の 3 チャネルのどれかと一致し、3 チャネルのどれよりも小さくない（壊れた写し = hand_L を置いた写しでは外れる）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grasppilot import grasp_signals as G  # noqa: E402
from stage2pilot.shuffle_signals import make_mapping  # noqa: E402

M = Path(__file__).resolve().parents[2]
MANIFEST = M / "experiments/analysis/grasp_tower_rebuild/signals_manifest.json"
TASK_ID = "T-2026-11-06-grasp-pilot-arms"
TOOLS = [G.MAP_CHANNELS.index(k) for k in ("tool_L", "tool_R", "tool_B")]
HANDS = [G.MAP_CHANNELS.index(k) for k in ("hand_L", "hand_R")]
CHUNK = 256


def sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""):
            h.update(b)
    return h.hexdigest()


def build(part, man, out_dir):
    src = man["B_m"][f"pred_noCF_{part}"]
    view = json.loads(Path(src["view"]).read_text())
    assert view["maps"] == src["maps"] and view["mapping"] is None
    m = np.load(src["maps"], mmap_mode="r")
    n = m.shape[0]
    assert m.shape[1] == len(G.MAP_CHANNELS) and n == len(view["frame_ids"]) == src["frames"]
    dst = out_dir / f"tool_only_{part}_m.npy"
    out = np.lib.format.open_memmap(dst, mode="w+", dtype=np.uint8, shape=m.shape)
    stat = dict(not_one_of_three=0, below_some_tool=0, nonzero_other_channels=0,
                ctrl_keep_hands_frames_differ=0, ctrl_keep_hands_pixels_differ=0,
                ctrl_handL_not_one_of_three=0, ctrl_handL_below_some_tool=0,
                frames_with_tool=0, frames_with_hand=0, vmin=255, vmax=0)
    for s in range(0, n, CHUNK):
        x = np.asarray(m[s:s + CHUNK])
        t = x[:, TOOLS]
        mx = t.max(1)
        y = np.zeros_like(x)
        y[:, 0] = mx
        out[s:s + CHUNK] = y
        # 定義の確かめ: 1 チャネル目は器具の 3 チャネルのどれかと各画素で一致し、どれよりも小さくない。他の 4 チャネルは零
        stat["not_one_of_three"] += int((~(t == mx[:, None]).any(1)).sum())
        stat["below_some_tool"] += int((mx[:, None] < t).any(1).sum())
        stat["nonzero_other_channels"] += int((y[:, 1:] != 0).sum())
        # 対照 1: 手のチャネルを零にしない写し
        keep = y.copy()
        keep[:, HANDS] = x[:, HANDS]
        diff = (keep != y).reshape(len(x), -1).any(1)
        stat["ctrl_keep_hands_frames_differ"] += int(diff.sum())
        stat["ctrl_keep_hands_pixels_differ"] += int((keep != y).sum())
        # 対照 2: 1 チャネル目に hand_L を置いた壊れた写しでは、上の確かめが外れる
        bad = x[:, HANDS[0]]
        stat["ctrl_handL_not_one_of_three"] += int((~(t == bad[:, None]).any(1)).sum())
        stat["ctrl_handL_below_some_tool"] += int((bad[:, None] < t).any(1).sum())
        stat["frames_with_tool"] += int((mx.reshape(len(x), -1) > 0).any(1).sum())
        stat["frames_with_hand"] += int((x[:, HANDS].reshape(len(x), -1) > 0).any(1).sum())
        stat["vmin"] = min(stat["vmin"], int(mx.min()))
        stat["vmax"] = max(stat["vmax"], int(mx.max()))
    out.flush()
    del out
    digest = sha(dst)
    base = {k: view[k] for k in ("frame_ids",)}
    common = dict(maps=str(dst), task_id=TASK_ID, part=part, channels=G.MAP_CHANNELS,
                  format="(N, 5, 270, 480) uint8。1 チャネル目 = 器具の 3 チャネルの画素ごとの最大、他の 4 チャネルは零",
                  derived_from=dict(view=src["view"], view_sha256=src["view_sha256"], maps=src["maps"],
                                    maps_sha256=src["maps_sha256"]))
    v_no = dst.parent / f"B_toolonly_pred_noCF_{part}.json"
    v_no.write_text(json.dumps({**common, **base, "arm": "toolonly_pred_noCF", "mapping": None}, ensure_ascii=False))
    # 入れ替え: 規則から作り直した並べ替えが目録の見取りの mapping と一致すること
    shuf = man["B_m"][f"shuffle_{part}"]
    sview = json.loads(Path(shuf["view"]).read_text())
    remade = make_mapping(view["frame_ids"], 42)
    remade43 = make_mapping(view["frame_ids"], 43)
    assert sview["frame_ids"] == view["frame_ids"]
    mapping_equal = remade == sview["mapping"]
    if not mapping_equal:
        raise SystemExit(f"並べ替えが目録と一致しない: {part}")
    v_sh = dst.parent / f"B_toolonly_shuffle_{part}.json"
    v_sh.write_text(json.dumps({**common, **base, "arm": "toolonly_shuffle", "mapping": remade,
                                "mapping_rule": man["shuffle_rule"], "mapping_from_manifest_view": shuf["view"]},
                               ensure_ascii=False))
    fixed = sum(1 for f, g in remade.items() if f == g)
    return {"part": part, "frames": n, "shape": list(m.shape), "maps": str(dst), "maps_sha256": digest,
            "range_channel0": [stat["vmin"], stat["vmax"]], "checks": stat,
            "view_pred_noCF": str(v_no), "view_pred_noCF_sha256": sha(v_no),
            "view_shuffle": str(v_sh), "view_shuffle_sha256": sha(v_sh),
            "mapping_equals_manifest_view": mapping_equal, "mapping_seed43_equals_manifest_view": remade43 == sview["mapping"],
            "mapping_fixed_point_fraction": fixed / n,
            "pass": (stat["not_one_of_three"] == 0 and stat["below_some_tool"] == 0 and stat["nonzero_other_channels"] == 0
                     and stat["ctrl_keep_hands_frames_differ"] > 0 and stat["ctrl_handL_not_one_of_three"] > 0
                     and mapping_equal and remade43 != sview["mapping"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    man = json.loads(MANIFEST.read_text())
    rep = {"task_id": TASK_ID, "manifest": str(MANIFEST), "manifest_sha256": sha(MANIFEST), "code_sha256": sha(Path(__file__)),
           "channels": G.MAP_CHANNELS, "tools": TOOLS, "hands": HANDS}
    for part in ("train", "val"):
        rep[part] = build(part, man, out_dir)
        print(json.dumps({k: rep[part][k] for k in ("part", "frames", "maps_sha256", "range_channel0", "checks",
                                                     "mapping_equals_manifest_view", "pass")}, ensure_ascii=False), flush=True)
    (out_dir / "tool_only_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
