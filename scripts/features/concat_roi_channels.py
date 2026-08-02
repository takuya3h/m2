#!/usr/bin/env python3
"""複数の ROI npz を frame_id で join して 1 本の npz に連結する。

S4 の系統 9（bboxROI + handROI(bbox,2cls)）のように、既存の ROI チャネルを
複数まとめて base に足す系統を作るために使う。`train_g2.py` の `load_clips` は
`{split}_{system}.npz` を 1 本だけ読む設計なので、学習コード側は変更せず
**連結済みの npz を用意する**方針を採る。

frame_id は集合として完全一致することを assert する（順序は先頭の npz に揃える）。

Usage:
    python scripts/features/concat_roi_channels.py \
        --split val --name bboxROI_handROIbbox2 \
        --src A/features/val_bboxROI.npz B/features/val_handROIbbox2.npz \
        --out B/features
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--name", required=True, help="出力する system 名")
    ap.add_argument("--src", nargs="+", required=True, help="連結する npz（この順で連結）")
    ap.add_argument("--out", required=True, help="出力ディレクトリ")
    args = ap.parse_args()

    parts, ids_ref, dims = [], None, []
    for s in args.src:
        z = np.load(s)
        roi = z["roi"]                       # ループ外で 1 回だけ読む
        ids = [str(x) for x in z["frame_ids"]]
        if ids_ref is None:
            ids_ref = ids
        else:
            assert set(ids) == set(ids_ref), f"frame_id 集合が不一致: {s}"
            if ids != ids_ref:
                # 順序が違う場合は先頭に揃えて並べ替える
                pos = {f: i for i, f in enumerate(ids)}
                roi = roi[[pos[f] for f in ids_ref]]
        parts.append(roi)
        dims.append(int(roi.shape[1]))
        print(f"  + {s}  shape={roi.shape}")

    cat = np.concatenate(parts, axis=1).astype(np.float32)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    op = out / f"{args.split}_{args.name}.npz"
    np.savez(op, frame_ids=np.asarray(ids_ref), roi=cat)

    # 連結が単なる横結合であることを検証（各部分が元の値と一致すること）
    z = np.load(op)
    chk = z["roi"]
    o = 0
    for p, d in zip(parts, dims):
        assert np.array_equal(chk[:, o:o + d], p), "連結後の部分配列が元と一致しない"
        o += d
    assert o == chk.shape[1]

    info = {"split": args.split, "name": args.name, "src": args.src,
            "part_dims": dims, "total_dim": int(cat.shape[1]),
            "n_frames": int(cat.shape[0]), "out": str(op),
            "out_md5": hashlib.md5(op.read_bytes()).hexdigest(),
            "verified": "各部分配列が元 npz と厳密一致することを確認"}
    print(f"  -> {op}  shape={cat.shape} (部分次元 {dims})  検証 OK")
    print(json.dumps(info, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
