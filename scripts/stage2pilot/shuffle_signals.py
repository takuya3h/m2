"""Task C-2: 入れ替えの腕の信号を作る（非公式 T-2026-10-19-stage2-pilot-fix-epoch4-shuffle、SPEC §3）。

予測（交差適合なし）の信号の値を、split ごとに一つの固定の並べ替え（seed 42）で、フレームとの対応だけ入れ替える。

- 並べ替えは split 全体のフレーム（名前の昇順に並べたもの）にわたる。動画の中だけで入れ替えない
- 同じ split の信号（P0、D0、D0-RT、D0-INST-UQ）はすべて同じ並べ替えを使う（フレームの集合が同じことを確かめてから）
- 集合の信号（D0-INST-UQ）は、フレームごとの行（トークン全体と有効の数 count）を丸ごと入れ替える
- 入れ替えた信号でフレーム f が持つ値 = 元の信号でフレーム π(f) が持っていた値
- test のフレームは使わない（混ざれば止まる）。元の信号は読むだけで、入れ替えた信号は別のファイルに書く

記録: 並べ替えの seed、対応表とその sha256、元と同じフレームが来た割合、同じ動画のフレームから来た割合、
信号ごとの値の集合の一致（行を並べ直すと一致するか）、元と同じ値が来た割合、陽性対照（恒等の並べ替え・値を一つ変えた写し）。

    python scripts/stage2pilot/shuffle_signals.py --out-dir <dir> --record <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402

FINAL = C.STORE / "signals/final"
SIGS = ("P0", "D0", "D0-RT", "D0-INST-UQ")
SEED = 42


def load(path):
    with np.load(path) as d:
        return [str(f) for f in d["frame_ids"]], d["x"], (d["count"] if "count" in d else None)


def make_mapping(frames, seed=SEED) -> dict[str, str]:
    """フレーム f → 値を持ってくる元のフレーム π(f)。名前の昇順に並べてから seed で並べ替える。"""
    order = sorted(frames)
    perm = np.random.default_rng(seed).permutation(len(order))
    return {f: order[int(j)] for f, j in zip(order, perm)}


def mapping_stats(mapping) -> dict:
    n = len(mapping)
    fixed = sum(1 for f, g in mapping.items() if f == g)
    same_video = sum(1 for f, g in mapping.items() if C.video_of(f) == C.video_of(g))
    text = json.dumps(sorted(mapping.items()), ensure_ascii=False)
    return {"frames": n, "fixed_point_fraction": fixed / n, "changed_fraction": 1 - fixed / n,
            "same_video_fraction": same_video / n, "mapping_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "is_bijection": sorted(mapping.values()) == sorted(mapping)}


def rows_with_count(x, cnt):
    flat = x.reshape(len(x), -1)
    if cnt is not None:
        flat = np.concatenate([flat, np.asarray(cnt, dtype=flat.dtype).reshape(-1, 1)], 1)
    return flat


def sorted_digest(x, cnt) -> str:
    """行（count を含む）を並べ直した値の要約値。並べ替えに依らない。"""
    h = hashlib.sha256()
    for r in sorted(r.tobytes() for r in rows_with_count(x, cnt)):
        h.update(r)
    return h.hexdigest()


def apply(ids, x, cnt, mapping):
    idx = {f: i for i, f in enumerate(ids)}
    rows = [idx[mapping[f]] for f in ids]
    return x[rows], (None if cnt is None else cnt[rows])


def same_value_fraction(x, cnt, y, ycnt) -> float:
    a, b = rows_with_count(x, cnt), rows_with_count(y, ycnt)
    return float(np.mean(np.all(a == b, axis=1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--record", required=True)
    a = ap.parse_args()
    out_dir = Path(a.out_dir)
    record = {"task_id": C.FIX_TASK_ID, "seed": SEED, "source_dir": str(FINAL), "signals": list(SIGS), "parts": {}}
    for part in ("train", "val"):
        loaded = {s: load(FINAL / f"{s}_{part}.npz") for s in SIGS}
        frames = set(loaded[SIGS[0]][0])
        for s, (ids, _, _) in loaded.items():
            if set(ids) != frames or len(ids) != len(frames):
                raise SystemExit(f"{s}_{part} のフレームの集合が {SIGS[0]} と違う")
        videos = C.assert_no_test(frames, f"shuffle_signals/{part}")
        mapping = make_mapping(frames)
        C.write_json(out_dir / f"mapping_{part}.json", {"seed": SEED, "rule": "frame f gets the value of mapping[f]",
                                                         "mapping": dict(sorted(mapping.items()))})
        pr = {"videos": videos, **mapping_stats(mapping), "mapping_file": str(out_dir / f"mapping_{part}.json"),
              "signals": {}}
        for s, (ids, x, cnt) in loaded.items():
            y, ycnt = apply(ids, x, cnt, mapping)
            extra = {} if ycnt is None else {"count": ycnt}
            out = out_dir / f"{s}_{part}.npz"
            digest = C.save_signal(out, ids, y, **extra)
            src = FINAL / f"{s}_{part}.npz"
            back = load(out)
            sd_src, sd_out = sorted_digest(x, cnt), sorted_digest(back[1], back[2])
            pr["signals"][s] = {
                "source": str(src), "source_sha256": C.sha256(src), "out": str(out), "out_sha256": digest,
                "shape": list(x.shape), "sha256_differs_from_source": digest != C.sha256(src),
                "sorted_digest_source": sd_src, "sorted_digest_out": sd_out, "value_set_equal": sd_src == sd_out,
                "same_value_fraction": same_value_fraction(x, cnt, back[1], back[2]),
                "frame_ids_same_order": back[0] == ids}
        # 陽性対照（完了判定 e の四列目）
        ident = {f: f for f in frames}
        ids, x, cnt = loaded["D0"]
        y, _ = apply(ids, x, cnt, mapping)
        y_bad = y.copy()
        y_bad[0, 0] = y_bad[0, 0] + 1.0
        pr["controls"] = {
            "identity_mapping": {k: v for k, v in mapping_stats(ident).items() if k != "mapping_sha256"},
            "one_value_changed_D0": {"value_set_equal": sorted_digest(x, None) == sorted_digest(y_bad, None)},
        }
        record["parts"][part] = pr
    C.write_json(a.record, record)
    for part, pr in record["parts"].items():
        print(f"[{part}] frames {pr['frames']} 対応が変わった割合 {pr['changed_fraction']:.6f} "
              f"同じ動画から {pr['same_video_fraction']:.6f} 全単射 {pr['is_bijection']} 対応表 {pr['mapping_sha256'][:16]}")
        for s, r in pr["signals"].items():
            print(f"   {s:<11} 値の集合が同じ {r['value_set_equal']} 要約値が元と違う {r['sha256_differs_from_source']} "
                  f"同じ値が来た割合 {r['same_value_fraction']:.6f} {r['out_sha256'][:16]}")
        c = pr["controls"]
        print(f"   対照: 恒等の並べ替えの対応が変わった割合 {c['identity_mapping']['changed_fraction']}、"
              f"値を一つ変えた写しの集合の一致 {c['one_value_changed_D0']['value_set_equal']}")


if __name__ == "__main__":
    main()
