"""腕ごとの信号を組む（非公式 T-2026-10-18-stage2-pilot-folda、Task F の腕の表）。

    concat  --inputs a.npz b.npz --out c.npz    フレームごとに連結（順は引数の順。正解予測の腕は正解が先）
    merge   --inputs h1.npz h2.npz --out c.npz   フレームの重ならない複数の信号を一つにまとめる（交差適合版）

フレームの集合が食い違えば止まる（補完しない）。test の動画が混ざれば止まる。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402


def load(path):
    with np.load(path) as d:
        return [str(f) for f in d["frame_ids"]], d["x"].astype(np.float32), (d["count"] if "count" in d else None)


def concat(inputs, out):
    loaded = [load(p) for p in inputs]
    ids = loaded[0][0]
    for other, _, _ in loaded[1:]:
        if set(other) != set(ids):
            raise SystemExit(f"フレームの集合が違う: {len(set(other) ^ set(ids))} 件")
    idx = [{f: i for i, f in enumerate(o)} for o, _, _ in loaded]
    x = np.concatenate([arr[[ix[f] for f in ids]] for (_, arr, _), ix in zip(loaded, idx)], axis=-1)
    C.assert_no_test(ids, "arm_signals.concat")
    return C.save_signal(out, ids, x)


def merge(inputs, out):
    ids, xs, counts = [], [], []
    for p in inputs:
        f, x, c = load(p)
        ids += f
        xs.append(x)
        counts.append(c)
    if len(ids) != len(set(ids)):
        raise SystemExit("フレームが重なる")
    C.assert_no_test(ids, "arm_signals.merge")
    extra = {"count": np.concatenate(counts)} if all(c is not None for c in counts) else {}
    return C.save_signal(out, ids, np.concatenate(xs), **extra)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["concat", "merge"])
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    print({"concat": concat, "merge": merge}[a.cmd](a.inputs, a.out), a.out)


if __name__ == "__main__":
    main()
