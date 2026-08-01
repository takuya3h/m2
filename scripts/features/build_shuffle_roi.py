#!/usr/bin/env python3
"""S3: shuffleROI 特徴を作る（bboxROI のフレーム対応だけを無効化した対照）。

目的: G-2 の 2−1（bboxROI − base）が「ROI の情報」の効果か「入力次元の倍増」の
効果かを分離する。shuffleROI は bboxROI と**同一の行集合**を持ち、フレームとの
対応だけが壊れている。したがって次元も周辺分布も bboxROI と厳密に一致する。

設計（事前登録 prereg/s3_shuffle_prediction.md）:
  - シャッフルは **split 内**で行う（train / val / test を独立に置換）
  - 置換は **training seed ごとに別**で、seed から決定論的に導出する
  - **derangement**（どの行も自分自身に割り当たらない）を assert する
  - 周辺分布（mean / std / ノルム分布）が bboxROI と厳密一致することを assert する

GPU 不要（既存の npz を並べ替えるだけ。検出器を呼ばない）。

Usage:
    python scripts/features/build_shuffle_roi.py \
        --src experiments/g2_main_2026-07-29_lecun/features \
        --out experiments/g2_followup_2026-07-29/s3/features --seed 42
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

SPLITS = ["train", "val", "test"]


def derangement(n: int, rng: np.random.Generator) -> np.ndarray:
    """perm[i] != i を満たす置換を返す（棄却法 + 局所修復）。

    n が大きいと単純棄却は成功率 1/e ≈ 0.368 だが、1 回の試行が O(n) なので十分速い。
    残った不動点は隣とスワップして解消する（置換であることは保たれる）。
    """
    assert n >= 2
    for _ in range(64):
        p = rng.permutation(n)
        fixed = np.nonzero(p == np.arange(n))[0]
        if len(fixed) == 0:
            return p
        # 不動点を、不動点でない相手とスワップして解消する
        for i in fixed:
            j = int(rng.integers(n))
            while j == i or p[j] == i:
                j = int(rng.integers(n))
            p[i], p[j] = p[j], p[i]
        if not (p == np.arange(n)).any():
            return p
    raise RuntimeError("derangement を作れなかった")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="bboxROI npz があるディレクトリ")
    ap.add_argument("--out", required=True, help="出力先ディレクトリ")
    ap.add_argument("--seed", type=int, required=True, help="training seed（置換の導出に使う）")
    args = ap.parse_args()
    src, out = Path(args.src), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    stats: dict = {"seed": args.seed, "src": str(src), "splits": {}}
    for split in SPLITS:
        p = src / f"{split}_bboxROI.npz"
        assert p.exists(), f"入力が無い: {p}"
        z = np.load(p)
        roi = z["roi"]                       # (N, 3840) ループ外で 1 回だけ読む
        fids = z["frame_ids"]
        n = int(roi.shape[0])

        # 置換は (seed, split) から決定論的に導出する
        h = hashlib.sha256(f"s3-shuffle|{args.seed}|{split}".encode()).digest()
        rng = np.random.default_rng(int.from_bytes(h[:8], "big"))
        perm = derangement(n, rng)

        # --- assert 1: 置換であること ---
        assert np.array_equal(np.sort(perm), np.arange(n)), "置換でない"
        # --- assert 2: derangement（自分自身に割り当たらない）---
        n_fixed = int((perm == np.arange(n)).sum())
        assert n_fixed == 0, f"不動点が {n_fixed} 個ある（derangement でない）"

        shuffled = roi[perm]                 # 行 i に、別フレーム perm[i] の ROI を入れる

        # --- assert 3: 周辺分布が bboxROI と一致 ---
        # 厳密に成り立つ不変量は「**行の多重集合が同一**」であること。
        # 一方 float32 の総和は結合律を満たさないため、行を並べ替えると mean / std は
        # 最終ビットで変わる（実測 相対差 ~7e-7 = float32 eps 1.2e-7 の数倍で、
        # pairwise/SIMD 縮約の順序差として整合的）。したがって
        #   - 行の多重集合・行ノルム分布（行間の総和を含まない） -> **厳密一致**を要求
        #   - mean / std / 列 mean                              -> 許容誤差で検証し偏差を記録
        # と分けて検証する。
        h0 = sorted(hashlib.md5(r.tobytes()).hexdigest() for r in roi)
        h1 = sorted(hashlib.md5(r.tobytes()).hexdigest() for r in shuffled)
        assert h0 == h1, "行集合（多重集合）が保たれていない"

        nr = np.linalg.norm(roi, axis=1)
        ns = np.linalg.norm(shuffled, axis=1)
        assert np.array_equal(np.sort(nr), np.sort(ns)), "行ノルム分布が厳密一致しない"

        # float64 で累積すれば偏差はさらに小さくなる（順序依存が残るだけ）
        m0 = float(roi.mean(dtype=np.float64)); m1 = float(shuffled.mean(dtype=np.float64))
        s0 = float(roi.std(dtype=np.float64)); s1 = float(shuffled.std(dtype=np.float64))
        m32_0, m32_1 = float(roi.mean()), float(shuffled.mean())
        cm0 = roi.mean(axis=0, dtype=np.float64)
        cm1 = shuffled.mean(axis=0, dtype=np.float64)
        dev = {
            "mean_abs_dev_f64": abs(m0 - m1),
            "mean_rel_dev_f64": abs(m0 - m1) / max(abs(m0), 1e-30),
            "std_abs_dev_f64": abs(s0 - s1),
            "mean_rel_dev_f32": abs(m32_0 - m32_1) / max(abs(m32_0), 1e-30),
            "col_mean_max_abs_dev_f64": float(np.abs(cm0 - cm1).max()),
        }
        # float64 累積での相対差が 1e-12 を超えたら、順序依存では説明できないので落とす
        assert dev["mean_rel_dev_f64"] < 1e-12, f"mean が順序依存を超えて不一致: {dev}"
        assert dev["std_abs_dev_f64"] < 1e-12 * max(abs(s0), 1.0), f"std が不一致: {dev}"
        assert dev["col_mean_max_abs_dev_f64"] < 1e-9, f"列 mean が不一致: {dev}"
        # --- assert 4: 実際に対応が壊れていること ---
        n_same_row = int(sum(1 for i in range(n)
                            if np.array_equal(roi[i], shuffled[i])))
        # ゼロ行が複数あると derangement でも同値になりうるので、率で記録する
        zero_rows = int((nr == 0).sum())

        op = out / f"{split}_shuffleROI_seed{args.seed}.npz"
        np.savez(op, frame_ids=fids, roi=shuffled)
        stats["splits"][split] = {
            "n_rows": n, "n_fixed_points": n_fixed,
            "n_rows_identical_after_shuffle": n_same_row,
            "n_all_zero_rows": zero_rows,
            "note_identical_rows": ("全ゼロ行が複数あるため、derangement でも行の値が"
                                    "一致することがある。分母は n_rows。"),
            "exact_invariants": {"row_multiset_equal": True, "row_norm_dist_equal": True},
            "float_deviation_order_dependence": dev,
            "mean_f64": m0, "std_f64": s0,
            "out": str(op),
            "out_md5": hashlib.md5(op.read_bytes()).hexdigest(),
        }
        print(f"  [{split}] n={n} 不動点={n_fixed} 値一致行={n_same_row}/{n} "
              f"(全ゼロ行={zero_rows})")
        print(f"          厳密一致: 行多重集合 ✅ / 行ノルム分布 ✅   "
              f"順序依存の偏差: mean rel(f64)={dev['mean_rel_dev_f64']:.2e} "
              f"(f32 では {dev['mean_rel_dev_f32']:.2e}) 列mean max abs={dev['col_mean_max_abs_dev_f64']:.2e}")

    sp = out.parent / "json"
    sp.mkdir(parents=True, exist_ok=True)
    (sp / f"s3_shuffle_build_seed{args.seed}.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False))
    print(f"-> {sp / f's3_shuffle_build_seed{args.seed}.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
