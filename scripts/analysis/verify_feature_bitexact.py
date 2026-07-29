#!/usr/bin/env python3
"""D3-6/7: 既存 T1a region-token キャッシュと再抽出結果の bit-exact 比較。

なぜ必要か: 今後 region-token を再抽出する際、抽出時の torch が既存 T1a 特徴を作ったときと
違えば数値が微妙に変わり、Δ の比較が汚染される。環境修理として扱うと汚染に気付かないまま実験が進む。

Usage:
    python3 scripts/analysis/verify_feature_bitexact.py --old OLD.npz --new NEW.npz --out $OUT
    python3 scripts/analysis/verify_feature_bitexact.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import tempfile

import numpy as np


def compare(old_path, new_path):
    old = np.load(old_path)
    new = np.load(new_path)
    res = {"old_path": old_path, "new_path": new_path,
           "old_keys": sorted(old.files), "new_keys": sorted(new.files)}

    # 1. キー集合の一致
    res["keys_match"] = sorted(old.files) == sorted(new.files)
    if not res["keys_match"]:
        res["verdict"] = "FAIL"
        res["reason"] = f"キー集合が不一致: old={sorted(old.files)} new={sorted(new.files)}"
        return res

    # frame_ids の一致 (順序も含む)
    if "frame_ids" in old.files:
        oi, ni = old["frame_ids"], new["frame_ids"]
        res["n_frames_old"], res["n_frames_new"] = int(oi.size), int(ni.size)
        res["frame_ids_equal"] = bool(oi.size == ni.size and np.array_equal(oi, ni))
        if not res["frame_ids_equal"]:
            res["frame_ids_set_equal"] = bool(set(oi.tolist()) == set(ni.tolist()))

    key = "region" if "region" in old.files else [k for k in old.files if k != "frame_ids"][0]
    res["array_key"] = key
    a, b = old[key], new[key]

    # 2. shape / dtype
    res["shape_old"], res["shape_new"] = list(a.shape), list(b.shape)
    res["dtype_old"], res["dtype_new"] = str(a.dtype), str(b.dtype)
    res["shape_match"] = a.shape == b.shape
    res["dtype_match"] = a.dtype == b.dtype
    if not res["shape_match"]:
        res["verdict"] = "FAIL"
        res["reason"] = f"shape 不一致: {a.shape} vs {b.shape}"
        return res

    # 3. bit-exact
    res["bit_exact"] = bool(np.array_equal(a, b))

    # 4. 不一致時の統計
    diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
    res["max_abs_diff"] = float(diff.max())
    res["mean_abs_diff"] = float(diff.mean())
    ne = diff != 0
    res["n_elements"] = int(a.size)
    res["n_mismatch_elements"] = int(ne.sum())
    res["mismatch_element_frac"] = float(ne.mean())
    denom = np.maximum(np.abs(a.astype(np.float64)), 1e-12)
    rel = diff / denom
    res["rel_err_quantiles"] = {q: float(np.percentile(rel, p))
                                for q, p in [("p50", 50), ("p90", 90), ("p99", 99),
                                             ("p99.9", 99.9), ("max", 100)]}
    # フレーム単位の一致率
    per_frame_equal = ~ne.any(axis=1) if a.ndim == 2 else None
    if per_frame_equal is not None:
        res["n_frames"] = int(a.shape[0])
        res["n_frames_bit_exact"] = int(per_frame_equal.sum())
        res["n_frames_differing"] = int((~per_frame_equal).sum())
        res["frame_exact_frac"] = float(per_frame_equal.mean())

    # 7. 判定
    if res["bit_exact"]:
        res["verdict"] = "PASS"
        res["reason"] = "完全に bit-exact。G-2 に進んでよい"
    elif res["max_abs_diff"] < 1e-5 and res["rel_err_quantiles"]["max"] < 1e-4:
        res["verdict"] = "WARN"
        res["reason"] = ("差が float32 の丸め誤差相当 (max_abs_diff<1e-5 かつ相対誤差<1e-4)。"
                         "G-2 では「再抽出した特徴で T1a も取り直す」設計にすべき")
    else:
        res["verdict"] = "FAIL"
        res["reason"] = ("丸め誤差を超える差。G-2 に進まない。"
                         "原因調査を別タスクとして起票すべき")
    return res


def self_test() -> int:
    """検出できることを確認する:
       1) 完全一致を PASS と判定できるか
       2) 丸め誤差相当の差を WARN と判定できるか
       3) 大きな差を FAIL と判定できるか
       4) shape/キー不一致を検出できるか
    """
    ok = True
    with tempfile.TemporaryDirectory() as td:
        ids = np.array(["01_1_0001", "01_1_0002"])
        a = np.random.RandomState(0).randn(2, 8).astype(np.float32)

        p1 = os.path.join(td, "a.npz"); np.savez(p1, frame_ids=ids, region=a)
        p2 = os.path.join(td, "b.npz"); np.savez(p2, frame_ids=ids, region=a.copy())
        r = compare(p1, p2)
        if not (r["bit_exact"] and r["verdict"] == "PASS"):
            print(f"  [FAIL] 完全一致の判定: {r['verdict']}"); ok = False
        else:
            print("  [OK]   完全一致を PASS と判定")

        tiny = a + np.float32(1e-7)
        p3 = os.path.join(td, "c.npz"); np.savez(p3, frame_ids=ids, region=tiny)
        r = compare(p1, p3)
        if r["verdict"] != "WARN":
            print(f"  [FAIL] 丸め誤差の判定: {r['verdict']} "
                  f"(max={r['max_abs_diff']:.2e} rel={r['rel_err_quantiles']['max']:.2e})")
            ok = False
        else:
            print(f"  [OK]   丸め誤差相当の差を WARN と判定 (max_abs={r['max_abs_diff']:.2e})")

        big = a + np.float32(0.1)
        p4 = os.path.join(td, "d.npz"); np.savez(p4, frame_ids=ids, region=big)
        r = compare(p1, p4)
        if r["verdict"] != "FAIL":
            print(f"  [FAIL] 大差の判定: {r['verdict']}"); ok = False
        else:
            print("  [OK]   丸め誤差を超える差を FAIL と判定")

        p5 = os.path.join(td, "e.npz"); np.savez(p5, frame_ids=ids, region=a[:, :4])
        r = compare(p1, p5)
        if r["verdict"] != "FAIL" or r.get("shape_match", True):
            print(f"  [FAIL] shape 不一致の検出: {r}"); ok = False
        else:
            print("  [OK]   shape 不一致を検出して FAIL")

        p6 = os.path.join(td, "f.npz"); np.savez(p6, frame_ids=ids, other=a)
        r = compare(p1, p6)
        if r["verdict"] != "FAIL" or r["keys_match"]:
            print("  [FAIL] キー不一致の検出"); ok = False
        else:
            print("  [OK]   キー集合の不一致を検出して FAIL")
    print("SELF-TEST:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--old")
    ap.add_argument("--new")
    ap.add_argument("--out")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not (args.old and args.new and args.out):
        ap.error("--old --new --out が必要 (または --self-test)")
    os.makedirs(os.path.join(args.out, "json"), exist_ok=True)
    res = compare(args.old, args.new)
    with open(os.path.join(args.out, "json", "d3_bitexact.json"), "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    for k in ("keys_match", "frame_ids_equal", "shape_match", "dtype_match", "bit_exact",
              "max_abs_diff", "mean_abs_diff", "n_mismatch_elements", "mismatch_element_frac",
              "n_frames", "n_frames_bit_exact", "n_frames_differing", "frame_exact_frac"):
        if k in res:
            print(f"  {k}: {res[k]}")
    if "rel_err_quantiles" in res:
        print(f"  rel_err: {res['rel_err_quantiles']}")
    print(f"\n=== D3 VERDICT: {res['verdict']} ===\n  {res['reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
