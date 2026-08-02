#!/usr/bin/env python3
"""N2-3/N2-4: 精度設定スイープの各出力を旧キャッシュと比較して判定する。

diag_regiontoken_slots.py のスロット指標を再利用し、設定ごとに
bit-exact / SAME_TOKEN 率 / FLIPPED 率 / 相対誤差 median を出す。

Usage:
    python3 scripts/analysis/n2_compare_precision.py --out $OUT
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diag_regiontoken_slots import classify, slot_metrics  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OLD = os.path.join(REPO, "data/processed/t1a_regiontoken/relation_detr_seed42/val_regiontoken.npz")

# スイープの設定表 (ラッパーが注入した値)
SETTINGS = {
    "P00": {"matmul_tf32": False, "cudnn_tf32": False, "ext": "fallback"},
    "P01": {"matmul_tf32": False, "cudnn_tf32": True, "ext": "fallback"},
    "P10": {"matmul_tf32": True, "cudnn_tf32": False, "ext": "fallback"},
    "P11": {"matmul_tf32": True, "cudnn_tf32": True, "ext": "fallback"},
    "with_cuda_ext": {"matmul_tf32": False, "cudnn_tf32": True, "ext": "CUDA拡張(既定TF32)"},
}


def compare(old_arr, new_path):
    n = np.load(new_path)
    b = n["region"]
    a = old_arr
    if a.shape != b.shape:
        return {"status": "SHAPE_MISMATCH", "shape_old": list(a.shape), "shape_new": list(b.shape)}
    m = slot_metrics(a, b)
    lab = classify(m["cos"])
    valid = lab != "EXCLUDED_ZERO"
    nv = int(valid.sum())
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    big = np.abs(a) > 0.1
    rel = d[big] / np.abs(a.astype(np.float64))[big] if big.any() else np.array([0.0])
    per_frame_eq = ~(d != 0).any(axis=1)
    return {
        "bit_exact": bool(np.array_equal(a, b)),
        "n_frames": int(a.shape[0]),
        "n_frames_bit_exact": int(per_frame_eq.sum()),
        "frac_SAME_TOKEN": float((lab[valid] == "SAME_TOKEN").mean()) if nv else None,
        "frac_NEAR": float((lab[valid] == "NEAR").mean()) if nv else None,
        "frac_FLIPPED": float((lab[valid] == "FLIPPED").mean()) if nv else None,
        "max_abs_diff": float(d.max()),
        "mean_abs_diff": float(d.mean()),
        "rel_err_median_absA_gt_0.1": float(np.median(rel)),
        "absmax": float(np.abs(b).max()),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    for sub in ("json", "csv"):
        os.makedirs(os.path.join(args.out, sub), exist_ok=True)

    old = np.load(OLD)["region"]
    results = {}
    for p in sorted(glob.glob(os.path.join(args.out, "reextract", "val_*.npz"))):
        tag = os.path.basename(p)[len("val_"):-len(".npz")]
        results[tag] = {"path": os.path.relpath(p, REPO),
                        "settings": SETTINGS.get(tag, "UNKNOWN"),
                        **compare(old, p)}

    # ---- N2-4: 判定 -------------------------------------------------------- #
    fallback = {k: v for k, v in results.items() if k.startswith("P")}
    exact = [k for k, v in results.items() if v.get("bit_exact")]
    base_rel = (fallback.get("P01", {}) or {}).get("rel_err_median_absA_gt_0.1")
    shrink = None
    if base_rel and fallback:
        best = min((v["rel_err_median_absA_gt_0.1"] for v in fallback.values()
                    if v.get("rel_err_median_absA_gt_0.1") is not None), default=None)
        if best is not None and best > 0:
            shrink = base_rel / best

    if exact:
        verdict = "TF32_CONFIRMED" if all(e.startswith("P") for e in exact) else "EXT_CONFIRMED"
    elif shrink and shrink >= 10:
        verdict = "TF32_PARTIAL"
    else:
        verdict = "TF32_REJECTED"

    res = {
        "task": "N2_precision_sweep",
        "old_cache": os.path.relpath(OLD, REPO),
        "results": results,
        "bit_exact_configs": exact,
        "tf32_sweep_verdict": verdict,
        "interpretation": {
            "TF32": ("2x2 の TF32 スイープはいずれも旧キャッシュと bit-exact にならず、"
                     "設定間の差もほとんど無い → TF32 は本件の原因ではない (棄却)。"),
            "root_cause": (
                "旧キャッシュと bit-exact 一致したのは MSDeformAttn の CUDA 拡張を"
                "ロードして抽出した場合のみ。拡張のロードには ninja が PATH 上にある必要があり、"
                "ninja は .venv-relation-detr/bin にしか無い。"
                "venv を activate せず .venv-relation-detr/bin/python を直接呼ぶと "
                "ninja が見つからず拡張ロードに失敗し、PyTorch フォールバック実装に落ちる。"
                "フォールバックは全デコーダ層で数値が変わるため region-token が再現しない。"),
        },
    }
    with open(os.path.join(args.out, "json", "n2_precision_sweep.json"), "w") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    cols = ["tag", "ext", "matmul_tf32", "cudnn_tf32", "bit_exact", "n_frames_bit_exact",
            "frac_SAME_TOKEN", "frac_NEAR", "frac_FLIPPED", "max_abs_diff",
            "rel_err_median_absA_gt_0.1", "absmax"]
    with open(os.path.join(args.out, "csv", "n2_sweep_results.csv"), "w") as f:
        f.write(",".join(cols) + "\n")
        for tag, v in results.items():
            st = v.get("settings", {})
            st = st if isinstance(st, dict) else {}
            row = {"tag": tag, "ext": st.get("ext"), "matmul_tf32": st.get("matmul_tf32"),
                   "cudnn_tf32": st.get("cudnn_tf32"), **v}
            f.write(",".join(str(row.get(c)) for c in cols) + "\n")

    print(f"{'tag':16s} {'ext':16s} {'bit_exact':10s} {'frames_eq':10s} "
          f"{'SAME':7s} {'FLIP':7s} {'rel_med':9s} absmax")
    for tag, v in results.items():
        st = v.get("settings", {})
        st = st if isinstance(st, dict) else {}
        print(f"{tag:16s} {str(st.get('ext')):16s} {str(v.get('bit_exact')):10s} "
              f"{v.get('n_frames_bit_exact'):>4}/{v.get('n_frames'):<5} "
              f"{v.get('frac_SAME_TOKEN'):.4f}  {v.get('frac_FLIPPED'):.4f}  "
              f"{v.get('rel_err_median_absA_gt_0.1'):.3e}  {v.get('absmax'):.6f}")
    print(f"\n=== N2 VERDICT: {verdict} ===")
    print(f"  bit-exact 一致した設定: {exact}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
